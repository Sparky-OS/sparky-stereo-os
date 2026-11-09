---
metadata:
  requires-packages: qemu-system-x86 | igt-gpu-tools
name: vkms-stereo
description: >-
  Test DRM stereo mode enumeration, timing and writeback without a 3D display: the virtual KMS driver with an EDID that
  declares HDMI 3D modes (configfs, edid and edid_enabled, the status attribute for hotplug and detect), IGT kms_3d and
  its VKMS exceptions, KUnit and its exit status, KWin in the guest (udevd for hotplug, LIBGL_ALWAYS_SOFTWARE,
  kscreen-doctor), expectations computed from the EDID, a virtual machine always, VC4 and DisplayPort timing checked
  without the board, a claim's EDID read on any kernel through the debugfs edid_override of a QEMU bochs display. Load
  it when a 3D mode is missing from the list, interlaced or duplicated formats appear, a probe needs the DRM master, IGT
  leaves VKMS out, the compositor never sees a hotplug, kunit.py exits 0 with failed tests, drm.debug on the command
  line prints nothing after insmod, or a kernel stereo patch needs a bench.
---

# A virtual 3D display: VKMS in stereo

## Working recipe

1. Pin kernel/bench revisions and validate the test EDID. Derive expected modes from the EDID rather than the code under test.
2. Run the relevant guest phases with labelled eyes, the no-EDID/2D cases and the old-code control; keep VKMS off the active desktop.
3. Return mode and pixel comparisons with phase logs. Physical [HDMI®](https://www.hdmi.org/resource/brand) signaling and panel behavior require separate hardware tests.

**Check freshness first.**
Written on 2026-10-08.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill says what counts as proof; for driver work also load [`drivers`](../drivers/SKILL.md), and for captures of a compositor's eyes [`stereo-proof-rig`](../stereo-proof-rig/SKILL.md).
The step-by-step guide is [Test stereo without a 3D TV](../../docs/test-stereo-without-a-3d-tv.md); the tool is [vkms-stereo-bench](../../tools/vkms-stereo-bench/README.md).

## When to use it

- A change to how the kernel lists, checks or times 3D modes (the EDID parser, `drm_mode_set_crtcinfo()`, a driver's CRTC code).
- A change to how a compositor lists, sets or packs 3D modes, down to the frame it hands the display.
- A program that must react to a 3D mode, tested on a desktop that has one.

It replaces none of the tests on a real television: VKMS has no cable, so the HDMI® vendor InfoFrame is not checked here.

## The pieces

- **The kernel:** Louis Chauvet's VKMS configfs series ([v5](https://lore.kernel.org/dri-devel/20260627-vkms-all-config-v5-0-854aa0840926@bootlin.com/)) gives a VKMS connector a `type` and an EDID (`edid`, `edid_enabled`); the bench's five patches on top free that EDID, make the composer and the writeback connector use the whole frame of a stereo mode, allow stereo modes, test both, and attach the PATH property only where IGT expects it.
- **A virtual machine, always:** QEMU with KVM when available, a small kernel booted with an initramfs. On a desktop, the running compositor would take VKMS as one more screen.
- **The EDID decides the modes:** HDMI® 1.4b's Vendor-Specific Data Block with 3D present brings the mandatory 3D formats of the listed video formats, plus what `3D_Structure_ALL` and `3D_Structure_X` declare. Use an EDID that `edid-decode --check` passes, and a real display's EDID next to it.
- **Expectations come from the EDID, not from the kernel:** read the declared 3D formats from `edid-decode`'s text and compare them with what the connector lists. Comparing the kernel with itself proves nothing.
- **The frame of each layout:** frame packing is vdisplay + vtotal lines (1080p: 2205; 720p: 1470) with the right eye from line vtotal and black active space between; side by side (full) is twice the width; top-and-bottom and side by side (half) keep the mode's size. `drm_mode_get_hv_timing()` gives that size; planes, the composer and the writeback buffer all use it.

## The checks

1. The stereo formats the connector lists equal the EDID's declared ones, and a connector without an EDID lists none.
2. Every listed stereo mode, shown with a known left and right eye, read back through writeback: 0 wrong pixels, the frame packing active space included; also with one plane per eye at its place.
3. A 2D mode stays 2D: its writeback buffer is its own size, and a stereo-sized one is refused.
4. The vblank period of a frame packing mode equals its 2D mode's.
5. IGT's `kms_3d` passes.
6. With a compositor: it lists the 3D modes, sets each one, and its frame holds a fullscreen 2D client identical in both eyes, a stereo window's left view only in the left eye and its right view only in the right eye, a 2D window the same in both eyes.
7. Every check above fails on the kernel without the change, once; record how.

## Traps that fooled us

- **DRM lists 24, 30 and 60 Hz formats twice**, at the integer rate and at 1000/1001 of it, stereo modes included: match formats (size, rate, layout), not modes.
- **Only the DRM master forces a probe** with `DRM_IOCTL_MODE_GETCONNECTOR`; others get the last probe's list. A test that changes the EDID must be the master or probe through sysfs.
- **Stereo modes are hidden** from programs that do not set `DRM_CLIENT_CAP_STEREO_3D`, and interlaced ones are dropped because VKMS does not allow interlace (no 1080i side by side (half)).
- **The KUnit output needs `loglevel=7`** on the console: KTAP lines are informational messages. Under UML in Docker, `/dev/shm` is mounted noexec; point `TMPDIR` at an exec mount.
- **Write the EDID in one `write()`, before enabling the device:** configfs hands each write to the attribute on its own, and the v5 code does not yet protect an EDID changed while the connector is probed (KASAN reports an out-of-bounds read).
- **Set `edid_enabled` before enabling the device too, and leave it:** with v5, turning it on later gives a Virtual connector no EDID modes (no EDID property to hold the blob), a dynamic Virtual connector never gets its EDID, and turning it off later leaves the old EDID blob on the connector.
- **With v5 as posted, IGT stops on every VKMS connector:** each one has a PATH property without a blob, and `kmstest_get_path_blob()` asserts a blob whenever the property exists; the bench's patch 5 attaches PATH only to connectors with a parent.
- **IGT leaves VKMS out of `DRIVER_ANY`:** set `IGT_FORCE_DRIVER=vkms`, give the connector the HDMI-A type (`kms_3d` looks for one), and boot with `vkms.create_default_dev=0` so the configfs device is the only card.
- **KWin scans out 16 bits per channel** (`DRM_FORMAT_ABGR16161616`) on VKMS: a frame grabber must read it.
- **A grab while the compositor renders** catches a half-drawn buffer: copy the scanned-out buffer at once and copy again if the plane flipped away meanwhile.
- **EGL clients need `LIBGL_ALWAYS_SOFTWARE=1`** on VKMS, which has no render node; without it the test client crashed.
- **`kscreen-doctor` needs Qt's Wayland shell integration** installed even though it opens no window.
- **A black desktop is the same in both eyes for free:** put a fullscreen 2D client with a gradient on it before calling "identical in both eyes" a result.

## Proof for this kind of work

- The bench's results for each phase, with the kernel's commit and the EDIDs used.
- The same phases on the kernel without the change, failing where expected.
- Pictures of a few writeback frames and compositor frames, looked at by eye.
- The real-hardware test (a television switching itself into 3D) stays in the [`drivers`](../drivers/SKILL.md) skill's proof list.
- How to run that real-hardware test with a person at the bench and the partner remote, without risking the machine or the television: [`test-bench`](../test-bench/SKILL.md).

## A 3D mode of the EDID is missing from the connector's list

Walk the EDID to the mode list one step at a time, each with a check that can fail: the EDID decodes with 3D, the expectation is made from `edid-decode` (never from the kernel), the connector's modes read with the stereo capability set, and, if they are missing, `drm.debug=0x4` names the status of every mode the probe helper drops (`NO_STEREO` means the connector lacks `stereo_allowed`).
Then the frame of each layout, and the same guest on the kernel without the change.
The steps, the guest for a published kernel, and the traps are in [references/edid-to-mode-list.md](references/edid-to-mode-list.md); the bench's `src/lsmodes.c` lists a connector's modes against an expectation and `edid/make-2d-edid.py` makes the 2D-only twin of an EDID.

## An EDID for a claim, read on any kernel

What a kernel's EDID parser makes of one declaration (a sink that sets 3D_present with no mandatory timing, one 3D format on one VIC, a reserved bit, a shipped device's EDID from linuxhw/EDID) needs no VKMS patch: build the EDID from HDMI® 1.4a Table 8-16, pass `edid-decode --check`, boot the kernel package's own `bochs` driver in QEMU with `-device bochs-display,edid=on`, write the file to the connector's debugfs `edid_override`, `echo detect` to its sysfs `status`, and read the parser's stereo modes from the `Rejected mode ... (NO_STEREO)` lines of `drm.debug=0x4`, which that connector drops for want of `stereo_allowed`.
The recipe, the edid-decode failures and their fixes, the Debian 14 kernel package split, and the facts measured on two kernels are in [references/edid-for-a-claim.md](references/edid-for-a-claim.md).

## The output's eye flip on every 3D mode, and an old lane's open points

Every 3D mode of one output (anaglyph, rows, columns, checkerboard, half side by side, top and bottom, side by side full, frame packing, frame sequential) with the eye swap off and on, each against a model that the other swap must fail, in one guest run of about four minutes: [references/eye-order-matrix.md](references/eye-order-matrix.md) has the recipe, the traps and how to reconcile an old report's open points against what ships; the scripts are in `tools/vkms-stereo-bench/eyeorder`.

## Lessons from the lanes, October to November 2026

From the lanes of 25 October to 6 November 2026; add the next lesson here as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

- Test vc4's HDMI stereo timing without a Pi: KUnit on the real encoder callback in ARM64 QEMU with fixed CEA expectations. Baseline 22 rows: 4 pass, 18 fail; after the patch 77 pass, zero failures (44 stereo cases plus 33 existing vc4 cases); cases cover both SBS-full choices, repeated checks, original VIC and flags, RGB8/RGB12 clock agreement, generation limits, overflow, DBLCLK and 2D controls. Targeted ARM GCC 16.2.0 compile and ARM64 Clang 21.1.8 KUnit kernel build pass; strict checkpatch has zero errors. Tools: GCC 16.2.0, Clang 21.1.8, QEMU 11.1.2. (lane vc4-stereo-timing-155-gpt)
- Hotplug test on VKMS: build one VKMS device with two DisplayPort connectors by configfs (dp0 connected, dp1 disconnected, each its own CRTC); the connector `status` attribute (1 connected, 2 disconnected) hotplugs; an EDID rewrite while enabled then `echo detect > /sys/class/drm/cardN-DP-N/status` re-announces on the same connector (lane lutz-xreal-driver-233)
- Symptom: KWin in the guest never sees the hotplug. Cause: KWin binds udevd's netlink group ("udev"), not the kernel's, and the guest root had no udevd. Fix: overlayfs over the read-only 9p root adds udev (systemd 262) and the new kscreen-doctor without touching the shared root (lane lutz-xreal-driver-233)
- A VKMS connector made through configfs read its EDID but listed no 3D mode (builds 14 and 16 of the edition's kernel): `drm_mode_validate_stereo()` dropped each stereo mode with `NO_STEREO` because VKMS never set `stereo_allowed`; found with `drm.debug=0x4` ("Rejected mode"), fixed with the connector flag plus a composer and writeback frame that hold both eyes. Steps and traps: [references/edid-to-mode-list.md](references/edid-to-mode-list.md).
- A writeback fence that times out on a configfs-made VKMS device (builds 14 and 16) while the default device passes: the job took its vblank reference before the CRTC was on, `drm_crtc_vblank_get()` failed with `-EINVAL` unnoticed, so the vblank timer, and with it the composer, never ran; the default device only passed because its fbdev client had already enabled the CRTC. Run the same device with the CRTC off and on at the first commit. Steps and traps: [references/edid-to-mode-list.md](references/edid-to-mode-list.md).
- A CRC source asked of a CRTC that is off warns `refcount == 0` on close (builds 14 and 16): `vkms_set_composer(true)` dropped the `-EINVAL` of `drm_crtc_vblank_get()` and counted a composer user anyway, and the close path put the reference it never took. The debugfs `crc/data` open itself cannot show it: the core returns `-EIO` for an off CRTC before the driver runs (`drm_debugfs_crc.c`); reach `vkms_set_crc_source()` from KUnit instead. Fixed in series group 38, 0012. Steps and traps: [references/edid-to-mode-list.md](references/edid-to-mode-list.md) (lane vkms-crc-vblank-452b)
- Symptom: a right eye first frame-sequential frame fails the model of the left eye first one with the halves exchanged. Cause: the order of frame sequential is in time (the scheduler starts on the right half of the same packed frame), so the swap exchanges the eyes inside the packed frame and the twin does not. Fix: model one packed frame for both orders and compare the eye streams from the first frame after the mode set (drm-planelog): they are the same. Found by: 12800 failing pixels, the two 6400-pixel eye areas (lane mesa-stereo-followups-116)
- Symptom: a saved frame-sequential mode comes back as 2D after a restart. Cause: the store's restore check knew no sequential layout. Fix: accept them; test by saving the mode in the JSON and asking the store (lane mesa-stereo-followups-116)
- Symptom: SRC_X changes 17 to 25 times in 240 vblanks and KWin reports 1644 missed refreshes. Cause: software GL in the guest, about one frame in five refreshes; both halves are shown, not strictly alternately. Fix: judge pacing on the DisplayPort bench, content in the guest (lane mesa-stereo-followups-116)
- `python3 edid/make-edid.py --help` writes an EDID called `--help` (the first argument is the output path): run the bench's tools from a scratch folder and never ask them for help.
- Symptom: a 3D television's EDID lists only 2D modes in the guest and `dmesg` has no `Rejected mode` line, with `drm.debug=0x4` on the kernel command line. Cause: a module parameter on the command line is applied by modprobe, and BusyBox insmod ignores it. Fix: `echo 0x4 > /sys/module/drm/parameters/debug` after loading the modules, and print it back. Found by: the mode count alone, every layer showing the same short list (lane hdmi-technical-note-475)
- Symptom: `edid-decode --check` fails a generated EDID with "The HDMI Specification requires EDID 1.3 instead of 1.4", "EDID 1.3 does not support week 0xff", "'Bare Limits' is not allowed for EDID < 1.4", "sRGB is not signaled" or "Missing VCDB". Cause: E-EDID 1.4 habits in the 1.3 structure HDMI asks for. Fix: version `01 03`, a real week, range limits with default GTF, the sRGB feature bit, a VCDB `e2 00 4a`; the parser's answer to each file is then about the field under test only (lane hdmi-technical-note-475)
- Measured 2026-11-08 on Debian 7.3.3 and 7.3.1-stereo3d16: `add_hdmi_mandatory_stereo_modes()` adds a mandatory 3D format only to a 2D timing the sink lists, so a 1080p60 panel with 3D_present set gets no stereo mode; the 2D_VIC_order_X entries are read with 3D_present clear, so one entry gives exactly 1920x1080p60 side by side (half). Steps and traps: [references/edid-for-a-claim.md](references/edid-for-a-claim.md) (lane hdmi-technical-note-475)

HDMI®, HDMI® High-Definition Multimedia Interface and the HDMI® Logo are trademarks or registered trademarks of HDMI Licensing Administrator, Inc.
