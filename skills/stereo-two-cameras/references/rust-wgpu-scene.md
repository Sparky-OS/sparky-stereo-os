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

Source-audit distinction: hiding an environment backdrop does not disable image-based material lighting.
MaterialCraft's `show_env` selects the miss image; its PBR shader still samples `Lighting::specular` with the reflected view direction.
The current adapter retains a conservative infinity envelope for that renderer; its measured alpha/geometry fixture is not a maximum-disparity claim for every preview mode.
Also read the camera constructor actually used by the preview: its FOV is 35 degrees even though the generic `OrbitCamera::default` uses 40.
This distinction was found by following the caller into `preview::camera`, `Settings::default`, the miss selection and the specular lookup, rather than treating the shared type's defaults as the application's defaults.

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
The audit followed `render_mode::TraceCallback::run` into `GpuTracer::pass`; a subsequent real software-GPU diagnostic queued two different cameras on that owner before submitting and found that the first pass used the second camera and sample index.
This reproduces misuse beyond the documented once-per-submission contract, not a failure of the original ordinary caller.
Give each eye a private tracer uniform, then require a queued pair's raw accumulation and resolved denoised pixels to equal independently submitted eye controls.
Do not mark Rendering mode adapted merely because the raster companion opens beside it.

Symptom: a retained white scene turns black after a different view uploads a new black material at the same texture dimensions.
Cause: an `Arc` shares the material wrapper, but a same-size reuse path still copies new pixels into its shared GPU textures.
Fix: reuse those textures only when their material owner is unique; otherwise allocate a new immutable map set and share that set with the new pair.
How found: retain the old scene, replace the active material, trace both, and check the old white scene's actual accumulation; removing only the ownership guard makes that regression fail.
A pointer-sharing assertion alone cannot detect a texture's contents changing.

Symptom: two CPU sample counters are equal, but the returned image already contains some rows from the next sample.
Cause: counters advance only after a full pass, while row-sliced accumulation mutates pixels before then.
Fix: track the in-progress pair boundary as well as N and refuse publication while either next pass is incomplete.
How found: after one complete pair, advance only three rows, require image publication to fail despite counters still reading one and one, then finish the pass and compare both complete images with the ordinary zero-budget render.

Use stochastic lighting for a convergence witness, separately from the emissive geometry fixture that makes visibility and disparity easy to measure.
Save each eye's linear estimator and completed N before tone mapping; compare it with that same eye and backend at a stated longer reference N.
A finite reference is not ground truth, and CPU/GPU floating-point estimators need not match bit for bit.
One measured procedural lit sphere at 64 by 48, three bounces and no denoising completed 1, 8, 32 and 256 samples in both eyes on CPU and software GPU.
Each of its four backend/eye RMSE sequences decreased against its own 256-sample reference; the CPU left eye went from 0.3137 at one sample to 0.0647 at 32.
Those renderer outputs establish this convergence case, not a native-window capture; the companion still needs its own source, sample metadata, geometry and stock controls.

A native host should retain at most one pending worker or GPU pair.
When an immutable request becomes obsolete, cancel it and wait for acknowledgement before starting another worker, rather than accumulating cancelled workers during rapid edits.
Only hand the native window one complete left-first picture, together with the sample and scene metadata belonging to that picture.
Poll live compositor feedback after the scene settles because resizing changes the native disparity budget even when the chosen source resolution stays fixed.

A native progressive TextureCraft capture used the existing 40 degree camera, target distance 5 and model depths 4 and 6.
Here d is the left image x coordinate minus the right image x coordinate.
With a perspective environment and a 24/12 native-pixel budget, the infinity constraint gives e*f=120, so d(Z)=e*f*(1/Z-1/5) predicts +6 and -4 pixels.
At a 320 by 180 window with the chosen 640 by 360 source grid retained, the 48/24 native budget gives e*f=240 and +12/-8 native pixels; one compositor resize restores +6/-4 displayed pixels.
Both CPU and software GPU measured these values, zero vertical shift and zero differences outside the content, and the unchanged geometry oracle rejected reversed eyes.
Each completed capture recorded four samples and 921600 primary rays per eye under one scene revision; the 640-window native and displayed pixels matched exactly.
This is a two-feature, two-size perspective case, not dense accuracy evidence for every material or orthographic tracing.

