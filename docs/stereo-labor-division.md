# Stereo labor division in Sparky Stereo OS

Who does what to show a stereo picture, from the program to the screen, and what each part never has to care about.
Written for people who work on one part of the stack, not the whole OS: application, engine and toolkit developers, driver developers, display and hardware people.
Every rule points to the specification behind it; the references are at the end.

## In one minute

**KWin knows stereo, and only one kind: full side by side.**
Both eyes complete, side by side, left eye on the left, at any resolution.
This is how IMAX 3D projects: two complete pictures, one per eye, next to each other, never squeezed.

**Programs hand KWin full side by side and say so.**
That is all a program needs to know about displays.

**Every conversion happens at an edge.**
Before KWin, the program or its library turns whatever it has into full side by side.
After KWin, each output turns full side by side into whatever its display, projector, glasses or headset needs.

**Nothing in the middle knows about formats.**
No program knows about HDMI 3D, anaglyph colours, interleaved lines or shutter timing.
No driver knows about programs.

## What a program keeps, and the one option it needs

**A program works in 2D, as it always has.**
Its window keeps its normal size and position, windowed or fullscreen, exactly as in 2D.
Only the 3D content gets stereo, and KWin assembles it and puts it on the screen, so nothing else in the program changes and nobody has to worry about it.

**The one required option is the render resolution.**
- **Internal render resolution:** the size each eye is rendered at, higher than the output for sharpness, lower for speed.
- **Output at one eye's resolution:** the window's size when windowed, the screen's size when fullscreen, which every program already handles.

**The rest is KWin's:** the monitor's resolution and 3D mode, scaling each eye to its place, and assembling the stereo picture for each output.
No program offers output formats, 3D modes or monitor settings.

## The picture KWin understands

**Full side by side, left eye first.**
Each eye is a complete picture at its full aspect ratio, so the buffer is twice as wide as one eye.
It is HDMI 1.4's 3D structure 3, "side by side (full)" (`HDMI_3D_STRUCTURE_SIDE_BY_SIDE_FULL = 3` in the kernel's `include/linux/hdmi.h`), the layout SteamVR writes its stereo screenshots in, and the arrangement of IMAX 3D's two projectors.

**Any resolution.**
The buffer is the render resolution: higher than the window for sharpness, lower for speed.
KWin scales each eye to the window's place on screen, the way it scales any window.

**One value says it.**
A window declares full side by side, and nothing else exists to declare.
The declared value is 3, the same number as HDMI's 3D structure: `_KDE_NET_WM_STEREO_CONTENT` = 3 on X11, `side_by_side_full` in the `kde_stereo_content_v1` Wayland protocol.
Half side by side, top and bottom and right-eye-first are not inputs: they are converted at an edge.

**Windowed or fullscreen, it is the same.**
A stereo window sits on the ordinary desktop, next to 2D windows.

## Program developers: applications, games, engines

**Your part is the camera.**
Render the same world from two cameras, one per eye, and put the two pictures side by side.

**The two cameras:**
- Start from the camera you already have.
- Move it half the eye separation to the left for the left eye and half to the right for the right eye.
- Keep both looking straight ahead, parallel, and shift each view's frustum inward (an off-axis frustum), so both views meet at the screen's distance.
- Objects at that distance appear on the screen; nearer objects come out of it; farther ones go behind it.
- Do not turn the cameras inward (toe-in): with perspective, it bends the picture differently in each eye.
- An orthographic view has no perspective, so there the camera move is a small rotation around the point you look at.

**Render the whole frame once per eye.**
Shadows, lighting, reflections and post effects all run per eye, from that eye's camera.
That is what makes the result correct without per-game fixes.

**2D stays 2D.**
Your HUD, menus, crosshair, cursor and subtitles are drawn once, identical in both eyes, at the screen's depth.
Only the 3D world gets the second camera.

**Ways to hand it over:**
- Draw both eyes into one buffer twice as wide, and declare it through the shared helper (`stereo_declare_x11()` or `stereo_declare_wayland()` with `STEREO_SBS_FULL`).
- Or use the standard stereo APIs and let the system pack:
  - OpenGL quad-buffer: a `GLX_STEREO` visual (GLX 1.4) and the `GL_BACK_LEFT` and `GL_BACK_RIGHT` draw buffers (`glDrawBuffer`, OpenGL 4.6);
  - EGL: `EGL_EXT_multiview_window` with two views;
  - Vulkan: a swapchain with `imageArrayLayers` = 2 (`VK_KHR_swapchain`), offered through `maxImageArrayLayers`.
- Qt programs get the same through Qt (in progress: a declared Qt window gets the double-width buffer).
- Windows games under Proton get it through Wine and DXVK (in progress: Direct3D 11.1's standard stereo swapchain, `DXGI_SWAP_CHAIN_DESC1::Stereo` with `IDXGIFactory2::IsWindowedStereoEnabled` (DXGI 1.2), and Wine's render window for declared windows).

**Your sizes stay yours.**
Ask for your window at one eye's size, and read your size from the usual places: the GL and Vulkan size queries and the window events.
On Wayland your surface keeps its size and the buffer behind it is scaled onto it (`wp_viewporter`).
On X11 the real window is twice as wide behind the scenes, and the window manager's synthetic ConfigureNotify gives you your own size (ICCCM 4.1.5 and 4.2.3); a library that asks the X server for the raw window geometry sees the doubled window, and that is the one place a library adapts.

