---
name: native-linux
description: The routes a native Linux program uses to show stereo on Sparky Stereo OS (OpenGL quad buffer through GLX and EGL, Vulkan, Qt, X11 programs through Xwayland, programs that draw side by side themselves), what each needs, and the traps found on the way. Load the general sparky-stereo skill first.
---

# Native Linux programs

**Check freshness first.**
Written on 2026-10-07; the game engines and libraries on 2026-10-16.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; for the drawing itself load [`stereo-two-cameras`](../stereo-two-cameras/SKILL.md), and for a 3D area inside a window [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md).

## The routes

| The program uses | What happens in the edition | Its part |
|---|---|---|
| OpenGL quad buffer (GLX or EGL) | Mesa packs the two back buffers into one full side-by-side picture at the swap and declares it to Stereo KWin | Ask for a stereo visual or config and draw each eye into its buffer |
| EGL multiview windows (`EGL_EXT_multiview_window`) | Mesa's EGL, also on NVIDIA's Vulkan driver through zink, the edition's default where NVIDIA's driver runs the desktop; NVIDIA's own EGL has no second view, and the gl-stereo layer gives one over it | Create a two-view window |
| Vulkan with a two-layer swapchain | Mesa turns the two layers into one full side-by-side picture; a Vulkan layer does the same over drivers outside Mesa | Render each eye into its layer |
| Qt | A stereo `QOpenGLWidget` (Qt 6.5 and later) or a stereo `QWindow` in a widget container; on Wayland the second | See the window skill |
| X11 toolkits under Xwayland | Our Xwayland gives a redirected child window a surface of its own, so a 3D area inside an X11 window can be its own stereo layer | Nothing, if the program already asks for stereo on its child window |
| The program draws side by side itself (some games, some viewers) | It declares the window through the shared declaration library, and its own output modes go | Hand over full side by side and declare it |

## Traps already found

- **Declare before doubling.** Mesa must declare stereo *before* the window grows to hold both eyes; otherwise KWin takes the resize for a 2D window's.
- **GLX offers stereo visuals only when KWin announces stereo,** so a program on a plain 2D session sees none, as before.
- **No `glFinish` is needed, and `GL_BACK` follows the window.** Mesa packs the eyes when the swap flushes, and `GL_BACK` resolves to the drawable's stereo state from any context; a program that drew with a `glFinish` to force the pack can drop it.
- **Child windows were invisible to the compositor.** gmsh, ParaView, Sweet Home 3D, CloudCompare, GRASS and KiCad declared stereo on a child window, KWin read only top-level windows, and both eyes showed squeezed inside the 2D window; the Xwayland patches answer it.
- **A program option that does nothing** is common: Netgen had `-stereo` all along; it asked for nothing until patched.
- **Flatpak:** a Flatpak program loads Mesa from its own runtime, so the edition's stereo Mesa does not reach it; until a Flatpak extension of our Mesa exists, use the distribution's package or the vendor's tarball.
- **A Vulkan layer must stay out of the way of programs that do not use stereo.** An implicit layer loads into every Vulkan program. Ours wrapped every swapchain handle and passed its own handle down as `oldSwapchain`, so a GTK 4 program rebuilding its swapchain on a resize got `VK_ERROR_NATIVE_WINDOW_IN_USE_KHR` and crashed (2026-10-10). The rule: never wrap handles; key the layer's own data by the driver's handle; touch only swapchains created with `imageArrayLayers == 2`; pass `oldSwapchain`, unknown surfaces and every other swapchain call through unchanged. Prove it with a non-stereo program resizing (GTK 4 with `GSK_RENDERER=vulkan`, vkcube) as well as with the stereo case.
- **An OpenGL layer must interpose every drawing command.** Ten of OpenGL 4.6's drawing commands (the instanced draws with a base instance, multi-draw with a base vertex, the indirect draws with a count from a buffer, the transform feedback draws) once reached the driver unwrapped, with the left view's viewport and draw buffer, so a right-eye draw landed in the left view; Blender draws its batches with two of them, and its right eye on NVIDIA's own OpenGL showed only menus and panels. Export every wrapper through `glXGetProcAddress`, `eglGetProcAddress` and `dlsym`, and keep a test that draws one square per command into each view and reads both back: it must fail without the wrapper.

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
