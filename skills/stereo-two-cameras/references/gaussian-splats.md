# Gaussian splats in stereo: what is view-dependent, what a second camera costs, the route to a declared pair

Started in ORDER 501, November 2026, from unchanged Spirula Studio master `b8e15cb8d7f8a2f45ca9b4fea3fa331181433caa`.
The reference now includes the built ORDER 501 pair, its independent pixel checks and the original monoscopic baseline.
The implementation is tested privately on the edition fork; it is not a package or an upstream acceptance claim.

## Working recipe

1. Pin the source and read its build and contribution rules.
   Spirula's `build_develop.bash -DSS_BACKEND=vulkan -DCMAKE_BUILD_TYPE=Release` builds a native application without CUDA or model weights.
   Capture the dev script's effective job count as well as its container's CPU quota.
   At this revision the default Linux link failed; see the duplicate-symbol trap below before spending a cold build on that configuration.
2. Follow the viewport to the screen instead of inferring the toolkit from the compute backend.
   Spirula's Dear ImGui GUI uses GLFW and OpenGL; Vulkan computes splats and returns RGB bytes for a GL texture.
3. Generate calibrated turntable frames of simple shapes, with no outside media, and retain the generator.
   Train or load them without fetching inference models, then capture the unchanged GUI under an isolated compositor on each driver.
4. Trace camera projection, directional colour, tile membership and compositing order.
   Recompute those per camera, sharing only camera-independent scene state.
5. Measure an additional unchanged-camera render request before implementing a pair.
   State whether the timing includes readback, transfer, image encoding and presentation; a serial-request measurement is not a stereo frame-rate result.
6. Make each native viewport its own declared pair below the flat interface.
   Read the compositor's live depth limits, predict disparities independently, then prove geometry, scale, lifecycle and the no-limits case in the implementation milestone.

## Source map

