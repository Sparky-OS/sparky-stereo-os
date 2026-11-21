# Programs that draw OpenGL quad-buffer stereo, swept on the edition's desktop

A program that asks for a stereo visual and draws `GL_BACK_LEFT` and `GL_BACK_RIGHT` needs no change on the edition: Mesa gives the window two views and declares it as full side by side, and Stereo KWin does the rest (see the [contract](../../sparky-stereo/SKILL.md#part-one-the-contract)).
This page records the sweep of 18 November 2026 (ORDER 26): which program has which switch, which route it takes, the capture recipe and the traps.
Versions are those of that day: Mesa 26.1.6-1+stereo3d24, Xwayland 24.1.15-1+stereo3d3, Stereo KWin 6.7.4-2+stereo3d58 from the published tree, Debian testing for everything else.

## The short recipe

1. One throwaway container from `debian:testing` with the published tree as an apt source (pin 1001) **and deb-multimedia** (our Blender and FFmpeg libraries need `libaom3 >= 1:3.15.3` from it; without it apt answers `libavcodec63 ... [no choices]`).
2. A fresh `HOME` for every case (KWin keeps its output configuration and window states there) holding `.config/kwinrc` with `[Xwayland]` `XwaylandEisNoPrompt=true`, so `xdotool` reaches X11 clients.
3. `dbus-run-session`, then `kwin_wayland --virtual --xwayland --socket=w --width 1280 --height 800`, the program on `DISPLAY=:0` (Xwayland) or `WAYLAND_DISPLAY=w`, wait, `capture.py` twice, `x11_props.py` for the declarations. The GPU is a render node (`--device /dev/dri/renderD128 --group-add 125`) or the RTX 3060 through CDI (`--device nvidia.com/gpu=0`); with no GPU ScreenShot2 answers `Cancelled`.
4. On the NVIDIA row source the session's own `/etc/xdg/plasma-workspace/env/sparky-stereo-opengl.sh` (unpack the published sparky-stereo-hardware; it needs `kreadconfig6`, from `libkf6config-bin`, or it exports nothing) with `SPARKY_STEREO_OPENGL_CONF` naming a file that holds `desktop=nvidia` and `opengl=zink`.
5. Read the capture as two RGB arrays. A stereo capture is twice the output's width; a one-view capture is not stereo. Count differing RGB pixels, count them outside the declared area, measure the shift in pixels with its sign, and run the swapped reading, which must fail.

## Eye tags that work

| Program | The tag | Why it can fail |
|---|---|---|
| any scene | a near object tagged green (nearer than the zero-parallax plane, crossed, shift negative) and a far one tagged red (uncrossed, shift positive); the centroid of each colour in the right eye minus the left | swapped eyes flip both signs and fail |
| osgviewer | the program's own `--stereo LEFT_EYE` and `--stereo RIGHT_EYE` renderings of the same window, compared pixel for pixel with each eye of `--stereo QUAD_BUFFER` | 0 differing pixels for the right pairing, 16,464 for the swapped one |
| glxgears | none of its own (both eyes use one colour); the source says the left eye's scene is moved by `+0.5*eyesep` with an asymmetric frustum; the measured shift is reported and the identity rests on a calibration client | see Not proven in the lane report |
| calibration client | `scripts/quad-buffer-sweep/qbtest.c` (a red square in `GL_BACK_LEFT` at x=-0.2, a blue one in `GL_BACK_RIGHT` at x=+0.2): shift +128 px in a 640 px window, as predicted from 0.4 * 640 / 2 | proves the rig and Mesa's mapping before any program is trusted |

`osgviewer`'s home position normalises the model, so the model's size changes nothing: do not predict its shift from world units, use the per-eye renderings.
Block matching along rows gives a median over textured blocks; report the minimum and the maximum too (the edges of a flat shape match anywhere, so -200 px outliers appear).

## The programs

| Program (Debian testing) | Switch | Stereo types it offers | Route | Result on the published stack |
|---|---|---|---|---|
| Mesa demos 9.0 `glxgears` | `-stereo` | quad buffer only | GLX on Xwayland | pair, declared, both GPUs |
| OpenSceneGraph 3.6.5 `osgviewer` | `--stereo QUAD_BUFFER` or `OSG_STEREO_MODE` | anaglyphic, quad buffer, split, left or right eye, interlaced, checkerboard | GLX on Xwayland (no Wayland backend in 3.6.5) | pair on both GPUs; Debian's unpatched +b2 gives a bit-identical capture to our +stereo3d4 |
| Blender 5.0.1 (our +stereo3d3) | Output properties, Stereoscopy (`render.use_multiview`); the window's display mode is Time Sequential by default and the only one our build has | Time Sequential only in our build | native Wayland (EGL, `EGL_EXT_multiview_window`) and GLX on Xwayland | pair on both routes and both GPUs |
| ParaView 6.1.1 | `--stereo --stereo-type="Crystal Eyes"` (Render View's Stereo Type) | Crystal Eyes (quad buffer), Red-Blue, Interlaced, Dresden, Anaglyph, Checkerboard, SplitViewportHorizontal | native Wayland (a stereo `QWindow` in a window container, Mesa's EGL declares the subsurface) as the session starts it; GLX child window on Xwayland with `QT_QPA_PLATFORM=xcb` | 18 November: NVIDIA 2 pairs in 4 runs, AMD 0 in 6 on xcb (the child's pair taken back). Re-tested on r1118a (KWin +stereo3d59, Mesa +stereo3d26), 21 November: a pair in every run, Wayland AMD 6 of 6 and NVIDIA 4 of 4, xcb AMD 6 of 6 and NVIDIA 4 of 4; see [the re-test](#paraview-re-tested-on-the-published-tree-21-november-2026) |
| FreeCAD 1.1.3 | View, Stereo, Stereo Quad Buffer (`setStereoType("QuadBuffer")`) | off, red/cyan, quad buffer, interleaved rows, interleaved columns | Qt 6 `QOpenGLWidget` | flat: the program never asks for a stereo surface |
| Jmol 16.3, RasMol 2.7.6, Gwyddion 3.12, MeshLab 2025.07 | none is a quad-buffer switch | Jmol `stereo` and RasMol `stereo` draw their own pictures; Gwyddion and MeshLab: no stereo string in the installed libraries, none on Gwyddion's OpenGL page | Java 2D, GTK, Qt | not in this sweep |

## Traps

- **Symptom:** FreeCAD's Quad Buffer entry changes nothing and Mesa prints `GL_INVALID_OPERATION in glDrawBuffer(invalid buffer GL_BACK_LEFT)` under `MESA_DEBUG=1`. **Cause:** Quarter's viewport is a `QOpenGLWidget` (`CustomGLWidget` in `Quarter/QuarterWidget.cpp`), `View3DInventor` fills its `QSurfaceFormat` with samples only, never `setStereo(true)`, and Coin's `QUAD_BUFFER` mode draws to the two back buffers of a mono context. **Found by:** `MESA_DEBUG=1`, then reading the 1.1.3 sources. Upstream removed the feature on 2026-06-09 (FreeCAD pull request 30634, "Remove stereo views", also closing issues 27816, 21496 and 30633).
- **Symptom:** ParaView's `--stereo` window is flat and the program's log shows `paraview is shown flat: the desktop's X server could not show the two pictures of its 3D window together`. **Cause:** a declared child window's first presents complete as copies, Mesa takes the pair back (rule of ORDER 561b); it is the case of [x11-declared-child-limits-and-first-pair.md](x11-declared-child-limits-and-first-pair.md) (ORDER 697 and 698, staged Mesa +26 and KWin +59). **Found by:** five and six repeated runs per GPU, the capture's `stereo` flag and the notice in the log.
- **Symptom:** the same notice is printed by a top-level GLX program (`glxgears -stereo`, the calibration client) on the AMD card while two captures seconds later are a pair. **Cause:** not found; the notice appears to come from the first copied presents and the pair returns. It is a false alarm for the person and belongs to Mesa's `u_stereo_pair` rule.
- **Symptom:** Debian's Blender 5.2.2 aborts (`blender.crash.txt`, no symbols) when its window's display mode is set to Time Sequential, on Wayland and on X11; without stereo it runs. **Cause:** our published Blender is 5.0.1 with the edition's patches and pins above Debian's 5.2.2, so the patches are not on 5.2. **Found by:** `TMPDIR` pointed into the lane folder so the crash file survives the container.
- **Symptom:** the NVIDIA row measures nothing, KWin logs `eglInitialize failed` and Xwayland `GBM Wayland interfaces not available`. **Cause:** the session script exports `__EGL_VENDOR_LIBRARY_FILENAMES` with Mesa's vendor file first, which a virtual KWin on the NVIDIA render node cannot use; a real session's KWin runs on the DRM backend. **Fix in the rig:** keep the variable away from KWin and Xwayland and export it again for the program only (GLX programs use `__GLX_VENDOR_LIBRARY_NAME=mesa`). **Found by:** `kwin.log`.
- **Symptom:** `QT_QPA_PLATFORM=xcb` set by the caller has no effect. **Cause:** the rig script exported it empty. **Symptom 2:** Qt's Wayland plugin reports `No shell integration named "xdg-shell" found`: `qt6-wayland` is not in the image, so Qt programs ran on Xwayland only.
- **Symptom:** a click or key from `xdotool` does nothing. **Cause:** KWin's Xwayland input prompt; set `XwaylandEisNoPrompt=true` in the rig's `kwinrc`. A native Wayland client (Blender) never receives XTEST events: set what it needs in its preference file (`show_splash` false through `blender -b --python-expr ... save_userpref()`).
- **Symptom:** Debian's ParaView has no `paraview` Python module, so `--script` fails (`ModuleNotFoundError`). **Fix:** open a legacy VTK file (`two.vtk`, two squares at different depths) and press Apply with a key and a click.
- **Symptom:** a case measures the one before it. **Cause:** a shared `HOME` keeps KWin's `kwinoutputconfig.json` and the programs' settings. **Fix:** a fresh `HOME` per case.

## ParaView, re-tested on the published tree (21 November 2026)

Debian's ParaView 6.1.1+dfsg1-3, unchanged, on the published tree r1118a (Stereo KWin +stereo3d59, Mesa +stereo3d26, Xwayland +stereo3d3), a 1920x1080 virtual output, one fresh session per run.
Fixture: a legacy VTK file of two squares, the far one 2x2 at z = 0 coloured by scalar 0 (blue), the near one 0.8x0.8 at z = 1 (red), opened with `--data` and Auto Apply, the window maximized by a KWin script.

**How ParaView makes its pair (read in Debian's sources):** `--stereo-type` sets the Render View's `StereoType` (Remoting/Views/vtkSMRenderViewProxy.cxx, the client's type taken as given); the view is VTK's `QVTKOpenGLStereoWidget`; VTK 9.6 shears each eye's projection by plus or minus half its `EyeAngle` (2 degrees, ParaView sets none of its own) about the camera's focal distance (vtkCamera.cxx, `vtkPerspectiveTransform::Stereo`), in eye space before the frustum: two parallel off-axis cameras `D tan(1 deg)` to each side, zero parallax at the focal point. The closed form is `disparity = 2 f tan(EyeAngle / 2) (1 - D / depth)` pixels, `f` the focal length in pixels; the rig solves `f` and the near square's depth from the two squares' captured widths (sizes 2 and 0.8, depths one apart) and takes the focal point at the box's centre, as VTK's ResetCamera does.

| Route, card | Runs with a pair | Near square, measured / predicted | Far square | Vertical | Declaration |
|---|---|---|---|---|---|
| Wayland (the session's default), AMD | 6 of 6 | -5 / -5.04 px | +4 / +4.24 px | 0 | one `set_content` on Mesa's subsurface |
| Wayland, RTX 3060 (zink) | 4 of 4 | -5 / -5.04 | +4 / +4.24 | 0 | the same |
| xcb (GLX child on Xwayland), AMD | 6 of 6 | -5 / -5.26 | +4 / +4.42 | 0 | the child: content 3, version 4, listed by its top-level, limits 10 and 4 |
| xcb, RTX 3060 (zink) | 4 of 4 | -5 / -5.26 | +4 / +4.42 | 0 | the same |
| Red-Blue, Interlaced, Anaglyph, Checkerboard, Dresden, SplitViewportHorizontal | one flat picture each, nothing declared | | | | ParaView's own output formats, drawn into one picture |
| no `--stereo` (the 2D control) | flat, nothing declared | | | | |

Every pixel that differs between the eyes lies in the render view.
ParaView's pair keeps ParaView's own separation (Daniel, 2026-11-18: a program that draws its own pair keeps it); at these sizes the near square stands 5 px in front, past a popped limit of 4.

Traps:
- **Symptom:** ParaView opens a window over the view, "Output Messages", full of `Generic Warning: ... vtkOpenGLState.cxx ... Error in cache state for GL_DRAW_BUFFER got 1027 expected1029`, 16 to 25 per start, in Crystal Eyes only, on both cards and both routes. **Cause:** VTK's state cache for the draw buffer and the buffer GL reports disagree around the eyes' blit (QVTKOpenGLWindow.cxx blits the right eye into `GL_BACK_RIGHT`); ParaView issue 19038 (Mathieu Westphal, 2019, open) records the same warnings on another vendor's Windows driver, so it is VTK's, not the edition's stack. **Found by:** counting the line in ParaView's log per run and searching VTK's and ParaView's trackers for the message. The pair is right with the warnings; the window is the fault a person meets.
- **Symptom:** the welcome dialog covers the view although `ParaView-UserSettings.json` says `ShowWelcomeDialog: 0`. **Cause:** ParaViewMainWindow.cxx reads it from Qt's settings file. **Fix:** `~/.config/ParaView/ParaView.ini`, `[General]` `GeneralSettings.ShowWelcomeDialog=0`.
- **Symptom:** ParaView starts on native Wayland in the rig and logs "ParaView is not fully tested on Wayland". **Cause:** Qt picks Wayland when `WAYLAND_DISPLAY` is set, as in a person's Plasma session. Measure that route first: it is the one people get; `QT_QPA_PLATFORM=xcb` gives the GLX child route.
- ParaView merge request 7994 (Scott Wittenburg, open) restores a missing negation in the client's stereo type; 6.1.1 does not have the code it fixes (it sets the client's type directly), so it changes nothing here.
