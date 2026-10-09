---
name: vkms-stereo
description: >-
  How to test HDMI 3D (stereo) modes without a 3D display: VKMS, the kernel's virtual display driver, in a virtual machine, with a connector that reads a 3D display's EDID through configfs, its writeback connector reading each eye back, and the bench that runs KUnit, a pixel-exact writeback test, IGT's kms_3d and Stereo KWin on it. For kernel, driver and compositor work on 3D modes. Load the general sparky-stereo skill first.
---

# A virtual 3D display: VKMS in stereo

**Check freshness first.** Written on 2026-10-08. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill says what counts as proof; for driver work also load [`drivers`](../drivers/SKILL.md), and for captures of a compositor's eyes [`stereo-proof-rig`](../stereo-proof-rig/SKILL.md).
The step-by-step guide is [Test stereo without a 3D TV](../../docs/test-stereo-without-a-3d-tv.md); the tool is [vkms-stereo-bench](../../tools/vkms-stereo-bench/README.md).

## When to use it

- A change to how the kernel lists, checks or times 3D modes (the EDID parser, `drm_mode_set_crtcinfo()`, a driver's CRTC code).
- A change to how a compositor lists, sets or packs 3D modes, down to the frame it hands the display.
- A program that must react to a 3D mode, tested on a desktop that has one.

It replaces none of the tests on a real television: VKMS has no cable, so the HDMI vendor InfoFrame is not checked here.

## The pieces

- **The kernel:** Louis Chauvet's VKMS configfs series ([v5](https://lore.kernel.org/dri-devel/20260627-vkms-all-config-v5-0-854aa0840926@bootlin.com/)) gives a VKMS connector a `type` and an EDID (`edid`, `edid_enabled`); the bench's five patches on top free that EDID, make the composer and the writeback connector use the whole frame of a stereo mode, allow stereo modes, test both, and attach the PATH property only where IGT expects it.
- **A virtual machine, always:** QEMU with KVM when available, a small kernel booted with an initramfs. On a desktop, the running compositor would take VKMS as one more screen.
- **The EDID decides the modes:** HDMI 1.4b's Vendor-Specific Data Block with 3D present brings the mandatory 3D formats of the listed video formats, plus what `3D_Structure_ALL` and `3D_Structure_X` declare. Use an EDID that `edid-decode --check` passes, and a real display's EDID next to it.
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
