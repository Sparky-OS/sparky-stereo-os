# Emulators that hand Stereo KWin a declared pair (Dolphin and Azahar)

Learned on ORDER 39, milestone 1 (November 2026): the reconcile and the reading of both programs.
No emulator was built or run in that milestone; every row below that needs a run says "not run".

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

## Proof rows still to run (none run in milestone 1)

1. Dolphin and Azahar published or upstream: what KWin receives (undeclared 2D surface), red.
2. Our build: one declaration, both eyes captured as decoded arrays, the shift in pixels with its sign, identical eyes at zero depth, the interface flat, Vulkan and OpenGL each, a renderer that cannot give two views telling the person.
3. Free test content, pinned by address and hash: homebrew built with devkitPro's libogc (GameCube and Wii) and libctru with citro3d (3DS); no game, no firmware, no key.
