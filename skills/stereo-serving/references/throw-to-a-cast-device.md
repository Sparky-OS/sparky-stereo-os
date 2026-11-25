# Throwing the desktop to a Cast device

**For** whoever builds or changes Throw to a Google Cast device (the edition's `sparky-stereo-throw`, queue row 81): what already ships for a network screen, the Cast channel as a recipe, the software receiver as the test fixture, the device table, the virtual output's life, the loopback proof, and the traps met.

**Check freshness first.**
Written on 2026-11-24 from the reconcile of row 81, milestone 1, against the published round of that day (KWin 6.7.4-2+stereo3d64, plasma-wayland-protocols 1.21.0-1+stereo3d12, KRdp and KPipeWire 6.7.4-1+stereo3d8, KRDC 26.04.0-1+stereo3d1), and from the cast study of 2026-10-14.
Extended on 2026-11-25 with KWin 4:6.7.4-2+stereo3d66 (staged, not published), which makes a network screen a screen like the others.
The daemon is not built yet: every line below says whether it was read in the source, proved by a test, proved by the study, or is planned and not run.

## The shape

- **A Cast device is one more output of Stereo KWin** (Daniel, 2026-10-14, the network displays design): its 3D packing and its eye swap are the output's own, in Display Settings, as for any screen; the daemon offers no packing and no swap of its own.
  Inside KWin nothing changes: every source hands KWin full side by side, declared once ([sparky-stereo](../../sparky-stereo/SKILL.md)).
- **Plug and play:** when a Throw starts, KWin gets a virtual output already at the device's own resolution and refresh from the device table, with nothing for the person to set first (Daniel's words on the phone headset, the first network screen: "after connected, a virtual monitor is added already in the proper mode to kwin").
- **The names:** "Throw to…", "Throwing to…", "Stop Throwing"; the sound output "Throw: <device>"; the package `sparky-stereo-throw`; Catch is the counter action.
  In every language the two names stay "Throw" and "Catch", with the meaning in parentheses where a person first meets them, pt_BR "Throw (jogar)" and "Catch (receber)" (Daniel, 2026-11-20); status lines and stop actions of a running Throw carry the bare name.
- **Licence:** GPL-2.0-or-later, matching KRdp. GNOME Network Displays (GPL-3.0-or-later) is read and credited, never copied.

## What ships today, and what does not

