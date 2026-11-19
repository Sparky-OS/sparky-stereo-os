# Emulators that hand Stereo KWin a declared pair (Dolphin and Azahar)

Learned on ORDER 39 (November 2026). Milestone 1: the reconcile and the reading of both programs. Continuation 1: Dolphin built and run in a Stereo KWin (rows below); Azahar is its own item and was not run.

## What each program does today

| | Dolphin (Debian testing 2609.b+dfsg-1, Qt 6, GPL-2.0-or-later) | Azahar (release 2126.2, Qt 6, GPL-2.0) |
|---|---|---|
| Debian | in testing, built with Qt 6 and the Vulkan backend (`ENABLE_VULKAN` is on by default) | not in Debian: no source package, no removal in ftp-master's removal log, no request to package it; Debian's only 3DS request is the 2017 request for Citra (bug 870143, open) |
| Edition | Debian's package, unchanged (listed in `emulation-3d.list`) | missing from Debian, listed in `lists/MISSING.md`; the build tree has the source as a submodule, no recipe |
| Stereo modes | `StereoMode`: Off, SideBySide, TopAndBottom, Anaglyph, QuadBuffer, Passive (`VideoConfig.h`) | `StereoRenderOption`: Off, SideBySide, SideBySideFull, Anaglyph, Interlaced, ReverseInterlaced, CardboardVR (`settings.h`) |
| How the second view is made | the emulator moves the camera: geometry shader (OpenGL, Vulkan) copies each draw to two layers by `stereo_depth` and `stereo_convergence` | the guest game draws both eyes itself; the console's 3D slider (`factor_3d`, 0 to 100) is written to the shared page and to the HID page, the game scales its own parallax by it |
| What goes to the window | SideBySide and TopAndBottom put the two layers into halves of one window picture (`Presenter::RenderXFBToScreen`, `ConvertStereoRectangle`); with "per eye resolution full" the aspect is doubled; nothing is declared | SideBySideFull draws the whole layout twice, left half then right half (`framebuffer_layout.width / 2` each), nothing is declared |
| Lower screen | none | drawn in both halves at the same place, so it has no parallax (`renderer_vulkan.cpp`, the bottom screen cases) |

## Rules each contributor asks for

- Dolphin, `Contributing.md`, "Generative AI": contributions from humans, not from AI agents; the person understands and answers for the code; disclose which non-trivial parts are generated; no LLM for anything about the emulated console's behaviour.
- Azahar, `AI-POLICY.md` (effective 20 March 2026): snippets up to about five lines with disclosure; no AI-written significant contribution, no AI-written copyrightable snippet, no autonomous pull requests or issues; closed pull requests, and accepted ones found in breach are removed.
- Both: a patch for upstream is written by a person; our build can carry larger changes in our fork.

## What upstream has about it (searched 19 November 2026 with the issues search API, no account)

- Azahar: SideBySideFull and Swap Eyes arrived in #604 (OpenSauce04, closed 2025-05-16) and #1212 (DavidRGriswold, merged 2026-01-03: full-width side by side, swap eyes, which display to render stereo on). Open: #2483 per game 3D depth, #655 IPD adjustment, #2718 libretro views API. Nothing for Wayland, KDE or a declaration.
- Dolphin: quad buffer fixes #8378 (stenzek, merged 2019), SBS/TAB aspect #13009 (BryanJacobs), float depth and convergence #14100 (AndrewGDX, merged 2025-11-12). Open: #14288 (jasonphillips) stereo on Vulkan without geometry shaders, by instancing with `VK_EXT_shader_viewport_index_layer`. Nothing for Wayland or a declaration.
- So no upstream patch declares a surface; the declaration is ours (libstereo-declare, `stereo_declare_wayland`).

## Where the declared surface goes

- Azahar: `GRenderWindow` is a Qt child window of the main window (menus stay 2D). Declare that surface full side by side; its width is two eyes, the layout is already built that way. In the edition's build SideBySideFull is the only 3D output; the other modes, Swap Eyes and the mono-eye choice are not built (the swap is the output's).
- Dolphin: the render widget is the same kind of child. Presenting from the emulator's two-layer XFB texture, a Vulkan swapchain with two image layers lets Mesa pack and declare it (see `qt-vulkan-two-views.md`); on OpenGL the packing is the presenter's and the declaration is libstereo-declare's.

## The fit (design, not built)

- Dolphin makes its second view by moving the camera, so the house rule applies: the camera offset is the largest for which every pixel stays inside the person's limits, no separation or convergence setting (stereo-two-cameras, ORDER of 18 November 2026). It needs the scene's nearest and farthest depth each frame, read from the depth buffer.
- Azahar and the 3DS: the console draws its own pair and has its own slider as part of the machine. There is no recorded rule; today's behaviour is kept and the numbers (the games' disparity at slider 0, 50 and 100 against the limits) are Daniel's call. Not measured: it needs a 3D homebrew program that reports its disparity.