Symptom: replacing an environment image under the same resource name leaves the paired scene cached.
Cause: an outer scene cache can stop before the ordinary renderer's decoded-image identity check is reached.
Fix: retain the source image and compare its Arc identity as well as the ordinary composition key; give a replacement a new source generation and invalidate both histories.
How found: replace red environment samples with blue under one name, remove only the image-identity guard, and observe the stale-scene assertion fail before restoring it.
Holding the old source also prevents a later allocation from reusing its address; release it when the replacement is accepted.

Do not let a control probe supply the wakeup it is meant to verify.
For an idle resize witness, finish tracing, resize through the compositor, then freeze and capture both eyes before any new ui.inspect request.
The tested CPU companion retains the existing 16ms native-feedback poll even after its worker completes; the GPU path keeps the same polling boundary.
The 320-window CPU and GPU witnesses both consumed the new budget without a control request, then separately verified the four-sample metadata.

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
Keep original world vertices and the ordinary f64 raster projection.
Apply the physical eye offset to camera-space x after the original central view transform and before clipping or perspective division, then apply the shared core's off-axis projection delta.
Do not narrow a large world-space origin to f32 or point each eye at the unchanged world target.
Expand normalized depth rounding outward, and include the near clipping plane when geometry crosses it, so the camera budget cannot miss newly clipped corners.
Keep the headlight at the central camera while geometric eyes, visibility/depth targets and resolved images are private.
These are renderer bridge requirements; each adapter must carry its own raster regressions and native capture, rather than borrowing a core-only result.

Symptom: the orthographic camera's analytic baseline is correct, but the rendered disparities do not match it.
Cause: the match arm shadows the render grid's pixel height with the world's orthographic height when restoring the projection coefficient.
Fix: give the world height its own name and retain the original pixel aspect and focal scale.
How found: render two colored finite-depth surfaces, compare their actual edge runs to +12 and −12 pixels, and check the baseline equation separately.

Symptom: an orthographic model very close to the eye gets a zero baseline.
Cause: its depth scan applies the perspective near-plane threshold even though the ordinary orthographic rasterizer does not clip there.
Fix: admit representable positive orthographic depths while retaining perspective clipping and outward rounding.
How found: put all vertices at a positive depth below the perspective threshold and require a finite positive baseline before checking the complete raster suite.

Symptom: a stereo scene changes pixels when its world origin is moved far from zero, even though its represented relative geometry is unchanged.
Cause: adding a small eye offset to an absolute f64 eye coordinate rounds the offset before vertices enter view space.
Fix: implement the parallel view translation in local camera coordinates; keep the central eye for headlight shading.
How found: a world at x=1e15 failed an all-pixel comparison with a rebased copy of those same represented vertices; the local translation restores equivalence.
Build the reference from the already represented points, because adding the large origin may itself quantize the input geometry.

Symptom: a complete pair reports an infinite physical baseline, or silently turns a nonzero normalized baseline into a flat pair.
Cause: multiplying the normalized camera offset by an extreme f64 model scale can overflow or underflow even when both inputs are finite.
Fix: refuse unrepresentable physical baselines and eye offsets before drawing or publishing the pair.
How found: the overflow regression accepted an infinite baseline; a separate tiny-scale regression first proved the ordinary scene visible, then found that the stereo call accepted an underflowed baseline.
Zero budget retains the exact ordinary path.

## A finite f64 rasterizer at the native window

For an embedded PRC model, retain a cheap immutable working-file snapshot keyed by document ID, edit generation and page.
Parse the document, decompress its model stream and assemble the world on the worker, not during UI painting.
Both geometric eyes borrow that same placed mesh set and central headlight; each owns its depth target and image.
Publish a single complete picture and the metadata belonging to it, never a poster raster or two independent document reads.
This renderer completes one raster pass per eye and has no temporal accumulation; record one and one, rather than inventing progressive sample counters.

