# A udev rule that blocks the boot

On mains power, a boot that used to reach login may spend two minutes in `systemd-udev-settle.service`.
Look for a udev worker's warning that `invoke-rc.d anacron start` is still running, then for `Timed out while waiting for udev queue to empty`.
The settle unit is the waiter.
The process named in the worker's warning is what keeps the event in the queue.

## Find the wait

1. Read `journalctl -b -o short-monotonic -u systemd-udevd.service -u systemd-udev-settle.service -u anacron.service`, then the previous boot with `-b -1`.
   Compare the adapter event, worker warning, settle result, service start and reached target.
2. Read `systemctl list-dependencies --reverse systemd-udev-settle.service` and `systemctl cat systemd-udev-settle.service anacron.service`.
   Identify the consumer that pulls the settle unit into early boot.
   The typical symptom is a worker waiting for a normal service's start job while an early unit waits for that worker.
3. Confirm the service ordering.
   `After=` orders units when both jobs are present.
   Normal services also start after `sysinit.target` and `basic.target`.
   A file-system consumer ordered after settle and before `local-fs.target` places its wait ahead of anacron. [systemd.unit(5), Before= and After=](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html#Before=), [systemd.service(5), Default Dependencies](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#Default%20Dependencies).
4. Read the exact rule in `/usr/lib/udev/rules.d/` and identify its package with `dpkg -S`.
   A `RUN` helper runs inside event processing and must return quickly.
   The rule's parent or consumer can be visible earlier than the service that caused the wait. [udev(7), Rules Files and RUN](https://www.freedesktop.org/software/systemd/man/latest/udev.html).

## Reproduce in a guest

- Boot a headless Debian testing guest with systemd as PID 1.
  Install Debian anacron 2.3-52 and udev 262.2-1 in the guest before measuring.
  Use the same QEMU configuration and clean disk overlay for every boot.
- Use Linux's [test_power driver](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/power/supply/test_power.c).
  If the Debian kernel has no `test_power.ko`, build it as an external module against headers for the exact guest release and install it under the guest's `/lib/modules/`.
  Run guest `depmod` and load it with `modprobe test_power ac_online=on usb_online=off` in an `ExecStartPre=` drop-in on `systemd-udev-trigger.service`.
  Confirm `Mains` and `1` from `/sys/class/power_supply/test_ac/type` and `online`.
- Add a stand-in under `local-fs.target.wants/` with `DefaultDependencies=no`, `Wants=systemd-udev-settle.service`, `After=systemd-udev-settle.service`, `Before=local-fs.target` and a oneshot `ExecStart=/usr/bin/true`.
  Record the monotonic time of `multi-user.target` or the login screen and the duration of settle.
- Run three boots with the rule and the consumer.
  Repeat on the same disk with `/etc/udev/rules.d/60-anacron.rules` linked to `/dev/null`, then with the stock rule and only the consumer link removed.
  The journal establishes whether settle ran and which command the worker launched.
  Read `systemctl show -p UserspaceTimestampMonotonic` and `systemctl show multi-user.target -p ActiveEnterTimestampMonotonic` through the guest's serial console.
  Subtract the first value from the second for time from systemd's userspace start.

## Repair and prove both power transitions

On systemd, `systemctl --no-block start` and `stop` enqueue the operations and return after submitting the jobs.
Keep the original `invoke-rc.d` rule on SysV installations, using `TEST=="/run/systemd/system"` and its inverse to select the route. [systemctl(1), Options, --no-block](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html#--no-block).

`SYSTEMD_WANTS` alone activates a unit when the tagged device becomes active.
That one property leaves AC disconnect and repeated changes to an existing device unhandled.
A device-lifetime design needs readiness transitions and a stop relationship.
`ConditionACPower=true` already guards service activation, including timer starts, and is evaluated when each start job runs. [systemd.device(5), The udev Database](https://www.freedesktop.org/software/systemd/man/latest/systemd.device.html#The%20udev%20Database), [systemd.unit(5), Conditions and Asserts](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html#Conditions%20and%20Asserts).

Install the patched package and repeat the red boot with the consumer enabled.
Use an anacrontab fixture with a pending delayed harmless job so the service remains observable.
Toggle `off`, `on` and `off` through `/sys/module/test_power/parameters/ac_online`.
Verify both the kernel's `online` attribute and the actual `anacron.service` state after each transition.
The service's own stop signal and timeout determine when a running job is released.

## Measured on Debian testing

One-core QEMU/KVM guest, Linux 7.3.5+deb14-amd64, systemd and udev 262.2-1. Times below are from the guest kernel clock to `multi-user.target`.

| Case | Three boot times (s) | Journal |
| --- | --- | --- |
| Debian 2.3-52, settle consumer enabled | 179.855, 179.821, 179.875 | All three log the 59 s worker warning, then the udev queue timeout. |
| The same package, rule masked | 17.251, 17.314, 17.171 | Settle succeeds on all three boots. |
| Debian 2.3-52, settle consumer removed | 23.488, 20.201, 20.528 | The service starts on all three boots, with no settle job or long-worker warning. |
| Patched package, settle consumer enabled | 16.523, 16.503, 16.829 | Settle succeeds and the AC off/on/off sequence gives inactive/active/inactive on every boot. |

Host loads differed across cases. The journal places the long wait between the mains event and the settle timeout on the stock boot and shows a completed settle before normal service startup on the patched boot.

## Traps

- **Symptom:** the red boot clears settle and then stays at Initial Setup with no proof output.
  **Cause:** the exported guest lacked `/etc/machine-id` and the first-boot wizard waited on the serial console.
  **Fix:** leave an empty `/etc/machine-id` in the guest template.
  **Found by:** the firstboot service start and terminal control sequences after settle failed. [machine-id(5), First Boot Semantics](https://www.freedesktop.org/software/systemd/man/latest/machine-id.html#First%20Boot%20Semantics).
- **Symptom:** systemd reports Docker while booting a disk in QEMU.
  **Cause:** Docker included `/.dockerenv` in its filesystem export.
  **Fix:** remove the marker from the extracted guest filesystem before building the disk.
  **Found by:** the guest's startup log and the exported tarball's file list.
- **Symptom:** the serial console prints thousands of udev debug lines before reaching the guest root.
  **Cause:** the debug kernel argument also enables logging in the initramfs.
  **Fix:** run the timed series with ordinary udev logging and print the filtered journal after reaching the target.
  **Found by:** the initramfs output in a serial preflight.
- **Symptom:** `mke2fs -d root.tar` fails while populating the image, although the option accepts tarballs.
  **Cause:** this e2fsprogs binary has no libarchive support.
  **Fix:** extract the tar in the disposable image-building container and pass the extracted directory to `mke2fs -d`.
  **Found by:** mke2fs's `you need libarchive to be able to process tarballs` diagnostic.
- **Symptom:** apt recognizes a newer local package and says its install pathname is not absolute.
  **Cause:** `--no-download` skips the acquisition step that supplies the local file path.
  **Fix:** allow apt to acquire the local file in a networkless container with dependencies already cached.
  **Found by:** comparing the same absolute .deb argument before and after dropping `--no-download`.
- **Symptom:** QEMU boot times vary by tens of seconds with identical guest inputs.
  **Cause:** CPU and storage contention affect the entire TCG boot.
  **Fix:** keep three timings and host load per variant and compare the udev wait directly alongside the time to the reached target.
  **Found by:** comparing the monotonic target timestamps and wait intervals across unchanged masked boots.
