---
metadata:
  requires-packages: libx11-dev
name: native-linux
description: >-
  Native Linux stereo routes: GLX quad buffer, EGL multiview, Vulkan, Qt,
  X11 declarations (one view size, child windows through Xwayland), libstereo-declare, SDL, GLFW, GLUT, FLTK, Ogre,
  raylib, plib, KWin's buffer formats, eye delivery and the 2D fallback. Load it when GLX offers no stereo visual, a
  program's stereo option does nothing, a child window is invisible to the compositor, an X11 child gets no
  WL_SURFACE_SERIAL in CI, wp_viewporter says the surface already has a viewport, a mono EGL window draws at half its
  width, a video crashes KWin switching between ARGB and NV12, a Vulkan swapchain errors with NATIVE_WINDOW_IN_USE, a
  toolkit lacks stereo, a canvas or video looks pixelated or black in the stereo browser, the browser's video is
  green on NVIDIA, a gl-stereo layer change needs the saver receipts again, or the saver list says "Not offered".
---

# Native Linux programs

## Working recipe

1. Identify the actual loaded toolkit/driver, window system and stereo surface owner; choose the matching route below.
2. Check the granted configuration, draw labelled eyes and capture the compositor output. Exercise resize, close/reopen and the ordinary 2D path.
3. Return loaded versions, surface declarations, geometry and captures. An API flag or source-code capability is not a runtime result.

**Check freshness first.**
Written on 2026-10-07; the game engines and libraries on 2026-10-16; X11 views at another size than their resolution on 2026-10-22.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; for the drawing itself load [`stereo-two-cameras`](../stereo-two-cameras/SKILL.md), and for a 3D area inside a window [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md).

## The routes

For Qt/StyleKit/Canvas Painter or KWin effects work, first classify the input using [the depth guidance](../stereo-window-3d-area/references/qt-kde-depth.md).
The edition's Qt draws a window whose style shows depth (Union) once per eye on Wayland: Qt Quick on the OpenGL RHI, Qt Widgets on the shared memory backing store; the Vulkan RHI, the software backend, `QQuickWidget`, client-side decorations and X11 still draw it flat ([Depth inside every window](../../docs/depth-inside-windows.md)).
An imperative 2D API can produce coordinated eye views; shared styling does not make Widget and Quick rendering identical.
Record exact toolkit/backend versions and loaded libraries before adopting an API from a talk.
For KDE application or toolkit changes, use [the development review recipe](references/kde-development-practices.md): translation context/extraction, QML tooling, lifetime, CI and privileged-action checks.
Qt's own window frame around a stereo window (both routes, the recipe, the traps): [qt-client-decorations.md](references/qt-client-decorations.md).

| The program uses | What happens in the edition | Its part |
|---|---|---|
| OpenGL quad buffer (GLX or EGL) | Mesa packs the two back buffers into one full side-by-side picture at the swap and declares it to Stereo KWin | Ask for a stereo visual or config and draw each eye into its buffer |
| EGL multiview windows (`EGL_EXT_multiview_window`) | Mesa's EGL, also on NVIDIA's Vulkan driver through zink, the edition's default where NVIDIA's driver runs the desktop; NVIDIA's own EGL has no second view, and the gl-stereo layer gives one over it | Create a two-view window |
| Vulkan with a two-layer swapchain | Mesa turns the two layers into one full side-by-side picture; a Vulkan layer does the same over drivers outside Mesa | Render each eye into its layer |
| Qt | A stereo `QOpenGLWidget` (Qt 6.5 and later) or a stereo `QWindow` in a widget container; on Wayland the second | See the window skill |
| X11 toolkits under Xwayland | Our Xwayland gives a redirected child window a surface of its own, so a 3D area inside an X11 window can be its own stereo layer | Nothing, if the program already asks for stereo on its child window |
| The program draws side by side itself (some games, some viewers) | It declares the window through the shared declaration library, and its own output modes go | Hand over full side by side and declare it; on X11, also the size one view is shown at when it differs from the view's resolution ([below](#x11-views-at-another-size-than-their-resolution)) |

