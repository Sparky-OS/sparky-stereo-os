# The Camera page (ORDER 570, 2026-11-15)

System Settings had no page for a webcam: the only place was Kamoso, and Kamoso keeps its own choice.
`sparky-stereo-camera` adds the Camera page (under Multimedia, beside Sound) and a command of the same name that does everything the page does.
Check freshness first: written on 2026-11-15 from the package `sparky-stereo-camera` 0.1.0, PipeWire 1.6.9, WirePlumber 0.5.19, Kamoso 26.04.0 and Qt Multimedia `6.11.2-3+stereo3d15`.

## Recipe: what lives where

1. **The default camera is the session's default video source.** WirePlumber keeps two metadata keys in the `default` metadata object: `default.configured.video.source` (the person's choice) and `default.video.source` (what every program that asks PipeWire for a camera gets). Set the first and WirePlumber moves the second and saves the choice:

       pw-metadata -n default 0 default.configured.video.source '{ "name": "NODE_NAME" }' Spa:String:JSON

   WirePlumber writes `~/.local/state/wireplumber/default-nodes` (`default.configured.video.source=NODE_NAME`, older choices below as `.0`, `.1`) about a second later, so a test that reads the file waits a few seconds. The page and `sparky-stereo-camera default NODE_NAME` do exactly this call, with the name written by a JSON writer, never pasted into a string.
2. **A format, size, frame rate or control is set on the V4L2 device**, with the kernel's own ioctls (`linux/videodev2.h`): `VIDIOC_QUERYCAP`, `VIDIOC_ENUM_FMT`, `VIDIOC_ENUM_FRAMESIZES`, `VIDIOC_ENUM_FRAMEINTERVALS`, `VIDIOC_S_FMT`, `VIDIOC_S_PARM`, and for controls `VIDIOC_QUERY_EXT_CTRL` (ask with `V4L2_CTRL_FLAG_NEXT_CTRL | V4L2_CTRL_FLAG_NEXT_COMPOUND`), `VIDIOC_QUERYMENU`, `VIDIOC_G_EXT_CTRLS`, `VIDIOC_S_EXT_CTRLS`. Every program that opens the device sees the control; a program that sets its own format overrides the saved one. A button is written any value; an inactive control answers `EACCES`; a value the driver does not take answers `ERANGE` or `EINVAL`; a stream held by another program makes `S_FMT` and `S_PARM` answer `EBUSY` while controls still work (UVC).
3. **A PipeWire node reaches its device by `api.v4l2.path`** (`/dev/videoN`), the property PipeWire's V4L2 source gives a real camera. A node without it (libcamera) has no V4L2 controls here, and the page says so on that camera.
4. **What the person chose is a file any program can read:** `~/.config/sparky-stereo-camera/cameras.ini`, a group for each camera named by its V4L2 `bus_info` and card (so the choice follows the camera to the same port), with the packing (the stereo layer's input id), the mode and the controls that differ from the driver's default. A camera starts at its own defaults when plugged in, so the user service `sparky-stereo-camera.service` (`sparky-stereo-camera watch`) applies the file when a camera appears and every two seconds checks for a new one.
5. **The preview is a PipeWire stream** (`pw_stream`, raw BGRx/BGRA/RGBx/RGBA, any size) copied into a `QVideoSink`, shown by a QML `VideoOutput`. A two-lens camera that sends one packed picture gets a packing from the layer's list (the same names; the page's catalogues carry the layer's own translations), and the pair is drawn by a second window: `VideoOutput` with `stereoInput` and `stereoSwapEyes` declares it to Stereo KWin (`kde_stereo_content_v1.set_content(3)` on a subsurface placed below). The embedded preview shows what the camera sends, flat.

## Which programs follow the default (measured on 2026-11-15, rig of the lane)

| Program | Result |
|---|---|
| A PipeWire client that says it is a video capture (GStreamer `pipewiresrc` with `media.type=Video`, `media.category=Capture`, `media.role=Camera`) | follows: linked to the camera that was the default, each of three in turn (`rig/who-is-linked.py` prints the link) |
| Kamoso 26.04.0 | does not follow: its `DeviceManager` takes the first device of GStreamer's `Video/Source` device monitor (`src/devicemanager.cpp`; kamosorc's `deviceObjectId` overrides it), and it linked to the same camera for three different defaults |
| Qt Multimedia's camera (FFmpeg backend), FFmpeg's `-f v4l2` | read V4L2 directly: the plugin has `qt.multimedia.ffmpeg.v4l2camera` and `v4l2cameradevices` and no PipeWire link, `ffmpeg -devices` lists `video4linux2` |

