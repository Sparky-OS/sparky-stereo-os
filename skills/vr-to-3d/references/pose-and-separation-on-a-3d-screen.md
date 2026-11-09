# No head on a 3D screen: the view from the mouse or a pad, the separation from the desktop's depth limits

Learned on DisplayXR, xrizer and an OpenVR program with a scene of known depth (ORDER 478 milestones 2 and 2b, November 2026).
A 3D screen has no head.
An OpenVR or OpenXR program that expects one gets its view from the runtime's keyboard and mouse driver (qwerty) or from a gamepad, and the eye separation and screen plane come from the desktop's depth limits and the person's choices on top, not from numbers of the runtime's own.
Both live in the runtime, so every program gets them with no setting of its own, and nothing in KWin changes ([openvr-on-the-openxr-runtime.md](openvr-on-the-openxr-runtime.md) has the chain).

## Where the view comes from

A legacy application (no `XR_DXR_display_info`) never chooses its own camera.
`xrLocateViews` returns, for each eye, a pose and a field of view that are complete for rendering (DisplayXR: `docs/architecture/extension-vs-legacy.md`, "The View Path").
xrizer turns them into OpenVR's head pose (`WaitGetPoses`, device 0), `GetEyeToHeadTransform` and `GetProjectionRaw`.

| What | Where it comes from |
| --- | --- |
| Head pose | the qwerty head device: W A S D Q E move, a right-button drag with the pointer turns, arrow keys turn, Space goes back to the start; or the gamepad provider (left stick moves, right stick looks, triggers go up and down). No tracker runs. With no input the pose stays exactly where it is |
| Eye offsets | the display's reported eye separation (sim_display: a fixed 60 mm; a tracked display: the viewer's eyes) times the camera rig's `ipdFactor`, half to each side |
| Field of view | the rig's vertical field of view with each eye's frustum shifted toward the shared window at `convergenceDiopters` (the zero parallax plane, 1/diopters metres) |
| The rig's numbers | a per-title record wins (`DXR_LEGACY_CAMERA_RIG` inline JSON or a path, else `app-profiles/<executable>.json`); otherwise they follow the depth limits below |

## The depth limits, and the rig that keeps to them

Stereo KWin announces, for the output a window mainly sits on, how far behind and in front of the screen anything may go: `kde_stereo_depth_v1.depth_limits` (`kde-stereo-content-v1`, since version 5), `sunk` and `popped` in pixels of a view 1920 wide, "the user's limits built on the output's display: a headset gets more separation, a framed 3D screen less".
A program reads them and draws inside them, so its nearest thing and the desktop's popped menu agree on one screen.
The runtime does the same for the camera; the order of importance is the browser's and the desktop's: the person's choice, built on the display.

The closed form, for a point at distance Z, as a fraction of the canvas width and positive behind the plane (DisplayXR `legacy-camera-profile.md`, "Disparity does not depend on the display"):

```
p(Z) = k (c - 1/Z)      k = ipd * m2v * eyeSeparation / (2 * tan(vFov/2) * aspect)      c = convergence in diopters
```

With the sunk limit s (pixels / 1920) at infinity, the plane at D metres and the popped limit q:

```
ipdFactor = s * D * (2 * tan(vFov/2) * aspect) / (m2v * eyeSeparation)       convergence = 1 / (D * m2v)
p(Z) = s * (1 - D / Z)                      the popped limit is met at Z = D * s / (s + q)
```

That is the browser's form (its far parallax and `dom.vr.flat.screen-plane-mm`, default 1 m).
The eye separation is divided out, so the limits hold on any display; the metres-to-world scale cancels in the separation and moves the convergence.
A scene nearer than D s / (s + q) pops past the popped limit: the camera does what the geometry says and a finished picture is never shifted; the person who wants a scene to reach nearer moves the plane (D = Znear (s + q) / s).
The runtime logs one `Depth limits:` line with the values in force, that distance included, whenever they change.
The runtime's comfort rule (the plane no nearer than the viewer) still holds, and the line says when it binds.

