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

## Recipe

- Check the source first: `GtkGLArea` renders in `gtk_gl_area_snapshot` (gtk/gtkglarea.c); `GskOffload` (gsk/gskoffload.c, `find_texture_to_attach`) decides what can be attached; `gdk_wayland_subsurface_attach` (gdk/wayland/gdksubsurface-wayland.c) does the Wayland side; `GDK_DEBUG=offload` prints each refusal with its reason.
- Add the protocol XML as a private protocol of GDK (`gdk/wayland/protocol/kde-stereo-content-v1.xml`, meson `'stability': 'private'`), bind `kde_stereo_content_manager_v1` from version 2, and declare in a new `GdkSubsurface` vfunc `set_stereo`.
- In GSK's offload, for a stereo subsurface take the whole texture as the source rectangle (a clip would otherwise crop it to the area's half).
- The rig: a headless Stereo KWin (the shared image), the program under test run in the same container against the GTK build's library directory (`LD_LIBRARY_PATH`), `GDK_DEBUG=offload` and `WAYLAND_DEBUG=1` on the client, ScreenShot2 for the capture. A stereo window's capture is twice the output's width (2560 for a 1280 output): that alone tells that KWin took the declaration.
- The test program draws with scissored clears only (a red or blue field, the tag LEFT or RIGHT in 5x7 glyphs, a frame number, a white square and a one pixel white frame), looks the stereo API up with `dlsym` and `g_object_class_find_property`, so one binary is the test on the patched GTK and the control on Debian's. A checker redraws the expected picture in Python and compares every sample of each eye.
- The cases, each in a fresh KWin session: stereo; the swapped-eye program (must fail the LEFT/RIGHT check); a resize while shown; stereo switched off and on; hidden and shown; the failure cases (a widget opacity below 1; the protocol removed with `GDK_WAYLAND_DISABLE=kde_stereo_content_manager_v1`; a context that cannot export a dma-buf); the control (stereo off against Debian's GTK).

## The scripts

- `scripts/glarea-stereo-test.c`: the test program. `cc glarea-stereo-test.c $(pkg-config --cflags --libs gtk4 epoxy) -ldl`, then run it with `--stereo` (and `--swap`, `--opacity 0.99`, `--grow-after 3`, `--toggle-after 4`, `--hide-after 3`, `--overlay`, `--offload`, `--frame N`, `--size WxH`, `--report FILE`, `--quit-after SECS`). It writes the property values, the renderer string and the eyes its render handler saw to the report file. The same binary runs on a GTK without the API (it looks the property and the getter up at run time): that is the control.
- `scripts/check_eyes.py CAPTURE.png [--size WxH] [--expect stereo|left|mono] [--overlay] [--tol N] [--swap]`: redraws the expected pictures and checks the capture: both eyes in one capture (twice the output's width), red LEFT in the left half and blue RIGHT in the right half with no red in the right and no blue in the left, the area at its own size and place in both halves, each eye's every sample equal to what the program drew, and everything outside the area identical in both eyes. `--expect left` and `--expect mono` check a 2D capture (the area that could not be shown per eye, an area without stereo). It exits 1 when a check fails, so the negative controls are runs that must exit 1.

## Traps

- **Both eyes shown squeezed in the area's place when GTK does not offload.** Symptom: the area shows two small pictures side by side. Cause: GSK draws the subsurface node's child when it cannot attach it, and the child was the double-width texture scaled to the area. Fix: the child is a clip of the area's size over a texture node twice as wide, so the fallback is the left view at its own size, and GSK's offload takes the whole texture for a stereo subsurface instead of the clip's part. Found by reading `gsk_gpu_node_processor_add_subsurface_node` and `find_texture_to_attach`.
- **No dma-buf, no subsurface.** Symptom: `🗙 Texture type not supported or export failed` in `GDK_DEBUG=offload`. Cause: GTK attaches only dma-buf textures, and llvmpipe cannot export one. Fix: none in GTK; prove the offload on a GPU (the RTX 3060 through CDI), and let the CPU-only run prove the honest failure. The area says it.
- **zink on NVIDIA kills the connection (unpatched GTK too).** Symptom: `Error 9 (Bad file descriptor) dispatching to Wayland display` right after `zwp_linux_dmabuf_v1.create_params`. Cause: not found yet; Debian's gtk4 4.24.1 shows it as well with a plain `GtkGraphicsOffload` around a `GtkGLArea` (control: the same program without our change), so it is not the stereo change. NVIDIA's own EGL works. For milestone 2.
- **A blit ignores the colour mask and obeys the scissor.** ES 3.2 section 16.2.1: only the pixel ownership test, the scissor test and sRGB conversion affect a blit. A program that leaves `GL_SCISSOR_TEST` on (the test program does) would clip the copy: disable it around the blit.
- **Alpha.** The picture handed over is opaque (`GL_RGB8`, `B8G8R8X8`): GTK refuses a non-opaque texture on a subsurface below the window, and a stereo picture has nothing to blend with.
- **The decision comes a frame late.** GSK decides offloading while it renders, after the snapshot. The area checks `gdk_subsurface_get_texture()` after the frame clock's `after-paint` and switches to the left view alone when the subsurface has no texture; the clip makes that frame correct too.
- **A passwd entry for uid 1000.** GTK's tests start `dbus-daemon`, which fails with `Could not get password database information for UID` in a container without one (the rig mounts a passwd file).
- **Build dependencies against the edition's pins.** `apt-get build-dep gtk4` in an image with the edition's repository at pin 1001 stops on librsvg (it wants libdav1d 1:1.5.4) and on the media libraries. Lower the edition pin to 100 and pin the Mesa and Wayland packages back to the edition at 1001.
- **An image committed from a container started with `--entrypoint sh` keeps that entrypoint**: `docker run IMAGE sh script` then fails with `sh: 0: cannot open sh`. Start with `--entrypoint sh IMAGE script`.
- **Reproducing the program's picture in the checker.** GL's y goes up and the capture's goes down: the first checker put the white square one row off (134 samples per eye). Redraw the expected picture with the same flip, and compare every sample.