## Traps already found

- **Declare before doubling.** Mesa must declare stereo *before* the window grows to hold both eyes; otherwise KWin takes the resize for a 2D window's.
- **GLX offers stereo visuals only when KWin announces stereo,** so a program on a plain 2D session sees none, as before.
- **No `glFinish` is needed, and `GL_BACK` follows the window.** Mesa packs the eyes when the swap flushes, and `GL_BACK` resolves to the drawable's stereo state from any context; a program that drew with a `glFinish` to force the pack can drop it.
- **Child windows were invisible to the compositor.** gmsh, ParaView, Sweet Home 3D, CloudCompare, GRASS and KiCad declared stereo on a child window, KWin read only top-level windows, and both eyes showed squeezed inside the 2D window; the Xwayland patches answer it.
- **A program option that does nothing** is common: Netgen had `-stereo` all along; it asked for nothing until patched.
- **Flatpak:** a Flatpak program loads Mesa from its own runtime, so the edition's stereo Mesa does not reach it; until a Flatpak extension of our Mesa exists, use the distribution's package or the vendor's tarball.
- **A Vulkan layer must stay out of the way of programs that do not use stereo.** An implicit layer loads into every Vulkan program. Ours wrapped every swapchain handle and passed its own handle down as `oldSwapchain`, so a GTK 4 program rebuilding its swapchain on a resize got `VK_ERROR_NATIVE_WINDOW_IN_USE_KHR` and crashed (2026-10-10). The rule: never wrap handles; key the layer's own data by the driver's handle; touch only swapchains created with `imageArrayLayers == 2`; pass `oldSwapchain`, unknown surfaces and every other swapchain call through unchanged. Prove it with a non-stereo program resizing (GTK 4 with `GSK_RENDERER=vulkan`, vkcube) as well as with the stereo case.
- **An OpenGL layer must interpose every drawing command.** Ten of OpenGL 4.6's drawing commands (the instanced draws with a base instance, multi-draw with a base vertex, the indirect draws with a count from a buffer, the transform feedback draws) once reached the driver unwrapped, with the left view's viewport and draw buffer, so a right-eye draw landed in the left view; Blender draws its batches with two of them, and its right eye on NVIDIA's own OpenGL showed only menus and panels. Export every wrapper through `glXGetProcAddress`, `eglGetProcAddress` and `dlsym`, and keep a test that draws one square per command into each view and reads both back: it must fail without the wrapper.

## OpenGL on NVIDIA's own driver

Two paths, a per-program choice with zink the default: Mesa's OpenGL on NVIDIA's Vulkan driver, or NVIDIA's own OpenGL with the gl-stereo layer in front of it (`gl-stereo-run --nvidia-opengl zink|nvidia`).
What each needs, the proof rig and the traps met (a race that left the right eye black, Qt's frame on NVIDIA's EGL, kopper without a second view, a Vulkan client that never read its socket): [nvidia-opengl.md](references/nvidia-opengl.md).

## X11 views at another size than their resolution

On Wayland a declared surface's `wp_viewport` destination is the size one view is shown at, whatever the buffer's resolution.
An X11 window's buffer is its own pixmap, so an X11 program declares that size apart: `_KDE_NET_WM_STEREO_CONTENT_ONE_VIEW_SIZE` (CARDINAL/32, the width and the height one view is shown at, in display pixels), which Stereo KWin reads from support version 6 (kwin +stereo3d30).

