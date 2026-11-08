# GTK 4: a GtkGLArea as a declared 3D area inside an ordinary window

Written on 2026-11-07 (ORDER 137, milestone 1: GTK 4.24.1 on Wayland).
The general rules are in [SKILL.md](../SKILL.md); this page is what GTK needs on top of them.

## The route

GtkGLArea draws into a framebuffer of its own and hands GTK one texture, which GTK appends to the scene graph as a texture node.
The window's own surface carries everything else, so the area is the one place that needs a surface of its own, as the pattern says.
GTK already has the machinery: `GtkGraphicsOffload` puts a subtree on a `GdkSubsurface` (a `wl_subsurface` with a `wp_viewport`) when the subtree is one texture and nothing blocks it, and draws it normally otherwise.
So a stereo GtkGLArea is a GtkGLArea that

1. renders each view into a framebuffer of the area's size, the program's render handler unchanged (it asks `gtk_gl_area_get_current_eye()` which camera to use), and copies each view with `glBlitFramebuffer` into its half of one opaque texture twice as wide as the area (left half first);
2. appends that texture inside a subsurface node, in a clip of the area's size, with the node's rectangle twice the area's width, and declares the `GdkSubsurface` with `kde_stereo_content_v1.set_content(3)` (the protocol's version 2: a declared surface is one view wide, and `wp_viewport` destination is one view, so the area keeps its size on the screen and the source is the whole texture);
3. tells the program when it cannot do this (`stereo-shown`, `stereo-error`, one log message) and then renders the left view alone.

## The X11 route (GDK 4 on Xwayland, milestone 2)

GDK 4 has no subsurface on X11, so the area is a child X window, the pattern of [Declaring an X11 child window](../../native-linux/references/x11-video-child.md):

1. a frame window the size of one view, a child of the toplevel's X window at the area's place (`gtk_widget_compute_bounds()` into the native plus `gtk_native_get_surface_transform()`, times the scale factor), and inside it a window twice as wide that holds the two views side by side; no events selected on either, so the pointer and the keys go to the toplevel;
2. the inner window is declared with `stereo_declare_x11_child(display, toplevel, inner, STEREO_SBS_FULL, class, subclass, view_width, view_height)`, the shown size being the frame's; GDK loads `libstereo-declare.so.1` with `g_module_open` when the first stereo area asks (loaded when needed; `libgtk-4-1` depends on `libstereo-declare1 (>= 1.7.0)`, because X11 stereo areas are a designed feature) and needs `_KDE_NET_WM_STEREO_CONTENT_SUPPORTED` 8 or more;
3. the views are read back from the stereo texture (`glReadPixels`, rows turned over, red and blue swapped) and put into the inner window with `XPutImage`: one copy through the CPU, each view at the resolution it was drawn at. The readback route stays for now (it works and is measured); a GL route (an EGL surface on the inner window) is the next step and the speed-up, the picture is the same.
4. an area that cannot do it says so as on Wayland (`stereo-error`: no library, a window manager below version 8, no stereo window manager) and draws its left view alone.

Measured on Stereo KWin +46's Xwayland (client on llvmpipe): 9 of 9 checks (every sample of each eye), resize, another size, off and on, hide and show, two areas in one window; the child is listed in the toplevel's `_KDE_NET_WM_STEREO_CONTENT_CHILDREN`, declared 3, with the one view size 480x270.

