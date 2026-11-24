# Explicit sync on Xwayland's surfaces, ours included

What a compositor demands once an X11 program presents with explicit sync, where Xwayland 24.1.15 keeps that promise and where it did not, and how to drive each path in the rig.
Written on 2026-11-24 (queue row 862), when the compositor closed Xwayland on a desktop with `wp_linux_drm_syncobj_surface_v1#39: error 4: explicit sync is used, but no acquire point is set`, and every X11 program closed with it.

## The rule

`linux-drm-syncobj-v1` (staging): once a client has made a `wp_linux_drm_syncobj_surface_v1` for a `wl_surface`, every commit of that surface that attaches a buffer must carry an acquire point and a release point, or the compositor raises `no_acquire_point` (4) or `no_release_point` (5) and the client is disconnected.
KWin checks it in `LinuxDrmSyncObjSurfaceV1::maybeEmitProtocolErrors()`: a pending non-null buffer and no acquire timeline is error 4.
For Xwayland that disconnection is the end of every X11 program of the session.

## Who presents with explicit sync on an X11 window

- Mesa's Vulkan X11 swapchain, whenever Xwayland offers `PresentCapabilitySyncobj` (DRI3 1.4 and Present 1.4) and the driver supports it: `xcb_present_pixmap_synced` with timeline points (`wsi_common_x11.c`, Mesa 26.1.6).
  Xwayland offers it when the compositor advertises `wp_linux_drm_syncobj_manager_v1` and its render node has syncobj timelines.
- Not Mesa's OpenGL on X11: `loader_dri3_helper.c` presents without sync objects (Mesa 26.1.6, and the edition's patches add none).
- So on an AMD or Intel desktop it is a Vulkan program (a game through DXVK or VKD3D, a Vulkan toolkit, OpenGL on zink); on NVIDIA's own driver the GL path too.

## Where Xwayland keeps `surface_sync` consistent (24.1.15)

`xwl_window->surface_sync` is made at the first synced flip (`xwl_glamor_dri3_syncobj_passthrough()`) and must be destroyed before any commit that cannot set points:

1. A synced flip: both points set (`xwayland-present.c`, `xwl_present_flip()`).
2. An implicit flip: `surface_sync` destroyed before the attach (same function).
3. The window-buffers path (X11 drawing, a copied present, damage on the window): `xwl_window_swap_pixmap()` sets points through `xwl_glamor_gbm_set_syncpts()` when glamor lacks implicit sync, else destroys `surface_sync`, but only on its main path.
   Xwayland counts every EGL vendor but NVIDIA's as implicit sync (`xwl_gbm->implicit_sync = !strstr(egl_vendor, "NVIDIA")`, `xwayland-glamor-gbm.c`): on NVIDIA's driver this path sets points itself, on Mesa's drivers (radeonsi, iris, NVK) it relies on destroying `surface_sync`.
   Its two early returns (the window's pixmap is still the client's flipped pixmap, or no window buffer could be made) call `xwl_window_handle_pixmap_sync()` and ignore its result, so on Mesa's drivers `surface_sync` stays there, and the next attach of the client's pixmap would carry no acquire point.
   Upstream's open merge request !2399 (Thomas H.P. Andersen, "xwayland: drop surface sync on implicit sync fallback", 2026-11-20, found with Mesa's NVK under Mutter when a game recreated its swapchain or resized its window) makes `xwl_window_handle_pixmap_sync()` itself destroy `surface_sync` when it falls back to implicit sync, so every caller gets it.
   It applies to the edition's 24.1.15 with its 14 patches (offset 12 lines).
   The edition does not carry it yet: the row-862 rig did not reproduce the error (below), so there is no red to turn green.

The edition's 14 patches add no attach, no commit and no `surface_sync` handling of their own; they change which windows get surfaces (redirected children) and which pixmaps may flip (a stereo window's pixmap of both eyes, patch 0005), and they make X11 drawing over a flipped stereo window ordinary (the 2D cover of 0013 and 0014), so a stereo window reaches the early returns above more often than a plain one.

## What the row-862 rig tried, and what it did not

The client is [`x11-synced-present.c`](../../stereo-proof-rig/scripts/xwayland-death/x11-synced-present.c) (DRI3 1.4 `PixmapFromBuffer` of a GBM buffer, two imported timeline syncobjs, `PresentPixmapSynced` with the acquire point signalled from the CPU, then one other path), run by [`synced-present-session.sh`](../../stereo-proof-rig/scripts/xwayland-death/synced-present-session.sh).
One fresh KWin 6.7.4 session on a virtual output per case, Xwayland's Wayland connection traced with `WAYLAND_DEBUG=client` in KWin's environment (Xwayland inherits it), the edition's Xwayland 24.1.15 +stereo3d3 and, as the control, Debian testing's Xwayland 24.1.15-1 mounted over it.

"Whole" means the X connection stayed whole and Xwayland's log in KWin's has no `explicit sync is used, but no acquire point is set`.

| Case | NVIDIA (RTX 3060, its own GBM) | AMD (radeonsi, one run each) |
| --- | --- | --- |
| six synced flips | whole; points on every commit | (not run alone) |
| synced flips, then X11 drawing on the window | whole | whole: Present re-allocated the window's pixmap, the main path destroyed `surface_sync`, then a new window buffer was attached |
| synced flips, then a copied present (an offset) | whole | whole |
| synced flips, then a resize | whole | whole |
| synced flips, then an unsynced present of another pixmap | whole | whole |
| vkcube (Mesa's X11 swapchain with explicit sync), resized to 640x480 and 300x200 (swapchain recreated twice) | whole (about 400 acquire points) | whole (392 acquire points) |
| a window declared full side by side, version 4, synced flips of pixmaps twice its width (patch 0005), then drawing; then a copied present | whole, flipped | whole, flipped |
| the same on a child window listed in `_KDE_NET_WM_STEREO_CONTENT_CHILDREN` | not reached: KWin did not redirect a child declared by hand, so no child surface was made and every present was copied | not run |
| Debian's Xwayland (control): drawing after flips; vkcube resized | whole | vkcube resized: whole |

Not tried: a redirected child with a surface of its own presenting with sync (a child declared through Mesa's GLX or the Vulkan stereo layer), a covered declared child, a GPU under load, a game through DXVK or VKD3D, NVK.
The station's own death (Xwayland 24.1.15 +stereo3d3 on radeonsi, Discord among the X11 programs, two lanes' containers busy) stays unexplained by these rows.

## Traps

- **Symptom:** a count of `set_acquire_point` lines in the trace says 0 while the program flips with sync. **Cause:** libwayland's debug lines name an object as `interface#id`, not `interface@id`. **Fix:** match `wp_linux_drm_syncobj_surface_v1#[0-9]+\.set_acquire_point`.
- **Symptom:** `gbm_bo_create` fails on NVIDIA's GBM with `GBM_BO_USE_LINEAR | GBM_BO_USE_RENDERING`. **Fix:** fall back to `GBM_BO_USE_RENDERING` (the driver's own layout; the buffer cannot be mapped to write its contents, which a sync test does not need).
- **Symptom:** `xdotool search --name vkcube` finds nothing. **Cause:** vkcube's X11 window is called "Vkcube X11". **Fix:** read the id from `xwininfo -root -tree`.
