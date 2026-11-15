# A Qt window with depth that stays flat

Learned on ORDER 583 (November 2026), on qt6-base 6.11.2+dfsg-5+stereo3d22, Qt Quick 6.11.2+dfsg-3+stereo3d3, Stereo KWin +stereo3d54, Mesa 26.1.6-1+stereo3d24 with its Vulkan stereo layer and Xwayland 24.1.15 +stereo3d3.
Load it with [native-linux](../SKILL.md) when a Qt window whose style shows the depth of its elements (Stereo Union, or a program that sets the window's `_q_stereo_depth`) is shown with both eyes the same and nobody was told, or when a Vulkan program asking for two views on X11 stops at its swapchain.

The result first.
Three routes left such a window flat with nothing said.
The first, Qt's own frame on the OpenGL path, gets its pair from two small changes (built and proved; packages follow).
The other two are planned: the Vulkan stereo layer on an X server without DRI3, and Qt on xcb.

## Tell the three apart, one command each

Run the program in the rig (the [qdiscs fixture](../scripts/qt-quick-pair) prints a `STATE` line at 7 s: `views-asked` is what the window asked, `pair` whether Qt Quick drew the eyes apart, `stereo-format` what the surface got).

1. **Qt's own frame, OpenGL.** The client's protocol log has the frame on the client's side and the mark of depth, but no declaration of a pair.
   `WAYLAND_DEBUG=client PROGRAM 2>&1 | grep -E 'toplevel_decoration_v1#[0-9]+\.configure|set_desktop_depth|set_content'` shows `configure(1)` (client side), `set_desktop_depth(1)` and no `set_content(3)`; qdiscs says `stereo-format 1 views-asked 2 pair 0`.
   Under KWin's own decoration the same window shows `configure(2)` and `set_content(3)`, and pairs.
2. **The Vulkan stereo layer on X11 without DRI3.** `xdpyinfo | grep DRI3` prints nothing and the program's error output has `Mesa stereo layer: this X11 server has no DRI3; the one-layer WSI cannot present a complete pair. The two-view swapchain request was refused.`, then `vkCreateSwapchainKHR` fails with `VK_ERROR_FEATURE_NOT_PRESENT` (-8).
3. **Qt on xcb.** The program runs with `-platform xcb` or `QT_QPA_PLATFORM=xcb` (`tr '\0' ' ' < /proc/PID/cmdline`, `/proc/PID/environ`), and its X11 window carries no declaration: `xprop -id WINDOW _KDE_NET_WM_STEREO_CONTENT` says `not found`; qdiscs says `stereo-format 0 views-asked 2 pair 0`.

## 1. Qt's own frame on the OpenGL path (fixed)

Qt draws its own frame (client-side decorations) when the compositor offers no server-side one (a compositor without a decoration plugin) or a program asks for it.
The window's content is then rendered into a framebuffer object and blitted with the frame into the window surface from a second context ([qt-client-decorations.md](qt-client-decorations.md), route a).

The pair was lost in two places, and each alone leaves the window flat:

- **Qt Quick** (`QQuickWindowStereo::beginFrame()`, qt6-declarative patch s1-0002) drew a window with a frame once ("its frame is no part of the pair") but asked for the two views all the same, so `pair 0` while `views-asked 2`.
  The change: such a window is drawn as a pair when its platform says it draws the frame into both eyes (the window's `_q_stereo_csd_pair_supported`, set by the Wayland EGL window).
- **The Wayland EGL plugin** (`QWaylandGLContext::swapBuffers()`, `DecorationsBlitter::blit()`) took the number of eyes and its API from the context's own format (`m_stereo`), so a window whose engine asked for the pair later (Qt Quick, through `_q_stereo_views`, on a format that did not ask for stereo) was blitted as the left slot alone into `GL_BACK`, from an OpenGL ES context.
  Mesa's two-view surface becomes two views at the first right-eye draw ([lessons](lessons-2026-11.md), "make two-view window surfaces stereo at their first right-eye use"), so it stayed one view wide (buffers 946x653 for a 940x620 window and its frame) and declared nothing, while Qt had marked the window's depth.
  The change: a window whose framebuffer object has a slot per eye is blitted eye by eye from a desktop OpenGL context, made the first time one is blitted when the context's own is OpenGL ES; and the slots follow the surface's views when the surface is made again with another number of them (before, the object kept the slots it was made with).

Measured on llvmpipe, radeonsi and zink over NVIDIA (16 rows a driver), the window in Qt's frame and the same window under KWin's decoration give the same six parallaxes (0.5, -0.478, 1.5, -1.383, 0.25, 1.0 device pixels; at 125 % 0.5, -0.5, 1.5, -1.396, 0.25, 1.0), the eyes differ only inside the content, the frame in each eye equals the frame of the unchanged libraries, and a window without depth and the decorated pair are the same to the pixel as before, on a 3D and on a 2D output.
Depth off, depth off and on, a hide and a show, sixty changes in six seconds, and depth off and on in one turn of the event loop (`QDISCS_OFF`, `QDISCS_TOGGLE`, `QDISCS_LIFECYCLE`, `QDISCS_STRESS`, `QDISCS_FLICK`) each end as they should: the declaration withdrawn while flat, the pair back with the same parallaxes, the program alive.

Upstream Qt moved the frame into subsurfaces on its dev branch (94f96210518d, David Edmundson, "wayland: move decoration into subsurfaces", Qt 6.12), which removes the blitter: at the move to 6.12 the plugin's part goes and Qt Quick's part stays.

## 2. The Vulkan stereo layer on X11 without DRI3 (planned)

Xwayland has no DRI3 when glamor cannot start (no 3D acceleration) or `XWAYLAND_NO_GLAMOR=1` is set.
Measured with the vk-views client ([stereo-proof-rig/scripts/vk-views](../../stereo-proof-rig/scripts/vk-views)):

| Driver | One layer | Two layers |
| --- | --- | --- |
| NVIDIA's, through the layer | shown whole | refused by the layer, the program stops |
| lavapipe (Mesa's own presentation) | shown whole | `VK_ERROR_OUT_OF_DATE_KHR` once Stereo KWin doubles the declared window |
| radv | cannot present at all ("No DRI3 support detected - required for presentation") | the same |

The layer packs both layers into one driver swapchain twice as wide; without DRI3 NVIDIA's presentation copies into the window, which is one view wide until Stereo KWin doubles it, and gives no Present completion for the copied-pair check (patch 0039) to read.

## 3. Qt on xcb (planned)

Nothing on xcb reads `_q_stereo_views`, and Stereo Union learns that a window shows depth only through Wayland (`stereo_depth_wayland_watch`), so a real program on xcb never asks; only a program that sets `_q_stereo_depth` itself shows the red.
Stereo KWin tells an X11 window its depth limits (`_KDE_NET_WM_STEREO_DEPTH_LIMITS`, support 10) but not whether it shows depth now, and has no X11 mark for a pair that is the desktop's own depth.
Programs that meet it: every Qt program started on xcb, such as Debian's qjackctl and qsynth, whose menu entries start them with `-platform xcb`.

## Recipe: the red and the green of route 1

1. The rig image: KWin's decoration installed (`kwin-style-breeze`), so a case chooses Qt's frame by `kwinrc` `[org.kde.kdecoration2] NoPlugin=true` and the control by leaving it out.
2. One case per fresh session, the output in its side-by-side 3D mode, qdiscs on OpenGL, a capture at 8 s; read it with `disc-parallax.py` and [`frame-check.py`](../scripts/qt-quick-pair/frame-check.py) (the eyes may differ only inside the content; with the unchanged libraries' capture as reference, the frame must be the same).
3. A change to the Wayland EGL plugin can be proved without building qtbase: its four sources build alone against the installed Qt and its private headers in about a minute ([`egl-plugin-CMakeLists.txt`](../scripts/qt-quick-pair/egl-plugin-CMakeLists.txt)); lay the built `libqt-plugin-wayland-egl.so` over the installed one. Build the unchanged sources the same way first: it must reproduce the red.
4. A change to Qt Quick needs only the `Quick` target of a configured qt6-declarative tree: 792 steps, about 25 minutes at four CPUs, 1.6 GB of build tree; lay `libQt6Quick.so.6.11.2` over the installed one.

## Traps

- **Symptom:** with Qt's frame the window reports a stereo format, asks for two views and sends `set_desktop_depth(1)`, but Mesa never sends `set_content(3)` and every buffer is one view wide.
  **Cause:** the frame's blit drew only `GL_BACK`, from an OpenGL ES context, so the right view was never drawn and Mesa's surface never became two views.
  **Fix:** blit eye by eye from a desktop OpenGL context whenever the window has two slots (route 1).
  **How found:** the whole protocol log of the framed case against the decorated control: the control's buffers go from 940 to 1880 wide with `set_content(3)`; the framed case's stay 946 wide.
- **Symptom:** after that fix the window is declared as a pair but both eyes are the same.
  **Cause:** Qt Quick's own exception for a framed window: `STATE ... pair 0`.
  **Fix:** the Qt Quick part of route 1.
  **How found:** a diagnostic copy of the plugin printing the slots, the API and the blitter's eyes (`contentEyes=2 desktopGL=1 eyes=2`), so the two slots held the same picture; then `frameMargins()` in Qt Quick's patch.
- **Symptom:** a framed Qt Quick window whose depth is turned off and on quickly ends with `kde_stereo_content_manager_v1#N: error 0: wl_surface already has a stereo content declaration` and a fatal protocol error, on some drivers and runs only (llvmpipe and zink, not radeonsi, in the first matrix).
  **Cause:** the Wayland EGL window reads the window's `_q_stereo_pair` when `_q_stereo_views` changes, as the mark of an engine that composes its pair into one picture (Qt Widgets, side by side in one buffer under a frame), and then declares the surface itself; Qt Quick sets `_q_stereo_pair` too, and once it drew framed windows as pairs a stale `true` from the last frame met a new views request, while Mesa had declared the surface already.
  **Fix:** Qt Quick ends its pair (`_q_stereo_pair` false) before it changes the views request (`QQuickWindowStereo::depthChanged()`).
  **How found:** the stress row of the matrix (`QDISCS_STRESS=1`: sixty changes in six seconds over a hide, a show and a resize) missed its `STATE` line and its capture; the client's log ended on the protocol error, and the manager's object number was Qt's own, not Mesa's.
  The stress row is a race (two later runs of the faulty build passed), so the proof is a case that cannot miss: `QDISCS_FLICK=1` turns the depth off and on again in one turn of the event loop, and the faulty build ends there every time.
- **Symptom:** a rig image runs no command: `/usr/bin/sh: cannot execute binary file`.
  **Cause:** the base image's entrypoint is `bash`, which takes the command as a script; an image committed from a container started with `--entrypoint /bin/bash` keeps that entrypoint, and `docker commit --change 'ENTRYPOINT []'` does not clear it.
  **Fix:** commit with `--change 'ENTRYPOINT ["/usr/bin/env"]'`, or start with `--entrypoint /bin/sh`.
- **Symptom:** a rig image's `apt-get update` fails with `The repository 'file:/repo mashtabba Release' no longer has a Release file`.
  **Cause:** the image's own source list names a repository folder that was mounted only when that image was made.
  **Fix:** set that list aside while the new image is made, and put it back.
