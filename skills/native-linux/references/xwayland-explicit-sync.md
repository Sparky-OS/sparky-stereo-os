# Explicit sync on Xwayland's surfaces, ours included

What a compositor demands once an X11 program presents with explicit sync, where Xwayland 24.1.15 kept that promise and where it did not, the sequence that broke it, and how to drive each path in the rig.
Written on 2026-11-24 (queue rows 862 and 865), when the compositor closed Xwayland on a desktop with `wp_linux_drm_syncobj_surface_v1#39: error 4: explicit sync is used, but no acquire point is set`, and every X11 program closed with it.

## The rule

`linux-drm-syncobj-v1` (staging): once a client has made a `wp_linux_drm_syncobj_surface_v1` for a `wl_surface`, every commit of that surface that attaches a buffer must carry an acquire point and a release point, or the compositor raises `no_acquire_point` (4) or `no_release_point` (5) and the client is disconnected.
KWin checks it in `LinuxDrmSyncObjSurfaceV1::maybeEmitProtocolErrors()` (`src/wayland/linux_drm_syncobj_v1.cpp`): a committed non-null buffer and no acquire timeline is error 4.
For Xwayland that disconnection is the end of every X11 program of the session.

## Who presents with explicit sync on an X11 window

- Mesa's Vulkan X11 swapchain, whenever Xwayland offers `PresentCapabilitySyncobj` (DRI3 1.4 and Present 1.4) and the driver supports it: `xcb_present_pixmap_synced` with timeline points (`wsi_common_x11.c`, Mesa 26.1.6).
  Xwayland offers it when the compositor advertises `wp_linux_drm_syncobj_manager_v1` and its render node has syncobj timelines.
- Not Mesa's OpenGL on X11: `loader_dri3_helper.c` presents without sync objects (Mesa 26.1.6, and the edition's patches add none).
- So on an AMD or Intel desktop it is a Vulkan program (a game through DXVK or VKD3D, a Vulkan toolkit, a browser whose ANGLE runs on Vulkan, OpenGL on zink); on NVIDIA's own driver the GL path too.

## Where Xwayland keeps `surface_sync` consistent (24.1.15)

`xwl_window->surface_sync` is made at the first synced flip (`xwl_glamor_dri3_syncobj_passthrough()`) and must be destroyed before any commit that cannot set points.
Every buffer Xwayland attaches to a window's surface goes through one of two functions:

1. `xwl_present_flip()` (`xwayland-present.c`): a synced flip sets both points; an implicit flip destroys `surface_sync` before the attach.
2. `xwl_window_attach_buffer()` → `xwl_window_swap_pixmap(xwl_window, TRUE)` (`xwayland-window.c`, `xwayland-window-buffers.c`): X11 drawing, a copied present, damage on the window.
   `xwl_window_handle_pixmap_sync()` sets points through `xwl_glamor_gbm_set_syncpts()` when glamor lacks implicit sync, else the caller destroys `surface_sync`, but in 24.1.15 only on its main path.
   Xwayland counts every EGL vendor but NVIDIA's as implicit sync (`xwl_gbm->implicit_sync = !strstr(egl_vendor, "NVIDIA")`, `xwayland-glamor-gbm.c`): on NVIDIA's driver this path sets points itself, on Mesa's drivers (radeonsi, iris, NVK, zink) it relies on destroying `surface_sync`.
   Its two early returns (the window's pixmap is still the client's flipped pixmap, or no window buffer could be made) ignore the result of `xwl_window_handle_pixmap_sync()`, so on Mesa's drivers `surface_sync` stays and the client's own buffer is attached with no acquire point.

Upstream's merge request !2399 (Thomas H.P. Andersen, "xwayland: drop surface sync on implicit sync fallback", commit `cbd97d97a289`, reviewed by Olivier Fourdan and Michel Dänzer, open on 2026-11-24) moves the destroy into `xwl_window_handle_pixmap_sync()` itself, so every caller gets it.
After it, every attach is preceded by both points or by the destroy, on every path above; the cursor surface never has a `surface_sync`.
The edition carries it unchanged as patch 0015 of Xwayland `2:24.1.15-1+stereo3d4` (queue row 865).

The edition's 14 patches add no attach, no commit and no `surface_sync` handling of their own: they give more windows a surface of their own (children a client redirects, 0001 to 0003, 0006, 0008), let a stereo window flip a pixmap of both eyes (0005), and set window pixmaps of their own making (0013's double-width copy, 0014's restored pair), which are the server's pixmaps and take the main path.
They add surfaces and flips that can reach the early returns, but no path of their own; Debian's Xwayland without them gives the same error 4 (below).

## The sequence that gives error 4 (found in row 865)

