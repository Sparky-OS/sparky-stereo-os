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

## Measured traps

- Symptom: the control socket connects, but import returns `FilmCraft is still starting; send the request again`.
  The listener starts before the app can drain its command queue; `control_server.rs` explicitly rejects the request before queueing it.
  Poll the read-only `ui.menu.list` with a deadline until the handler is ready, then issue import once.
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
