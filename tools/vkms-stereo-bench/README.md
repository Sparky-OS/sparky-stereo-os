# vkms-stereo-bench

A test bench for HDMI 3D (stereo) modes that needs no 3D display.
It boots a Linux kernel in QEMU whose VKMS, the kernel's virtual display driver, lists and composes stereo modes.
VKMS connectors get an EDID through configfs, so their 3D modes come through the kernel's normal EDID path, exactly as a 3D television's would.
The bench then checks each eye of each mode, from the kernel's unit tests up to a desktop compositor.

The step-by-step guide is [Test stereo without a 3D TV](../../docs/test-stereo-without-a-3d-tv.md); this page is the tool's reference.

It answers questions such as:

- Does this kernel list the 3D modes an EDID declares, and only those?
- In each 3D mode, does each eye land where the HDMI 1.4b frame packing, top-and-bottom or side by side layout puts it?
- Does a 2D mode stay 2D?
- Does IGT's `kms_3d` pass?
- Does a compositor (Stereo KWin) list the 3D modes, set them, and draw a stereo window's left view only in the left eye and its right view only in the right eye?

Nothing is installed on the host when you use the Docker wrapper, and no module is loaded on the host: VKMS only ever runs in the guest.
A virtual display driver on a desktop would be taken by the running compositor as one more screen.

## What you need

- **A kernel tree with the VKMS stereo patches** ([patches/](patches/), on top of Louis Chauvet's VKMS configfs series, see below).
- **A test kernel** built from it: `tools/build-test-kernel.sh SRC OUT` makes a small one (`make tinyconfig` plus [kconfig/vkms-stereo-x86_64.fragment](kconfig/vkms-stereo-x86_64.fragment)) in a few minutes.
- Docker, or on Debian: `qemu-system-x86 busybox-static edid-decode build-essential python3 python3-pil` (`./bench doctor` tells what is missing).
- KVM (`/dev/kvm`) is optional. Without it QEMU uses TCG: slower, but it works.
- For the optional phases: a root file system with IGT's `kms_3d` (`tools/build-igt-root.sh` builds one), and for the compositor phase a root file system of Sparky Stereo OS (Stereo KWin, `kscreen-doctor`, Qt's Wayland shell integration, Mesa, D-Bus, gcc with the Wayland and EGL development files) with a kernel built from `BASE=x86_64_defconfig` and [kconfig/vkms-stereo-full.fragment](kconfig/vkms-stereo-full.fragment).

## The kernel

VKMS reads an EDID through configfs with Louis Chauvet's series [VKMS: Introduce multiple configFS attributes](https://lore.kernel.org/dri-devel/20260627-vkms-all-config-v5-0-854aa0840926@bootlin.com/) (v5, 38 patches, in review on dri-devel), which applies to its base commit `6648301c5bb2` of drm-misc-next.
The [patches/](patches/) folder goes on top of it:

| Patch | What it does |
|---|---|
| 0001 | Frees the connector's EDID copy with its configuration (a leak in v5 32/38, proposed to the author as a fixup) |
| 0002 | The composer and the writeback connector use the whole frame of a stereo mode (`drm_mode_get_hv_timing()`): for frame packing, vdisplay + vtotal lines |
| 0003 | VKMS connectors allow stereo modes (`stereo_allowed`) |
| 0004 | KUnit tests: the stereo modes an EDID declares, and the writeback buffer size of each layout |
| 0005 | Attaches the PATH property only to connectors that have a parent: with v5 as posted every VKMS connector has an empty PATH, and IGT fails in `kmstest_get_path_blob()` on every VKMS device, `kms_3d` and every test built on `igt_display` (`kms_atomic` measured) alike (proposed to the author as a fix for v5 37/38) |

```sh
# in a clone of the mainline kernel: the base commit is in v7.3-rc1
git checkout -b vkms-stereo 6648301c5bb2
b4 am -o - 20260627-vkms-all-config-v5-0-854aa0840926@bootlin.com | git am
git am /path/to/vkms-stereo-bench/patches/*.patch
```

Side by side (full) is timed by the DRM core only with a core change that mainline does not have; `--sbs-full` adds a device whose EDID declares it, for kernels that carry that change.

## Quick start

```sh
# 1. a small test kernel
tools/build-test-kernel.sh ~/src/linux ~/build/vkms

# 2. the phases (the first run builds the Docker image)
./run-in-docker.sh -m ~/build/vkms:$HOME/build/vkms:ro --kernel ~/build/vkms/arch/x86/boot/bzImage run kunit writeback

# 3. IGT's kms_3d (the root is built on the host, it needs Docker)
tools/build-igt-root.sh ~/build/igt-root
./run-in-docker.sh -m ~/build/vkms:$HOME/build/vkms:ro -m ~/build/igt-root:$HOME/build/igt-root:ro \
    --kernel ~/build/vkms/arch/x86/boot/bzImage --igt-root ~/build/igt-root run igt
```

Without Docker: `./bench --kernel ... run all` after installing the packages above.
Every run keeps its console log, its results and its pictures under `bench-work/runs/<time>-<phase>/`, and the exit status is 0 when every check passed.

## Phases

