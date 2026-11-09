# No head on a 3D screen: the view from the mouse, the separation from the kind of display

Learned on DisplayXR, xrizer and an OpenVR program with a scene of known depth (ORDER 478 milestone 2, November 2026).
A 3D screen has no head.
An OpenVR or OpenXR program that expects one gets its view from the runtime's keyboard and mouse driver (qwerty), and the eye separation and screen plane come from a choice the person makes, with one default for each kind of display.
Both live in the runtime, so every program gets them with no setting of its own, and nothing in KWin changes ([openvr-on-the-openxr-runtime.md](openvr-on-the-openxr-runtime.md) has the chain).

## Where the numbers come from

A legacy application (no `XR_DXR_display_info`) never chooses its own camera.
`xrLocateViews` returns, for each eye, a pose and a field of view that are complete for rendering (DisplayXR: `docs/architecture/extension-vs-legacy.md`, "The View Path").
xrizer turns them into OpenVR's head pose (`WaitGetPoses`, device 0), `GetEyeToHeadTransform` and `GetProjectionRaw`.

| What | Where it comes from |
| --- | --- |
| Head pose | the qwerty head device: W A S D Q E move, a right-button drag with the pointer turns, arrow keys turn, Space goes back to the start. No tracker runs. With no input the pose stays exactly where it is |
| Eye offsets | the display's reported eye separation (sim_display: a fixed 60 mm; a tracked display: the viewer's eyes) times the camera rig's `ipdFactor`, half to each side |
| Field of view | the rig's vertical field of view with each eye's frustum shifted toward the shared window at `convergenceDiopters` (the zero parallax plane, 1/diopters metres) |
| The rig's starting numbers | the legacy camera profile: `DXR_LEGACY_CAMERA_RIG` (inline JSON or a path), else `app-profiles/<executable>.json` in the runtime's configuration directory, else the view class below |

The closed form for a point at distance Z, as a fraction of the canvas width (positive behind the screen plane):

```
p(Z)/W = ipd * m2v * (convergence - 1/Z) * eyeSeparation / (2 * tan(vFov/2) * aspect)
```

Because `eyeSeparation` and the canvas aspect are the only display inputs (DisplayXR #2451, fixed in #2452), the same numbers give the same fraction of the canvas on any display.

## The selector and its defaults

The view class is the person's choice of display kind, never read from the output (a desktop can drive a 3D television and a viewer at once).
`DXR_VIEW_CLASS` in the process environment, else the first line of the file `view-class` in the runtime's configuration directory, else the display's default, `screen`.
A value that is neither `screen` nor `headset` is refused and said: one error line names the source, the value and the accepted names, and the default applies.
Anaglyph shares the screen's default (the brief's two kinds); libstereo-policy keeps anaglyph at 0.7 of a framed screen if it ever gets its own value.

| Class | `ipdFactor` | `convergenceDiopters` | Eye offsets | Infinity | 2 m | 0.8 m |
| --- | --- | --- | --- | --- | --- | --- |
| `screen` | 0.43 | 0.89 | 25.8 mm apart | 2.0 % behind | 0.9 % behind | 0.8 % in front |
| `headset` | 1.075 | 0.89 | 64.5 mm apart | 5.0 % behind | 2.2 % behind | 2.0 % in front |

Where each number comes from: the headset takes 2.5 times the separation of a framed screen (libstereo-policy's factor, the edition's one depth source); infinity at 2.0 % on a screen is the edition's browser, measured; the pop at the nearest working distance (0.8 m, a proposal) is 0.4 of the sunk side, the ratio of libstereo-policy's popped limit (0.079 degrees) to its sunk limit (0.198 degrees).
The 2.0 %, the 0.8 m and the plane they give (0.89 diopters) have no recorded design: they are proposals, Daniel's call.

## The proof, at two settings

