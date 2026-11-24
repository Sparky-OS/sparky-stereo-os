# Throwing the desktop to a Cast device

**For** whoever builds or changes Throw to a Google Cast device (the edition's `sparky-stereo-throw`, queue row 81): what already ships for a network screen, the Cast channel as a recipe, the software receiver as the test fixture, the device table, the virtual output's life, the loopback proof, and the traps met.

**Check freshness first.**
Written on 2026-11-24 from the reconcile of row 81, milestone 1, against the published round of that day (KWin 6.7.4-2+stereo3d64, plasma-wayland-protocols 1.21.0-1+stereo3d12, KRdp and KPipeWire 6.7.4-1+stereo3d8, KRDC 26.04.0-1+stereo3d1), and from the cast study of 2026-10-14.
The daemon is not built yet: every line below says whether it was read in the source, proved by the study, or is planned and not run.

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
| A networked flag on such outputs | ships, set on every v7 output; nothing in KWin reads it yet (no window menu, no output-device attribute) | KWin patch `phone-throw-7afd08684125.patch`, `BackendOutput::isNetworked()` |
| "Throw to" in KWin's window menu for networked outputs | not built | |
| The 3D formats and the eye swap on a v7 output without the split-eye flag | not built: see the first trap | `BackendOutput::initializeVirtualOutput`, `OutputScreenCastSource` |
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
Rows, each red first: the published set has no such output (`kscreen-doctor -o` before and after); a receiver that answers `LAUNCH_ERROR` is said, not retried in silence; the stream read back by `ffprobe` (codec, profile, level, size, rate) against the device table, first generation 1080p30 and Ultra 4K; a model with no HEVC never offered HEVC; the output listed while thrown and gone after the receiver closes the channel; a declared stereo window on the output in its half side by side mode, the left eye's marker in the left half and the right eye's in the right half of a frame of the stream, and one view when the output is 2D (this row needs the KWin change of the first trap).

## Traps

- **Symptom:** a network output made by the v7 request without the split-eye flag offers no 3D formats and no eye swap in Display Settings, and its stream is one view.
  **Cause:** `BackendOutput::initializeVirtualOutput` gives such an output one 2D mode, `otherStereoFormats` false and no `VirtualStereo` capability (the capability, and the swap, are only on real DRM outputs, `drm_output.cpp`); `OutputScreenCastSource` draws each eye only for a split-eye display; `OutputConfigurationStore` takes `otherStereoFormats` from the split-eye flag for every virtual output with an initial mode.
  KWin's own `test_virtual_output_properties` asserts it (`otherStereoFormats() == splitEye`).
  **Fix (proposed, not built):** a networked output gets the 3D formats, the anaglyph twins and the eye swap of a monitor, and its stream carries the output's own filter result (the twin's packing, the swap), as the headset's split-eye stream already does for half side by side.
  **How found:** the published series applied to KWin 6.7.4 and read; the stereo proof rig's lesson that a virtual output's own stream "renders the scene once, as for a 2D output".
- **Symptom:** a Cast output would start at the size or scale a stream consumer asks for, not the device's.
  **Cause (upstream, read, not measured on our KWin):** "since !7932 a virtual output follows the size its PipeWire stream negotiates, and since !10190 also its scale" (KWin merge request 10427, open); KPipeWire 294 sends the scale as the `org.kde.preferred-scale` stream tag.
  **Fix:** the daemon's encoder asks for the device mode's size and never another; prove the size with `kscreen-doctor -o` while a second stream is open.
- **Symptom:** `chromium.googlesource.com` answers 403 to a fetch of openscreen's log.
  **Fix:** the GitHub mirror `chromium/openscreen` through GitHub's API (`commits?path=cast&since=...`), which answered on 2026-11-24.
- **Symptom:** a package called `sparky-stereo-headset` looks like the phone headset's Throw.
  **Cause:** it is the USB gaming headset page (HeadsetControl, UPower); the phone headset's Throw is KRdp and KRDC Catch.

## Upstream, as searched on 2026-11-24

- **KDE** (merge requests updated since 2026-10-01 in KWin, KRdp, KPipeWire, xdg-desktop-portal-kde, plasma-workspace): nothing for Cast, network displays or a networked output. Close to the work: KWin 10190 (merged, consumer-picked scale of virtual outputs), 10427 (open, only the creating stream resizes a virtual output), 10355 (merged, screencast plugin ported away from OpenGL, which the next rebase of our screencast patches meets); KRdp 290 (open, drops the zkde_screencast path for the portal only), 275 (open, scale), 239 (open, an audio sink KRdp makes the default, which our design does not do).
- **GNOME Network Displays:** fifteen commits since 2026-10-01, all Miracast or translations; its Cast code last changed on 2026-01-23 (8c6a4de2, Christian Glombek).
- **openscreen:** 43 commits under `cast/` since 2026-10-01, nearly all Cast Streaming (path B, a later milestone); for the channel, message chunking (64d7c985d1); a new mirroring app id `015B5861` (f2b951181d, Shawn Quereshi).

## Credits

GNOME Network Displays (Benjamin Berg, Christian Glombek, Anupam Kumar, whose commits brought its Chromecast media factory, and the contributor credited in its NEWS for the Chromecast protocol, @kyteinsky), pychromecast (Paulus Schoutsen, Erik Montnemery), the Open Screen Library (The Chromium Authors; Taesun Yeoum for message chunking), KRdp and KPipeWire (Aleix Pol Gonzalez, Arjen Hiemstra and the KDE contributors), and the edition's phone headset work that made the v7 request.
