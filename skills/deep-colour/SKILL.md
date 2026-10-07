---
name: deep-colour
description: How 10, 12 and 16 bits per colour reach the screen on Sparky Stereo OS, from the display's EDID and the HDMI link through the kernel drivers, Mesa and Qt to a program's canvas, without being cut to 8 bits on the way; and how to prove the depth. Load the general sparky-stereo skill first.
---

# Deep colour, the whole path

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first. HDR facts and measurements are gathered in [awesome-linux-hdr](https://github.com/danielcamposramos/awesome-linux-hdr).

## The rule

Deep colour means the **whole standard**: 10, 12 and 16 bits per colour (HDMI's 30, 36 and 48-bit deep colour), never capped at 12 or at the displays at hand. Any one link that drops to 8 bits drops the whole picture to 8 bits, so every layer is checked: the display, the link, the driver, the compositor, the toolkit, the program.

## The layers, and what was found in each

| Layer | What it needs | Where |
|---|---|---|
| The display | What its EDID declares (deep colour flags, maximum TMDS clock); read it before choosing anything | KInfoCenter's "Stereo 3D and Deep Colour" page (in the edition) |
| The kernel drivers | The link at the depth the display declares, not a fixed 8 | NVIDIA's open kernel modules: HDMI deep colour at the declared depth ([#1386](https://github.com/NVIDIA/open-gpu-kernel-modules/pull/1386), in review); nouveau: deep colour on Turing and newer (patches in [sony-bravia-linux/docs/upstream](https://github.com/danielcamposramos/sony-bravia-linux/tree/main/docs/upstream)) |
| Mesa | Window configs with 10/10/10/2 and 16/16/16/16 (unorm and half float), with alpha | 177 window-capable EGL configs on Wayland with our Mesa |
| Qt | The program's requested `QSurfaceFormat` kept, alpha included. Qt Widgets forced an 8-bit alpha on every translucent window; our Qt keeps the alpha and depth the window asks for (10/10/10/2 or 16/16/16/16), and a window that asks for nothing stays 8/8/8/8 | [`stereo3d-alpha`](https://github.com/danielcamposramos/qtbase/tree/stereo3d-alpha); see [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md) |
| A layer in the compositor's shared memory (`wl_shm`) | A deep buffer format: `XR30` for 10 bits, then `XB48` (16-bit integer) when no half-float format is offered | Qt Multimedia's video layer in the edition |
| The program | Its canvas or video at the source's depth, not converted to 8-bit RGBA on the way | Krita: a 16-bit canvas on Wayland ([`sparky/deep-colour-canvas`](https://invent.kde.org/danielcamposramos/krita/-/tree/sparky/deep-colour-canvas)), and its main window at 16/16/16/16 in a stereo session with the Qt fix above ([`sparky/stereo-canvas-wayland`](https://invent.kde.org/danielcamposramos/krita/-/tree/sparky/stereo-canvas-wayland)); MpvQt's video layer at 10 bits or half float ([`stereo3d`](https://invent.kde.org/danielcamposramos/mpvqt/-/tree/stereo3d)) |

What Krita taught: it forced X11, where under Xwayland it got only 8 bits, and offered only 8 and 10. On Wayland with a 16-bit format, a ramp that held 1 level at 8 bits holds 249 at 16 in the same band. Each canvas in its own layer, in its own deep format, stays the pattern: the layer's depth does not depend on the window's.

## Proof for this kind of work

- **A ramp, counted:** draw or play a smooth ramp over a narrow band (for example 1/256 of the range) and count the distinct levels in the capture: 1 at 8 bits, about 4 at 10, 249 to 256 at 16 in Krita's band. Report the count, not "looks smooth".
- **The configs, listed:** print the EGL config the program actually got, and the link depth the driver set.
- **Stereo too:** the same count in each eye when the area is stereo.
- **The 2D control:** at the same depth, the changed program against the distribution's build, 0 differing pixels.
- **What was not tested, said:** 48-bit links need a 48-bit display; until one is at hand, say so.