The person's choices on top, with the browser's names (`dom.vr.flat.mode`, `depth-strength`, `screen-plane-mm`):

| Choice | Environment | File in the configuration directory |
| --- | --- | --- |
| class `tv` or `headset` | `DXR_VIEW_CLASS` | `view-class`, first line |
| strength, percent | `DXR_VIEW_DEPTH_STRENGTH` | `view-depth`: `depth-strength=` |
| screen plane, mm | `DXR_VIEW_SCREEN_PLANE_MM` | `view-depth`: `screen-plane-mm=` |
| absolute sunk, popped | `DXR_VIEW_SUNK_PX`, `DXR_VIEW_POPPED_PX` | `view-depth`: `sunk-px=`, `popped-px=` |

`tv` leaves the announced limits as they are; `headset` takes libstereo-policy's headset factor (2.5) over them; unset is as announced; the class is the person's, never read from the output (a desktop can drive a 3D television and a viewer at once).
Absolute values replace the limit they name.
The environment wins over the file key by key, the files are read again twice a second so a change reaches the next frame, and a wrong value (not a number, out of range, an unknown class or key) is refused and said once, never dropped quietly and never read past to the next source.

## Which window can be told its limits (a finding of milestone 2b)

`depth_limits` is an event on a Wayland surface (`kde_stereo_content_manager_v1.get_depth`).
A hosted legacy session's window is an X11 client of Xwayland, which cannot ask: KWin sends the limits only to windows whose surface tree has a depth object, and it publishes no X11 property or D-Bus value for them.
An app-provided Wayland surface (`XR_DXR_wayland_surface_binding`) could ask, but those sessions do not use the qwerty camera rig.
So today the hosted rig has no source of the compositor's limits: with none and no absolute sunk value the runtime logs `Depth limits: none` with the reason and keeps DisplayXR's own rig (ipdFactor 1, convergence 0.5 diopters); the class, strength and plane have nothing to scale.
The smallest change that would close it, in KWin: write the same two numbers it already sends to Wayland clients, as 24.8 fixed point in one `CARDINAL/32[2]` property `_KDE_NET_WM_STEREO_DEPTH_LIMITS` on an X11 window that declares stereo content, from `StereoDepthStates::update()`, and raise `_KDE_NET_WM_STEREO_CONTENT_SUPPORTED` to 10.
The other way is a native Wayland window for the hosted session in the runtime.

## The proof

1. What KWin announces: a small Wayland window that follows its desktop depth (`kde_stereo_depth_v1`) prints each `depth_limits` event; run it on the headless Stereo KWin with the person's `[StereoDepth]` `SunkLimit` and `PoppedLimit` in `kwinrc` (10 and 4, the shipped values), rewrite the file while it runs and ask KWin to reconfigure (`org.kde.KWin.reconfigure`): the events follow, 10/4, then 24/9.5, then 3/1.25, and KWin's own side of the Wayland log (`WAYLAND_DEBUG=server`) shows the same numbers.
   The virtual output has no physical size, so KWin's display factor is 1 and the announced values equal the person's.
2. The runtime: an OpenVR client of your own that draws squares of known size and depth from the values OpenVR returns (head pose, eye-to-head, raw projection tangents), by ray casting each pixel through exactly those, so nothing is shifted after the drawing.
   Anchor the scene to the first head pose it sees.
   Run it through xrizer into DisplayXR on the headless Stereo KWin, once per set of limits, and capture the output (3840x1080 for a 1920x1080 view: the eyes side by side).
3. Predict from the limits alone, d(Z) = -S (1 - D/Z) in pixels of a view 1920 wide (left centroid minus right, positive in front), and from the returned views (a pinhole camera per eye, 8x8 samples per pixel).
   Measured at 4 squares (0.8, 2, 6, 30 m): against the limits 0.0024 px rms at 10/4 and 0.066 px at 24/9.5, against the returned views 0.04 px horizontal and 0.000 px vertical, 0 swapped pixels, no square past a limit.
