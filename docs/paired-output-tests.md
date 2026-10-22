# Matched displays as one stereo output

This is the acceptance procedure for two matched panels or projectors, one per eye.
It exercises the existing **Dual projection** and **Mirror rig** modes in Display Configuration.
Applications still supply full side by side; KWin owns eye assignment and output conversion.

**Status, 22 October 2026:** the freeze of the 20 October physical test (AMD Cezanne left, NVIDIA RTX 3060 right, two Sony displays at 1920×1080, 60 Hz) is understood and fixed.
`DrmGpu::presentStereoPair()` looked for the partner only among its own GPU's outputs, so every frame of a pair split over two GPUs failed, and each failure re-probed every connector on both GPUs, which slowed the third monitor; the saved pair froze again after a restart.
A pair on one GPU could also crash KWin, because the pair's commit could be freed by the other output's commit thread.
Eight KWin commits fix both, with five new tests that fail first: across GPUs each output shows its own eye, on one GPU the pair's commit stays on one commit thread, a frame waiting for its partner is released, and a mode change while paired works.
They are on the [paired-output-recovery branch](https://github.com/Sparky-OS/kwin/tree/paired-output-recovery), packaged as kwin `4:6.7.4-2+stereo3d29`.
In a VKMS guest, 41 runs over every topology and action ended with no crash and no freeze, and the 19 mock DRM pair tests pass.
How the two GPUs time their flips against each other still needs a physical test. Ordinary desktop mirroring across GPUs is a separate behavior.

## Configurations

Use two outputs with matching pixel dimensions, refresh rate and scale, starting with 1920×1080 at 60 Hz and scale 1. Keep another ordinary display available for operating the test.

| Case | Connections | Purpose |
|---|---|---|
| Matched pair | Two connectors on one GPU | Shared composed pair, one atomic DRM submission |
| Matched pair across GPUs | One connector on each GPU | Preserve the same pair through buffer transfer and both driver submissions |
| Mirror rig | Either qualified connection route | Apply the required reflection once, after eye selection |

A monitor with built-in mirror correction starts with **Reflection: None**. The asymmetric chart below establishes whether any software correction is needed.

## VM configuration

Use an isolated guest with the edition's KWin and KScreen. Two ordinary display connectors are sufficient: each connector shows one eye at its own mode's size, so this test does not require a packed HDMI 3D mode on either connector.

For one virtual GPU with two outputs, replace the VM's video-device arguments with:

```sh
-vga none -device virtio-gpu-pci,max_outputs=2,xres=1920,yres=1080,max_hostmem=1G
```

For two virtual GPUs with one output each:

```sh
-vga none \
-device virtio-gpu-pci,id=eye-gpu-a,max_outputs=1,xres=1920,yres=1080,max_hostmem=1G \
-device virtio-gpu-pci,id=eye-gpu-b,max_outputs=1,xres=1920,yres=1080,max_hostmem=1G
```

These are device configurations, not a claim that the guest test has passed. Record the guest's actual DRM device and connector mapping before testing; two connectors on one card do not exercise transfer between GPUs.

## Observable checks

Before another physical test, reproduce activation and recovery in a guest. Keep a guest console or SSH path available independently of the tested compositor. A timed restore using the same Wayland connection is insufficient if rendering failure prevents client responses. Save output identities and mode properties, then rediscover current protocol objects for restoration; do not assume their lifetimes survive a configuration change. Verify restoration of every output's position and priority, including outputs outside the pair.

1. Save the original output configuration, package versions and connector mapping. Configure reciprocal partners with complementary left/right roles, matching mode and scale, and the same logical desktop position.
2. Show a synthetic pair with LEFT and RIGHT labels, an asymmetric corner marker, a grid and a circle in each eye. Each connector must show its assigned eye filling its mode, with matching geometry and no squeeze. Check ordinary menus and pointer coordinates too.
3. Animate both eyes from one frame counter, committed as one full-SBS buffer. At the output handoff, the selected halves must carry the same counter. Count mismatches and repeated complete pairs separately; a repeated complete pair is not an eye-pair mismatch.
4. On one GPU, record both primary planes' framebuffer IDs and source rectangles in the same atomic submission. Expect one shared framebuffer and complementary crops, one eye each.
5. Across GPUs, record the source generation and completion of the buffer transfer before either eye advances. Framebuffer IDs are local to each DRM device: numeric equality across devices proves nothing. Inspect both resulting images and their frame counters.
6. Swap eyes for the pair, then restore them. Exercise horizontal and vertical reflection with the asymmetric marker; only the selected output is reflected.
7. Return to ordinary 2D, restore the saved setup, and verify that both displays remain usable.

Retain an intentional wrong-eye or mismatched-counter control that the checker rejects. A raw stereo screenshot alone does not establish which eye a physical connector received: inspect the output crop and submitted buffer as well.

The software acceptance boundary is the complete stereo pair handed to the drivers. Record physical display observations separately, without moving display-specific responsibilities into the applications.
