# A VKMS connector lists the 3D modes of its EDID: the steps, and how to check each one

Use it when a configfs VKMS connector reads an EDID that declares HDMI 3D (`edid-decode` shows `3D present`) and the connector lists 2D modes only.
Every step has a check that fails by itself, so the step that loses the modes shows.

## The recipe

1. **The EDID is right.** `edid-decode --check EDID.bin` ends with `EDID conformity: PASS` (a real television's EDID may not pass; keep it as a second case). Its HDMI Vendor-Specific Data Block must show `3D present` and the structures you expect (HDMI 1.4a, Appendix H, Table H-2).
2. **The expectation comes from the EDID, never from the kernel.** `edid/expect-from-decode.py DECODE.txt` turns edid-decode's text into the stereo formats a connector should list (`1920x1080@24 fp`, `sbs-half`, `tab`, `line-alt`, `sbs-full`, `l-depth`, `l-depth-gfx`). Make a 2D-only twin with `edid/make-2d-edid.py IN.bin OUT.bin`: it must list none.
3. **The kernel reads the EDID.** In the guest, make the device and give the connector its type, its EDID in one `write()`, and `edid_enabled`, all before `enabled`. Then `wc -c /sys/class/drm/cardN-HDMI-A-1/edid` is 256 for a base block and one extension.
4. **The parser adds the stereo modes, and the probe helper keeps them.** List the modes the way a compositor does, with `DRM_CLIENT_CAP_STEREO_3D` set: `src/lsmodes.c` of the bench prints every mode as `WxH@R layout` and compares the stereo formats with the expectation file (`lsmodes /dev/dri/cardN NAME EXPECT`; `NOCAP=1` leaves the capability out, and must list no stereo mode). A mode count of 2D modes only is the symptom of this document.
5. **If the stereo modes are missing, ask the probe helper why.** `echo 0x4 > /sys/module/drm/parameters/debug`, list the modes again, and read `dmesg | grep "Rejected mode"`: each dropped mode is printed with the name of its status. `(NO_STEREO)` is `drm_mode_validate_stereo()` in drivers/gpu/drm/drm_probe_helper.c: the connector has no `stereo_allowed` (frame-sequential modes are judged by `stereo_frame_sequential_allowed` instead). Other statuses name other filters (`NO_INTERLACE`, `NO_DBLESCAN`, and the driver's own `mode_valid`). If nothing is rejected and nothing is listed, the parser added nothing: read the EDID again (steps 1 and 3).
6. **The frame of each layout is composed and written back.** `stereo-wb-test` (the bench's) shows each listed mode with a known left and right eye and reads the writeback buffer back pixel by pixel; the KUnit suites `vkms-stereo`, `vkms-stereo-whole-spec` and `vkms-stereo-no-edid` check the frame sizes (`vkms_frame_size()`: vdisplay plus one vtotal for frame packing, three for L + depth + graphics + graphics-depth, twice the lines for line alternative, twice the width for side by side (full)) and a connector without an EDID.
7. **Red and green.** The same guest, the same EDIDs, on the kernel without the change (24 modes rejected with `NO_STEREO` for the bench EDID) and with it (none rejected, every expected format listed, the 2D-only twin and the default device unchanged).

## Interlaced modes: carried and marked

An interlaced timing needs its scan type beside its dimensions, refresh rate and stereo structure.
The notation is `1920x1080i`; a 60 Hz interlaced timing has 60 fields per second and 30 complete frames per second, as the kernel’s [DRM mode name and refresh helpers](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/gpu/drm/drm_modes.c?h=v7.3) represent it.
Keep the scan type separate from the stereo packing: an interlaced timing may also carry frame packing.
Check the applicable CTA timing and HDMI® structure clauses in the edition being used; a missing local clause is an explicit evidence gap, never a formula supplied from memory.

Follow the flag through these boundaries before changing a label:

1. Decode the EDID independently with `edid-decode`, preserving the `i` and the per-VIC stereo entries.
   Use `edid/expect-from-decode.py --include-interlaced DECODE.txt` for a bench that supports interlace.
   Its default deliberately keeps only progressive formats for the ordinary VKMS bench.
   A television can declare frame packing on VIC 5 and VIC 20 without declaring 1080p60 frame packing.
2. Compare the kernel's `drmModeModeInfo.flags` with KWin's `DrmConnectorMode::nativeMode()` and its `OutputModeline::flags()`.
   In KWin 6.7.4 +stereo3d54, the native mode retains `DRM_MODE_FLAG_INTERLACE`, but `flagsForMode()` in `src/backends/drm/drm_connector.cpp` copies only the preferred and stereo flags into `OutputModeline`.
   Its refresh calculation already doubles the frame rate for interlaced timings.
3. Trace the output-device mode's flags through the protocol XML, KWin's `OutputDeviceModeV2InterfacePrivate::bindResource()`, libkscreen's `WaylandOutputDeviceMode` and `WaylandOutputDevice::updateKScreenModes()`.
   Check both protocol version gates and the client's registry bind version.
4. Preserve the flag in libkscreen's `Mode` clone, equality and config serializer, including its D-Bus deserializer.
   Check `WaylandOutputDevice::modeName()` and `Doctor::outputs()`: they construct names independently.
5. Include scan type in KScreen's `OutputModel` resolution identity, current index, refresh filtering and selected-mode matching.
   Changing only the displayed string leaves progressive and interlaced modes of equal size and rate merged or selects the other one.
6. Prove selection separately from naming: inspect the native mode and mode blob, the stereo frame geometry and a refused commit's visible failure.
   Run the installed doctor and KCM, compare every row with the EDID-derived expectation, and retain a progressive-only control against the previous packages.

Do not use the stock VKMS list as proof that a television declares no interlaced modes.
VKMS rejects interlace with `NO_INTERLACE`; use an isolated mock DRM test for flag propagation, and a separately qualified guest path for installed compositor behavior.
A mock passing a commit does not establish physical interlaced scanout.

Traps:

- **Symptom:** a 1080i 3D mode reads as 1080p.
  **Cause:** the native DRM mode carries interlace, but the compositor's general mode object and its clients lose it; independent formatters then print only width and height.
  **Fix:** carry scan type across every boundary above and mark the height with `i`, in 2D and 3D alike.
  **Found by:** decoding the EDID first, then comparing `flagsForMode()` with the retained native mode and following each formatter.
- **Symptom:** a proposed interlace test lists only progressive formats.
  **Cause:** VKMS filters interlaced timings before the compositor receives them, and the ordinary EDID expectation script filters them too.
  **Fix:** read the kernel's rejection status, choose the test layer explicitly and enable `--include-interlaced` for its expectation.
  **Found by:** the driver's interlace policy, the `NO_INTERLACE` probe status and the expectation script's `add()` filter, rather than the displayed mode count.

The +stereo3d54 trace was followed by installed candidate tests in an isolated virtual backend: all 41 EDID-derived logical timing rows matched doctor and the KCM, including ten interlaced rows.
The progressive-only control retained the same 21 rows, labels and order.
Selecting 1080i60 frame packing retained the interlaced frame-packing identity, and selecting progressive 2D remained possible.
This qualifies the tested native-flag boundary and installed protocol/client presentation.
It does not qualify a notebook's physical interlaced scanout, kernel-generated duplicate or fractional timings, or a physical DRM commit.

### Capturing the real KCM list without a physical display

Use [the test observer](../scripts/kcm-mode-list-observer.cpp) inside the isolated container, with the installed KCM and its own virtual compositor session:

```sh
ulimit -c 0
c++ -std=c++23 -O2 -fPIC -shared kcm-mode-list-observer.cpp \
  $(pkg-config --cflags --libs Qt6Core Qt6Gui Qt6Qml Qt6Quick Qt6Widgets Qt6QuickWidgets) \
  -o "$scratch/kcm-mode-list-observer.so"
LANG=C.UTF-8 QT_QUICK_BACKEND=software \
  KSCREEN_MODE_CAPTURE_OUT="$scratch/kcm-list" \
  LD_PRELOAD="$scratch/kcm-mode-list-observer.so" kcmshell6 kcm_kscreen
```

Expect `kcm-list.json`, `kcm-list-resolutions.png` and `kcm-list-refresh.png`.
The JSON enumerates the real resolution and refresh controls; the images show their open lists.
This observer stages resolution changes in the KCM and exits without pressing Apply.
Use a disposable home and compositor, never a person's session.
It expects the English `Hz` label.
Inspect each PNG before counting it as a capture.

A Qt Quick KCM hosted by `kcmshell6` can live in a `QQuickWidget`.
Its internal `QQuickWindow` is not a visible top-level window.
For a headless software-rendered capture, inspect visible `QQuickWidget` instances, follow `quickWindow()` and the visual `childItems()` tree, and use the containing widget's `grab()` for the PNG.
Read a ComboBox through its public `count` and `textAt(index)` API; its `model` variant need not be a string list.
Open its `popup` before capture.
A test observer can enumerate resolutions and each resolution's refresh entries by setting the ComboBox index and emitting `activated(index)`, without pressing Apply.
Keep this observer outside the shipping package and compare its observations with the EDID expectations.
This captures the rendered installed KCM, not DRM scanout or stereo eye delivery.
A virtual-backend fixture likewise tests installed protocol/client presentation; it cannot establish physical kernel EDID enumeration or field timing.

### Further flag propagation traps

- **Symptom:** a disconnected display loses its legacy interlaced choice after settings are merely loaded and saved. **Cause:** the writer stamps a previously unknown scan type as known progressive before the display can be matched. **Fix:** omit the new scan marker until scan type is known; test load/save without querying outputs, then reconnect and restore. **Found by:** restart cases that passed directly but failed after an intervening disconnected store.
- **Symptom:** a legacy protocol test passes although no current-mode event is delivered after selecting an interlaced virtual mode. **Cause:** its cached mode already equals the expected fallback; a new scan flag also prevents the old-client base-mode search from matching. **Fix:** count current-mode events as well as checking their value; include scan type among non-layout flags and require the fallback base to have the same scan type. **Found by:** the event-count assertion fails for interlaced clients at versions 21 and 23 while progressive and newer clients pass.


- **Symptom:** a protocol configure check accepts an old XML file although mode flags lack interlace. **Cause:** the same XML already contains `ized3d_mode.interlaced`, an unrelated output format. **Fix:** inspect the mode `flags` enum or match the exact new entry and value; require it in edition builds. **Found by:** comparing the generated mode flag macro with the XML enum containing the earlier word match.
- **Symptom:** an interlaced choice saved before the new flag falls back after an upgrade. **Cause:** modeline matching compares the complete flags, while the old saved mode omitted scan type. Virtual-mode restoration also treated the new bit as part of its packing. **Fix:** mark newly saved scan types as known; for legacy choices prefer the exact existing match, then recover the interlaced counterpart. Keep interlace out of the layout mask and retain it in base-mode matching. **Found by:** tracing saved-mode equality and running restart tests for 2D, frame packing and virtual anaglyph, with both legacy and new JSON.

## A writeback fence that never signals: missing connector or stuck job

1. **A missing writeback connector** shows in the first lines of `stereo-wb-test`: `objects ... connector, writeback connector or properties missing`, or no `Writeback-N` entry under `/sys/class/drm/cardN-*`. In configfs the CRTC needs `writeback` set to 1 (`echo 1 > crtcs/crtc0/writeback`) before the device is enabled; the writeback connector, its encoder and its bind to that CRTC are made by `vkms_enable_writeback_connector()`, nothing else to link. A client has to set `DRM_CLIENT_CAP_WRITEBACK_CONNECTORS` to see it.
2. **A stuck job** has a connector (`Writeback-N`, status `connected` or `unknown`) and an atomic commit that returns 0, then the out fence stays unsignalled (`poll()` times out, `Connection timed out`). Read `drm.debug=0x3f` (add `log_buf_len=16M` to the guest's command line, or the default device's vblank lines push the commit out of the ring; BusyBox has no `awk` or `tail`, filter with `grep` and `sed`): an `-22` right after `Invalid framebuffer size` is the bench's negative test of a wrong buffer size and returns at once, it is not the timeout. A commit that completes with the CRTC enabling and no `enabling vblank on crtc` before the next commit is the vblank timer that never started; a `pr_info()` of the `drm_crtc_vblank_get()` result in the driver names it.
3. **Make the CRTC state a variable.** The same device and mode, committed with the CRTC off at the start (as after `enabled`) and with the CRTC already on (a first commit without the writeback job): a job that completes only in the second case is this trap.

## A CRC source set on a CRTC that is off: the unbalanced vblank put

1. **The debugfs open cannot show it.** On these kernels (7.3 line), `crtc_crc_open()` in drivers/gpu/drm/drm_debugfs_crc.c returns `-EIO` when `!crtc->state->active`, and `set_crc_source` is gated the same way, so the driver's `set_crc_source` is never reached from an off CRTC through debugfs. An open of `crc/data` that fails with `EIO` on a configfs device whose CRTC is off (`/sys/kernel/debug/dri/N/state`: `enable=0 active=0`) is this gate, not the driver.
2. **Reach the driver directly.** A KUnit test calls `vkms_set_crc_source("auto")` on a CRTC whose vblank is off: `vkms_set_composer(true)` then shows the defect, `drm_crtc_vblank_get()` returns `-EINVAL` (the CRTC is off) on a kernel without series 38/0012, the result is dropped, a composer user is counted, and the matching `vkms_set_composer(false)` puts a reference that was never taken: `drm_WARN_ON` in `drm_vblank_put()` (`refcount == 0`), an unbalanced `refcount_warn_saturate` report.
3. **The fix** (series group 38, 0012): `vkms_set_composer()` returns the error of `drm_crtc_vblank_get()` and counts a composer user only after the reference is taken; the put happens only if the get counted. A source set on an off CRTC then fails with `-EINVAL` and nothing leaks. KUnit red and green cases are in the patches's own suite; the writeback twin of this defect is series 38/0011.

## Guests for published kernels

The bench's tiny kernel builds VKMS in; a published kernel has it as a module.
Unpack its `linux-image` package with `dpkg-deb -x`, take `vmlinuz` from `boot/` and the modules `configfs`, `drm`, `drm_kms_helper`, `drm_shmem_helper`, `drm_client_lib`, `rc-core`, `cec`, `drm_display_helper` and `vkms` from `lib/modules/RELEASE/kernel/` (decompress them: BusyBox `insmod` does not read `.xz`), put them with a static BusyBox, the EDIDs, the expectation files and a static `lsmodes` in an initramfs, and boot it with QEMU (KVM, `-display none`, `-serial stdio`).
The init script runs `insmod` in that order, mounts configfs, and prints one line per result.
To test a patched VKMS against a published kernel without building the kernel, build the module against that kernel's `linux-headers` package (`make -C /usr/src/linux-headers-RELEASE M=$PWD/vkms CONFIG_DRM_VKMS=m modules`, with a `Kbuild` holding `obj-m += vkms.o` and the object list of the driver's Makefile) and put it in the initramfs in place of the kernel's own; the kernel has no `CONFIG_MODVERSIONS` and does not force signatures, so it loads (tainted).
Build the unpatched source the same way too: if it is red like the published module, the build is not what changed the result.

## Traps met (symptom, cause, fix, how found)

- **Symptom:** the connector lists `12 2D modes, 0 stereo modes`, the EDID decodes with 3D, and `modetest` or `lsmodes` show no `3D` flag. **Cause:** nothing in VKMS set `connector->stereo_allowed`, so `drm_mode_validate_stereo()` removed the 24 stereo modes the parser had added. The vkms-stereo-bench's patch "Allow stereo modes" did it, and was lost when the configfs EDID attributes were rewritten for another base. **Fix:** set `stereo_allowed` on every VKMS connector, and make the composer and the writeback buffer use the frame of both eyes (`drm_mode_get_hv_timing()`), or a client that sets a frame packing mode would be refused or composed at one eye. **Found by:** `drm.debug=0x4` and `Rejected mode ... (NO_STEREO)`; before that the symptom was only a smaller list, which every layer of the stack shows alike.
- **Symptom:** `edid/make-edid.py --help` leaves a 256-byte file named `--help` next to the script. **Cause:** the tool takes its first argument as the output path and has no options parser. **Fix:** never ask it for help; read its docstring, and run it from a scratch folder with the output path first.
- **Symptom:** on a kernel without series 38/0012, a CRC source set through the driver on a CRTC that is off (KUnit: `vkms_set_crc_source("auto")` with the vblank off) ends in `refcount_warn_saturate` / `drm_WARN_ON` on the matching close, after `drm_crtc_vblank_get()` answered `-EINVAL` and nobody noticed. **Cause:** `vkms_set_composer(true)` ignored the failed get and counted a composer user; `vkms_set_composer(false)` then put a reference that was never taken. The literal debugfs repro (`echo auto > crc/control`, open `crc/data` on an off CRTC) cannot show it: the DRM core's `crtc_crc_open()` returns `-EIO` for an inactive CRTC before the driver runs. **Fix:** series group 38, 0012: `vkms_set_composer()` propagates the get's error and puts only what it counted. **Found by:** the ORDER 452 writeback fix (same get shape) plus reading `vkms_crc.c` next to it: the CRC path had never been counted; the debugfs gate was found by running the literal repro in a guest and watching it fail with `EIO`.
- **Symptom:** `stereo-wb-test` reports `commit or writeback: Connection timed out` for the 2D mode of a device made through configfs, then for every later mode too, while the module's default device passes (kernel builds 14 and 16; 36 of 39 checks failed on a 3D-EDID device). **Cause:** the writeback connector exists and is bound to the CRTC; the first job never completes because nothing runs the composer, and it stays first in the connector's job queue, so every later `drm_writeback_signal_completion()` signals it instead of the new job. The job's vblank reference was taken in `prepare_writeback_job()`, before the commit enables the CRTC: a CRTC that is off holds the private reference of `drm_crtc_vblank_off()`, so `drm_crtc_vblank_get()` returns `-EINVAL` (drivers/gpu/drm/drm_vblank.c, `drm_vblank_get()`: refcount already above 0 and `vblank->enabled` false), the result was dropped, `drm_crtc_vblank_on_config()` then found no user and left the vblank timer off, and the composer runs only from that timer. The default device passes because its fbdev client has enabled the CRTC before any test (`/sys/kernel/debug/dri/N/state`: `enable=1 active=1` for the default device, `enable=0 active=0` for the configfs one). **Fix:** count the composer user at prepare (it must balance the cleanup), take the vblank reference in `atomic_commit()`, where the CRTC is on, and put it in the cleanup (series group 38, 0011). **Found by:** `drm.debug=0x3f` showed a clean atomic commit and no `enabling vblank` line until the next commit, 5 seconds later; a `pr_info()` in `vkms_set_composer()` printed `vblank_get ret=-22`; then the kernel's `drm_vblank_get()` and `drm_crtc_vblank_on_config()`. A timeout that only the configfs device shows is the CRTC state at the first commit, not the configfs code. Running the test a second time on the same device does not help: the stuck job is still queued.
- **Symptom:** a KUnit test that commits a writeback job passes on the kernel with the bug. **Cause:** the fixture's device uses DRM's default commit tail, which calls `drm_atomic_helper_wait_for_vblanks()` and starts the vblank timer on its own, as VKMS's own commit tail does not. **Fix:** set `mode_config.helper_private` to `vkms_mode_config_helpers` (exported for KUnit), call `drm_vblank_init()` before `vkms_output_init()`, give the device `DRIVER_GEM` and real shmem buffers, and turn the vblank off at the end (`drm_crtc_vblank_off()`: a running vblank timer outlives the device and faults). **Found by:** a `dump_stack()` in `drm_vblank_enable()` of the scratch tree named `drm_atomic_helper_commit_tail` as the caller.
- **Symptom:** a KUnit run faults in `cleanup_work` or in the vblank timer after the test ended. **Cause:** a writeback job is cleaned up from a worker after its fence signals, and the vblank timer runs for the offdelay after the last user; both outlive a test that returns at once. **Fix:** wait until the job queue is empty and the driver's composer user count is back to 0, and disable the planes (`drm_atomic_helper_disable_all()`) so their buffers are unmapped before they are freed.
- **Symptom:** a Virtual connector made through configfs lists no EDID mode, while an HDMI-A one does. **Cause:** a Virtual connector has no EDID property to hold the blob (see the traps in the skill). **Fix:** type 11 (HDMI-A) for the 3D bench.
- **Symptom:** `kunit.py --arch=um` stops with `CONFIG_MIN_BASE_SLICE_NS undeclared` in `kernel/sched/fair.c`. **Cause:** the edition's scheduler patch adds that option in an x86 Kconfig. **Fix:** run the KUnit suites on `--arch=x86_64` (QEMU, KVM), as `kernel/tests/kunit/run.sh` does, in an image that has both the kernel build tools and `qemu-system-x86`. An image committed from a container started with `--entrypoint sh -c ...` keeps that entrypoint: override it with `--entrypoint sh` when you run it.
- **Symptom:** QEMU writes nothing with `-serial file:` or with the console redirected inside a container started without a terminal. **Fix:** `sh -c 'qemu ... -serial stdio 2>&1 | cat'` and redirect the container's output.