1. A client of your own that draws squares of known size and depth from the values OpenVR returns (head pose, eye-to-head, raw projection tangents), by ray casting each pixel through exactly those, so nothing is shifted after the drawing.
   Anchor the scene to the first head pose it sees, so a head that moves afterwards moves the view of a world that stays put.
   Print every frame's returned values next to the scene.
2. Run it through xrizer into DisplayXR on a headless Stereo KWin ([openvr-on-the-openxr-runtime.md](openvr-on-the-openxr-runtime.md)), once per class, and capture the output (3840x1080 for a 1920x1080 view: the eyes side by side).
3. Predict each square's picture in each eye from the returned values: a pinhole camera per eye, the returned tangents as the off-axis frustum, 8x8 samples per pixel.
   Measure the centroid of each square's colour in the capture by the fraction of the pixel it covers.
   Disparity is the left centroid minus the right.
4. Measured, per class (4 squares at 0.8, 2, 6 and 30 m, both eyes): centroid error 0.077 px rms for the screen class and 0.070 px for the headset class, horizontal disparity error 0.085 and 0.042 px rms, vertical disparity error 0.000 px, 0 swapped pixels, and the capture equals the client's own eye images pixel for pixel.
   The disparity of the 0.8 m square is 15.5 px at the screen class and 38.7 px at the headset class, the ratio of the separations.
5. Controls that must fail: each class's capture against the other class's returned values (horizontal disparity error 25 px rms), and a selector value that is not a class (refused, the error line, the default applies).
6. The pose: real events through KWin's fake input, phases with a capture after each.
   No input: the head pose is exactly the same over 90 frames.
   W held: the head moves along its own forward axis and nothing else; D: along +x; S: backward along the turned view; a right-button drag of 100 px turns the view to the right and leaves the position alone.