What GDK needs from KWin and Mesa (both are lane 160's, nothing was changed here):
- KWin: an acknowledgement that the declared child is redirected (a property or an event) so the first frames need not be repeated (see the trap); the child cut to its window and under its siblings (the clipping draft); and the child's place with "below the parent's own surface" (`stereo_declare_x11_child_place()`, support 7) together with a transparent hole in the toplevel, so that a 2D widget drawn over the area shows over it as on Wayland. Without it a `GtkOverlay` label over an X11 stereo area is hidden (0 samples of it in either eye, measured).
- Mesa: nothing; the GLX and EGL child listing is not used (GDK lists the child itself with the library).

## Recipe

- Check the source first: `GtkGLArea` renders in `gtk_gl_area_snapshot` (gtk/gtkglarea.c); `GskOffload` (gsk/gskoffload.c, `find_texture_to_attach`) decides what can be attached; `gdk_wayland_subsurface_attach` (gdk/wayland/gdksubsurface-wayland.c) does the Wayland side; `GDK_DEBUG=offload` prints each refusal with its reason.
- Add the protocol XML as a private protocol of GDK (`gdk/wayland/protocol/kde-stereo-content-v1.xml`, meson `'stability': 'private'`), bind `kde_stereo_content_manager_v1` from version 2, and declare in a new `GdkSubsurface` vfunc `set_stereo`.
- In GSK's offload, for a stereo subsurface take the whole texture as the source rectangle (a clip would otherwise crop it to the area's half).
- The rig: a headless Stereo KWin (the shared image), the program under test run in the same container against the GTK build's library directory (`LD_LIBRARY_PATH`), `GDK_DEBUG=offload` and `WAYLAND_DEBUG=1` on the client, ScreenShot2 for the capture. A stereo window's capture is twice the output's width (2560 for a 1280 output): that alone tells that KWin took the declaration.
- The test program draws with scissored clears only (a red or blue field, the tag LEFT or RIGHT in 5x7 glyphs, a frame number, a white square and a one pixel white frame), looks the stereo API up with `dlsym` and `g_object_class_find_property`, so one binary is the test on the patched GTK and the control on Debian's. A checker redraws the expected picture in Python and compares every sample of each eye.
- The cases, each in a fresh KWin session: stereo; the swapped-eye program (must fail the LEFT/RIGHT check); a resize while shown; stereo switched off and on; hidden and shown; the failure cases (a widget opacity below 1; the protocol removed with `GDK_WAYLAND_DISABLE=kde_stereo_content_manager_v1`; a context that cannot export a dma-buf); the control (stereo off against Debian's GTK).

## The scripts

- `scripts/glarea-stereo-test.c`: the test program. `cc glarea-stereo-test.c $(pkg-config --cflags --libs gtk4 epoxy) -ldl`, then run it with `--stereo` (and `--swap`, `--opacity 0.99`, `--grow-after 3`, `--toggle-after 4`, `--hide-after 3`, `--overlay`, `--offload`, `--frame N`, `--size WxH`, `--report FILE`, `--quit-after SECS`). It writes the property values, the renderer string and the eyes its render handler saw to the report file. The same binary runs on a GTK without the API (it looks the property and the getter up at run time): that is the control.
- `scripts/dmabuf-export-probe.c`: exports a GL texture as GTK does and says whether each plane's descriptor is open (`cc dmabuf-export-probe.c -lEGL -lGLESv2`); run it with `__EGL_VENDOR_LIBRARY_FILENAMES` naming Mesa's vendor file first and NVIDIA's second, `MESA_LOADER_DRIVER_OVERRIDE=zink` and `VK_DRIVER_FILES` for NVIDIA's Vulkan driver.
- `scripts/check_eyes.py CAPTURE.png [--size WxH] [--expect stereo|left|mono] [--overlay] [--tol N] [--swap]`: redraws the expected pictures and checks the capture: both eyes in one capture (twice the output's width), red LEFT in the left half and blue RIGHT in the right half with no red in the right and no blue in the left, the area at its own size and place in both halves, each eye's every sample equal to what the program drew, and everything outside the area identical in both eyes. `--expect left` and `--expect mono` check a 2D capture (the area that could not be shown per eye, an area without stereo). It exits 1 when a check fails, so the negative controls are runs that must exit 1.

## Traps

- **Both eyes shown squeezed in the area's place when GTK does not offload.** Symptom: the area shows two small pictures side by side. Cause: GSK draws the subsurface node's child when it cannot attach it, and the child was the double-width texture scaled to the area. Fix: the child is a clip of the area's size over a texture node twice as wide, so the fallback is the left view at its own size, and GSK's offload takes the whole texture for a stereo subsurface instead of the clip's part. Found by reading `gsk_gpu_node_processor_add_subsurface_node` and `find_texture_to_attach`.
- **No dma-buf, no subsurface.** Symptom: `🗙 Texture type not supported or export failed` in `GDK_DEBUG=offload`. Cause: GTK attaches only dma-buf textures, and llvmpipe cannot export one. Fix: none in GTK; prove the offload on a GPU (the RTX 3060 through CDI), and let the CPU-only run prove the honest failure. The area says it.
- **zink on NVIDIA ends the connection (Debian's GTK too).** Symptom: `Error 9 (Bad file descriptor) dispatching to Wayland display` right after `zwp_linux_dmabuf_v1.create_params`, in 4 of 6 runs of the stereo area and in 2 of 2 runs of a plain `GtkGraphicsOffload` around a `GtkGLArea` on Debian's gtk4 4.24.1. Cause: with Mesa's zink on NVIDIA's proprietary Vulkan driver `eglExportDMABUFImageMESA` returns success and writes no file descriptor (the modifier is `DRM_FORMAT_MOD_INVALID`), and GTK's `fds[]` was uninitialised, so it sent random integers. Fix in GTK: the descriptors start at -1 and every plane's must be open, otherwise the export has failed and GTK draws the texture itself (6 of 6 runs then end in the honest failure). Mesa's side is fixed in the edition's Mesa 26.1.6-1+stereo3d18 (0030: zink exports with a modifier NVIDIA's driver can render with; 0031: a failed export returns EGL_BAD_MATCH): with it the stereo area shows on zink over the RTX 3060 (dma-buf XB24:0x300000000606014, 9 of 9 checks), and the GTK fix stays for any driver that exports no open descriptor. Found by `GDK_DEBUG=dmabuf` (the crashing runs printed `Exported GL texture to dmabuf`), then `scripts/dmabuf-export-probe.c`, which presets the descriptors to -1 and showed -1 kept. NVIDIA's own EGL exports a valid dma-buf and works.
- **A blit ignores the colour mask and obeys the scissor.** ES 3.2 section 16.2.1: only the pixel ownership test, the scissor test and sRGB conversion affect a blit. A program that leaves `GL_SCISSOR_TEST` on (the test program does) would clip the copy: disable it around the blit.
- **Alpha.** The picture handed over is opaque (`GL_RGB8`, `B8G8R8X8`): GTK refuses a non-opaque texture on a subsurface below the window, and a stereo picture has nothing to blend with.
- **The decision comes a frame late.** GSK decides offloading while it renders, after the snapshot. The area checks `gdk_subsurface_get_texture()` after the frame clock's `after-paint` and switches to the left view alone when the subsurface has no texture; the clip makes that frame correct too.
- **A passwd entry for uid 1000.** GTK's tests start `dbus-daemon`, which fails with `Could not get password database information for UID` in a container without one (the rig mounts a passwd file).
- **Build dependencies against the edition's pins.** `apt-get build-dep gtk4` in an image with the edition's repository at pin 1001 stops on librsvg (it wants libdav1d 1:1.5.4) and on the media libraries. Lower the edition pin to 100 and pin the Mesa and Wayland packages back to the edition at 1001.
- **An image committed from a container started with `--entrypoint sh` keeps that entrypoint**: `docker run IMAGE sh script` then fails with `sh: 0: cannot open sh`. Start with `--entrypoint sh IMAGE script`.
- **The right eye is black on X11 (the left is right).** Symptom: the first captures of the X11 area show the left picture and a black right half. Cause: the inner window is twice as wide as its frame, X clips drawing to the frame until the window manager redirects the declared child, and what was drawn before is lost (a later `XPutImage` is not clipped: a resize fixed it). Fix: the first ten frames are drawn again, 100 ms apart. Found by growing the area after three seconds: the capture then had both eyes.
- **A 2D widget over an X11 stereo area is hidden.** Cause: the child window is above the toplevel's own pixels. Fix: not in GDK (see what GDK needs from KWin). Measured with `glarea-stereo-test --overlay`.
- **A capture that never returns.** Symptom: a proof case stays at its capture step for minutes after KWin's ScreenShot2 call timed out (a software-rendered KWin on a loaded machine). Cause: `capture.py`'s reader thread was not a daemon thread and waited for the pipe's end for ever after the exception. Fix: `daemon=True` on the thread (done in `stereo-proof-rig/scripts/capture.py`); rerun the case when the machine is idle. Found with `ps --forest`: the case script's only child was the `docker exec` of the capture.
- **Reproducing the program's picture in the checker.** GL's y goes up and the capture's goes down: the first checker put the white square one row off (134 samples per eye). Redraw the expected picture with the same flip, and compare every sample.

## Limits (milestone 2)

| Case | Result |
|---|---|
| two stereo areas in one window | works on Wayland (two subsurfaces) and X11 (two child windows): each band red in the left eye and blue in the right, same places in both eyes, nothing in the wrong eye |
| an area under a rounded clip, an opacity below 1, partly scrolled out | GSK cannot offload it: the honest failure for good until `stereo` is set again; kept as is, it is the safe answer |
| a `GtkWidgetPaintable` or other snapshot of the area | the frame check can read another window's state; not lifted (rare) |
| fractional output scale (1.5) | the area is drawn at the integer scale (2) and Stereo KWin resamples: works, not sample-exact |
| a popover or menu over the area | a separate surface: works |
| a `GtkOverlay` child over the area | Wayland: works (the area lies below the window with a hole); X11: hidden |
| the GTK demo (`gtk4-demo --run glarea`, `GTK_DEMO_GLAREA_STEREO=1` or the check button) | shown in 3D on NVIDIA's EGL and on Mesa +stereo3d18's zink over the RTX 3060: the triangle's two views 22 samples apart, the rest of the window identical in both eyes |
