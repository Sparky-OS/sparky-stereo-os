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

X11 and Xwayland (`_KDE_NET_WM_STEREO_CONTENT_SUPPORTED` 10 or later, on a window that declares stereo content):

```c
stereo_declare_x11(display, window, STEREO_SBS_FULL, STEREO_CLASS_GAME, STEREO_GAME_3D);
XSelectInput(display, window, PropertyChangeMask);
int r = stereo_depth_x11_get_limits(display, window, &limits);        /* 0, -ENODATA until KWin writes it, -ENOTSUP */
/* in the event loop */
if (stereo_depth_x11_limits_event(display, window, &event, &limits) == 1) { /* changed */ }
```

Python: `Declaration.depth_limits(window)`, `x11_depth_limits(display, window)`, `x11_depth_limits_event(display, window, event)` and `Wayland(display).depth_limits(surface)` / `.watch(surface, callback)`; they return `DepthLimits(sunk, popped)` and raise `DepthLimitsNotOffered` or `DepthLimitsNotDelivered`.
The full table of returns is in the library's API.md ("The person's depth limits").

- **The numbers.** `sunk` and `popped` are magnitudes in pixels of a view 1920 wide (24.8 fixed point on the wire), the same as the protocol's `depth_limits` and the X11 property; scale them to the view's width, `limit * width / 1920`. They equal pixels of the output only for a 1920 wide output. Defaults 10 and 4 at the person's default settings, times the display's factor.
- **Never zeros.** `-ENOTSUP` is "the compositor does not offer them" (protocol under 5, support under 10, or the loaded library older than 1.10.0); `-ENODATA` is "offered, not delivered yet". The structure is untouched in both. A program then shows 2D, or says it has no limits (as Amoebius's `StereoOutput.Status` does), and never invents numbers.
- **One object per surface.** `get_limits` and `watch_limits` follow the surface's depth with the same `kde_stereo_depth_v1` that `stereo_depth_wayland_watch()` makes; the first call creates it, so `get` answers `-ENODATA` until the event is dispatched. The listener is not called for limits already received: read them with `get` right after watching.
- **Live.** A change of the person's limits reaches the listener (Wayland) or the property event (X11) about 0.3 s after `qdbus6 org.kde.KWin /KWin reconfigure`; the same happens when the output's mode or kind changes or the window moves to another output.

## Traps, symptom first

- **`interface 'kde_stereo_depth_v1' has no event 1` and the connection drops.** KWin sent `depth_limits` (since 5) to an object bound at a lower version. The library binds the lower of the compositor's version and the 5 its protocol copy knows (`STEREO_PROTOCOL_VERSION` in `stereo-declare.c`), so it never expects an event above the bound version. Raise that number only together with the protocol XML in `protocol/`; see `stereo-proof-rig/references/versioned-events.md` for the server side.
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