7. The picture of each eye changes as a camera moved, not as a shifted copy: after D the squares' sideways shifts follow 1/Z (fitted slope -467.1 px per metre against -467.2 predicted, intercept 0.03 px, residual 0.07 px); after W each square's area changes as the returned views predict (within 1 %), the square the picture does not cut grew by (Z/Z')^2 (2.885 against 2.885).

## Traps

### VR_Init says "vrclient Shared Lib Not Found (102)"

- **Symptom:** the OpenVR program exits at `VR_Init`; the runtime path in `openvrpaths.vrpath` exists.
- **Cause:** the runtime directory's `bin/linux64/vrclient.so` was a symlink with an absolute target in the folder it was copied from, and the copy lost it.
- **Fix:** `ln -s ../../libxrizer.so bin/linux64/vrclient.so`, relative, inside the copied directory.
- **How found:** `VR_Init` returned code 102, not 100: the path was read, the library was not there.

### The pointer never reaches the runtime's window, the keyboard does

- **Symptom:** W A S D move the view; a right-button drag does nothing; with `DXR_QTRACE=1` the log has FOCUS_IN and FOCUS_OUT but no BUTTON_PRESS.
- **Cause:** KWin's fake input device exists only while the program that authenticated it is connected, and the seat's pointer capability appears when it does and goes when it leaves.
  A script that calls the tool once to place the pointer and again to press loses the first events of every call: Xwayland has not made its `wl_pointer` yet.
- **Fix:** one program for the whole gesture, with a wait after the first move: `pa 960 540 w 800 bd 273 w 300 pm 100 0 w 300 bu 273` (absolute move, wait for Xwayland to take the pointer, button down, motion in steps of at most 8 px, button up).
- **How found:** KWin's server-side Wayland log (`WAYLAND_DEBUG=server`) showed `wl_seat.capabilities(2)` then `(3)`, `(7)`, `(6)`, `(2)` within 30 ms of each call, and the button press arriving before `get_pointer`.

### A capture does not match the pose in the log

- **Symptom:** one capture of a series is off by tens of pixels, the others by 0.1 px.
- **Cause:** the runtime reads input between frames, so a key held for a commanded second keeps moving the view after the script's `ku`, and the capture shows a frame older than the log's last line.
  The CPU ray caster runs at about 2 frames per second, which makes the gap a few frames.
- **Fix:** capture only after the last six logged poses are identical, and again check they still are after the capture; take the pose from the frame number logged just before the capture.
  Do not infer a speed from the hold time: distance depends on frames, not seconds.

### A predicted centroid is off by a few pixels only for a near or a rotated square

- **Symptom:** the check passes with the head still and fails after it moved forward or turned, by 2 to 3 px, for the near square and for a square cut by the picture's top.
- **Cause:** the prediction and the measurement both looked inside a window sized from the square's expected area; a square that grew, or that the picture cut, fell partly outside it and both numbers were truncated the same way.
- **Fix:** the window is the bounding box of the square's four corners seen by the eye (a projection keeps lines straight), with a few pixels of margin.
- **How found:** a full-image prediction (2x2 samples over the whole picture) agreed with the measurement to 0.08 px where the windowed one was 3 px away.

### Antialiasing in the client limits what can be measured

The client averages 3x3 samples per pixel, so an edge is placed to a third of a pixel and a centroid to about 0.1 px.
That is why the horizontal disparity error is 0.04 to 0.09 px and not zero; the limit asked for is 0.5 px.

### A per-title profile makes the class look ignored

- **Symptom:** `DXR_VIEW_CLASS=headset` and the eye separation does not change.
- **Cause:** `DXR_LEGACY_CAMERA_RIG` or `app-profiles/<executable>.json` exists; the class is only the default of the profile and the person's more specific record wins.
- **How found:** the log has a `Legacy camera profile:` line with the profile's numbers and no `View class:` line.

### The gamepad cannot give the pose on desktop Linux

- **Symptom:** a pad is attached; the runtime's input plugin loader says `no registered provider claimed the system (2 declined)`; the head is still moved by WASD and the mouse.
- **Cause:** the gamepad provider (it drives the rig through the navigation role) reads pads with XInput, a Windows HID backend or GameController; `gamepad_backend_stub.c` is what desktop Linux compiles: `available = 0`, "no pad reader on this platform; evdev TODO(linux)".
  No open DisplayXR issue or pull request covers a Linux reader (searched 2026-11-09).
- **What would fix it:** a `gamepad_backend_evdev.c` that reads `/dev/input/event*` for devices with `BTN_GAMEPAD` and absolute axes, maps them onto `gamepad_state` (the hub, devices and mapping table need no change), plus a pure decoder with a test on synthetic `input_event` arrays.
  A test through a real device node needs `/dev/uinput`, which a container without the device cannot have; say so instead of faking it.

## Where the kind of display could come from

KWin tells a program, per output: the name, the description and the physical size through `wl_output` (zero or unknown for a virtual output or a projector); the modes with stereo flags (HDMI side by side, top and bottom, frame packing, anaglyph, rows, columns, checkerboard) through `kde_output_device_v2`, the current one marked; `stereo_glasses` (USB-C glasses known by EDID), `stereo_pair`, `stereo_swap_eyes`, `stereo_depth` (the depth source and a viewing distance in centimetres, 0 when it derives it); and per surface, `depth_state` (awake, the edges on the output's edge) from `kde_stereo_content_manager_v1`.
No event names a device class (monitor, television, projector, glasses, headset), and an X11 program on Xwayland sees only RandR (millimetres, a fixed 96 dpi guess) and the stereo content support version.
The one thing that says "headset" is KWin's own D-Bus answer, `org.kde.KWin /KWin headsetViews`, which lists the outputs that are split-eye displays; the runtime already links libdbus, and the answer is an empty array for a plain 2D output.
So the selector starts on `screen` everywhere, which is right for a framed screen and for anaglyph (both are announced as stereo modes); starting on `headset` for a headset output would take one small thing, a per-output device class set in Display Settings with the EDID's guess as its default, announced as one more `kde_output_device_v2` event.
The selector stays the person's either way.
