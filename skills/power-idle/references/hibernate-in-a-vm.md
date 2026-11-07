# Hibernate and resume in a disposable VM

How to tell whether a guest that "reset itself after resume" was reset by the kernel, by QEMU, by the firmware or by the harness.
Measured on 2026-11-07 with QEMU 10.x, OVMF 4M, a q35 guest with KVM, kernels 7.3.1-stereo3d16, 7.3.0-rc1-stereo3d and Debian 7.2.12.

## Recipe

1. Work on a copy-on-write overlay of the development image (`qemu-img create -f qcow2 -F qcow2 -b BASE overlay.qcow2`) and a copy of the UEFI variable store, so nothing of the original is touched.
2. Give the guest a real resume area: a second virtio-blk disk used as swap, `RESUME=UUID=...` in `/etc/initramfs-tools/conf.d/resume`, then `update-initramfs -u -k all`.
   zram cannot hold the image, and a guest with only zram refuses or fails the hibernation.
3. Put the kernel messages on a serial console that survives power-off: `console=tty0 console=ttyS0,115200n8 loglevel=7 ignore_loglevel no_console_suspend printk.time=1` on the guest command line and `-chardev file,id=ser,path=serial.log,append=on -serial chardev:ser` on QEMU.
   One file across all boots; note its size before each boot so every cycle gets its own slice.
4. Start QEMU with `-no-reboot` (a guest reset or triple fault ends QEMU instead of rebooting the guest), `-qmp unix:SOCK,server=on,wait=off` and read its events with a script: `SUSPEND_DISK` then `SHUTDOWN {reason: guest-shutdown}` is a normal hibernation, `SHUTDOWN {reason: guest-reset}` or `RESET` is a guest reset, `WATCHDOG` is a firmware watchdog, `GUEST_PANICKED` a panic.
5. A cycle: plant a nonce in `/run` and a transient unit (`systemd-run --unit=witness sleep infinity`), run `systemctl hibernate`, wait for QEMU to exit (ACPI S4 is a guest power-off to QEMU), start QEMU again with the same disks and variables, then check the nonce, the unit and the boot id.
   Equal boot id plus the nonce proves a resume from the image rather than a fresh boot.
6. Watch the resumed guest for at least two minutes (ssh `cat /proc/uptime` every 5 s; a container or QEMU that disappears is a reset, four failed polls with QEMU alive is a hang) before the next hibernation.
7. Repeat at least ten times per kernel, and run the same guest image with Debian's stock kernel: if only one kernel misbehaves it is the kernel; if all do, suspect QEMU, OVMF or the guest set-up.

## Traps met

- Symptom: the journal of the machine that was hibernated shows `hibernation entry`, `Normal pages needed`, `Waking up from system sleep state S4`, `Basic memory bitmaps freed`, `hibernation exit` and no `Compressing and saving image data`, and Cushion Swap logs `after resume: AREA was empty, switched off again`; it looks like a hibernation that returned in place and wrote nothing.
  Cause: it is the RESUMED side of a good cycle. The image-writing lines are printed after the snapshot was taken, so the resumed system never contains them (they exist only on the serial console of the machine that went down); everything after `Normal pages needed` in that journal is the restored kernel waking up. A gap of tens of seconds in the timestamps is the time the machine was off. The hook's "was empty" only says no swapped-out pages were in the area: hibernation images are not counted as swap use.
  Fix: judge a cycle by the boot id (unchanged) and a witness process (alive) across the restart, and by `PM: Image saving done` on the serial console of the going-down boot; never by the absence of write lines in the journal.
  Found by: the October lane's own verify record (boot id unchanged, witness alive) against its journal, then the same journal shape in a good cycle here.
- Symptom: a hibernation that really returns in place leaves `hibernation exit` with `PM: failed to freeze` or another error before it, and `systemctl hibernate` fails.
  Cause: a device refuses to freeze (see the virtio-fs trap).
- Symptom: `systemctl hibernate` returns after a few seconds, the guest keeps running, the kernel log says `virtio-fs: suspend/resume not yet supported` and `virtio_pci_freeze returns -95`.
  Cause: a virtio-fs share (vhost-user-fs device) refuses to freeze, so the whole hibernation is abandoned.
  Fix: test without the share; the guest stays up and nothing resets (watched 200 s with the share, an HDA codec, xhci and a tablet attached).
  Found by: the serial console of a run with `-chardev socket` + `vhost-user-fs-pci`; the in-place return, unlike a good resume, has `failed to freeze` and no `Image saving done`.
