# Test stereo without a 3D TV

A step-by-step guide for driver, compositor and program developers.
It shows how to test HDMI 3D modes, from the kernel's mode list to the frame a compositor sends to the display, on any Linux computer, without a 3D display.
The tool is [vkms-stereo-bench](../tools/vkms-stereo-bench/README.md); this guide walks through it and says what each test proves and how it fails when support is missing.

## The idea

A 3D television says what it accepts in its EDID.
Its HDMI Vendor-Specific Data Block (HDMI 1.4b) says "3D present" and lists the 3D structures, such as frame packing, top-and-bottom and side by side, for the video formats of CTA-861.
The kernel turns that into 3D modes; a compositor sets one and sends the display one frame that holds both eyes.
How the eyes sit in that frame is fixed by HDMI 1.4b: in frame packing, the left eye, then as many lines as the vertical blanking (the "active space"), then the right eye; in top-and-bottom and side by side (half), each eye in one half of an ordinary frame; in side by side (full), the two eyes next to each other at full width.
The timings are laid out in awesome-stereoscopy's [frame packing and HDMI timings](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/docs/frame-packing-and-hdmi-timings.md).

VKMS, the kernel's virtual display driver ([Documentation/gpu/vkms.rst](https://docs.kernel.org/gpu/vkms.html)), does what a display driver does except drive a cable, and its writeback connector returns the frame it composed.
Give a VKMS connector the EDID of a 3D display, and the whole path runs in a virtual machine: the kernel lists the 3D modes, a test or a compositor sets one, and the writeback frame shows where each eye landed.

Run VKMS only in a virtual machine.
On a desktop, the running compositor takes a virtual display as one more screen.

## What each test proves

| Test | What it proves | How it fails without the support |
|---|---|---|
| KUnit `vkms-stereo` | The connector lists exactly the 3D modes the EDID declares, and the writeback connector takes a buffer of the frame that holds both eyes, for a 2D mode, frame packing, top-and-bottom and side by side (half). | Without `stereo_allowed`, all 14 stereo formats of the test EDID are "not listed". Without the composer change, frame packing fails both size checks: the frame-sized buffer is refused, the one-eye buffer is accepted. |
| `writeback` phase | For every stereo mode a synthetic EDID and a real television's EDID give: the left eye, the right eye and the frame packing active space land where HDMI 1.4b puts them, pixel by pixel, also with one plane per eye; a 2D mode stays 2D; frame packing keeps the 2D refresh rate. | Without `stereo_allowed`, the mode lists are empty. Without the composer change, every frame packing commit is refused. |
| IGT `kms_3d` | The driver lists the 3D modes of IGT's own 3D EDID and sets each one with a stereo framebuffer. | "3D modes not detected". On v5 as posted, without the PATH fix, an assertion in `kmstest_get_path_blob()`. |
| `kwin` phase | Stereo KWin lists the 3D modes, sets each one, and draws a 2D window the same in both eyes and a stereo window's left view only in the left eye and its right view only in the right eye. | No 3D mode is listed. |

## Step 1: the kernel

VKMS reads an EDID through configfs with Louis Chauvet's series [VKMS: Introduce multiple configFS attributes](https://lore.kernel.org/dri-devel/20260627-vkms-all-config-v5-0-854aa0840926@bootlin.com/) (v5, in review on dri-devel).
Five patches go on top of it, in the bench's [patches/](../tools/vkms-stereo-bench/patches/) folder:

1. **Free the connector's EDID with its configuration:** a fix for a leak in v5, offered to the author.
2. **Compose the frame of both eyes:** a frame packing mode describes one eye, while its frame holds both and the active space; the DRM core already gives that frame's size (`drm_mode_get_hv_timing()`) and clips planes to it, and now the composer and the writeback connector use it too.
3. **Allow stereo modes:** VKMS connectors set `stereo_allowed`, without which the kernel drops every 3D mode while probing.
4. **KUnit tests** for both.
5. **Attach the PATH property only to connectors that have a parent:** with v5 as posted, every VKMS connector has an empty PATH property and IGT's connector setup fails on it; a fix offered to the author.

