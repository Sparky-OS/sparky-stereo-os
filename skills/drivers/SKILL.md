---
name: drivers
description: How the kernel and GPU drivers give Sparky Stereo OS its 3D modes and deep colour (HDMI 3D modes from the EDID, the InfoFrame, frame-packing timings, deep colour links), how to prove a driver change on a real display, and how to carry driver patches in the edition's kernel while mainline review takes its time. Load the general sparky-stereo skill first.
---

# Drivers: 3D modes and deep colour in the kernel

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; for the colour side also load [`deep-colour`](../deep-colour/SKILL.md).

## What a display driver must do for HDMI 3D

1. **List the 3D modes the display declares:** the HDMI vendor-specific block of its EDID says whether it accepts 3D and which structures (frame packing, side by side, top and bottom) for which video formats, and HDMI 1.4 makes some of them mandatory for every 3D display. The structures and timings are laid out in awesome-stereoscopy's [frame packing and HDMI timings](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/docs/frame-packing-and-hdmi-timings.md) and [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md).
2. **Allow stereo modes** on the connector (`stereo_allowed` in DRM), so they reach user space.
3. **Signal the mode:** the HDMI vendor-specific InfoFrame carries the 3D structure, so the television switches itself.
4. **Time it:** frame packing doubles the vertical total with an active space between the eyes; side by side and top and bottom keep the 2D timing. Full side by side is handled in the DRM core.

Where mainline stands (October 2026): Intel's i915, nouveau and the Raspberry Pi's vc4 allow HDMI stereo modes; stock amdgpu refuses them; the shared HDMI bridge connector that many SoC display drivers build on still reads "[TODO: Handle doublescan_allowed and stereo_allowed](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/display/drm_bridge_connector.c)", so one fix there would open HDMI 3D on every board built on it.

## The work so far, public

- **amdgpu:** expose the HDMI stereo modes and emit the InfoFrame; extend the display core's stream timing for frame packing. Patches in [sony-bravia-linux/docs/upstream](https://github.com/danielcamposramos/sony-bravia-linux/tree/main/docs/upstream). A Sony 3D television switched itself into 3D from System Settings on 2026-10-01.
- **NVIDIA's open kernel modules:** the 3D modes built from the display's HDMI stereo block, and HDMI deep colour at the declared depth ([#1386](https://github.com/NVIDIA/open-gpu-kernel-modules/pull/1386), in review); on an RTX 3060 KWin listed the television's 3D modes and the link ran at 12 bits, the display's own maximum.
- **nouveau:** deep colour on Turing and newer, the piece it was missing (patches in the same folder).
- **Probing:** [`stereo-kms-probe`](https://github.com/danielcamposramos/sony-bravia-linux/tree/main/tools/stereo-kms-probe) lists what a connector offers and sets a stereo mode from the command line.

## Android TV-box vendor kernels (checked 2026-10-07)

- **Allwinner's vendor display stack has HDMI 3D paths.** Its [display header](https://github.com/allwinner-zh/linux-3.4-sunxi/blob/6964d467510849e3e262518cb87bff7ef92e01f5/include/video/sunxi_display2.h) defines stereo layer buffers and frame-packing output modes. Its [HDMI timing table](https://github.com/allwinner-zh/linux-3.4-sunxi/blob/6964d467510849e3e262518cb87bff7ef92e01f5/drivers/video/sunxi/hdmi/aw/hdmi_core.c) includes 1080p24 and 720p50/60 frame packing.
- **Rockchip's vendor HDMI driver has a 3D mode control.** The [mode enum](https://github.com/rockchip-linux/kernel/blob/9ead5f3cbd6e0abd0ac70002205993c953c227ea/drivers/video/rockchip/hdmi/rockchip-hdmi.h) assigns 0 to frame packing, 6 to top and bottom, and 8 to half side by side. The [HDMI implementation](https://github.com/rockchip-linux/kernel/blob/9ead5f3cbd6e0abd0ac70002205993c953c227ea/drivers/video/rockchip/hdmi/rockchip-hdmiv2/rockchip_hdmiv2_hw.c) adjusts frame-packing timing and writes the HDMI vendor InfoFrame's 3D structure.
- **These are vendor interfaces, not portable Android or mainline DRM APIs.** For a TV-box port, identify the actual kernel and display stack, then verify the sink's modes, signalling and restoration to 2D. Source support alone does not qualify an H313/H616 or RK322x board. Keep physical HDMI packing in the output backend; an Android app still supplies full side by side to the edition's compositor.

## Carrying patches until mainline takes them

Kernel review is slow and careful, and a subsystem owes nobody a merge. Plan for it:

- **The edition's kernel carries the patches,** rebased on each release, so users have the feature while review goes on. Nothing in the edition waits for a merge.
- **Send in kernel style:** the subsystem's mailing list (and Patchwork where it uses one), `scripts/checkpatch.pl` clean, one logical change per patch, a cover letter that states the measured result on real hardware, a `Tested-by:` only from someone who ran it.
- **Disclose AI assistance once,** in the form the kernel uses (an `Assisted-by:` trailer).
- **Respect each subsystem's policy on AI-written code.** Some subsystems do not accept it; read the policy before sending (known policies are collected in [sony-bravia-linux/docs/ai-contribution-policies.md](https://github.com/danielcamposramos/sony-bravia-linux/blob/main/docs/ai-contribution-policies.md)). Where it is not accepted, the work stays in the edition's kernel and the conversation stays polite; the subsystem decides.
- **Answer review with measurements,** not opinions: the timing table, the InfoFrame bytes, a capture of the display's own info screen.

## Proof for this kind of work

- The connector's mode list before and after, from `stereo-kms-probe` or the compositor (KScreen labels 3D modes "(3D …)").
- The display switching itself into 3D, shown by its own info screen, on real hardware.
- For frame packing: the timing compared with the HDMI table, and both eyes captured where the hardware allows.
- For deep colour: the link depth the driver set, and the display's own report.
- The 2D control: every 2D mode unchanged.