4. Live: rewrite `view-depth` while the runtime runs; the next logged line is the new limits and the capture after it follows them.
5. Controls that must fail: a capture against the other set's limits (9.8 px rms), a value that is not a number (refused once, no limits then), no limits at all (said, DisplayXR's own rig).
6. The keys' proof of milestone 2 stands: the pictures change as a camera moved, not as a shifted copy (the shifts follow 1/Z).

## The gamepad on Linux

The gamepad provider reads the pad through a per-platform backend; desktop Linux had the stub (`available = 0`, "evdev TODO") until `gamepad_backend_evdev.c`.
It is three layers so each can be tested alone: `gamepad_evdev_decode.c` (pure: `struct input_event` arrays in, `gamepad_state` out), `gamepad_evdev_core.c` (which pads exist, which one speaks, what happens when one goes, with the system calls behind a small table so a test runs on pipes) and the backend (open, ioctl, inotify).
The mapping is the kernel's gamepad protocol (`Documentation/input/gamepad.rst`): `BTN_SOUTH`, `BTN_EAST`, `BTN_NORTH`, `BTN_WEST` are A, B, X, Y by position; the d-pad is `BTN_DPAD_*` or `ABS_HAT0X/Y`; the sticks are `ABS_X/Y` and `ABS_RX/RY` with "negative is left/up", so Y is negated to the +Y up of `gamepad_state`; the lower triggers are `ABS_HAT2*` by the protocol and `ABS_Z`/`ABS_RZ` in the legacy drivers (xpad, hid-microsoft, hid-sony), or 0 and 1 from `BTN_TL2`/`BTN_TR2`; a pad with no `ABS_RX` has its right stick on `ABS_Z`/`ABS_RZ`.
A batch counts only at `SYN_REPORT`; `SYN_DROPPED` discards the torn batch and the device layer reads the real state (`EVIOCGKEY`, `EVIOCGABS`).
A node is a pad when it has `BTN_SOUTH`, a left stick and no relative axis.
Several pads are all read and the one touched last speaks; a pad that fails to read (`ENODEV`, end of file) is closed and the next takes over; inotify on `/dev/input` finds a pad plugged in later, with a rescan every second while none is open.
It tells the person when `/dev/input` cannot be opened (the provider declines), when no node can be read by this user (a pad's node belongs to the seat's session or the group `input`) and that rumble is not sent.

The tests: `tests_gamepad_evdev` on synthetic event arrays and on pipes (104 assertions); six mutations of the source each turn it red (the stick's Y not negated, `SYN_DROPPED` not asking for a resync, North and West swapped, the first pad speaking instead of the last touched, end of file not dropping a pad, a hat's sign), and the unmutated tree is green.
The real kernel device is `tests/gamepad_evdev_uinput.py` with the `gamepad_evdev_probe` binary; it creates virtual pads through `/dev/uinput` and its header says what it must print.
Never run it on a machine whose session or games should not see a new pad.

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

### A 100 px drag turns the view 11.345 degrees, not 10

- **Symptom:** the turn is 13 % more than "0.1 degrees per pixel" predicts.
- **Cause:** two things, both in the qwerty driver. `SENSITIVITY 0.1` (`qwerty_xcb.c:41`) is multiplied by the head's look speed `0.02` (`QWERTY_HMD_INITIAL_LOOK_SPEED`, `qwerty_device.c:57`) in `qwerty_add_look_delta` (`yaw_delta += yaw * look_speed`, line 1028) and the sum is an angle in radians (`math_quat_from_angle_vector`, lines 544-558): 0.002 rad, 0.1146 degrees, per pixel, not 0.1. And the X server hands the driver integer pointer positions (Xwayland truncates `wl_pointer.motion`'s fixed point): the pointer travelled 960.0 to 1059.988, X reported 960 to 1059, and the driver's per-event differences (`root_x - last_x`, line 547, with `last_x` taken at the button press, line 515) add up to 99.
- **Check:** 99 px * 0.002 rad = 0.198 rad = 11.3446 degrees; measured 11.345.
- **How found:** the compositor's own log of the motion events (`wl_pointer.motion` with fractional positions) against the integer positions the driver sees; the arithmetic matched to three decimals.

