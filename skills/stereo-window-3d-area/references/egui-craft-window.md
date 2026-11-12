# egui: a native stereo window with one shared owner

The Craft Apps' `craft-stereo-window` work uses a native toplevel for the picture, beside an ordinary egui editing window.
This is a separate Stereo View/Monitor, not a claim that the image is embedded under the main canvas.
An embedded canvas needs its own subsurface/child-window integration and overlay/input tests.

## Working recipe

1. Keep document/media interpretation outside the window backend.
   Deliver one left-first side-by-side raster, with both eyes at their stored resolution.
   Carry intended pixel aspect as a positive rational separately from the pixel dimensions.
2. Put the Linux backend in one app-independent shared crate; app adapters supply the picture and lifecycle only.
   A Wayland backend owns its display connection/thread, attaches the native buffer, declares content value 3 and uses viewporter destination for logical placement.
   X11 needs the announced protocol's independent native raster/one-view placement handshake; changing the drawable size to fit the window would resize the input.
   Retain the vendored protocol's exact licence and attribution; check the receiving project's allowlist.
3. Make declaration state explicit: no pair means no declaration; opening declares once; an ordinary image removes it; closing and reopening creates a live handle again.
   Unsupported desktops follow the ordinary left-eye preview policy without stereo declarations.
   Do not declare the egui editing window.
4. In an egui refactor, follow the actual owners.
   PhotoCraft moved save logic into `ui-egui/src/app/files.rs`, services into `services.rs`, canvas display into `canvas/display.rs`, and commands into `engine/src/cmd/`.
   FilmCraft split export types, registries and encoders into `format.rs`, `registry.rs` and `encoders.rs`.
   Port the small hook into those owners; do not restore obsolete monoliths from a conflict.
   When the receiving host separates logic from drawing, keep native picture delivery and closure in its logic callback so they continue without a UI paint.
5. Test independent eye/row/column sample IDs before compositor scaling.
   X11 drawable readback can establish every native sample; a Wayland trace establishes buffer geometry, and the captured output still needs both-eye comparisons against independent references.
   Read the client's rectangle from KWin rather than deriving it from the image being tested.
   Assert zero differing pixels outside it.
6. Build a stock-main binary from an untouched pinned checkout with the same environment.
   Clean the one Cargo target between worktrees as well as projects: reuse can select a branch's same-named crate artifact in the control build.
   Compare ordinary 2D captures byte for byte on both backends.

For an editor with square-pixel previews, keep those previews separate from the stored eye grids.
Do not feed an expanded preview or a viewport-sized texture to the native window.
A request for the full source can still render into its requested box: derive the output dimensions from the edited native frame, and carry sample aspect independently.
Account for retained original grids in the source cache's byte budget and identity checks.
Unequal source grids need an explicit native-view refusal rather than silently fitting one view to the other.

## Measured traps

- Symptom: native workspace tests and Clippy pass, but the final wasm gate reports `missing field stereo_view in initializer of Services`.
  The browser host has an explicit service literal that native target checks do not compile.
  Set the native-only service to `None` there, preserve the ordinary browser loupe, and rerun the receiving gate including wasm before committing.
- Symptom: a logic-only test appears to set a texture limit, but never reports it to the app.
  A `Headless` harness property is consumed by its `step`, not by a separate `Context::run_ui` closure that calls only app logic.
  Send `RawInput::max_texture_side` in that closure and assert the app received it.
  The tested egui font atlas requires a width of at least 1024; use a larger source view to test cap independence, rather than an invalid smaller atlas.
