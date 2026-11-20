# A wxWidgets GL canvas and GRASS's 3D view as declared 3D areas (KiCad, GRASS GIS)

Learned on ORDER 50 step 3 (November 2026): KiCad 10.0.6 (Debian 10.0.6+dfsg-1) and GRASS GIS 8.5.0 (Debian 8.5.0-1), on Stereo KWin 6.7.4 +stereo3d59, Mesa 26.1.6 +stereo3d26, Xwayland 24.1.15 +stereo3d3 and libstereo-declare 1.12.1.
Load it with [`stereo-two-cameras`](../SKILL.md) and [native-linux's depth limits page](../../native-linux/references/depth-limits-declare.md) when a wx (C++ or wxPython) program's OpenGL view should show a stereo pair.

## The result first

Both programs draw their 3D view twice, from two parallel cameras with an off-axis frustum meeting at the look-at point (KiCad) or the focus point (GRASS), into the left and right back buffers of a quad-buffer GLX visual.
The edition's Mesa packs the two at the swap and declares the GL child window; Stereo KWin shows it per eye at the child's place and writes the person's depth limits on it.
The separation is the largest under which every pixel of the view stays inside those limits; neither program has a separation setting.
Their only 3D options are Enable 3D (on by default, applied when the 3D view is made) and a button to Display Settings.

## Which case a program is

Settle it from upstream's own source before anything else: a program that already draws its own pair keeps its own separation (Daniel, 2026-11-18); a program where we add the cameras is fitted to the person's limits.

```sh
grep -rn -i -E 'stereo|GL_BACK_LEFT|GL_BACK_RIGHT|GL_STEREO|anaglyph|eye_?sep' SRC/3d-viewer SRC/common/gal/3d     # KiCad
grep -rn -i -E 'stereo|GL_BACK_LEFT|GL_STEREO|eye_?sep|anaglyph' SRC/lib/ogsf SRC/lib/nviz SRC/gui/wxpython/nviz  # GRASS
```

KiCad 10.0.6 has one hit, `glReadBuffer( GL_BACK_LEFT )` for a screenshot; GRASS 8.5.0 has none (its tree's only "stereo" words are a Vis5D projection name and a lidar comment).
Both are programs where we add the cameras.

## The recipe

1. **The window route.** Debian's wxWidgets 3.2 is built with `wxUSE_GLCANVAS_EGL 0`: its GL canvas is GLX only.
   KiCad sets `GDK_BACKEND=x11` itself when wx has no EGL canvas (`libs/kiplatform/os/unix/environment.cpp`); GRASS did not, so the edition's GRASS does the same in `gui/wxpython/core/globalvar.py`, before wx opens its display, and keeps a `GDK_BACKEND` the person set.
   The 3D view is then a GLX child window under Xwayland: the declared X11 child of [x11-declared-child-limits-and-first-pair.md](../../native-linux/references/x11-declared-child-limits-and-first-pair.md).
2. **The visual.** Ask for a stereo visual when Enable 3D is on and `wxGLCanvas::IsDisplaySupported` offers one (KiCad: `wxGLAttributes::Stereo()`, wxPython: `WX_GL_STEREO`); draw the two eyes only when the context reports `GL_STEREO` and the setting asks, because the edition's Mesa may give a stereo visual to a mono request.
3. **The limits.** Read them on the drawable the context is current on: `glXGetCurrentDisplay()`, `glXGetCurrentDrawable()` (wxGLCanvas makes the X window itself current), then `stereo_depth_x11_get_buffer_limits(display, window, width, width, &limits)`, `width` being the view's width in device pixels.
   They come in the view's pixels; the program adds no arithmetic of its own.
   In C++ put the GLX and libstereo-declare includes in a file of their own (KiCad's renderers include glad, which refuses `GL/gl.h`); from wxPython load `libstereo-declare.so.1` with ctypes, as GRASS reaches its own C libraries.
   `-ENODATA` at the first frames is normal: Mesa declares the child at its first swap of the eye buffers, and Stereo KWin writes the property after it takes the child.
   Draw identical eyes until the limits come, read them again four times a second, redraw when they change, and tell the person once if they have not come after two seconds (or are not offered at all).
4. **The fit, by pixels.** Before the two eyes, draw the view once from the camera between the eyes into the left back buffer and read its depth buffer (`glReadPixels`, `GL_DEPTH_COMPONENT`, `GL_FLOAT`) before any 2D overlay is drawn; every pixel below the cleared depth is the scene.
   Turn the nearest and farthest window depth into distances with the projection of that draw: perspective `D = B / ((2d - 1) + A)`, orthographic `D = (B - (2d - 1)) / A`, `A = P[2][2]`, `B = P[3][2]` (GRASS's `glFrustum`: `D = n f / (f - d (f - n))`).
   With `k` half the view's width in pixels times `P[0][0]`, the zero-parallax distance `C` and the separation `t` as a fraction of `C`, a point's disparity is `k t (1 - C/D)` in perspective and, for an orthographic shear of `t` per unit of depth, `k t (D - C)`.
   The separation is the smallest of `sunk / (k (1 - C/Dfar))` and `popped / (k (C/Dnear - 1))` (orthographic: `sunk / (k (Dfar - C))`, `popped / (k (C - Dnear))`); with nothing off the zero-parallax plane, a perspective view puts infinity at the sunk limit.
5. **The options.** Enable 3D on by default (KiCad `render.opengl_stereo` in `3d_viewer.json`, GRASS `display:nvizStereo:enabled`), applied when the 3D view is made because the visual is chosen at creation; a screen with no stereo visual stays one picture without a word; a person who ticks Enable 3D there is told.
   Display Settings: `systemsettings kcm_kscreen`, else `kcmshell6 kcm_kscreen`, and say so when neither starts.

## Proof

The rig scripts of ORDER 50 step 3 drive each program as a person does: KiCad's PCB editor opens a demo board, Alt+3 opens the 3D viewer, an XTEST drag tilts it (KiCad has no tilt hotkey; the drag reaches it on Stereo KWin +stereo3d59 with `XwaylandEisNoPrompt=true`); GRASS's own wxGUI is driven in-process (add the DEM, pick "3D view", drape a textured raster).
KiCad traces each stereo frame with `KICAD_ENABLE_WXTRACE=1 WXTRACE=KI_TRACE_EDA_3D_CANVAS` (a release build needs both); GRASS says its fit at debug level 3 (`DEBUG: 3` in `~/.grass8/rc` before the start: `g.gisenv` inside a `grass --exec` session only writes a temporary gisrc), and the GRASS driver reads the depth map of the camera between the eyes straight from OpenGL (`glReadPixels` of the depth and `GL_PROJECTION_MATRIX` after a draw with the separation at 0), so the prediction for every block does not lean on the program's fit.

Measured on GRASS 8.5.0-1+stereo3d1 (a 1132 px view on a 1920 output, the October lane's synthetic relief with a textured raster draped):

| Limits, card | Separation (program / from the depth map) | Nearest, farthest predicted | Measured range | Blocks within 1 px of the per-pixel prediction | Half a pixel from the screen |
|---|---|---|---|---|---|
| 10/4, AMD | 0.00435911 / 0.00435912 | -4.000, +2.331 | -4.04 .. +2.70 | 99.96 % of 5,060 (median abs 0.066) | 23.8 % |
| 20/8, AMD | 0.00871822 / 0.00871824 | -8.000, +4.662 | -8.01 .. +5.00 | 99.92 % of 5,006 (median abs 0.093) | 11.7 % |
| 10/4, RTX 3060 (zink) | 0.00435928 / 0.00435929 | -4.000, +2.331 | -4.04 .. +2.68 | 99.94 % of 5,060 | 23.8 % |

Every matched block inside the limits, vertical disparity 0, 0 pixels differ between the eyes outside the 3D area; with Enable 3D off the 3D view equals Debian's to the pixel (0 of 996,160).

## Traps, symptom first

- **Symptom:** on a Wayland desktop GRASS stops when its 3D view opens: "Fatal Error: This program wasn't compiled with EGL support required under Wayland, either install EGL libraries and rebuild or run it under X11 backend by setting environment variable GDK_BACKEND=x11". Debian's own GRASS 8.5.0 does it too.
  **Cause:** Debian's wx 3.2.11 has no EGL GL canvas (`wxUSE_GLCANVAS_EGL 0`), and GRASS lets GTK pick Wayland.
  **Fix:** set `GDK_BACKEND=x11` before wx opens its display when the GL library wxPython loaded has no `wxGLCanvasEGL` (`hasattr(ctypes.CDLL(lib), "_ZN13wxGLCanvasEGL11SwapBuffersEv")`; the positive control is `_ZN13wxGLCanvasX1111SwapBuffersEv`).
  **How found:** running the GUI in the rig with the session's own `WAYLAND_DISPLAY` and no `GDK_BACKEND`; the October harness had set `GDK_BACKEND=x11` and never met it.
- **Symptom:** a mangled name test says "not found" for a symbol `nm -D` lists. **Cause:** a miscounted length (`wxGLAttributes` is 14 characters, `14wxGLAttributes`). **Fix:** copy the name from `nm -D --defined-only`, and test a symbol that must be there before trusting a "not there".
- **Symptom:** an audit lists GRASS's 3D view as a program with its own separation. **Cause:** the audit read the setting our own October patch added. **Fix:** grep upstream's tree, never our patch, for the program's own pair.
- **Symptom:** a GRASS driver never reaches its measurement; a modal "Failed to load image from file .ppm" stands over the GUI. **Cause:** in a container glycin's image loaders have no sandbox, and the 2D map's PPM load fails. **Fix:** close modal dialogs from a timer in the driver; and since GRASS's GUI sends stdout into its own console, signal a finished step with a file, not a printed line.
- **Symptom:** `x11_props.py` stops with `TypeError: Object of type bytes is not JSON serializable` on KiCad's windows. **Cause:** a window title in UTF-8 that Xlib returns as bytes. **Fix:** decode bytes when writing the JSON (the script in stereo-proof-rig does since this change).
- **Symptom:** the package build stops at once: "unmet build dependencies: node-acorn nodejs python3-yaml". **Cause:** `lean.debian_prepare` adds the Lean Code tools to Build-Depends. **Fix:** put them in the builder image.
- **Symptom:** `msgfmt -c` fails on KiCad's own catalogues (and GRASS's pt_BR) before any change. **Cause:** upstream entries with mismatched format strings. **Fix:** count the errors before and after the patch, and check the added entries alone.
- **Symptom:** a rig variable named `GRASS_DEBUG` makes `grass` print "GRASS_DEBUG environmental variable is set. It is meant to be an internal variable for debugging only this script" and GRASS's own debug lines never come. **Cause:** the launcher owns that name. **Fix:** name rig variables with a prefix of your own (`RIG_...`) and set GRASS's level with `DEBUG: 3` in its rc file.
- **Symptom:** the build machine's root disk fills while Debian's KiCad package builds; `dh_install` stops with "No space left on device" after a full compile and `make install`. **Cause:** Debian's rules build KiCad's QA test programs too (`nocheck` does not stop that) and the whole build carries `-g` debug information: the build tree was 31.5 GB when `make install` began, and the install and the package copies come on top. **Fix:** start a KiCad package build only on a disk with about 40 GB free, watch it, and pause the container before the disk reaches its floor; for a proof of a code change alone, build the `pcbnew` target with `-DKICAD_BUILD_QA_TESTS=OFF` and no debug information (a few GB) and lay its files over the same version's package in the rig. **How found:** the disk guard reached 0 MB at the copy step (ORDER 50 step 3).
- **Symptom:** GRASS has no zh_TW catalogue. **Fix:** a new `grasswxpy_zh_TW.po` with only the added sentences: Python's `gettext.translation` chains every catalogue it finds, so zh_TW still falls back to GRASS's `zh` catalogue for the rest.
