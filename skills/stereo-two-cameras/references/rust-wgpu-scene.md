# A Rust scene with parallel cameras

Use this recipe when a Rust renderer already has an orbit camera, shared scene uploads and per-view render targets.
Keep the camera mathematics in a pure shared crate; the desktop window and live depth feedback remain a separate dependency of the app's UI layer.
Check the current upstream camera and its open work before adding another owner.
Imported camera format data can serve a different purpose from navigation and stereo projection.

## Projection contract

Pass the existing central view and projection by value.
Use its point of interest as the zero-parallax distance D, retaining its field of view, clipping and navigation.
Translate the eye along the central view's world-space horizontal basis by a = ±e/2.
The eye view is a camera-space translation by −a multiplied by the central view.
Subtract P00*a/D from the projection's x-from-camera-z term, keeping every view axis parallel.
This is an off-axis frustum for perspective, a shear for orthographic, never toe-in.

For native eye width W, let f = P00*W/2 and let Z be a point's positive central camera depth.
The predicted left-minus-right horizontal disparity is e*f*(1/Z−1/D) in perspective and e*f*(1−Z/D) in orthographic.
The vertical disparity is zero and Z=D has zero horizontal disparity.
Transform model bounds into central camera depths, including displacement, and solve for the maximum baseline allowed by both live native-pixel budgets.
Also reserve the sunk budget for infinity; a finite far bound alone does not constrain a sky or environment.
Pass the actual perspective environment's horizontal focal coefficient as part of the shared camera input.
Its infinity profile relative to the model projection is `background_P00 / model_P00 / D` for either model projection type.
A narrowed environment field of view can otherwise exceed the sunk budget even when every model vertex passes.
For an orthographic model view whose environment uses a perspective camera, derive that background's off-axis projection from the same physical eye offsets and D.
A zero budget returns the exact central camera bits; an unavailable budget is reported by the host, never replaced with an invented separation.

## Renderer boundary

Keep simulation, geometry, materials, textures, lights and light-space shadows in one scene.
Supply each view's product, inverse product and physical eye position coherently to the unchanged shaders.
Give screen-space effects and temporal histories private targets and keys including the actual eye projection.
Retain the ordinary mono entry point and its caches unchanged.
Do not mutate and later try to repair the central camera.
Encode both cameras and their readbacks after one scene sync and before another can replace its content.
Keep at most one incomplete pair; map only after submission and present only once both eyes of that snapshot finish.
The UI must not call a blocking GPU readback during painting.

## Acceptance evidence

Compare thousands of transformed points against the equations independently, including pose, aspect, units, target plane, both projection types, zero budget and infinity.
Render a near and a far feature through the actual application and compositor at two window sizes.
Record predicted and measured disparities, matching tolerance, vertical shift and a wrong-eye control that fails.
Inspect both eyes and compare the ordinary whole window with stock on the same input, with no masks.
Pure projection tests establish the camera algebra; they do not establish GPU uniform coverage, history isolation or native delivery.

## Traps found while testing the camera core

Symptom: a finite zero-scale affine view panics inside `glam::Mat4::inverse` when a consumer enables `glam-assert`.
Cause: checking the inverse for finiteness comes after glam's singular-matrix assertion.
Fix: check finite nonzero determinants before inversion, then validate inverse, product and resulting eye matrices.
How found: a targeted singular-view regression was rerun with the dependency feature `glam/glam-assert`; it failed at glam's determinant assertion before the guard moved and passed afterwards.
Also reject a physical eye that disagrees with the inverse view, and projection cross terms that turn horizontal camera motion into vertical disparity.

Source-audit finding: two single-view eye calls can resolve a pending texture at different times even though they receive the same frame.
Cause: a public single-view preparation method resolves asynchronous allocations on every call.
The pair boundary must resolve scene resources and generate shared mips once before preparing the two private views.
Found by reading the renderer’s `resolve_pending` call and its existing deferred-allocation tests; the inter-eye race has not been reproduced.
One immutable frame argument alone does not establish one immutable GPU world.

## Inputs and renderer checks

In a branch carrying `craft-stereo-camera`, run its point-projection tests with `cargo test -p craft-stereo-camera --features glam/glam-assert`.
The tested core compares 6630 projected point pairs with the independent equations, plus pose, units, infinity, zero budget and invalid-camera controls.
TextureCraft's renderer tests use `TEXTURECRAFT_TEST_GPU=software` in an isolated software-Vulkan container and assert a CPU Vulkan adapter instead of returning early when no adapter exists.
Its `stereo_` tests check private TAA and bloom history, exact fresh mono restoration, one submitted pair with asynchronous copies, distinct target IDs, and cached displacement, high-poly and cage bounds.
Keep the ordinary entry point delegating with no eye override, including its original frame and target identity.
Cache signed height peaks only from the first half-float channel of the actual uploaded rectangle, with its actual stride.
A partial edge tile's padding is not rendered, and overwriting the maximum must remove its old envelope; a historical maximum leaves the view unnecessarily flat.
The tests upload height 20, overwrite it with zero, and require the original baseline to return; another test excludes unused padding and checks NaN repair.

