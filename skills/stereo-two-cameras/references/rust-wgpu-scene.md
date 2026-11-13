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

### Prepare sample rays once per eye

For a CPU ray renderer, prepare the checked inverse eye view-projection once, then unproject its native pixel samples.
`EyeCamera::rays()` returns a prepared `RayGrid`; `RayGrid::ray([x, y])` takes NDC with Y up and depth in 0..1.
Its origin is on the near clipping plane, matching the existing OrbitCamera ray contract, rather than behind that plane at the physical eye.
Retain the renderer's existing supersample positions and trace the original immutable world for every sample.

Trap: unprojection can divide an infinite far point by zero.
For homogeneous near and far points A and B, use origin `A.xyz/A.w` and normalize `B.xyz*A.w - A.xyz*B.w` for the direction.
This also handles `B.w=0`, where B is a direction at infinity.
Reject singular matrices before inverse, and reject nonfinite sample coordinates or directions explicitly.
The cause was identified from the homogeneous far-plane calculation; new tests compare ray-plane intersections with independent perspective and orthographic equations, including an infinite-far projection and a singular matrix with `glam-assert` enabled.
The first test run failed on the absent prepared-ray API; the implementation then passed the same tests.

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

## CPU previews and progressive tracers

Check whether the renderer is actually progressive before introducing temporal state.
MaterialCraft's preview performs finite supersampling: a settled frame uses a 2 by 2 grid, or four primary rays per pixel, and has no cross-frame accumulation.
Its stereo entry point borrows one immutable mesh and BVH, material maps and environment/light set, prepares two `RayGrid` values, then invokes the existing sample loop for each eye.
Compute a camera-relative key light once from the central camera, before the rows and eyes; deriving it from each off-axis centre ray changes the world.
Keep the existing sample positions, tone mapping, clipping and ordinary entry point unchanged.
Count actual completed primary rays and publish the pair only after both eyes finish; cancellation returns no pair.
At 640 by 360 with four samples per pixel, each eye completes 921600 primary rays.
The native proof checked those equal counts and a single immutable scene key before freezing the app and reading the declared buffer.
In original fixture units, at depths 4 and 6 with a target distance of 5, the tested 35 degree camera gave the same predicted +6 and −4 displayed pixels at 640 by 360 and 320 by 180 windows, with zero vertical shift.
The smaller window retained 640 by 360 native samples per eye and measured +12 and −8 before the compositor's resize.
The existing mesh importer first normalizes the fixture into a unit sphere; the camera distance setting and the baseline in native metadata are therefore in those app units.
Scale e, Z and D together when comparing with the original fixture equations, rather than treating a metadata baseline as metres or as the original file's units.
The active preview's key-light strength was its unchanged default zero; a separate renderer regression exercised a nonzero key light and ambient-occlusion rays.
Do not describe that capture as a progressive path-tracing or nonzero-key-light proof.

For an actual progressive tracer, separate immutable scene resources from mutable eye resources.
Geometry, BVH, materials, textures, environment distributions and lights have one owner and one revision for a pair.
Each eye owns its camera uniform, accumulation, sample counter, denoising buffers, temporal history and resolved image.
Advance both eyes to the same sample count under the same scene, time, camera, size and depth revision before presenting their pair.
Discard an obsolete complete pair and invalidate both eye histories together when that revision changes.
Record the completed sample count and scene revision with each capture; matching frame sizes alone does not establish convergence or identity.
Check mono state restoration after tracing, and do not use a shifted flattened result for the other eye.

Source-audit trap: a raster stereo entry point need not cover an application's Rendering mode.
TextureCraft's model companion calls `Renderer::prepare_stereo`, while Rendering mode owns a separate `GpuTracer` and a separate CPU `Tracer`.
The GPU tracer's `pass` documents one call per submission because `queue.write_buffer` rewrites its sole camera uniform.
Two calls on that owner before one submission would not provide independent eye uniforms, accumulation or sample counts.
The spare accumulation buffer is a previous-size allocation cache, not a second eye.
The required fix belongs in that tracer's resource ownership and pair submission boundary, with the same coherent camera inputs, plus an equivalent CPU adapter.
This was found by following `render_mode::TraceCallback::run` into `GpuTracer::pass` and inspecting its fields; the uniform overwrite has not been reproduced as a stereo runtime failure.
Do not mark Rendering mode adapted merely because the raster companion opens beside it.

A native host should retain at most one pending worker or GPU pair.
When an immutable request becomes obsolete, cancel it and wait for acknowledgement before starting another worker, rather than accumulating cancelled workers during rapid edits.
Only hand the native window one complete left-first picture, together with the sample and scene metadata belonging to that picture.
Poll live compositor feedback after the scene settles because resizing changes the native disparity budget even when the chosen source resolution stays fixed.

## Solid backgrounds and model units

Pass the actual perspective environment's horizontal focal coefficient to `Camera::infinity_projection_x`.
Use zero when the renderer paints only a solid background; a constant background is not a perspective plane at infinity.
Budget the visible model depths against the existing target plane and the compositor's limits.
When the entire model lies on that plane and no environment is drawn, keep the central camera with zero baseline.

Symptom: a solid-background model cannot enter the shared camera core without pretending to draw an environment.
Cause: the input validator required a strictly positive infinity coefficient and the baseline solver assumed a nonzero sunk constraint.
Fix: accept a finite nonnegative coefficient, apply only nonzero disparity constraints, and keep zero baseline when neither side constrains depth.
How found: a regression with no environment was rejected by the old validator; the same test now predicts +12 and -8 pixels at depths 4 and 6, checks the flat target-plane case, and still rejects negative/nonfinite environment inputs.
The existing perspective-environment and orthographic tests retain their earlier predictions.

For an f64 CAD or PRC rasterizer using an f32 camera core, express the shared camera in its local basis and measure distances in the existing positive eye-to-target distance.
Keep original world vertices and the ordinary f64 raster projection; restore physical eye offsets along the original right vector and apply the shared core's off-axis projection delta.
Do not narrow a large world-space origin to f32 or point each eye at the unchanged world target.
Expand normalized depth rounding outward, and include the near clipping plane when geometry crosses it, so the camera budget cannot miss newly clipped corners.
Keep the headlight at the central camera while geometric eyes, visibility/depth targets and resolved images are private.
These are renderer bridge requirements; the PRC adapter still needs its own tests and native capture before it can be called proved.

Symptom: the orthographic camera's analytic baseline is correct, but the rendered disparities do not match it.
Cause: the match arm shadows the render grid's pixel height with the world's orthographic height when restoring the projection coefficient.
Fix: give the world height its own name and retain the original pixel aspect and focal scale.
How found: render two colored finite-depth surfaces, compare their actual edge runs to +12 and −12 pixels, and check the baseline equation separately.

Symptom: an orthographic model very close to the eye gets a zero baseline.
Cause: its depth scan applies the perspective near-plane threshold even though the ordinary orthographic rasterizer does not clip there.
Fix: admit representable positive orthographic depths while retaining perspective clipping and outward rounding.
How found: put all vertices at a positive depth below the perspective threshold and require a finite positive baseline before checking the complete raster suite.
