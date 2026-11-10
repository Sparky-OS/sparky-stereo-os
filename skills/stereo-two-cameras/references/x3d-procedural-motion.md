# Procedural motion in X3D: a live scene from disk, and what the clauses say

Written 2026-11-10 from an explanation page with live X_ITE scenes (X_ITE 16.7.1, MIT, Holger Seelig, from its npm release), checked in the edition's browser inside a private Stereo KWin session.
It covers three subjects that meet on x3d-public in November 2026: `TimeSensor.reverse` (Holger Seelig's proposal), a second-order follower beside the Followers component, and inverse kinematics on HAnim Sites.
Credits: t3ssel8r for the second-order follower ("Giving Personality to Procedural Animations using Math"), argonaut for chains of constraints ("A simple procedural animation technique"), Andreas Aristidou and Joan Lasenby for FABRIK (2011), Michalis Kamburelis for Castle Game Engine's `fractionIncreasing`, Don Brutzman and Joe Williams for the HAnim text.

## The recipe: an X3D scene that runs from a folder, driven by page script

1. **Files beside the page,** copied unchanged from the release's `dist` folder: `x_ite.min.js`, `x_ite.css`, `assets/components/<Name>Component.min.js` for each component the scene declares that is not built in (HAnim is separate; Followers, Interpolation and Time are built in), `assets/lib/mikktspace_bg.wasm`, and the licence text. Record the tarball's SHA-256.
2. **Load:** `<script defer src="x_ite/x_ite.min.js">`, one `<x3d-canvas>` per scene, then `X3D (() => { ... })` once its browsers exist.
3. **Build the scene from a string:** `const scene = await browser .createX3DFromString (xml); await browser .replaceWorld (scene);` with `profile='Interchange'` and a `<component name='HAnim' level='1'/>` line for what the profile lacks. Profile `Full` would import every component file.
4. **Read and write fields by name:** `scene .getNamedNode ("Clock")`, then `node .set_fraction = 0.3`, `node .rotation = new X3D .SFRotation (1, 0, 0, a)`, `node .llimit [0]`.
5. **A per-frame hook without a Script node:** a looping TimeSensor and `node .addFieldCallback (key, "time", time => ...)`. The key comes first, then the field name. The time step is the difference of two `time` values.
6. **Say on the page what is a real X3D node and what is page script** standing in for a node that does not exist yet.
7. **Check it by running:** open the page from `file://` in the browser under a private KWin session, read each scene's own log through Marionette, and compare with a number known beforehand (below). A scene that only looks right proves nothing.

## What the clauses say, and what was measured

**TimeSensor (X3D 4.1 CD, 8.4.1).** "temp = (now - startTime) / cycleInterval", "f = fractionalPart(temp)": the fraction is a function of absolute time, with nothing kept from the frame before.
Measured: X_ITE's `fraction_changed` equals that formula to 2e-8 on every frame, except the frame that completes a pass, where it sends exactly 1 ("at the end of every cycle ... the value of fraction_changed is 1").
A smooth `reverse` therefore needs state. The draft already keeps state for pause (8.2.4.4, "continues from its value when paused") and for a changed `cycleInterval` (8.4.1, "continue to increase smoothly").
Holger Seelig's test build of 9 November 2026 does it this way (read from its source, not run): `set_reverse__` calls `setRange (this .fraction, ...)`, which moves the start of the current pass so the count goes on from the last fraction sent, mirrored.
Castle Game Engine's page describes `fractionIncreasing` as "fraction := 1 - fraction" after the standard calculation; read literally, a switch at 0.2 jumps to 0.8. Measured on a prototype of each reading: a step of 0.003 with the fraction kept as state, 0.69 with 1 - f alone at f = 0.15.

**Followers (clause 39).** A damper is "a set of linear first-order filters each of which processes the output of the previous filter" (39.3.2); Equation (5) is `output = destination + (last output - destination) * exp (-dT / tau)`. A chaser's transition is Equation (2), `R(x) = (1 - cos (pi x)) / 2` (39.3.1). Both equations are pictures in the draft, so a text copy of the page loses them: open the image files.
Measured on a jump in X_ITE: neither PositionDamper nor PositionChaser passes the destination (largest share of the jump 0.996 and 1.000).

**A second-order follower** (after t3ssel8r): `y + k1 y' + k2 y'' = x + k3 x'`, with `k1 = zeta / (pi f)`, `k2 = 1 / (2 pi f)^2`, `k3 = r zeta / (2 pi f)`. f is the speed in Hz, zeta the damping (below 1 it swings), r the first response (above 1 it leaps, below 0 it first moves the wrong way).
Update with semi-implicit Euler: `y += T yd; yd += T (x + k3 xd - y - k1 yd) / k2`.
One plain step is stable while `T < sqrt (4 k2 + k1^2) - k1`: the largest eigenvalue of the step crosses 1 exactly there (checked for five settings, 0.98 and 1.02 of the limit).
Its answer depends on the frame rate unless the frame is cut into slices: for zeta 0.5 the analytic overshoot is 16.3 % of the jump; one step per frame gave 12.9 to 14.5 % over five runs whose frames took 16 to 57 ms; slices of at most 1/240 s, with the destination moved evenly across them, gave 15.7 % and 15.8 % at 19 and 54 ms.
It belongs after the interpolator, on the value. On the clock's fraction it would run the animation backwards at every wrap from 1 to 0. It does not replace `reverse`.

**HAnim (X3D 4.1 clause 26, HAnim 2.1 WD clause 6).** HAnimSite: "to define an 'end effector' location that can be used by an inverse kinematics system" (26.3.7 in the 4.1 draft; it was 26.3.6 in 4.0). A Joint's `llimit` and `ulimit` are "the upper and lower joint rotation limits", three values for X, Y and Z, read in the frame `limitOrientation` gives; `stiffness` scales the solver's turn by (1 - stiffness). A segment's length is the distance between two Joint centres, so FABRIK needs no new field.
Two editors' notes in HAnim 2.1 ask how the limits relate to an inverse kinematics engine and ask for an example model; a NOTE says the limits "only affect Joint presentation", which a solver cannot live with: it has to apply them while it solves.
A planar FABRIK that reads `llimit` and `ulimit` from the nodes: every turn stayed inside the limits over a full turn of the target, the hand reached the target when it could (0 mm) and stopped up to 32 cm short when the target went behind the back; with the limits ignored the hand always arrived (within 4 mm) and the elbow turned to +3.1 rad against an allowed 0.

## Traps

- **"Couldn't create browser", WebGL creation failed.** Cause: the browser was started headless in a container with no display, and Gecko found no GL. Fix: run it inside the proof rig's private KWin session (software GL is enough to draw). Found in the browser's log: `FEATURE_FAILURE_WEBGL_EXHAUSTED_DRIVERS`.
- **"Screenshot got cancelled".** Cause: KWin had no render node. Fix: give the container one, as [`stereo-proof-rig`](../../stereo-proof-rig/SKILL.md) says; the page's own checks still run without it.
- **An unhandled rejection "NetworkError when attempting to fetch resource" from a page opened from disk.** Cause: X_ITE fetches `assets/lib/mikktspace_bg.wasm` when it builds tangents and imports each external component from `assets/components/`; the file was not copied. Fix: copy them beside `x_ite.min.js`. Found by listing `fetch (` and `import (` in the unminified `x_ite.js`.
- **Every canvas shows the scene twice, squeezed, in a WebDriver screenshot.** Cause: the camera hack is on by default, so the canvas buffer holds both eyes side by side; WebDriver reads that buffer. What a person sees is KWin's picture: capture with ScreenShot2. The eyes then differ only inside the canvases.
- **The fraction and the time disagree by one frame now and then.** Cause: the clock sends `time` and `fraction_changed` one after the other, so a callback on one may read the other from the frame before. Fix: compare on both callbacks and keep the closer reading of each pair.
- **A reversed fraction jumps by almost 1 at random.** Cause: `fraction_changed` is single precision, so two frames can differ by -1e-8, and `(f - last + 1) % 1` turns that into 0.99999999. Fix: take the advance the short way round, `(f - last + 1.5) % 1 - 0.5`.
- **The limited arm swings to the far side and misses by its whole length.** Cause: an angle outside its limits was clamped by value, which picks the far end when the target passes the back of the joint's range. Fix: stop at the end that is nearer round the circle. Found by the largest miss of a full turn (0.79 m for a 0.75 m arm).
- **A rotation about X bends a hanging arm backwards.** A positive turn about +X takes -Y toward -Z. With the figure facing +Z, forward flexion is a negative X rotation, so an elbow that only bends forward has `llimit` negative and `ulimit` 0.
- **A test that scrolls and screenshots shows the top of the page.** Cause: `scroll-behavior: smooth` and a second scroll call cancel the first. Fix: `scrollIntoView ({ behavior: "instant" })`.
- **The sign of parallax.** Stereo books call behind the screen positive; a table of left minus right has behind negative. Say which one a page uses.
- **Portuguese names:** give one only where it is in common use (paralaxe, sobressinal, cinemática inversa, efetuador final); node names stay as they are.

## The perks of this part

- An editors' note in a draft is the editors' own open question: an offer that answers one is not a new subject.
- X_ITE's unminified `x_ite.js` is readable source: `grep` a field name and read the node.
- A person reading on a stereo screen gets the page's moving scenes in stereo with no work, through the camera hack.
