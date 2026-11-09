# A canvas, video or image with `image-rendering: pixelated` in the stereo browser (Wayland native compositor)

Symptom first: a page whose canvas has CSS `image-rendering: pixelated` (CesiumJS sets it) shows black in the browser on Stereo KWin, in plain 2D too, while the page's own `readPixels` shows the picture; a `<video>` with the style is solid green (Y, U and V read as zero); a 2D-context canvas with the style is blurry, not nearest-neighbour.
It appears with `gfx.webrender.compositor` on (the edition's default) on Wayland; it is in Firefox's code (stock Waterfox 6.7.5 with that pref shows it too), and every edition build up to +stereo3d12 has it.

## The cause, with the code path

1. `nsHTMLCanvasFrame` pushes the canvas to WebRender with `wr::ToImageRendering(UsedImageRendering())`, so `Pixelated` reaches `tile_cache/mod.rs`.
2. A WebGL canvas is an external DMABuf image that is promoted to a compositor surface. The external image is attached to the native surface only when `image_rendering == Auto` (`setup_compositor_surfaces`). With `Pixelated` WebRender made a surface of its own and drew the image into it.
3. For that draw `compute_external_surface_dependencies` called `resolve_image(..., is_composited = true)` for every surface, so `wr_renderer_lock_external_image` took the Wayland branch added by Mozilla's Bug 1959975, `Lock(channel, nullptr)`: no GL context, texture 0. The surface is filled from texture 0: black for RGB, green for YUV (the same lock that was the green video of ORDER 471).
4. Past that, Wayland has no request for a sampling filter: `NativeLayerWayland::SetSamplingFilter` only stores it, so a surface the compositor scales is scaled with the compositor's own filter, never nearest.

## The fix (Sparky-OS/waterfox branch order482)

- `compute_external_surface_dependencies` resolves for direct compositing only when the surface has an external image attached.
- `CompositorCapabilities::supports_sampling_filter`, false for the Wayland native compositor (`RenderCompositorNative::GetCompositorCapabilities`): a pixelated image that is scaled on its way to the screen is not promoted (`SamplingFilterUnsupported`), so WebRender draws it in the tiles with `GL_NEAREST`. Unscaled, it is still promoted.

## Recipe: prove it

1. A page with an 8x8 canvas of four 4x4 colour quadrants (red, green / blue, yellow) shown at 256x256, `image-rendering: pixelated` on or off, for a 2D, a WebGL and a three.js canvas, plus a video.
2. Read the page's own pixels (`readPixels`, `getImageData`), capture the compositor output (ScreenShot2), and measure the canvas rectangle: quadrant centres, the mean, and the distinct colours on a row across the red and green seam (nearest gives 2, linear gives about 30).
3. Run unfixed and fixed, the AMD route and the RTX route, plus the camera hack with a declared canvas (`set_content(3)`), and CesiumJS as it ships.
4. Count the wl_buffers (`WAYLAND_DEBUG=1`): `create_immed` (dmabuf) against `wl_shm_pool.create_buffer`; the fixed build must keep the dmabuf path for a canvas and a video without the style.

## Traps

- Symptom: a dev build starts and Marionette answers, but the page is not found (`window.__x is not a function`, or `Couldn't load XPCOM`). Cause: `dist/bin` is symlinks into the source and object trees; a container that mounts only `dist/bin` loses them. Fix: mount the object folder and the source tree read-only at their own paths and set `LD_LIBRARY_PATH` to `dist/bin`. Found by `Missing chrome or resource URL` in the log.
- Symptom: `mach build` says "Your build was successful" in 30 s and the Rust change is not in the binary. Cause: not found; the file had been edited while the first full build was still running, so the crate was already compiled when the edit landed and the later incremental build did not see it as newer. Fix: `touch` the file and run `mach build -v`, and look for the `Compiling webrender` line before trusting the binary.
- Symptom: Marionette `execute_script` cannot see `window.myFunction` of a module page. Cause: the content sandbox is Xray-wrapped. Fix: the page copies its values into `document.documentElement.dataset` and the test reads those.
- A pass is not "not black": measure nearest-neighbour (the seam colours), not only the mean.
- `--kiosk` needs the whole chrome (nimbus, urlbar) to load; a dev build with missing resources hangs in `WebDriver:NewSession`.
