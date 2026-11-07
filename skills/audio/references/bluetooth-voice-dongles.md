# Bluetooth voice (HFP) over a USB dongle: telling a dongle that cannot carry voice from a profile or codec problem

Written 2026-11-07 (ORDER 133). Versions measured: Linux 7.3.1, BlueZ 5.87, PipeWire and WirePlumber 1.6.9 and 0.5.18.

## Which layer refuses

Read the layers in this order, each with one command.

1. **The controller's buffers.** `btmon -w FILE` before the adapter powers up, `btmon -r FILE` afterwards: the reply to `Read Buffer Size` lists `SCO MTU` and `SCO max packet`. `hciconfig -a hci0` shows what the kernel kept (`SCO MTU: 48:0`).
2. **The kernel's decision.** `hci_cc_read_buffer_size()` (net/bluetooth/hci_event.c) sets `sco_pkts` from the reply, applies `HCI_QUIRK_FIXUP_BUFFER_SIZE` (64 and 8), then sets `sco_pkts = 0` when `read_voice_setting_capable()` is false. btusb sets `HCI_QUIRK_BROKEN_READ_VOICE_SETTING` on every fake CSR clone it detects (`btusb_setup_csr()`: HCI revision different from the LMP subversion). `hci_connect_sco()` then returns `-ECONNREFUSED` before any HCI command is sent. Measured on a clone (USB 0a12:0001, bcdDevice 88.91, LMP subversion 0x2312): the controller answered `SCO MTU: 48  SCO max packet: 16` and the kernel logged `SCO MTU: 48:0`, so the zero buffers were the kernel's rule and not the chip's report.
3. **The connect.** PipeWire's native backend logs `sco_do_connect: connect(): Connection refused`; in btmon no `Setup Synchronous Connection` command appears. With a working buffer count the command appears and `Synchronous Connect Complete` (link type eSCO, air mode CVSD) follows.
4. **The USB side.** `lsusb -v -d VID:PID`: interface 1 must have isochronous alternate settings. mSBC (transparent data) needs alternate setting 6; PipeWire logs `bluetooth host adapter does not support USB ALT6` and offers no mSBC profile.
5. **The profile and codec.** `pw-dump` lists the card's profiles (`headset-head-unit` on the gateway side, `audio-gateway` on the hands-free side in PipeWire 1.6). A missing profile is a profile problem; a profile whose transport fails is layer 3 or 4.

## The two-machine test with no person wearing a headset

The gateway is a disposable VM with the adapter (QEMU `usb-host`, vendor and product), BlueZ and PipeWire. The headset is a second machine with a real adapter. A known tone is the headset's microphone, and the gateway records the headset's microphone and checks the tone.

- Gateway: `bluetoothctl --agent NoInputNoOutput` fed from a fifo; a watcher answers `yes` to every `(yes/no)` prompt. Roles `[ hfp_ag hsp_ag ]`. Select the card profile, `pw-record --target bluez_input.ADDR.N`, `pw-play --target bluez_output.ADDR.N` for the other direction.
- Headset: roles `[ hfp_hf hsp_hs ]`, trust the gateway as soon as it is paired, select the profile `audio-gateway`, play the tone into the card's sink.
- Check: `bench/tone-check.py WAV --freq HZ` passes only when the loudest peak is within the tolerance, the level is above the floor and the peak holds enough of the energy. Prove the checker with a pure tone (pass), the wrong frequency, silence, a quiet tone and noise (all must fail).
- Control: the same run on the unpatched kernel must show the refusal of layer 3.

## Traps met

- **Symptom:** the first command times out (`command 0x1001 tx timeout`, `CSR: Local version failed (-110)`) and every retry does too. **Cause:** these clones answer only after the device has been suspended once; a USB reset (QEMU's default when the guest resets the port) undoes it, and the guest cannot suspend the host device. **Fix:** `-device usb-host,vendorid=...,productid=...,guest-reset=false`, and start the guest only when the host driver has finished its own retries (powered, idle for 10 s). **Found by:** the guest's `btmon` showing nine `Read Local Version` commands and no event.
- **Symptom:** the headset side shows no Bluetooth devices in `pw-dump` and advertises no hands-free profile. **Cause:** WirePlumber's Bluetooth monitor waits for an active seat; a desktop session without one has none (`monitor.bluez.seat-monitoring`). The login screen's own WirePlumber may hold the audio gateway profile, and oFono, when running, holds the hands-free profile before PipeWire. **Fix:** a drop-in with `support.logind = disabled` and `monitor.bluez.seat-monitoring = disabled` in the `main` profile, stop the other holders for the test and put them back. **Found by:** `bluetoothctl show` listing the profile UUIDs (`0000111e` hands-free, `0000111f` audio gateway) before and after each change.
- **Symptom:** pairing stops at `Request authorization` or `Authorize service` and the link drops. **Cause:** bluetoothctl's agent waits for a typed answer. **Fix:** the fifo watcher above, and `trust` the peer as soon as it is paired so services need no authorization.
- **Symptom:** one run in three finds no `hci0` in the guest. **Cause:** the dongle re-enumerated on the host (new device number) while the container held the old node. **Fix:** find the node by vendor and product in sysfs for every start, and retry the guest once or twice.
- **Symptom:** `btmon > file` is empty or cut. **Cause:** stdout buffering when the guest powers off. **Fix:** `btmon -w file.snoop` and decode with `btmon -r` afterwards.
- **Symptom:** the temperature gate reads 66 C on an idle machine. **Cause:** the battery sensor is among the hwmon files. **Fix:** read only the `k10temp` (or the CPU package) sensor.
