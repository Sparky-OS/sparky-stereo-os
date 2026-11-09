# An OpenVR program on the edition's OpenXR runtime, no SteamVR

Learned on xrizer, DisplayXR and Valve's OpenVR sample (ORDER 478 milestone 1, November 2026).
An ordinary OpenVR program runs through xrizer into DisplayXR with no SteamVR anywhere, and both of its eyes reach Stereo KWin as one window declared full side by side.
Nothing in KWin changes: the OpenVR road ends in the same OpenXR projection layer as any other route ([who-runs-whose-vr-software.md](who-runs-whose-vr-software.md)), and the runtime's declaration does the rest ([openxr-runtime-full-sbs.md](openxr-runtime-full-sbs.md)).

## The chain

```
OpenVR program (hellovr_vulkan, a game)
  -> libopenvr_api.so (Valve's client library, BSD-3-Clause)
  -> openvrpaths.vrpath  "runtime": [ DIR ]        (a JSON file in $XDG_CONFIG_HOME/openvr/)
  -> DIR/bin/linux64/vrclient.so                    (xrizer, GPL-3.0, a Rust cdylib)
  -> the OpenXR loader -> XR_RUNTIME_JSON or active_runtime.json -> DisplayXR
  -> one X11 window declared full side by side -> Stereo KWin's outputs
```

## How the OpenVR library finds the runtime

- The library reads `openvrpaths.vrpath` from `$XDG_CONFIG_HOME/openvr/` (else `~/.config/openvr/`).
  Its `runtime` list names directories; the library loads `DIR/bin/linux64/vrclient.so` from the first that has it.
  An empty list gives `VR_Init failed: Installation Not Found (100)` and the client exits: that is the visible failure, there is no silent fallback to anything.
- `cargo xbuild --release` in the xrizer checkout writes the runtime directory (`target/release/` holding `bin/linux64/vrclient.so` and a ready `openvrpaths.vrpath`).
  Point the file at that directory.
  A program can print the answer: `vr::VR_GetRuntimePath()` returns the directory it will use, which is the proof that no SteamVR path is in play.
- Prove there is no SteamVR: no package or file named steamvr, vrclient, vrserver, vrcompositor, vrstartup or vrmonitor in the image, the path above, and the client library built from Valve's source (its sha256 differs from the prebuilt binary the repository ships).
- The sample's own CMake refuses to configure without an `openvrpaths.vrpath` and needs Qt 5 and GLEW for samples you do not use.
  Build the one sample by hand instead: the API library with CMake (`-DBUILD_SHARED=ON -DUSE_LIBCXX=OFF`), then one `g++` line for `hellovr_vulkan_main.cpp` plus `shared/*.cpp` against the system SDL2 and Vulkan headers.

## What xrizer needs from a runtime

Read from xrizer's source and measured against DisplayXR:

- `XR_KHR_vulkan_enable` (the legacy extension) for Vulkan programs, `XR_KHR_opengl_enable` for OpenGL ones; it enables only what the runtime lists, so a missing optional extension is not an error.
  DisplayXR offers everything xrizer asked for; the only message is `XR_ERROR_FEATURE_UNSUPPORTED in xrCreateHandTrackerEXT: System does not support hand tracking`, twice, and the program goes on.
