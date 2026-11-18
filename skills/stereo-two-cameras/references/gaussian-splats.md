# Gaussian splats in stereo: what is view-dependent, what a second camera costs, the route to a declared pair

Started in ORDER 501, November 2026, from unchanged Spirula Studio master `b8e15cb8d7f8a2f45ca9b4fea3fa331181433caa`.
This is a source study and monoscopic baseline, not an implemented stereo renderer.

## Working recipe

1. Pin the source and read its build and contribution rules.
   Spirula's `build_develop.bash -DSS_BACKEND=vulkan` builds a native application without CUDA or model weights.
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

## The route to the window

Vulkan compute does not imply Vulkan presentation.
In this application an image-layer count on a top-level Vulkan swapchain would not reach the actual GUI, and declaring the whole GUI would put flat controls in the wrong surface.
A native viewport adapter must expose a Wayland subsurface or X11 child, with the pair declared through the shared declaration library and a transparent viewport hole in the parent.
Keep flat overlays above that surface, coordinates logical, and the eye raster independent from the displayed rectangle.
The ordinary 2D viewport remains the comparison control.

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
  A standard CMake Release configuration is being checked as a source-preserving baseline; an owning-target correction needs a separate source-fix task if it is still required.
  **How found:** the link map's archive-inclusion table names `std::string::append` as the trigger, and [upstream issue 339](https://github.com/harry7557558/spirula-studio/issues/339) reports the same Linux failure.
  The reported one-target removal in that issue explicitly leaves other targets broken, so it was not applied.

## Measurements and limits

The initial fixture is twelve calibrated 192 by 144 frames of three spheres over a checkerboard floor, with 3,395 visible-surface seed points.
The baseline compositor capture is a 1280 by 900 monoscopic virtual output, with desktop depth disabled.
Runtime timing and memory figures belong to the measured setup and are added after the unchanged build and application runs finish.
No stereo image or second-eye geometry is claimed here.
