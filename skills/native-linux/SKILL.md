---
name: native-linux
description: The routes a native Linux program uses to show stereo on Sparky Stereo OS (OpenGL quad buffer through GLX and EGL, Vulkan, Qt, X11 programs through Xwayland, programs that draw side by side themselves), what each needs, and the traps found on the way. Load the general sparky-stereo skill first.
---

# Native Linux programs

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; for the drawing itself load [`stereo-two-cameras`](../stereo-two-cameras/SKILL.md), and for a 3D area inside a window [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md).

## The routes

| The program uses | What happens in the edition | Its part |
|---|---|---|
| OpenGL quad buffer (GLX or EGL) | Mesa packs the two back buffers into one full side-by-side picture at the swap and declares it to Stereo KWin | Ask for a stereo visual or config and draw each eye into its buffer |
| EGL multiview windows (`EGL_EXT_multiview_window`) | Mesa's EGL; NVIDIA's egl-wayland learns the same two-view window in the edition | Create a two-view window |
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

## Proof

As in the general skill: both eyes captured, one declaration, the 2D control. For a route change (Mesa, Xwayland), also the programs that already worked, rerun.