The early returns need `xwl_window_post_damage()` to meet a window whose surface window's pixmap is still the client's flipped pixmap.
A flip itself takes the window off the damage list, and later drawing on the window goes through `damage_report()`, which swaps the client's pixmap out first.
What does not: `xwl_window_update_surface_window()`, which every clip change of the window tree calls (`xwl_clip_notify()`), moves the surface from one window to another and carries the queued damage without a report.

1. A toplevel T whose child C covers it exactly and has its own pixmap (C has another visual: a 24-bit child of a 32-bit ARGB toplevel is redirected by the server, `compImplicitRedirect()`), so Xwayland makes C the surface window and C's presents flip.
   Chromium 156 on X11 does not have it: with OpenGL it draws into its 32-bit toplevel, with Vulkan into a child over the whole toplevel with the same 32-bit visual, which shares the toplevel's pixmap, so its surface never moves (measured, both whole on radeonsi).
2. C flips with explicit sync: `surface_sync` exists, C's pixmap is the client's.
3. Something stacks above C for a moment (a sibling raised, mapped), so the walk down the first children stops and T is the surface window; T gets damage (the sibling is painted), the window joins the damage list.
4. Before Xwayland's block handler posts that damage, C is first again (the sibling lowered): C is the surface window with the client's pixmap, and nothing reported damage on it.
5. The block handler posts: `xwl_window_swap_pixmap()` takes an early return and attaches the client's buffer with no point while `surface_sync` stays: error 4 on radeonsi.

On NVIDIA's own driver step 5 sets points from Xwayland's own timeline, so the same sequence stays whole.
Without step 4 inside the same dispatch (the damage posted while T is the surface window), the main path destroys `surface_sync` first and nothing happens.

## Recipe

The rig scripts are in [`scripts/xwayland-death`](../../stereo-proof-rig/scripts/xwayland-death/) of the proof-rig skill:

```sh
gcc -O2 -Wall -o x11-surface-switch x11-surface-switch.c $(pkg-config --cflags --libs xcb xcb-dri3 xcb-present gbm libdrm)
# one fresh container per case, the render node of the card passed in, then:
bash traced-xwayland-session.sh OUT 20 ./x11-surface-switch 6 switch     # the sequence above, red on the published Xwayland
bash traced-xwayland-session.sh OUT 20 ./x11-surface-switch 6 split      # the same with the damage posted in between: whole
python3 explicit-sync-verdict.py OUT                                     # whole or red, and the last requests on the surface
```

- Red on Xwayland `2:24.1.15-1+stereo3d3+lc1` with radeonsi: the client prints `X connection broken (error 1)`, KWin's log `XWAYLAND: wp_linux_drm_syncobj_surface_v1#37: error 4: explicit sync is used, but no acquire point is set`, and the trace ends with synced flips (`set_acquire_point`, then `attach`) followed by `wl_surface#17.attach(wl_buffer#35, 0, 0)` with no point before it.
- Green on `+stereo3d4`: `wp_linux_drm_syncobj_surface_v1#37.destroy()` right before that attach, the connection whole.
- A managed window (no override-redirect) gives the same: KWin on Wayland puts no frame window around an X11 window.
- `x11-program-actions.sh vkcube|chromium-gl|chromium-vulkan` drives a real program through resize, minimize, restore and a covering window in the same session.

## Cases measured

"Whole" means the X connection stayed whole and KWin's log has no error 4; the counts are acquire points in the trace.

| Case | NVIDIA (RTX 3060, its own driver) | AMD (radeonsi, one run each) |
| --- | --- | --- |
| synced flips, then X11 drawing, a copied present, a resize, or an unsynced present (row 862) | whole | whole |
| vkcube, swapchain recreated by two resizes (row 862) | whole | whole |
| a window declared full side by side, version 4, double-width synced flips, then drawing and a copied present (row 862) | whole | whole |
| the surface switch above, override-redirect or managed (row 865) | whole, 3 of 3 each: points from Xwayland's own timeline | **red**, error 4, on `+stereo3d3`; whole on `+stereo3d4` |
| the same with the damage posted between the restacks | whole | whole |
| the surface switch, published source with `XWAYLAND_TEST_IMPLICIT_SYNC` (below) | red 20 of 20; whole 20 of 20 with 0015 | |
| the same with a second Vulkan client drawing at full speed on the card (test switch) | red 3 of 3; whole 3 of 3 with 0015 | not run: no load on the card that drives the screens |
| a child through the Vulkan stereo layer, covered, painted and uncovered while it presents ([`vk-x11-covered.c`](../scripts/vk-x11-covered.c)) | whole, 3 of 3 | whole (81 points) |
| the same child never covered | whole, 3 of 3 | whole (120 points) |
| a quad buffer GLX child ([`glx-child-first-pair.c`](../scripts/glx-child-first-pair.c)) | whole, 3 of 3, no points (GL presents without sync) | whole, no points |
| vkcube resized three times, minimized, restored, covered by another X11 window, resized again | whole, 3 of 3 | whole (890 points, the swapchain recreated) |
| Chromium 156 on X11, OpenGL (its default) and Vulkan, the same actions | whole, 3 of 3 each | whole (Vulkan: 15 points, 6 sync objects made and dropped) |
| Debian's Xwayland 2:24.1.15-1 (control, row 862): drawing after flips; vkcube resized | whole | vkcube resized: whole |
| Debian's Xwayland 2:24.1.15-1, none of the edition's patches: the surface switch (row 865) | | **red**, error 4: the fault is upstream's |