**Eye order:**
If your engine has its eyes reversed, fix it once, in your camera.
If your stream says right eye first, swap it once, where you read the stream: `content_interpretation_type` 2 in the frame packing SEI (H.264 Annex D, D.2.26 in the 08/2021 edition; H.265 D.3.16; H.274 8.6 for VVC), or Matroska StereoMode 11 instead of 1 (RFC 9559).

**You need no 3D hardware to work on it.**
A full side-by-side picture is an ordinary wide image: open it in GIMP or Krita and each eye is a half.
A screenshot of your window is that same picture.
Every output has an anaglyph mode, so red/cyan paper glasses show your depth on any screen.

## Toolkit and library developers: Qt, Wine, Mesa, players

**Your part is the double-width buffer and the declaration, once, for every program built on you.**
- Mesa packs the eyes from quad-buffer, multiview and two-layer swapchains into full side by side and declares it.
- Qt gives a declared window a buffer twice as wide, at a render resolution of its own (in progress).
- Wine gives a declared window's render window the full doubled size (in progress).
- Players read the stream's own packing and eye order (the frame packing SEI's `frame_packing_arrangement_type`: 3 side by side, 4 top and bottom, 5 temporal; Matroska StereoMode) and unpack it to full side by side before declaring, respecting the message's persistence (H.264 D.2.26, H.274 8.6.2).

**A library never offers output formats.**
No anaglyph, no interleaving, no "3D TV mode" settings: those belong to the outputs.

## KWin: the middle

**KWin knows stereo, not formats.**
It composes the desktop with each stereo window's two eyes in their places, 2D windows in both eyes, and hands one full side-by-side picture to each output.
It does not know left from right beyond the convention: left eye first.

## Outputs: where formats live

**Each output converts full side by side into what its device needs:**
- the display's own HDMI 3D modes: frame packing (3D structure 0), top and bottom (6), side by side half (8), switched by the HDMI Vendor Specific InfoFrame;
- anaglyph (red/cyan, Dubois least-squares matrices, with a set for CRT and one for modern panels) on any 2D screen;
- row, column and checkerboard interleaving for passive panels;
- frame-sequential for shutter glasses and DLP projectors;
- two outputs as one pair for dual projection;
- a headset, through SteamVR (OpenVR) and OpenXR.

**One eye flip per output.**
If a display, projector or pair of glasses shows the eyes reversed, flip that output once in Display Settings, and every 3D mode on it is right (in progress: today some modes come as left-first and right-first twins).

**A new kind of display means a new output filter, never a change in any program.**

## Driver developers: the smallest part

**Your part is to show the display's 3D modes and switch the display into them.**
- Expose the 3D modes the display declares in its EDID: the HDMI Vendor-Specific Data Block's `3D_present`, `3D_Multi_present` and 3D structure fields (parsed by `add_3d_struct_modes()` in `drm_edid.c`, carried as `DRM_MODE_FLAG_3D_*` in `drm_mode.h`).
- Send the HDMI Vendor Specific InfoFrame that tells the display which 3D structure it receives (`drm_hdmi_vendor_infoframe_from_display_mode()`).
- Time frame packing as HDMI 1.4 defines it: both eyes in one frame twice as tall, with the active space between them.
- Expose deep colour where the display declares it: `DC_30bit`, `DC_36bit` and `DC_48bit` in the same data block (10, 12 and 16 bits per colour, `drm_parse_hdmi_deep_color_info()`), through the connector's "max bpc" property.

**You never need to know about programs, cameras, packing or eye order.**
Stock i915 has done this since Linux 3.13.
Sparky Stereo OS carries the same for amdgpu, nouveau and NVIDIA's open kernel modules.

## Why it is cheap

Every vendor used to build the whole chain alone, from the game to the glasses, so every program had to know every display.
Here each part does one job: programs and engines own the camera, libraries pack once, KWin composes, outputs convert, drivers switch the display.
A new program needs no knowledge of displays, and a new display needs no change in any program.

## References

- **HDMI 1.4b** (HDMI Licensing): 3D structures, the HDMI Vendor-Specific Data Block (EDID) and the HDMI Vendor Specific InfoFrame; deep colour flags since HDMI 1.3. The Linux kernel's open implementation: `include/linux/hdmi.h`, `drivers/gpu/drm/drm_edid.c`, `include/uapi/drm/drm_mode.h`.
- **ITU-T H.264** (08/2021), Annex D, frame packing arrangement SEI, semantics in D.2.26.
- **ITU-T H.265**, D.3.16, frame packing arrangement SEI.
- **ITU-T H.274** (VVC SEI), 8.6, frame packing arrangement.
- **RFC 9559**, Matroska Media Container Format, the StereoMode element.
- **GLX 1.4** and **OpenGL 4.6**: stereo visuals and the left and right draw buffers.
- **EGL_EXT_multiview_window** (Khronos EGL extension registry).
- **Vulkan**, `VK_KHR_swapchain`: `VkSwapchainCreateInfoKHR::imageArrayLayers`, `VkSurfaceCapabilitiesKHR::maxImageArrayLayers`.
- **DXGI 1.2** (Microsoft): `DXGI_SWAP_CHAIN_DESC1::Stereo`, `IDXGIFactory2::IsWindowedStereoEnabled`.
- **Wayland**: `wp_viewporter` (wayland-protocols, stable); `kde_stereo_content_v1` (Sparky Stereo OS's addition to plasma-wayland-protocols).
- **ICCCM** 4.1.5 (configuring the window) and 4.2.3 (window movement, synthetic ConfigureNotify).
- **Eric Dubois**, "A projection method to generate anaglyph stereo images", ICASSP 2001.
- **OpenVR** (Valve) and **OpenXR** (Khronos), for headsets.
