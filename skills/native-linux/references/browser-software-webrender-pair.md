# The browser's two views when its own compositor runs in software

Symptom first: in the stereo browser, a WebGL page (the camera hack) or a WebXR page in the flat display shows both views squeezed side by side in the canvas's place, the same picture in each eye, with nothing said.
It happens where the browser draws without the graphics card: a computer or virtual machine without usable 3D, a driver the browser blocks, or `gfx.webrender.software` set.
`windowUtils.layerManagerType` then reads `WebRender (Software)`.

## The trap: whose compositor is "software"

"Software compositor" here is the browser's own: software WebRender (SWGL).
It is not Stereo KWin, which composes in software and keeps every declared pair.
Reading it as KWin's leads to the wrong answer, turning 3D off in the browser and telling the person it cannot work (ORDER 546 milestone 2 did that; ORDER 616 replaced it).
A piece without stereo is work to build: find where the declaration is lost and carry it.

## Where the pair stopped being declared (Waterfox 6.7.5, browser +stereo3d14)

1. The browser still uses its native Wayland compositor under software WebRender: `RenderCompositor::Create` picks `RenderCompositorNativeSWGL` when `gfxVars::UseWebRenderCompositor()` is true (`gfx/webrender_bindings/RenderCompositor.cpp`; Mozilla bug 1711224 added it for Wayland), and the edition forces that feature on (`gfx.webrender.compositor.force-enabled`). So the canvas still gets a subsurface of its own, filled through shared memory (`wl_shm`) instead of a DMABuf. The `WAYLAND_DEBUG` log shows it: a `wl_shm_pool.create_buffer` of the pair's size (1600x450 for an 800x450 canvas, 3840x1080 for the flat WebXR layer) attached hundreds of times to one subsurface, and no `kde_stereo_content`.
2. The mark was what got lost. `TexTypeForWebgl` (`gfx/layers/CanvasRenderer.cpp`) answers `Unknown` when `UsingSoftwareWebRender()`, so WebGL swaps through `SurfaceFactory_Basic`. The edition's `SetStereoMode` (`dom/canvas/WebGLContext.cpp`) wrote the pair's mark only into a DMABuf front buffer, so with a Basic buffer it did nothing.
3. `WebGLContext::PushRemoteTexture` reads a Basic front buffer back into a `BufferTextureData`; the compositor side makes a `BufferTextureHost` from it, whose RGB branch of `PushResourceUpdates` built the image descriptor with `stereo` 0.
4. WebRender gives a compositor surface it draws an image into the image descriptor's mark (`tile_cache/mod.rs`, `set_compositor_surface_stereo`, then `SwCompositor`, `RenderCompositorNative::SetSurfaceStereo`, `NativeLayerWaylandRender::SetStereoMark`, `DeclareStereoLocked`). With 0 the layer was never declared, and KWin showed the whole 1600-wide buffer in the 800-wide place.

Video was never affected: a YCbCr buffer's descriptor already carried its mark.

## The fix (Sparky-OS/waterfox branch order616, browser +stereo3d15)

- `SetStereoMode` returns the pair's mark for any front buffer (0 for one picture) and still writes it into a DMABuf.
- `Present` hands it to `PushRemoteTexture`, whose readback branch passes it to `RemoteTextureOwnerClient::PushTexture`, which calls `TextureHost::SetStereoMark` on the new host.
- `BufferTextureHost` keeps it and puts it in the RGB image descriptor (`descriptor.stereo`).
- Nothing else changes for a canvas with a surface of its own: the existing native layer code declares the shared memory surface full side by side, left eye first, exactly as it does a GPU route's RGB layer, and a 2D canvas keeps mark 0.
- A canvas WebRender does not give a surface of its own (a rounded clip, an opacity) is drawn into the page's tiles once per eye, as on the GPU route. Under software WebRender a buffer image is sampled as a rectangle texture (`WR_FEATURE_TEXTURE_RECT`), and `brush_image.glsl` started that texture's bounds at its origin instead of at the eye's part (`min_uv`), so the right eye showed only the canvas's background. The bounds now start at `min_uv` for both kinds of texture; a whole image (`min_uv` 0) is drawn as before. Mozilla's current tree has replaced `brush_image.glsl` with the quad shaders, so there was nothing upstream to carry.

## Recipe: prove it

