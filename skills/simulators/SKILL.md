---
name: simulators
description: >-
  Diagnose FlightGear, TORCS and Speed Dreams stereo through OSG/plib, including UI, per-eye resources and OpenXR lifecycle.
---

# Open flight and racing simulators

## Working recipe

1. Choose one simulator and failing stage: drawable creation, cameras, render resources, UI/input, lifecycle or packaging.
2. Record versions and use the corresponding section below. Keep desktop stereo and XR as separate test dimensions; start with a labelled control.
3. Return the failing/fixed witness, installed executable hash and unaffected 2D result. Older diagnostic candidates below are not current release approvals.

Checked 2026-10-16 against FlightGear 2024.1.5, OpenSceneGraph 3.6.5, plib 1.8.5, TORCS 1.3.7 and Speed Dreams 2.4.2.
Recheck newer engine code and package versions before carrying a patch forward.
Load [sparky-stereo](../sparky-stereo/SKILL.md) first, then [native-linux](../native-linux/SKILL.md), [stereo-two-cameras](../stereo-two-cameras/SKILL.md) and [stereo-proof-rig](../stereo-proof-rig/SKILL.md).
For OpenXR, also load [vr-to-3d](../vr-to-3d/SKILL.md).

## Contract and ownership

Render one world with two parallel off-axis cameras and send declared full side by side to Stereo KWin.
Output-specific settings belong to KWin.
Keep ordinary 2D UI on an undeclared surface; check exact equality in both screen eyes, including overlap and input.
Implement shared behavior in OpenSceneGraph or plib before considering application-specific code.
The published fork branches are [OpenSceneGraph](https://github.com/Sparky-OS/OpenSceneGraph/tree/stereo3d), [plib](https://github.com/Sparky-OS/plib/tree/stereo3d), [TORCS](https://github.com/Sparky-OS/torcs/tree/stereo3d) and [Speed Dreams](https://github.com/Sparky-OS/speed-dreams-code/tree/stereo3d).

Use a private container session and installed packages, with no build-tree mount, private library prefix or inherited host display.
The latest installed-package and software OpenXR checks used Mesa 26.1.6-1+stereo3d12, KWin 4:6.7.4-2+stereo3d22 and Xwayland GLX.
Native OSG Wayland support was not merged at this check.
A Flatpak does not establish behavior with the edition's Mesa.

## FlightGear and the GUI camera

In the unmodified release, `/sim/rendering/osg-displaysettings/stereo-mode` defaults to OFF and overrides the OSG stereo environment.
Selecting QUAD_BUFFER there still does not request a stereo drawable in Debian's unmodified build.
Trace `src/Viewer/WindowBuilder.cxx`: `GraphicsContext::Traits::quadBufferStereo` must be requested before choosing the GLX framebuffer configuration.
Read the startup property directly at that point; FlightGear connects the global DisplaySettings properties after window creation.
Do not report an OSG environment setting as proof of an actual stereo FBConfig.

A diagnostic FBConfig request showed that the existing Compositor can produce depth-dependent desktop stereo without a rewrite on this stack.
At 800x600 per eye, separation 0.05, screen distance 0.5 and horizontal FOV 73.6 degrees, the predicted R-minus-L infinity disparity is +53.4691 pixels.
The measured distant scenery was +53.3237 pixels, with all 55 accepted matches within one pixel and vertical minimum zero.
These are diagnostic measurements, not a shipped native FlightGear desktop fix.

`CameraGroup::buildGUICamera` inherits global stereo settings unless it has its own `osg::DisplaySettings`.
The PUI quad is pixel-coordinate orthographic geometry at z=1, so stereo transforms move glyph sampling by a fraction of a pixel.
The measured menu had 2,250 differing pixels despite best integer alignment at zero.
Camera-local mono settings eliminated all differences; keeping stereo enabled with local separation zero did too, isolating the transform from repeated blending.
These were diagnostic controls, not an accepted application fix.
An independent source review found stock-OSG buffer-state dependencies and split-mode regressions in a permanently mono GUI camera.
Its replacement keeps native eye routing and viewports while returning unchanged GUI and splash matrices from SceneView callbacks; the replacement preserves those routes; its first private-eye helper was subsequently rejected for incomplete pass ownership and eye masks.
World disparity remained unchanged.
This is why checking only whole-pixel UI movement misses a real stereo defect.

FlightGear has a generative-AI contribution policy.
Keep exact diffs and runtime evidence for the authorized independent line review before submission; for this release, Daniel asked for an independent line review by a second AI model (GPT-6-Astra), and it reviewed four rounds before approving.
Local review branches and package candidates are authorized for that work; an interposer remains diagnostic apparatus.
The release replacement covers the early drawable request and unchanged screen-space matrices with both eye routes retained.
A permanently mono GUI camera is a rejected diagnostic, because it breaks stock-OSG routing and split layouts.
A complete contract implementation also separates the world child surface from the ordinary UI parent, with window creation in WindowBuilder/WindowSystemAdapter and camera/input work in CameraGroup/FGEventHandler.
Test child-only stereo declaration, parent UI equality, resizing, hit testing, dialogs and overlapping windows.
Local native package proofs are authorized for this review; publication still waits for the required independent review, and the physical-display run is separate.

## Native FlightGear replacement and offscreen resources

Request the configured stereo visual before the existing property tie runs.
An explicit property has precedence over OSG's environment, including OFF and invalid spellings.
A valueless property may preserve OSG_STEREO=ON plus OSG_STEREO_MODE=QUAD_BUFFER.
Copy the main window's requested capability into Sview windows, and query actual GL_STEREO on each drawable.
Reject a mono-created window's later QUAD_BUFFER transition with the restart choice; do not describe that as automatic fallback.
Keep GUI and splash eye routing active and return unchanged screen-space projection/view matrices from SceneView's four stereo-matrix callbacks.
This preserves buffer and viewport routing, runtime modes and split layouts.
Camera-local mono or zero-separation settings are diagnostic controls, not the final general solution.
An opaque marker must match exactly; translucent pixels can differ where they blend over different world images.
The native two-commit replacement measures panel -16.635 px, far +28.975 px and 0 menu/opaque-marker differing pixels on stock OSG.
The release source adds separate offscreen, input, fullscreen and XR lifecycle corrections below; each needs its own causal controls.

Test a color-RTT pipeline and a copying fullscreen pass separately.
The two-commit control gives both panel and far approximately -52 px in that test, exposing a flat shared image.
The initial private-eye follow-up improved color history but was rejected for incomplete pass ownership; a complete fix belongs in SimGear's Compositor, with FlightGear selecting OSG's existing off-axis matrices once.
Its first experiment restores panel -16.648 px and far +28.975 px, with far error 0.02235 px and zero vertical residual.
Keep shader/history buffers private to each eye, route final window passes to their eye buffer, and suppress a second SceneView stereo transform.
Leave XR's existing per-view Compositors with osgXR, and test mode changes, reset, resize, threaded rendering and extra windows.
A frozen-history witness followed by a live view change distinguishes stored eye images from merely different current frames.
Do not infer complete ownership from a passing color-history image.
A depth-only pipeline with CSM still needs shared monoscopic light passes, resources covering both eye frusta and separate eye-space shadow lookup transforms.
Classify shared writer outputs explicitly, retain eye-private screen color/depth/history, and preserve compute GL_NONE targets.
Shared shader view/projection/history inputs must use the centre camera, not an alias of one eye's uniform group.
Check real dispatch counters, actual light traversals, nonempty shadow depth, matrices and targets against an old implementation.
Private mono cameras must promote the effective left/right traversal mask, then refresh it after world-mask changes, render conditions and OFF/back.
Use left-only red, right-only blue and shared green geometry as visible witnesses.
The fourth-review SDK controls pass these checks; the complete release runtime matrix remains subject to independent review.

OSG 3.6.5's DisplaySettings copy routine reads its destination shader hint instead of the source.
A zero-filled placement copy and assignment from a different hint reproduce expected=3, copy=0, assignment=2.
The owning correction is setShaderHint(vs._shaderHint).
The +stereo3d3 installed package passes the same test with expected=3, copy=3, assignment=3.
Never use a new DisplaySettings copy to hide a GUI symptom on an unfixed stock library.

## Speed Dreams and OSG state

Use osggraph explicitly and the `best` video mode for the measured v2.4.2 route.
Request stereo with the application's `stereo-vision=yes` setting and OSG's `OSG_STEREO=ON OSG_STEREO_MODE=QUAD_BUFFER`.
Inspect the actual GL_STEREO capability and saved in-test settings; a menu's yes value alone proves neither.
`src/libs/tgfclient/glfeatures.cpp` previously hardcoded stereo unsupported and lost the best-mode request through restart/fallback.
Keep the actual accepted fallback choice and persist the tested stereo setting.

OSG `src/osgUtil/SceneView.cpp` previously left GL_BACK_RIGHT selected after the QUAD_BUFFER draw.
A legacy prompt drawn afterward appeared in only the right eye.
Save and restore both entry draw and read buffer selections around the two eye draws.
Guard the saved desktop buffer enums and the glDrawBuffer/glReadBuffer calls for all GLES1/GLES2/GLES3 profiles; GLES has no glDrawBuffer.
Retain desktop GL3 support rather than placing this state restoration behind a fixed-function-only condition.
Compile real profile headers and retain a failing unguarded GLES control.

A new Speed Dreams package needs a per-asset copyright inventory of its data submodule and bundled libraries.
Do not assign licences by a similarly named font or a later import.
Five v2.4.2 GLFs (b5, b6, b7, digital and fragile) are byte-identical to Debian torcs-data 1.3.7+dfsg-5 and covered by its GPL-2+ wildcard notice.
The other five Droid Sans, Jura and Liberation Sans GLFs remain with Daniel and upstream for original font records before the held package is published.
That release gate does not stop independent engine or runtime work.

## TORCS and plib

The native plib path is opt-in:

```sh
PLIB_SSG_STEREO=ON PLIB_SSG_EYE_SEPARATION=0.065 PLIB_SSG_CONVERGENCE=10 torcs
```

TORCS' shared graphics startup requests a stereo drawable for that option.
The plib ssg engine draws the same scene twice, then restores its centre camera, frustum and buffer state.
Never combine these native cameras with the GL stereo camera layer; doing so would apply stereo twice.
An independent 5,000-point pinhole oracle must check both draws, disparity sign, zero vertical error and restored context, and fail with pristine plib.
The independent stereo-off comparison must remain exactly identical to the pristine program.

## Per-view depth defaults

Use camera separation 0.065 m, with a separate screen plane for cockpit and chase.
The measured candidates use FlightGear cockpit 1.2 m, TORCS driver 1.8 m, Speed Dreams cockpit 0.7 m, and chase 2 m for all three.
These are model-dependent proposed defaults, not a guarantee of human comfort on a particular screen.
At 800 pixels per eye FlightGear's diagnostic panel median is -16.635 px and yoke -25.199 px, with the largest sampled pop -58.921 px (7.365%).
At 640 pixels per eye TORCS' native dashboard median is -10.222 px and the sampled whole-scene pop bound -39.983 px (6.247%).
At 800 pixels per eye Speed Dreams' native panel median is -12.009 px, wheel -51.316 px and wheel-region pop bound -67.070 px (8.384%).
All three chase fixtures keep their sampled vehicle and nearest world foreground behind the screen with a near-camera plane.
Record the nearest sampled world object rather than counting zero-disparity HUD text as foreground scenery.

FlightGear's edition Nasal module uses `/sim/stereo/cockpit-distance-m`, `chase-distance-m` and `eye-separation-m`.
A view's `config/stereo-screen-distance-m` overrides the corresponding global plane.
Setting `/sim/stereo/defaults-enabled=false` leaves the existing OSG distance properties under manual control.
These settings measurements still use a labelled drawable diagnostic until the independent native patch matrix passes.

For TORCS, use the Graphic settings `stereo cockpit convergence` and `stereo chase convergence`.
The F2 group begins with two external cameras; actual driver/interior cameras have IDs >= 2, so classifying the whole F2 list as cockpit is wrong.
Pass the selected convergence through the ABI-preserving ssgCullAndDraw overload; keep the original entry point and explicit PLIB_SSG_CONVERGENCE override.
Do not set that global override when testing per-camera defaults.
Its radius-one sky needs the infinity overload: suppress eye translations and scale the projection shift by tan(backgroundFov/2)/tan(worldFov/2).
The real driver sky then matches analytic infinity within 0.019 px; a sky ROI through the flat mirror gives a false zero and must be rejected.

Speed Dreams exposes the same Graphic convergence settings plus `stereo eye separation`.
Only the first four cameras in F2 list 0 are cockpit cameras; the remaining cameras are external.
Attach a newly configured camera-local DisplaySettings rather than OSG View fusion distance, which also scales the effective eye separation.
Force bundled FreeSOLID in the Debian recipe with CMAKE_DISABLE_FIND_PACKAGE_SOLID=ON so an older installed libsolid cannot silently become an undeclared external dependency.

Package installation through a Docker proxy is asynchronous even when docker exec returns 0.
Wait for an in-container result marker and assert the system defaults before starting a fresh private profile.
A package-version query after a capture cannot prove which defaults the application copied before installation finished.
The retained rejected +4 runs fail their infinity predictions by about 15 px and 6.5 px; the gated reruns pass.
Retain no-interposer CPU and GPU captures, complete immutable source packages and zero-pixel stereo-off controls.

## OpenXR spectator route

Enable the existing bundled osgXR through Debian packaging with `libopenxr-dev`, `-DENABLE_VR=ON` and `-DSYSTEM_OSGXR=OFF`.
Preserve the existing Debian flags and tests, the source package and the bundled LGPL/Apache notices.
The original OpenXR packaging-only rebuild passed all 24 Debian CTest tests without changing FlightGear C++.
The later native desktop candidate changes FlightGear C++ and must carry its separate authorized review and runtime gate record.
Build each architecture from the same .dsc; do not generate a different source package or changelog for each architecture.

Reuse the edition's Monado spectator implementation rather than inventing an application mirror converter.
Its test settings are:

```sh
SIMULATED_ENABLE=1 XRT_WINDOW_PEEK=both \
XRT_COMPOSITOR_SCALE_PERCENTAGE=100 SDL_VIDEODRIVER=x11 \
VK_DRIVER_FILES=/usr/share/vulkan/icd.d/lvp_icd.json monado-service
```

Run it inside the private headless KWin session, then start `fgfs --enable-vr` with desktop OSG stereo OFF and `/sim/vr/mirror-enabled=false`.
Pin Monado to lavapipe in this rig; the existing runtime proof records an AMD compute-compositor failure.
The simulated HMD is a graphics runtime with actual images.
XR_MND_headless supplies no image proof.
Test an independent red-left/blue-right client and the SDK's OpenGL hello_xr control before assigning a failure to FlightGear.
Select and activate the sole X11 window with `_KDE_NET_WM_STEREO_CONTENT=3`; Monado's ordinary main window is a different 2D surface.
The measured spectator target has 640x720 per eye and correct ordering, with zero differences outside the colour-control window.

A spectator route preserves headset cameras and may contain a floating VR UI.
A 3D-display Play driver still needs display-derived off-axis FOV, ordinary game-controlled view, screen-plane UI/input and exit restoration as vr-to-3d specifies.
Do not describe a simulated-headset spectator run as a completed Play driver or a physical-TV test.
For stationary geometry, the existing Monado Qwerty driver works with `QWERTY_ENABLE=1 SIMULATED_ENABLE=0`; send no headset movement input.
The independent hello_xr control must first confirm fixed poses.
FlightGear's installed-package proof then had 40/40 far matches within one pixel of zero on Mesa +stereo3d12, cockpit disparity about -28.8 pixels, vertical minima zero, and 0 differing pixels outside the stereo window.
The moving simulated driver had nonzero near vertical residuals, so it was not used to assert stationary geometry.
In this fixture, `QT_XCB_NO_XI2=1` avoided a Qt 6.11.2 synthetic-device crash, and the existing `/sim/startup/splash-screen=false` option removed a persistent loading overlay.
Record those settings and the fixture's missing-model warnings; they do not prove normal loading, performance or flight readiness.
Earlier +stereo3d11 property queries timed out; the +stereo3d12 query confirms built/present/running true and the Monado Qwerty HMD.
A property query supplements actual OpenXR submissions and captures; state alone is not stereo proof.
The optional GPU OpenGL control on Mesa +stereo3d11 failed before projection submission; GPU VR was not retested on +stereo3d12, whose verified VR route is llvmpipe/lavapipe.
Record runtime loading failures, synthetic-input failures and real cockpit frames separately.

## Evidence and handoff

Capture ScreenShot2 window and full-screen pairs, declaration metadata, package versions, exact options, input timing and per-eye pose/FOV data where available.
Inspect the images.
Count differing eye pixels, then use textured near and far regions with same-row block matching and a separately reported vertical residual.
Compare distant disparity with the prediction from that run's camera geometry; the symmetric simulated-HMD infinity disparity is zero, unlike OSG's desktop convergence settings above.
Keep pristine and stereo-off controls with 0 differing pixels and measure repeat noise.
A loading image or an API session alone does not prove cockpit stereo.

Leave one or two selected full side-by-side PNGs with registered sTER mode 1 and exact LEFT/RIGHT crops for publishing.
The integrator makes the MPO and red/cyan proof formats, reviews credits, publishes packages and sends the upstream heads-up, in Daniel's words and after his approval.
Credit the engine and simulator developers by their own source records, disclose AI assistance once in upstream drafts, thank the project and make one clear ask.
Never send the draft from the working session that wrote it.

## Canvas texture and runtime pitfalls

A Canvas texture is a shared two-dimensional source, even when placed inside a stereo world.
ODGauge needs camera-local stereo disabled while preserving its shader hint; do not make the world instrument placement mono.
Use a four-quadrant texture and inspect all four parts in both split layouts, with exact opaque-body equality and a raw Canvas screenshot control.
The corrected SimGear SDK passes 50 enabled tests and is statically linked into FlightGear; installing an SDK after linking does not update an executable.
A reused Debian build can skip compilation and tests while debian/debhelper-build-stamp exists.
Remove that stamp for a changed-source rebuild, preserve the immutable .dsc, and require fresh compiler/test logs and executable hashes.

For deterministic ordinary-mono comparison, freeze the clock with /sim/time/cur-time-override=1792062000 and --time-offset=0.
An absolute start date alone allows initialization-time differences before freeze.
Retain repeat captures and multiple pristine launches; the measured pristine launch variation is four pixels in one 2x2 patch, and the later pristine reference matches the installed candidate at exactly zero.
Do not hide a nonzero comparison with a tolerance or mask.
A reset can show an equal-eye loading splash before returning to real stereo; distinguish that frame from initialized cockpit evidence.
Avoid placing a distant-scene block-match ROI across an opaque dialog or its shadow.

A successful OpenXR session recreation and two correct pose/subimage routes do not prove the headset image survived.
The autonomous lifecycle witness exposed black images after disable/re-enable in both osgXR modes, with shader failures after GL context release.
The unmodified release fails after recreation, and a tracker-only correction fails with a later crash.
Scoped restoration of the actual entry GLX context and separate draw/read drawables passes both installed +9 lifecycle witnesses, including an auxiliary window.
Check actual images, API submission routes and fixed headset poses after the restart; do not infer success from XR state alone.

A real mirror change requires reload-compositor, as FlightGear's VR options dialog does; changing mirror-enabled alone is not proof that the mirror rendered.
Observe the VRMirror renderer alongside the GUI frame without changing GL state, and capture both rendered states.
A compositor reload can take longer than the property mutation, so gate the capture on the actual rendered frame rather than a timer alone.
Use wall-clock deadlines in slow software-rendered lifecycle fixtures; Nasal timer intervals are not a measured wall-clock dwell.
Wait for FDM initialized and splash alpha 0 before reset, and wait for that readiness again afterward.

A packed X11 stereo window can have a native width twice its GLX drawable width.
OSG's X11 event backend must keep camera and event coordinates in GLX drawable dimensions; querying that drawable on a size mismatch avoids interpreting a packed native event as a new eye width.
The stale-ConfigureNotify control must fail before the correction, retain the logical width afterward, and preserve window-local mouse coordinates.
A separate raw GLX remap control also exposes a stack resize issue without OSG or FlightGear; do not attribute that independent failure to this engine correction.

## Third-review interaction and edition gates

Detect the compositor contract before choosing the visual and permit only OFF or QUAD_BUFFER on its managed desktop.
Test all eight rejected stock formats through property startup, environment startup and runtime writes, including explicit OFF precedence.
Keep stock format behavior when the compositor contract is absent, and keep osgXR's internal routing independent.
Edition UI offers Enable 3D, resolution per eye and the Display Settings shortcut; output formats and monitor configuration remain with KWin.

Each split half needs a fresh session with a verified closed File menu, the one target click and the resulting menu transition.
A state-changing Canvas widget must also change a property from its known initial value.
A no-click second-half control must fail those same transitions; an already-open final menu proves no second click.
Captured releases in a nonzero separator gap must finish Canvas drag/resize and PUI dragging even though a new hit in that gap is rejected.
Follow release with unpressed motion and a subsequent widget action to expose stale capture.

Keep desktop stereo and XR modes as two explicit dimensions.
Both SCENE_VIEW and SLAVE_CAMERAS need simultaneous desktop QUAD_BUFFER controls with actual GL_STEREO=1, actual mirror on/off renders, complete opaque equal-eye UI and unchanged headset routes, poses and depth.
Record API session recreation separately.
Gate capture timing on initialization readiness and inspect actual render telemetry for the mirror state.
A software-rendered startup can outlast an arbitrary mirror-on capture deadline, even while the mirror fixture starts its deadline at FDM readiness.
Hold mirror-on until the harness has its ready on capture, then trigger mirror-off and reload through a property listener; require actual render telemetry for both states.
A blocking property request during auxiliary-window creation can also overrun later scheduled snapshots.
Leave creation time before the OFF snapshot and mode change, and associate every active XID with its actual queried capability.

FlightGear's legacy PUI font path consumes byte strings; shipping UTF-8 text alone does not prove readable controls.
Use its existing Qt GUI for the edition's ordinary control window, with English fallback when FGLocale has no language node for the C locale.
A nonmodal Qt dialog also needs event processing from the GUI subsystem while it exists; opening a correctly named black window is a failing control, not a successful UI.
Check its painted pixels, ordinary undeclared surface, equal opaque placement in both output eyes, delegate arguments, resize behavior and close/reopen lifecycle.

An auxiliary window with a valid stereo visual can still render black if a view matrix is non-finite.
Sview zero damping must take the target directly; evaluating dt/damping when both are zero creates NaN and permanently poisons the camera.
TimeManager quantizes real dt to model-hz intervals, so zero-time updates are legitimate.
Keep a failing original numerical control and check real camera matrices and visible output after initializing the auxiliary view; forcing a tiny clock before initialization can stall unrelated initialization work.

Shared Compositor masks need two update phases.
Refresh shared masks before their shared callbacks, then refresh only eye-owned passes during eye updates.
A shared CSM callback can deliberately set its mask to 0 for a below-horizon light with render-at-night=false; neither eye may overwrite that final callback mask.
Keep an actual CSM CPU control for day/night and mono/stereo transitions, with updateShared followed by both updateEye calls.
The ordinary update path is a separate mono reference.
The default render-at-night=true ownership test cannot expose this regression.
An auxiliary-view renderer witness can additionally verify the final four CSM masks on the selected simulator executable; do not infer a default-window rendering or performance fix from that witness.

The +21 stock-OSG comparison reproduced exactly the earlier pristine four-pixel variant, including the whole-image byte values.
A fresh stock/pristine pair and their repeats match the later pristine reference at zero pixels.
Retain both pristine variants and report the unresolved low-level cause; comparing only one historical reference can misattribute that existing launch variation to a new engine change.