A measured original PRC fixture has camera depths 4 and 6, target distance 5 and vertical field of view 30 degrees.
For its solid background use zero infinity coefficient; the popped budget of 12 native pixels gives e*f=240 and predicted disparities +12 and -8.
The actual native application and compositor measured those values at a 640 by 360 window, with zero vertical shift and every native/display sample identical.
At a 320 by 180 window the selected source grid stayed 640 by 360 per eye, the native budget doubled and the native disparities became +24 and -16, while the displayed values stayed +12 and -8.
The identical block-matching oracle rejected reversed eyes, and the far-surface disocclusion remained visible.
These are two measured features at two sizes, not a dense accuracy claim for every model.
Keep the ordinary renderer entry point and headless tool defaults, including its per-eye grid and size bound, unless the person chooses another resolution.
The capture must open the actual original PDF and parse its PRC annotation through the production loader; rendering only directly constructed test meshes does not verify that path.

## Orthographic trace backgrounds and hardware witnesses

Derive the prediction from the actual render mode's background projection as well as its model camera.
An orthographic path tracer has parallel miss rays; it does not inherit a painting renderer's perspective sky constraint.
For orthographic geometry, use `disparity = focal * baseline * (1 - Z/C)`.
Solve both compositor inequalities over the scene's near and far depths before making the capture.

Symptom: an orthographic trace measures twice the disparity expected by a previously passing painting-view oracle.
Cause: the oracle reused the painting view's perspective environment constraint, while `TracePairFrame::cameras` correctly supplies zero infinity coefficient for orthographic miss rays.
Fix: keep the production camera unchanged and derive a fresh prediction from the trace mode's actual depth range and constraints.
How found: both processor and GPU captures measured 12 pixels where the inherited oracle expected 6; reading the actual trace camera and the common solver explained the factor of two.
Fresh captures, with the independent prediction recorded first, then measured +12 and -12 displayed pixels at depths 3.75 and 6.25 about target distance 5.
At a 640 by 360 window the native grid measured the same values; at a 320 by 180 window the selected 640 by 360 grid measured +24 and -24 before compositor scaling.
Both tracers completed four samples per eye, vertical disparity was zero, the reversed-eye control failed, and the eyes outside the stereo window were identical.
These are two measured features, not a dense accuracy claim.

For hardware proofs, restrict the client to the intended Vulkan ICD and check the actual client process's loaded driver and open device nodes.
Retain the enumerated device information alongside the native pair and the completed sample counters.
An available adapter alone does not establish which driver rendered the client.
The processor and GPU trace witnesses at both window sizes also passed on AMD and NVIDIA hardware with their existing perspective +6/-4 displayed prediction.
The hardware selection belongs to the private proof harness, not to the program's stereo controls.

Symptom: the launcher cannot stat an authorized render node before starting its container.
Cause: the tool's own device namespace does not expose the daemon host's render node.
Fix: use the already authorized device and group, verify their identity inside the isolated container, and inspect the actual client descriptors there.
How found: host-side stat failed before rendering; the in-container check succeeded and the actual client mapped the selected hardware ICD with the matching device open.
Never replace that check by a software fallback and call it a hardware pass.

## Root shutter samples through collapsed instances

An evaluated composition camera needs the root frame's camera identity and the root shutter sample time as separate inputs.
Carry that time explicitly through collapsed instances, retaining their instance transforms and property overrides.
Map sample time down through stretch and remapping; do not recover root time by subtracting a nested time.
Keep an uncollapsed composition's own camera boundary.
Prepare the composition, lights and environment once for a sample, then make its two parallel eye views with private effects and histories.