In a clone of the mainline kernel (the series' base commit is in v7.3-rc1):

```sh
git checkout -b vkms-stereo 6648301c5bb2
b4 am -o - 20260627-vkms-all-config-v5-0-854aa0840926@bootlin.com | git am
git am ~/vkms-stereo-bench/patches/*.patch
~/vkms-stereo-bench/tools/build-test-kernel.sh . ~/build/vkms
```

The last command makes a small kernel (`make tinyconfig` plus the bench's configuration fragment) with VKMS, configfs, writeback, KUnit and 9p built in, in a few minutes on four cores.
For the compositor test, build a second one with `BASE=x86_64_defconfig` and `kconfig/vkms-stereo-full.fragment`, because a desktop needs system calls that tinyconfig leaves out.

## Step 2: a virtual 3D display

This is what the bench does for you; do it by hand to use the virtual display with your own program in your own virtual machine.
With configfs mounted at `/sys/kernel/config`:

```sh
d=/sys/kernel/config/vkms/stereo
mkdir $d
mkdir $d/planes/primary $d/crtcs/crtc0 $d/encoders/encoder0 $d/connectors/hdmi0
echo 1 > $d/planes/primary/type                 # primary plane
echo 1 > $d/crtcs/crtc0/writeback               # a writeback connector to read the frame back
ln -s $d/crtcs/crtc0 $d/planes/primary/possible_crtcs/
ln -s $d/crtcs/crtc0 $d/encoders/encoder0/possible_crtcs/
echo 11 > $d/connectors/hdmi0/type              # DRM_MODE_CONNECTOR_HDMIA
cat stereo-test.bin > $d/connectors/hdmi0/edid  # one write, the whole EDID
echo 1 > $d/connectors/hdmi0/edid_enabled
ln -s $d/encoders/encoder0 $d/connectors/hdmi0/possible_encoders/
echo 1 > $d/enabled
```

The connector then lists the EDID's modes, the 3D ones among them, through the kernel's normal EDID parser.
A program sees the 3D modes only after it sets the `DRM_CLIENT_CAP_STEREO_3D` client capability.
Write the EDID and set `edid_enabled` before enabling the device, and leave both alone afterwards.
With v5, an EDID rewritten while the connector is probed is read while it changes (KASAN reports an out-of-bounds read in `vkms_connector_read_block()`); `edid_enabled` turned on later gives a Virtual connector no EDID modes, and turned off later it leaves the old EDID on the connector.

The bench's test EDID ([edid/make-edid.py](../tools/vkms-stereo-bench/edid/make-edid.py), `edid-decode --check` passes) declares 3D present, which brings HDMI 1.4b's mandatory 3D formats of the video formats it lists (1080p24, 720p60 and 720p50 in frame packing and top-and-bottom), side by side (half) for its six video formats, top-and-bottom for 1080p60 and frame packing for 1080p30.
The second EDID is a Sony KDL-46HX855's, a 3D television of 2012, which brings 17 stereo formats on a connector without interlace.

## Step 3: run the bench

```sh
cd ~/vkms-stereo-bench
./run-in-docker.sh -m ~/build/vkms:$HOME/build/vkms:ro \
    --kernel ~/build/vkms/arch/x86/boot/bzImage run kunit writeback
```

The first run builds the tool image: QEMU, a static BusyBox, edid-decode and a compiler.
Nothing is installed on the host and no module is loaded there; KVM is used when `/dev/kvm` is usable.
Each phase boots the kernel once and prints its checks; every run keeps its console log, its results and pictures of the frames under `bench-work/runs/`.

What a pass looks like, measured on 2026-10-08 on the base commit with v5 and the five patches:

- **kunit:** `vkms-stereo` passes, next to VKMS's own suites (`vkms-config`, `vkms-configfs`, `vkms-format`, `vkms-color`).
- **writeback:** 39 checks on the synthetic EDID's device, 49 on the television's, 3 on the default device without an EDID, 0 failed. A frame packing 1080p frame is 1920x2205 with the right eye from line 1125; a 720p one is 1280x1470 with the right eye from line 750. The vblank period of 1080p24 frame packing was 41666.7 µs, the same as 2D 1080p24.

The same phases and `igt` on a kernel built with KASAN as well (add `kconfig/debug.fragment` to the fragments of `build-test-kernel.sh`) passed with no KASAN report.

And how the same phases failed on that base without the patches: with only the test (patch 4), the KUnit test reported all 14 stereo formats "not listed" and the writeback phase found 0 of 14 and 0 of 17 formats; with the test and `stereo_allowed` (patches 3 and 4) but not patch 2, frame packing failed both KUnit size checks, and the writeback phase failed every frame packing commit, 26 checks in all.

## Step 4: IGT's kms_3d

```sh
tools/build-igt-root.sh ~/build/igt-root
./run-in-docker.sh -m ~/build/vkms:$HOME/build/vkms:ro -m ~/build/igt-root:$HOME/build/igt-root:ro \
    --kernel ~/build/vkms/arch/x86/boot/bzImage --igt-root ~/build/igt-root run igt
```

`kms_3d` writes IGT's own 3D EDID to the connector's debugfs `edid_override`, which the v5 EDID path honours, and needs an HDMI-A connector, which is why the bench sets the connector type.
IGT leaves VKMS out of the drivers it opens by default; the bench sets `IGT_FORCE_DRIVER=vkms` and boots with `vkms.create_default_dev=0`, so the configfs device is the only card.
Measured: "Subtest basic: SUCCESS", ten 3D modes set; with v5 as posted, without patch 5, `kms_3d` stops at an assertion in `kmstest_get_path_blob()`.

## Step 5: a compositor

With a root file system of Sparky Stereo OS (Stereo KWin, `kscreen-doctor`, Qt's Wayland shell integration, Mesa, D-Bus, gcc and the Wayland and EGL development files) and the desktop kernel from step 1:

```sh
./run-in-docker.sh -m ~/build:$HOME/build:ro --kernel ~/build/vkms/arch/x86/boot/bzImage \
    --full-kernel ~/build/vkms-full/arch/x86/boot/bzImage --kwin-root ~/build/sparky-root run kwin
```

KWin runs on the VKMS card from that root in a chroot, renders with Mesa's software rasterizer, and `kscreen-doctor` sets each 1920x1080 3D mode.
The bench reads the frame KWin hands to the display and checks, for each layout: a fullscreen 2D client identical in both eyes, a stereo client (a 2D window with a two-view EGL surface inside it) with its left view only in the left eye and its right view only in the right eye at the same place, the same client as a plain 2D one the same in both eyes, and the frame packing active space black.
Measured with this bench on 2026-10-08, Stereo KWin 6.7.4 with Mesa 26.1.6 and Qt 6.11.2, on Sparky Stereo OS's 7.3-rc1 based kernel with the same VKMS changes and `--sbs-full`: 26 3D modes listed, each layout set at 1920x1080, 22 checks, 0 failed, frame packing at 1920x2205 and side by side (full) at 3840x1080.

## When a check fails

Every failing check names what it expected and what it found: the first wrong pixel with both values, or the stereo formats that are missing or unexpected.
Run the same phase on the kernel without the patches once: it must fail, or the check proves nothing.
On the kernel without the patches, the bench reported exactly the failures in the table above.

## Limits

- VKMS has no cable, so the HDMI vendor InfoFrame that tells a television which 3D structure it receives is not checked; that stays a test on real hardware.
- VKMS does not allow interlaced modes, so the mandatory 1080i side by side (half) formats are not listed.
- The DRM core lists four of the 3D structures of HDMI 1.4b from an EDID: frame packing, top-and-bottom, side by side (half), and side by side (full) only with a core change that mainline does not have yet (`--sbs-full` tests it). Field alternative, line alternative and the two L + depth structures are listed by no driver.
- The compositor phase reads KWin's frame, not VKMS's writeback, because KWin owns the display; with KWin's cursor plane off in 3D modes, the two hold the same pixels.
- A real 3D television is still the last test.

## Sources

- HDMI Specification 1.4b: the HDMI Vendor-Specific Data Block and the 3D video format structures. CTA-861: the video formats (VICs).
- Kernel: [VKMS](https://docs.kernel.org/gpu/vkms.html), [KUnit](https://docs.kernel.org/dev-tools/kunit/index.html), and in the source, `drm_mode_set_crtcinfo()` and `drm_mode_get_hv_timing()` in `drivers/gpu/drm/drm_modes.c`, the HDMI block parser in `drivers/gpu/drm/drm_edid.c`, the stereo filter in `drivers/gpu/drm/drm_probe_helper.c`.
- [IGT GPU Tools](https://gitlab.freedesktop.org/drm/igt-gpu-tools) (`tests/kms_3d.c`), [edid-decode](https://git.linuxtv.org/v4l-utils.git/tree/utils/edid-decode) (in v4l-utils), [QEMU](https://www.qemu.org/).

## Credit

VKMS was written by Rodrigo Siqueira and Haneen Mohammed, and is maintained by Louis Chauvet, with Haneen Mohammed, Simona Vetter and Melissa Wen as reviewers.
José Expósito wrote VKMS's configfs interface, and Louis Chauvet's v5 series adds the connector type and EDID attributes this bench stands on.
IGT's `kms_3d` was written by Thomas Wood (Intel) in 2014.
edid-decode was written by Adam Jackson (Red Hat) and is maintained by Hans Verkuil (Cisco).
The bench and the stereo patches are by Daniel Ramos, directed and verified, with Claude (Anthropic) as an AI partner.
