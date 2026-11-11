---
metadata:
  requires-packages: dkms | edid-decode
name: drivers
description: >-
  Kernel and display-driver work for stereo and deep colour: the HDMI 3D modes an EDID declares and the kernel lists
  (amdgpu, NVIDIA, nouveau, VC4), USB-C 3D glasses, the edition's kernel configuration (Secure Boot without lockdown,
  the real-time flavour), DKMS modules on a new kernel (NVIDIA, ZFS, openssl for signing, first-boot MOK enrolment,
  linux-headers without gcc), udev rules for wheels tested without hardware (umockdev), HDMI-CEC, VRAM protection,
  patches carried with provenance. Load it when a 3D mode is missing, the TV never switches to 3D, a DKMS build fails on
  a new kernel, dkms says openssl not found and the module is unsigned, modprobe says Key was rejected by service,
  ConditionFirstBoot never fires, nouveau reports firmware unavailable, amdgpu hangs with a page fault, ring timeout and
  a device coredump, an old Radeon repeats a successful IP block soft reset with device wedged but no recovery needed,
  virtio-gpu oopses with stereo on, or a udev chmod hides its failure behind || true.
---

# Drivers: 3D modes and deep colour in the kernel

## Working recipe

1. Save the EDID, connector modes, kernel/driver revision and current 2D behavior before changing mode handling.
2. Test mode construction and timing in VKMS first; use an authorized physical display for signaling and link qualification.
3. Return mode/timing differences, InfoFrame or display evidence, 2D regressions and untested hardware. A virtual driver cannot prove a cable handshake.

**Check freshness first.**
Written on 2026-10-07; the kernel configuration and its traps, the carried gamepad fix and the test without firmware added on 2026-11-02.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; for the colour side also load [`deep-colour`](../deep-colour/SKILL.md).

## What a display driver must do for [HDMI®](https://www.hdmi.org/resource/brand) 3D

1. **List the 3D modes the display declares:** the HDMI® vendor-specific block of its EDID says whether it accepts 3D and which structures (frame packing, side by side, top and bottom) for which video formats, and HDMI® 1.4 makes some of them mandatory for every 3D display. The structures and timings are laid out in awesome-stereoscopy's [frame packing and HDMI® timings](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/docs/frame-packing-and-hdmi-timings.md) and [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md).
2. **Allow stereo modes** on the connector (`stereo_allowed` in DRM), so they reach user space.
3. **Signal the mode:** the HDMI® vendor-specific InfoFrame carries the 3D structure, so the television switches itself.
4. **Time it:** frame packing doubles the vertical total with an active space between the eyes; side by side and top and bottom keep the 2D timing. Full side by side is handled in the DRM core.

Where mainline stands (October 2026): Intel's i915, nouveau and the Raspberry Pi's vc4 allow HDMI® stereo modes; stock amdgpu refuses them; the shared HDMI® bridge connector that many SoC display drivers build on still reads "[TODO: Handle doublescan_allowed and stereo_allowed](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/display/drm_bridge_connector.c)", so one fix there would open HDMI® 3D on every board built on it.

## The work so far, public

