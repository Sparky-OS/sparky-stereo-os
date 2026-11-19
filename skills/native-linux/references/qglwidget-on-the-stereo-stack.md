# A Qt 5 program with a QGLWidget: why its 3D view stays empty, and what it needs

Written for ORDER 28 (Fraqtive, 19 November 2026).
Debian's Fraqtive 0.4.8.1-1 (Qt 5.15.19, a fixed-function OpenGL mesh in a `QGLWidget`) showed an empty 3D view on the edition.
The cause was the program's, present on stock Debian and on Debian 12 as well; no package of the edition was involved.

## The four-cell recipe

One throwaway image per stack, both from `debian:testing` (amd64 digest, `--pull=never`):

- **Stock:** Debian's `fraqtive kwin-wayland xwayland mesa` and `qtwayland5`, nothing else added.
- **Edition:** the same, then the published tree as a `file:///` apt source (`Signed-By` its `.asc`, `Suites: mashtabba`) with the pin `Package: *`, `Pin: release o=Sparky Stereo OS`, `Pin-Priority: 1001`, and `apt-get --allow-downgrades dist-upgrade` (the tree's Qt 6 is older than Debian's, so apt downgrades Qt 6 without the flag). Our Mesa, Stereo KWin and Xwayland come in; the edition ships no Qt 5 of its own.
- Each stack on **Wayland** (`QT_QPA_PLATFORM=wayland`) and on **X11 through Xwayland** (`QT_QPA_PLATFORM=xcb`, `DISPLAY=:0`).

Per cell, one fresh session as the stereo-proof-rig skill says (`dbus-run-session`, `kwin_wayland --virtual --xwayland --socket=sub --width 1280 --height 800`, a render node: `--device /dev/dri/renderD128 --group-add 125` or CDI for the NVIDIA card, `--cap-add SYS_NICE`, a passwd entry for the user, `/tmp/.X11-unix` made by hand under a tmpfs `/tmp`):

1. start Fraqtive and wait 8 s; the first run opens the About dialog, answer it with Return through `fakeinput k:28`;
2. capture the 2D view (`capture.py`), send F3 (`fakeinput k:61`, "3D View"), wait 8 s, capture again;
3. measure the view's rectangle in the capture: the number of distinct colours and the share of pixels that are not black (`proof/measure.py` in `sparky-os/upstream/fraqtive`); a view that drew nothing is one grey (Wayland, 1 colour) or 99.9 % black (X11).

A red counts only after a green in the same rig: the same cells with the fix are the green (4,700 to 4,900 colours, 65 to 74 % non-black in the first run), and a plain Xvfb with llvmpipe (`LIBGL_ALWAYS_SOFTWARE=1`, windows clicked with `xdotool` because no window manager gives focus) is a second, independent rig for the same program.

| Cell | Debian 0.4.8.1-1+b1 | 0.4.8.1-1+stereo3d1 (installed from its .deb) |
|---|---|---|
| Stock, Wayland | empty (1 colour) | 4,923 colours, 74 % |
| Stock, X11 | black (2 colours) | 4,723 colours, 66 % |
| Edition, Wayland | empty | 3,446 colours, 65 % |
| Edition, X11 | black | 4,723 colours, 66 % |

## Symptom, cause, how it was found

- **Symptom 1 (X11, every stack, also Debian 12 and a plain Xvfb):** the 3D View button is checked, the area is black, the program logs nothing and `glGetError` is 0. **Cause:** `MeshView::initializeVertices()` calls `glVertexPointer`, `glTexCoordPointer` and `glEnableClientState` from `initialUpdate()`, a callback of the fractal generator, where no OpenGL context is current (a `QGLWidget`'s context is current only inside `initializeGL()` and `paintGL()`). The calls are dropped, the client arrays stay disabled, `glDrawElements` draws nothing. **Found by:** a `fprintf` of `QGLContext::currentContext()` in `initialUpdate()` (null) beside one in `paintGL()` (the widget's context) and of `glGetError()` after the draw (0); one `makeCurrent()` there turned the black area into the mesh. **Fix:** set the arrays in `paintGL()`.
- **Symptom 2 (native Wayland, every stack):** the area keeps the window's grey (`efefef`), nothing is logged (Qt logs "Using Wayland-EGL" and no error), not even with symptom 1 fixed. **Cause:** `QGLWidget` draws nothing under Qt's Wayland platform plugin; `QOpenGLWidget` (Qt 5.4 and later) renders into a framebuffer object and does. A KDE merge request that moved Gwenview's OpenGL renderer from `QGLWidget` to `QOpenGLWidget` names the same cure ("Fixes the OpenGL Renderer not working on Wayland"; read through a search summary, the merge request itself was not opened). **Found by:** the Wayland cell staying grey after the fix that turned the X11 cell green, then the port. **Fix:** port the view to `QOpenGLWidget` (`update()`, `grabFramebuffer()`, `glClearColor()`, `QImage::convertToFormat(Format_RGBA8888)`, the context's `getProcAddress()`); the 3D View action is enabled when `QOpenGLContext().create()` succeeds, which is what `QGLFormat::hasOpenGL()` asked.
- **Trap in the rig:** a first F3 sent while the About dialog is up goes to the dialog. A capture before the Return shows the dialog, and `xdotool` on Xwayland reaches only X11 clients: use KWin's fake input for both routes.
- **Trap in the rig:** `dpkg-source -x` followed by `rm -rf .pc` and added patches builds the old source without a word (the patches are taken as applied). Keep `.pc`, add the patches to `debian/patches/series`, and check the binary for the new symbols (`strings | grep QOpenGLWidget`) before installing it.
- **Trap in the rig:** under a tmpfs `/tmp`, Xwayland needs `/tmp/.X11-unix` (mode 1777) or it logs "Failed to establish X11 socket" and the X11 cell cannot start.
- **Perk:** Debian's package is built with `-debug`, so the About dialog says "Built in debug mode"; the build is not optimised, which does not change these results.

## What a Qt 5 OpenGL program needs to show its 3D view on the edition

1. A context that is current whenever it calls GL: state set outside `initializeGL()`, `resizeGL()` and `paintGL()` needs `makeCurrent()` first, and is safest set where the context is known to be current.
2. `QOpenGLWidget` (or a `QOpenGLWindow`) instead of `QGLWidget` for any window that may run on native Wayland. The old classes run on X11 through Xwayland, which is also the only place a quad buffer (a `QGLFormat::setStereo(true)` visual, drawn into `GL_BACK_LEFT` and `GL_BACK_RIGHT`) can be asked for in Qt 5.
3. For stereo inside a Qt 5 widget window there is no per-eye `paintGL()`: Qt's `QOpenGLWidget::TargetBuffer` and `QSurfaceFormat::StereoBuffers` are since Qt 6.5 (Qt documentation, QOpenGLWidget). A Qt 5 program draws each eye itself (two cameras, [stereo-two-cameras](../../stereo-two-cameras/SKILL.md)) into one buffer twice as wide and declares the area as full side by side ([stereo-window-3d-area](../../stereo-window-3d-area/SKILL.md)), or moves to Qt 6.

The patches, the proof and the candidate's recipe are in the build tree under `sparky-os/upstream/fraqtive`.
