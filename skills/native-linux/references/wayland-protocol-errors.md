# A Wayland protocol error that closes a program: resolve the object, find the side at fault

Learned on ORDER 578 (November 2026): VLC Stereo closed on a notebook with `wl_display#1: error 0: invalid object 46` and `The Wayland connection experienced a fatal error`, in a virtual 3D mode at 125 %.
The cause was the player's, not the compositor's, and not the 3D mode's or the scale's.

## Recipe

1. **Make it red in a private compositor, with the client's trace.**
   Run the program under `WAYLAND_DEBUG=client` in the proof rig ([stereo-proof-rig](../../stereo-proof-rig/SKILL.md)) and drive it the way a person does, with KWin's fake input ([input-delivery.md](../../stereo-proof-rig/references/input-delivery.md)): pointer moves, double clicks, keys, the program's own views and menus.
   A program left alone may never fail; VLC Stereo lived through 40 s of untouched playback, and one Ctrl+L closed it 4 to 41 ms after Qt destroyed its video surface.
2. **Read the error line, then the object.**
   libwayland 1.26 prints each request as `{QUEUE}  -> interface#ID.request(...)`, the queue being the one its proxy belongs to.
   The error comes as `{Display Queue} wl_display#1.error(wl_display#1, 0, "invalid object 40")`.
   Find the request that created the id (`new id wl_surface#40`), every request that named it, the one that destroyed it, and the last one sent on it before the error:
   ```
   grep -n -E '#40[.(,)]|new id [a-z_0-9]+#40\)' trace.log
   ```
   Ids are reused once the server has sent `delete_id`, so read the lines in order, not as a set: in ORDER 578 the destroyed video surface's id 33 came back at once as a frame callback of the main window.
3. **Name the side at fault from libwayland's own rules** (wayland 1.26.0).
   - The server's `wl_client_connection_data` (`src/wayland-server.c`) posts `invalid object N` for a request whose target id has no object in the client's map, and nothing else posts that exact text.
   - The client marshals a request on any proxy, destroyed or not, and on an id the server deleted (`wl_proxy_marshal_array_flags` checks neither `WL_PROXY_FLAG_DESTROYED` nor `WL_PROXY_FLAG_ID_DELETED`).
   - So: the client destroyed the object itself (a `destroy` request on it in the trace) and something still used it: **the client is at fault**, usually two threads or two libraries sharing one object.
     The server deleted an object the client never destroyed (`delete_id` with no `destroy` request before it): **the compositor is at fault**, unless the protocol says the object dies with an event (a `wl_callback` after `done`).
   - A protocol error of the object's own interface (`wp_viewport#36: error 3: the wl_surface for this viewport no longer exists`) is the same kind of fault seen from another object: a request on an object whose surface is gone.
4. **Find who sent the last request and from which thread.**
   The queue in braces tells which code sent the request: `{Default Queue}` is the toolkit's main thread, `{mesa egl surface queue}` is Mesa's EGL inside the thread that swaps, an unnamed queue is a library's own (VLC's declaration and viewport).
   A destroy on one queue followed by a request on another is a lifetime shared across threads.
5. **Make the trigger certain before you fix.**
   When the natural trigger is rare, force it: `../../stereo-proof-rig/scripts/qt5-hideshow.cpp`, preloaded into a Qt 5 program, hides and shows its native child window from Qt's own thread after `HIDESHOW_AFTER` milliseconds, as Qt does when a container or its page is hidden.
   Then find the natural trigger in the program's own code (what hides, re-parents or re-creates that window) and make it a rig row; the row, not the helper, is the proof.
6. **Search upstream before fixing**, for the same error and for the same lifetime problem in sibling code ([search-upstream-first](../../search-upstream-first/SKILL.md)); carry the maintainer's technique when the sibling code has one.
7. **Prove:** the red row many times on the published build, the same row many times on the fixed one, at every scale and output mode, on each card, the 2D control unchanged.

## Qt 5 destroys a hidden window's surface

Qt Wayland 5.15 (KDE's kde/5.15 branch, which Debian's 5.15.19 follows): `QWaylandWindow::setVisible(false)` calls `reset()`, which destroys the window's `wl_subsurface` and `wl_surface` (emitting the private `wlSurfaceDestroyed()` first); the next show makes a new surface.
Qt hides a native child window whenever its `QWidget::createWindowContainer` container is hidden: the page that holds it is turned, the widget gets a new parent (Qt hides a widget while re-parenting it), the top level is made again (`setWindowFlags`).
`QWindow::visibleChanged(false)` is emitted before the surface goes; `QPlatformSurfaceEvent::SurfaceAboutToBeDestroyed` comes only from `QWindow::destroy()`, after the hide has already destroyed it.
VideoLAN met the same behaviour in VLC 4 (84e7e017, "qt: do not hide window on close on Wayland", which says it holds before Qt 6.9) and removed VLC 3.0.x's Qt Wayland video window (04d8fcb9).

So a program that draws on a Qt window's surface from a thread of its own (EGL, Vulkan, a player's video output) holds a surface whose life is Qt's.
Draw on a surface of your own instead, as VLC 4's Wayland compositor does (`modules/gui/qt/maininterface/compositor_wayland_module.c`):

