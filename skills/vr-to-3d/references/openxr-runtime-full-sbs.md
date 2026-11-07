# An OpenXR runtime that hands its eyes to Stereo KWin

Learned on DisplayXR (ORDER 34, November 2026): an OpenXR runtime presents the two views of any OpenXR app as one window declared full side by side, so Stereo KWin's outputs show it on a 3D television, in anaglyph on any monitor, or as the left view on a plain 2D output.
The runtime keeps no knowledge of the screen.

## The shape

1. **The display processor says what its output is.** A runtime with display processors (DisplayXR's vendor plug-ins, sim_display) cannot tell from the pixels that an output is a stereo pair, so the display processor declares it, per instance and per mode.
   DisplayXR: `XRT_DP_SCANOUT_FLAG_FULL_SIDE_BY_SIDE` in the existing `xrt_dp_scanout_caps::flags` word (no ABI change; a plug-in built before the bit wrote 0 there).
2. **The views are handed over as they were rendered.** Each view at the window's resolution (view scale 1.0 x 1.0, two tiles side by side), left first, copied 1:1 into a buffer twice the window's width.
   The window, and the canvas the views are rendered for, keep the window's size; only the swapchain and the canvas the display processor writes into are two views wide.
3. **The window is declared once.** On native Wayland, `kde_stereo_content_v1` value 3 on the app's surface, bound at version 2: from version 2 a declared surface without a viewport destination is one view wide, so the window keeps its size on screen.
   The request takes effect with the next commit, which the Vulkan WSI makes inside `vkQueuePresentKHR`: send it before the present that carries the first buffer of the new width.
4. **Nothing is pretended.** Where the declaration cannot be made (no global, protocol version 1, an X11 window not yet handled, a build without `wayland-scanner`, a switch that turns it off), the buffer stays the window's size and one log line says why; the window shows the two views side by side, flat.

## Recipe: the proof on a headless Stereo KWin

1. **Image:** `debian:testing` by digest, the edition's published repository at pin 1001 (Stereo KWin, its Mesa and Qt), the runtime's build dependencies, PipeWire, GStreamer's core and base elements, Python with numpy and PIL. Every container that runs apt starts with the HTTPS-only helper.
2. **Compositor:** `kwin_wayland --virtual --width 1920 --height 1080` with `KWIN_VIRTUAL_STEREO_MODES=1` (the output lists its 3D twins), on the NVIDIA card through CDI (`--device nvidia.com/gpu=0`, the render group by number, `--cap-add SYS_NICE`, `GBM_BACKEND=nvidia-drm`).
   `kscreen-doctor -o` then lists `1:1920x1080@60.00*!  2:(3D-SBS)(virtual-3D:1)  3:(3D-TaB)(virtual-3D:2)  4:(virtual-3D:5)  5:(virtual-3D:6)`; 5 is anaglyph (modern), 4 anaglyph (CRT), from KWin's `StereoLayout` order.
   `kscreen-doctor output.Virtual-0.mode.5` puts the output in the anaglyph twin.
3. **The app:** DisplayXR's `cube_handle_vk_linux --platform=wayland --windowed` with `SIM_DISPLAY_OUTPUT=sbs_full`, `DXR_PLUGIN_EXCLUSIVE=sim-display`, `SIM_DISPLAY_PIXEL_W/H` set to the output's size, `DXR_CUBE_WINDOW=800x450`, and `DXR_CUBE_TEST_EYE_COLORS=1`, which clears view 0 red and view 1 blue under the scene.
   Pin the app's Vulkan driver with `VK_DRIVER_FILES` (NVIDIA's or lavapipe's ICD file), so no other card is tried.
4. **Expect in the runtime's log:** `FULL_SBS: the window is declared full side by side, left view first (kde_stereo_content_v1 version 2, value 3); presenting 1600x450 px, the two views at the window's 800x450 each`.
5. **Expect from KWin:** a KWin script printing `bufferGeometry` gives `800x450` for the window (one view wide on screen while the runtime presents 1600x450).
   KWin started with `WAYLAND_DEBUG=server` logs every request it received: exactly one `kde_stereo_content_manager_v1#N.create(...)` and one `set_content(3)` for the session, and a `destroy()` at the end.
6. **Expect in the captures:** ScreenShot2 `CaptureScreen` answers `stereo 1`, 3840x1080; inside the window's rectangle the left eye is about 91 % red and the right eye about 91 % blue (the rest is the cube and the floor grid), 0 pixels with the eyes swapped, 0 pixels differing between the eyes outside the window.
   On the plain 2D mode, one frame of the output's own screencast (`zkde_screencast` output stream through PipeWire) shows the window red, 0 % blue: the left view only.
7. **Controls that must fail the LEFT/RIGHT rule:** the same run with the declaration switched off (`DXR_STEREO_DECLARE=0`) and with an output mode that does not set the flag (`SIM_DISPLAY_OUTPUT=squeezed`) show both views side by side in both eyes, identical, and KWin receives no `create`; a display-processor build with the tiles placed the other way round shows blue in the left eye (325,316 and 324,831 swapped pixels in the 800x450 window on two captures).
   A plain OpenXR app on the runtime's own X11 window (DisplayXR's `cube_hosted_legacy_vk_linux`, session with `--xwayland`) logs that its window is not declared and shows both views side by side, flat, with 0 pixels differing between the eyes.

## Traps

- **Symptom:** KWin's log in a CDI container starts with `kwin_core: Failed to open drm node /dev/dri/renderD128: No such file or directory`.
  **Cause:** not a failure. The virtual backend walks every DRM device `drmGetDevices2()` reports from sysfs, which lists the card the container was not given; its node is absent, so the backend opens the next one, the NVIDIA render node.
  **How found:** `org.kde.KWin.supportInformation` says `OpenGL renderer string: NVIDIA GeForce RTX 3060`.
