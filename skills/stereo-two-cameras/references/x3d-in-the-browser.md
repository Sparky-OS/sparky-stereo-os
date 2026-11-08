# Measuring an X3D scene's two eyes in the browser

Measured 2026-11-08 on the edition's browser (Waterfox-based, 6.7.5 +stereo3d10) with X_ITE 16.7.1 (MIT, Holger Seelig) and X3DOM 1.8.3 (MIT or GPL-3.0), each from its own npm release (checked against the registry's SHA-512), under a private Stereo KWin with a stereo virtual output, Mesa on an AMD render node.

## The recipe

1. **A scene with known geometry.** A Viewpoint at `0 0 10` (the X3D default pose, ISO/IEC 19775-1 23.3.1; X3D units are metres, 4.3.6) and four unlit boxes (emissive colour only, headlight off) whose front faces are 2, 5, 12 and 30 m away, each 0.08 of its distance wide, in four pure colours.
   Place them for the narrow view a flat WebXR session gives (about 25 degrees tall), or the near and far boxes leave the picture.
2. **The same markup for both libraries:** `<x3d-canvas><X3D><Scene>...` for X_ITE, `<x3d><scene>...` (explicit closing tags) for X3DOM. A page with no library script renders nothing: `<X3D>` and `<x3d-canvas>` are unknown elements, and the measurement says so (0 canvases).
3. **Three cases per library, each in a fresh container and session:** the 2D control (`webgl.stereo-camera.enabled` false: the two captures equal, disparity 0), the camera hack (pref true), and WebXR (`dom.vr.enabled`, `dom.vr.webxr.enabled`, `dom.vr.flat.enabled`, `permissions.default.xr` 1, `dom.vr.flat.mode` 0 = flat TV or output, 1 = flat headset).
4. **WebXR needs a real click on the library's own button:** X_ITE's is `.x_ite-private-xr-button` inside the `x3d-canvas` shadow root (it appears over the canvas), X3DOM's is `.x3dom-vr`. Move a real pointer over the canvas first, then click at the button's centre with WebDriver pointer actions (this is what worked; an element click and a script click were not tried).
5. **Tap the session, change nothing:** wrap `navigator.xr.requestSession` and `XRSession.prototype.requestAnimationFrame` in the page so each frame's `views` (projection matrix and inverse transform) and the base layer's viewports are recorded. The prediction is then each box's front-face centre (viewpoint at the XR origin) projected through the recorded views; disparity in pixels is the left eye's x minus the right's, so negative means behind the screen.
6. **Measure:** capture both eyes (ScreenShot2), find each colour's centroid per eye inside the canvas (in a flat WebXR session the whole screen), report disparity, vertical shift (0 expected) and, for a page with text around the canvas, the difference outside the canvas (0 expected).
7. **Zero parallax by arithmetic:** the distance at which the two recorded views agree (bisection on the projected x difference) is the screen plane; compare it with the preference that sets it (`dom.vr.flat.screen-plane-mm`).

## What was found

- X_ITE and X3DOM both use `navigator.xr.requestSession("immersive-vr")` and the `local` reference space and draw each eye with the views the session gives, so flat WebXR gives each eye its own view on both: measured against the prediction, within 0.3 px at the default plane (1 m) and the 3.5 mm flat TV interaxial, 0.2 px for the 8.7 mm flat headset one, 2 px with the plane at 10 m (the near box is partly clipped there).
- The Viewpoint's `fieldOfView` (23.4.6) is not used: the view angle is the display's (25.4 degrees tall in flat TV mode, 21.9 in flat headset mode against the scene's 45), so the authored framing changes and boxes grow 2.5 times.
- X3D has no zero-parallax plane, so metres 1 to 1 against a 1 m screen plane put a scene that is 2 to 30 m away wholly behind the screen (-4 to -7.5 px at 1280 wide). With the plane at the Viewpoint's distance to its `centerOfRotation` (10 m, `dom.vr.flat.screen-plane-mm` 10000) the same boxes read +29.6, +7.1, -1.5, -5.5 px against +31.5, +7.9, -1.3, -5.2 predicted.
- The camera hack keeps the author's framing and the HTML around (outside-canvas difference 0.000) but puts the screen plane at 5 times the library's near plane: X_ITE's near is 0.125 m (plane about 0.6 m, all boxes behind the screen, -11 to -15.5 px of 800, so 2 m and 30 m differ by 4.5 px), X3DOM computes its near from the scene (1.4 m, plane about 7 m: +59.6, +9.0, -11.5, -19.5). `webgl.stereo-camera.convergence` is a multiple of the near plane.

## Traps

- **A float preference written as a number is ignored.** Symptom: `webgl.stereo-camera.convergence` 80.0 in user.js changed nothing. Cause: Gecko stores float preferences as strings. Fix: `"80.0"`. Found by the identical numbers of two runs.
- **A model/x3d type is not shown.** Navigating to a `.x3d`, `.x3dv` or `.x3dj` served as `model/x3d+xml`, `model/x3d+vrml` or `model/x3d+json` times out and leaves about:blank (an external handler, nothing drawn); served as `application/xml` it opens the XML tree.
- **JSON in a shell word:** a preference object passed through an unquoted variable breaks at its space; write it compact.
- **Measure the whole screen in a flat WebXR session:** the library's canvas is resized to the session's layer, so its page rectangle is not where the views are.
