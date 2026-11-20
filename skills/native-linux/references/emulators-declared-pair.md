# Emulators that hand Stereo KWin a declared pair (Dolphin and Azahar)

A core limit of exactly 1 suppresses the piped core helper; a zero limit does not, as the [crash trap](../../stereo-proof-rig/SKILL.md#traps-that-fooled-us) explains.

Learned on ORDER 39 (November 2026). Milestone 1: the reconcile and the reading of both programs. Continuation 1: Dolphin built and run in a Stereo KWin. Continuation 3 (19 November 2026): the fit withdrawn, Dolphin's own Depth and Convergence back, the Vulkan pair from two image layers and its fault found in Mesa (rows below). Azahar is its own item and was not run.

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
- Dolphin: the render window (or, with Render to Main Window, the render widget, a child) is declared. On Vulkan the swapchain has two image layers and Mesa packs and declares them (see `qt-vulkan-two-views.md`); on OpenGL the packing is the presenter's and the declaration is libstereo-declare's.

## The depth: each program's own settings (Daniel, 2026-11-19)

- **Dolphin keeps its own Depth and Convergence.** Daniel, 2026-11-19, on the fit of continuation 1: "dolphin felt not 3D since that change"; "one separation setting, centralized, tailored TO THE SCREEN not to the element size"; "I accepted internal 3D programs settings". A program that renders its own pair with its own 3D settings keeps them ([one-separation-one-place.md](one-separation-one-place.md), exceptions). Nothing of ours reads the desktop's limits or scales the separation.
- **Dolphin's formula, from its source (2609b):** `stereo_depth = Depth * DepthPercentage * 0.00001` and `stereo_convergence = Convergence * ConvergencePercentage * 0.01` (`VideoCommon/VideoConfig.cpp`, lines 171 to 174); the left eye gets `-stereo_depth`, the right `+stereo_depth` (`GeometryShaderManager.cpp`, 55 to 57); each vertex moves by `pos.x += hoffset * (pos.w - stereo_convergence)` (`GeometryShaderGen.cpp`, 238 to 239). After the division by w the eyes differ by `2 * stereo_depth * (1 - stereo_convergence / w)` in normalized device coordinates, so a plane at distance w is `stereo_depth * (1 - stereo_convergence / w) * D` pixels apart on the screen (right minus left, positive behind it), D being the width the picture is drawn at.
- **What that means on the screen:** the shift is a share of the drawn picture, as a camera pair's is: the same scene in a window 640 wide and maximized on a 1920 wide output (the picture 1750 wide) measured +6.34 and +17.42 px for the near plane at Dolphin's defaults. The desktop's limits do not move it.
- **Azahar and the 3DS:** the console draws its own pair and has its own slider as part of the machine; today's behaviour is kept, the numbers are not measured yet (its own item).

## Traps already known from reading

- Both emulators double the window's width for the pair, so the declaration must come before the surface grows (native-linux, "Declare before doubling").
- Azahar's touch mapping subtracts half the window width in SideBySideFull; a declared surface that KWin scales needs the pointer mapped through the surface, not through `framebuffer_layout.width`.
- Dolphin's "per eye resolution full" doubles the aspect for SideBySide; in a declared pair that doubling must go, each eye keeps its own aspect and size.

## Dolphin as built in the edition (ORDER 39, continuation 3)

dolphin-emu 2609.b+dfsg-1+stereo3d1+lc1: Debian's 2609.b+dfsg-1 with two patches from branch `order39` of the edition's fork (recipe `sparky-os/packages/dolphin-emu-stereo-1` of the build tree). Not offered upstream: Dolphin takes contributions from humans, not from AI agents.

- **One output.** `StereoMode` is Off or SideBySide, and SideBySide means both eyes as separate complete pictures, left eye first, declared full side by side. Top and bottom, anaglyph, quad buffer, passive, the half-width eyes and the eye swap are not built; an older configuration holding any other mode reads as the one output. The Graphics page has "3D: Off / On", Dolphin's own Depth and Convergence sliders and a "Display Settings..." button (`systemsettings kcm_kscreen`); the game's own settings keep Depth Percentage, Convergence and Monoscopic Shadows; the hotkeys keep "Toggle 3D Side-by-Side" and the four depth and convergence keys.
- **Declaration.** Dolphin runs on X11 (`Main.cpp` forces xcb). OpenGL: `DolphinQt/StereoDeclare.cpp` declares the render window (`stereo_declare_x11`, class game 3D; support version 3) or, with Render to Main Window, the render widget as a child (`stereo_declare_x11_child`; support version 8); Stereo KWin makes the X11 window two views wide and the presenter draws each eye into its half at the eye's own size. Vulkan: the swapchain has two image layers (`VKSwapChain::CreateSwapChain`), Mesa packs them and declares the window with version 4, so the window stays one view wide and nothing races its size.
- **The interface.** The on-screen display (ImGui) is drawn once per eye at the same place in the window's halves on OpenGL, and into both layers by a passthrough geometry shader on Vulkan; the post-processing pass copies both layers there too.
- **On by default** (stereo-integrations-auto-enable, Daniel 2026-10-14, as PyMOL's edition build has it): `GFX_STEREO_MODE` defaults to the one output; a desktop that cannot take the pair shows 2D and says nothing unless the person turned 3D on (any config layer holds `StereoMode`); a renderer without geometry shaders and a Vulkan surface with one image layer are told in a message box. `UpdateActiveConfig` turns the active stereo mode off when the host or the backend says so, so the next frame follows. The no-GUI front end declares nothing: 2D, and a console and on-screen sentence when the person turned 3D on.
- **The person's language:** the eight new sentences are in Dolphin's catalogues for pl, pt_BR, fr, de, es, ja, ko, zh_CN and zh_TW, in Dolphin's own terms for Depth, Convergence and Internal Resolution; the messages are composed where they are shown (`tr()` with the renderer's name as `%1`, `GetStringT` in the no-GUI front end), because Dolphin's Qt translator looks a string up by its exact English text.

## The rig, the content and the rows

- **Rig:** an image of its own from `debian:testing` with the edition's published round at pin 1001 (and deb-multimedia's source), `kwin-wayland xwayland mesa-vulkan-drivers dolphin-emu x11-utils python3-xlib libkf6config-bin`, libstereo-declare 1.11.1 (1.11.0 and 1.12.0 abort a program that sets the library up on a private Wayland queue and destroys it); `docker run` with `--shm-size 2g`, `--cap-add SYS_NICE`, the render node and its group; one fresh session per row on a 1920x1080 virtual output (`scripts/emulator-depthtest/dolphin-cell.sh`); Dolphin's settings written as files (`GFX.ini [Stereoscopy] StereoMode, StereoDepth, StereoConvergence`, `[Settings] ShowFPS`); captures by ScreenShot2; the window tree's declarations by `x11_props.py`.
- **Content, free:** `scripts/emulator-depthtest/depthtest.c` (GX on libogc, zlib licence; the program is ours, MIT): three planes at w = 40 (red), 80 (green) and 160 (blue), each 80 % of a third of the picture, with stripes and gaps of pseudo-random widths so a shift has one match however large. devkitPPC from `docker.io/devkitpro/devkitppc@sha256:f97cca81c09ce3a24ebb34cc3e0eb515a9d0490ae3c8be6f1d8e7f4960f17170`; `depthtest.dol` sha256 093e1e4ee71f5ac3727f99554d5efd2f8f4747bab5d031932d5c40d8f1fcf018 (the folder's `build.sh` makes the same bytes). No game, firmware or key.
- **Measuring:** `measure.py CAPTURE DEPTH CONVERGENCE`: each plane's shift by cross-correlating its colour profile between the eyes along many rows (sub-pixel), its vertical shift, the drawn picture's width D from the render window's place, and the prediction from Dolphin's formula above. `osd.py` (the FPS overlay band in both eyes), `ui.py` (the main window's 2D part with Render to Main Window), `xvfb.py` (one picture or two halves on a plain X server).
- **Rows (build tree binary and the installed package, both renderers, one session each):** Depth 20 and 45 by Convergence 20 and 60 in a 640 wide window: near, middle and far planes +6.34/+9.50/+11.17, -6.34/+3.17/+8.00, +14.34/+21.50/+25.17 and -14.34/+7.17/+18.00 px against Dolphin's +6.40/+9.60/+11.20, -6.40/+3.20/+8.00, +14.40/+21.60/+25.20 and -14.40/+7.20/+18.00 (within 0.1 px; vertical 0); Depth 0: 0 pixels differ between the eyes; the desktop's limits at 30/12 and 0/0: the same shifts; maximized (the picture 1750 wide): +17.42/+25.97/+30.59 and -39.31/+19.66/+49.21 against +17.50/+26.25/+30.62 and -39.38/+19.69/+49.22. The FPS overlay: 2,410 pixels in each eye, 0 differ. Render to Main Window: 0 of 67,200 pixels of the 2D interface differ.
- **Vulkan's reliability:** 20 of 20 fresh sessions right on Mesa with patch 0047; 6 of 10 on the published Mesa +stereo3d26 (the other four drew each eye at half the window's width, below). OpenGL: 20 of 20.

## Traps, symptom first

- **Each eye drawn at half the window's width in some Vulkan sessions** (about four in ten; the picture 197 rows tall where 395 were due, the shifts still right on the screen). Cause: Mesa's X11 surface kept three fields of patch 0041 unset, so its extents were halved whenever its memory held old bytes; a stereo swapchain is never told it is out of date. Fix: Mesa patch 0047 (+stereo3d29). Found by a trace of the swapchain's capabilities against the window's own `XGetGeometry`; [`../scripts/vk-x11-surface-extent.c`](../scripts/vk-x11-surface-extent.c) makes it certain. The continuation 1 symptom (the right half black, the swapchain one view wide in a window two views wide) was the same fault on the old route.
- **A pass test that compares shifts only passes the half-width eye:** a shift on the screen scales with the drawn width, so a half-resolution eye stretched to its place reads right. Check the picture's own size too.
- **Dolphin dies at once with "Bus error (core dumped)" in a container.** Its memory arena is a shared-memory file and Docker's /dev/shm is 64 MB: `--shm-size 2g`.
- **Dolphin ignores `-C GFX.Settings.StereoMode=1`.** The section is `Stereoscopy`; write `GFX.ini` instead. The analytics question goes with `[Analytics] Enabled = False, PermissionAsked = True` in `Dolphin.ini`.
- **The host's crash list shows the emulator** although the container had `--ulimit core=0`: the session script killed the compositor first and Dolphin died on its lost X connection. Kill Dolphin first by SIGKILL.
- **Debian's KWin cannot be installed in an edition image:** the edition's `libegl-mesa0` Breaks `kwin-wayland (<< 4:6.7.4-2+stereo3d24~)`. "A desktop without Stereo KWin" runs on a plain X server (Xvfb) instead.
- **Lean Code wrote a C++ comment into Dolphin's empty GraphicMods markers.** Without a payload source plan the restore maps an installed file to its source by the hash of the source's projected form; `Externals/picojson/picojson.cpp` is one comment, so its projected form is empty like every marker. Fix in the recipe: `debian/sparky-lean-payload-sources.json` (the installed Sys folder to `Data/Sys`). Found by comparing the package with Debian's file by file.
- **`docker run` cannot bind a repository folder given as a symbolic link.** The daemon refuses it; mount the link's target.

## Not proven

A 3D display; Wii or GameCube games (only the test program); the Mesa package with patch 0047 (proved with a development build of RADV and lavapipe mounted over the installed ones); the translations' native review; the per-game settings through the game's own properties dialog (they are upstream's code unchanged).