| Phase | What it checks | How it fails without the patches |
|---|---|---|
| `kunit` | VKMS's KUnit suites, built into the kernel, run at boot. `vkms-stereo` builds a device from a configuration, reads a test EDID that declares 3D, and checks the listed stereo modes and the writeback buffer size of a 2D mode, frame packing, top-and-bottom and side by side (half). | Without 0003: every stereo format is reported "not listed". Without 0002: frame packing fails both size checks (the frame-sized buffer is refused, the one-eye buffer accepted). |
| `writeback` | `stereo-wb-test` on configfs devices whose HDMI-A connector reads the test EDID and the EDID of a Sony KDL-46HX855 (a 3D television of 2012), and on the default device without an EDID as the 2D control. The listed stereo formats must equal the ones `edid-decode` reads from the EDID; every listed stereo mode is then shown with a known left and right eye and read back through the writeback connector, pixel by pixel; one plane per eye at its place; a one-eye writeback buffer refused in frame packing, a frame packing buffer refused in 2D; the vblank period of 1080p24 frame packing equal to 2D's. | Without 0003: the format lists are empty. Without 0002: every frame packing commit is refused and the one-eye buffer is accepted. |
| `igt` | IGT's `kms_3d`: forces IGT's own 3D EDID through debugfs, requires 3D modes, and sets each one with a stereo framebuffer. | Without 0003: "3D modes not detected". Without 0005: an assertion in `kmstest_get_path_blob()`. |
| `kwin` | Stereo KWin on the VKMS device: `kscreen-doctor` lists the 3D modes and sets each one; the frame KWin scans out is read back (as root, with `DRM_IOCTL_MODE_GETFB2`) and checked: a fullscreen 2D client identical in both eyes, a stereo client's left view only in the left eye and its right view only in the right eye at the same place, a 2D client the same in both eyes, the frame packing active space black. | Needs a kernel with 0002 and 0003; on a kernel without them KWin lists no 3D mode. |

The test EDID is made by [edid/make-edid.py](edid/make-edid.py) and passes `edid-decode --check`.
It declares 3D present (the HDMI 1.4b mandatory formats of the 2D formats it lists), side by side (half) for every video format through `3D_Structure_ALL`, top-and-bottom for 1080p60 and frame packing for 1080p30 through `3D_Structure_X`.

## How it works

- **Guest:** a small initramfs (static BusyBox, the phase scripts in `guest/`, the static `stereo-wb-test` and `drm-grab`) running as PID 1; results go to the serial console as `STEREO|check|...|PASS` or `FAIL` lines.
- **Devices:** each phase makes its VKMS devices in configfs (`guest/phases/lib.sh`): planes, a CRTC with a writeback connector, an encoder, and a connector with `type` 11 (HDMI-A), `edid` and `edid_enabled`.
- **Expectations:** the stereo formats each EDID should give are read from `edid-decode`'s text by [edid/expect-from-decode.py](edid/expect-from-decode.py), not from the kernel's parser, and kept to what a connector without interlace can list.
- **Frames:** pictures of the writeback frames and of KWin's frames are written to the run directory over a 9p share; [tools/analyze-kwin.py](tools/analyze-kwin.py) checks KWin's.
- **Roots:** IGT and KWin run from root file systems shared read only over 9p, in a chroot.

## Limits

- VKMS has no link, so the HDMI vendor InfoFrame that a real driver sends with a 3D mode is not checked here.
- VKMS does not allow interlaced modes, so the mandatory 1080i side by side (half) formats are not listed.
- The DRM core lists four of the HDMI 1.4b 3D structures from an EDID (frame packing, top-and-bottom, side by side half, and side by side full with the core change mentioned above); field alternative, line alternative and the two L + depth structures are listed by no driver.
- The kwin phase reads the frame KWin hands to the display, not VKMS's writeback (KWin is the DRM master); with the cursor plane off, as in KWin's 3D modes, they hold the same pixels.
- A real 3D television is still the last test: this bench proves the kernel and compositor side, not a display's behaviour.

## Layout

```
bench                  the command (bash)
run-in-docker.sh       runs it inside the tool image as your user
Dockerfile             tool image: QEMU, BusyBox, edid-decode, gcc, Python with Pillow
guest/                 init and the phase scripts that run in the guest
src/                   stereo-wb-test.c (writeback checks), drm-grab.c (frame readback), and the two Wayland
                       test clients for the kwin phase: stereo-subsurface.c and fullscreen-2d.c
edid/                  the test EDIDs, the generator, and the expectation reader
kconfig/               kernel configuration fragments: small test kernel, desktop kernel, KASAN and kmemleak
patches/               the VKMS stereo patches, on top of the v5 configfs series
tools/                 build-test-kernel.sh, build-igt-root.sh, mkcpio.py (initramfs without root), analyze-kwin.py
igt/                   the image that builds IGT's kms_3d
```

## Licence

GPL-2.0-or-later (SPDX headers in the files), the same family as the Linux kernel the bench is meant to help test.
The EDID of the KDL-46HX855 is the one published in [sony-bravia-linux](https://github.com/danielcamposramos/sony-bravia-linux/tree/main/docs/research/liverecon), read from the television itself.
