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

## Packaging a Qt 5 program of Debian's as an edition package (ORDER 743)

The edition ships no Qt 5 of its own, so a Qt 5 program is rebuilt against Debian's Qt 5 and the route needs nothing of ours for the toolkit; only Mesa, KWin and Xwayland change on the edition. The route for `fraqtive 0.4.8.1-1+stereo3d1+lc1` (recipe in the build tree, `sparky-os/upstream/fraqtive/packaging`):

1. `next-source.sh` (in the Lean Code migration image, apt over https): `apt-get source --download-only fraqtive=0.4.8.1-1` from a `deb-src` line of testing, then `sha256sum -c` against the three hashes written in the script (the signed index is the first check, the hashes the second); `dpkg-source --skip-patches -x` (no `.pc`: dpkg-source applies the patches itself when it packs); the patches appended to `debian/patches/series`; one changelog entry dated by the recipe (`SOURCE_DATE_RFC2822`, never the clock); `dpkg-source --before-build` then `--after-build` proves the series applies and unapplies; `reproducible.py normalize-tree`; `dpkg-source -b`. Then the same source is unpacked, `python3 -m lean.debian_prepare t VERSION+lc1 --toolkit /toolkit`, normalised and packed again: the `+lc1` source.
2. `build.sh` calls `packages/depth-source/build.sh PKG WORK SRC PREV REPO ARCHIVE "" SIBLINGS` (it is generic: it only needs a `+lc1` `.dsc` and its orig tarball in `SRC`). `PREV` is an empty folder for a first build. `ARCHIVE` is a folder with `sources.json` and `keyrings/`; the keyring path in `sources.json` is the path inside the container (`/archive/keyrings/debian-archive-keyring.gpg`). `REPO` is the published tree by its real path (the Docker daemon cannot stat the `sparky-repo-current` link). Export `SPARKY_BUILD_IMAGE` with the name of the image you hold, or the build record names `sparky-lc-migration:20261020`.
3. What comes out: the `.deb`, the dbgsym, the `.dsc`, the Debian tarball, the buildinfo, the changes and `*.sparky-build.json` (the build record, `unrecorded: []`). `lean.release check-debs` said `verified 2 packages` and the archive-qualified link gate `passed`.
4. **No `-lc-hr` companion when no payload file was projected.** A compiled program's payload (the binary, a `.desktop`, a man page, icons) has nothing Lean Code removes: `Payload Lean Code: fraqtive: 0/12 files projected`, and the check requires no companion. Published `bino` has none either. Do not add one by hand.
5. **The comparison with Debian's package** is `dpkg-deb -c` plus `md5sum` of both trees: here the binary (the fix), `changelog.Debian.gz` (ours; Debian's `changelog.Debian.amd64.gz` is the binNMU note of `+b1` and is not in a `+stereo3d1` build), `copyright` (the credit paragraph), the Lean Code record under `usr/share/dpkg-stereo`, and one `Depends` line: `libqt5opengl5t64` is gone because the patched program no longer links Qt's OpenGL module, and `libstdc++6 (>= 12)` against `(>= 5)` from today's toolchain.
6. **Ours over Debian's:** the `+stereo3d1` suffix sorts above `+b1` (`s` after `b`), and the pin `Package: * / Pin: release o=Sparky Stereo OS / 1001` decides first anyway: `apt-get -s install fraqtive` printed `Inst fraqtive (0.4.8.1-1+b1 Debian:testing ...)` without the stage and `Inst fraqtive (0.4.8.1-1+stereo3d1+lc1 Sparky Stereo OS:testing ...)` with it. The flat index of a stage needs `Origin: Sparky Stereo OS` in its Release (`apt-ftparchive -o APT::FTPArchive::Release::Origin=...`, and `apt-utils` installed) or the pin never applies. The block of Debian's build at -1 comes with the round's regenerated `sparky-stereo-apt`.
7. **Lintian against Debian's own source** (`lintian -I --pedantic` on both `.dsc` files): ours adds the edition-wide `unknown-field Original-Maintainer`, `unknown-field Sparky-Lean-Code`, `bugs-field-does-not-refer-to-debian-infrastructure` (the same three on published kubrick), `build-depends-on-build-essential-package-without-using-version gcc` (the toolkit's build dependency), `no-nmu-in-changelog` and `source-nmu-has-incorrect-version-number` (the `+stereo3dN` suffix), and `non-debug-file-in-debug-package` for the Lean Code record inside the dbgsym.

### Traps of the route (symptom, cause, how found, fix)

- **`next-source.sh: unexpected EOF while looking for matching '`** with a plain `bash -n` clean-looking script. Cause: an apostrophe inside `: "${VAR:?the recipe's date}"`; the word of `${VAR:?...}` inside double quotes still opens a quote. Found by running `head -N file | bash -n` for growing N until the error appeared. Fix: no apostrophe in the message.
- **A stage's apt index is ignored** (the Debian build is the candidate). Cause: no `Origin` in the flat `Release`. Fix: as step 6.

## Two probes for the 3D view in stereo (ORDER 743, rig `fq743-rig`)

