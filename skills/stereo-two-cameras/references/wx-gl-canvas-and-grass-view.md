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
4b. **Translucent pixels.** The rule (Daniel, 2026-11-18) counts a translucent pixel at its contribution-weighted mean depth, and a renderer that draws its transparent models without writing depth (KiCad: `glDepthMask( GL_FALSE )` around `renderTransparentModels`) leaves them out of a depth-buffer read.
   KiCad's recipe, fixed function only, so the models keep the eyes' own alpha: draw the measuring pass into an off-screen framebuffer (colour `GL_RGBA32F`, depth `GL_DEPTH24_STENCIL8`); before the transparent models read the depth and `glDrawPixels` each pixel's distance `(D - near) / (far - near)` into red, with alpha 1 on the scene and 0 on the background, the background at the screen (`C`, where it stands in both eyes); then draw the transparent models in the eyes' own order and blending with the texture stage's RGB set to `GL_SUBTRACT` of the primary colour from itself (black, alpha untouched) and linear fog (`GL_FOG_COORD_SRC` `GL_FRAGMENT_DEPTH`, start `near`, end `far`, colour white), which adds exactly `(D - near) / (far - near)`; every pixel ends as `sum(w_i D_i)`.
   Fog uses the distance without its sign, so for an orthographic view with clip planes on both sides of the camera move the scene `-near` along the view axis for the fog and give the projection the opposite move (the picture does not change).
   Read the colour back; a pixel whose depth changed after the transparent models (KiCad's grid) keeps its own depth, a background pixel no model covers (alpha still 0) is not counted.
   Without a float framebuffer let the transparent models write depth in that pass: they then count at their own depth, which keeps every pixel inside with less depth.
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
GRASS's fringe, north arrow and scale bar are in the scene and counted (see the trap below): with a north arrow at 5 % of the view's height from its bottom (GRASS puts it at the surface's highest elevation, floating above the near ground) the separation falls from 0.00435911 to 0.00163016, equal to the depth map's own fit with the arrow, the arrow's nearest edge measured at -4.04 px, every block inside (100 % of 6,021).

Measured on KiCad 10.0.6 with the edition patches (a reduced build of the `pcbnew` target laid over Debian's same version; a 1083 px view on a 1920 output, the pic_programmer demo board tilted by a drag), from the trace and the capture:

| Limits, view, card | Separation | Nearest, farthest (trace) | Measured 1st to 99th percentile | Inside the limits | Half a pixel from the screen |
|---|---|---|---|---|---|
| 10/4, perspective, AMD | 0.03102816 | -4.000, +2.902 | -3.82 .. +2.81 | 99.93 % of 4,186 blocks | 12.7 % |
| 20/8, perspective, AMD | 0.06205632 | -8.000, +5.804 | -7.43 .. +5.50 | 100 % of 4,161 | 7.0 % |
| 10/4, orthographic (shear), AMD | 0.03629871 | -4.000, +3.857 | -3.83 .. +3.78 | 99.95 % of 4,095 | 12.0 % |
| 10/4, perspective, RTX 3060 (zink) | 0.03101935 | -4.000, +2.893 | -3.81 .. +2.80 | 99.93 % | 12.9 % |

The traced ratio of the two extremes equals the closed form to six digits (perspective -0.725525 against -0.725524, orthographic -0.964275 against -0.964270); the blocks outside the limits are false matches on the board's repeated pads.
A per-block vertical test flags about 8 % of KiCad's blocks with a one to three row shift, symmetric in sign and all on the socket's and the connector's pin columns (vertically periodic): matching aliasing, not vertical disparity; the whole area's rows align best at offset 0 (mean difference 1.43 against 2.06 at one row), and the camera test against an independent projection gives 0.

KiCad's translucent model and the live change of the limits (the reduced build of the same patched source, 10/4 unless named; a 20.3 mm square plate of opacity 0.8, 40 mm above the board's centre, nearer than every opaque pixel; its pixels measured from the capture as 0.8 times the plate's own disparity plus 0.2 times the board's under it, the plate row by row from its magenta pixels, the board as a plane fitted to its blocks):

| Row | Separation | Nearest (trace) | Plate's own disparity | Weighted disparity of the plate's pixels |
|---|---|---|---|---|
| before patch 0006, perspective | 0.03102816 (as with no plate) | 13.7027, the board's | -5.19 .. -6.97 | down to -5.59: 6,579 of 8,281 pixels past the popped limit of 4 |
| patch 0006, perspective, AMD | 0.02320419 | 13.0699, the plate's mean | -3.91 .. -5.21 | -2.92 .. -4.18: none past (0.25 px tolerance) |
| patch 0006, orthographic | 0.02837594 | 13.0668 | -3.84 .. -4.82 | -2.86 .. -3.86 |
| patch 0006, RTX 3060 (zink) | 0.0232058 | 13.0701 | -3.91 .. -5.21 | -2.91 .. -4.18 |

The plate's own layer stands past the limit, as the rule allows for a single layer inside a pixel; the pixels do not.
The installed package (kicad 10.0.6+dfsg-1+stereo3d1+lc1, apt from the stage over Debian's) gives the same numbers as the reduced build to the trace's last digit: 0.03098766 at 10/4 perspective, 0.06197532 at 20/8, 0.03625176 orthographic, 0.03099471 on the RTX 3060, 0.02320419 with the plate; Enable 3D off equals Debian's picture to the pixel (0 of 689,871 in the 3D view, 0 on the screen); the German, Portuguese and Japanese sentences on screen from its catalogues.
Without a translucent model the fit moved by 0.1 % (separation 0.03098766 against 0.03102816): the depth now comes from a single-sample buffer instead of the window's multisampled one.
Live: with the view open at 10/4, the rig wrote `[StereoDepth]` 20/8 into the session's kwinrc and called `org.kde.KWin.reconfigure`, and sent nothing to the program; Stereo KWin rewrote the property on the 3D area, the program's quarter-second poll saw it and drew the next frame at separation 0.06197532 (from 0.03098766), measured -7.40 .. +5.50.
GRASS did the same (0.00435911 to 0.00871822, measured -8.01 .. +5.00).

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
- **Symptom:** the build machine's root disk fills while Debian's KiCad package builds; `dh_install` stops with "No space left on device" after a full compile and `make install`.
  **Cause:** Debian's rules build KiCad's QA test programs too (`nocheck` keeps them from running, not from being built) and everything carries `-g` debug information: the tree was 31.5 GB when `make install` began, and the install and the package copies come on top.
  **Fix:** the edition's recipe adds `-DKICAD_BUILD_QA_TESTS=OFF` to Debian's CMake options (qa/ has no install rule, so the package's paths do not change) and compresses the debug information in the objects and linked files (`DEB_CXXFLAGS_MAINT_APPEND=-gz=zstd`, `DEB_LDFLAGS_MAINT_APPEND=-Wl,--compress-debug-sections=zstd`; dh_strip compresses the dbgsym anyway). Measured on the final build (four threads on a loaded machine, 1 h 27 min): 2,139 compiled units against 2,727 with the QA programs, the tree 11.6 GB at the end of the compile and 19.1 GB at its peak (the Lean Code gate's scratch at the very end), the package's 413 paths equal to Debian's (only the Lean Code record added). Run the build with a guard (rig/disk-guard.sh of ORDER 50 step 3: every 20 s the free space, the tree's size and the build's phase; under the floor it kills the container and removes the tree). For a code change alone, the reduced build (target `pcbnew`, Release, no QA programs, no catalogues: rig/kicad-dev-build.sh, about 35 minutes at four threads and 2.9 GB on disk) laid over the same version's package in the rig is enough, and a change rebuilds in minutes.
  **How found:** the first build reached 0 MB at the copy step; a second one without the QA programs alone was on course for about 28 GB at its peak (8.0 GB of tree at 50 % of the compile, half of each object debug information, read with `readelf -S`), more than the disk had above the floor while other lanes wrote, and was stopped and restarted with the debug information compressed.
- **Symptom:** KiCad's 3D viewer told nothing although the depth limits were not offered (identical eyes, no info bar). **Cause:** a board (re)load in the same frame reports its own warning, often an empty one, into the same `INFOBAR_REPORTER` (`BOARD_ADAPTER::InitSettings`), which keeps only the last message, so the sentence was replaced and the bar dismissed; the sentence was marked as told and never came back. **Fix:** say it after the render passes, and only when the frame has no warning of its own (otherwise on the next frame). **How found:** a libstereo-declare stand-in answering `-ENOTSUP` (preloaded into KiCad, mounted over the library for GRASS's ctypes), then reading who else reports into the bar.
- **Symptom:** a KiCad row driven in German never tilts its board. **Cause:** the rig found the viewer window by its English title "3D Viewer"; in German it is "3D-Betrachter". **Fix:** search for every language's title (`xdotool search --name '3D Viewer|3D-Betrachter'`).
- **Symptom:** a vertical-disparity test flags blocks of a picture with vertical stripes. **Cause:** a stripe matches every row alike, so the smallest cost picks a row at random. **Fix:** count a row shift only when it matches clearly better than row 0, and check the whole area's row offset as well.
- **Symptom:** GRASS has no zh_TW catalogue. **Fix:** a new `grasswxpy_zh_TW.po` with only the added sentences: Python's `gettext.translation` chains every catalogue it finds, so zh_TW still falls back to GRASS's `zh` catalogue for the rest.
- **Symptom:** every rig session stops at once: "dbus[11]: Failed to start message bus: Memory allocation failure in message bus", then "dbus-run-session: EOF reading address from bus daemon".
  **Cause:** the container runs as uid 1000 and the image has no passwd entry for it; dbus-daemon 1.16 cannot look the user up and reports it as a memory failure.
  **Fix:** `useradd -u 1000 -m rig` in the rig image (ORDER 50 step 3's `make-rig.sh` does).
  **How found:** `dbus-run-session -- true` alone fails in the image as uid 1000 and passes after the user exists.
- **Symptom:** a lane suspects GRASS's north arrow, scale bar and fringe are left out of the fit, because `UpdateMap` draws them after the measurement pass.
  **Cause of the doubt:** that later call (`_DrawDecorations`, upstream's own, which in 2D draws them again on the front buffer after the swap, "otherwise it don't have to be visible on some computers") is a second drawing at the same place; GRASS's full draw, `Nviz_draw_all` in `lib/nviz/draw.c`, already draws every fringe, the north arrow and every scale bar into the scene, so the pass from the camera between the eyes counts them.
  **How found:** a north arrow nearer than all ground (GRASS puts it at the surface's highest elevation) made the program's separation fall from 0.00435911 to 0.00163016, equal to an independent fit from the depth map with the arrow, and the arrow's own disparity, measured row by row from its black pixels, reached -4.04 px at the popped limit of 4.
- **Symptom:** a test scene with a translucent model at opacity 0.5 above the board never gives a pixel past the popped limit, even on the build that leaves the model out of the fit.
  **Cause:** the rule weights each layer by its share, and the board under the model stands near the screen, so half of the model's disparity is averaged away.
  **Fix:** give the red row a model whose weighted pixels must pass: opacity 0.8 and 40 mm above the board's centre, nearer than the board's front edge.
  **How found:** the rows at 8 mm and 0.5 (weighted -1.69 px) and at 40 mm and 0.5 (-3.47 px) measured inside on the old build.
- **Symptom:** a colour mask for one model of a KiCad picture also catches the navigator in the corner. **Fix:** keep the largest connected blob (`scipy.ndimage.label`).
- **Symptom:** a lane cannot tell its crashes apart after its `--rm` containers are gone. **Fix:** start each with `--cidfile FILE` and append the file's ID to the lane's `.container-ids` when it ends.
- **Symptom:** a KiCad row must tick a box in Preferences on a 2D screen and there is no accessibility bus in the rig. **Fix:** open Preferences from the 3D viewer with Ctrl+, (a 980x652 dialog at +150+34 on a 1280x720 Xvfb screen), click "Realtime Renderer" in the tree (258,323) and the "Enable 3D" box (387,167): the "Information" dialog that tells the person opens over it; read the positions from a picture of each step first, since a language with taller glyphs may move the tree's rows.