- Symptom: with Debian's stock 7.2.12 every second hibernation in a row stalls for about 150 s ("task kworker blocked ... virtio_gpu_queue_fenced_ctrl_buffer ... virtio_gpu_primary_plane_update") and the following resume never answers ssh; 7.3.1-stereo3d16 and 7.3.0-rc1-stereo3d did not, in ten cycles each.
  Cause: not found; the display commit waits for a fence the (new) virtio-gpu device never signals after a resume. A fresh boot between cycles avoids it.
  Fix: none needed on the edition's kernel; do not read this stall as a reset.
- Symptom: the harness waits for QEMU to exit and times out.
  Cause: a second QEMU left running holds the forwarded port, or the first container never stopped.
  Fix: one container per disposable VM, named, stopped by name when a cycle ends; the harness kills a guest that does not answer after a resume instead of looping.
- A lock-up that never shows up in `-no-reboot` runs is not a QEMU or firmware reset: with `-no-reboot` the QMP socket reports the reason of every exit.

## The edition's own path in the VM (2026-11-07)

Set the guest up as the installer leaves a machine, then run the same cycle:

- Swap partition or disk: `UUID=... none swap sw,noauto 0 0` in fstab (the area stays off at boot) and `RESUME=UUID=<that UUID>` in `/etc/initramfs-tools/conf.d/resume`.
  Cushion Swap switches the area on in the sleep unit's ExecStartPre (`hibernation: DEVICE switched on for the image`) and off again after the resume.
- Swap file: `fallocate -l 5G /swapfile; chmod 600; mkswap`, the same noauto fstab line, `RESUME=UUID=<root filesystem UUID>` and `RESUME_OFFSET=<first physical block from filefrag -v>` in the same conf.d file, then `update-initramfs -u -k all` (Cushion's initramfs hook turns the offset into a `resume_offset` snippet that initramfs-tools 0.151 would ignore).
  Resume of a swap file reads it through the disk image, so allow 30 to 90 s before ssh answers.
- PowerDevil's own path, headless: as the session user, `busctl --user call org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement/Actions/SuspendSession org.kde.Solid.PowerManagement.Actions.SuspendSession suspendToDisk`; logind then logs `hibernate requested from client PID N ('org_kde_powerde')`.
- Suspend then hibernate: put `HibernateDelaySec=40s` in `/etc/systemd/sleep.conf.d/`, run `systemctl suspend-then-hibernate`; QEMU's RTC alarm wakes the S3 guest, systemd-sleep hibernates and QEMU exits.
  With a 25 s delay the RTC woke the guest 0.5 s early, systemd-sleep took it for a wake by the user and returned without hibernating: use at least 40 s in a VM.
- Traps: `systemctl hibernate` over ssh as the session user is refused by polkit (`Access denied ... interactive authentication`): use `sudo` or the PowerDevil call; `journalctl -S -3min` spans boots of a disposable guest, so read `-b 0` or a named boot; a guest that went through virtio-fs gets `hibernation exit` and the problems engine's notice `The system service System Hibernate (systemd-hibernate.service) failed ... exit status 1`, which does not name the device.

## Secure Boot and the kernel-soul bench

The bench in `tools/hibernate-bench` runs the signed edition kernel under OVMF Secure Boot with a software TPM.
Build its image with the build repository's `tools/https-only-build.sh` (the Dockerfile's apt step needs the two mounts), unpack the image and headers packages, and give the bench the public certificate only:

```
run-in-docker.sh -m PKG:PKG:ro -m HDR:HDR:ro -m CERTDIR:/sb:ro --kernel PKG/boot/vmlinuz-REL --ksrc HDR/usr/src/linux-headers-REL \
    --modules-dir PKG --kernel-signed --db-cert /sb/CERT.der run policy hibernate
```

`sbverify --cert CERT.pem vmlinuz-REL` first proves the image carries that signature.
Expect `SecureBoot=1`, `lockdown: [none]`, unsigned and unknown-key modules refused, the enrolled key's module loaded, `hibernate_entered`, `hibernate_resumed`.
The certificate shows up in the log as `Loaded X.509 cert '<name>'` in the platform keyring.
