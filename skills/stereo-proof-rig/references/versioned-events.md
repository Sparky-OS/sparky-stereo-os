# Versioned events and legacy clients

Symptom: `interface 'kde_stereo_depth_v1' has no event 1`, then `The Wayland connection experienced a fatal error: Resource temporarily unavailable`. Read the first protocol error before treating the later errno text as a resource shortage.

## Diagnose and fix

1. Capture `WAYLAND_DEBUG=client` and, when needed, `WAYLAND_DEBUG=server` in a private compositor session. Find the registry binding, the child object it creates, and the event just before the connection fails.
2. Compare the object's negotiated version with the event's XML `since`. [Wayland's versioning rules](https://wayland.freedesktop.org/docs/book/Protocol.html#versioning) make the registry binding determine the global object's version; children inherit from their creator. The advertised maximum is not the version every client uses.
3. Guard the send in the compositor, using the generated event constant:

   ```cpp
   if (resource()->version() >= KDE_STEREO_DEPTH_V1_DEPTH_LIMITS_SINCE_VERSION) {
       send_depth_limits(sunk, popped);
   }
   ```

   Keep events the older client does know. Keep the existing values and change suppression for clients new enough to receive the event. Check initial replies, cached replies to late followers and later broadcasts.

The greeter investigation found KWin sending `depth_limits` (event 1, since 5) to depth objects created from a v3 manager binding. The old client only knew `depth_state` (event 0). Protocol traces identified the unsupported event; a debugger stopped at `wl_display_get_error` on the Qt Wayland error path. The owning send site is `StereoDepthSurfaceV1::sendState` in `src/wayland/stereocontent_v1.cpp`.

Audit the other events in each modified XML too. A generated send wrapper does not replace a resource-version check. A parent interface's enforced minimum can establish that an older event is safe; record that creation path instead of assuming it. `#ifdef ..._SINCE_VERSION` only checks what was available when compiling, so newer events still need the runtime check.

## Make the regression model the old client

Binding the current generated client at v3 is insufficient to reproduce every legacy failure: its `wl_interface` can still describe event 1. Use the event table the old client actually knew. For this protocol, the requests and event 0 are unchanged, so an integration test can copy the current `wl_interface`, set its version to 3 and its `event_count` to 1, then pass that descriptor to `wl_proxy_marshal_flags` when creating the depth object. Keep the descriptor alive until its proxy is destroyed. For a protocol whose signatures changed, generate a separate fixture from the old XML instead.

Run the same rows before and after the server change:

- Bind v3, and v4 immediately below the event's version. Receive the initial depth state, then another state update, and complete a display sync with `wl_display_get_error() == 0`. No depth-limits event may arrive.
- Bind v5. Verify the initial limits and changed limits numerically, and verify that repeating identical values sends no duplicate.
- Follow the same surface simultaneously with a v5 resource and an older resource. The older binding must not suppress the v5 follower's limits.

In the configured KWin integration-test container, build `testStereoDepthExchange` and run `bin/testStereoDepthExchange testResourceVersion` under the test session bus. Keep the failing old-server log. The full depth exchange suite checks the window, output and inert-surface behavior alongside this version test.

Connection survival is protocol proof. The real greeter's lock, idle CPU, unlock and wallpaper depth are separate checks; run them with depth enabled and disabled when fixing a greeter incident.
