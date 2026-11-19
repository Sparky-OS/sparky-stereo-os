# One separation, one place

Daniel, 2026-11-19: "one separation setting, centralized, tailored TO THE SCREEN not to the element size"; "there's only one separation, and one place to set it up"; "in stereo, the separation is related to eye distance".

## The spec in three lines

1. The person's limits (sunk, popped) are set in one place, the desktop's 3D Depth settings, and built on the display; a program is handed them as pixels of a view 1920 wide of the screen (`kde_stereo_depth_v1.depth_limits`, `_KDE_NET_WM_STEREO_DEPTH_LIMITS`, `stereo_policy_display_depth()`), and Stereo KWin applies `lround(limit * output width / 1920)`.
2. A program that draws a real 3D scene with its own two cameras chooses a separation from them, and the elements around it (its window, its 3D area, its picture, its render buffer) have no say: the same separation for any size.
3. The only arithmetic a place may add is the unit conversion of its buffer: `screen width / 1920 * (buffer width / the width Stereo KWin shows it at)`; never the element's own width over 1920.

## Exceptions, and only these

A program with its own internal 3D settings, and content that carries its own authored pair (a stereo photograph, a film, an icon pair rendered by a tool).
Established programs have no formula tying separation to a window or screen size: Bino's source has no separation or parallax code, sView's separation is the person's own offset, mpv and VLC have none.

## How a place gets the value

One function in the layer: libstereo-declare 1.11 `stereo_depth_limits_for_buffer(screen_limits, output_width, buffer_width, shown_width, out)`, with `stereo_depth_x11_get_buffer_limits` (the output is the RandR monitor the window overlaps most, Xwayland's outputs included) and `stereo_depth_wayland_get_buffer_limits` (the only `wl_output`; with several it answers `-ENOTUNIQ` and a Qt program gives `QWindow::screen()`'s width to the pure function).
The unit test (`tests/test-buffer-limits.c`) runs two RandR monitors, 1920 and 3840 wide, with windows of different sizes on each: 10 and 4 on the first, 20 and 8 on the second, whatever the window's size, and half of that again for a buffer rendered at half the size it is shown.
Programs call it and keep no conversion of their own: Spirula `NativeViewport::buffer_limits`, F3D `vtkF3DGLXRenderWindow::UpdateStereoDepthLimits`, CloudCompare `ccDepthLimits::readX11`, Fraqtive `MeshView::eyeOffset`; the browser's `ReadStereoLimits` already converted correctly (`sunk / 1920 * outputWidth / canvasWidth`) in its own language.

## The proof: a large and a small element on one screen

Show the same content at two sizes on one output, render as shown, capture both eyes as arrays and measure the separation of the same scene feature in output pixels.
It must be the same at both sizes and equal to the limit the fit allows for that feature (the popped limit for the nearest point, the sunk limit for infinity), on a screen of the width the conversion used.
Spirula's engine test (`stereo_camera_pair`) does it on the maths: the same scene shown 1920, 960 and 480 px wide on a 1920 px screen, 2.0 and -4.0 px at all three (the build before gave 2.0, 1.0 and 0.5 and -4.0, -2.0 and -1.0).
Render resolution is the other row: a buffer rendered at half the size it is shown at gets half the pixels of separation, so the screen still gets the limit.

## Traps

- **Symptom:** a small 3D view, a window or a model-viewer area shows almost no depth, "not 3D". **Cause:** the limits were multiplied by the element's width over 1920 (F3D 0008, CloudCompare 0003, Fraqtive 0004, Spirula's fit, the first Dolphin-emulator fit). **Found by:** grepping the patches for `1920` and listing what multiplies it. **Fix:** the screen's width in the numerator, and the buffer-to-shown ratio only where the buffer is not shown 1:1.
- **Symptom:** the boot splash's logo is 4 px at 1920 where the theme had 9.08. **Cause:** ORDER 472 (2026-11-08) cut the levels because the picture looked huge on a notebook; the look was an upscaled anaglyph before any compositor. **Fix:** the theme's own levels, as multiples of the limits Plymouth gives (`STEP_PX = POPPED_LIMIT * 1.135`), scaled by the eye's width over 1920 (the screen's) only.
- **Symptom:** WebXR flat mode, a window narrower than the screen, less separation than the screen's limit. **Cause:** `sunk / 1920 * windowWidth` made the window a view of its own. **Fix:** times the screen's width over the window's, so the window's share is the screen's limit.
- What other programs of the kind do when their window is resized, read at their source on 2026-11-19: see the lane's REPORT (upstream F3D's `render.stereo_eye_angle`, CloudCompare's `eyeSeparation_mm * scale` with scale from the convergence distance, neither reads the window's size).

Wayland: the library cannot tell which output a toolkit surface entered; Stereo KWin sending the output width with `depth_limits` (a protocol 6 field) would remove the last special case.
