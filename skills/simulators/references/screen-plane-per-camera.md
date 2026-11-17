# A screen plane for each camera mode

A driver and a chase camera show the same world from different places.
They need different zero-parallax distances.
Daniel's rule is that the interior should pop enough for the cockpit to feel real; a chase camera has its screen plane near the camera, a small pop for nearer objects and generous depth beyond it.
Keep the two cameras parallel and use off-axis projection, as [stereo-two-cameras](../../stereo-two-cameras/SKILL.md) specifies.

## Recipe

1. Reconcile the published source and its Debian patch series before changing a fork.
   A fork's older packaging is not proof of what the edition ships.
2. Identify the actual camera ids, not only the function-key group.
   Apply a plane when selecting or restoring a camera, separately for each view.
3. Capture the published package first in an isolated compositor, then each candidate with the same car, track, eye width and camera.
   Inspect both eyes and the declaration.
4. Measure panel/bodywork, steering wheel where the model has one, distant scenery, chase car and nearest road.
   Exclude screen-space gauges and text from world-depth measurements.
   Report the largest sampled pop and sink in pixels and as fractions of one eye's width, and check vertical alignment independently.
5. Compare the far result with the run's camera projection, rather than a physical-screen estimate from another camera.
   With focal length f in pixels, separation e and plane C, the R-minus-L disparity is f*e*(1/C - 1/Z).
   An infinite background has disparity f*e/C even when its mesh is a small cylinder.
6. Keep a stereo-off control and require exact pixel equality against the published package.
   Preserve scene state and record any animation that prevents an exact scene comparison.
7. Ship decided package defaults with the person's configuration and explicit environment settings taking precedence.
   Keep the full side-by-side left-first pair and its own format mark, separately from output filters.

## plib and TORCS

The original native plib path takes PLIB_SSG_STEREO, PLIB_SSG_EYE_SEPARATION and PLIB_SSG_CONVERGENCE.
The old library default for convergence is 10 scene units; the launcher need not set that variable.
The per-draw extension takes convergence and separation arguments while retaining both environment overrides.
Its overloads preserve the existing entry points and context layout.
A separate infinite-background draw keeps projection shift and suppresses eye translation, with the projection scale of the world camera.
Otherwise a unit-radius sky mesh can acquire foreground parallax.

TORCS classifies inside cameras within its camera group rather than treating every F2 camera as inside.
Its graph.xml entries are `stereo cockpit convergence`, `stereo chase convergence`, `stereo cockpit eye separation` and `stereo chase eye separation` in the Graphic section.
A person's existing graph.xml is left alone; code fallback values cover an existing file that has no new entries.
PLIB_SSG_CONVERGENCE remains an explicit global override, so it deliberately overrides both camera modes.
Never combine native plib stereo with another layer that moves the cameras again.

## Speed Dreams and OSG

OSG's camera DisplaySettings supplies screen distance and eye separation.
Use camera-local settings and refresh them when the selected camera changes, including the saved-camera restoration path.
Speed Dreams' Graphic section can carry `stereo cockpit convergence`, `stereo chase convergence` and `stereo eye separation`; the view-specific `stereo cockpit eye separation` and `stereo chase eye separation` take precedence over that older global setting.
Explicit OSG_SCREEN_DISTANCE and OSG_EYE_SEPARATION settings retain precedence over those defaults.
A camera-specific fusion distance can also affect the result: measure the actual projection and distant image in each view.
The held Speed Dreams package and its contribution-policy restrictions remain separate gates; a rig build is not publication approval.

## Measured profiles

At 800 pixels per eye, the TORCS car7-trb1 inside view uses a 1.8 m plane and 0.065 m separation; chase uses 2 m and 0.10 m.
The Speed Dreams quickrace inside view uses a 0.65 m plane and 0.065 m separation; chase uses 2 m and 0.10 m.
These are model-dependent edition defaults, not settings imposed on an upstream release.
For the measured Speed Dreams car, moving the inside plane from 0.7 m to 0.65 m changes the panel median from -12.01 px to -9.15 px and reduces the wheel-region pop bound from -67.07 px to -64.24 px.
The increased chase separation widens object-depth differences; convergence alone only moves the whole scene relative to the screen.
TORCS's 1.2 m candidate gives about -5 px on the bodywork, while 1.8 m gives -13 px, a clearer interior without the old 10 m plane's stronger pop.

A person's settings go into the Graphic section of the game's ordinary graph.xml in its own configuration directory.
Keep the package defaults and fallback values together, and leave existing personal files untouched.

## Traps

- **Symptom:** the new recipe loses a previously repaired undefined-symbol failure.
  **Cause:** starting from the old game fork instead of the published source package.
  **Fix:** preserve the complete published Debian series before appending the depth patches.
  **How found:** compare the source series and the library's NEEDED entries; TORCS's libtgfclient must own its Xrandr dependency.
- **Symptom:** measuring a dashboard gives zero disparity despite a visible popped interior.
  **Cause:** the ROI includes screen-space gauge overlays or large untextured polygons.
  **Fix:** inspect the image and measure textured world geometry separately from HUD controls.
  **How found:** compare accepted block locations with the actual panel and gauge positions.
- **Symptom:** a published mono baseline works but ScreenShot2 stalls in a new software session.
  **Cause:** KWin fell back to its software compositor without a render node.
  **Fix:** provide an allowed render node to the isolated compositor, then select and record the application's renderer separately.
  **How found:** the compositor log reports the fallback and Xwayland reports that glamor is unavailable.

- **Symptom:** changing convergence makes the car and scenery move together, leaving the chase view's narrow depth range.
  **Cause:** for fixed cameras and separation, the convergence term cancels when subtracting two objects' disparities.
  **Fix:** measure a separate chase separation, retaining the cockpit separation and explicit overrides.
  **How found:** compare the pinhole equation with near/far block matches at both plane settings.
- **Symptom:** a second package build stops with “already marked”.
  **Cause:** a reused staging tree already contains projected payloads.
  **Fix:** build from a fresh extraction of the same descriptor with the complete gate sibling set.
  **How found:** the Lean Code refusal, followed by a clean build passing the archive-qualified gate.
- **Symptom:** a compiler cannot find tgfclient.h even though the export directory contains it.
  **Cause:** TORCS's generated export links are absolute paths into the original container build location.
  **Fix:** bind the build tree at the same container path for the compiler check.
  **How found:** readlink of the exported header.

- **Symptom:** the infinity checker fails although the far-scene median is close.
  **Cause:** a broad ROI also contains nearby grandstands and walls; finite objects must have less disparity than infinity.
  **Fix:** inspect the capture, document a genuinely distant ROI, and keep an independent unobstructed sky-band control.
  **How found:** accepted match coordinates against the image, then the separate sky result (0.07 px error on the fixed TORCS background, about 29 px on the published control).
