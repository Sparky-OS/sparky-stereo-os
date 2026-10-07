---
name: stereo-two-cameras
description: How to make a program that draws a scene (a globe, a plot, a molecule, a CAD model, a game view) produce a correct stereo pair on Sparky Stereo OS: one world seen from two cameras, the camera maths for orthographic and perspective views, the OpenGL routes, and how to prove the result against a prediction. Load the general sparky-stereo skill first.
---

# One world, two cameras

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; where the drawing sits inside an ordinary window, also load [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md).

## The rule

A stereo pair is the **same scene seen from two camera positions**, about an eye's distance apart. The program places two cameras at its projection and draws the scene once for each. It never draws once and then shifts items left and right one by one: that breaks lighting, shadows, occlusion and anything computed per view. Wrappers that inject stereo into programs follow the same rule and move the camera at the API.

- **Parallel axes, never toe-in.** Turning the two cameras inward makes keystone distortion and vertical disparity, which the eyes cannot fuse. The cameras stay parallel and the projection is shifted (off-axis) instead.
- **Choose the zero-parallax plane.** Points on it sit at screen depth in both eyes; nearer points come out of the screen (crossed disparity), farther ones go in. Put it where the scene's centre of interest is.
- **Vertical disparity is zero.** Any vertical difference between the eyes is a bug.
- **Things at infinity** (stars, sky, a far horizon) take the parallax of infinity, not the scene's.
- **2D items over the scene** (a compass, labels, a legend, the cursor) are drawn once and are identical in both eyes. Picking (what the mouse points at) uses one eye, the left.

## The maths, by kind of camera

| Camera | What to do | Example |
|---|---|---|
| **Orthographic, round object** (a globe) | Orbit: turn the view about the object's centre by plus and minus half the separation angle `h`. A point's horizontal position becomes `x·cos h ± z·sin h`; height is unchanged | [Marble's globe, 43d2b67f37b9](https://invent.kde.org/danielcamposramos/marble/-/commit/43d2b67f37b9) |
| **Orthographic plot** | A shear about the camera target: `x' = x ± k·(z − z_target)` per eye | GNU Octave (in the edition) |
| **Perspective, camera at a finite distance** | Move each eye's camera sideways along the camera's horizontal axis, keep the axes parallel, shift the frustum so the zero-parallax plane stays put. In Marble's vertical perspective view the eyes sit `e = P·sin(h)` globe radii to the sides, and a point projects to `x = unitX·k + e·((P−1)/P − k)`, `k = (P−1)/(P−cos c)` | [Marble's perspective view, 8b1ec5b961a7](https://invent.kde.org/danielcamposramos/marble/-/commit/8b1ec5b961a7) |
| **Perspective, any OpenGL scene** | The standard asymmetric frustum: each eye's camera translated by plus or minus half the eye separation, its near-plane window shifted by `(e/2)·near/C` for a zero-parallax distance `C`; screen disparity is proportional to `e·(1/C − 1/Z)` | [KAlgebra](https://invent.kde.org/danielcamposramos/kalgebra/-/tree/stereo3d) and [Analitza](https://invent.kde.org/danielcamposramos/analitza/-/tree/stereo3d), [Kalzium](https://invent.kde.org/danielcamposramos/kalzium/-/tree/stereo3d) with [Avogadro](https://github.com/danielcamposramos/avogadrolibs/tree/stereo3d), [Kubrick](https://invent.kde.org/danielcamposramos/kubrick/-/tree/stereo3d), GRASS GIS (in the edition) |
| **VTK programs** | VTK's own projection shear for stereo, set by the program itself when its render passes never set the camera's stereo flag | F3D (in the edition) |

Keep the program's existing separation setting when it has one, and say how its value maps to the new cameras: Marble's 0.5 to 10 degrees kept their meaning in both of its views, so no saved setting changed.

## The OpenGL routes

- **Quad buffer:** draw the left eye into `GL_BACK_LEFT` and the right into `GL_BACK_RIGHT`. The edition's Mesa packs the two at the swap into one full side-by-side picture and declares it to Stereo KWin, so a program that already has quad-buffer stereo works unchanged once it asks for a stereo visual. Netgen had a `-stereo` option that did nothing; it now asks for the quad-buffer window and draws once per eye.
- **Qt:** a `QOpenGLWidget` with a stereo surface format gets `paintGL()` called once per eye, with `currentTargetBuffer()` saying which (Qt 6.5 and later). KAlgebra, Kubrick and Kalzium were proved this way on X11 and on Wayland (on Wayland the whole window is declared today; see the window skill for the fix in progress).
- **Vulkan:** a two-layer swapchain image becomes one full side-by-side picture the same way.

## Proof for this kind of work

As in the general skill, plus the geometry:

1. **The camera maths alone,** in a small test program: project a few thousand visible points with the program's code and with a closed-form prediction (the orbit formula, a pinhole camera, a ray against a sphere), and compare. Expect an error of zero within floating point, zero vertical disparity, and near points crossed.
2. **The rendered pair** (captured with the [`stereo-proof-rig`](../stereo-proof-rig/SKILL.md)): block-match the two captured eyes along the same row (for example 17×17 blocks, sum of absolute differences; check the vertical profile separately) and compare the measured disparity with the prediction. Report the median error, the median absolute error, the share within one pixel, and the vertical shift. Marble's figures, for scale: median absolute error 0.10 to 0.29 px, about 90 % of points within one pixel, vertical shift 0.
3. **Infinity:** stars or sky shift by the predicted parallax of infinity.
4. **The 2D parts:** 0 differing pixels between the eyes; the 2D control against the distribution's build, 0 differing pixels.
5. **Measured limits, written down:** Marble's perspective eyes see a slightly off-centre globe disc that the texture mapper still clips at a circle, about 0.3 px at the default separation; a known limit is stated with its number, not hidden.