- **amdgpu:** expose the HDMI® stereo modes and emit the InfoFrame; extend the display core's stream timing for frame packing. Patches in [sony-bravia-linux/docs/upstream](https://github.com/danielcamposramos/sony-bravia-linux/tree/main/docs/upstream). A Sony 3D television switched itself into 3D from System Settings on 2026-10-01.
- **NVIDIA's open kernel modules:** the 3D modes built from the display's HDMI® stereo block, and HDMI® deep colour at the declared depth ([#1386](https://github.com/NVIDIA/open-gpu-kernel-modules/pull/1386), in review); on an RTX 3060 KWin listed the television's 3D modes and the link ran at 12 bits, the display's own maximum.
- **nouveau:** deep colour on Turing and newer, the piece it was missing (patches in the same folder).
- **Probing:** [`stereo-kms-probe`](https://github.com/danielcamposramos/sony-bravia-linux/tree/main/tools/stereo-kms-probe) lists what a connector offers and sets a stereo mode from the command line.

## Android TV-box vendor kernels (checked 2026-10-07)

- **Allwinner's vendor display stack has HDMI® 3D paths.** Its [display header](https://github.com/allwinner-zh/linux-3.4-sunxi/blob/6964d467510849e3e262518cb87bff7ef92e01f5/include/video/sunxi_display2.h) defines stereo layer buffers and frame-packing output modes. Its [HDMI® timing table](https://github.com/allwinner-zh/linux-3.4-sunxi/blob/6964d467510849e3e262518cb87bff7ef92e01f5/drivers/video/sunxi/hdmi/aw/hdmi_core.c) includes 1080p24 and 720p50/60 frame packing.
- **Rockchip's vendor HDMI® driver has a 3D mode control.** The [mode enum](https://github.com/rockchip-linux/kernel/blob/9ead5f3cbd6e0abd0ac70002205993c953c227ea/drivers/video/rockchip/hdmi/rockchip-hdmi.h) assigns 0 to frame packing, 6 to top and bottom, and 8 to half side by side. The [HDMI® implementation](https://github.com/rockchip-linux/kernel/blob/9ead5f3cbd6e0abd0ac70002205993c953c227ea/drivers/video/rockchip/hdmi/rockchip-hdmiv2/rockchip_hdmiv2_hw.c) adjusts frame-packing timing and writes the HDMI® vendor InfoFrame's 3D structure.
- **Proven on the boards tested (2026):** an Allwinner H616 TV box and a Rockchip RK3228A TV box switch a 3D television into HDMI® 3D on their vendor Android kernels (frame packing on the H616 box, half side by side on the RK3228A box), and both run the HDMI® link at 10-bit RGB.
- **These are vendor interfaces, not portable Android or mainline DRM APIs.** On another board, identify its kernel and display stack first, then check the modes, the signalling and the return to 2D. Keep physical HDMI® packing in the output backend; an Android app still supplies full side by side to the edition's compositor.

## The edition's kernel configuration

Daniel, 2026-10-07: "kernel is the soul, we ship it all we can, with all enhancements possible".
A fast kernel without the modules people need fails them silently, so the configuration in [the build tree's `kernel/config`](https://github.com/Sparky-OS/sparky-stereo-os-build/tree/main/kernel/config) is built this way:

- **Debian's own configuration of the nearest version first,** so every module Debian ships is there (`debian-7.2.11-amd64.config` for the 7.3 kernels).
- **Then what the edition's people need beyond Debian's values,** each a commented pin in `sparky-stereo.config`: Binder with binderfs for Waydroid, sim-rig panels, USB displays and projectors, both NTFS drivers, handheld and laptop drivers; Rust, BTF and sched_ext stay on.
- **Then the proven performance work** of CachyOS and Bazzite, and what XanMod and Liquorix offer, where the licence and the upstream status allow.
  The patches taken are folders of their own in `kernel/series/` (the BORE scheduler, CachyOS's, the handheld series), beside the stereo series.
- **Headers that build DKMS modules** (NVIDIA's open modules, xpadneo and the others), in either install order.
- Performance is measured as information, never as a gate ([`sparky-stereo`](../sparky-stereo/SKILL.md)).

Traps measured on the way:

- **Secure Boot without losing hibernation** (Daniel, 2026-10-08).
  Debian's patch that locks the kernel down under Secure Boot is not carried, so lockdown comes only from the boot command line (`lockdown=integrity`), and hibernation keeps working.
  Under Secure Boot, `IMA_ARCH_POLICY` (`security/integrity/ima/ima_efi.c`) still enforces module and kexec signatures without lockdown.
- **The real-time flavour keeps the EFI runtime services** (build 8, 2026-10-09): `CONFIG_EFI_DISABLE_RUNTIME` stays unset (`flavour-rt.config`).
  With Debian's rt value (`=y`) the platform keyring stays empty under Secure Boot, so modules signed by a key in the firmware's db or in shim's MOK list (NVIDIA's, every DKMS module) are refused.
- **ZFS on a new kernel:** Debian's `zfs-dkms` 2.4.4 names Linux 7.2 as its newest kernel and does not build on 7.3, and its failed build stops the kernel's install script (2026-10-16).
  The edition builds `zfs-linux` 2.4.4-1+stereo3d1 from Debian's source with OpenZFS's own commits for 7.3 (Rob Norris's, and the supported-kernel maximum by ooonea), carried with their authors ([the recipe](https://github.com/Sparky-OS/sparky-stereo-os-build/tree/main/sparky-os/packages/zfs-linux)), and the ISO packer refuses an image without configured ZFS tools and module files for every kernel (`iso-build/zfs-check.py`).
- **NVIDIA's older cards:** Debian's `nvidia-kernel-dkms` 550 does not build on 7.3 (`strncpy`, 2026-10-16).
  The edition's NVIDIA driver is the open kernel modules (615 with its patches), which run Turing and newer; the live image and Hardware Setup run nouveau on older NVIDIA cards, deciding from the open modules' list of devices.

## Carrying patches until mainline takes them

### Keep kernel flavours aligned

Base, x86-64-v3 and PREEMPT_RT carry the same accepted edition fixes and optimizations, including stereo, HDR/deep-colour, virtual displays, input and hardware support. RT is an optional kernel for latency-sensitive workloads, not a reduced-feature audio edition. Compare the retained patch lists and hashes before building a release; an older flavour build is not an acceptable reason to omit an accepted fix. Keep required scheduling/ISA differences explicit. Where RT makes a driver or optimization incompatible, record the exact restriction, affected hardware and test evidence instead of silently dropping it or promising identical hardware support.

Qualify each flavour's final packages, boot, Secure Boot, hibernation and DKMS independently. Measure latency/jitter and missed deadlines for the actual audio/video, robotics or inference pipeline before claiming an RT benefit; kernel scheduling alone does not qualify GPU execution or application timing. Preserve the user's kernel choice and the working fallback.

Kernel review is slow and careful, and a subsystem owes nobody a merge.
Plan for it:

- **The edition's kernel carries the patches,** rebased on each release, so users have the feature while review goes on. Nothing in the edition waits for a merge.
- **Send in kernel style:** the subsystem's mailing list (and Patchwork where it uses one), `scripts/checkpatch.pl` clean, one logical change per patch, a cover letter that states the measured result on real hardware, a `Tested-by:` only from someone who ran it.
- **Disclose AI assistance once,** in the form the kernel uses (an `Assisted-by:` trailer).
- **Respect each subsystem's policy on AI-written code.** Some subsystems do not accept it; read the policy before sending (known policies are collected in [sony-bravia-linux/docs/ai-contribution-policies.md](https://github.com/danielcamposramos/sony-bravia-linux/blob/main/docs/ai-contribution-policies.md)). Where it is not accepted, the work stays in the edition's kernel and the conversation stays polite; the subsystem decides.
- **Answer review with measurements,** not opinions: the timing table, the InfoFrame bytes, a capture of the display's own info screen.
- **A regression fix, carried with its own patch.** Mainline 5cdad13a40ac ("HID: betop: move FF initialization to .input_configured()", 7.3 cycle) turned a failed force-feedback setup into an error from `.input_configured()`, and the HID core then drops the input device.
  A pad without an output report, such as the ShanWan "Frostbite" receiver (20bc:5500, "Shanwan Twin Usb Joystick"), lost every input device, so no program saw a gamepad.
  The edition's kernel carries [HID: betop: keep the input device when the pad has no force feedback](https://github.com/Sparky-OS/sparky-stereo-os-build/blob/main/kernel/series/02-carry-stereo-ramos/0009-HID-betop-keep-the-input-device-when-the-pad-has-no-.patch): a missing or unusable output report means no rumble and a working pad, while allocation and ff-memless errors still fail.
  It has a `Fixes:` tag and `Assisted-by`, and no Signed-off-by from the tool ([`contrib-kernel`](../contrib-kernel/SKILL.md)).
  Mainline's `hid-betopff.c` still returns the error (checked 2026-11-02).
  The fix stays a patch apart from the stereo work, so it can go to the input subsystem's maintainers on its own.

## Proof for this kind of work

- The connector's mode list before and after, from `stereo-kms-probe` or the compositor (KScreen labels 3D modes "(3D …)").
- The display switching itself into 3D, shown by its own info screen, on real hardware.
- For frame packing: the timing compared with the HDMI® table, and both eyes captured where the hardware allows.
- For deep colour: the link depth the driver set, and the display's own report.
- The 2D control: every 2D mode unchanged.
- **A test "without firmware" removes the GPU's whole firmware folder.** For nouveau on an RTX 3060 that is `nvidia/ga106`, then rebuild the initramfs: the log says `acr: firmware unavailable`, `gr: firmware unavailable` and `sec2: firmware unavailable`.
  Renaming only the GSP firmware link is not "no firmware": nouveau then takes its own Ampere path with the ACR, GR and SEC2 firmware, the GR engine comes up, and the code path without a GR engine never runs ([the 2026-10-03 test of the NULL-pointer fixes](https://github.com/danielcamposramos/sony-bravia-linux/tree/main/docs/upstream/nouveau-null-v3-test-2026-10-03); the fixes themselves are in [`search-upstream-first`](../search-upstream-first/SKILL.md)).

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 11 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (52 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

HDMI®, HDMI® High-Definition Multimedia Interface and the HDMI® Logo are trademarks or registered trademarks of HDMI Licensing Administrator, Inc.
