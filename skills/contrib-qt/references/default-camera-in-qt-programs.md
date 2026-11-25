# The default camera in Qt programs (ORDER 582, 2026-11-15; ORDER 625, 2026-11-16)

A Qt program that asks for "the default camera" (`QMediaDevices::defaultVideoInput()`, QML `MediaDevices.defaultVideoInput`, a `QCamera` made without a device) got the first camera of the kernel's list, whatever camera the person chose on the Camera page.
Check freshness first: written on 2026-11-15 from Qt Multimedia 6.11.2 (`qt6-multimedia 6.11.2-3+stereo3d16+lc1`), Qt's `dev` branch of 2026-11-13, PipeWire 1.6.9 and WirePlumber 0.5.18.

## Recipe: what lives where

1. **Qt lists V4L2 cameras itself.**
   In 6.11 the FFmpeg backend's `QV4L2CameraDevices::doCheckCameras()` (`src/plugins/multimedia/ffmpeg/qv4l2cameradevices.cpp`; on `dev` since 2026-09-23 `src/multimedia/v4l2/`) scans `/dev/video*`, keeps the capture devices with streaming and a usable format, and used to mark the first as `isDefault` (the comment said so).
   `QMediaDevices::defaultVideoInput()` returns the camera with `isDefault()`, else the first; `QCamera()` calls it at construction.
   The GStreamer backend takes `is-default` from the device provider; the edition ships the FFmpeg backend.
2. **The session's default lives in WirePlumber's metadata.**
   Object "default", subject 0, key `default.configured.video.source` (the person's choice, JSON `{ "name": "NODE_NAME" }`, type `Spa:String:JSON`) and `default.video.source` (WirePlumber's live pick, which exists even when nobody chose: with three virtual cameras it picked a different one in each session).
   The edition follows only the configured key: nobody having chosen leaves Qt's first camera, as before.
3. **A camera node reaches its device by a path.**
   The registry's `global` event carries only some of a node's properties.
   `media.class` is `Video/Source`, `node.name` is the name the metadata holds, and PipeWire's V4L2 source gives `object.path = v4l2:/dev/videoN`; the full property `api.v4l2.path` comes only with the node's info event (it is what `pw-dump` shows).
   A node with neither (libcamera) has no V4L2 device: the first camera stays the default and the log says so.