The paths below are relative to the pinned [Spirula Studio tree](https://github.com/harry7557558/spirula-studio/tree/b8e15cb8d7f8a2f45ca9b4fea3fa331181433caa).

| Owner | What matters for a pair |
| --- | --- |
| `src/app/gui/GuiMain.cpp`, `spirula_gui_main` | GLFW top level and the ImGui OpenGL presentation path |
| `src/app/gui/ViewportPanel.cpp`, `pump_engine`, `upload` | One pending render and one displayed texture; training updates use the same worker as loaded splats |
| `src/app/gui/PreviewRenderer.cpp`, `render` | Point and mesh preview GL FBO; its projected geometry and depth buffer are camera dependent |
| `src/app/webviewer/RenderWorker.cpp`, `render_once` | Camera conversion, one engine lock around camera/forward/blit/readback, shared by the GUI and HTTP viewer |
| `src/engine/EngineForward.cpp`, `forward_3dgs` | Projection and SH colour, camera-indexed tile intersection, rasterization, forward buffers and postprocessing |
| `src/backend/vulkan/kernels/IntersectTile.cpp` | Tile membership, depth keys and ordering depend on each view's projected footprints |
| `src/core/PoolSlots.h`, `src/core/Tensor.h` | Scratch aliases and high-water allocations make persistent two-eye results different from transient sequential renders |

## Share one world, keep two results

Share splat means, orientations, scales, opacity, colour coefficients, scene placement and the training update.
Projection transforms the covariance into screen space, so even parallel cameras with the same axial depths can have different footprints and tile membership.
Evaluate spherical harmonics and spherical-beta lobes from each camera's direction.
Keep the tile lists, projected splats, clipping, raster outputs, picking data and any screen-space postprocessing associated with their camera.
An identical axial depth order is not permission to reuse a tile's membership list.

The [3D Gaussian Splatting paper](https://arxiv.org/abs/2308.04079), section 4 equation 5 and section 6, gives the projected covariance and tile/depth sorting model.
The implementation's own approximation, banding and primitive variants must be audited separately.

The engine is a process-global singleton and each `forward_3dgs` replaces its forward state.
Hold a single scene revision across the pair and copy or consume the first result before the next forward overwrites it.
Two ordinary `submit` calls are insufficient: the worker has one replaceable pending request and one result slot.
The training loop must not update the scene between eyes.
`render_raw` retains `raw_rgb` and `raw_ts` capacities; the ordinary worker also reuses device upload/output buffers, and the viewport retains its last pose, step, pending ID and displayed texture.
Those capacities can be reused sequentially, but each camera's pixel contents and result identity must be preserved.
`PreviewRenderer::ensure_fbo` owns one colour/depth target, so points and meshes need the same first-result preservation even though their world VBOs can be shared.

## The route to the window

Vulkan compute does not imply Vulkan presentation.
In this application an image-layer count on a top-level Vulkan swapchain would not reach the actual GUI, and declaring the whole GUI would put flat controls in the wrong surface.
A native viewport adapter must expose a Wayland subsurface or X11 child, with the pair declared through the shared declaration library and a transparent viewport hole in the parent.
Keep flat overlays above that surface, coordinates logical, and the eye raster independent from the displayed rectangle.
The ordinary 2D viewport remains the comparison control.
At the pinned source, `GuiMain` clears with alpha 1 and does not request a transparent GLFW framebuffer; the implementation needs an alpha-capable parent and an accurate opaque region, with the canvas cleared before flat overlays are drawn.

## Traps, symptom first

- **Symptom:** a plan proposes a two-layer Vulkan swapchain for the whole application.
  **Cause:** the compute backend was mistaken for the window's rendering API.
  **Fix:** trace `GuiMain`, `ViewportPanel::upload` and ImGui's backend before selecting the native surface adapter.
  **How found:** CMake links `imgui_impl_opengl3.cpp`; `upload` calls `glTexImage2D`, and the frame is drawn by ImGui.
- **Symptom:** the second render shows a newer training step, or the first result is overwritten.
  **Cause:** the singleton forward buffers and worker's single pending/result slots are reused between requests.
  **Fix:** submit an atomic pair over one frozen scene revision, serializing forward passes and preserving each finished image.
  **How found:** `RenderWorker::submit` overwrites `pending`, and `forward_3dgs` replaces `engine().fwd`.
  The atomic implementation and its deliberately blocked trainer test now pass on both backends.
- **Symptom:** a build runs more compiler jobs than its CPU quota.
  **Cause:** a quota alone does not necessarily change `nproc`, which the upstream script uses.
  **Fix:** verify the printed job count; with GNU `nproc`, `OMP_NUM_THREADS=4` made this dev script report four CPUs and four jobs.
  **How found:** the actual build log's `CPU cores` and `Using jobs` lines.
- **Symptom:** Linux's final `spirula` link fails with multiple definitions of `gui::ProcessPipe`, `ProcessReader` and `ProcessDuplex` from `Subprocess.cpp` and `libss_inference_worker.a`.
  **Cause:** the file is built in the executable and the archive; the archive lacks the target's `-O3`, and GNU ld extracts that unoptimized member for a weak `std::string::append` reference from `FrameMaskSvg.cpp`, bringing the strong process definitions too.
  **Fix:** do not suppress duplicate-symbol errors or remove the file from just one target without checking its other consumers.
  A standard CMake Release configuration completed both unchanged dev builds; record that explicit configuration rather than claiming the empty-build-type Vulkan script passed.
  **How found:** the link map's archive-inclusion table names `std::string::append` as the trigger, and [upstream issue 339](https://github.com/harry7557558/spirula-studio/issues/339) reports the same Linux failure.
  The reported one-target removal in that issue explicitly leaves other targets broken, so it was not applied.

- **Symptom:** a supposed training timing is only milliseconds and produces cameras but no checkpoint.
  **Cause:** `SS_DUMP_CAMERAS` is a parse-and-exit diagnostic, before `session.setup_engine()`.
  **Fix:** keep its output as a separate parser check and unset it for the training measurement.
  **How found:** `src/app/cli/main.cpp` returns immediately after `dump_cameras_json`; the output file list was empty.
- **Symptom:** automation reports a ready viewer but its capture is black or remains on the welcome screen.
  **Cause:** readiness and screen-state fields do not prove GL pixels reached the compositor; on a measured NVIDIA/Linux Vulkan native Wayland case, opening a model triggered ImGui shader failures or a frozen prior frame.
  **Fix:** inspect actual compositor captures and retain the failure; compare the unchanged Xwayland path before attributing it to the renderer.
  **How found:** the native direct-open log repeated shader compile failures, a deferred-open capture stayed on welcome while state said viewer, and the same PLY rendered correctly through Xwayland.
  At the study checkpoint the native-path cause and source fix were unresolved; selecting only NVIDIA's EGL vendor did not remove the direct-open failure.
  The implementation checkpoint below records the later cause and fix.
  The CUDA backend displayed its trained PLY through native Wayland on the same driver, providing a narrower control.

## Measurements and limits

The initial fixture is twelve calibrated 192 by 144 frames of three spheres over a checkerboard floor, with 3,395 visible-surface seed points.
The baseline compositor capture is a 1280 by 900 monoscopic virtual output, with desktop depth disabled.
A 300-step Vulkan training run used 19.81 seconds / 278,960 KiB peak process RSS on a RADV integrated GPU, and 37.73 seconds / 561,160 KiB on an RTX 3060.
Reported tensor-pool high-water capacities were 4.97 and 4.98 MiB respectively; they are not whole-driver allocation or total machine usage.
CUDA on the same RTX 3060 took 0.76 seconds / 326,136 KiB peak RSS with a reported 5.00 MiB tensor pool.
These are small profiled cold starts with shader initialization/checkpoint writing; Vulkan overlapped compiler activity while CUDA ran after the main builds, so they are not a controlled API comparison or a GPU ranking.

At 400 by 300 pixels, ordinary HTTP requests after five warmup rounds and 25 measured rounds gave:

| Backend/device | One camera median | Two sequential cameras median | Ratio |
| --- | ---: | ---: | ---: |
| RADV integrated | 9.684 ms | 20.073 ms | 2.073 |
| Vulkan RTX 3060 | 4.176 ms | 8.376 ms | 2.006 |
| CUDA RTX 3060 | 1.598 ms | 3.098 ms | 1.939 |

The timings include HTTP, render, readback and JPEG encoding.
They measure two separate ordinary views, not atomic stereo presentation or a simultaneous two-eye memory high-water mark.
The input and camera count are small; larger splat counts, overlap and lens variants need fresh measurements in the implementation milestone.
No stereo image or second-eye geometry is claimed here.


## Implementation checkpoint: native pair transport

ORDER 501's implementation work uses the same RenderWorker for CUDA and Vulkan.
Its atomic request holds one engine mutex over both forward passes and copies the left RGB result before the singleton forward storage is reused.
The regression compares each packed half against an independent camera render and places a waiting trainer between the two render callbacks.
The GPU regression passes on RADV Vulkan, NVIDIA Vulkan and NVIDIA CUDA.
The rebuilt application also displays its trained PLY on NVIDIA native Wayland with the actual source context-restoration helper and no preload.
CUDA parity has zero tolerance violations and byte-identical reference blits after the affine shader change.
Both Vulkan GPUs pass the same accepted parity gate as the monoscopic baseline.

The native adapter was built separately against GLFW 3.4 and libstereo-declare 1.10.
A synchronized Wayland subsurface is below the alpha-capable parent, has an empty input region, and carries one XRGB8888 full side-by-side SHM buffer.
The viewport destination is independent of the eye raster; the compositor performs the resize.
Released SHM buffers may be reused; busy buffers are retained until release, with a bounded allocation count.
The Xwayland child uses the declaration library's child membership, one-view size and below-parent placement.
A transport harness with distinct patterns per eye was captured on RADV and NVIDIA through native Wayland and Xwayland.
These patterns prove eye transport and flat-parent composition, not 3D scene geometry or pair cost.

- **Symptom:** opening a Vulkan-backed model on NVIDIA native Wayland leaves a black or frozen UI and repeated ImGui shader failures.
  **Cause:** on driver 615.71.09, destroying a Vulkan probe instance clears the calling thread's current EGL context.
  **Fix:** preserve the current EGL display, context, read/draw surfaces and client API across instance destruction, restoring them when the context changes and reporting restoration failure.
  **How found:** trace the EGL state before and after each Vulkan call; only vkDestroyInstance clears it.
  A standalone Wayland EGL/Vulkan test loses its context unguarded and passes four iterations with the source helper; probing on another thread also preserves the UI thread's context.
  A shim using restoration makes the original application's native Wayland capture work.
  The closed driver's internal teardown mechanism was not established.
  An EGL_EXT_platform_device pbuffer reproducer cannot restore its context, so the Wayland result does not establish a fix for that separate route.
- **Symptom:** an X11 child is declared correctly but its first image stays black.
  **Cause:** mapping the child after XPutImage clears the pixels with the window's background.
  **Fix:** map before uploading the first image.
  **How found:** retain the black capture and repeat the same child declaration and placement with the map ordered first.
- **Symptom:** the Xwayland child is visible but the flat GLFW parent disappears.
  **Cause:** the measured GLX parent path does not retain its flat surface across child redirection.
  The lower-level GLX mechanism remains unestablished.
  **Fix:** use an alpha-capable EGL parent on both Linux window systems and verify the ordinary 2D control independently.
  **How found:** change only GLFW's context creation API in the same harness; the parent and both child eyes then appear together.
- **Symptom:** libstereo-declare 1.10 reports no delivered depth limits for a listed stereo Xwayland child, while native Wayland receives them.
  **Cause:** KWin +stereo3d58 writes the property only to a managed top-level that declares stereo content; the ordinary parent is deliberately undeclared and the child is not a managed top-level.
  **Fix:** the compositor writes the parent window's output limits on each listed declared child, follows stereoChildrenChanged, and withdraws the property when the declaration or membership goes.
  **How found:** the same extended testStereoDepthLimits binary fails at the child's missing property against the published library in normal and scaled2x rows, and both rows pass with the local compositor patch.
  The SDK harness then receives 10 and 4 on both GPUs through Xwayland.
  This fix was built and tested privately; no package or publication is claimed.

Orthographic shear still needs care beyond the scalar disparity equation.
The splat engine's SH and ray helpers recover a camera origin using a transposed rotation, which assumes a rigid view matrix.
Do not feed an affine shear through that pose and claim the view-dependent colour and ray state remain correct.
Keep the pose separate from the projection or add an explicitly tested affine-camera path in the shared engine.
Wide-angle projections also require rectification analysis before claiming zero vertical disparity.
The later whole-window measurements below complete the splat, preview and pair-cost checks.

## Captured point and mesh geometry

The preview uses the same compositor-limit fitter as the splat worker.
Preserve the first eye's FBO pixels before rendering the next eye.
A native pair uses two complete eye rasters; the logical canvas stays independent of the render width.
The point/mesh regression measures coloured markers at camera depths 1.5, 3 and 6 with a zero-parallax distance of 3.
It passes perspective and orthographic projections, widths 960 and 1200, and normalized limits (10,4) and (24,9.5) on AMD and NVIDIA through Wayland and Xwayland.
Absent and zero limits reproduce the mono pixels exactly in this renderer test; swapping the captured halves fails.
These measurements are FBO reads in private compositor sessions, not the complete application/output-scale acceptance matrix.

- **Symptom:** the mesh has twice the predicted perspective disparity while the point preview is correct.
  **Cause:** the mesh's optimized clip-space branch bypasses the common nonlinear projection helper.
  **Fix:** add the principal-point displacement multiplied by clip w to that branch, and the orthographic shear to its separate branch.
  **How found:** measure marker centroids against the camera prediction; the mesh measured -4 where the prediction was -2, on both GPUs.
- **Symptom:** a finite centre-projected Gaussian makes the fitted pair identical because its cutoff sphere crosses the camera plane.
  **Cause:** a physical solid's singular perspective bound was applied to the linearized 3DGS/Mip projection.
  **Fix:** bound inverse-depth parallax using the linearized Gaussian reach and the renderer's clamped Jacobian; keep the physical bound for ray-traced 3DGUT.
  **How found:** the first native application capture reported no finite support; source inspection showed centre-only culling and covariance projection, and the expanded CPU regression covers large/off-axis Gaussians.
  The real trained-splat viewer now presents a valid declared pair on both GPUs.
- **Symptom:** orthographic disparity maths is right but view-dependent colour follows the wrong eye position.
  **Cause:** using a transposed affine matrix as its inverse moves the recovered camera origin.
  **Fix:** preserve the rigid arithmetic for ordinary rotations and use a true inverse for oblique cameras, in shared Slang with regenerated CUDA headers.
  **How found:** a first-band spherical-harmonic fixture at the zero plane gives 0.347021 rather than the physical-eye prediction 0.359601.
  The activated regression has a verified red and matches the physical-eye colour prediction with the shared shader on RADV and NVIDIA Vulkan.
  The same physical-eye colour test also passes on CUDA, with the ordinary rigid-camera reference unchanged.

The preview PNG checker independently decodes all 64 retained pairs and checks their chunk CRCs and left-first sTER mark.
Its 192 marker measurements have a maximum horizontal error of 0.96875 pixels and zero vertical error.
Swapping the decoded halves fails the checker.


## Built pair and whole-window proof

The shared camera fitter takes only the compositor's normalized sunk and popped limits, visible scene support and the current navigation camera.
No setting, environment reader, CLI field or generic configuration schema can write a separation, swap or output mode.
The only persisted stereo keys are enable and per-eye width; the remaining control opens Display Settings.
For perspective, the predicted right-minus-left disparity is `f b (1/C - 1/Z)`.
For orthographic views it is `2 f a (Z-C)`, with parallel physical origins at `-a C` and `+a C` and opposite projection shears.
The Gaussian support uses the actual linearized covariance/Jacobian reach, including its off-axis clamp; 3DGUT retains the physical ray support.
Grid, cameras, visible mesh triangles and ROI geometry contribute to the same conservative fit.
Linked comparison wipes merge support in shared world units and compose corresponding integer regions of each eye only after both image epochs and cameras agree.

The complete application was captured as 108 marked pairs: 96 cases cover splats, points and meshes, perspective/orthographic, two limit settings, 100/125 percent output scale, two GPUs and both window systems.
Another twelve cover the three wide lenses rectified to a real perspective view.
An independent checker measures 324 near/screen/far markers; maximum horizontal error is 0.676 pixels and vertical error 0.373 pixels, within the one-pixel sampling allowance.
The earlier 64 FBO pairs remain the separate renderer control; exchanging their decoded halves fails the prediction checker.
The complete ordinary 2D client above its log equals the accepted baseline pixels on all four GPU/window-system routes.
No-limits and zero-limits source eyes are exact copies and say so visibly; after the compositor filter correction below, their complete captured eye images are also byte-identical.
Resize, hide/show, close/reopen, grid overlays and a near-marker double-click are exercised through ordinary UI/window actions.
Live training captures use the same pair worker and record one engine step for both images.

Wide fisheye/equisolid/panorama views are explicitly rectified when 3D receives nonzero valid limits.
The selected lens and horizontal centre magnification are retained; a panorama uses square-pixel perspective sampling.
The resulting field is narrower than the original panorama, and the person can turn to see its other directions.
A translated notice explains the changed projection.
Ordinary 2D and absent/zero limits keep the original lens; there is no additional stereo control.

At 400 by 300 pixels per eye, a real atomic request over the loaded 3,395-splat scene gave these medians after five warm-ups and 25 interleaved samples:

| Backend/device | One camera | Atomic pair | Ratio |
| --- | ---: | ---: | ---: |
| RADV integrated | 1.863 ms | 3.964 ms | 2.128 |
| Vulkan RTX 3060 | 0.787 ms | 1.972 ms | 2.506 |
| CUDA RTX 3060 | 0.398 ms | 1.030 ms | 2.585 |

These include the fitter, engine lock, render, readback and packing, excluding HTTP/JPEG and GUI presentation.
The engine pool plus scratch capacity remained 4,134,023 bytes on Vulkan and 3,663,750 bytes on CUDA for either request; these are not total driver allocations.
This is a small scene and camera, not a GPU ranking or a large-scene throughput guarantee.

- **Symptom:** a successful capture process saves Rendering instead of the model.
  **Cause:** GUI readiness precedes the asynchronous worker's completed image.
  **Fix:** wait for a completed native pair and a semantic scene witness, not a fixed sleep alone.
  **How found:** inspect the rejected full-window picture and its worker revision log.
- **Symptom:** a fractional-scale capture misses markers below or beside the screen.
  **Cause:** the initial GLFW window's pixel-sized work area can exceed the compositor's logical output.
  **Fix:** maximize the private test window through KWin's ordinary window API before measuring it.
  This is a rig operation, not a claimed application startup-size fix.
  **How found:** compare the application's display/framebuffer sizes with the output's scale and logical geometry.
- **Symptom:** tiny antialiased point clusters appear to have vertical disparity in a thresholded centroid.
  **Cause:** the binary threshold discards different edge pixels after a horizontal subpixel shift and output resize.
  **Fix:** use each pure primary marker's intensity centroid, preserving all its filtered sample weights and the same one-pixel tolerance.
  **How found:** retain the threshold-check failure and compare its discarded pixels against the renderer FBO's zero vertical error.
- **Symptom:** identical RGB eyes differ by one code value after the output resize.
  **Cause:** interpolating atlas coordinates before subtracting an eye offset changes floating-point filter weights; normalized hardware bilinear sampling adds another offset-dependent rounding.
  **Fix:** interpolate eye-local texel coordinates, compute the area weights there and fetch RGB texels explicitly for bilinear interpolation.
  **How found:** the same standalone KWin texture test fails on both GPUs before the filter change and passes afterward, along with its existing address/downscale rows.
  The complete no/zero-limit captures then have exactly identical halves.
  This correction is in the compositor; the program does not pre-resize an eye.
  Legacy GLSL and multiplanar/external texture paths keep their existing sampling, and are not claimed by this RGB regression.
- **Symptom:** fractional-scale Xwayland picking misses while native Wayland succeeds.
  **Cause:** the test converted screenshot pixels using output scale even though the Xwayland client's coordinate space was already in pixels.
  **Fix:** derive pixels per client coordinate from the captured eye width and the application's reported display width.
  **How found:** the injected click left the camera pivot at depth 3; the corrected mapping picks the near marker at depth 1.5.

Live limit changes from (10,4) to (24,9.5) change the fitted camera offset by the predicted 2.375 ratio without reopening the view.
The same open window survives a 100-to-125-percent output-scale change, zero limits, and restored limits on native Wayland and Xwayland.

- **Symptom:** a tall point/mesh canvas stretches the scene when the eye raster reaches its height cap.
  **Cause:** the preview used the whole canvas after independently capping render height.
  **Fix:** letterbox the capped preview at its rendered aspect, like the engine viewport, without resizing the eye internally.
  **How found:** review the preview and engine placement paths, then capture the same markers in a 400-by-850 window at a requested 4,096-pixel eye width.
  Both tested GPUs retain square geometry; maximum horizontal prediction error is 0.097 pixels.

## Checking that a proof picture actually has two eyes

Decode the PNG and compare the RGB planes of its two halves as well as checking its left-first sTER chunk and CRCs.
A marked pair with equal eyes is a flat control, never proof of a real scene in depth.
Keep deliberate absent-limit and zero-limit pairs, labelled with that reason, and make the proof checker refuse them if offered as a proof.
The same refusal applies to a .pns file: its extension and mark do not prove depth.

- **Symptom:** a complete real-scene pair is reported identical while the renderer and a fresh capture show different eyes.
  **Cause:** an RGBA difference's alpha plane is zero when both inputs are opaque; an alpha-only bounding-box check then returns no box even when RGB differs.
  **Fix:** compare decoded RGB arrays or explicitly include the RGB bands in the difference criterion.
  **How found:** the same two retained pictures returned no box as RGBA differences but 134,976 and 67,707 differing RGB pixels, confined to their native viewports.
- **Symptom:** a static model has only one completed native presentation and the rig waits for a second forever.
  **Cause:** loading and resize events can coalesce into one valid final image; readiness is not a frame-count promise.
  **Fix:** require a completed native presentation and a semantic scene witness, then check the decoded proof's unequal eyes and geometry.
  **How found:** an unmodified program presented the trained spheres once, with a valid camera offset and unequal submitted RGB eyes, while the old two-presentation wait timed out.


## Real Gaussian scenes measured in compositor captures

For a real trained scene, trace a completed atomic pair while holding the engine lock.
Record its request id, training step, cameras, native RGB eyes and the GPU's projected Gaussian ids, world centres, conics, opacity and colour for centre, left and right cameras.
First independently project every in-viewport world centre and compare it with the GPU coordinates.
The common ids must still have bit-identical world centres in all three projections.
For near, navigation-target-plane and far witnesses, require actual front-to-back contribution above the raster cutoff in both eyes, rather than choosing invisible points from the model's bounding box.
Register each native eye to its compositor screenshot with the compositor's actual area filter and a two-axis textured patch.
Transfer the selected Gaussian centre through that measured registration to obtain its captured position.
State the raster and displayed size, candidate depth range, contribution, image residual and horizontal/vertical error.
These are contributing Gaussian-centre correspondences, not a claim that an alpha-blended pixel has one opaque surface depth.
A 48-case real-scene matrix on both tested GPU families and both native window routes, including CUDA, used 1,920-pixel-wide eye rasters at two limit settings and 100/125 percent output scale.
Its 144 visible-centre measurements had maximum horizontal prediction error 0.069733 displayed pixels and vertical residual 0.044086, below the fixed 0.15-pixel gates.
Independent GPU-coordinate prediction error stayed below 0.000196 native pixels and the largest native/captured patch residual was 0.307 RGB codes.
The navigation target has an analytic zero disparity; distinguish that prediction from the measured visible Gaussian nearest its plane.

A three-pixel-displaced eye is not proved by an RGB inequality check alone.
Keep a swapped-eye geometry negative that fails the same fixed measurement tolerances.
A separate analytic translation calibration should include a nonzero vertical shift and fractional native-to-display transforms.

An instrumented pair costs an extra centre render and GPU readbacks.
Never report its frame time as the ordinary pair cost given above.
Keep the trace ring bounded and preserve only the request actually found in the screenshot.
For live training, keep two coherent presented pairs with strictly increasing training steps, without pausing training or disabling Live.

- **Symptom:** deprojected Gaussian depth predicts the wrong disparity despite correct camera matrices.
  **Cause:** this renderer stores each Gaussian's centre distance, `length(mean_c)`, then alpha-composites it; that value at a pixel is not the depth of an opaque surface.
  **Fix:** measure actual projected contributing Gaussian centres, independently check their world-to-camera projection and register their native raster to the captured output.
  **How found:** the rejected blended-depth probe predicted +0.041 pixels for a patch whose registered displacement was +0.163 pixels; reading the projection and raster code exposed the mixed-distance definition.
- **Symptom:** the log says a pair was uploaded, but registration matches an older live-training image.
  **Cause:** upload completion precedes compositor presentation.
  **Fix:** under explicit test automation only, encode the request and step with a checksum in identical monochrome cells in both eyes; select the trace by decoding the screenshot.
  Check witnesses at opposite ends of each eye raster, not only one corner.
  **How found:** one-corner registration at fractional scale selected a new request while the bottom of the captured native image belonged to its predecessor.
- **Symptom:** one Xwayland capture contains two training steps even though the shared worker produced a coherent pair.
  **Cause:** a large `XPutImage` to a visible child is split into protocol chunks that the compositor can observe separately.
  **Fix:** upload the complete pair into a cached offscreen X11 pixmap and issue one `XCopyArea` to the declared child; replace/free the pixmap on resize and destruction.
  No extra stereo declaration, camera implementation or user option is needed.
  **How found:** a test interposer deliberately split the image upload with a half-second delay; opposite-end CRC witnesses read requests 3 and 2 before the fix, and two coherent advancing training frames after it.
  Native Wayland keeps its immutable shared-memory buffer commits.
- **Symptom:** point-sampling a native raster produces a large image residual after a fractional compositor resize.
  **Cause:** the compositor uses an area filter, so point samples are a different reference image.
  **Fix:** integrate the same source texel boxes and fit translation at the screenshot's integer pixel centres.
  **How found:** an independent analytic fractional-transform calibration and the compositor's filter source separated interpolation error from camera error.


## Choosing which visible depth receives the budget

Daniel decides the support policy; the accepted conservative fitter remains the production default until that decision.
A renderer can place most visible texture almost at screen depth while its covariance envelope consumes the person's popped limit.
Measure the picture before treating that result as a failed two-camera implementation.

For a translucent Gaussian image, distinguish each contributing Gaussian's centre depth from a pixel's mixture of depths.
With axial depths `Z_i` and the renderer's front-to-back weights `w_ip = alpha_ip T_before`, accumulate `A_p = sum_i w_ip` and `R_p = sum_i w_ip / Z_i`.
The contribution-weighted pixel disparity is `f b (1/C - R_p/A_p)`.
Use `A_p` as the histogram weight and `A_p/R_p` as the effective depth; this is an inverse-depth statistic, not an opaque surface reconstructed by deprojecting blended ray distances.
A dedicated study build fits only its weighted 1st and 99th percentiles, keeping the navigation target fixed.
The ordinary executable contains neither this fitter nor a runtime route to it.
A build switch defaults off, requires the test targets and gives the experimental executable a distinct name.

Keep both kinds of tail measurement.
The weighted pixel mean can lie inside a limit while one of its visible translucent layers lies outside it.
Report the mean's out-of-budget pixel area and weight, the individual-layer out-of-budget weight and area, the largest excursions and their locations, and the fraction in a specified edge band.
Content outside the chosen percentile range remains rendered with its original geometry and opacity in this experiment.
A percentile rule is not a hard guarantee for all visible content and cannot silently replace a hard-bound contract.
For on-screen statistics, filter opacity and disparity-times-opacity with the compositor's actual filter before dividing, sorting and counting pixels.
Keep the renderer-native distribution separately, because nonlinear histogram operations do not commute with the output resize.

In one generated object study, the conservative fit put all contribution-weighted pixel means within half a displayed pixel at the default limits.
The percentile experiment gave stronger depth and also retained out-of-budget layers; use the paired pictures and full tail table to decide the policy rather than reporting only its central 98 percent.
The working comparison keeps both GPUs, exact centre-camera/world/RGB controls, GPU-transmittance checks and captured projection correspondences.
It adds no program setting or separation control.

Established alternatives differ.
[OSCAM](https://studios.disneyresearch.com/wp-content/uploads/2019/03/OSCAM-Optimized-Stereoscopic-Camera-Control-for-Interactive-3D-1.pdf), section 5, takes a min/max reduction of the visible depth buffer and controls convergence as well as baseline.
[Blender's stereoscopy manual](https://docs.blender.org/manual/en/latest/render/output/properties/stereoscopy/usage.html) exposes interocular distance and convergence rather than automatically selecting a contribution percentile.
Their display controls are not imported into the edition's program.

- **Symptom:** a log value is read as hundreds of omitted Gaussians.
  **Cause:** the field printed as `unbounded` is the first offending Gaussian index, not a count; its finite positive-centre projection can still constrain the fit.
  **Fix:** inspect the variable and measure the actual contributing set before changing the explanation or dropping points.
  **How found:** `unbounded=463` identified an index; the fixture had seven spherical envelopes crossing the camera plane and retained all 3,395 candidates in the projected-support loop.
- **Symptom:** a tail report suddenly assigns several percent of the weight just beyond the limit although the endpoint equals it.
  **Cause:** algebraically equal double-precision endpoints differ by one unit in their last place.
  **Fix:** declare a tiny numerical boundary tolerance, keep it separate from the capture error allowance and still report the actual excursion size.
  **How found:** a nominal endpoint of -6.269010416666666 pixels became -6.269010416666667 in the equivalent disparity expression; a 1e-7-pixel roundoff tolerance removed this false tail without hiding real multi-pixel excursions.
