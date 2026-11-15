# A USB camera that delivers nothing in one format

**For kernel contributors:** diagnose a format-specific empty stream, test the real decoder without hardware and prepare the separate camera comparison.
Written 2026-11-14 from ORDER 569's source audit, synthetic QEMU proof and supplied hardware measurements.

## Working recipe

1.
   Record the USB ID, descriptors and endpoint type.
   Compare YUYV with MJPEG, and keep an independent isochronous camera as a control.
   Do not begin by changing unrelated quirks.
2.
   Capture the negotiated UVC probe with usbmon and trace payload decoding.
   Keep frame counts, `bytesused` and errors, without private camera pictures.
3.
   Compute image bytes plus headers.
   Check whether the negotiated maximum payload ends inside a full bulk URB.
4.
   Search the current media tree, linux-media and review before editing.
   Use the newest confirmed technique, with credit.
   Restrict a noncompliance workaround to known devices and validate the next header before splitting.
5.
   Test the actual decoder in KUnit in a virtual machine inside a container, red before green.
   Build against the target kernel's published headers.
   A person then compares the module on hardware; synthetic evidence does not qualify the physical camera.

## How the cause was found

Realtek `0bda:5722` in a Sony VAIO Duo 13 streams through a bulk endpoint.
YUYV 640×480 negotiates `dwMaxVideoFrameSize=614400` and `dwMaxPayloadTransferSize=119296`.
The driver caps a bulk URB at 32 USB packets, 16384 bytes here. usbmon recorded:

```
37 × 16384 + 8264 = 614472 = 614400 image bytes + 6 × 12 header bytes
```

The payloads follow one another, so a header falls inside a full URB.
The original decoder resumed parsing at the next URB and traced `Dropping payload (out of sync)`.
A compressed frame smaller than one payload can therefore work while uncompressed frames never complete.
Isochronous input uses a separate decoder.

Julian Meyer identified this for `0bda:579f` in [2020 v3](https://lkml.iu.edu/2004.2/06143.html).
Muhammad Waleed Badar's [2026 v3](https://lkml.iu.edu/hypermail/linux/kernel/2611.0/04453.html) adds the device quirk after Hans de Goede's review and checks the next header after Ricardo Ribalda's trailer-data concern.
These are unmerged submissions, not upstream acceptance.
Check current subsystem policy before preparing contact; follow [contrib-kernel](../../contrib-kernel/SKILL.md).

The carried quirk covers the two reported IDs.
It splits only at a positive remaining payload size with a complete next header: EOH set, length within the available bytes and large enough for its PTS/SCR fields.
An unrecognised remainder stays intact and produces a once-only warning.
Bound scheduled copies by `copy_operations` capacity; mark and drop excess data.
Every iteration consumes input even when it schedules no copy.

## Test without hardware

The build repository's `kernel/tests/uvc-bulk/README.md` describes the fixture.
Apply group 02 patch 0011 alone to vanilla Linux 7.3.1 for red, then 0010 for green.
Run inside an isolated container with core dumps disabled, four CPUs and no physical USB devices.
From the kernel source tree:

```
python3 tools/testing/kunit/kunit.py run --arch=x86_64 \
  --build_dir="$TEST_OUT" \
  --kunitconfig="$RECIPE_ROOT/kernel/tests/uvc-bulk/uvc-bulk.kunitconfig" \
  --make_options CC=gcc-16 --make_options HOSTCC=gcc-16 --jobs=4 \
  --timeout=180 --qemu_args="-accel tcg -smp 2" 'uvc-bulk-payload*'
```

Select compiler versions actually present in the chosen container.
Retain parsed status and raw KTAP: raw-output mode alone can exit successfully despite a failing case.
Compare every byte of two 614400-byte patterned images, alternating FID, from the reported 119296-byte payload shape.
Unpatched fails frame length, contents and completion; the quirk passes eleven cases.
The supplied generic hardware-tested reference also passes the same image comparison, but predates the trailer-safe form.

Controls: short packet; maximum a multiple of URB size; maximum zero; isochronous; small MJPEG; trailer without a valid header; quirk off; inconsistent PTS/SCR header length; stale oversized payload counter; full async-copy array.
Inspect error/state and queue references as well as byte counts.
The fixture executes scheduled copies and releases references without submitting an URB to hardware.

## Traps: symptom, cause, fix and how found

* **An interface rebind leaves the camera silent.** The observed camera kept state beyond that interface.
  Close its users and have the person rebind the whole USB device or reconnect it, using the confirmed path.
  Completion traffic before and after the two rebind types exposed the distinction.
* **The quirks parameter does not help.** Existing flags do not implement inside-URB payload boundaries.
  The flag definitions, decoder trace and usbmon arithmetic identify the missing path; unrelated flags cannot fix it.
* **Module unloading breaks the session sound bridge.** Masking the person's sound service to free module users changes unrelated routing.
  Close camera clients normally and plan replacement with the person at the bench; never mask session sound as an unload trick.
  The bridge disappearing after the mask identified the cause.
* **Red faults in `usb_hcd_get_frame_number`.** Image bytes misread as a header can claim SCR.
  A fake stream without a USB controller is invalid.
  Supply a stopped test controller and real clock ring, then require normal frame assertions to fail.
  The guest backtrace found the fixture fault; an oops alone was not accepted as red evidence.
* **Checkpatch floods a read-only-tree log.** It writes a CamelCase cache.
  Use the disposable writable source tree and fix strict alignment checks.
  The first `.checkpatch-camelcase.date` error identified the cause.
* **Clang rejects a module built with GCC-prepared headers.** The published configuration keeps GCC flags such as `-fconserve-stack` and `bounds-strict`.
  Use the matching GCC for that module.
  Configure an independent reduced Clang KUnit tree for a second compiler; do not edit published-header flags and call that the target-header proof.

Version 1.1's restricted quirk builds against 7.3.1-stereo3d16 headers and still needs a camera test.
Only the generic reference has the measured YUYV hardware result at 640×480, 1280×720 and 1920×1080.
Keep those claims separate.