- It starts a first session with no graphics, tears it down, and creates the real session when the first texture arrives, because the legacy Vulkan binding needs the program's own instance, device and queue.
  Every runtime therefore sees an end then begin cycle in the first second ([the trap below](#both-eyes-show-view-0)).
- One swapchain of array size 2: the left eye is array layer 0, the right eye layer 1, and the projection layer names them with `imageArrayIndex`.
  The program's textures must be in `VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL` when it calls `Submit` (openvr.h, `VRVulkanTextureData_t`).
- The program gets its Vulkan instance extensions from `IVRCompositor::GetVulkanInstanceExtensionsRequired`, its physical device from `IVRSystem::GetOutputDevice`, its device extensions from `GetVulkanDeviceExtensionsRequired`.
  A client that follows that contract works on the discrete GPU and on lavapipe alike.
- DisplayXR logs one warning for a legacy Vulkan session: the program created the device, so the runtime has no queue of its own and the weave rate follows the render rate (`DXR_VK_QUEUE_LOCK=1` changes that).
  It is a note about pacing, not a fault.

## The proof recipe

Use the rig of [openxr-runtime-full-sbs.md](openxr-runtime-full-sbs.md): Stereo KWin on its virtual backend with the output's anaglyph twin, Xwayland on, ScreenShot2 captures at the output's size, the runtime's own X11 window (hosted legacy session) declared by DisplayXR.

1. A client of your own that submits one solid colour per eye through `IVRCompositor::Submit`: left red, right blue, `--swap` for the control. About 150 lines of C++ against `openvr.h` and Vulkan; hellovr has no such mode.
2. Run it with `HOME` pointing at a folder whose `.config/openvr/openvrpaths.vrpath` names the xrizer directory, `XR_RUNTIME_JSON` at DisplayXR's manifest, `DXR_PLUGIN_EXCLUSIVE=sim-display` and `SIM_DISPLAY_OUTPUT=sbs_full`.
3. Capture twice, a second apart.
   Expected (measured): left eye red 1.000, right eye blue 1.000, 0 swapped pixels, a 3840x1080 capture, the runtime's X window 3840x1080 with `_KDE_NET_WM_STEREO_CONTENT` = 3.
4. Controls that must fail: the eyes swapped in the client (2,073,600 swapped pixels), `DXR_STEREO_DECLARE=0` (each eye holds red and blue half and half: both views squeezed), Debian's own KWin (one 1920x1080 picture, `stereo 0`: no eyes, the rule fails by definition), an empty `runtime` list (the client prints the error and exits).
5. The 2D control: the runtime in its 2D mode on a plain 2D output gives one picture, view 0 alone (red 1.000, blue 0.000).
6. The real program: `hellovr_vulkan` unmodified through the same chain, with `SDL_VIDEODRIVER=x11` ([trap](#hellovr_vulkan-crashes-after-the-extension-lines)).
   Measured: the eyes differ at 1,282,066 of 2,073,600 pixels, the right eye is shifted +38.06 px against the left, the vertical shift is -0.01 px, and the left eye matches the 2D control at unit horizontal scale (correlation 0.344) better than the left half stretched back (0.158).
   The squeeze reading is a correlation, not a colour: a view squeezed into half the width matches the reference better when its left half is stretched back, which is what the declaration-off control shows (0.024 against 0.344).

## Traps

### Both eyes show view 0

- **Symptom:** the solid client's captures show red in both eyes (the swap control shows blue in both); the runtime log says `Sim display mode changed: 2D` when the first session ends and the fast path says `sRGB fast path drawn ... (1 draw(s))` for a two view layer.
- **Cause:** DisplayXR sizes a legacy app's atlas once, for the rendering mode active at that moment.
  When the first session ends, the display drops to mode 0; the second session is created in 2D (an atlas of one tile) and `xrBeginSession` then restores the 3D mode.
  The per frame sync updated the tile grid to 2 by 1 but, for legacy apps, never the atlas, so the second view fell outside it and was never drawn.
  Any legacy session that ends and begins again should meet it, not only xrizer's (not tested with another app).
- **Fix:** in the legacy branch of the per frame sync, resize the atlas to the mode's grid at the app's view size when the grid changes (the same call the extension app branch makes). Commit `dea3eca1a` on branch `order478m1-legacy-atlas-follows-mode` of the DisplayXR clone, 17 lines.
- **How found:** the two `Created atlas texture` lines of the second session (`1920x1080 ... tiles 1x1`, no 3840 wide one) against the first session's (`3840x1080 ... tiles 2x1`), and the draw count of 1 in `draw_raw_view_pass`; then `fast_path_view_count` clamps to `layout->views`.
  Red before the fix, green after, same client, same captures.
- A DisplayXR issue (2322) lists "OpenVR via xrizer" as an open question; this is its answer for the Vulkan route.

### hellovr_vulkan crashes after the extension lines

- **Symptom:** the log ends at `required device extensions: ...` and the shell prints `dumped core`.
- **Cause:** with `WAYLAND_DISPLAY` set SDL 2 picks its Wayland driver, and the sample reads `wmInfo.info.x11.display` for `vkCreateXlibSurfaceKHR`.
- **Fix:** `SDL_VIDEODRIVER=x11` (an environment variable; the sample is not changed). The companion window then appears under Xwayland beside the runtime's own window.
- **How found:** `libdecor` messages ("No plugins found, falling back on no decorations") in the log meant SDL was on Wayland; the source line 1101 uses the Xlib surface.

### hellovr_vulkan says it cannot open a SPIR-V file

- **Symptom:** `Error opening SPIR-V file: .../shaders/scene_vs.spv`, `BInit - Unable to initialize Vulkan!`.
- **Cause:** the sample opens `../shaders/` and `../cube_texture.png` relative to its executable's directory.
- **Fix:** install it as `hellovr/bin/hellovr_vulkan` beside `hellovr/shaders/` and `hellovr/cube_texture.png`.

### xrizer does not build

- `Unable to find libclang` (bindgen): install `libclang-dev`.
- `failed to launch glslc`: install `glslc` (Debian package from shaderc).
- Keep `CARGO_HOME` and `CARGO_TARGET_DIR` on the build disk; a release build is about 760 MB and the crates 140 MB.

### A flat undeclared window reads as two eyes

- **Symptom:** the Debian KWin control "passes" the left and right check.
- **Cause:** that KWin answers one 1920 px picture; split into two 960 px halves, the runtime's squeezed pair reads red then blue.
- **Fix:** treat a capture KWin answers as one picture (`stereo 0`) as having no eyes, so the rule fails by definition, as the control script of the full side by side rig does.

### The logs are huge

`RUST_LOG=xrizer=debug` writes 25 MB in 45 seconds; use `info` unless you read the call trace (`RUST_LOG=openvr_calls` names every OpenVR call).

## Perks

- xrizer's log is `$XDG_STATE_HOME/xrizer/xrizer.txt`; the lines `Creating OpenXR session with graphics API` and `Received game texture, restarted session with new data` mark the session restart.
- `IVRCompositor_029` and `IVRSystem_026` are the interface versions a current program asks for.
- xrizer reports the render size from the runtime: 1920x1080 per eye with DisplayXR's compromise scale of 1.0, so a program draws one view at the window's resolution and Stereo KWin does the single resize.
- Rust 1.85 or newer builds it (Debian testing's 1.97 was used).
