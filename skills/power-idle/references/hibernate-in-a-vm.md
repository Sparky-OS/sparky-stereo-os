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

- Symptom: the journal shows "Waking up from system sleep state S4", "hibernation exit" and an ordinary running system, then the guest vanishes without a shutdown record.
  Cause: that is not a resume. The kernel entered hibernation, never wrote an image (no "Compressing and saving image data" line) and returned in place; the real event is whatever ended the VM afterwards.
  Fix: count a resume only when the boot id is unchanged after QEMU was restarted and the serial log has "Image successfully loaded".
  Found by: reading the serial log of a good cycle (it has "PM: Image saving progress" and "Image saving done") against the old journal, which had neither.
- Symptom: `systemctl hibernate` returns after a few seconds, the guest keeps running, the kernel log says `virtio-fs: suspend/resume not yet supported` and `virtio_pci_freeze returns -95`.
  Cause: a virtio-fs share (vhost-user-fs device) refuses to freeze, so the whole hibernation is abandoned.
  Fix: test without the share; the guest stays up and nothing resets (watched 200 s with the share, an HDA codec, xhci and a tablet attached).
- Symptom: with Debian's stock 7.2.12 every second hibernation in a row stalls for about 150 s ("task kworker blocked ... virtio_gpu_queue_fenced_ctrl_buffer ... virtio_gpu_primary_plane_update") and the following resume never answers ssh; 7.3.1-stereo3d16 and 7.3.0-rc1-stereo3d did not, in ten cycles each.
  Cause: not found; the display commit waits for a fence the (new) virtio-gpu device never signals after a resume. A fresh boot between cycles avoids it.
  Fix: none needed on the edition's kernel; do not read this stall as a reset.
- Symptom: the harness waits for QEMU to exit and times out.
  Cause: a second QEMU left running holds the forwarded port, or the first container never stopped.
  Fix: one container per disposable VM, named, stopped by name when a cycle ends; the harness kills a guest that does not answer after a resume instead of looping.
- A lock-up that never shows up in `-no-reboot` runs is not a QEMU or firmware reset: with `-no-reboot` the QMP socket reports the reason of every exit.