- Symptom: native sample IDs are correct but a PNG pair's displayed shape is wrong.
  Preserve the PNG decoder's `pHYs` information through view copies.
  [PNG 3 §11.3.4.3 and §13.6](https://www.w3.org/TR/png-3/#11pHYs) define sample width/height as ppuY/ppuX, including unit 0.
  Keep it as a reduced positive rational and invert it when EXIF or an edit exchanges the axes.
  This is metadata for the native window; it does not call for expanding its sample buffers.

- Symptom: the control socket connects, but import returns `FilmCraft is still starting; send the request again`.
  The listener starts before the app can drain its command queue; `control_server.rs` explicitly rejects the request before queueing it.
  Poll the read-only `ui.menu.list` with a deadline until the handler is ready, then issue import once.
- Symptom: an ordinary LightCraft control is dimmed by `Lens Profiles` despite an initial dialog cancel.
  Its first-launch offer waits for earlier dialogs and library startup to finish, so it can appear later.
  Dismiss it after the selected image has finished loading, then settle and capture.
  Apply the same sequence to edition and untouched-stock controls; inspect the complete image and compare without masks.
- Symptom: complete ordinary captures compare equal while startup dialogs cover the photograph.
  The probe wrote an obsolete `seenVersion`; a disk notice blocked the underlying What's New dialog from being presented and recording the current version, so cancelling it could make it due again.
  Read the actual version from the pinned source for private test setup, acknowledge the disk notice through its registered OK button, and require a stable interval with no notices or modal widgets before exporting or capturing.
  Record that state witness and inspect the complete image as well as comparing every pixel.
  Preserve the application's warning threshold: its 20 GiB or 10 percent low-space notice can be legitimate above the build lane's floor.
  Repeat affected captures with fresh names and keep the obscured attempts as diagnostics.
- Symptom: ordinary controls differ in 106 pixels although full-resolution exports match exactly.
  Compare the actual stage buffers: the edition cached a CPU preview while stock used GPU stages.
  LightCraft's `gpu::device` deliberately returns `None` during `WINDOW_PENDING` adoption.
  Read-only poll `app.gpu` until the default adapter is available before importing in both controls; leave GPU enablement and processing unchanged.
  Retain the readiness and stage-cache witnesses.
  Both backend comparisons then matched every RGB pixel, without a tolerance or mask.
  This removed the startup rejection in the fresh X11 capture without changing the application.
- Symptom: Stereo Monitor enablement tests pass, but its host receives zero pictures after a rebase.
  FilmCraft's old update called `stereo_monitor::tick`; that call was lost when main split logic from drawing.
  Restore it in `logic_inner` after playback and job updates.
  A regression that calls only logic, without UI passes, failed with no delivered frame before the fix and then passed frame delivery and closure; all seven monitor tests passed.
  Keep native compositor proofs as a separate check.
- Symptom: an ID probe shows a blank stereo image and every sample is wrong.
  Check the decoder first: FilmCraft reported no decoder for FFV1.
  A successful import/sequence command did not prove the frames decoded.
  A supported PNG with explicit Interpret Footage provided a valid native-grid negative control.
- Symptom: a font-menu test passes in a shared test process but fails under nextest.
  Measure the real per-process font inventory and run the saved binary with that inventory.
  Do not relax the test or report the shared-process pass as isolated coverage.
- Symptom: a HEVC conformance test passes almost instantly while another environment fails.
  Verify that the external oracle actually ran: an upstream fixture helper may return a successful skip before reading even an existing fixture.
  Decode suspect streams with HM and check the number and content of reconstructed pictures; exit zero on an empty stream is not success.
- Symptom: strict shared-crate Clippy fails on protocol imports after a rebase.
  Follow the workspace's new explicit-import policy in the handwritten protocol wrapper; generated code allowances need not weaken workspace rules.
- Symptom: an unchanged Unicode process-path test fails only in the minimal SDK.
  Compare the same binary under the C and UTF-8 locales before changing process matching.
  The Craft library test passed with `LANG=C.UTF-8 LC_ALL=C.UTF-8`; preserve that environment in the runner.
  A separate spelling-budget test exceeded its deadline in a parallel workspace run and passed in the complete serial run.
  Keep both logs and the actual thread setting; do not increase the assertion's deadline to hide contention.

- Symptom: private portal tests report `Memory allocation failure in message bus`, preceded by `Looking up user ID 1000: not found`.
  The SDK has no passwd entry for the unprivileged test UID.
  Add that account in the disposable build image; raising the memory limit does not address this cause.
  The same compiled portal tests then pass with no app source change.
- Symptom: scratch-corruption regressions fail during setup with `scratch disk ... is low on free space`, even above the lane's disk floor.
  Read the product reserve too: PhotoCraft at de7e1eec keeps max(1 GiB, 5% of the scratch volume), so a nearly full build disk cannot enable spilling.
  Provide a separate bounded test filesystem with enough room for that unchanged reserve.
  A 4 GiB private tmpfs under a 16 GiB container memory cap passed the identical portal/scratch binaries; Cargo targets and caches stayed on the build disk.
  Record the backing filesystem, memory limit and actual free-space measurement with the test result.

## A retained SHM pool is a direct native-grid witness

An editor's finishing pass can intentionally change input samples through colour conversion and dithering.
A LightCraft native ID probe initially differed from its source PNG in 327 pixels, each by one channel step.
Its existing Bayer dither and colour processing were byte-identical to stock main.
Ordinary single-eye exports matched the native buffer exactly.

Keep two independent checks: compare decoder copies with decoded input samples before rendering, then compare native output with ordinary single-eye renders from untouched stock main using the same settings and GPU path.
Validate all reference images against that stock build.
Preserve the initial mismatch and a swapped-eye failing control.
Do not disable intended processing, mask pixels or relax an exact comparison to make the probe pass.

A preload recorder may produce no dump even while a dynamically dispatched client logs valid `wl_shm` requests.
Geometry in the protocol log alone does not prove that the samples were copied.
For the tested SCTK native window, the pool retains its original memfd for resizing.
The FD number printed by marshalling was a transient duplicate; opening that number later failed, while the retained original was still present.

1. Use only the test client's PID inside its isolated container.
2. Follow the stereo declaration to its surface, the attached buffer, and that buffer's pool, offset, width, height, stride and format.
3. Select the retained `smithay-client-toolkit` memfd by its public name and the pool capacity from create/resize requests.
   Require one unique inode before looking at any expected pixels; reject missing or ambiguous candidates.
4. Read the buffer region twice and require stable bytes.
   Interpret XRGB8888 as the protocol specifies, then compare every RGB pixel with independently generated left/right references.
5. Keep a swapped-eye reference as a failing control, and measure the displayed pair against one-resize references plus the independent client rectangle.

On 2026-11-10, PhotoCraft's full, half-width and half-height ID pictures matched 6,635,520 native RGB pixels across Wayland and X11 with zero differences.
The Wayland swapped-eye references differed at every pixel.
Displayed sample shape matched its rational pixel aspect, single-resize PSNR was 58.94–69.46 dB, and there were zero eye differences outside the media window.
This result covers the tested opaque RGB8 path; it is not a deep-colour, stock-main 2D or other-platform proof.

## Prove the decoder feature that changed

LightCraft's default desktop feature set excludes HEIF, while its Linux gate separately tests the HEIF codecs and engine.
For a HEIF change, build both the untouched stock GUI and the candidate with `cargo build -p lightcraft --features heif`, keeping their other defaults equal and recording the feature flags with each ELF hash.
Use a synthetic HEIF whose primary image and two eye images have different samples; the metadata-only stereo fixture's identical eye samples cannot establish eye identity.
For a tiled PCM fixture, decode each distinct coded tile with HM and compare it with the chosen YCbCr samples, then require every reused tile to match a checked stream.
Export the standalone left and right HEIF images as ordinary pictures through untouched stock to obtain the finishing and dithering oracle.
Compare the candidate's native pair with those exports on Wayland and X11, retain swapped-eye failures and check the area outside the media rectangle.
Compare complete ordinary HEIF captures against stock too, using the same default GPU readiness sequence and no masks.
The measured aligned 384 by 256 grids produced exact native and displayed eye pixels, and exact whole-output ordinary controls on both backends.
Keep that aligned-file identity claim separate from the declared-size crop correction carried by [craft-libs #841](https://github.com/storytold/craft-libs/pull/841); the former app decoder could expose coded padding on other files.
This is opaque RGB8 synthetic coverage; real-camera HEIC, padded-file GUI behavior, HDR and other platforms need their own checks.

## A depth-plane animation stage

Keep an authored 2D stage's depth model in its evaluator, before rasterization.
AniCraft's camera law is `p(z) = 1000 / (1000 + clamp_depth(z))`: camera pan gains parallax while artwork keeps its size.
For two stereo views, keep the ordinary camera transform and shift each root layer horizontally by half its signed disparity, in opposite directions after that transform.
Nested symbol artwork inherits its root layer's placement once; do not apply the inner layer's depth again.
Masks, clips, groups, guide flags and timeline identity stay in the ordinary evaluator.
Real 3D transforms require coherent parallel cameras of one world, rather than this depth-plane model.

Read the compositor's current limits through the shared window owner.
The version-5 Wayland protocol supplies `depth_limits`; the later X11 support-10 protocol supplies two signed 24.8 words in `_KDE_NET_WM_STEREO_DEPTH_LIMITS`.
Keep the vendored protocol's licence and source sidecar.
Those limits are pixels at an output width of 1920: convert to native samples with `output_width * native_eye_width / (1920 * displayed_view_width)`.
An absent or ambiguous output/view geometry is unknown, not permission for a guessed baseline.
A first ordinary pair can map the native window so placement feedback arrives; give that asynchronous handshake a bounded grace period before reporting unavailable depth.
For the tested planar model, left-minus-right disparity is `min(sunk_native * (p(z) - 1), popped_native)`.
Depth zero skips the extra matrix operation entirely, preserving even the ordinary transform's floating-point representation.

Key both the image cache and the evaluated-display-list cache by eye and native limits, in addition to the existing document state and frame identity.
Otherwise two separately keyed images can still reuse one eye's display list.
Reuse the engine's bounded renderer and hold one pending document/frame snapshot until both eyes finish.
Then request the latest frame; slow rendering may drop frames, but must never pair different timeline positions.
Copy complete native rows left first into one full side-by-side picture, without scaling either eye.
Match the window's alpha policy explicitly: premultiplied RGB already represents compositing over black, so an opaque black-backed window must not multiply it by alpha again.
Do not change the ordinary editor renderer or declare its window as stereo.

Test the depth prediction, rotated-camera horizontal disparity, masks and hidden layers, nested symbols, immutable timeline frames, both cache identities and exact flat CPU bytes.
Use an untouched stock build for the ordinary GUI and flat-render references, with the same fonts, catalogs and renderer settings.
Read window geometry independently from KWin and trace the declared surface to its attached native buffer.
Retain a wrong-eye control that fails for a nonzero-depth fixture; identical flat eyes cannot establish eye order.
Keep software ScreenShot2 delivery coverage separate from real output scanout, hardware and deep-colour claims.

A real Wayland feedback probe used limits `36/18`, a 1280-wide output and a 320-wide native/displayed view.
The shared client received `24/12` native pixels, then `12/6` after a live change to `18/9`.
Both eye colors were captured and the wrong-eye color check failed.
The X11 limits reader compiled and passed fixed-point tests; that probe did not exercise an X11 support-10 compositor.

### Preserve the movie playhead and measure the actual pair

Symptom: the native movie view jumps to a different timeline position while a nested symbol is being edited.
AniCraft's `Session.frame` belongs to the current edit context; the first saved edit level holds the root movie playhead.
Select that root frame for a movie-stage view and test nested contexts with deliberately different frame numbers.
Do not advance either eye's timeline independently.

A 320 by 180 self-authored stage with layers at depths -250, 0 and 1000 gave left-minus-right disparities +8, 0 and -12 output pixels under limits 36/18 on a 1280-wide output.
Two different timeline positions moved the screen-plane layer in both eyes together.
The attached 640 by 180 native buffer matched the independent raster exactly, and swapped-eye controls failed.
After a live resize to 160 by 90 per eye, the native buffer stayed 640 by 180 and the native disparity doubled; the displayed disparity stayed +8, 0 and -12.
A flat fixture must instead match an untouched stock CPU render and ordinary GUI capture exactly; identical eyes alone cannot prove eye order.

Symptom: the proof times out waiting for feedback although the client trace contains it.
The Rust and C Wayland logging paths can spell object IDs and event arguments differently, such as `@id.depth_limits, (...)` and `#id.depth_limits(...)`.
Accept the documented trace spellings, then require native-buffer and captured-pixel checks; changing a log parser does not fix the product.
Give repeated compositor-geometry queries unique markers so a later read cannot reuse an earlier log record.
Keep the entire ordinary control window inside the virtual output and compare the complete output without masks.

### Container metadata can stop an otherwise correct client

- Symptom: KWin exits with `Operation not permitted` although its executable and shared libraries exist.
  Inspect executable file capabilities inside the disposable image.
  A retained `cap_sys_nice=ep` can request a capability excluded from the container's bounding set.
  Remove that file capability only in the disposable proof image, keeping the executable bytes unchanged, or use an explicitly authorized capability configuration.
  Never change the host executable to repair a headless rig.
- Symptom: the proof command reports `/usr/bin/bash: cannot execute binary file` before KWin starts.
  Inspect both image `Entrypoint` and `Cmd`; committing a shell-based preparation container can retain a shell entrypoint and invoke it twice.
  Set the final image entrypoint, command and unprivileged user explicitly, then run the actual launcher against that exact image ID.
- Symptom: real depth feedback arrives but ScreenShot2 reports `Screenshot got cancelled`.
  Check the rig's authorized render-node access and compositor log before changing the application.
  A software-rendered session can still need that node for the tested capture path.
  Repeat in a fresh private session and require captured pixels, not only a successful protocol event.

## A refused proof launch must explain itself

Symptom: the proof launcher exits 1 without a message before creating a container.
A bare shell regular-expression check under `set -e` rejected the case label silently.
Validate the argument count, case-label pattern, flow, frame, binary and existing receipt explicitly, printing the refused value or accepted shape to stderr.
Keep invalid-label, invalid-flow, invalid-frame and missing-binary controls that fail with a diagnostic before Docker starts.
The cause was found by running the rejected argument list with captured exit status and stderr; an empty stderr was the red witness.
Do not relax a safety pattern just to make a label work without saying what it accepts.
