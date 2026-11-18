# Gaussian splats in stereo: what is view-dependent, what a second camera costs, the route to a declared pair

Started in ORDER 501, November 2026, from unchanged Spirula Studio master `b8e15cb8d7f8a2f45ca9b4fea3fa331181433caa`.
This is a source study and monoscopic baseline, not an implemented stereo renderer.

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
  This fix is proposed; it was not implemented in the baseline milestone.
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
The GPU regression passes on RADV and NVIDIA Vulkan.
The rebuilt application also displays its trained PLY on NVIDIA native Wayland with the actual source context-restoration helper and no preload.
CUDA parity after the affine shader changes remains pending.

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
  **Fix:** the compositor writes the owner's output limits on each listed declared child, follows stereoChildrenChanged, and withdraws the property when the declaration or membership goes.
  **How found:** the same extended testStereoDepthLimits binary fails at the child's missing property against the published library in normal and scaled2x rows, and both rows pass with the local compositor patch.
  The SDK harness then receives 10 and 4 on both GPUs through Xwayland.
  This fix was built and tested privately; no package or publication is claimed.

Orthographic shear still needs care beyond the scalar disparity equation.
The splat engine's SH and ray helpers recover a camera origin using a transposed rotation, which assumes a rigid view matrix.
Do not feed an affine shear through that pose and claim the view-dependent colour and ray state remain correct.
Keep the pose separate from the projection or add an explicitly tested affine-camera path in the shared engine.
Wide-angle projections also require rectification analysis before claiming zero vertical disparity.
The end-to-end splat geometry, preview paths and real atomic-pair timing remain unverified at this checkpoint.

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
  The full trained-splat capture after this correction remains pending.
- **Symptom:** orthographic disparity maths is right but view-dependent colour follows the wrong eye position.
  **Cause:** using a transposed affine matrix as its inverse moves the recovered camera origin.
  **Fix:** preserve the rigid arithmetic for ordinary rotations and use a true inverse for oblique cameras, in shared Slang with regenerated CUDA headers.
  **How found:** a first-band spherical-harmonic fixture at the zero plane gives 0.347021 rather than the physical-eye prediction 0.359601.
  The activated regression has a verified red and matches the physical-eye colour prediction with the shared shader on RADV and NVIDIA Vulkan.
  CUDA green and final parity remain pending.

The preview PNG checker independently decodes all 64 retained pairs and checks their chunk CRCs and left-first sTER mark.
Its 192 marker measurements have a maximum horizontal error of 0.96875 pixels and zero vertical error.
Swapping the decoded halves fails the checker.