- **Symptom:** the screencast frame of the output in the anaglyph twin is the left view in plain colours, (255,0,0) inside the window, no anaglyph.
  **Cause:** the output stream of a virtual output renders the scene once, as for a 2D output; it is not the output filter's result. ScreenShot2 rerenders each eye instead.
  **Fix:** prove the eyes with ScreenShot2's stereo capture; prove a filter's own pixels on a scanout (a VKMS guest), not with either capture.
  **How found:** counting the colours of the frame.
- **Symptom:** ScreenShot2 answers a stereo capture, twice the output's width, although the output is in its plain 2D mode.
  **Cause:** Stereo KWin captures both eyes whenever the output has eyes or stereo content is on it.
  **Fix:** for "a 2D output shows the left view only", read the 2D output's own screencast frame.
- **Symptom:** a KWin script finds no property that says a window is declared stereo.
  **Cause:** scripts see only `declaredStereoContentClass` and `declaredStereoContentSubclass`.
  **Fix:** start KWin with `WAYLAND_DEBUG=server` and count the `create(` and `set_content(` requests. Count those, not binds: the session's Qt clients (kscreen-doctor, the capture tool) bind `kde_stereo_content_manager_v1` at version 3 for their own windows.
- **Symptom:** none, a design trap. A runtime that presents on its app's Wayland connection cannot use libstereo-declare's per-thread state (the library initialises on the thread that dispatches the display, which is the app's), and DisplayXR's packages refuse new shared-library dependencies.
  **Fix:** generate the protocol client from the XML with `wayland-scanner` and run it on a private event queue with a proxy wrapper, the way the runtime's other helper objects on that connection do.
- **Symptom:** none, a design trap. DisplayXR's existing `sbs` output crops the centre half of each view and scales it up, and `squeezed` halves each view's width.
  **Fix:** neither is full side by side under the any-resolution rule, so the declared output is a new mode with each view at the window's resolution; the existing modes stay as they were, undeclared.
- **Symptom:** the app's log says `Atlas swapchain: 1920x1080` for two views at full scale.
  **Cause:** `cube_handle_vk_linux` sizes one swapchain for all tiles and clamps it to `maxImageRectWidth`, the panel's width; each tile is then at most half the panel wide.
  **Fix:** keep the test window at most half the declared panel width (an 800x450 window on a 1920x1080 panel), or raise `SIM_DISPLAY_PIXEL_W`.
- **Symptom:** installing `gstreamer1.0-plugins-good` in a container on the edition's repository fails: `librsvg2-2 ... Depends libdav1d7 (>= 1:1.5.4) but none of the choices are installable`.
  **Cause:** plugins-good pulls gdk-pixbuf, glycin and the edition's librsvg2, which is built on deb-multimedia's dav1d.
  **Fix:** read one raw frame with core elements: `pipewiresrc path=NODE num-buffers=1 ! videoconvert ! video/x-raw,format=RGB ! filesink`, then write the PNG with PIL; take the size from the `GstFileSink ... caps =` line of `gst-launch-1.0 -v`, whose `format` comes last.
- **Symptom:** `su: Authentication failure` when a root container step drops to the lane user whose passwd entry was mounted.
  **Fix:** `setpriv --reuid=UID --regid=GID --clear-groups`.
- **Symptom:** `git clang-format` stops on `Configuration file(s) do(es) not support Objective-C` in DisplayXR.
  **Fix:** `git clang-format --extensions c,h,cpp,hpp`; where a change only adds a line to a hand-aligned table, keep the table's own alignment rather than the whole-statement reflow clang-format proposes.
- **Symptom:** three unit tests fail in a Debian testing container (`tests_mirror_calib`, `tests_component_loader` at `mkdtemp`, `tests_service_orchestrator_linux`).
  **Cause:** the container, not the change: the same three fail on the unpatched base built the same way.
  **How found:** a worktree of the base commit, the three test targets built and run.

## Not done yet, and where it goes

- **X11 windows.** The runtime's own window for plain OpenXR apps (DisplayXR's `cube_hosted_legacy_vk_linux`, or Monado's xrgears) is an X11 window under Xwayland, which the change logs and leaves flat.
  The route: `_KDE_NET_WM_STEREO_CONTENT` = 3 on the window when the root's `_KDE_NET_WM_STEREO_CONTENT_SUPPORTED` is 3 or more; Stereo KWin then makes the X11 window two views wide while placing it one view wide, so the runtime's window follow, its window metrics (the Kooima canvas) and its X11 1:1 gate divide the X window's width by two.
  The Vulkan 1.3 specification sets the difference: on Wayland "the surface size is defined by the images presented to it", while on X11 "it is only possible to create a new swapchain on this platform with imageExtent being equal to the current size of the window" (unless present scaling is used); so the X11 swapchain follows the X window only after KWin has doubled it, and KWin may double it seconds late under load.
- **A mode change in the middle of a session** (withdrawing the declaration and shrinking the buffer) is in the code and not yet driven in the rig: it needs a key sent through KWin's fake input.

## Perks

- DisplayXR's display processors already answer `get_scanout_caps` per mode, so a new output kind is one bit and one helper, and every vendor plug-in can set it.
- KWin's protocol log is the cheapest proof of "declared once" for any program: it needs no client changes.
- A test hook that clears each view to its eye's colour turns any capture into a LEFT/RIGHT check; the cube's `DXR_CUBE_TEST_EYE_COLORS=1` is the DisplayXR one.

Credits: DisplayXR by David Fattal and its contributors; Monado by Collabora and its contributors, which DisplayXR derives from; KWin by the KDE developers; the stereo declaration and libstereo-declare by Daniel Campos Ramos.