- **When to set it:** the views have another resolution than the size they are shown at. The two 1920x540 views of a half top-and-bottom 1920x1080 video, shown at 1920x1080; the two 960x1080 views of half side by side, shown at 1920x1080; the 720x288 fields of a PAL frame, shown at the picture's display size; a game that renders each eye at the person's render resolution in a window of another size. Not needed when each view is shown at its own resolution, and never on Wayland, where the viewport destination says it.
- **With libstereo-declare 1.4.0:** create the window at one view's resolution (1920x540), declare it with `stereo_declare_x11(display, window, STEREO_SBS_FULL, class, subclass)`, then call `stereo_declare_x11_one_view_size(display, window, 1920, 1080)` when `stereo_supported_x11(display)` is 6 or more. Draw both views side by side at their own resolution into the X11 window, which KWin makes two views wide (3840x540). `0, 0` removes the size, and `stereo_remove_x11()` removes it with the rest. From Python: `stereo_declare.Declaration(one_view_size=(1920, 1080))`.
- **By hand:** once `_KDE_NET_WM_STEREO_CONTENT` is 3, and only when the root window's `_KDE_NET_WM_STEREO_CONTENT_SUPPORTED` is 6 or more, set the property on the window with `XChangeProperty(display, window, XInternAtom(display, "_KDE_NET_WM_STEREO_CONTENT_ONE_VIEW_SIZE", False), XA_CARDINAL, 32, PropModeReplace, (const unsigned char *)size, 2)`, `size` being `unsigned long[2]` (Xlib's 32-bit format), and delete it to go back.
- **What KWin does:** the X11 window keeps the program's own size, so the views keep their resolution; the window's place on screen is one view at the declared size; KWin resizes each view once, to the window's place, also when the person maximizes or resizes it; the pointer reaches the first view at its place. A new size changes the place.
- **Traps:** the program's own window size is one view's resolution (from support version 3 KWin makes the X11 window hold both), not the doubled size. The property counts only when the program declares the window itself; a window rule's declaration ignores it. A KWin that announces 5 or less ignores it and shows each view at the window's own size, which makes it the negative control.
- **Two sizes in the events of a declared window** (ORDER 34b, a Vulkan program on its own X11 window): after each configure Stereo KWin sends a synthetic ConfigureNotify in the program's own units, one view, after the X server's own ConfigureNotify with the X window's size. A Vulkan X11 swapchain must be the X window's size, so a program that sizes its swapchain from events takes the size from the server's events only (response type without the 0x80 bit) while it is declared, and knows the doubling when the server's width is twice its own or the synthetic width is half the server's; see vr-to-3d's [openxr-runtime-full-sbs.md](../vr-to-3d/references/openxr-runtime-full-sbs.md).

## A window drawn without OpenGL (XPutImage, XShm)

A software-drawn X11 window is declared like any other (`stereo_declare_x11_format()` at support version 1 or more) and Stereo KWin shows each half to its eye; the program draws its picture at the X window's size, which KWin makes twice the created width, and takes that size from the X server's events, never from the synthetic one-view `ConfigureNotify`.
The recipe, the per-eye proof with its negative controls and the traps are in [x11-software-drawn.md](references/x11-software-drawn.md).

## A GL child that is larger than its window, or under a sibling

X clips a child to its window and a sibling stacked over it hides it; the redirected child's buffer is whole, so the scene must cut it the same way: Stereo KWin does from +stereo3d53 (`X11StereoChild::visible`, cut in the item's shapeForSourceBox, windows that appear later noticed through SubstructureNotify; ORDER 160).
Mesa's GLX lists its stereo children; the EGL X11 platform, the Vulkan stereo layer and the gl-stereo layer declare the child but do not list it, and then the capture is one picture squeezed into the child.
The rows, scripts and traps: [x11-child-clipping.md](references/x11-child-clipping.md), scripts in `../stereo-proof-rig/scripts/x11-child`.

## A video or GL child window of an X11 window