| Piece | State on 2026-11-24 | Where |
|---|---|---|
| A typed request for a virtual output with identity, exact pixels, refresh in millihertz, millimetres and a split-eye flag | ships: `zkde_screencast_unstable_v1` version 7, `stream_virtual_output_with_properties` | plasma-wayland-protocols patch `screencast-v7.patch`; KWin patches `phone-Create-virtual-panels-with-identity-exact-refresh-an.patch`, `phone-wayland-accept-typed-virtual-panel-requests-in-scree.patch` |
| A networked flag on such outputs | ships, set on every v7 output; the window menu reads it from +stereo3d66 | KWin patch `phone-throw-7afd08684125.patch`, `BackendOutput::isNetworked()` |
| "Throw to" in KWin's window menu for networked outputs | +stereo3d66 (staged) | KWin patch `s66-0004-The-window-menu-lists-network-screens-under-Throw-to.patch`, `kwin-throw-to-menu.po.patch` |
| The 3D formats and the eye swap on a v7 output without the split-eye flag, its choice kept per device, its stream in the chosen format | +stereo3d66 (staged); not in +64 or +65 (the first trap) | KWin patches `s66-0002-...`, `s66-0003-...`; [a network screen in KWin](#a-network-screen-in-kwin-stereo3d66) |
| KRdp's phone headset Throw (discovery, approval, the v7 request with the split-eye flag) | ships | KRdp patches `Pass-validated-phone-panel-descriptors-and-millihert.patch`, `phone-throw-8a3a79dbfca1.patch` |
| KRDC Catch (`krdc-catch`) | ships, eight catalogues, no Spanish; translates the name (pt_BR "Receber") | KRDC patches `catch-backport.patch`, `krdc-catch.po.patch`; successors in the build repository's `sparky-os/translations` |
| KWin's headset "Throw view" strings by the names rule | ships in ten languages | KWin patches `kwin-throw-catch-names.patch`, `kwin-order46b.patch` |
| A Cast daemon, a Cast device table, a "Throw: <device>" sink, Throw and Catch icons | not built | |

## The virtual output, as KWin creates it (read in the source)

```xml
<request name="stream_virtual_output_with_properties" since="7">
  stream, name (persistent device identifier), description (user-visible name),
  width, height (panel pixels), refresh (millihertz), scale (UI scale per viewport),
  physical_width, physical_height (millimetres or zero), headset (0 or 1), pointer
</request>
```

- The protocol's own text: "Invalid or unsupported properties fail the stream and create no output. The compositor must not silently substitute a mono view, a different pixel size or a different refresh", and "A client requiring these properties must not fall back to an older request when version 7 is unavailable. Closing the stream removes the output".
- KWin names the output `Virtual-` plus the name, puts the description in its model, sets `networked`, checks that the mode it made has the asked size and refresh, and answers `failed` with "Virtual panel configuration could not be applied" otherwise (`ScreencastManager::streamVirtualPanel`).
- The output lives as long as the client's stream object: a daemon that loses its Wayland connection loses the output, which is the removal a Throw's end needs.
- `zkde_screencast` is a restricted interface: a client gets it only when its desktop file lists it (`X-KDE-Wayland-Interfaces`), as KRdp's does.
- For a Cast device: the device's name in `name` (the `id` of its DNS-SD record, so a returning device is the same output and its saved placement comes back), its friendly name in `description`, the device table's mode, scale 1, millimetres 0, headset 0.

## A network screen in KWin (+stereo3d66)

Since KWin 4:6.7.4-2+stereo3d66 (queue row 81; staged, not published) a v7 output without the split-eye flag is a screen like the others, as Daniel's design says ("A Cast device is one more KWin output: its 3D packing and its eye swap are the output's own, in Display Settings, as for any screen").
Each line is held by KWin's own tests, red on +65 and green on +66:

| What | How | Test |
|---|---|---|
| It offers the 3D formats and the eye swap | `initializeVirtualOutput` gives it the VirtualStereo and StereoSwapEyes capabilities (`BackendOutput::offersNetworkFormats()`: networked and not split-eye), so Display Settings shows its Anaglyph and Other stereo formats switches and its swap | `test_virtual_output_properties`, `networkedOutput` |
| It arrives in 2D at the device mode | one Preferred 2D mode at the requested pixels and millihertz, as before | same |
| The twins come from the switches | `VirtualOutput::applyChanges` and `DrmVirtualOutput::applyChanges` call `BackendOutput::withNetworkFormatModes()`: side by side half and top and bottom with Other stereo formats, the modern and CRT anaglyph twins with Anaglyph, at the 2D mode's size and refresh; a twin the switches no longer offer goes and the screen is back in 2D | same |
| The choice comes back for the same device | `OutputConfigurationStore` restores the saved twin, switches and swap of that output's identity (the v7 request's persistent name) when the twin belongs to the device's current mode; another device, or the same device at another mode, starts in 2D | `networkedChoiceKeptByIdentity` |
| Its stream is that output's picture | `OutputScreenCastSource::renderNetworkFormat`: each eye drawn at the device raster; side by side half and top and bottom squeeze each eye into its half (linear blit); the anaglyph twins mix the eyes with the Dubois matrices in linear light (`opengl/anaglyphmatrix.h`, one copy shared with the DRM layer); the output's swap exchanges the eyes; 2D stays one view | `screencasting_test`, `testNetworkedOutput`, eight rows |
| A choice made while it streams reaches the receiver | the source repaints its whole picture and asks for a frame when the panel's mode or eye order changes (`repaintWhole`), since such a change damages nothing in the scene | `testNetworkedFormatChangeReachesStream` |
| The next Throw to that device opens in the chosen format | the typed panel request compares the split-eye flag with the panel's own (`isSplitEyeDisplay`) and asks for eyes only of a split-eye panel; a network screen restored into a 3D twin has eyes and is accepted | `testNetworkedChoiceComesBack` |
| The window menu | "Move to Screen" keeps the computer's own screens (and stays offered for a window on a network screen, to bring it back); networked outputs are under "Throw to" by their device names (the v7 description); "Throw &to" in nine catalogues by the names rule | integration test `testThrowToMenu` |
| The headset is unchanged | split-eye outputs keep their capability, their side by side mode and their stream | `creation` rows, `testNativePanel` (9 rows), `testNativePanelMirror` (13 rows) |

