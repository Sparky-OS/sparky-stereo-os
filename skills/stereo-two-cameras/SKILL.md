---
metadata:
  requires-packages: libgl-dev | libvulkan-dev | qt6-quick3d-dev
name: stereo-two-cameras
description: >-
  Generate and verify coherent per-eye projections of one world for real 3D scenes: parallel axes never toe-in, the
  zero-parallax plane, the maths for orthographic and perspective cameras, VTK programs, quad buffer and Vulkan routes,
  state restoration, eye-private effects, infinity, 2D items over the scene, and the closed-form prediction a capture is
  measured against. Load it when a globe, plot, molecule, CAD model or game scene shows vertical disparity, the wrong
  sign, a flat second eye, a swapped eye, or when the disparity must be predicted and measured.
---

# One world, two cameras

## Working recipe

1. Identify projection type, coordinate units, zero-parallax plane and per-eye resources. For flat UI plane depth, use the window/depth guidance instead.
2. Compare camera math to an independent prediction, then capture rendered near/far geometry and verify vertical alignment and state restoration.
3. Return predicted/measured disparity, tolerance, controls and ordinary 2D comparison. Keep view-dependent history private to each eye.

**Check freshness first.**
Written on 2026-10-07.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; where the drawing sits inside an ordinary window, also load [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md).

## The rule

A stereo pair is the **same scene seen from two camera positions**, about an eye's distance apart.
The program places two cameras at its projection and draws the scene once for each.
For a 3D scene, shifting fragments of one flattened image cannot reconstruct missing visibility, lighting or other view-dependent results.
This does not forbid depth for ordinary 2D UI planes: synchronized per-eye composition with declared disparity is the implemented desktop mechanism, without an application 3D engine.
Use [the toolkit/depth guidance](../stereo-window-3d-area/references/qt-kde-depth.md) for that case.
Wrappers that inject stereo into programs follow the same rule and move the camera at the API.

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
| **Perspective, any OpenGL scene** | The standard asymmetric frustum: each eye's camera translated by plus or minus half the eye separation, its near-plane window shifted by `(e/2)·near/C` for a zero-parallax distance `C`; screen disparity is proportional to `e·(1/C − 1/Z)` | [KAlgebra](https://invent.kde.org/danielcamposramos/kalgebra/-/tree/stereo3d) and [Analitza](https://invent.kde.org/danielcamposramos/analitza/-/tree/stereo3d), [Kalzium](https://invent.kde.org/danielcamposramos/kalzium/-/tree/stereo3d) with [Avogadro](https://github.com/Sparky-OS/avogadrolibs/tree/stereo3d), [Kubrick](https://invent.kde.org/danielcamposramos/kubrick/-/tree/stereo3d), GRASS GIS (in the edition) |
| **VTK programs** | VTK's own projection shear for stereo, set by the program itself when its render passes never set the camera's stereo flag | F3D (in the edition) |

Keep the program's existing separation setting when it has one, and say how its value maps to the new cameras: Marble's 0.5 to 10 degrees kept their meaning in both of its views, so no saved setting changed.

## The OpenGL routes

- **Quad buffer:** draw the left eye into `GL_BACK_LEFT` and the right into `GL_BACK_RIGHT`. The edition's Mesa packs the two at the swap into one full side-by-side picture and declares it to Stereo KWin, so a program that already has quad-buffer stereo works unchanged once it asks for a stereo visual. Netgen had a `-stereo` option that did nothing; it now asks for the quad-buffer window and draws once per eye; OpenSCAD and KiCad take the same route in the edition. Mesa packs the eyes when the swap flushes, so no `glFinish` is needed, and `GL_BACK` follows the drawable's stereo state from any context.
- **Qt:** a `QOpenGLWidget` with a stereo surface format gets `paintGL()` called once per eye, with `currentTargetBuffer()` saying which (Qt 6.5 and later). KAlgebra, Kubrick and Kalzium were proved this way on X11 and on Wayland (on Wayland the whole window is declared today; see the window skill for the fix in progress).
- **Vulkan:** a two-layer swapchain image becomes one full side-by-side picture the same way.

## Proof for this kind of work

As in the general skill, plus the geometry:

1. **The camera maths alone,** in a small test program: project a few thousand visible points with the program's code and with a closed-form prediction (the orbit formula, a pinhole camera, a ray against a sphere), and compare. Expect an error of zero within floating point, zero vertical disparity, and near points crossed.
2. **The rendered pair** (captured with the [`stereo-proof-rig`](../stereo-proof-rig/SKILL.md)): block-match the two captured eyes along the same row (for example 17×17 blocks, sum of absolute differences; check the vertical profile separately) and compare the measured disparity with the prediction. Report the median error, the median absolute error, the share within one pixel, and the vertical shift. Marble's figures, for scale: median absolute error 0.10 to 0.29 px, 81 to 91 % of points within one pixel, vertical shift 0.
3. **Infinity:** stars or sky shift by the predicted parallax of infinity.
4. **The 2D parts:** 0 differing pixels between the eyes; the 2D control against the distribution's build, 0 differing pixels.
5. **Measured limits, written down:** Marble's perspective eyes see a slightly off-centre globe disc that the texture mapper still clips at a circle, about 0.3 px at the default separation; a known limit is stated with its number, not hidden.

## An X3D scene in the browser

X_ITE and X3DOM scenes are real 3D scenes, so they take cameras, not a flat UI's depth: flat WebXR (the page's own views) or the browser's camera hack. The recipe to measure both eyes of either, the numbers found and the traps (float preferences are strings, a shadow-root button needs a real click, model/x3d types open nothing) are in [references/x3d-in-the-browser.md](references/x3d-in-the-browser.md).