A program whose interface is a toolkit window and whose 3D area is a native child (a player's video, a GL widget) declares the child with `stereo_declare_x11_child()` on its top-level window, not with `stereo_declare_x11()` on the child, and takes the declaration back when the area closes: the top-level must list the child, or Stereo KWin shows one view in both eyes.
Each view keeps its resolution: the program draws on a window of its own inside the toolkit's child, twice a view wide, and declares that window with the size one view is shown at (support version 8), so Stereo KWin resizes once; where the desktop announces less, each view is drawn in half of the child and the program says so.
The recipe, the proof (a column-coded clip), and the traps (the toolkit that reads its child's real size, the library version, the link gate, the error handler, the notices) are in [x11-video-child.md](references/x11-video-child.md).

## Requalifying the gl-stereo savers

The 130 saver receipts bind the stripped layer's SHA-256 and each saver's executable, so any layer change (even a message on stderr) and any rebuild of XScreenSaver's savers needs all 130 again, or the package build stops with "untested layer binary".
The recipe on a device other than the AMD render node (the NVIDIA card through CDI, with Xwayland's glamor off), how the device is proved with the published layer, the run times, the exact pin of the XScreenSaver build the receipts name and the publication gate that refuses a round whose catalogue would drop savers, and every trap met: [requalifying-gl-stereo-savers.md](references/requalifying-gl-stereo-savers.md).

## Game engines and libraries

Read on 2026-10-16 from the sources of Debian testing (the version named) and from the edition's own builds.
"Asks for stereo" means the code requests a stereo visual, context or window; none of the engines has been run in the proof rig yet, so each route below is the one the edition's stack provides, still to prove per engine.
The developer task (`task-sparky-stereo-developer`) installs all of them.

**Window libraries, the edition's builds:**

| Library | Stereo in the edition |
|---|---|
| SDL 3 (3.4.18, ours) | `SDL_GL_STEREO` gives a two-view EGL window (`EGL_EXT_multiview_window`) on Wayland; on X11 SDL asks GLX for a stereo visual. SDL 2 programs get the same, because Debian's SDL 2 is sdl2-compat on SDL 3. |
| GLFW (3.5.1, ours) | `GLFW_STEREO` gives a two-view EGL window; on X11 the window size comes from the synthetic ConfigureNotify, one eye's size. |
| freeglut (3.4.0, ours) | `GLUT_STEREO` asks GLX for a stereo visual; `glutGet` reports one eye's size. |
| FLTK 1.4 (1.4.4, ours) | `FL_STEREO` gives a two-view EGL window on Wayland and a GLX stereo visual on X11. |
| Qt 6 (ours) | A stereo `QOpenGLWidget` or `QWindow` ([`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md)). |

**Engines and frameworks:**

| Engine (Debian testing) | What its source does | Route in the edition |
|---|---|---|
| Godot 4.6.3 | No stereo window; XR through OpenXR (built against the system loader) with multiview rendering, and the Mobile VR interface (`modules/mobile_vr`), which draws both eyes side by side in the window with a lens distortion for phone viewers | An XR project runs on Monado; the edition's Monado shows both eyes undistorted in its peek window (`XRT_WINDOW_PEEK=both`) and declares full side by side. A desktop stereo window is missing. |
| Godot 3.6.2 | No stereo window; the Mobile VR interface as in Godot 4; no OpenXR module | Missing: the Mobile VR picture is two half-width eyes with a lens distortion, so a full-width, undistorted mode declared to Stereo KWin is the change. |
| LÖVE 11.5 | An SDL 2 window that never asks for stereo | Missing: a `stereo` window flag passed to SDL, then each eye drawn to its back buffer. |
| Ren'Py 8.3.4 | pygame on SDL 2; no stereo request | Missing. |
| raylib 6.0 | A "VR stereo mode" (`BeginVrStereoMode`, `src/raylib.h`) that draws both eyes side by side with a lens-distortion shader for headsets, over GLFW | Missing: a `GLFW_STEREO` window, or the stereo mode without distortion at full width, declared. |
| Allegro 5.2.11 | The `ALLEGRO_STEREO` display option asks GLX for a stereo visual (`src/x/xglx_config.c`) | Quad buffer, through Mesa. |
| SFML 3.1 | No stereo request | Missing. |
| Irrlicht 1.8.5 | `SIrrlichtCreationParameters::Stereobuffer` asks GLX or SDL for stereo; `ERT_STEREO_LEFT_BUFFER` and `ERT_STEREO_RIGHT_BUFFER` render targets | Quad buffer, through Mesa. |
| OGRE 14.5 | Quad-buffer stereo behind the CMake option `OGRE_CONFIG_ENABLE_QUAD_BUFFER_STEREO`, off by default and off in Debian's build | Missing until a build turns the option on. |
| OpenSceneGraph 3.6.5 (ours) | Stereo modes, quad buffer among them; our build restores the caller's draw buffers after quad-buffer drawing | Quad buffer, through Mesa. |
| plib 1.8.5 (ours) | Our build adds opt-in quad-buffer cameras to `ssgCullAndDraw`; our TORCS asks for a stereo drawable | Quad buffer, through Mesa. |
| ClanLib 1.0 | Asks GLX for a stereo visual when the display description asks for stereo | Quad buffer, through Mesa. |
| pygame 2.6.1 | Exposes `GL_STEREO` for `gl_set_attribute`, passed to SDL | Quad buffer through SDL and Mesa, for PyOpenGL programs. |
| pyglet 2.1.14 | `Config(stereo=True)` asks GLX for a stereo visual | Quad buffer, through Mesa. |
| moderngl 5.12, PyOpenGL 3.1 | No window of their own: they draw in the window of the library above | The window library's route. |
| Luanti 5.15.2 | `3d_mode`: anaglyph, top and bottom, side by side, cross view, each eye at half size in one picture | Its own output modes go in the edition's build; it hands over full side by side, declared. |
| ioquake3 1.36 | `r_stereoEnabled` asks SDL for stereo and draws to `GL_BACK_LEFT` and `GL_BACK_RIGHT` (`code/sdl/sdl_glimp.c`, `code/renderergl1/tr_cmds.c`); `r_anaglyphMode` is its own output | Quad buffer through SDL and Mesa; the anaglyph mode goes. |
| DarkPlaces | `vid_stereobuffer` (quad buffer) beside its own side by side and anaglyph modes | Quad buffer, through Mesa. |
| dhewm3 1.5.5 | Would ask SDL for stereo, but the renderer always sets `parms.stereo` false | Missing. |
| RBDoom3BFG 1.4.0 | `stereoRender_enable`: 6 is OpenGL quad buffer; 1 to 5 are its own packings | Quad buffer, through Mesa. |
| FreeSpace 2 Open 26.0.1 | OpenXR support | XR, through Monado. |
| OpenMW 0.51.0 | `[Stereo] stereo enabled` splits the window with OpenSceneGraph's horizontal split, each eye at half the width | Missing: OpenSceneGraph's quad buffer, or full side by side declared. |
| Spring 106, Flare 1.15, Cube 2, FIFE 0.4.3, KDE's libkdegames | No stereo request | Missing. |

"Missing" is the next piece of work, in the engine's own window or camera code, proved in the rig like any program ([`stereo-two-cameras`](../stereo-two-cameras/SKILL.md) for the cameras).
Zig, RenderDoc, GFXReconstruct, Hotspot, GitHub's CLI, Tiled and KDE's Kommit are not in Debian testing (2026-10-16), so the developer task cannot carry them yet.

## Proof

As in the general skill: both eyes captured, one declaration, the 2D control.
For a route change (Mesa, Xwayland), also the programs that already worked, rerun.

A client drawing on a GPU other than the compositor's (a dmabuf import failure, "importing the supplied dmabufs failed"): [references/two-gpu-dmabuf.md](references/two-gpu-dmabuf.md).

A compute or sparse-buffer program that draws nothing on the RTX through zink, with no GL error (64-bit atomics in another storage buffer, a sparse buffer's tail reading zero): [references/zink-storage-and-sparse.md](references/zink-storage-and-sparse.md).

A browser canvas (WebGL, three.js, CesiumJS), video or image with `image-rendering: pixelated` that shows black, solid green or blurry on Stereo KWin: [references/browser-pixelated-canvas.md](references/browser-pixelated-canvas.md).

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (10 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