A fix for Kamoso is a change to that constructor (prefer the node named by `default.video.source`); it is a patch to carry in our own build of Kamoso, and the page's text says that programs which let the person choose a camera keep their own choice.

## Traps (symptom, cause, fix, how found)

- **`pipewiresrc` ends with `stream error: target not found` although a camera exists.** The client had no `media.type`, so WirePlumber saw a `Stream/Input/Unknown` stream and no default exists for that class. Give it the three media properties above. Found with `WIREPLUMBER_DEBUG=4 wireplumber` and the line `Lookup for 'gst-launch-1.0' (53) / 'Stream/Input/Unknown'` followed by `target not found`. A client that connects to a node id (the preview) is linked at once, which is why the preview worked while the plain client did not.
- **`gst-launch-1.0 ... stream-properties="props,node.description=\"A B\""` fails with `could not set property "stream-properties"`.** gst-launch splits its arguments at every space before the structure is read, quotes and backslashes included. Write the description with a no-break space (U+00A0) inside double quotes.
- **A mode change that fails halfway.** `S_FMT` took the new format, then `S_PARM` refused the frame rate, and the camera stayed in the half-changed mode; the rig row "refusal keeps the earlier mode" failed on it. `setMode` now puts the earlier format back. Keep that row: it fails on any code that stops after `S_FMT`.
- **A fake or real device lists no controls although it has them.** `VIDIOC_QUERY_EXT_CTRL` was asked with `V4L2_CTRL_FLAG_NEXT_COMPOUND` and the fake device only cleared `V4L2_CTRL_FLAG_NEXT_CTRL` from the id. Clear both.
- **A QML `ComboBox` shows the first entry although the value is another.** `currentIndex: indexOfValue(x)` ran when the model was still empty and has no dependency on the model. Set it again in `onCountChanged`.
- **A stereo `VideoOutput` inside the page shows only the left view and nothing is declared** (`set_content` never in `WAYLAND_DEBUG=client`). System Settings hosts a page in a `QQuickWidget`, which has no subsurface of its own. Open the pair in a QML `Window`; there the declaration is made.
- **A 2D control by capture.** `ScreenShot2` holds both eyes whenever a declared pair is on screen, whatever the output's mode, so a capture on a flat output does not show the flat picture; and a saved `kwinoutputconfig.json` in the config folder keeps the 3D mode of an earlier session (remove it for a flat run). The control that works: a camera set to "Not 3D" makes no declaration and the capture is one picture, half the width.
- **`kill $!` of a shell function leaves its program running** (the unit's `watch` loop stayed alive between two runs and applied the saved values "before the unit ran"). Start the program directly (`env LD_PRELOAD=... sparky-stereo-camera watch &`) so `$!` is its PID, and list `pidof sparky-stereo-camera` before handing back.
- **`kwin_wayland` exits "Operation not permitted" and every capture is `Cancelled`.** The container lacks `--cap-add SYS_NICE` and a render node (`--device /dev/dri/renderD128 --group-add RENDER_GID`): see [the proof rig](../../stereo-proof-rig/SKILL.md).

## Where the page is proved

`tests/rig-proof.sh` in the package runs the engine against a private PipeWire and WirePlumber, virtual cameras and a user-space V4L2 device ([the virtual camera recipe](../../stereo-proof-rig/SKILL.md#a-virtual-camera-without-a-camera)). Rows: `default persist modes controls two held replug`; each prints PASS or FAIL with the value read, and the script exits 1 when any failed. The page itself was driven with real pointer clicks (the fake input client of the proof rig): click a camera's radio button and Apply, then read the session's default.

## Perks

- Every refusal is one sentence made in one place (`V4l2Camera::explain`): a camera held by another program, a value refused, a control that is off until another changes, a camera that went away. The page and the command show the same words.
- Nothing is hidden: every format and size the driver lists is offered, a control of a kind the page cannot change is listed with the reason, and a camera that is not V4L2 says so.
- The camera's own names (control names such as Brightness) come from the driver in English; the page translates its own sentences, and the packing names come from the stereo layer.