4. **The change (patch 0049 in the edition, a commit on `dev` in Qt's form).**
   `QtPipeWire::QDefaultCameraMonitor` (`src/multimedia/pipewire/qpipewire_defaultcamera.cpp`) has its own `pw_thread_loop`, core, registry and a listener on the "default" metadata; the constructor waits at most two seconds for the first two roundtrips (globals, then the metadata's first values); `choiceChanged()` is emitted from the PipeWire thread.
   `QDefaultCameraState` is the pure part (events in, a choice out) and `pickDefaultCamera()` picks among the device paths; both are covered by `tst_qpipewiredefaultcamera` with no PipeWire server.
   `QV4L2CameraDevices` rescans on `choiceChanged()`; `isDefault` moves, the order and the list do not, and `videoInputsChanged` is emitted because `QCameraDevicePrivate::operator==` compares `isDefault`.
   The reason the choice cannot be honoured (no session, camera not connected, not a V4L2 device, not among Qt's cameras) is logged once per distinct reason in `qt.multimedia.ffmpeg.v4l2cameradevices` (`qt.multimedia.v4l2.cameradevices` on `dev`), at info level, which Qt prints by default.
5. **The rig: two or three user-space cameras and a private PipeWire session, no kernel module.**
   `stereo-proof-rig/scripts/virtual-camera/` has the session (`session-start.sh`), the PipeWire cameras (`virtual-camera.sh a|b|held`, now with `object.path` too), the V4L2 side (`vcam-shim.c`, an `LD_PRELOAD` library) and `qt-default/` with the probe program (`probe.cpp`: the three routes, the program's own choice, `--watch SECONDS`), `in-container.sh` and `scenario.sh` (cases 1 to 7: nobody chose, chose the second camera, own choice kept, default changing while the program runs, chosen camera unplugged and plugged, a name that matches none, no session).
   In a throwaway root container: install the Qt Multimedia debs under test, make `ln -s /nonexistent-camera /dev/videoN` for each camera (a broken symbolic link is what `QDir::System` lists, and the shim answers `open()`), `chmod 0777 /dev` so the user can plug and unplug by removing and making links, then run `scenario.sh` as uid 1000. Red is the published `+stereo3d15`, green the new build.
6. **Expected result:** with `cam-b` chosen, red lists `/dev/video20*` and all three routes give `/dev/video20`; green lists `/dev/video21*` and all three give `/dev/video21`; changing the default three times while the program runs gives three `videoInputsChanged` with the new default each time; unplugging the chosen camera gives the first camera and one log line, plugging it again gives it back; no session gives the first camera and one line.

## Traps (symptom, cause, fix, how found)

- **Qt lists no camera although the shim answers.** `LIST` is empty, no `found camera` line with `QT_LOGGING_RULES="qt.multimedia.ffmpeg.v4l2*.debug=true"`. Three causes in turn: Debian builds with `_FORTIFY_SOURCE`, so `open(path, O_RDONLY)` is `__open_2`, which the shim did not define (add `__open_2` and `__open64_2`); Qt declares `xioctl(int fd, int request, void *)`, so `VIDIOC_QUERYCAP` arrives sign-extended as `0xffffffff80685600` and matches no `case` (mask it); and the listing is `QDir::entryList(QDir::System)` of `/dev`, which needs device nodes or broken symbolic links, not regular files. Found with `VCAM_TRACE=1` (the shim prints each open and ioctl) after `LD_DEBUG=bindings` showed the preload bound.
- **The monitor says "not a V4L2 device" for a camera that has `api.v4l2.path` in `pw-dump`.** The registry event did not carry the property (see 3 above). Fix: read `object.path` with its `v4l2:` prefix; make the rig's cameras carry it. Found by printing the node's properties from the registry callback.
- **The build stops with `defaulted operator== only available with -std=c++20`, then `no member named starts_with`.** Qt 6.11's multimedia module builds as `gnu++17` although the pipewire files use designated initializers. Write `operator==` out and compare `substr(0, n)`. Check one translation unit in seconds by replaying its compile command from the build log (`ninja -v` prints it) in a container with `libpipewire-0.3-dev` unpacked by `dpkg -x` into a prefix and `-isystem` on it.
- **A header that includes `<pipewire/pipewire.h>` breaks the FFmpeg plugin's translation units** (`pipewire/extensions/metadata.h: No such file`): the plugin is not given PipeWire's include path. Keep the monitor's header free of PipeWire types (an opaque `Impl`) and include `qpipewire_support_p.h` in the `.cpp` only.
- **`SIGSEGV` in `parseDefaultSourceName` when the JSON has another member before `name`.** `spa_json_next(&it, nullptr)` writes the value pointer through its second argument. Pass a pointer. `QAudioContextManager`'s own parser (`qpipewire_audiocontextmanager.cpp`, `jsonParseObjectName`) has the same call; found by the unit test's "other members first" row, which crashed before the fix and passes after it.
- **`dpkg -i` of the new Qt Multimedia fails on `libstereo-av1 (>= 1.18.0)` and `libstereo-policy1 (>= 1.18.0)`.** The build image had the published 1.18.0 libraries, so the new `Depends` name them; install them from the published pool beside the debs.
- **`docker run -v` made a root-owned folder** and the next run could not write in it: create the folders before the first run, and remove root-owned leftovers through a container, as the lane's own user.
- **`rp-580-rig:published` does nothing useful with `docker run IMAGE cmd`:** its entrypoint is `bash /rig/in-published.sh`; start it with `--entrypoint sh`.
- **Qt's Gerrit answers 403 to the REST API without an account;** Jira answers anonymously at `https://qt-project.atlassian.net/rest/api/2/search/jql?jql=...` (the old `bugreports.qt.io` address redirects there). `github.com/qt/qtmultimedia` shows what is merged on `dev` only.

## Perks

- A program's own choice is never touched: `QCamera(device)` keeps its device (the probe's OWN line).
- `dev` has a PipeWire camera backend (`qpipewire_camera*`, opt-in with `QT_CAMERA_BACKEND=pipewire`, by Tim Blechmann, October and November 2026) whose device monitor said "PipeWire has no notion of a default video source, so the first camera in a stable order it is"; WirePlumber does have one. That backend is where Qt follows the session's default: the next section (ORDER 625).
- The edition's Camera page and Kamoso set and follow the same key; the page's `sparky-stereo-camera default` prints it.

## The PipeWire camera backend follows the session's default (ORDER 625, 2026-11-16)

Written from qtmultimedia `dev` 5d5bb219c3, qtbase `dev` 49df9da9, PipeWire 1.6.9 and WirePlumber 0.5.19; the change is commit f22e69f8ca on a branch, not on Gerrit when this was written.
Corrected on 2026-11-25 (ORDER 879) after the maintainer's review of the change as Gerrit 792002: the recipe and the test rows below describe its second patch set, and [Qt code as its maintainers write it](qt-code-as-its-maintainers-write-it.md) has what the review taught.
Check freshness first: the PipeWire camera files change every week; search Gerrit before anything else (step 1).

### Where the change goes: the lesson of Gerrit 789011

The first offer (789011, ORDER 603) put the session's default into the V4L2 camera layer, with its own `pw_thread_loop`, core and registry, and found the V4L2 device from a node's `v4l2:` path.
Tim Blechmann gave it -2 and closed QTBUG-152302: "the v4l2 camera layer should be independent from pipewire"; "do we really want to have a separate event loop?"; "you'd only want to have a single registry for all devices"; "this logic will break when pipewire camera's use libcamera instead of raw v4l2"; and on the report, "feel free to reopen, if the pipewire camera layer does not follow pipewire's selected default".
This skill already said that `dev` had his PipeWire camera backend with a "no default" comment, and the change still went to the V4L2 layer.
So: before choosing where a Qt change goes, read which layer the maintainer is building (`git log --format='%an %s' -- the neighbouring folder` for the last two months), put the change there, and use that layer's own registry, loop and names.

### Recipe

1. **Search first.** Gerrit's REST API with the account's token: `q=project:qt/qtmultimedia dir:src/multimedia/pipewire after:2026-10-01` lists every change on the folder (the form `path:^src/.*` answers an error page, not JSON), then `status:open` with the subject words, then `message:QTBUG-N`. Jira answers anonymously (see above).
2. **Mirror the audio side**, which already follows `default.audio.source` and `default.audio.sink`:
   - `QCameraContextManager::objectAdded()` sends a `Metadata` global named `default` to `startListenDefaultMetadataObject()`: `bindMetadata()` on the existing registry and `pw_metadata_add_listener()`, the same names as `QAudioContextManager`; no second loop, no second registry.
   - `handleDefaultMetadataObjectEvent()` takes subject `PW_ID_CORE`, key `default.video.source`, type `Spa:String:JSON`, reads the name with the module's own `jsonParseObjectName()`, and calls `QCameraDeviceMonitor::setDefaultVideoSource(name)` (`std::nullopt` for a removed key or a cleared subject), which emits `camerasChanged()`. The event's key, type and value can each be a null pointer, so the record keeps them as `std::optional<std::string_view>`.
   - When that metadata global is removed (WirePlumber stops or restarts), the listener goes, the default becomes `std::nullopt`, and the next `default` global is followed again. The object is selected by its `metadata.name` and its removal is matched by the id that was bound.
   - `cameraDevices()` calls `syncRegistry()` once, as before the change, builds the list and then marks `defaultCameraIndex(ids)`. The first form synced twice; measured on 2026-11-25, one sync gives the session's default in the first list in 30 of 30 fresh starts, because each camera's format enumeration makes its own roundtrip after the metadata is bound.
   - `defaultCameraIndex()` matches the camera node whose `node.name` is the session's name, so V4L2 and libcamera nodes are the same case; no device paths. It asserts a list that is not empty.
   - `QCameraDevice::operator==` compares ids only, and `QPlatformVideoDevices::updateVideoInputsCache()` uses it, so a default that moved alone was dropped and the stale `isDefault` stayed in the cache. `QtPipeWire::QCameraDevices::updateVideoInputs()` compares id and `isDefault` (the audio monitor's comparison) and calls the base class's `onVideoInputsChanged()` when they differ, and also when nothing was cached yet, as `updateVideoInputsCache()` did.
   - When the session names no default, or a node that is not a listed camera, the first camera stays and `qt.multimedia.pipewire.camera.devicemonitor` says why at info level each time the list is built. The first form kept the last message to say it once; the review asked for no such state.
3. **Which key.** `default.video.source` is WirePlumber's live pick, as `default.audio.source` is for audio; it follows `default.configured.video.source` (the person's own choice) whenever that camera is present, and moves to another camera while it is away.
4. **"Connect without a target" cannot be reached from this layer.** `QCamera(QObject *)` is `QCamera(QMediaDevices::defaultVideoInput())` and `QCameraPrivate::init()` replaces a null device with the same call (`src/multimedia/camera/qcamera.cpp`), so the platform camera always gets a device; `QPipeWireCamera::startStream()` connects with `target.object` set to that node's serial. What the session would link a target-less stream to was measured anyway (rig case 9): WirePlumber links a stream with `media.type=Video`, `media.category=Capture`, `media.role=Camera` and no target to `default.video.source`, the same camera the layer now reports.
5. **Red and green from one commit.** Export the commit twice with `git archive COMMIT | tar -x -C DIR` (no extra worktrees in a shared clone), disable the matching line in one copy with `sed`, check with `diff -r` that it is the only difference, and run the same test in both builds; read the exit codes directly.

### The test rows (`tst_qpipewire_cameradevicemonitor`, in its own style)

Registry events go in as in the existing rows (`objectAdded()` with a property fixture), plus `setDefaultVideoSource()`; three cameras, `cam_a` and `cam_c` through V4L2 and `cam_b` through libcamera.
- `defaultCameraIndex_returnsDefaultVideoSource_matchedByNodeName`: the libcamera node named as default is index 1.
- `setDefaultVideoSource_emitsCamerasChanged_whenTheNameChanges`: two changes, two signals; the same name again is no change; removing the name is one more.
- `defaultCameraIndex_returnsFirstCamera_withoutDefaultVideoSource` and `..._whenDefaultVideoSourceIsNotListed`: index 0 and the log line (`QTest::ignoreMessage`, once for each call).

Measured on 2026-11-25 on the second patch set: with the matching line disabled the test exits 2 (2 of 19 fail: the first row and the signal row); with the change it exits 0 (19 passed). The keep-the-first rows pass on both, as they assert the old behaviour plus the line.
The first patch set had a fifth row for the stored message and 20 rows in all (2026-11-16: 3 failed with the match disabled).

### The rig

`stereo-proof-rig/scripts/virtual-camera/qt-pipewire/`: `entry.sh` (root: a passwd entry for uid 1000, then the scenario as that uid), `scenario.sh` (cases 1 to 9), `replug.sh` (case 10: a streaming program through its camera's unplug and plug), `probe.cpp` (the default by `defaultVideoInput()` and by `QCamera()`, a program's own choice with `--own ID`, `--start` to stream into a `QVideoSink`, `--watch`), `links.py` (the metadata's video keys, the Video/Source nodes, and which process each camera link feeds).
Run it in a throwaway container with the Qt build mounted read-only, a private PipeWire and WirePlumber, and GStreamer `pipewiresink mode=provide` nodes as cameras; environment `QT_CAMERA_BACKEND=pipewire QT_MEDIA_BACKEND=ffmpeg QT_QPA_PLATFORM=offscreen`.
Run it once on the unmodified build and once on the branch, each in a fresh container.

### Measured (2026-11-16, three cameras, cam-b chosen unless said)

| Case | dev 5d5bb219c3 | with the change |
| --- | --- | --- |
| Chosen cam-b, `defaultVideoInput()` and `QCamera()` | cam-a (the first) | cam-b |
| Three changes while running | no `videoInputsChanged` | three, each with the new default |
| A camera that sorts first is plugged in | it becomes the default (cam-0) | cam-b stays |
| cam-b unplugged, then plugged in again, program running | cam-a throughout | cam-a while away, cam-b again |
| WirePlumber stopped, then back | cam-a, nothing said | cam-a with one line, then cam-b |
| Default names a screen-share node, not a camera | cam-a, nothing said | cam-a with one line |
| Program's own `QCamera(cam-c)`, hotplug, refresh, restart | cam-c kept | cam-c kept |
| A program streaming the default camera; cam-b unplugged, plugged in again (case 10) | opens cam-a; WirePlumber moves the stream to cam-b when it returns, `QCamera` still says cam-a | opens cam-b; the stream runs from cam-a while cam-b is away and from cam-b again, frames never stop, the default shown follows |

WirePlumber's side, measured the same day: unplugging the chosen camera moves `default.video.source` to another camera and keeps `default.configured.video.source`; plugging it in again makes it the default again.
A `QCamera` that is already open keeps its device through every change (Qt's API); only the default and the list move.
A running stream is the session's to move: WirePlumber relinked the Qt stream to the default camera while its own camera was away, and on `dev` moved a stream opened on another camera to the returning default (why WirePlumber moved a stream with a present target was not examined); `QCamera::cameraDevice()` keeps naming the camera it opened.

The module's tests as `ctest -j4 --timeout 120` runs them, offscreen, without a display or a camera: the same six tests fail on `dev` and with the change (`module_includes`, `tst_qcamerabackend`, `tst_qcudatextureconverter`, `tst_qmediaformatbackend`, `tst_qmediarecorderbackend`, `tst_qvideoframebackend`); `tst_qmediaframeinputsbackend` failed once in the change's full run and passed once in `dev`'s, and run alone through ctest it fails five times out of five on both (its `mediaRecorderWritesVideo_withSingleFrame` row), so it is a recorder test that depends on the run, not the camera layer.

### Traps (symptom, cause, fix, how found)

- **The PipeWire backend lists no camera although `pw-cli ls Node` shows them.** A registry client sees only some properties of a node: `object.serial`, `factory.id`, `client.id`, `node.description`, `node.name`, `media.class`, `media.role` (and `object.path` when set); `device.api` never arrives, so `isCameraNode()` accepts a camera by `media.role = Camera`, which SPA's V4L2 source sets. Give the rig's nodes `media.role=Camera`. Found with `QT_LOGGING_RULES="qt.multimedia.pipewire*=true"`: the metadata lines appeared and no "camera node added", then `pw-cli ls Node` printed the global's properties.
- **Default changes while running give no `videoInputsChanged`.** `QCameraDevice::operator==` compares ids only (`qcameradevice.cpp`), and the base cache's `update()` uses it. Found by the rig: node changes gave events, metadata changes none.
- **`QT_CAMERA_BACKEND=pipewire` needs the FFmpeg plugin built** (`FEATURE_ffmpeg=ON`): the backend is chosen in `qffmpegmediaintegration.cpp`. The build stops with `X11/Xlib.h: No such file` when the prefix's QtGui has `xlib` (see `mkspecs/modules/qt_lib_gui_private.pri`): install `libx11-dev libxrandr-dev libxext-dev`.
- **An integration test run by hand says `isMediaBackendPluginLoaded() returned FALSE`** while ctest runs it fine: ctest gives the test the build's plugin path. Rerun a single test with `ctest -R '^NAME$' --output-on-failure` in the build folder, not the binary alone.
- **`qsb: error while loading shared libraries: libpcre2-16.so.0`** in a fresh image: the prefix's tools need what the image that built them had. Run `ldd` over the prefix's `bin`, `lib` and `plugins` once and install every "not found" (here `libpcre2-16-0 libinput10 libmtdev1 libwayland-client0 libwayland-cursor0`; `apt-cache policy libmtdev1` shows no candidate and apt installs `libmtdev1t64`, which provides it).
