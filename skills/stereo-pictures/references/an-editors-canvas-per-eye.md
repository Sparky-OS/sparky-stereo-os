# An editor's canvas per eye: GIMP 3.2 through GTK 3's stereo area

Written on 2026-11-26 (queue row 137 with row 148, the stereo GIMP's milestone 1).
The stereo area itself is [GTK 4 and GTK 3 and GtkGLArea](../../stereo-window-3d-area/references/gtk-glarea.md); what is left for GIMP (the depth layers, the deep canvas) is in [GTK pieces still to build](../../stereo-window-3d-area/references/gtk-glarea-plans.md).

## What the person sees

- An image with the top-level layers "Left eye" and "Right eye" (how the stereo pictures plug-in opens MPO, JPS and PNS files), or a side-by-side or top-and-bottom picture the person put into one of the plug-in's editing modes, is shown in 3D: each eye sees its own content, at the canvas's own size, and Stereo KWin does the one resize.
- A packed picture shows each eye's view in both halves (the left eye sees the left view in the left half and in the right half), so the canvas keeps the image's size and coordinates and every tool works where it is used: a stroke in either half edits that half, and the plug-in's "Both eyes alike" mode repeats it in the other.
- Guides, the selection, paths, the layer boundary and the tools' frames and handles are drawn over the picture at the screen, the same overlay in both eyes.
- View > Enable 3D (on by default, per window, not remembered) and View > Display Settings (`kcmshell6 kcm_kscreen`) are the program's 3D options; nothing else.
- Where the canvas cannot be shown per eye (a window drawn by the processor on Wayland, a desktop without the stereo declaration) the left eye is shown and the status bar says why, in the person's language; GTK's exact reason is in the log.
- A 2D image, and any image with Enable 3D off, is drawn exactly as Debian's GIMP draws it (the proof compares every sample of the screen).

## The route, and why

GIMP 3.2's canvas is cairo: `gimp_display_shell_draw_image()` renders the image chunk by chunk through GEGL into an 8 bit render cache (`gimp_display_shell_render()`), and the canvas items (`GimpCanvasItem`) are drawn with cairo over it.
GTK 3's stereo area takes OpenGL views.
The chosen route: **each eye is rendered by GIMP's own render code into a render cache of its own, from that eye's sources, and the two pictures go up as textures into one stereo GtkGLArea that lies under the canvas items.**

- The eye's sources: an eye layer's own buffer (a `GeglBuffer` view with `shift-x`/`shift-y` for the layer's offset), or the projection seen through a shifted view for each half of a packed picture, each clipped to its half. `gimp_display_shell_render()` became `gimp_display_shell_render_eye()` with a source list; the screen's picture is the same code with the shell's pickable.
- The area is GimpCanvas's **underlay**: a child outside GimpOverlayBox's overlay list (`forall`, `remove`, `size_allocate`), never drawn by the box, drawn by the shell's draw handler with `gtk_container_propagate_draw()` between the backdrop and the canvas items. The area clears its rectangle (the hole) and the window drops it from its opaque region, so the items GIMP draws afterwards lie over the picture.
- Each eye's picture is the whole canvas: the ancestors' backgrounds (the canvas window has none of its own), the padding, the checkerboard and the image, the same function the 2D canvas uses (`gimp_display_shell_draw_picture()`).
- Only what the canvas redraws is painted again in each eye's picture and uploaded (`glTexSubImage2D` of the exposed rectangles); the whole texture is blitted into the area's framebuffer turned over (cairo's first row is the top, OpenGL's the bottom).
- On X11 the image window gets a 32-bit visual on a compositing screen, so that GTK places the stereo child below the window (`stereo->below`); otherwise the guides and outlines would lie under it.

Why this route rather than a memory route in GTK (`wl_shm` pictures): the stereo area already does the subsurface or the X11 child, the declaration, the hole, the failure and the depth and colour state, and needs no change; GIMP's tools and items stay untouched; the depth road stays open, since the area takes half float and float views and a colour state, and GEGL renders in float (milestone 3). The memory route remains the way for a 16-bit integer picture on drivers that export no 16-bit dma-buf, and for a software renderer on Wayland; it is GTK's work, planned with milestone 3.

## Recipe

1. Read `app/display/gimpdisplayshell-callbacks.c` (`gimp_display_shell_canvas_draw_image()`), `gimpdisplayshell-draw.c`, `gimpdisplayshell-render.c` and `gimpdisplayshell-scroll.c` (the cache is moved on scroll), and `app/widgets/gimpoverlaybox.c` (children are offscreen windows drawn by `gimp_overlay_child_draw()`).
2. The module `app/display/gimpdisplayshell-stereo.c`: the model (eye layers or a packed picture in a mode), the eye caches and pictures, the area, its render handler, the told failure; built only with `gtk_gl_area_set_stereo()` (meson `HAVE_GTK_GL_AREA_STEREO`, OpenGL through epoxy).
3. The menu: `view-stereo` (a toggle) and `view-stereo-display-settings` in `app/actions/view-actions.c`, their callbacks in `view-commands.c`, two items in `menus/image-menu.ui.in.in`; the words are the stereo layer's ("Enable 3D", "Display Settings…") in its nine translations.
4. Build: the edition's recipe `sparky-os/packages/gimp` (Debian's 3.2.8-1, the patches after Debian's series, `release/build-from-lc-dsc.sh` with the staged gtk+3.0 as siblings).

## The proof

One container per row: a headless Stereo KWin (`kwin_wayland --virtual`, Xwayland for X11 rows), GIMP started on an XCF fixture with a fresh profile, actions driven over the bus, ScreenShot2 for both eyes, judged sample by sample.

- **Fixtures,** made by Debian's own `gimp-console` (python-fu-eval): 400 x 300 views, the left red, the right blue, a white square 30 px further right in the right eye, a green square at the same place, guides at x 200 and y 150; the eye-layers image, a selection variant, a packed side-by-side and a top-and-bottom picture with the plug-in's parasites, a 2D image.
- **Controls:** GIMP in 2D on one view of the same file in the same window (`ctl-left`, `ctl-right`). The image's place is the dense block where the two controls differ (rows and columns with at least 100 differing samples: the image tab's and the Layers dock's thumbnails differ too and must stay out). In it each eye must equal its control in every sample; everywhere else the two eyes must be identical.
- **Overlays** (the selection's outline, a tool's frame and translucent handles): one 2D picture drawn over both eyes' own pictures, so where the pictures agree the eyes agree, and elsewhere `L - R = (1 - a)(P_L - P_R)` with one alpha in every channel (0 for an opaque outline).
- **Red rows:** Debian's GIMP on the same file (flat), the capture judged against swapped controls.
- **Actions over the bus:** GIMP 3 is a non-unique GtkApplication (`org.gimp.GIMP`), which owns no name but exports its actions at `/org/gimp/GIMP` on its own connection: find the connection whose PID is GIMP's (`GetConnectionUnixProcessID`) and call `org.gtk.Actions` (`SetState view-stereo false`, `Activate view-zoom-4-1`, `Activate tools-rect-select`).

## Traps

- **The whole canvas black in both eyes, the guides drawn.** Cause: GIMP's welcome dialog covered the canvas in that run; with a fresh profile GIMP shows it whenever `config-version` is missing or older, whatever `show-welcome-dialog` says. Fix: `(config-version "3.2.8")` in the test profile's `gimprc`. Found in a reduced capture of the run.
- **Every `gimprc` value ignored.** Cause: one unknown key (`single-window-mode` is not a `gimprc` key) is a fatal parse error and GIMP uses defaults for the whole file (`Gimp-Config-Message ... fatal parse error` in GIMP's output). Fix: only `gimprc` keys; the window's size goes into `sessionrc` (`(session-info "toplevel" (factory-entry "gimp-single-image-window") (position 0 0) (size W H))`).
- **The padding black in both eyes, the image right.** Cause: the canvas's window has no background; in 2D what shows there is what the widgets around it painted underneath (the theme's 60, 60, 60). Fix: each eye's picture starts with the CSS backgrounds of the canvas's ancestors, top level first, each at its place relative to the canvas (`gtk_render_background()`). Found by dumping each eye's picture to PNG (alpha 0 outside the image).
- **Both eyes one image pixel off after scrolling at 400 %.** Cause: `gimp_display_shell_scroll()` moves the render cache's pixels and translates its valid region instead of rendering again; the eye caches stayed valid with the old content. Fix: the scroll moves each eye's cache the same way (GIMP's own technique). Found by comparing the guides (drawn by the canvas, at the right place) with the squares (one pixel off) in the same capture; a GEGL test showed a shifted buffer view reads exactly like its buffer.
- **The area drawn over the guides.** Cause: a container child is drawn after the shell's draw handler, which already drew the items. Fix: the area is an underlay that GimpOverlayBox's own draw never draws, and the shell draws it before the items. GimpOverlayBox's overlay children are offscreen windows: no place for an OpenGL area.
- **GIMP's meson asks for `INSTALL.in`.** Cause: a tree holding `.git` is taken for a development checkout. Fix: keep the baseline repository beside the tree (`git init --separate-git-dir`, then remove the `.git` file).
- **`gen-languages: setlocale() failed`.** GIMP's build needs a UTF-8 locale; Debian's rules run it under `localehelper LANG=en_US.UTF-8`.
- **(packaging) deb-multimedia's libmypaint wins the build.** Its `libmypaint-dev` has epoch 1 (1:1.6.1), Debian's has none (1.6.0), so a build with both sources links `libmypaint.so.0` where Debian's GIMP links `libmypaint-1.5.so.1` (the only difference in `ldd` over the program and its plug-ins); a bound `libmypaint-dev (<< 1:0)` is refused by apt's solver ("Reached two conflicting assignments"). `release/build-from-lc-dsc.sh` adds deb-multimedia to every build, so the edition's GIMP is built that way and says so in its README.
- **(packaging) `Missing toolkit input: packages/dpkg-stereo/LICENSE`** from `lean.debian_prepare` in a sparse checkout of the build repository: check out `sparky-os/packages/dpkg-stereo` too.
- **(packaging) a native source in the release builder:** `build-from-lc-dsc.sh` dates a source by the changelog in its Debian tarball, which a native source has not ("debian.tar.xz: open failed"). A plug-in whose upstream lives elsewhere is a `3.0 (quilt)` package with a reproducible orig tarball (names sorted, the commit's time, owner 0) from the pinned trees.
- **(catalogues) a patch that rewrites a translation file's header.** Python's text mode turns CRLF into LF (GIMP's `pt_BR.po` header has CRLF lines), so the exported patch removed and re-added 20 lines of translators' names. Fix: read and write with `newline=""`; check that a catalogue patch has no `-` lines.
- **(catalogues) round 1's `.po` files refused by `msgfmt`** ("end-of-line within string" at line 11): the header ended in a stray quote line; its own `.mo` writer worked, so the plug-in ran. The header is now written line by line, and the package compiles the catalogues with `msgfmt -c`.
- **(rig) KWin does not start: `env: 'kwin_wayland': Operation not permitted`.** The binary carries a file capability (CAP_SYS_NICE): the container needs `--cap-add SYS_NICE`. The session bus also needs a passwd entry for the user's uid.
- **(rig) A drag through fake input does nothing.** Each `fakeinput` process is one client, and KWin's fake pointer (with its pressed button) lives only while the client is connected; a press in one process and moves in the next leave no drag. Send the whole drag through one connection (`fakeinput m:X,Y s:300 p:272 m:... r:272`). Pointer motion alone draws no brush outline in a headless session; the Rectangle Select tool's frame after a drag is a tool's outline that does appear.
- **(rig) docker made a missing working folder as root,** and the container's user could not write in it: make `-w` folders on the host first.

## Measured

On NVIDIA's own EGL under Wayland, the development build: eye layers, side by side and top and bottom each equal their controls in every sample of the picture, the eyes identical everywhere else; at 400 % after a scroll the same; the selection's 596 outline samples and the Rectangle Select tool's 1,822 frame and handle samples are one overlay over both eyes; Enable 3D off and the 2D image equal Debian's GIMP in every sample of the screen; Debian's GIMP on the stereo file is flat. The other routes, and the same rows from the installed packages, are in the lane's report.