Symptom: an orthographic model camera is accepted although its perspective environment has an invalid clip range.
Cause: a large distance with a tiny scene radius rounds the background's near and far planes to the same float; validating only the orthographic projection misses it.
Fix: validate the actual background's clip range before constructing its projection, as well as supplying its actual focal coefficient to the infinity budget.
How found: a renderer regression used a valid orthographic model at distance `1e10` and radius `1e-3`; it failed before the common clip guard and passed afterwards.

For egui, check the exact callback phases in the pinned `CallbackTrait`.
`finish_prepare` runs after every ordinary `prepare` call, which provides a place to encode a native pair after ordinary scene uploads.
A pair drawn by an earlier ordinary callback can precede another callback's height upload; this is a source-audit hazard, not a reproduced inter-eye race.
Retain a shared pending scene sync until either the ordinary view or the pair consumes it, and report a truly dropped sync through the existing resync mechanism.
A clipped ordinary widget must not strand the world update needed by a separate model view.

Source-audit hazard for a CPU preview: MaterialCraft derives a camera-relative key light from the central camera ray.
Keep that light in the central world and share it between eye jobs; the off-axis centre rays differ, so deriving a new light from each eye would change the world between views.
The reviewed renderer owns one immutable mesh/BVH scene, maps and lighting; adapting its rays must not create two simulations or recook materials per eye.

Symptom: the native companion opens and closes with “stereo needs two private targets distinct from the ordinary view”.
Cause: the UI put a reserved eye-target ID into the source frame as well as the separate eye-ID argument.
Fix: retain the ordinary scene ID in the source frame; the pair API assigns each private target internally.
How found: a source audit identified the collision, then a healthy private control session loaded the original two-depth model and captured the renderer’s exact rejection before the one-field fix.
The same native probe then measured the predicted +6 and −4 pixel disparities, zero vertical shift, and exact native-to-compositor pixels at a one-to-one display size.
Keep the renderer’s target-identity guard; weakening it would hide the incorrect call site.

A smaller displayed window can leave only two fully interior pixels in an analytically predicted disocclusion strip after the same edge margin.
Check every predicted interior sample and require the interval to be nonempty; do not impose a fixed four-pixel minimum copied from a larger grid.
The disparity and wrong-eye tests retain their separate exact predictions.
The ordinary stock comparison still checks every pixel without an edge margin or mask.

## A measured two-depth fixture

Use original overlapping quads at world z=+1 and z=−1, a central camera at z=5 looking at zero, and a 40 degree vertical field of view.
Their positive camera depths are 4 and 6; the target plane is D=5.
With 640×360 native samples per eye, f=360/(2*tan(20 degrees)), about 494.55 samples per world unit at depth one.
Configure the private virtual output to 1280 samples wide and limits 36 sunk, 18 popped, expressed at the protocol's reference width of 1920.
At a 640×360 displayed window, the native budgets are 24 and 12.
Infinity limits e*f to 24*5=120, giving predicted left-minus-right disparities +6 and −4 samples for the two quads.
At a 320×180 displayed window with the same 640×360 source grid, the shared feedback conversion gives native budgets 48 and 24.
The native disparities become +12 and −8; the compositor's single resize produces +6 and −4 displayed pixels again.
The measured debug captures match all four displayed predictions with vertical shift zero; at the one-to-one size, both displayed eyes match every native pixel.
These captures test two features at two sizes, not a dense disparity field over arbitrary content.

Match two-edge corners in both horizontal and vertical directions, then run the identical oracle with its captured eyes reversed and require rejection.
Also test depth ordering and the newly visible part of the far surface, which a shifted flat copy cannot reconstruct.
Keep non-stereo UI identical outside the declared model rectangle.
A marked parallel-view PNG uses its registered `sTER` value 1 under the `.pns` name; check chunk CRC, order, padding and unchanged samples instead of creating an unmarked pair or an anaglyph.

In a native host, an unchanged request key does not imply that an outstanding GPU texture verdict has completed.
Continue the existing pending-allocation preparation and private accumulation before treating the view as idle.
Forward allocation failures through the UI's existing GPU report path even when the ordinary viewport is not drawn.
This pending-allocation refinement came from source review and the renderer's existing late-acceptance/rejection tests; it is not a reproduced native driver failure.

Symptom: an idle native view leaves a failed texture upload unreported while the ordinary viewport is absent.
Cause: rejected immediate growth leaves the bound world revision unchanged, so the idle-key check returns before draining the renderer's failure queue.
Fix: forward pending reports immediately after scene sync, before every mailbox or idle return, retaining the post-render report for failures discovered during preparation.
How found: follow the rejected `grow` return and `content_rev` increment, then run the actual native callback with a checked allocation rejection and an already encoded request key.
The regression uses a second private software Vulkan device capped at 64 texels to reject a 128-square growth, while the bound scene remains on its original healthy device.
It expects the existing UI report queue to contain texture set zero; the pre-fix callback leaves it empty.
This is a deterministic validation rejection, not a reproduced driver out-of-memory event.
Do not force memory exhaustion: automatic dimension downscaling can also invalidate an oversized-descriptor fixture, and destroying a wgpu device need not produce a scoped allocation error.