### A capture does not match the pose in the log

- **Symptom:** one capture of a series is off by tens of pixels, the others by 0.1 px.
- **Cause:** the runtime reads input between frames, so a key held for a commanded second keeps moving the view after the script's `ku`, and the capture shows a frame older than the log's last line.
  The CPU ray caster runs at about 2 frames per second, which makes the gap a few frames.
  The same happens when the limits change: a capture taken before the change must be read against the views of its own frame, not the last logged ones (`--frame` of `check_limits.py`, from the frame number logged just before the capture).
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

### A per-title profile makes the limits look ignored

- **Symptom:** `DXR_VIEW_SUNK_PX` is set and the eye separation does not change.
- **Cause:** `DXR_LEGACY_CAMERA_RIG` or `app-profiles/<executable>.json` exists; a per-title record is the person's more specific choice and the rig does not follow the limits then.
- **How found:** the log has a `Legacy camera profile:` line with the profile's numbers and no `Depth limits:` line.

### The same wrong value is logged every half second

- **Symptom:** the log fills with the same `depth: DXR_VIEW_SUNK_PX holds "abc"` line.
- **Cause:** the settings are read again twice a second so that an edited file takes effect; each read refused the same value again.
- **Fix:** the refusal is kept and logged only when its text changes.
- **How found:** 17 identical lines in a 40 second case.

### A mutation test stays green after the source was put back

- **Symptom:** after a script that breaks a source line, builds, runs the test and restores the file, the next build says `ninja: no work to do` and the test is red on an unmutated tree.
- **Cause:** `cp file file.orig; mutate; ...; mv file.orig file` gives the file the copy's modification time, older than the mutated object, so the build keeps the mutated object.
- **Fix:** `touch` the file after restoring it. A run of several mutations on one tree also needs this between them, or a later red can be an earlier mutation's.

### Two pads: the wrong one speaks after both report at once
- **Symptom:** every synthetic test passes, and on a real kernel device pad A pressed right after pad B was released shows no button: B still speaks, with nothing held.
- **Cause:** "touched last" was the time of the read, and the reader goes through the pads in slot order, so within one poll the pad read last wins.
- **Fix:** take the time from the kernel's stamp on the batch's last `SYN_REPORT`, and set the node's clock with `EVIOCSCLOCKID` to `CLOCK_MONOTONIC`, the clock the reader compares with. A report with no stamp takes the time of the read.
- **Found by:** the real-device script on the A10, the one step a pipe-driven test could not show, because the fake delivered one pad per poll. A real uinput device gives both in the same poll.

### The gamepad cannot give the pose on a machine with no readable pad

- **Symptom:** a pad is attached; the log says `no registered provider claimed the system` or the head still moves only with WASD.
- **Cause:** the reader declines where `/dev/input` cannot be opened; where it can, it needs a readable node: a pad's node belongs to the seat's active session (udev's `uaccess`) or the group `input`; a user with neither sees no pad, and the first scan says "no input node can be read by this user".
- **How found:** run `gamepad_evdev_probe` as that user: it prints `DECLINED`, or `STATE connected=0` with the reason before it.

## Where the kind of display could come from

KWin tells a program, per output: the name, the description and the physical size through `wl_output` (zero or unknown for a virtual output or a projector); the modes with stereo flags through `kde_output_device_v2`, the current one marked; `stereo_glasses`, `stereo_pair`, `stereo_swap_eyes`, `stereo_depth`; and per surface, `depth_state` and `depth_limits` from `kde_stereo_content_manager_v1`.
No event names a device class (monitor, television, projector, glasses, headset), which is why the limits are what a program reads: KWin has already built them on the output's kind and size.
Because the output's kind is not announced, the class `headset` takes the 2.5 over the limits as announced; on an output KWin already knows as a headset the limits are already larger and the class is left unset.