Symptom: a collapsed identity composition under a moving root camera renders like a held camera during motion blur.
Cause: the Classic path's shutter-camera helper returns the cached `Collapse3d.cam` for every sample.
Candidate repair: evaluate the selected root camera at each explicit root shutter time and carry the corresponding placement through the complete collapsed-instance chain.
How found: the retained monoscopic regression differs from the direct moving-camera world in 160 of 20,000 pixels, with maximum alpha difference about 0.361111; its held-camera control matches the collapsed frame exactly.
This is a prerequisite failure, not a stereo proof.
[EffectCraft #3623](https://github.com/storytold/effectcraft/pull/3623) fixes the distinct first-frame camera-identity problem; retain zorianflorian's original commit when it is needed, rather than freezing the animated camera to hide the collapsed-instance defect.
The candidate passed 88 CPU controls including direct, nested, remapped, mixed card/mesh, held-view, blur-switch and uncollapsed-boundary cases.
The corrected initial runtime test set had 21 passes and 47 failures before the repair.
These component results do not establish the application's full gate or a native stereo adapter.
The subsequent root-owner subject passed its complete nine-stage application gate: 6,677 test passes, 46 skipped or ignored, and 32 WASM crates checked.
That checkpoint precedes its separate shared-revision receiver migration; it is still not a native stereo adapter proof.

### Shutter lights must reach the GPU with their geometry sample

Symptom: the CPU follows an animated root light during motion blur, while the Classic GPU keeps the frame-time brightness.
Cause: a prepared run carried several geometry samples but exported only one frame-time light array to the shader.
Candidate fix: retain one immutable light set per root sample and give every geometry record its light-range offset and count in one bounded storage pool.
Keep held geometry on the original frame-time set.
How found: a tent-shaped ambient-intensity curve inside the shutter separates a sampled average from the frame value; a symmetric linear curve would not.
Three strict Vulkan controls, for direct and one/two-level collapsed scenes, failed before the change with 8,000 or 16,000 differing pixels and maximum channel difference 0.19047618, then all three passed.
The changed CPU/GPU geometry layout must agree in stride and light-range fields; updating just the CPU record leaves a different shader ABI.
Require the actual adapter and kernel for these controls, so a missing software Vulkan adapter cannot turn the test into a successful early return.

### The root blur switch owns the sample count

Symptom: turning off the root composition's motion blur still blurs a collapsed child's camera.
Cause: choosing root shutter timing while retaining the child's enabled flag leaves multiple geometry samples active.
Candidate fix: derive both the enabled flag and sample count from the root shutter owner, retaining the existing render switch and inherited layer limits.
How found: render-off, root-off and uncollapsed controls expanded the CPU matrix to 88 cases; six root-off cases failed before the enabled flag was carried, then all 88 passed.
Retain an observed negative in which enabling blur changes the picture, so equality is not explained by an invisible or stationary fixture.


## Composition identity owns the stereo camera boundary

Carry the selected root composition identity alongside its sample clock.
Evaluate the root camera at each shutter sample, gather actual world-plane and mesh bounds before culling, and derive parallel views from the complete envelope.
Keep an authored uncollapsed precomposition flat under its own camera, including any collapsed worlds inside that boundary.
Use a point of interest only while that camera actually uses it; a one-node camera retains its image plane.
Sort sample receipts by their exact time before comparing complete eye identities.

Symptom: an inactive Point of Interest property changes a one-node camera's stereo zero plane while ordinary pixels stay unchanged.
Cause: testing whether the property exists does not establish that the camera uses it.
Fix: reuse the camera engine's two-node predicate; retain the image plane otherwise.
How found: two cameras with identical ordinary projections and different inactive target values produced different stereo pixels; the regression failed before the predicate was applied and passed afterwards.

Symptom: an authored flat precomposition changes the root near-depth ratio from 0.8 to 0.25 and gains unintended internal disparity.
Cause: recursion depth and the mere presence of a collapsed instance cannot distinguish the root world from a collapsed world behind an uncollapsed boundary.
Fix: key eye projection, geometry observations, infinity and camera-space effect handling by root composition identity.
How found: a blue internal world inside a collapsed instance, itself behind an ordinary flat precomposition, contaminated the observed root envelope; the corrected control retains the 0.8/1.2 root range and identical blue positions in both eyes.
These two runtime regressions failed together, then the expanded renderer library passed 517 tests with one ignored and strict Clippy passed.
Native presentation remains a separate proof.

Symptom: a finite singular or sheared composition view is accepted by an adapter that canonicalizes only its camera-relative ratios.
Cause: canonicalization hides the malformed original world-to-camera basis from the shared solver.
Fix: validate the original finite rigid basis, handedness, affine row and physical eye consistency before making either view.
How found: independent projection/disparity, zero-budget, invalid-depth and infinity tests passed while the finite-malformed-view regression failed; validating the original basis made all five pass.

Symptom: a camera-aware effect returns a plausible flat picture even though its internal 3D geometry never reached the pair depth envelope.
Cause: an effect-host API may expose only a projection and light while the effect privately rasterizes its own geometry.
Fix: refuse that stereo result explicitly until the owning effect engine exports its geometry envelope and consumes the evaluated eye projection, with private history.
Keep ordinary rendering available and respect authored flat precomposition boundaries.
How found: a Card Dance Comp Camera fixture produced ordinary pixels and the first pair API incorrectly returned success; a negative control failed before the refusal and passed afterwards.
A refusal is not evidence that the effect's stereo renderer has been implemented.


## Freeze decoded resources for the complete pair

An immutable project is not sufficient when a footage source decodes or replaces its resources on demand.
For one pair, memoize decoded float/byte frames, vector rasters, models, auxiliary channels and audio by the complete query identity, then reuse those immutable values during preparation and both eye renders.
Include the footage descriptor, proxy interpretation, exact time, dimensions and curve in keys where those affect decoding.
Keep processed effects, accumulations and histories private to each eye; discard the query snapshot after the complete pair.
Forward cancellation and refuse a missing required frame or model, while retaining optional negative-query results.

Symptom: the same project and exact timeline time produce red content in one eye and blue content in the other.
Cause: a decoded-resource provider returns a different frame on successive identical queries; an immutable project borrow does not freeze that provider.
Fix: cache the original immutable decoded result once per complete query across both eye renderers and the bounds preparation.
How found: an alternating source made the independent two-eye equality test fail; the frozen-source implementation passed with exactly one original frame read.

Symptom: an unavailable required image returns a successful blank stereo pair.
Cause: memoizing `None` preserves query identity but leaves the renderer's lenient missing-resource behavior unchanged.
Fix: retain the original source problem or report the required input as unavailable before publishing either eye.
How found: a separate negative regression required an error and failed before the explicit check; the corrected renderer library passed 523 tests with one ignored and strict Clippy.
The complete application gate then passed 6,705 tests, with 46 skipped or ignored and 32 WASM crates checked.
Those are source-gate results; they do not establish native presentation, and query counters are not scene hashes or path-tracing sample counters.


### Preserve the ordinary background at the native pair boundary

A transparent composition frame is not yet the ordinary opaque output.
Reuse the document's existing background conversion separately on each real eye, then pack its rows without resampling.
Capture the background in the same immutable world snapshot and include document edits in stale-work identity.

Symptom: flat content in the native pair is black where ordinary output has the authored non-black background.
Cause: the new companion calls `to_rgba8_over([0; 3])`, while the existing ordinary exporter composites over `comp.background`.
Fix: pass the immutable document background through the native packer to both conversions.
How found: a runtime test against the actual ordinary session exporter failed with black versus RGB128/80/32; after using the same background, all nine focused native-control tests passed.
Use the engine's actual clamped dimensions in that reference; the first attempted assertion also assumed a smaller stage than the document permits.
This focused result precedes the full application gate and compositor proofs.


## Native composition shutter witness

For Effect's composition-pixel camera, predict `d = b * f * (1/Z - 1/C)` with `f = zoom * native_eye_width / composition_width`.
Read the actual compositor budget and choose the common baseline before reading captured pixels.
A 200 by 100 authored composition, 50mm camera with C=200*50/36, native640 by320 eyes and cards at0.8C/1.2C measured+12/-8pixels in a640 by320 window.
After resizing the client to320 by160, the native grid stayed640 by320 and measured+24/-16; the compositor scaled once.
Classic and Advanced mixed mesh/card worlds passed, including two collapsed instance levels; a separate pixel count establishes that the blue real mesh is actually visible in each eye.
Those are two geometric features and a mesh-presence control, not a dense shading or depth-accuracy claim.

Decode the timeline identity from each eye's camera-dependent feature positions, independently of the UI frame selector.
Frames13,15and17 matched in both eyes; all seven root shutter times had distinct central camera positions and matching eye sample records.
Disable root blur through the existing command and require a new one-sample pair whose actual pixels differ in both eyes; matching seven-sample metadata alone cannot prove visible blur.
The six native witnesses had zero vertical disparity, failing reversed-eye controls and zero differences outside the declared area.
Four full-size native/display comparisons covered1,638,400pixels with zero differences; the six native readbacks contained2,457,600pixels, which is a different scope.
The authored flat control matched ordinary output in40,000native pixels; an independent stock comparison is still a separate requirement.