Each case in a fresh container and session (the rig of [stereo-two-cameras, webgl-control-on-a-gpu-and-without.md](../../stereo-two-cameras/references/webgl-control-on-a-gpu-and-without.md): Stereo KWin `--virtual` with `KWIN_VIRTUAL_STEREO_MODES=1`, its output in its 3D twin, the browser under Marionette in `--kiosk`).

1. **Pages a script can measure.** A WebGL page whose camera is an ordinary perspective projection (vertical angle 0.7854 rad, near 0.1) with four unlit squares in colours nothing else on the page has, at 2, 5, 12 and 30 m; a WebXR page with the same squares drawn with the session's views (`local` space), recording every frame's views; the same WebGL page inside a wrapper with `border-radius` and `overflow: hidden` (WebRender then draws the canvas into the page's tiles instead of a surface of its own); a 2D page; and the WebGL page with `webgl.stereo-camera.enabled` false.
2. **Four routes.** The card given with `gfx.webrender.software` true (the browser's compositor in software, KWin on the card); the card given to KWin and only the browser on Mesa's software renderer (`LIBGL_ALWAYS_SOFTWARE=1` in the browser's environment: it blocklists itself, `FEATURE_FAILURE_SOFTWARE_GL`, as in a virtual machine without 3D, and KWin can still capture); no device at all (KWin falls back to QPainter, "Configured compositor not supported by Platform", and ScreenShot2 answers `Screenshot got cancelled`, so the Wayland log is the evidence there); and the card with the browser on the GPU (the route that must not change). Run them on two cards (NVIDIA through CDI, AMD's render node).
3. **Read the Wayland log** (`WAYLAND_DEBUG=client`): which `wl_buffer` (`wl_shm_pool.create_buffer` or `zwp_linux_buffer_params_v1.create_immed`, with its size) each `wl_surface` was given, and `get_stereo_content` with `set_content(3)` on which surface. Under software WebRender the canvas's subsurface takes `wl_shm` buffers of the pair's size; it must be the one declared.
4. **Where no capture is possible** (no device at all), count per surface what the log shows: the canvas's subsurface declared once, with the pair's shared memory buffers attached; the pixels come from the browser-on-llvmpipe route of step 2, which runs the same browser code.
5. **Measure the captures.** Per eye and colour, the runs of that colour: one run per eye is a view; two runs of half the width in one eye are an undeclared pair squeezed into one place. The disparity is the left run's centroid minus the right one's; the vertical offset must be 0; the pixels outside the canvas must not differ between the eyes.
6. **Predict.** The camera hack's right eye is the page's camera moved by the whole separation: disparity `s W (C / Z - 1)` in canvas pixels, `s` and `C` from the `WebGLStereo` log lines (`separation`, `in use`). WebXR's from the recorded views and viewports. The squares have hard edges, so predict the centroid of the pixels whose centre lies inside each projected square ([web3d-engines-in-the-browser.md](../../stereo-two-cameras/references/web3d-engines-in-the-browser.md), step 7); a continuous centroid leaves half-pixel errors.
7. **Red first:** the published build on the software routes (squeezed, undeclared), and the earlier answer that turned 3D off (one picture and a notice); then the fixed build. The 2D page and the stereo-off page: equal eyes, and equal to the published build's capture.

Measured on 2026-11-16 (Stereo KWin +stereo3d54, Mesa +stereo3d21, one fresh container per case; an 800x450 canvas, separation 0.0125 of its width and plane 2.8 m from the `WebGLStereo` log):

| route | +stereo3d14 | +stereo3d15 |
|---|---|---|
| card given, `gfx.webrender.software` (NVIDIA and AMD): page canvas, worker canvas, WebXR | no declaration; each square twice per eye, 21 px wide instead of 43; both eyes identical | one `set_content(3)` per surface, `wl_shm` 1600x450 (3840x1080 for WebXR); disparities 4.0, -4.5, -7.5, -9.0 px (WebXR 13.0, -0.5, -5.5, -8.5), all within 0.5 px of the prediction, vertical 0.0, 0 pixels differ outside the canvas |
| the same, canvas under a rounded clip (per-eye tiles) | squeezed, undeclared | tiles declared (`wl_shm` 2048x512), same disparities; with only the mark fixed the right eye showed the canvas's background |
| browser on llvmpipe, KWin on the AMD card | squeezed, undeclared | declared, same disparities |
| no device at all | no declaration, `wl_shm` 1600x450 attached about 3,400 times | declared once, the same buffers |
| GPU route, both cards; 2D page and stereo-off page in software | | 0 pixels differ from +stereo3d14 |

Inside the canvas the software route's picture equals the GPU route's (0 pixels; the rounded clip's corners 1 level on 134 pixels).

## Traps

- **Reading "software compositor" as KWin's.** Symptom: a fix that turns the browser's 3D off "because the compositor is in software". Cause: the browser's own compositor (software WebRender) was meant, while Stereo KWin keeps a pair in software too. Fix: measure which surface the pair reaches (step 3) before deciding; here it still had a surface of its own and lacked only its mark. Found by Daniel reading the notice patch.
- **The pair has its own surface and is still flat.** Symptom: the `WAYLAND_DEBUG` log shows a subsurface given hundreds of `wl_shm` buffers of the pair's size and no `kde_stereo_content`. Cause: the mark rides on a DMABuf only; a buffer read back for software WebRender carried none. Fix: carry the mark with the read-back buffer (the fix above). Found by counting buffers per surface, then following `SetStereoMode`, `TexTypeForWebgl` and `BufferTextureHost::PushResourceUpdates`.
- **ScreenShot2 is cancelled with no device at all.** Symptom: `GDBus.Error:org.kde.KWin.ScreenShot2.Error.Cancelled` on every try. Cause: without a render node KWin's virtual backend composites with QPainter (`kwin.log`: "Configured compositor not supported by Platform. Falling back to defaults"). Fix: give KWin a card and only the browser the software renderer (step 2), and keep the no-device run for the Wayland log.
- **The buffer recorder records nothing from this browser.** Symptom: `wlrec.so` preloaded, surfaces declared in the log, no dump and no `log.jsonl`. Cause: the browser reaches libwayland-client through its own `libmozwayland.so`, which the preloaded wrappers do not see. Fix: the llvmpipe-browser route of step 2.
- **The right eye of a canvas drawn into tiles shows only its background under software WebRender.** Symptom: the markers in the left eye only (one run per colour on the left, none on the right), the tiles declared (`shm 2048x512`), the GPU route right. Cause: `brush_image.glsl` bounds for a rectangle texture (above). Found by reading the right eye's colours (the canvas's own clear colour, not the page's: the image was drawn, from the wrong place) and following `v_uv`, `v_uv_bounds` and the clamp to `v_uv_sample_bounds`.
- **A hard-edged marker's centroid moves in half pixels.** Symptom: one marker off the prediction by 0.5 to 0.8 px while the others agree. Cause: the continuous projection was compared with a centroid of whole pixels. Fix: the pixel-centre rule (step 6).
- **The recipe's object folders on a first run.** Symptom: `dpkg-source: error: unpack target exists: source`, then `rm: cannot remove 'obj-x86_64-pc-linux-gnu/x86_64-unknown-linux-gnu': Device or resource busy` in `debian/rules clean`. Cause: Docker makes the mount points of `BROWSER_OBJ_DIR` and `BROWSER_RUST_DIR` before the container starts. Fix (recipe, ORDER 616): unpack beside the tree and move it in, and build with `-nc` when an object folder is mounted.
- **The compiler bundle is gone.** Symptom: no folder holding `.mozbuild` and `.rustup` for the recipe's third argument. Fix: rebuild it with the source's own `debian/fetch-toolchains.py` (pinned Mozilla archives, hash checked, then `verify-toolchains.py`) in a container that has `zstd` and `rustup`; about 2.3 GB.
- **A notice patch overlaid on a package.** Script and string patches can be tried without a build by replacing the files in `browser/omni.ja` (entries are stored), after checking that each file is byte-identical to the fork's commit; the packaged locale files differ from the source's, so only the source's own `en-US` hunk applies there.

## What was measured impossible

Nothing, on the routes measured: the card given with software WebRender forced (NVIDIA and AMD), no device at all, a page canvas, a canvas drawn from a worker, a canvas WebRender draws into the page's tiles (a rounded clip), and WebXR's flat display.
So the browser has no notice for this case: the pair is declared on every one of them.
Where the browser has no native compositor at all (an X11 session; a Wayland compositor without `wp_viewporter`), `gfxVars::StereoContentDeclaration()` is false, the camera hack never starts and WebXR's flat display is not offered, on the GPU route as well: that is the desktop lacking Stereo KWin, which the browser already says, not a software route.
Not measured: `webgl.out-of-process.async-present` set false (the canvas then reaches the compositor through a content-side snapshot that carries no mark); it is true by default and no setting of ours touches it.
