# An OpenXR runtime that hands its eyes to Stereo KWin

Learned on DisplayXR (ORDER 34 and 34b, November 2026): an OpenXR runtime presents the two views of any OpenXR app as one window declared full side by side, so Stereo KWin's outputs show it on a 3D television, in anaglyph on any monitor, or as the left view on a plain 2D output.
The runtime keeps no knowledge of the screen.

## The shape

1. **The display processor says what its output is.** A runtime with display processors (DisplayXR's vendor plug-ins, sim_display) cannot tell from the pixels that an output is a stereo pair, so the display processor declares it, per instance and per mode.
   DisplayXR: `xrt_dp_scanout_caps::stereo_layout`, a `uint32_t` taken from the first `reserved[]` word (no ABI change; a plug-in built before the field wrote 0 there), holding the HDMI 1.4b 3D_Structure numbers; 3 is Side-by-Side (Full).
   The first form was a flag bit in `flags`; its maintainer asked for the field because layouts are mutually exclusive and bits allow contradictory combinations (DisplayXR #1928).
2. **The views are handed over as they were rendered.** Each view at the window's resolution (view scale 1.0 x 1.0, two tiles side by side), left first, copied 1:1 into a buffer twice the window's width.
   The window, and the canvas the views are rendered for, keep the window's size; only the swapchain and the canvas the display processor writes into are two views wide.
3. **The window is declared once.** On native Wayland, `kde_stereo_content_v1` value 3 on the app's surface, bound at version 2: from version 2 a declared surface without a viewport destination is one view wide, so the window keeps its size on screen.
   The request takes effect with the next commit, which the Vulkan WSI makes inside `vkQueuePresentKHR`: send it before the present that carries the first buffer of the new width.
4. **The runtime's own X11 window is declared too** (plain OpenXR apps run in it, under Xwayland on Plasma). When the root window's `_KDE_NET_WM_STEREO_CONTENT_SUPPORTED` is 3 or more, set `_KDE_NET_WM_STEREO_CONTENT` = 3 (CARDINAL/32) on the window; no `_KDE_NET_WM_STEREO_CONTENT_ONE_VIEW_SIZE`, because each view is rendered at the window's own size.
   Stereo KWin keeps the window's place and makes the X window twice as wide when it reads the property, which can be seconds later.
   Vulkan creates an X11 swapchain only at the window's current size (Vulkan 1.3, VK_KHR_xlib_surface: "it is only possible to create a new swapchain on this platform with imageExtent being equal to the current size of the window"), so the runtime presents both views only after the X window has doubled, and until then the window's own size.
   While doubled, everything but the swapchain sees one view: the window follow, the window metrics (the projection's canvas) and a legacy app's tiles.
   A fullscreen window doubles too: KWin keeps the program's own frame for a fullscreen stereo window and makes the X window twice that.
5. **Nothing is pretended.** Where the declaration cannot be made (no global, protocol version 1, a window manager without the announcement, an app's own X11 window, a build without `wayland-scanner`, a switch that turns it off), the buffer stays the window's size and one log line says why; the window shows the two views side by side, flat.
6. **The rendering mode counts, not only the display processor.** A 2D rendering mode hands the display processor one view, so the declaration is withdrawn there even when the display processor's own output setting still says "full side by side", and made again when a stereo mode returns.

## The layout field: the 0 trap and the clamp

- **One number per layout, HDMI's.** The values are the 3D_Structure numbers of the HDMI Vendor-Specific InfoFrame (HDMI 1.4b section 8.2.3); the Linux kernel names them in `enum hdmi_3d_structure` (`include/linux/hdmi.h`: frame packing 0, field alternative 1, line alternative 2, side by side full 3, L + depth 4, L + depth + graphics + graphics-depth 5, top and bottom 6, side by side half 8).
  The HDMI text itself is not free; check the numbers against the kernel enum.
- **0 is not HDMI's 0.** HDMI's 0 is *frame packing*, but a field that older plug-ins already write as 0 must keep meaning "an ordinary weave". Both can be true only while nothing acts on frame packing: say it in the header, with the clause, so whoever adds frame packing gives it a value of its own. Our path acts on 3 alone, so nothing collides today.
- **Unknown reads as 0**, with a `clamp` function next to the enum, as `weave_scope` is clamped. The test pins 3, 0, the other HDMI numbers (1, 2, 4 to 8) and values past the table (255, 0x80000003, 0xFFFFFFFF), and that only 3 makes `outputs_full_sbs()` true.
- **Only 3 goes to the compositor.** The KDE stereo content protocol carries one value (`none` 0, `side_by_side_full` 3), so a layout other than 3 puts nothing on the wire; do not "pass the value straight through". Stereo KWin takes one format and its outputs do every other, which keeps spatial work out of every program.
- **A claim knob for the test.** sim_display's `SIM_DISPLAY_STEREO_LAYOUT=N` changes what the DP claims, not what it renders (like `SIM_DISPLAY_WEAVE_SCOPE`); with 8 or 4294967295 the run shows no `create` at KWin and the two views flat.
- **The protocol keeps its KDE name.** Other desktops already run each other's protocols unchanged: GTK 3 binds KDE's `org_kde_kwin_server_decoration_manager` (gdk/wayland/gdkdisplay-wayland.c), wlroots implements it (types/wlr_server_decoration.c), GNOME Shell's AppIndicator extension implements `org.kde.StatusNotifierWatcher` (statusNotifierWatcher.js), and KWin recognises GNOME's screen reader by `org.gnome.Orca.KeyboardMonitor` (src/a11ymanager.cpp, `checkPermission`; the file was `a11ykeyboardmonitor.cpp` earlier, so search by the string).

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
7. **Controls that must fail the LEFT/RIGHT rule:** the same run with the declaration switched off (`DXR_STEREO_DECLARE=0`) and with an output mode that does not report layout 3 (`SIM_DISPLAY_OUTPUT=squeezed`) show both views side by side in both eyes, identical, and KWin receives no `create`; a display-processor build with the tiles placed the other way round shows blue in the left eye (325,316 and 324,831 swapped pixels in the 800x450 window on two captures).

## Recipe: rerun the proofs after a rebase or a change of the layout field

1. Rebuild the runtime and the two cube apps (`scripts/build_linux.sh --apps` builds the loader and the apps in the same container after the runtime: wait for the container to exit, not for the plug-in file), then run the whole `ctest` and compare with the unpatched base: three tests fail in the Debian testing container on the base too (`tests_mirror_calib`, `tests_component_loader`, `tests_service_orchestrator_linux`).
2. Red and green for the unit test: make `xrt_dp_stereo_layout_clamp` return its input for unknown values, rebuild `tests_dp_full_sbs`, see it fail, restore it.
3. The cases are the two recipes below, plus two controls for the clamp: `SIM_DISPLAY_STEREO_LAYOUT=8` and `=4294967295` on both window kinds. Expect in the log `SIM_DISPLAY_STEREO_LAYOUT claims stereo_layout N` and no `FULL_SBS:` line, at KWin `create 0, set_content(3) 0`, the X window still 1920 wide, and both views side by side, identical, in both eyes.
4. Rebuild the planted plug-in from the new tree (apply the swap diff, build `DisplayXR-SimDisplay.so`, copy it, revert, rebuild) and compare its sha256 with the normal one before running the control.
5. A run of 20 cases takes about 35 minutes at four CPUs; the numbers to expect are in the two recipes (about 91 % on Wayland, 95 % on X11, 0 swapped pixels; the planted swap about 325 thousand pixels on Wayland and 1.97 million on X11 in two captures; 24 of 24 control captures fail the rule).

## Recipe: a plain OpenXR app on the runtime's own X11 window

1. **Session:** the same compositor started with `--xwayland`; the X programs (`xwininfo`, `xprop`) talk to `DISPLAY=:0` inside the container.
2. **The app:** DisplayXR's `cube_hosted_legacy_vk_linux` (no DisplayXR extension, so the runtime makes the window), `SIM_DISPLAY_OUTPUT=sbs_full`, `SIM_DISPLAY_PIXEL_W/H` the output's size, `DXR_CUBE_TEST_EYE_COLORS=1`.
   The window opens fullscreen on the panel's RandR monitor (`DXR_WINDOW_FULLSCREEN=0` makes it a plain window).
3. **Wait for the doubling, then capture.** Poll until the runtime's log says `FULL_SBS: the window manager holds the declared X11 window at both views' width` and `xwininfo -name DisplayXR` says `Width: 3840`; capture only then, because KWin may double a declared X11 window seconds after the client wrote the property.
4. **Expect in the runtime's log:** `the window manager announces version 9` (Stereo KWin +stereo3d43 and +stereo3d46), the declaration, the X server's 3840x1080 and one view 1920x1080, `presenting 3840x1080 px, the two views at the window's 1920x1080 each`.
5. **Expect from the X server and KWin:** `xwininfo` gives 3840x1080 for the X window, `xprop` gives `_KDE_NET_WM_STEREO_CONTENT(CARDINAL) = 3`, and a KWin script gives the window's frame 1920x1080, fullscreen.
6. **Expect in the captures:** view 0 in the left eye and view 1 in the right eye over about 95 % of the screen, 0 pixels swapped, on two captures a second apart; on the plain 2D mode the output's own screencast frame is view 0 only.
   Colour alone does not show a squeezed view: also measure the crate's bounding box in each eye (its width over its height stays between about 0.95 and 1.45 as it turns, and halves when a view is squeezed), and the boxes' vertical centres and heights must be equal between the eyes.
7. **A mode change in the session:** press V (Linux key code 47; qwerty's 2D/3D toggle in the runtime's window) through KWin's fake input.
   The property goes away, the X window returns to 1920x1080 and both eyes show the same 2D picture; V again declares it, the X window is 3840x1080 again and the eyes are right.
8. **Controls that must fail the LEFT/RIGHT rule:** `DXR_STEREO_DECLARE=0` and `SIM_DISPLAY_OUTPUT=squeezed` (nothing declared, the X window stays 1920x1080, both views squeezed side by side in both eyes, the crate about half as wide as tall); a display-processor build with the views swapped (blue in the left eye); and Debian's own KWin, which announces nothing (`FULL_SBS: ... the window manager announces no stereo declaration`, a single 1920x1080 picture with both views squeezed side by side).

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
- **Symptom:** after moving a flag to a field, one old test fails: `offsetof(struct xrt_dp_scanout_caps, reserved) == 12` (`tests_dp_weave_scope`).
  **Cause:** an earlier change had carved `flags` out of `reserved[0]` and the test pinned where `reserved` begins; the new field takes the next word, so `reserved` begins at 16 and the field is at 12. The caps struct on current `main` is `struct_size, weave_scope, flags, reserved[5]`, so "reserved[0]" in a maintainer's words means the first word still reserved.
  **Fix:** update the pin and add the field's own offset; the size stays 32.
  **How found:** the full `ctest` after the change, which a run of only the new test would not show.
- **Symptom:** `ninja: error: unknown target 'DisplayXR-SimDisplay'`, and the "planted" plug-in then equals the normal one.
  **Cause:** the target is `DisplayXR-SimDisplay.so`; a copy made after the failed build copies the unplanted file.
  **Fix:** build the target by its exact name, then compare the sha256 of the planted and the normal plug-in before using it as a control.
- **Symptom:** a wait loop on `_plugins/DisplayXR-SimDisplay.so` or on "no container" reports the build finished while `scripts/build_linux.sh --apps` is still building the OpenXR loader and the test apps.
  **Cause:** the runtime build finishes first, then the SDK and the apps are built in the same container.
  **Fix:** wait for the build container itself to exit and read the last line of its log (`Built weave_present_vk_linux`).
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

- **Symptom (what it would look like; found by reading first):** once a declared X11 window has doubled, the runtime's idea of the window's size flips between the X window's width and one view on every configure, and the views come out half as wide as they are shown.
  **Cause:** while a window is declared, Stereo KWin follows every configure with a synthetic ConfigureNotify (ICCCM 4.1.5) in the program's own units, one view; the X server's own ConfigureNotify carries the X window's size, and the synthetic one arrives after it.
  **Fix:** while declared, take the X window's size only from the server's events (response type without the 0x80 bit); know the doubling from the server's width becoming twice the width at the declaration, or from the synthetic size being half the X window's (the place can change in the same configure).
  **How found:** KWin's `X11Window::sendSyntheticConfigureNotify` (`width = client width x program scale / stereo window scale`); a unit test that takes the synthetic size instead fails 3 of its 7 cases.
- **Symptom:** after V (2D) the X window stays 3840 wide and both eyes show red, each a half of the single 2D view.
  **Cause:** qwerty's V switches the head's rendering mode to 2D, but sim_display's own output setting stays `sbs_full`, so `get_scanout_caps` still reports layout 3, and the runtime asked only the display processor.
  **Fix:** count the layout only in a rendering mode with two or more views on a 3D display state (`hardware_display_3d`); a 2D mode withdraws the declaration.
  **How found:** the mode-change case's third capture and the X window's width after the key.
- **Symptom:** the planted eye-swap control passed the LEFT/RIGHT rule.
  **Cause:** the plug-in manifest copied beside the planted binary (`200-sim-display.json`) names its binary by absolute path (`binary_path`), so the planted folder loaded the ordinary build.
  **Fix:** point `binary_path` at the planted copy, and read the runtime's `loading plug-in binary PATH` line in every control.
  **How found:** a control that must fail passed; the app's log named the build's path.
- **Symptom:** an image with Debian's own KWin, for the control without the announcement, does not install: `libegl-mesa0 ... Breaks kwin-wayland (< 4:6.7.4-2+stereo3d24~)`.
  **Cause:** the edition's Mesa breaks KWin builds older than +stereo3d24.
  **Fix:** install Debian's Mesa with it (each installed package of the `mesa` source with `+stereo3d` in its version, at Debian's version); apt then also removes the edition's `libkscreen-bin`, so that image has no `kscreen-doctor`, and its ScreenShot2 answers one picture (`stereo 0`). Debian testing's architecture packages are a binNMU (`4:6.7.4-2+b1`) while `kwin-data` is `4:6.7.4-2`: read each version from `apt-cache madison`.
- **Symptom:** `invalid version for org_kde_kwin_fake_input#4.destroy (4, need at least 5)`.
  **Cause:** the destructor came in version 5 of the interface.
  **Fix:** bind version 5 where it is offered, or never call `destroy` on 4. Reuse the stereo-proof-rig skill's `scripts/fakeinput.c` rather than writing another client (ORDER 34b wrote a second one before finding it).
- **Symptom:** after the cube's `DXR_CUBE_TEST_RESIZE=640x360` the window's decoration is 640 wide and its content still 800x450.
  **Cause:** the test hook declares the new size to the runtime but leaves the app's own `wp_viewport` destination at the old size, and KWin shows each view at the destination; the runtime's buffers are 1280x360, two 640x360 views.
  **How found:** KWin's protocol log (`set_window_geometry(0, -58, 640, 418)` and the decoration's new destination, no new `set_destination` on the main surface); the undeclared control shows its 640x360 buffer at 800x450 the same way, so it is the hook, not the declaration.

## Display zones and full side by side (ORDER 58b)

**What a zone is** (DisplayXR's `XR_DXR_display_zones` spec, ADR-027, and `XR_DXR_local_3d_zone`): an app's window holds N 3D zones (window-pixel rectangles, each with its own view framing and its own multiview picture), M flat 2D zones, and one "wish" mask, a per-pixel value from 0 (flat) to 1 (3D) in window pixels that says where the panel itself should switch.
The mask has two readers that must agree: the runtime's own composite (2D laid over the woven 3D wherever the mask is below 1) and, on a display with switchable lens zones, the display processor, which turns the lens cells.
Displays it matters for are the ones with a lens or barrier that can switch part of the panel; on a display that is 3D everywhere, or flat everywhere, the mask only decides which pixels get the weave.

**What the edition's build does today** (measured in lane 58b with DisplayXR's `cube_zones_vk_linux` on the staged package, Stereo KWin in the rig): sim_display is built with 2D and full side by side only, so there is no output that keeps pixel positions to substitute for the mask, and it logs "zone mask active ... drawn as it is".
On a native Wayland window (declared, target 3840x1080 for a 1920x1080 window) the zones and the 2D strip are laid in window coordinates, which is the left half of the doubled target: the left eye holds the scene, the right eye is entirely black (0 of 2,073,600 pixels lit; undeclared, with `DXR_STEREO_DECLARE=0`, both eyes hold it). On an app's own X11 window nothing is declared and both eyes hold the flat window.
**Why it is a decision and not a patch:** flat content in a stereo window is simply the same pixels in both views, so for every output KWin makes (anaglyph, interleaved, HDMI 3D) a 2D zone needs no mask at all; only a switchable-lens output needs to know where the 3D is, and that would be a declaration to KWin that no recorded design covers.
Options, in the words the person sees: keep today (one eye black in zone apps), present zone apps undeclared (two squeezed pictures side by side, flat, told through the problems engine), lay every zone in both halves (zone apps in true 3D, 2D zones flat at the screen), or the same plus the mask declared to KWin for panels with switchable lens zones.
The state is in the hand-back of ORDER 58b; the decision is Daniel's.

## Not done yet, and where it goes

- **An app's own X11 window** (`XR_DXR_xlib_window_binding`) and **adopt-own-window's child** (DisplayXR #2322) are not declared; the log says so.
  The app's window belongs to the app, which would see the doubling in its own events; the child would go through the X11 child declaration (`_KDE_NET_WM_STEREO_CONTENT_CHILDREN`, the place negotiation of support 8, libstereo-declare's child calls).
- **A legacy app's window smaller than the size its views are rendered at:** the runtime scales each view into its tile (DisplayXR's legacy behaviour, with or without the declaration); the route that keeps each view at its resolution is `_KDE_NET_WM_STEREO_CONTENT_ONE_VIEW_SIZE` with the X window two rendered views wide (native-linux, "X11 views at another size than their resolution").
- **Monado's xrgears** as a second plain client: not run yet. It builds with meson against the OpenXR loader DisplayXR's build makes (`_openxr-*/lib/pkgconfig/openxr.pc`) and needs glm, GLib's GIO and xxd; it runs in the runtime's own X11 window like `cube_hosted_legacy_vk_linux`, with no eye-colour hook, so its check is the declaration, the doubling and the geometry.
- **A real screen and a scanout:** the captures are the eyes KWin draws; an output filter's own pixels need a VKMS scanout or a real display.

## Perks

- DisplayXR's display processors already answer `get_scanout_caps` per mode, so a new output kind is one number and one helper, and every vendor plug-in can set it.
- KWin's protocol log is the cheapest proof of "declared once" for any program: it needs no client changes.
- A test hook that clears each view to its eye's colour turns any capture into a LEFT/RIGHT check; the cubes' `DXR_CUBE_TEST_EYE_COLORS=1` (`cube_handle_vk_linux` and `cube_hosted_legacy_vk_linux`) is the DisplayXR one.
- On X11 there is no protocol log, but the X server tells the same story for free: `xprop` shows the declaration on the window, `xwininfo` the X window's doubled width, and a KWin script the place on screen.
- One rig image serves every KWin build: replace only KWin (dpkg the staged packages, no network) and start the session with that image.

Credits: DisplayXR by David Fattal and its contributors; Monado by Collabora and its contributors, which DisplayXR derives from; KWin by the KDE developers; the stereo declaration and libstereo-declare by Daniel Campos Ramos.