- create the `wl_surface` yourself (`wl_compositor` v4 bound on an event queue of your own; v4 has `damage_buffer`, which Mesa uses, and sends no preferred-scale events), with an empty input region so that the pointer reaches the toolkit's window under it;
- make it a desynchronized sub-surface of the main window's surface only while the widget that holds its place is shown, at that widget's position plus the window's `frameMargins()` (where Qt places its own sub-surfaces), and destroy that role on the widget's hide event; on the main window's next expose make it again (a hidden window gets its new surface only when shown);
- set the buffer scale Qt gives its own surfaces (`QPlatformWindow::devicePixelRatio()`, the integer the window's surfaces get), on the main thread; the drawing thread's next commit takes it;
- destroy the surface only when the drawing thread is done with it (VLC: when the video output releases the window).
A sub-surface whose parent died is inert: destroying it later is allowed, but KWin answers `set_position` on it with `wl_subsurface: error 0: no parent`, so never move it after the parent's hide.

## The trap, ORDER 578

- **Symptom:** VLC Stereo closes during playback with `wl_display#1: error 0: invalid object N` or `wp_viewport#N: error 3: the wl_surface for this viewport no longer exists`, sometimes with `h264 get_buffer() failed` and `no frame!` near it.
- **Cause:** the video output drew, through Mesa's EGL on its own thread, on the `wl_surface` of the `QWindow` the interface held in a window container (patch 3d-0021); Ctrl+L (the playlist) moved the playing video widget into the playlist's panel, Qt hid the window while re-parenting it and destroyed its surface, and Mesa's next `attach` (or VLC's next `wp_viewport.set_destination`) named the dead object 4 to 41 ms later.
  `get_buffer() failed` is libavcodec's line when VLC's frame allocator gets no picture; with software decoding that happens only while the decoder is flushed or its video output is gone, so it is a bystander of the closing player, not a cause.
- **Fix:** 3d-0049 (VLC Stereo +stereo3d20): the interface makes the video surface itself, as above; a plain widget holds its place and takes the mouse and the keys, as on X11.
- **How found:** `WAYLAND_DEBUG=client`, the error line, the object's creating request (`wl_compositor#4.create_surface` on `{Default Queue}`, then `get_subsurface(..., wl_surface#40, wl_surface#26)`), Qt's `wl_subsurface#42.destroy()` and `wl_surface#40.destroy()` at the key press, and `{mesa egl surface queue}  -> wl_surface#40.attach(...)` right before the error; the forced hide first, then the program's own `showTab()`, which re-parents the video widget.
- **Bounded:** on the published build (+stereo3d19) 22 of 22 rows with Ctrl+L died (100, 125 and 150 %; a 2D output and the side by side, top and bottom and anaglyph twins; 2D and 3D films; AMD and NVIDIA; software and copy-back decoding), every one naming the destroyed video surface; untouched playback, pointer moves, double clicks into full screen, seeks, minimal view, minimizing, always on top, output mode and scale changes lived. Neither KWin's 3D mode nor the scale is part of the cause.
- **Proved:** on +stereo3d20 the same 22 rows lived through 164 presses (344 sub-surface roles made and dropped, no protocol error, both eyes right in every capture); 24 static captures at 100, 125 and 150 %, windowed and full screen, both cards, 3D and 2D films, have the film at the same place and size in each eye as the published build, and differ only where one build differs from itself between two moments (the seek slider, the fixture's coding noise at fixed spots); double click, F, Esc and Space read back the same from VLC's MPRIS state and KWin's window list.

## Traps of the rig

- **Symptom:** a batch row has no verdict, or its input steps stop half way. **Cause:** the session script was edited while a container ran it (bash reads a script as it goes). **Fix:** each case runs its own copy of the session script.
- **Symptom:** rows "live" with no video at all. **Cause:** the fixtures folder was removed by a work folder of the same name. **Fix:** give the fixtures and the work trees distinct names; a row's log saying `cannot open file` is void, not a pass.
- **Symptom:** a run dies with `The Wayland connection broke. Did the Wayland compositor die?` and no error event, while KWin's log says `error in client communication (pid N)`. **Cause:** libwayland's server posted an error and closed the client (`wl_client_connection_data`, after `client->error`) before the event reached it. **Fix:** class the run by the client's last requests (here an `attach` on the destroyed surface), not by the printed error. **How found:** KWin's log of the same session, then libwayland 1.26's `wayland-server.c`.
- **Symptom:** the forced trigger's rows "pass" on the fixed build. **Cause:** `qt5-hideshow.cpp` prints `hideshow: no visible video window`: the fixed program has no Qt window for the video any more. **Fix:** such a row is not a green; the natural trigger's rows are.
- **Symptom:** the fix fails to build with `expected unqualified-id before numeric constant` at `QEvent::Expose`. **Cause:** `<X11/Xlib.h>` defines `Expose` as a macro. **Fix:** `#undef Expose` beside the file's existing `#undef KeyPress`; rebuild only the plugin in the failed package tree (`make -C modules libqt_plugin.la`) before the next full build.
- The rig writes `qt-privacy-ask=0` into the profile's `vlcrc` before VLC starts, as a returning person has it, so no first-run question can hold the window.
- **Symptom:** `kscreen-doctor` aborts with `No shell integration named "xdg-shell" found`. **Cause:** the image lacks Qt 6's Wayland plugins. **Fix:** `qt6-wayland` in the rig image.
- **Symptom:** VLC decodes in software in the rig although VA-API works there. **Cause:** VLC Stereo is a copy-back caller of the edition's media GPU route, which answers software unless copying back is allowed (`MEDIA_GPU_ROUTE_COPY_BACK=true`, or `[Decoding] CopyBack` in `sparky-stereo-graphicsrc`). **Fix:** run the rows both ways.
