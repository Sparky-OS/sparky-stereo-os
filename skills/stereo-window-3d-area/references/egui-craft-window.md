# egui: a native stereo child with one shared owner

The Craft Apps' `craft-stereo-window` work uses a native child toplevel for the picture, beside an ordinary egui editing window.
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
5. Test independent eye/row/column sample IDs before compositor scaling.
   X11 drawable readback can establish every native sample; a Wayland trace establishes buffer geometry, and the captured output still needs both-eye comparisons against independent references.
   Read the client's rectangle from KWin rather than deriving it from the image being tested.
   Assert zero differing pixels outside it.
6. Build a stock-main binary from an untouched pinned checkout with the same environment.
   Clean the one Cargo target between worktrees as well as projects: reuse can select a branch's same-named crate artifact in the control build.
   Compare ordinary 2D captures byte for byte on both backends.

## Measured traps

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