## Traps already known from reading

- Both emulators double the window's width for the pair, so the declaration must come before the surface grows (native-linux, "Declare before doubling").
- Azahar's touch mapping subtracts half the window width in SideBySideFull; a declared surface that KWin scales needs the pointer mapped through the surface, not through `framebuffer_layout.width`.
- Dolphin's "per eye resolution full" doubles the aspect for SideBySide; in a declared pair that doubling must go, each eye keeps its own aspect and size.

## Dolphin as built in the edition (ORDER 39, continuation 1)

Dolphin 2609.b+dfsg-1 (Debian's source and its four patches) with one change set, `dolphin-order39.patch` of the lane (not offered upstream: Dolphin takes contributions from humans, not from AI agents).

- **One output.** `StereoMode` is Off or SideBySide, and SideBySide means both eyes as separate complete pictures, left eye first, declared to the desktop as full side by side. Half side by side, top and bottom, anaglyph, quad buffer, passive, the swap, "full resolution per eye", depth, convergence and their hotkeys are not built. An older configuration holding any other mode reads as the one output. The 3D choices of the Graphics page are "3D: Off / On" and a "Display Settings..." button (`systemsettings kcm_kscreen`); the size of each eye is the Internal Resolution.
- **Declaration.** Dolphin always runs on X11: `Main.cpp` forces `QT_QPA_PLATFORM=xcb` ("games do not launch on Wayland"), so the program is under Xwayland and the declaration is the X11 one. `DolphinQt/StereoDeclare.cpp` declares the render window (`stereo_declare_x11`, class game 3D) or, with the render widget inside the main window, declares it as a child of the main window (`stereo_declare_x11_child`, one view size), reads the person's limits (`stereo_depth_x11_get_limits`) and removes the declaration when 3D is turned off.
- **The picture.** `Presenter` fits one eye's picture into one half of the window (`EyeRegionWidth`) and draws the right eye the same rectangle one half to the right, so nothing is stretched or squeezed. The window is two views wide because Stereo KWin makes a declared X11 window hold both.
- **The fit (stereo-two-cameras, "one rule"):** `VideoCommon/StereoFit.cpp`. Dolphin's geometry shader moves each eye by `offset * (w - convergence)` in clip space. For a point at distance `w`, with `u = 1 / w`, the horizontal difference of the two eyes as a fraction of one eye's width is `a - b * u` (a = offset, b = offset * convergence; positive behind the screen). With the nearest pixel allowed to pop by P and the farthest to sink by S (the person's limits divided by 1920), the largest `b` is `(P + S) / (u_max - u_min)` and `a = S + b * u_min`. The depth of the frame is read from the EFB just before an XFB copy clears it (`FramebufferManager::ReadEFBDepthRange`), the next frame uses the result; the background counts (a frame that does not fill the screen has the far plane in it). Without limits there is no 3D.
- **A renderer or desktop that cannot.** A renderer without geometry shaders (the Software renderer) shows a message box "3D is not available with this renderer (NAME): it needs geometry shaders. Showing 2D." and declares nothing; a desktop without declaration support 10 (limits) gets "3D needs a desktop that takes both eyes and gives its depth limits (Stereo KWin); showing 2D." (code path read, not run).

## The rig, the content and the rows

- **Rig:** an image of its own from `debian:testing` with the edition's repository at pin 1001 (and deb-multimedia's source, which the edition's FFmpeg needs), the packages `kwin-wayland xwayland mesa-vulkan-drivers libstereo-declare-dev dolphin-emu x11-utils libxcb-cursor0`, the fake input client; the build image adds `apt-get build-dep dolphin-emu`, `cmake ninja-build ccache`. `docker run` needs `--shm-size 2g` (Dolphin's memory arena lives in /dev/shm: with the default 64 MB it dies with a bus error), `--cap-add SYS_NICE`, the render node and its group.
- **Content with real depth, free:** `scripts/emulator-depthtest/depthtest.c`, 100 lines of GX (libogc, zlib licence): three planes of 10 vertical stripes at w = 40 (red), 80 (green) and 160 (blue) in a perspective projection (near 10, far 300), each plane filling a third of the picture; the background is the far plane. Built with devkitPPC from the image `docker.io/devkitpro/devkitppc@sha256:f97cca81c09ce3a24ebb34cc3e0eb515a9d0490ae3c8be6f1d8e7f4960f17170` (libogc: zlib licence, Michael Wiedenbauer (shagkur) and Dave Murphy (WinterMute)); the program is ours (MIT). `depthtest.dol` sha256 e9880d4abf2d57245d92baa4a7680aa386e3d52bfb4185178c0ff8481a9e10f4. No game, no firmware, no key.
- **A run:** `dolphin-cell.sh NAME BACKEND -b` inside the rig: `kwin_wayland --virtual --xwayland`, `kwinrc [StereoDepth] SunkLimit/PoppedLimit` written first, Dolphin started with `-u` of its own, `-e depthtest.dol`, `-v Vulkan|OGL|"Software Renderer"`, `GFX.ini [Stereoscopy] StereoMode = 1`, three captures (ScreenShot2), `xprop` of every X window for `_KDE_NET_WM_STEREO_CONTENT*`. `analyze.py CAPTURE SUNK POPPED` pairs the edges of each plane by polarity between the eyes and compares with the prediction of the rule.
- **Red** (Debian's package, its side by side): the capture is `stereo: false`, 1280 wide (one picture), no window has a `_KDE_NET_WM_STEREO_CONTENT` property, the render window is 640x480 and holds both eyes squeezed to 320 px each, in Vulkan and in OpenGL.
- **Green, the shift at the shipped limits (10 and 4 px of a view 1920 wide; 640 px view: far 3.33, near -1.33):** measured mean right-minus-left shifts near -1.33, middle +1.33, far +2.67 px against predicted -1.33, +1.36, +2.71 (errors 0.00, 0.03, 0.04), identical in Vulkan and OpenGL. At 30 and 12: -4.00, +4.00, +8.00 against -4.00, +4.08, +8.12. At 60 and 24: near -8.00 and middle +8.00 against -8.00 and +8.15; the far plane (16.2 predicted) is past half the stripe period (10.7 px) and reads as its alias, -5.0: the content cannot say more there. With both limits 0: 0 of the window's pixels differ between the eyes (decoded arrays), the three planes at 0.00.
- **The interface:** with the render widget inside the main window (declared as a child), 0 of 67,200 pixels of the window's 2D part differ between the eyes, the 3D child 14 percent (OpenGL) and 27 percent (Vulkan).
- **A renderer that cannot:** the Software renderer: message box on screen, `stereo: false`, nothing declared.

## Traps, symptom first

- **Dolphin dies at once with "Bus error (core dumped)" in a container.** Cause: its memory arena is a shared-memory file and Docker's /dev/shm is 64 MB. Fix: `--shm-size 2g`. Found with the exit code 135 of the process and the failing `mmap` on /dev/shm.
- **Dolphin ignores `-C GFX.Settings.StereoMode=1`.** Cause: the section is `Stereoscopy` (`GFX_STEREO_MODE` is `{GFX, "Stereoscopy", "StereoMode"}`), and the analytics question is `Dolphin.Analytics.PermissionAsked`, not `Analytics.Analytics...`. Found in `Core/Config/GraphicsSettings.cpp`. A `-C` that names no key is silent.
- **A cell shows the "Do you authorize Dolphin to report information" box over the game.** Put `[Analytics] Enabled = False, PermissionAsked = True` in the `Dolphin.ini` of the user folder.
- **The fit reads a "farthest" pixel that is the nearest.** Dolphin's depth buffer is 1 at the far plane: with GX projection elements p22 and p23 a point at distance w reads `near + range * (1 - p22 + p23 / w)` (measured: a plane at w = 40 reads 0.7759 for p22 -0.0345 and p23 -10.345). The first formula had the opposite sign.
- **Both eyes drawn, the right half of the window black, the left half squeezed.** In about one run of three on Vulkan (5 pairs in 8, OpenGL 8 in 8) the swapchain stays one view wide (the Vulkan surface reports `currentExtent` 640x480 with min and max the same) while the X server holds the window at 1280x480 (read with XGetGeometry); each recreation answers the same and the program recreates every frame. Not solved in this milestone; it is the declared X11 window's size seen by Mesa's WSI against the server's (vr-to-3d's openxr-runtime-full-sbs.md describes the two sizes). The host re-reads the server's size every 50 ms and asks for a new surface until the backbuffer matches (40 tries); OpenGL needs none of it.
- **Edges paired across a shift larger than half the stripe period.** Periodic test content aliases: 16 px reads as -5 for stripes 21.3 px apart. Pair edges by polarity and keep the limits where the largest shift is under half a period, or make the stripes irregular.
- **`docker run` cannot bind /var/tmp/sparky-repo-current.** It is a symlink; the daemon refuses to stat it. Mount its target.

## Not proven

A 3D display; a desktop without Stereo KWin (the message path was read, not run); NVIDIA's driver (the AMD render node and llvmpipe were visible to Vulkan; which one Dolphin drew with was not recorded); the on-screen display in both eyes (Dolphin draws it once over the whole window; not checked, probably in one eye only); Wii games and the GameCube's own 3D scenes (only the test program); the per-game depth percentage Dolphin kept in game settings is gone with the rest.
