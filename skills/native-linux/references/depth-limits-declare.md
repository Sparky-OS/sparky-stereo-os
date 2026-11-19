# The person's depth limits through libstereo-declare (1.10.0)

A program that shows depth reads the limits here before it invents numbers.
Stereo KWin resolves them per output, from the person's sunk and popped limits built on the output's display, and hands them over on both routes; the library gives the same two numbers on both.

## The recipe

Wayland (`kde_stereo_content_manager_v1` at version 5 or later):

```c
stereo_declare_wayland_init(display, NULL);  /* once, then dispatch the queue */
struct stereo_depth_limits limits;
int r = stereo_depth_wayland_watch_limits(surface, on_limits, data);  /* the listener hears every delivery */
if (r == -ENOTSUP) { /* this compositor does not send them: say so, draw flat */ }
r = stereo_depth_wayland_get_limits(surface, &limits);                /* 0, -ENODATA until the first event, -ENOTSUP */
```

X11 and Xwayland (`_KDE_NET_WM_STEREO_CONTENT_SUPPORTED` 10 or later, on a window that declares stereo content; 11 or later on a declared child window, which is where a toolkit's 3D area is: see [x11-declared-child-limits-and-first-pair.md](x11-declared-child-limits-and-first-pair.md)):

```c
stereo_declare_x11(display, window, STEREO_SBS_FULL, STEREO_CLASS_GAME, STEREO_GAME_3D);
XSelectInput(display, window, PropertyChangeMask);
int r = stereo_depth_x11_get_limits(display, window, &limits);        /* 0, -ENODATA until KWin writes it, -ENOTSUP */
/* in the event loop */
if (stereo_depth_x11_limits_event(display, window, &event, &limits) == 1) { /* changed */ }
```

Python: `Declaration.depth_limits(window)`, `x11_depth_limits(display, window)`, `x11_depth_limits_event(display, window, event)` and `Wayland(display).depth_limits(surface)` / `.watch(surface, callback)`; they return `DepthLimits(sunk, popped)` and raise `DepthLimitsNotOffered` or `DepthLimitsNotDelivered`.
The full table of returns is in the library's API.md ("The person's depth limits").

- **The numbers.** `sunk` and `popped` are magnitudes in pixels of a view 1920 wide (24.8 fixed point on the wire), the same as the protocol's `depth_limits` and the X11 property; they are tailored to the screen, never to the element: on the screen a limit is `limit * output width / 1920` pixels, whatever the size of the window, the 3D area, the picture, the thumbnail or the icon, and whatever the render resolution. There is one separation setting, in one place (the desktop's 3D Depth settings). A program never rescales the limits by its own width; an earlier version of this line said to, and that made small views nearly flat. Defaults 10 and 4 at the person's default settings, times the display's factor.
- **Never zeros.** `-ENOTSUP` is "the compositor does not offer them" (protocol under 5, support under 10, or the loaded library older than 1.10.0); `-ENODATA` is "offered, not delivered yet". The structure is untouched in both. A program then shows 2D, or says it has no limits (as Amoebius's `StereoOutput.Status` does), and never invents numbers.
- **One object per surface.** `get_limits` and `watch_limits` follow the surface's depth with the same `kde_stereo_depth_v1` that `stereo_depth_wayland_watch()` makes; the first call creates it, so `get` answers `-ENODATA` until the event is dispatched. The listener is not called for limits already received: read them with `get` right after watching.
- **Live.** A change of the person's limits reaches the listener (Wayland) or the property event (X11) about 0.3 s after `qdbus6 org.kde.KWin /KWin reconfigure`; the same happens when the output's mode or kind changes or the window moves to another output.

## Several screens: the compositor says which output

A program can receive the correct limits and still be unable to convert them to buffer pixels.
In staged libstereo-declare 1.11.0, `stereo_depth_wayland_get_buffer_limits(surface, buffer_width, shown_width, &limits)` first reads the surface's limits, then calls the display-wide `stereo_depth_wayland_output_width()`.
That helper returns `-ENOTUNIQ` when two outputs are advertised, including when the window lies wholly on one of them.
It leaves the destination untouched.
Do not choose the first `wl_output`, guess from the window's size, or replace that error with zero limits.
The compositor owns the surface's output selection; a program reports that it cannot obtain its limits through the layer's problem message.

### Reconcile before a change

1. Read the published KWin source's `debian/patches/series`, apply it to the matching orig archive and inspect `src/wayland/protocols/stereo/kde-stereo-content-v1.xml`.
   In published KWin +stereo3d59 it is v5, with two fixed-point arguments on `depth_limits`, and no output width.
   The XML in published plasma-wayland-protocols +stereo3d11 is still v3; the staged 1.11.0 library carries KWin's v5 copy.
   Editing one copy does not update the others.
2. Follow `StereoDepthStates::watch`, `scheduleUpdate` and `update` in `src/scene/stereodepthstates.cpp`.
   They react to the window's geometry and output, settings and backend-output changes, then take both limits from `window->output()` and deliver them to every followed surface in its tree.
   For a Wayland window, `WaylandWindow::updateGeometry` selects the output at the frame's center through `Workspace::outputAt`.
3. Follow `SurfaceInterface::setStereoDepthState` and `StereoDepthSurfaceV1::sendState`.
   A new follower gets cached state; subsequent updates send limits only if the values changed and the resource is new enough.
   Moving between screens with equal limits sends no new `depth_limits` event in v5.
4. The repair belongs in a new protocol version: KWin must carry the selected output's pixel width with the matching limits, send the new state on output changes even when the limits are equal, and the library must consume that surface-specific width.
   Keep the old events and their version guards, and retain `-ENOTUNIQ` for an older compositor that cannot supply the width.
   ORDER 750e implements this in KWin +stereo3d60, plasma-wayland-protocols +stereo3d12 and libstereo-declare 1.12.0; the candidate package and scene qualification status must accompany that claim. It is not functionality in +59 or 1.11.0.
   The library's one conversion function continues to perform the buffer-pixel conversion; no program adds arithmetic.

### Version 6 plumbing and the standard alternatives

Version 6 adds `output_width(uint width)` immediately before each `depth_limits` event. The value is the width in pixels of one view of the output KWin already selected for that window. Zero means unavailable. The cached state includes the selected backend output's UUID and width, so equal limit values still resend the pair on an output change. Legacy v5 resources retain their old event guard and change detection.

The library stores the width on the independent depth follower for that surface. Its buffer getter consumes it on v6, and retains the existing display-wide helper only for old compositors. It calls the same conversion function, keeps SONAME 1 and every old exported symbol, and adds no UI dependency. A missing v6 width is `-ENODATA`, not an invented screen choice.

Check standard APIs before adding an event. Wayland main's `wl_surface.enter` reports intersections, possibly several; `preferred_buffer_scale` reports an integer scale, not a pixel width. Both use the toolkit's surface listener, and `wl_proxy_add_listener` refuses a second implementation. Fractional-scale-v1 supplies a scale numerator and permits one object per surface; the toolkit may already own it. Experimental fractional-scale-v2 changes coordinate spaces, without associating this selected output width with depth limits. Wayland issue 576's preferred_outputs was still an open proposal when checked on 2026-11-19. Read KWin master, Wayland main, the protocols main, their merge requests and issues again before relying on that status.

All three shipped XML copies must agree. Append the new since=6 event after older requests in the XML so the scanner's monotonic-since check passes; event and request opcodes are separate, so moving the since=5 event after requests preserves its event opcode 1 and gives output_width opcode 2. The protocols package's own contract test must check version 6 rather than freezing the former version 3.

### Two-output wire rig

Run only in a disposable container with its own session bus and runtime directory:

```sh
KWIN_VIRTUAL_STEREO_MODES=1 \
KWIN_VIRTUAL_OUTPUT_SIZES=1920x1080,1280x800 \
kwin_wayland --virtual --output-count 2 --socket=proof
```

Set `WAYLAND_DISPLAY=proof` for clients inside that session.
Enumerate with `kscreen-doctor -j`, choose each output's listed `stereo3D: 1` mode by its current id, switch both, and read back the selected modes and widths.
Keep the frame wholly on each output in turn and record its actual output with a KWin script.
Use `WAYLAND_DEBUG=client` on a mapped xdg toplevel that calls `stereo_depth_wayland_watch_limits` and samples both the raw and buffer-limits getters while reading its Wayland socket.
A bare surface is insufficient.
With +59 and 1.11.0, both screens deliver raw 10/4 limits without a physical-size fixture, while the buffer getter returns `-ENOTUNIQ` on both.
In a fresh one-output session, the same 640-pixel view receives buffer limits 10/4 on the 1920-pixel output.
Change the test session's settings to 20/8 and reconfigure through its private D-Bus connection; require the changed event, then restore 10/4.
For different per-output values, provide a public test EDID to only one output with `KWIN_VIRTUAL_OUTPUT_EDIDS=,PATH`; verify the physical sizes and the values actually received before judging a move.
This checks the wire and library calls; the application's nearest-point disparity and both-eye pictures require the separate scene run.

### Traps found in ORDER 750e's reconcile

- **Symptom:** raw limits are available, but a scene gets no buffer limits with several screens.
  **Cause:** v5 identifies neither the chosen output nor its width; 1.11.0's width helper deliberately refuses an ambiguous display-wide answer.
  **Fix:** carry the compositor-selected output width with its limits in the next protocol version, then use it in the shared library.
  **How found:** a mapped client on published +59, moved between 1920- and 1280-pixel virtual outputs, returned `-ENOTUNIQ` on both; the same call succeeded with one output.
  The staged Spirula +stereo3d5 red scene also measured zero disparity on both screens in full and half windows; its one-screen control measured -3.984716 and -3.989684 px against -4 px. Its existing localized message says the limits were not received and the two pictures are identical, so this repair does not change the program.
- **Symptom:** moving to another output produces no new limits event.
  **Cause:** `sendState` compares only the two limit values, which may be equal on different screens.
  **Fix:** include the selected output state in the new version's change detection.
  **How found:** the protocol trace kept one limits event across the move with equal values; an EDID case with different limits did send another event.
- **Symptom:** `kscreen-doctor` prints "Cannot find output with id" and exits successfully, leaving the 2D mode current.
  **Cause:** explicitly setting `KSCREEN_BACKEND=KWayland` differs in case from the backend's `name()` value, `kwayland`; `loadBackendInProcess` can replace that backend between getting and setting a configuration, so the output ids no longer match.
  **Fix:** use `KSCREEN_BACKEND=kwayland`, or leave the selection to the Wayland platform, and require a mode readback.
  **How found:** the failed readback, followed by the case-sensitive cache comparison in libkscreen's `src/backendmanager.cpp`; the same mode command then applied on both outputs.

### Candidate package and measurement traps found while building the repair

- **Symptom:** `dpkg-source -b` reports reverse hunks as unexpected upstream changes after replacing an old quilt patch. **Cause:** an in-place successor overlays new patch files onto an already-applied old stack. **Fix:** the explicit `lc-successor.py --reapply-patches` route temporarily restores the old patch files, pops that stack, installs the overlay and pushes it. **How found:** compared the source produced by both the KWin and protocols successor descriptors against the published applied trees.
- **Symptom:** the scanner says the since version is not increasing, and the protocols suite fails. **Cause:** a since=6 event was placed before older requests. **Fix:** order versioned events after those requests, retaining the event opcode order, and run all 127 protocol tests. **How found:** the actual protocol package build, which exercises strict scanner tests absent from a library-only compile.
- **Symptom:** an output-change cache fails to compile with QString versus QUuid. **Cause:** BackendOutput::uuid() returns a string. **Fix:** construct the QUuid explicitly. **How found:** the complete KWin compile; a fresh corrected descriptor was prepared.

- **Symptom:** every desktop role measures zero, although the engine logs the expected per-eye shifts. **Cause:** the measurement indexes the left half for both views. **Fix:** address the right half at per-eye-width plus x, and require the zero-limits control and a distinct best match. **How found:** a read-only trace of StereoDepth::parallax and PaintData::toMatrix, followed by a fresh capture on the unmodified published binary. The corrected match gives the complete -10/0/-2/-4/+4/+8 table.

## Traps, symptom first

- **`interface 'kde_stereo_depth_v1' has no event 1` and the connection drops.** KWin sent `depth_limits` (since 5) to an object bound at a lower version. The library binds the lower of the compositor's version and the version its protocol copy knows (6 in 1.12.0, `STEREO_PROTOCOL_VERSION` in `stereo-declare.c`), so it never expects an event above the bound version. Raise that number only together with the protocol XML in `protocol/`; see `stereo-proof-rig/references/versioned-events.md` for the server side.
- **A program built for 1.9 sees no limits on a KWin that sends them.** The 1.9 library binds version 4: nothing to read, no error. Upgrading the library to 1.10 is enough; the SONAME and every old symbol are unchanged, so no relink is needed (proved: a client built against 1.9 ran on KWin +stereo3d54 with the 1.9 and the 1.10 library, same depth_state, connection clean).
- **`wl_global_create: implemented version ... higher than interface version (6 > 5)` in a test.** The generated server cannot advertise a global newer than the XML. To model a compositor newer than the library's copy, copy the `wl_interface` and raise its `version` (`tests/test-wayland.c`, `tests/wayland-shim.c`).
- **An in-process fake compositor hangs in `wl_display_roundtrip`.** Server and client share one thread, so nobody dispatches the server; pump both sides (flush, `wl_event_loop_dispatch`, `wl_display_flush_clients`, read events). The Python Wayland test hung for minutes before the cause was found with `docker top` and `timeout` around the call.
- **`XGetWindowProperty` of the limits.** Format 32 comes back as C `long`s: take the low 32 bits, convert to `int32_t`, divide by 256. Request three values and require exactly two, otherwise a longer property reads as limits. A property of another type or format is `-EPROTO`, a missing one `-ENODATA`.
- **The rig cannot show the display factor.** The virtual output reports no physical size (`kscreen-doctor -j`: `sizeMM` -1), so KWin's factor is 1 by its own rule and the client reads exactly the kwinrc `[StereoDepth]` values (10 and 4 by default; after `kwriteconfig6 --file kwinrc --group StereoDepth --key SunkLimit 20` and `PoppedLimit 8` and a reconfigure, 20 and 8). The factor itself is KWin's autotest (`testStereoDepthExchange`).
- **A stereo mode in the rig.** `KWIN_VIRTUAL_STEREO_MODES=1`, then `kscreen-doctor output.Virtual-0.mode.4` and a readback that the mode marked `*` is `virtual-3D:5` (the command exits 0 for an unknown name); the window's `depth_state` then says `awake=1`, on a 2D output `awake=0`; the limits are the same.

## Rig and build, as done in ORDER 495

- Library build and tests: the KWin build image plus `python3-xlib` for the Python test, in a container with `--network none` after the image is made (apt over https only; the image's `deb-multimedia` source needs its key, remove that list in the throwaway container). The amd64 SDK image for the recipe also needs `dh-python` and `bubblewrap`; an i386 image: the media i386 build image plus `cmake xvfb xauth python3-xlib dh-python wayland-protocols`.
- Real rig: the `kwin-487b-rig:54` image (KWin +stereo3d54), one fresh session per case (`dbus-run-session`, `kwin_wayland --virtual --xwayland --socket=w`), the client with `LD_LIBRARY_PATH` for the library under test (or the staged `libstereo-declare1` installed with `dpkg -i`, then `setpriv` to the render group), the person's limits changed live in `kwinrc`. A Wayland window needs an xdg toplevel with a buffer to count as a window; a bare surface gets no limits.
- Package: the recipe pins the library's release commit (`rev=` in `prepare-source.sh`); a change to the library after the pin means a new pin, a new recipe commit and a rebuild. Compare every `/usr/share` file of the two architectures with `cmp`: only the per-architecture `dpkg-stereo/lc/*/ARCH.json` differ. The symbols file must equal `nm -D --defined-only` of the library (every old symbol stays, six new at 1.10.0).

### Qualification status of the ORDER 750e candidates

Library 1.12.0 passed all nine tests and the archive gate on amd64 and native i386, retaining every old symbol and NEEDED list. Protocols +12 passed all 127 tests and its archive gate. KWin +60 completed the edition's retained-object packaging route and archive gate, with 13 qualified binary archives and its completed build record. The upgrade from published +59 and library 1.11.0 completed without removals. Every functional KWin payload path and all 66 functional ELF NEEDED lists remain; generated Depends minima changed for libstdc++6 and libstereo-policy1, as recorded in the package comparison.

Installed +60 wire checks passed with 1920/1280 outputs, equal-width 1920/1920 outputs, live limits and moves both ways. Every v6 limits event follows its matching output_width event. The old 1.11 library on +60 and new 1.12 library on +59 retain clean legacy behavior: explicit -ENOTUNIQ on two outputs, successful one-output conversion.

Spirula +stereo3d5 with library 1.12.0 measures -3.984716/-3.989684 px in maximized/half-width windows on 1920, and -2.657709/-2.661689 px on 1280, versus predictions -4 and -2.666667 with a fixed 0.03 px tolerance. Returning to 1920 restores -3.984716 px. Both eyes of the one-output scene are byte-identical to the red-one control within the central scene region; the dynamic timing glyphs are excluded.

The fixed 640-pixel window exposes a remaining application cache fault. Starting on 1920, moving to 1280 and returning leaves the nearest point at -3.997654 px on all three captures. The 1280 row fails; it must reach -2.666667 px. This is not a completed green qualification. The existing NativeViewport limits callback is empty, and ViewportPanel compares only raw 10/4 and settings revision before invalidating its pair. Output width changes the conversion without changing those raw numbers. The focused program correction is Spirula commit 27fbbcff over accepted d5c4ac86: advance a parent notification generation in the existing callback, and let every viewport invalidate its pair through its existing render epoch. The +stereo3d6 Vulkan/CUDA package build is in progress; no completed green claim is made yet. No server limit, camera formula or geometry workaround is justified.

KWin +60's own 13 desktop/control measurements equal published +59: wallpaper -10, panel 0, active 0, inactive -2/-4, menu +4, submenu +8, popup +4, and the zero-limit base roles all 0. Every best match has zero error and a distinct next-best match. Staged Fraqtive +stereo3d3 passes on 1920, 1280 and return, with nonzero fit and the corresponding 10/4, 6.667/2.667 and 10/4 limits.

- **Symptom:** Lean Code refuses resumed output filenames as already existing. **Cause:** an earlier incomplete run left unpublished binary archives in its output directory. **Fix:** preserve those exact lane-owned files with a hash manifest in a separate scratch directory, then rerun packaging with the overwrite guard unchanged. **How found:** the resumed +60 build refused the 13 incomplete files; preserving them allowed all 13 packages to finish the archive gate and completed build record.
- **Symptom:** a fixed-size scene remains at the old screen's separation after a move although the wire has the new width. **Cause:** the application treats equal raw limit numbers as an unchanged render state and discards its callback. **Correction:** track the existing limits notification generation, invalidate the rendered pair through its existing epoch and reread the library's conversion, including when raw values compare equal. **How found:** measured both-eye arrays with an unchanged 640×600 frame on each output; resizing had hidden the cache fault in earlier max/half rows.
