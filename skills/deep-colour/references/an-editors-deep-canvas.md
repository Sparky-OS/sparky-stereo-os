# An editor's deep and HDR canvas: GIMP 3.2 through GTK 3's GtkGLArea

Written on 2026-11-26 (queue row 137, the stereo GIMP's milestone 3).
The area it goes through is [GTK 4 and GTK 3 and GtkGLArea](../../stereo-window-3d-area/references/gtk-glarea.md); the canvas per eye and the depth layers it extends are [an editor's canvas per eye](../../stereo-pictures/references/an-editors-canvas-per-eye.md); what is left is in [GTK pieces still to build](../../stereo-window-3d-area/references/gtk-glarea-plans.md).

Daniel's design (2026-10-15): "gimp ramp up on the working canvas is included, deep sdr/hdr color + hdr - passing to the compositor just like 3D information ... our job is make sure to code it to the specs - inside our contract only!"
Every depth the standard defines, deep colour SDR as well as HDR, described to the compositor beside the stereo declaration; the compositor converts per screen; GIMP never tone-maps for a screen.

## What the person sees

- An image deeper than 8 bits (16 bit integer, half float, 32 bit integer, float, double), or whose profile carries ITU-T H.273 code points (an ICC `cicp` tag: PQ, HLG and the like) or reaches outside sRGB's gamut (Display P3, Rec. 2020, Adobe RGB...), is shown in its own depth and colour state, 2D or 3D. The screen shows what the compositor makes of it: more levels on a deep link, its HDR highlights on an HDR screen.
- An 8 bit sRGB image is drawn exactly as before, 2D (into GIMP's window) and 3D (milestone 1's canvas).
- Where the depth or the description cannot reach the compositor, the canvas takes the next step down and the status bar says, once that step is shown, in the person's language: "The canvas cannot hand this image's own depth and colors to the screen here: it is shown in 16 bits." (or "8 bits"); the exact reason is in GIMP's log (stderr).
- Preferences > Color Management > Color Managed Display: "Show deep images in their own depth and colors" (on by default; gimprc `deep-canvas`). Off, a deep image is shown as before this milestone: GIMP's own 8 bit canvas converted to GIMP's monitor profile, and a stereo image milestone 1's 8 bit sRGB canvas; nothing is told then, since the person chose it. The two paths give different pictures (a person who set a monitor profile only in GIMP sees GIMP's conversion on the old path, the compositor's on the new one), so both are offered.
- Nothing changed in the menus: the depth and the colour state follow the image; "Enable 3D" and "Display Settings…" stay the only 3D options.

## The route

GIMP 3.2's canvas is cairo, rendered through GEGL into an 8 bit render cache and converted to the monitor's profile (`gimpdisplayshell-render.c`, `gimpdisplayshell-profile.c`).
GTK 3 draws a window in 8 bit sRGB.
So the canvas of a deep image goes through the same GtkGLArea milestone 1 gave a stereo image, which GTK 3 +stereo3d2 hands to the compositor on a surface of its own for a plain (one picture) area too, with its format and colour state.

1. **The state** (`app/display/gimpdisplayshell-deep.c`, `gimp_display_shell_deep_describe()`): the image's profile's `cicp` tag (ICC.1:2022 9.2.17; RGB, full range) gives the code points as they are; GIMP's own sRGB and linear sRGB (or a profile babl takes for the same space) are 1/13 and 1/8; any other profile is converted to linear Rec. 2020, 9/8 (ITU-R BT.2020-2 table 3, white D65). Colour management off: sRGB, the values babl converts to it, as the 2D canvas.
2. **The depth** by the image's precision: 8 bits (half float when the state is linear: 8 bits linear band in the shadows), 16 bit integer, half float, float for 32 bit integer, float and double; the area's `GdkMemoryFormat` (`R16G16B16A16_PREMULTIPLIED` and so on) and `GdkColorState` (`gdk_color_state_get_rec2100_pq()`, or `GdkCicpParams` for other code points).
3. **Which images:** a stereo image always (its picture is the area's anyway); a 2D image when it is deeper than 8 bits, carries code points, or is wider than sRGB (its primaries transformed to linear sRGB with Little-CMS in floats fall outside 0..1).
4. **The display transform** to the state, not to the monitor's profile: the same flags as `gimp_widget_get_color_transform()` (the display's intent and black point compensation, or soft-proofing with the simulation profile and its gamut check), after the display filters as in 2D, into `"R'G'B'A float"` or `"RGBA float"` (the state's own encoding; the profile gives the space).
5. **The float caches:** each eye's render cache and picture are `CAIRO_FORMAT_RGBA128F`, premultiplied. What lies around the image (the widgets' backgrounds, the padding, the checkerboard) is drawn in 8 bit sRGB as ever and converted to the state; for a PQ state with its white at 203 cd/m² (Report ITU-R BT.2408, 2.1), as a compositor anchors sRGB content beside PQ content.
6. **The upload:** `GL_RGBA32F` textures with `GL_FLOAT`, blitted into the area's framebuffer of the area's format.
7. **The ladder:** an error of the area with `GDK_GL_ERROR_UNSUPPORTED_FORMAT` (a format or a description the way cannot carry) takes the next step: a float picture in 16 bit integer, then a stereo image in 8 bit sRGB (milestone 1's canvas), a 2D image in the canvas GIMP draws itself. Any other error ends as milestone 1 did. The person is told when a step is shown, not when it is tried.
8. **X11:** an X window holds 8 bits and no description, so a 2D deep image gets no area there (an area would also turn the whole window to OpenGL painting, black with zink); the canvas says so.

## Recipe

1. Read `gimpdisplayshell-render.c` (`gimp_display_shell_render_source()`, the 2D path's three buffers), `gimpdisplayshell-profile.c` and `libgimpwidgets/gimpwidgetsutils.c` (`gimp_widget_get_color_transform()`), `libgimpcolor/gimpcolortransform.c` (`gimp_color_transform_process_buffer()` reads and writes in the buffers' own spaces with the transform's encodings), and milestone 1's `gimpdisplayshell-stereo.c`.
2. Build against GTK 3 +stereo3d2 (`gtk_gl_area_get_surface_error()` is the meson check); `lcms2` joins the display library's dependencies.
3. Prove it with the private KWin's virtual HDR output (below), the GTK proof aid for the views as rendered, and the fixtures.

## The proof

`rig/gimp/proof.sh` in the lane folder: one fresh Stereo KWin per case, milestone 3's private KWin (a virtual output with Rec. 2020 PQ, reference white 203 and peak 1000 cd/m², each eye's frame written as floats on request), GIMP on a fixture at 100 %.

- **Fixtures** (`make_deep_fixtures.py`, by gimp-console): 560 x 300, a green marker the judge finds the image by, an eye tag, a ramp of 256 steps of 2 px over 1/256 of the range from 0.5 (`0.5 + i / 65536`), white and half patches (and in a linear float image a patch of 4.0); precisions u8, u16, half, float, float linear; a 10 and a 12 bit lossless HEIF of the 16 bit image (`file-heif-export`, `pixel-format` rgb); PQ and HLG images with ICC profiles carrying a `cicp` tag and a Display P3 one without (`make_profiles.c`, Little-CMS); a 16 bit stereo image. A check reads each fixture's own ramp first: 1 value at 8 bits, 4 at 10, 16 at 12, 255 at 16 (two steps round together), 9 in half float, 256 in float.
- **Where rendered:** a proof aid in the development GTK only (`GTK_GL_AREA_READBACK=DIR`: each view of the area's framebuffer written as floats on request), never in a package.
- **At the output:** each eye's frame from the private KWin; the white patch against KWin's pipeline for the description (`rig/gtk/colour_values.py`).
- **What KWin received:** its `WAYLAND_DEBUG=server` log in words (`rig/gtk/kwin_received.py`, which also names a `wl_shm` buffer's format).
- **Red rows:** the same frames judged as if the compositor had shown the written values; milestone 2's GIMP on the 16 bit image (8 bits at the output, no deep buffer received); the swapped eyes.

## Measured

Development build (GTK and GIMP from the lane's trees, the GTK proof aid for "rendered"), NVIDIA's EGL, the private KWin's virtual output in Rec. 2020 PQ at 203 cd/m² reference white and 1000 cd/m² peak, 50 rows in 13 minutes (2026-11-27 00:39 to 00:52 UTC, load 31 to 35 on the shared machine), every row as expected. "Values" counts the different values in the ramp's band of 1/256 of the range; the output frame is KWin's half float scanout, which holds 7 or 8 values in that band of PQ.

| Image | GIMP drew (values) | KWin received | At the output (values; white) |
|---|---|---|---|
| 8 bit sRGB | (the 2D canvas, no area) | `wl_shm` ARGB8888 window only, nothing described | 1; 0.5806 (PQ 203) |
| 10 bit HEIF (4 values in the file) | 4 | `wl_shm` XB48, srgb, gamma22 | 4; 0.5806 |
| 12 bit HEIF, loaded at 16 bits (16 in the file) | 16 | `wl_shm` XB48, srgb, gamma22 | 7; 0.5806 |
| 16 bit integer (255 in the file) | 255 | `wl_shm` XB48, srgb, gamma22 | 8; 0.5806 |
| half float (9 in the file) | 9 | dma-buf XB4H, srgb, gamma22 | 8; 0.5806 |
| float (256 in the file) | 256 | dma-buf XB4H (half float: the step to KWin), srgb, gamma22 | 7; 0.5806 |
| float, linear sRGB, a patch of 4.0 | | dma-buf XB4H, srgb, ext_linear | the 4.0 patch 0.729, above white |
| 16 bit, Rec. 2100 PQ (`cicp` 9/16) | | dma-buf XB4H, bt2020, st2084_pq | 8; 0.5171 (KWin's tone curve without mastering data) |
| 16 bit, Display P3 (no `cicp`) | | XB48, bt2020, ext_linear | 7; 0.5806 |
| float, HLG (`cicp` 9/18) | | nothing described: KWin lists no HLG | GIMP's 8 bit canvas; float and 16 bit refused, "shown in 8 bits" told once |
| 16 bit stereo (eyes red and blue), output in 3D | 255 per eye | `wl_shm` XB48 2562x758, srgb, gamma22, declared 3, description and declaration on one surface | 8 per eye, eyes in order; 0.5806 |
| 16 bit on X11 (Xwayland) | | the window only | 1; "shown in 8 bits" told, the reason logged |
| milestone 2's GIMP, 16 bit | | the window only | 1 (the red row of the depth) |
| 16 bit, the preference off | (GIMP's own canvas) | the window only, nothing described | 1; nothing told |
| 16 bit stereo, the preference off, output in 3D | | declared 3, no XB48 | 1 per eye, eyes in order |

Red rows, each failing as it should: the 16 bit frame judged as if KWin had shown the written values (white 1.0 wanted, 0.5806 there), the PQ canvas judged as if its values were shown as they are (0.5806 wanted, 0.5171 there), the left eye judged for the right eye's tag, milestone 2's GIMP for more than 6 values and for an XB48 buffer.
The installed packages (gimp 3.2.8-1+stereo3d3+lc1 and gtk+3.0 3.24.52-3+stereo3d2+lc1 installed by apt into the rig image) give the same numbers in every row: 58 rows in 11 minutes (2026-11-27 02:18 to 02:29 UTC, load 21 to 30), "where rendered" excepted (the proof aid is in the development GTK only), plus a row per 2D depth that nothing is declared for it.
GIMP's own meson tests: 20 of 20 on the development build. GTK's `glarea`, `notify`, `defaultvalue` and `objects-finalize` pass.

## Traps

- **Cairo clamps floats above 1.0.** Symptom: none until an HDR value: a linear float image's 4.0 would show at reference white. Cause: pixman's float combiners clamp to 1.0 (measured with cairo 1.18.4: `SOURCE` and `OVER` of an `RGBA128F` surface onto another, 1:1 and scaled, turn 2.5 into 1.0; 16 bit steps and negative values pass). Fix: the image's samples are copied into the cache and composited over the surroundings by GIMP's own float loop wherever the chunk lands on whole pixels unrotated; a rotated or unevenly scaled view still goes through cairo and is clipped at 1.0 (said in the debug log). Found with a probe of under 40 lines before writing the path: four pixels of an `RGBA128F` surface (2.5, 12.0, -0.25 and steps of 1/65536 from 0.5) painted onto another with `SOURCE` and `OVER`, at 1:1 and scaled by 2 with the nearest filter, then read back.
- **The image's rows interleaved into three narrow strips.** Symptom: the canvas garbled, a checkerboard showing through. Cause: the projection was read into a render-buffer-sized linear GEGL buffer with `GEGL_AUTO_ROWSTRIDE`, which is the chunk's width, not the buffer's. Fix: `gegl_buffer_linear_open (buffer, NULL, &rowstride, format)` and pass that stride. Found by looking at the first capture.
- **A transform that converts twice.** `gimp_color_transform_process_buffer()` reads and writes with the buffers' own babl spaces and the transform's encodings, so the canvas's buffers can be space-less (`"RGBA float"`): their numbers are the state's. A `gegl_buffer_copy()` into a space-less buffer, by contrast, converts to sRGB: only right with colour management off, where the state is sRGB.
- **A fixture's values converted on writing.** Symptom: a PQ fixture's ramp not where it was written. Cause: writing samples with `"R'G'B' float"` into an image whose profile is already PQ makes babl convert from sRGB's curve to PQ's. Fix: write the samples first, then assign the profile (`set_color_profile` keeps the numbers).
- **(rig) no `file-heif-export` in the package rig.** Symptom: `AttributeError: 'NoneType' object has no attribute 'create_config'` when the fixture script asks the PDB for `file-heif-export`. Cause: GIMP registers the HEIF export only when libheif has an encoder (libheif-plugin-x265 or -aomenc), and the rig image built from the installed packages has none. Fix: the fixtures are written by an image that has them (the proof's `FX_IMAGE`); every row still runs on the installed packages.
- **`file-heif-export` refuses `include-color-profile`** ("does not have property"): it is an auxiliary argument the PDB config does not take; the loader then builds the profile from the file's `nclx` box.
- **The person told of a step that fails next.** The first form said "shown in 16 bits" as soon as the 16 bit step was tried, which an HLG image then also failed. Fix: a step is told on the area's `surface-shown` or `stereo-shown`, the last failure as "8 bits".
- **(catalogues) pt_BR's CRLF header lines.** Python's text mode turns them into LF and the patch rewrites the header (43 lines added, 28 removed); read and write bytes (`po-deep.py`), then each catalogue adds 15 lines and removes none, and `msgfmt -c` passes.
- **(rig) the image keeps its entrypoint.** An image committed from a container started with `--entrypoint sh` runs `sh bash script` ("sh: 0: cannot open sh"), and `docker commit -c 'ENTRYPOINT []'` did not clear it (the rig image still listed `["sh"]`): give every `docker run` its own `--entrypoint`. Found when milestone 2's recommends row, the one run without it, read "cannot open sh" instead of apt's record.
- **(rig) a wait that sees itself.** `while pgrep -f build-gtk.sh; do sleep 5; done` in a shell whose own command line holds "build-gtk.sh" never ends: pgrep -f matches the waiting shell. Run the steps one after another in one script instead, or match a process id saved at the start.
- **(rig) an expanded word is not an assignment.** `want b && ROUTE=x $dbg bash ...` runs `$dbg` as the command; use `env ROUTE=x $dbg bash ...`.