Not reachable in the rig: NVK (the RTX 3060 runs NVIDIA's kernel driver), a Windows game through DXVK or VKD3D (no Wine in the rig image; DXVK presents through the same Vulkan X11 swapchain as vkcube).

## A loop on a card where the fault cannot show

NVIDIA's own driver never reaches the fault, and the AMD card that drives the person's screens takes single runs only.
Two routes were tried for loops:

- Xwayland's glamor on zink over the NVIDIA card (`__EGL_VENDOR_LIBRARY_FILENAMES` Mesa first, `MESA_LOADER_DRIVER_OVERRIDE=zink`, `GBM_BACKEND=dri`): fails, see the traps.
- What works: a test-only build of the same source with one switch, `if (getenv("XWAYLAND_TEST_IMPLICIT_SYNC")) xwl_gbm->implicit_sync = TRUE;` after the vendor test in `xwl_glamor_gbm_init_egl()`, built twice (the published patches, then with 0015 added; only `xwayland-window-buffers.c` recompiles), bind-mounted over `/usr/bin/Xwayland` and run with the switch in KWin's environment.
  Without the switch it behaves as the published binary does on NVIDIA (whole); with it the published source is red 20 of 20 and the successor whole 20 of 20.
  The switch is a test instrument and never goes into a package.

## Traps

- **Symptom:** a count of `set_acquire_point` lines in the trace says 0 while the program flips with sync. **Cause:** libwayland's debug lines name an object as `interface#id`, not `interface@id`. **Fix:** match `wp_linux_drm_syncobj_surface_v1#[0-9]+\.set_acquire_point`.
- **Symptom:** `gbm_bo_create` fails on NVIDIA's GBM with `GBM_BO_USE_LINEAR | GBM_BO_USE_RENDERING`. **Fix:** fall back to `GBM_BO_USE_RENDERING` (the driver's own layout; the buffer cannot be mapped to write its contents, which a sync test does not need).
- **Symptom:** `xdotool search --name vkcube` finds nothing. **Cause:** vkcube's X11 window is called "Vkcube X11". **Fix:** read the id from `xwininfo -root -tree`.
- **Symptom:** a 24-bit child of a 32-bit window is never created (`X error 8` on `CreateWindow`, then `BadWindow` on its map). **Cause:** border and colormap default to the parent's, which another depth cannot take. **Fix:** give the child `XCB_CW_BORDER_PIXEL` and the screen's default colormap.
- **Symptom:** the child's presents complete as copies, never flips, although it covers its toplevel. **Cause:** Xwayland chose the surface window when the toplevel was realized, before composite gave the child its pixmap, and nothing chooses again until the next clip change. **How found:** the attached buffers in the trace were the toplevel's ARGB format (`875713089`) and the client's XRGB buffers (`875713112`) were wrapped at the flip check but never attached. **Fix:** one restack (a sibling raised, then lowered) after mapping.
- **Symptom:** after a sibling is unmapped or destroyed, the surface stays on the toplevel. **Cause:** `xwl_window_update_surface_window()` walks only `firstChild`, and the clip notify of an unmap or destroy runs while the sibling is still first in the stack. **Fix:** lower the sibling below the child instead.
- **Symptom:** Xwayland with its glamor on zink hangs at start, no X client is served. **Cause:** a library zink loads on NVIDIA opens an X connection, and KWin's `DISPLAY` names Xwayland's own display, which cannot answer yet. **How found:** `strace -f` through a wrapper: `connect(... "/tmp/.X11-unix/X0")` and a `poll` with no timeout. **Fix:** unset `DISPLAY` in the wrapper; it then fails with `ZINK: failed to choose pdev` and glamor falls back to llvmpipe ("Refusing to try glamor on llvmpipe"), so zink is no route for this loop.
- **Symptom:** a run with `/bin/true` as the client shows nothing from Xwayland. **Cause:** KWin starts Xwayland on the first X connection. **Fix:** run a client that connects (`xdpyinfo`).
- **Symptom:** a binary given in the environment is not the one KWin runs. **Cause:** KWin starts `Xwayland` from `PATH`. **Fix:** bind-mount the binary over `/usr/bin/Xwayland`, and record its hash in the session folder.