One declared full side-by-side area inside the window, two parallel cameras, the offset the largest for which every visible vertex stays inside the person's limits: `e = min(sunk_px / d_far, popped_px / -d_near)` with `d(Z) = k (1/C - 1/Z)` per unit offset (`k` the focal length in pixels of one view, `C` the zero-parallax distance, here the camera distance 40), the limits in pixels of a view 1920 wide scaled to the area's width (`limit * width / 1920`; whether an area narrower than the screen should scale by the screen's width has no recorded design: stated, not decided). Camera `i` (-1 left, +1 right) is moved by `i e / 2` and its frustum is shifted by `-i (e/2) near / C`.

| Route | What was built | Result in the rig (virtual output 1280x800, AMD render node) |
|---|---|---|
| Qt 6 port, Wayland | `QOpenGLWidget` with `QSurfaceFormat::StereoBuffers`, `paintGL()` once per eye (`currentTargetBuffer()`), the edition's qt6-base gives the widget a native window that Mesa declares (`kde_stereo_content_v1.set_content(3)` on its own subsurface) | pair 2560x800; area differs between the eyes in 26.6 % of its pixels, the toolbar part in 0 %; disparity measured -1.92 to +2.01 px against -2.02 and +1.38 predicted, vertical shift 0 |
| Qt 5 as it is, X11 | `QGLWidget` with `QGLFormat::setStereo(true)`, `GL_BACK_LEFT` and `GL_BACK_RIGHT`, Mesa's GLX packs and declares | a pair in 2 of 7 cells (see the trap), then -1.57 to +1.46 px against -2.03 and +1.39 predicted, 2D part 0 differing pixels, limits from a probe-only stand-in |
| Qt 5 as it is, Wayland | a standalone probe: own `wl_subsurface` and `wp_viewport` on a second event queue, a `wl_egl_window` twice as wide, `libstereo-declare`, three squares at depths 28, 40 and 70 | pair 2560x800; near square -1 px, screen square 0, far square +1 px against -1.000, 0 and +1.000 predicted; vertical 0; the 2D part 0 differing pixels |
| Qt 6 port, X11 | the same widget under `QT_QPA_PLATFORM=xcb` | black area, no declaration, 1280 wide; the same widget without the stereo option draws (71.9 % non-black); `glxgears -stereo` in the same session gives a pair |

Lines: the Qt 6 port is 17 files, 46 added and 42 removed (qmake 6 and `configure` accepting it, `setMargin`, `qSort`, `QTime`, `QDesktopWidget`, `qRegisterMetaTypeStreamOperators`, the wheel event, `QPalette::Background`, `QStyleOptionFrameV3`, `QFontMetrics::width`); the stereo part is 3 files, 148 added; the Qt 5 X11 stereo part is 3 files, 126 added on top of patch 0001 and needs `QGLWidget` back (it draws nothing on Wayland), so a Qt 5 program with both routes keeps both classes; the Qt 5 Wayland plumbing is about 45 lines in the probe and does not yet hold the hole in the window, the rectangle follow and the fractional scale rule.

### Traps of the probes (symptom, cause, how found, fix)

- **Limits stay `-61` (not delivered) forever on Wayland.** Cause: the depth object was made for the widget's own subsurface; Stereo KWin sends `depth_limits` for a window, not for a bare subsurface. Found by printing the return code of `stereo_depth_wayland_get_limits` at every change and reading `get_depth(... wl_surface#49)` in `WAYLAND_DEBUG=client`. Fix: ask with the top level's surface (`window()->windowHandle()`).
- **The first call returns `-95` (not offered) on Wayland.** Cause: `stereo_declare_wayland_init` is asynchronous; the manager is bound after the first dispatch. Fix: ask again; draw identical eyes and log it until the limits are there.
- **X11: the limits of a declared child never arrive** (`-61`). Cause: the rig's published Stereo KWin (+stereo3d58) announces `_KDE_NET_WM_STEREO_CONTENT_SUPPORTED` 10, and a declared child gets the property from 11 (see x11-declared-child-limits-and-first-pair.md). Consequence for the program: on X11 the eyes stay identical and the window says why (the sentence belongs to milestone 2). The probe measured the camera maths with a stand-in (`FQ743_LIMITS=10,4`, probe only, never shipped).
- **X11: a pair in some cells only.** The static 3D view draws once; the rig's Mesa is +stereo3d24, and the page above says the first pair of a program that draws once needs +stereo3d26. Not proved here as the cause (an animated view was not run), listed as unknown.
- **`qt.qpa.backingstore: Recreating RHI support with a stereo format` and a black area (Qt 6, xcb).** Not explained; no property was set on any X window (`xprop` over the tree), the control without the option draws. Listed as unknown for milestone 2.
- **Private headers:** `QPlatformNativeInterface` (the `wl_display`, `wl_surface`, `display` resources) needs `qt6-base-private-dev` or `qtbase5-private-dev` and `QT += gui-private`; without them the include is missing.
- **A probe's own scene needs the same maths as the program's:** three squares at known depths gave integer disparities, which made the sign check exact (`red -1`, `blue +1` for the right eye minus the left); a textured mesh gave block-matching noise of about 0.5 px at the edges.