Motion in such a scene that is computed and not stored (a clock's `reverse`, a second-order follower beside the Followers component, inverse kinematics on HAnim Sites within their joint limits): the recipe for a live X_ITE scene that runs from a folder, what the X3D and HAnim clauses say, the numbers measured and the traps (a canvas shown twice in a WebDriver screenshot, a fetch that fails from disk, an arm that flips at its limit) are in [references/x3d-procedural-motion.md](references/x3d-procedural-motion.md).

A surface's texture as a procedure first and the image last: [a procedure fitted to a bitmap](references/procedural-texture-from-a-bitmap.md) has the method to measure how much of a bitmap a small procedure holds (OpenKTG's noise from Farbrausch's open tools, the controls that must come back exactly, the bytes of the remainder), the first numbers, where it fails, and six traps (an operator undefined at one value, a lossless codec that flatters the remainder, a licence that forbids the obvious library). The second round is there too: tiled procedures informed by each tile's own pixels, as a level-of-detail ladder, foveated on a still and compared with a tiled bitmap pyramid for the same gaze (the fitters, the controls that come back pixel for pixel, the numbers, six more traps). The third round starts from the source: .kkrieger's own texture graphs read out of its project file and drawn with Farbrausch's operator code, a vision model typing graphs for tiles of a photograph as a werkkzeug artist would, and the comparison by eye with a second cold judge (the tools, the idioms, eight more traps). The reverse by a program is there as well: a Zig fitter that reads a texture's pixels (its two colours, its repeats and the one cell under them, its noise's octaves), builds a werkkzeug3 procedure in the artists' idioms and tunes it by direct search with Farbrausch's operator code as the renderer, proved on .kkrieger's own textures as known answers (the method and its sources, the recipe, what it finds and misses, twelve traps). Its fourth round is werkkzeug's `Text`, a font glyph used as a shape: a font renderer on FreeType behind the operator, a font map that says which font stands in for Arial, Times New Roman and Verdana, the reading that says a glyph is there, and the Twirl run backwards, which gives the logo's twirled g back as the artists' own six operators (ten more traps). Its fifth round is any font and any character: `Text` version 2 (every format FreeType reads, variable axes, COLR, SVG and bitmap glyphs, HarfBuzz shaping, UAX #9), the machine's own fonts first and every free and open font in an index of 17 million glyph shapes, and the reading over all of them, with the traps of a search that large (presentation variants, homoglyphs, clones of one design).  Its sixth round takes high-resolution pictures tile by tile (512 pixel tiles at full size, the whole picture's repeat drawn at each tile's place, one procedure retuned per tile so neighbours stay one surface, seams mixed or colour-matched, the rungs of every tile as levels of detail, the bytes against the fair baseline) and glyphs as seeds (a repeat's motif laid over every glyph of the index with a soft likeness, drawings and fewer bytes preferred, the eye choosing among the candidates, what a seed costs and what its font weighs), with seventeen more traps. Its seventh round is modern operators (each in its own file with its parameter table and a version word: fractal, ridged and warped noise, cellular noise, structure by distance in nine layouts, a gradient map, a material layer, a light from a direction, scatter of a seed, wear, a tile's tint), every one a pure function of its place in the whole picture so a tile is the same procedure drawn over a window and the tiles meet without a seam; the fit takes each from its own reading, the whole picture first and a tile's own correction only where it differs; the same program built for WebAssembly draws the same bytes (with sixteen more traps, the WebAssembly ones among them). Its eighth round reads the full-size picture at 1:1 and lays what the eye misses close up, each layer by its own reading (grain, chipped edges and each piece's own grain, mortar and its specks, patches of a second colour, spots with their stain and runs, stones, pits), each a rung, with version 2 of the operators that changed; and every operator has a WGSL twin, so a page draws the procedures on WebGPU within one level of the native drawing, with the WebAssembly build beside it in the page (the browser in a container on an NVIDIA and an AMD GPU, and eleven more traps). Its ninth round draws four procedures per picture, one fitted to each quarter on its own canvas and laid together by a `Quad` whose seam keeps the coarse colour one smooth field (it helps where the colour changes across a picture, not where a repeat does not divide into quarters), reads a structure's joints again at 1:1 (thin joints, the joint's hollow, a tread plate's two seeds apart, framed tiles), and searches the whole glyph index for a flower and a snowflake's parts with the eye picking among the nearest (eleven more traps). Its tenth round lays whole procedures over each other (`Stack`: by alpha, by a layer's own height, dark or light, the relief in the same order), draws up to sixteen procedures per picture (`Grid`, rectangular tiles read beside their mirror image), reads the noise on every band, adds the eye's options (a bevel and a cast shadow on the structure's own relief, colours by hue, a thin joint's darkest line, the finest grain, a tile on the whole's structure), and searches themed fonts fetched with their licences read (twelve more traps). Its eleventh round carries a procedure and its picture in one glTF texture (the mixed texture: the picture stays the ordinary `texture.source`, so a viewer that ignores the extension shows it; one procedure and one picture per eye for stereo), loads a web scene in Daniel's five steps (every procedure first, drawing at once, the pictures beside it over several connections, a blend, then no more work for the procedure) through a scene tester whose one panel is Macromedia's Simulate Download with Dreamweaver's download time (a virtual link from 14.4 kbit/s dial-up to fibre, the connections, the sizes of the procedures against the pictures, one filling bar per scene component), checks the link's rate against the bytes really sent, proves by counting that a procedure stops, and keeps every GPU submission to one operator over one tile (TRAPCOUNT more traps).

## Any web 3D engine's two eyes

Eight engines (three.js, A-Frame, Babylon.js, PlayCanvas, react-three-fiber, model-viewer, Spark, CesiumJS) through the browser's two routes, one scene, a prediction from the session's own views, controls that must fail, and what each engine needs from the browser: [references/web3d-engines-in-the-browser.md](references/web3d-engines-in-the-browser.md).

A finished page you did not write (a three.js screensaver with a cube-map sky and bloom): freeze it with its own frame cap, read its camera, predict through the hack and the post pass, find a sky that stands in front of the screen with a dense disparity map, and the 23 line fix on the page: [references/web3d-engines-in-the-browser.md](references/web3d-engines-in-the-browser.md), section on a finished page.

## A game engine that draws its own frames (C#, OpenGL, Silk.NET)

An engine with its own camera class, post stack and UI (Froglet's Amoebius: Unity's `Camera` contract in C# over OpenGL 3.3) gets the pair in its camera (`stereoSeparation`, `stereoConvergence`, `GetStereoViewMatrix`, `GetStereoProjectionMatrix` with an off-axis frustum), draws each eye with its own post effects and the UI once per eye into the two halves of one window, declares the window once as full side by side, and takes the separation from the person's depth limits on the window: the recipe, the closed form, a probe scene and checker, the measured errors (0.05 to 0.16 px) and the traps (a newest commit that does not build, GLFW choosing Wayland, the doubled window, the limits property's format) are in [references/csharp-opengl-engine-two-eyes.md](references/csharp-opengl-engine-two-eyes.md).

## Reading a web 3D project before it goes on a list

Which licence, which AI position, whether it can be built from source, which stereo field it has (or none) and whether a native program can sit inside the browser are read from the project's own repository, not from its web page: the recipe, the read-only commands and the traps (NOASSERTION, a bulk licence folder, source-available viewers, code search that lags) are in [references/reading-a-web-3d-project.md](references/reading-a-web-3d-project.md).

Assets (scans, models, materials) for a stereo world come with a licence of their own: what a free operating system may ship, fetch at install, credit, and train on is read from the licence agreement's clauses, not from a marketplace's summary box: [references/reading-an-asset-marketplace-licence.md](references/reading-an-asset-marketplace-licence.md).