From the command line, as Display Settings does it: `kscreen-doctor output.NAME.otherStereoFormats.enable output.NAME.anaglyph.enable`, then `output.NAME.mode.ID` and `output.NAME.swapEyes.enable`; `kscreen-doctor -j` gives each mode's `stereo3D` (0 none, 1 side by side half, 2 top and bottom, 5 anaglyph modern, 6 anaglyph CRT).

What a frame of the stream holds, for a declared pair whose left eye is red (255, 0, 0) and right eye blue (0, 0, 255), measured on +66 at 1280x720 (`testNetworkedOutput`, the mean of each region 16 pixels away from the seams; the halves are exactly the eye colours):

| Format | Frame |
|---|---|
| 2D | red over the whole frame (one view, the left eye's) |
| side by side half | red left half, blue right half; swapped: blue left, red right |
| top and bottom | red top, blue bottom; swapped: blue top, red bottom |
| anaglyph | one colour over the whole frame, the Dubois mix: modern (170, 0, 255), CRT (178, 0, 255), modern swapped (110, 158, 0) |

Prediction for the anaglyph rows: the eye colours to linear light with a 2.2 gamma (KWin's sRGB), the left matrix times the first eye plus the right matrix times the second, back with 1/2.2; the swapped row predicts red 0.156 to 110, green 0.350 to 158, blue below zero to 0, which is what was measured.

### Proving it: KWin's tests, then the installed packages

1. **KWin's own tests, red then green.** Build the targets `kwin screencast testVirtualOutputProperties testThrowToMenu testScreencasting capturefixture` from two trees: red is +65's source with +66's test patch (`s66-0001-...`) and `src/opengl/anaglyphmatrix.h` (the matrices alone, which the stream test predicts the anaglyph colour with); green is +66's source.
   Run them in a container with the NVIDIA card through CDI and a PipeWire and WirePlumber of the container's own (the lane's `kwin-tests-in-container.sh`; every function of `testScreencasting`, so the headset's 22 split-eye rows and the 2D casts run too).
   Red on +65: `networkedOutput` (both rows), `networkedChoiceKeptByIdentity`, seven `testNetworkedOutput` rows, `testNetworkedFormatChangeReachesStream`, `testNetworkedChoiceComesBack` and `testNetworkScreensUnderThrowTo` fail; the 2D row and every split-eye row pass. Green on +66: everything passes (`testNativePanelRefresh`, an opt-in endurance proof for the isolated GPU rig, skips on both).
2. **The installed packages in a headless Stereo KWin** (`kwin_wayland --virtual --output-count 2`, the published round, the four +66 packages installed by `dpkg -i`): a Throw made by the screencast protocol's version 7 request (a small client with `stream_virtual_output_with_properties` and KPipeWire's `PipeWireSourceStream`), the KWin tests' capture fixture as the declared pair (left eye red, right eye blue), the switches and modes set with `kscreen-doctor` as Display Settings sets them, one frame of the stream per format, ScreenShot2 captures marked as `.pns` when KWin's result says `stereo`, the window menu opened with `workspace.slotWindowOperations()` and walked with fake input (S for "Move to &Screen", T for "Throw &to"), the same device thrown again and another device.
   ScreenShot2 draws each eye itself, so its capture of the network screen is the declared pair in every format; the format's own pixels are in the stream's frames only.
   To prove that a choice reaches the stream, ask for the frame first and make the change second: the client's `grab NAME 5000`, then `kscreen-doctor`; the frame saved must be one sent after the change (`new`) and must show the new format. A grab made after the change can only save the last frame, which proves nothing about when it came.
   Measured on 2026-11-25 (lane scripts `rig66/`, 17 rows): +65 fails the formats after the switches (only the 2D mode), the seven format rows and the kept choice, and passes the rest (the Throw, the 2D frame, the pair in ScreenShot2, the screen gone after the stream, another device in 2D); +66 passes all 17, each format's frame `new`.
   The window menu on +65: "Move to Screen" lists Screen 1 (Virtual-0), Screen 2 (Virtual-1) and Screen 3 (Virtual-cast-proof), no "Throw to". On +66: "Move to Screen" lists the two local screens, "Throw to" lists "Living room TV".

## The Cast channel, as a recipe (proved by the cast study on loopback, 2026-10-14)

1. Find the device: DNS-SD browse of `_googlecast._tcp`; the TXT keys `fn` (friendly name), `md` (model name), `id` (the device's identity); a service on a port other than 8009 is a cast group.
2. Open TLS to port 8009. The device does not authenticate the sender, and the public senders do not verify the device's certificate (pychromecast sets `verify_mode = ssl.CERT_NONE`, GNOME Network Displays accepts any certificate).
3. Each message is a 4-byte big-endian length followed by a `CastMessage` protobuf: source id, destination id, namespace, and a JSON (`payload_utf8`) or binary payload.
4. `CONNECT` on `urn:x-cast:com.google.cast.tp.connection` to `receiver-0`; `GET_STATUS` on `urn:x-cast:com.google.cast.receiver`; `PING` and `PONG` on `urn:x-cast:com.google.cast.tp.heartbeat` every few seconds.
5. `LAUNCH` the Default Media Receiver, app id `CC1AD845`; the `RECEIVER_STATUS` answer names its `transportId`.
6. `CONNECT` to that transport, then `LOAD` on `urn:x-cast:com.google.cast.media` with `contentId` (the URL of the live stream on the computer), `contentType` and `streamType: LIVE`; the answer is `MEDIA_STATUS` with a `playerState`.
7. `STOP` closes the application, `CLOSE` the channel.
8. openscreen implements "the Cast V2 Message Chunking specification" since 64d7c985d1 (Taesun Yeoum, 2026-10-30): a message over 64 KiB is split into chunks with `remaining_length` and `continued`, the payload in `payload_binary`. Whether a device sends a chunked message to a sender was not checked; a channel that meets one reassembles it or says that the message could not be read.

## The software receiver as the test fixture

[`scripts/cast-handshake/`](../scripts/cast-handshake/) holds the cast study's receiver and sender: `receiver.py` answers the connection, heartbeat, receiver and media namespaces on 127.0.0.1:8009 with a self-signed certificate and logs every message as a JSON line; `sender.py` is Debian's pychromecast against it; `inside.sh` installs `python3-pychromecast`, runs both and checks the nine steps in order.
Run it in a throwaway Debian testing container with `--network none` after the packages are installed, and never on a network that has a real Cast device: nothing in it browses DNS-SD, the sender connects by address.
Expected (`check.txt` of the study): nine `PASS` lines in order, "device authentication challenge from this sender: none", `RESULT: PASS`; a `LAUNCH` of any other app id is answered with `LAUNCH_ERROR`, which is the red control.
Not rerun since the study.
Planned for the core (not built): the receiver also fetches the URL it is told to `LOAD` and hands the bytes to `ffprobe`.

## The device table

One row per model name (`md`), as data the daemon reads, from Google's "Supported Media for Google Cast" (last updated 2024-09-18) as the study read it:

| Model | Video, as Google lists it | Default mode (the study's rule: the highest size the device lists, at 30 Hz) |
|---|---|---|
| Chromecast, first and second generation | H.264 High up to level 4.1 (720p60 or 1080p30), VP8 | 1920x1080 at 30 Hz |
| Chromecast, third generation | H.264 High up to level 4.2 (1080p60), VP8 | 1920x1080 at 30 Hz, 60 Hz offered |
| Chromecast Ultra | H.264 High 4.2; HEVC Main and Main10 up to level 5.1 (4K60); VP9 | 3840x2160 at 30 Hz |
| Chromecast with Google TV (4K) | H.264 High up to 5.1 (4Kx2K30); HEVC Main and Main10 5.1; VP9 Profile 2 | 3840x2160 at 30 Hz |
| Google TV Streamer | H.264 High up to 5.2 (4Kx2K60); HEVC; VP9; AV1 Main 5.1 | 3840x2160 at 30 Hz |

The level limits behind the first rows are ITU-T H.264 (V16, 06/2026) Table A-6: level 4.1 allows 8 192 macroblocks a frame and 245 760 a second, and 1920x1080 is coded as 1920x1088, 8 160 macroblocks, so 30.1 frames a second at most; level 4.2 allows 522 240 a second, 64 frames of 1080p.
A model not in the table is a fact to say, never a guess to hide: the study proposes the first generation's limits for it, and the person is told which limits were used.

## The loopback proof (planned, not run)

In containers with `--network none`, both ends in one network namespace: a stand-in DNS-SD responder that announces one `_googlecast._tcp` service on 127.0.0.1, the software receiver, a headless Stereo KWin of the published round, the daemon.
Rows, each red first: the published set has no such output (`kscreen-doctor -o` before and after); a receiver that answers `LAUNCH_ERROR` is said, not retried in silence; the stream read back by `ffprobe` (codec, profile, level, size, rate) against the device table, first generation 1080p30 and Ultra 4K; a model with no HEVC never offered HEVC; the output listed while thrown and gone after the receiver closes the channel; a declared stereo window on the output in its half side by side mode, the left eye's marker in the left half and the right eye's in the right half of a frame of the stream, and one view when the output is 2D (KWin +stereo3d66 gives this; its own tests and the installed-package session above hold it without the daemon).

## Traps

- **Symptom (history, fixed in +stereo3d66):** a network output made by the v7 request without the split-eye flag offered no 3D formats and no eye swap in Display Settings, and its stream was one view.
  **Cause:** `BackendOutput::initializeVirtualOutput` gave such an output one 2D mode, `otherStereoFormats` false and no `VirtualStereo` capability (the capability, and the swap, were only on real DRM outputs, `drm_output.cpp`); `OutputScreenCastSource` drew each eye only for a split-eye display; `OutputConfigurationStore` took `otherStereoFormats` from the split-eye flag for every virtual output with an initial mode.
  KWin's own `test_virtual_output_properties` asserted it (`otherStereoFormats() == splitEye`).
  **Fix:** [a network screen in KWin](#a-network-screen-in-kwin-stereo3d66).
  **How found:** the published series applied to KWin 6.7.4 and read; the stereo proof rig's lesson that a virtual output's own stream "renders the scene once, as for a 2D output".
- **Symptom:** a Cast output would start at the size or scale a stream consumer asks for, not the device's.
  **Cause (upstream, read, not measured on our KWin):** "since !7932 a virtual output follows the size its PipeWire stream negotiates, and since !10190 also its scale" (KWin merge request 10427, open); KPipeWire 294 sends the scale as the `org.kde.preferred-scale` stream tag.
  **Fix:** the daemon's encoder asks for the device mode's size and never another; prove the size with `kscreen-doctor -o` while a second stream is open.
- **Symptom:** `chromium.googlesource.com` answers 403 to a fetch of openscreen's log.
  **Fix:** the GitHub mirror `chromium/openscreen` through GitHub's API (`commits?path=cast&since=...`), which answered on 2026-11-24.
- **Symptom:** a package called `sparky-stereo-headset` looks like the phone headset's Throw.
  **Cause:** it is the USB gaming headset page (HeadsetControl, UPower); the phone headset's Throw is KRdp and KRDC Catch.

### Traps of the KWin work (+stereo3d66, 2026-11-25)

- **Symptom:** `build-66.sh` stops at once, exit 127, and `build.log` says `build-in-container-66.sh: line 28: dpkg-source: command not found`.
  **Cause:** the recipe's container script unpacks the source before it installs anything, so the builder image must already carry `dpkg-dev`.
  **Fix:** an owned builder image with `dpkg-dev` (and `python3`, the repository key in `/etc/apt/trusted.gpg.d/sparky-stereo-repo.asc`, a user of uid 1000), Debian taken from snapshot.debian.org at one instant.
  **How found:** the last line of `build.log`.
- **Symptom:** in the installed-package session every format row after the first saved the 2D picture; the proof client's grab said `last` (no frame within 2 s of the change).
  **Cause:** the stream's frames come from the screencast layer's `repaintScheduled`; a twin has the 2D mode's size, so a format change, or the eye swap, damages nothing in the scene and no frame is sent; KWin's own test set the format before the stream started and could not show it.
  **Fix:** `OutputScreenCastSource` follows the panel's `currentModeChanged` and `stereoSwapEyesChanged`, adds a full device repaint and emits `frame()`; held by `testNetworkedFormatChangeReachesStream` (red on the first +66 code at its first wait).
  **How found:** the rig's frame rows carry the client's `new` or `last`, and KWin's screencast log printed "stream in its 3D format" once, at the end of the session.
- **Symptom:** the second Throw to the same device fails with "Virtual panel configuration could not be applied"; the saved configuration holds the chosen twin and swap.
  **Cause:** `ScreencastManager::streamVirtualPanel` refused any panel whose `hasStereoEyes()` differed from the request's split-eye flag; a network screen restored into its 3D format has eyes without being split-eye. KWin's unit test restored the choice through the backend directly and never met this check.
  **Fix:** compare the split-eye flag with `isSplitEyeDisplay()` and ask for eyes only of a split-eye panel; held by `testNetworkedChoiceComesBack`.
  **How found:** the failure text in the rig's session log, then a search of the source for it.
- **Symptom:** a second run of `build-66.sh` ends at once with exit 125: `The container name "/tc81-b66-kwin" is already in use`.
  **Cause:** the recipe's `docker run` names its container `${BUILD_NAME_PREFIX}-kwin` without `--rm`, so the first build's exited container keeps the name.
  **Fix:** append its ID to the lane's `.container-ids`, `docker rm` it by that name, build again.
  **How found:** the host log's last lines.
- **Symptom:** `ninja: error: unknown target 'testScreencasting'`.
  **Cause:** the test is configured only when CMake finds KPipeWire (`if (TARGET K::KPipeWire)`), and `libkpipewire-dev` is not a KWin build dependency.
  **Fix:** install the edition's `libkpipewire-dev` in the test image and run `cmake .` again.
  **How found:** `Could not find a package configuration file provided by "KPipeWire"` in the configure log.
- **Symptom:** every screencasting row is skipped with `no render node available`.
  **Cause:** `GenericSceneOpenGLTest` needs a render node; a container without a GPU has none.
  **Fix:** the NVIDIA card through CDI (`--device nvidia.com/gpu=0 --group-add 44 --group-add 125`), as KWin's own test script does; the AMD card is not used for such loops.
  **How found:** the test's own skip message.
- **Symptom:** a test that makes its network screen through the screencast request waits for `created` and never gets it.
  **Cause:** the request needs OpenGL compositing and a PipeWire; a plain integration test has neither (`Unsupported compositing type`).
  **Fix:** a test of the window menu makes its networked output through the output backend (`createVirtualOutput` with `.networked = true`); the stream test keeps the real request with its own PipeWire and WirePlumber.
  **How found:** `ScreencastManager::streamVirtualPanel` read for its early `sendFailed`.
- **Symptom:** the format chosen for a device does not come back at the next output for that device, although the swap does.
  **Cause:** the store saves the output's desired mode, not its current one; Display Settings sets both (`outputmanagement_v2.cpp`), a test that sets only the current mode saves 2D.
  **Fix:** set the current and the desired mode, as Display Settings does.
  **How found:** `OutputConfigurationStore::storeConfig` read for the mode it saves.
- **Symptom:** a stream test that waits for a second frame times out on a still scene.
  **Cause:** KWin sends a frame on damage only.
  **Fix:** place the window before the stream starts and take its first frame.
- **Symptom:** the installed-package session stops at its first frame grab and never ends.
  **Cause:** the proof client saved "the next frame after the command"; the first format row (2D) changes nothing, and KWin sends a frame on damage only.
  **Fix:** a grab waits 2 s for a new frame, then saves the last frame received and says `last`; every row after a format change requires `new`, so a stale frame cannot pass.
  **How found:** the session log ended after the capture of the declared pair, with the client's grab unanswered.
- **Symptom:** an anaglyph row fails a threshold written from the matrices alone: (110, 158, 0) where red and blue under 96 were expected.
  **Cause:** the shader mixes in linear light; the threshold ignored the transfer function.
  **Fix:** predict the colour (2.2 gamma in, the matrices, 1/2.2 out) and compare within a few levels; the measured values match the prediction.
- **Symptom:** `no match for 'operator!=' (operand types are 'const std::ranges::dangling' ...)`.
  **Cause:** `std::ranges::find_if(output->modes(), ...)` on a list returned by value.
  **Fix:** keep the list in a variable first.

## Upstream, as searched on 2026-11-24

- **KDE** (merge requests updated since 2026-10-01 in KWin, KRdp, KPipeWire, xdg-desktop-portal-kde, plasma-workspace): nothing for Cast, network displays or a networked output. Close to the work: KWin 10190 (merged, consumer-picked scale of virtual outputs), 10427 (open, only the creating stream resizes a virtual output), 10355 (merged, screencast plugin ported away from OpenGL, which the next rebase of our screencast patches meets); KRdp 290 (open, drops the zkde_screencast path for the portal only), 275 (open, scale), 239 (open, an audio sink KRdp makes the default, which our design does not do).
- **GNOME Network Displays:** fifteen commits since 2026-10-01, all Miracast or translations; its Cast code last changed on 2026-01-23 (8c6a4de2, Christian Glombek).
- **openscreen:** 43 commits under `cast/` since 2026-10-01, nearly all Cast Streaming (path B, a later milestone); for the channel, message chunking (64d7c985d1); a new mirroring app id `015B5861` (f2b951181d, Shawn Quereshi).

## Credits

GNOME Network Displays (Benjamin Berg, Christian Glombek, Anupam Kumar, whose commits brought its Chromecast media factory, and the contributor credited in its NEWS for the Chromecast protocol, @kyteinsky), pychromecast (Paulus Schoutsen, Erik Montnemery), the Open Screen Library (The Chromium Authors; Taesun Yeoum for message chunking), KRdp and KPipeWire (Aleix Pol Gonzalez, Arjen Hiemstra and the KDE contributors), and the edition's phone headset work that made the v7 request.
