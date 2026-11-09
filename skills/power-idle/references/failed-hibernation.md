# A failed hibernation: the reason, read from that attempt

`systemctl hibernate` (and PowerDevil, and the lid) can fail, return in place and leave the computer running.
The edition's engine, `sparky-stereo-problems` 0.2.1, says why from the attempt's own journal; this is the recipe, the kinds and the traps.

## Recipe

1. The three units are `systemd-hibernate`, `systemd-suspend-then-hibernate` and `systemd-hybrid-sleep` (the battery default is suspend-then-hibernate, `HibernateDelaySec=2h`).
   A failed one triggers the engine's top-level `OnFailure=` handler (`sparky-stereo-problems service-failed`); for these units it now reads the reason instead of writing "it stopped with exit status 1, Repair starts it again".
2. Read it by hand the same way:
   `journalctl -b _SYSTEMD_INVOCATION_ID=ID -o json` for systemd-sleep's lines (the ID is `InvocationID` of the failed unit, or the `INVOCATION_ID` of its "Starting" line);
   `journalctl -b _TRANSPORT=kernel --since T0 --until T1 -o json` for the kernel's, between that invocation's first and last line.
3. Fields that exist, so no text scraping where one does: systemd-sleep's `SLEEP_STOP` line is `MESSAGE_ID=8811e6df2a8e40f58a94cea26f8ebf14` with `SLEEP=hibernate` and `ERRNO=95` (priority 3 on failure); a kernel line from a device has `_KERNEL_SUBSYSTEM=pci` and `_KERNEL_DEVICE=+pci:0000:00:05.0`.
   The device name ("virtio-pci 0000:00:05.0"), the driver callback and the error number are only in the message text (`PM: failed to freeze async: error -95`, drivers/base/power/main.c `pm_dev_err`).
4. Each kind, with the line that says it and its source, is in the package's README (`sparky-os/packages/sparky-stereo-problems/README.md`, "A failed hibernation says why"): lockdown, a virtio-fs share, a device that refused, programs that would not freeze, no swap area big enough, no resume device, the kernel's or systemd-sleep's own error line, nothing found.
5. Test with real journals: write an export (`__REALTIME_TIMESTAMP`, `_BOOT_ID`, the fields above), `systemd-journal-remote -o DIR/x.journal --split-mode=none EXPORT`, and point the engine at the folder with `SPARKY_STEREO_PROBLEMS_JOURNAL=DIR`.
   The suite is `tests/sleep-tests.sh` (red on 0.2.0: 43 of 53 checks fail; green on 0.2.1: 53 of 53), `tests/systemd-tests.sh` runs the handler and the ExecStopPost under a real systemd.
6. The real failure, in the VM of [hibernate-in-a-vm.md](hibernate-in-a-vm.md) with a virtio-fs share (`FS` argument of the boot script: virtiofsd on a folder, `vhost-user-fs-pci`, a memfd shared memory backend), mounted in the guest: `systemctl hibernate` returns after about 8 s, the guest keeps running, and the notice must name `virtio-pci 0000:00:05.0` and the mounted share.
   Then the same VM without the share: hibernate, resume (boot id unchanged, witness alive) and no sleep problem listed.

## Traps met

- Symptom: after a failed hibernation the Problems page says "The system service System Hibernate failed: it stopped with exit status 1. Repair starts it again", and Repair hibernates again.
  Cause: the engine's handler treats every failed unit alike; for a cause that stays (a virtio-fs share, a locked-down kernel, no swap) a retry fails the same way every time, and for a working one it puts the computer to sleep again.
  Fix: engine 0.2.1 reads the cause and offers no repair where the cause stays; a retry is offered only for "programs would not freeze", "the kernel's own line", "systemd-sleep's line only" and "nothing found", and the text says what Repair does.
  Found by: lane 32's guest journal (`in-place-failure-person-told.txt`) showed the old text after a real `virtio_pci_freeze returns -95`; reproduced in the VM with the 0.2.0 engine.
- Symptom: a laptop on suspend-then-hibernate wakes with no notice although its hibernation failed.
  Cause: systemd-sleep.c tries `suspend` when the hibernate step fails ("Couldn't hibernate, will try to suspend again.") and the service ends with exit 0, so `OnFailure=` never runs.
  Fix: a drop-in on `systemd-suspend-then-hibernate.service` and `systemd-hybrid-sleep.service` runs `sparky-stereo-problems sleep-attempt %n` in `ExecStopPost=` (`$SERVICE_RESULT`, `$INVOCATION_ID` are passed to it, systemd.service(5)); it keeps the reason without a `unit` field, because a record with a `unit` is ended as soon as the unit is not `failed`.
  Found by: reading systemd v262 `src/sleep/sleep.c`, and a fixture whose last line is a successful `SLEEP_STOP` after an error one.
- Symptom: a freeze failure of an earlier attempt, or a kernel line after the attempt, shows up as this attempt's reason.
  Cause: the kernel's lines belong to no unit; reading `_TRANSPORT=kernel` of the boot attributes all of them.
  Fix: bound them by the invocation: its first journal line to its last plus 5 s.
  Found by: the fixtures `older-attempt-only` and `after-end`.
- Symptom: in the journal the kernel's lines are listed after systemd-sleep's "Failed to put system to sleep" line.
  Cause: journald stamps them when it reads /dev/kmsg, after the write to /sys/power/state returned.
  Fix: end the window after the invocation's last line, never at the SLEEP_STOP line.
- Symptom: `journalctl -x` in German explains the notice with English words in the middle ("Der Computer konnte nicht hibernate: ...").
  Cause: a journal catalog fills `@SPARKY_ARG_A@` from the event's fields, and the engine writes the nested messages (the operation, the reason) in English into them.
  Fix: none in the catalog; the Problems page, the notifier and `sparky-stereo-problems list` render the nested messages in the person's language.
- Symptom: the fixture suite cannot make a kernel line.
  Cause: a container cannot write /dev/kmsg; `logger` and `systemd-cat` make `_TRANSPORT=journal` or `syslog` entries.
  Fix: journals imported with `systemd-journal-remote` keep every field of the export, `_TRANSPORT=kernel` and `_KERNEL_DEVICE` included.
- Symptom: a unit that logs as systemd-sleep (`SyslogIdentifier=systemd-sleep`, `<3>` prefix) is the way to test the handler under a real systemd in a container.
  Cause/Fix: the real systemd-sleep needs a kernel to hibernate; the engine only reads the identifier, the priority and the invocation ID.
