# Throwing the desktop to a Cast device

**For** whoever builds or changes Throw to a Google Cast device (the edition's `sparky-stereo-throw`, queue row 81): what already ships for a network screen, the Cast channel as a recipe, the software receiver as the test fixture, the device table, the virtual output's life, the loopback proof, and the traps met.

**Check freshness first.**
Written on 2026-11-24 from the reconcile of row 81, milestone 1, against the published round of that day (KWin 6.7.4-2+stereo3d64, plasma-wayland-protocols 1.21.0-1+stereo3d12, KRdp and KPipeWire 6.7.4-1+stereo3d8, KRDC 26.04.0-1+stereo3d1), and from the cast study of 2026-10-14.
Extended on 2026-11-25 with KWin 4:6.7.4-2+stereo3d66 (staged, not published), which makes a network screen a screen like the others, and the same day with the daemon, its command and its page, `sparky-stereo-throw` 0.1.0+lc1 (staged, not published; recipe `sparky-os/packages/sparky-stereo-throw` of the build repository), proved in a loopback session with software Cast devices, and with a study of what a Cast device lets the computer set; and with 0.2.0 (part C: the sound, every codec Google lists per model, the mode picker, a tighter stream server, Google's own documentation for the account route, and the kit for a real device).
Every line below says whether it was read in the source, proved by a test or a session, proved by the study, or is planned and not run.

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
| The Cast daemon, its command, the device table and the Throw page in System Settings | `sparky-stereo-throw` 0.1.0+lc1 (staged) | [the daemon](#the-daemon-sparky-stereo-throw-010) |
| The sound output "Throw: <device>", the codecs beyond H.264, the codec and mode chosen per device | `sparky-stereo-throw` 0.2.0+lc1 (staged) | [the sound and the codecs](#the-sound-and-the-codecs-020) |
| Throw and Catch icons, the Throw shortcut, Cast Streaming (path B), AV1 (no KPipeWire encoder) | not built | |

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
| The twins come from the switches, as a monitor's | `VirtualOutput::applyChanges` and `DrmVirtualOutput::applyChanges` call `BackendOutput::withNetworkFormatModes()`, which follows `DrmConnector::withVirtualStereoModes` with the device's mode as the native raster: with Other stereo formats, side by side half, top and bottom, rows, columns and checkerboard (left eye first; the swap gives the other order) and side by side full for a mode two eyes wide; with Anaglyph, the modern and CRT twins; never frame sequential (a stream sends a frame on damage, not at every refresh, so alternate frames cannot carry alternate eyes); a twin the switches no longer offer goes and the screen is back in 2D | same, five rows (two of them two eyes wide, one at 120 Hz) |
| The choice comes back for the same device | `OutputConfigurationStore` restores the saved twin, switches and swap of that output's identity (the v7 request's persistent name) when the twin belongs to the device's current mode; another device, or the same device at another mode, starts in 2D | `networkedChoiceKeptByIdentity` |
| Its stream is that output's picture | `OutputScreenCastSource::renderNetworkFormat`: each eye drawn at the device raster (half of it for side by side full); side by side half and top and bottom squeeze each eye into its half (linear blit), side by side full places each whole; the anaglyph twins mix the eyes with the Dubois matrices in linear light (`opengl/anaglyphmatrix.h`, one copy shared with the DRM layer); rows, columns and checkerboard interleave them with the screen layer's own `opengl/stereopattern.frag`; the output's swap exchanges the eyes; 2D stays one view | `screencasting_test`, `testNetworkedOutput`, sixteen rows |
| A choice made while it streams reaches the receiver | the source repaints its whole picture and asks for a frame when the panel's mode or eye order changes (`repaintWhole`), since such a change damages nothing in the scene | `testNetworkedFormatChangeReachesStream` |
| The next Throw to that device opens in the chosen format | the typed panel request compares the split-eye flag with the panel's own (`isSplitEyeDisplay`) and asks for eyes only of a split-eye panel; a network screen restored into a 3D twin has eyes and is accepted | `testNetworkedChoiceComesBack` |
| The window menu | "Move to Screen" keeps the computer's own screens (and stays offered for a window on a network screen, to bring it back); networked outputs are under "Throw to" by their device names (the v7 description); "Throw &to" in nine catalogues by the names rule | integration test `testThrowToMenu` |
| The headset is unchanged | split-eye outputs keep their capability, their side by side mode and their stream | `creation` rows, `testNativePanel` (9 rows), `testNativePanelMirror` (13 rows) |

From the command line, as Display Settings does it: `kscreen-doctor output.NAME.otherStereoFormats.enable output.NAME.anaglyph.enable`, then `output.NAME.mode.ID` and `output.NAME.swapEyes.enable`; `kscreen-doctor -j` gives each mode's `stereo3D` (0 none, 1 side by side half, 2 top and bottom, 4 side by side full, 5 anaglyph modern, 6 anaglyph CRT, 7 rows, 9 columns, 11 checkerboard, each left eye first).

What a frame of the stream holds, for a declared pair whose left eye is red (255, 0, 0) and right eye blue (0, 0, 255), measured on +66 at 1280x720 (`testNetworkedOutput`, the mean of each region 16 pixels away from the seams; the halves are exactly the eye colours):

| Format | Frame |
|---|---|
| 2D | red over the whole frame (one view, the left eye's) |
| side by side half | red left half, blue right half; swapped: blue left, red right |
| top and bottom | red top, blue bottom; swapped: blue top, red bottom |
| anaglyph | one colour over the whole frame, the Dubois mix: modern (170, 0, 255), CRT (178, 0, 255), modern swapped (110, 158, 0) |
| rows, columns, checkerboard | the first row, column or pixel the receiver sees is red, alternating with blue; swapped: blue first |
| side by side full (a device of 2560x720) | red left half, blue right half, each eye whole at 1280x720 |

Prediction for the anaglyph rows: the eye colours to linear light with a 2.2 gamma (KWin's sRGB), the left matrix times the first eye plus the right matrix times the second, back with 1/2.2; the swapped row predicts red 0.156 to 110, green 0.350 to 158, blue below zero to 0, which is what was measured.

### Proving it: KWin's tests, then the installed packages

1. **KWin's own tests, red then green.** Build the targets `kwin screencast testVirtualOutputProperties testThrowToMenu testScreencasting capturefixture` from two trees: red is +65's source with +66's test patch (`s66-0001-...`) and `src/opengl/anaglyphmatrix.h` (the matrices alone, which the stream test predicts the anaglyph colour with); green is +66's source.
   Run them in a container with the NVIDIA card through CDI and a PipeWire and WirePlumber of the container's own (the lane's `kwin-tests-in-container.sh`; every function of `testScreencasting`, so the headset's 22 split-eye rows and the 2D casts run too).
   Red on +65: `networkedOutput` (all five rows), `networkedChoiceKeptByIdentity`, fifteen `testNetworkedOutput` rows, `testNetworkedFormatChangeReachesStream`, `testNetworkedChoiceComesBack` and `testNetworkScreensUnderThrowTo` fail; the 2D row and every split-eye row pass. Green on +66: everything passes (`testNativePanelRefresh`, an opt-in endurance proof for the isolated GPU rig, skips on both).
2. **The installed packages in a headless Stereo KWin** (`kwin_wayland --virtual --output-count 2`, the published round, the four +66 packages installed by `dpkg -i`): a Throw made by the screencast protocol's version 7 request (a small client with `stream_virtual_output_with_properties` and KPipeWire's `PipeWireSourceStream`), the KWin tests' capture fixture as the declared pair (left eye red, right eye blue), the switches and modes set with `kscreen-doctor` as Display Settings sets them, one frame of the stream per format, ScreenShot2 captures marked as `.pns` when KWin's result says `stereo`, the window menu opened with `workspace.slotWindowOperations()` and walked with fake input (S for "Move to &Screen", T for "Throw &to"), the same device thrown again and another device.
   ScreenShot2 draws each eye itself, so its capture of the network screen is the declared pair in every format; the format's own pixels are in the stream's frames only.
   To prove that a choice reaches the stream, ask for the frame first and make the change second: the client's `grab NAME 5000`, then `kscreen-doctor`; the frame saved must be one sent after the change (`new`) and must show the new format. A grab made after the change can only save the last frame, which proves nothing about when it came.
   Measured on 2026-11-25 (lane scripts `rig66/`, 21 rows): +65 fails the formats after the switches (only the 2D mode), the eleven format rows and the kept choice, and passes the rest (the Throw, the 2D frame, the pair in ScreenShot2, the screen gone after the stream, another device in 2D); +66 passes all 21, each format's frame `new`.
   The window menu on +65: "Move to Screen" lists Screen 1 (Virtual-0), Screen 2 (Virtual-1) and Screen 3 (Virtual-cast-proof), no "Throw to". On +66: "Move to Screen" lists the two local screens, "Throw to" lists "Living room TV".

## The daemon (sparky-stereo-throw 0.1.0)

One engine: the daemon `sparky-stereo-throwd` (in `/usr/lib/x86_64-linux-gnu/libexec`) is the only program of ours that speaks Cast; the command `sparky-stereo-throw` and the page talk to it over the session bus (`org.sparky.Throw`, `/org/sparky/Throw`).
It is a user service (`sparky-stereo-throw.service`, part of the graphical session) and D-Bus activatable (`org.sparky.Throw.service` names the executable and the unit).

| Piece | What it does | Source file |
|---|---|---|
| Discovery | KDNSSD `ServiceBrowser("_googlecast._tcp")`, TXT `id`, `fn`, `md`; refuses to start, said, when Avahi is not running | `src/discovery.cpp` |
| The device table | `data/devices.json` (installed in `/usr/share/sparky-stereo-throw`): per model name, the generation words, video or sound only, codec, level, mode; a model not in it gets the unknown row (the first Chromecast's limits) and the person is told once per device (`sparky-stereo-throwrc [Device][id] ToldUnknownModel`) | `src/devicetable.cpp` |
| The network screen | the v7 request: name the device's `id`, description its name, the table's mode in millihertz, scale 1, not a headset, the pointer embedded | `src/networkscreen.cpp` |
| The stream | KPipeWire's `PipeWireEncodedStream` (H.264 Main, `Speed`, the table's frame rate) on the screen's node; libavformat Matroska with `live=1`, `cluster_time_limit=1000`, `write_crc32=0` into a custom AVIO context on a small HTTP server, one random path per Throw; a reader gets the current group of pictures first, then live packets | `src/streamer.cpp` |
| The channel | CASTv2 over TLS (no peer verification, as the public senders), a hand-written `CastMessage` codec (fields 1 to 9 of openscreen's `cast_channel.proto`, chunks joined), heartbeat every 5 s, three missed PONGs and the device is gone | `src/castmessage.cpp`, `src/castchannel.cpp` |
| A Throw | the mode (the table's, or `[Device][id] Mode=WxH@Hz`), the screen, the stream, LAUNCH `CC1AD845`, CONNECT to its transport, LOAD `video/x-matroska` `LIVE`, a 20 s fetch timeout; states `starting`, `throwing`, `stopped`, `failed`, the last one kept for the page until the next Throw | `src/throwsession.cpp` |
| Saying it | KNotification events `throwStarted`, `throwEnded`, `throwFailed` (high), `unknownModel`; every failure kept in the problems engine under `throw:<id>` until a Throw to that device works | `src/tell.cpp` |
| The read side and the volume | `DeviceInfo(id)`: `/setup/eureka_info?params=device_info,name` and `build_info` on HTTPS 8443, then HTTP 8008, the retry with an empty `Host` on 403 (pychromecast's way), and the receiver's `GET_STATUS` on a channel of its own; `SetVolume(id, level, muted)`: `SET_VOLUME` read back from the `RECEIVER_STATUS` with the same request id | `src/daemon.cpp` |

The D-Bus methods: `Devices()` (JSON, ordered by the devices' names), `Throw(id)`, `Stop(id)`, `DeviceInfo(id)` (answered when the device has answered), `SetVolume(id, level, muted)` (level below 0 leaves it, muted -1 leaves it); signals `DevicesChanged`, `StateChanged(id, state, detail)`.
The command: `sparky-stereo-throw list | throw ID [--wait SECONDS] | stop ID | info ID | volume ID LEVEL|- [mute|unmute]`; `--wait` exits 0 when the device plays, 1 on a failure with its reason, 3 on the timeout.
The page: `kcm_sparkystereo_throw` in the Display group of System Settings, the devices with Throw, Stop Throwing and their page; `systemsettings kcm_sparkystereo_throw --args device=ID` opens a device's page directly.
KWin gives the screencast protocol to the daemon through `org.sparky.throw.desktop` (`X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1`, its `Exec` the daemon's installed path, `NoDisplay`).

## The sound and the codecs (0.2.0)

**The sound** (Daniel, 2026-10-14: "must carry audio", "as a optional sink", the output named "Throw: <device>"): while a Throw runs, the daemon owns a PipeWire node `throw.<id>`, `media.class = Audio/Sink`, `node.description = "Throw: <device>"`, `node.virtual = false` (KDE's Sound page lists it), `node.always-process = true` and `node.want-driver = true` (it is processed when nothing plays into it, so the stream's sound never stops while the picture runs: silence is sound too), F32 stereo at 48 kHz (`src/audiosink.cpp`, a `pw_thread_loop`, the samples handed to the Qt thread).
The person chooses it as any output; it never takes the default by itself: sparky-stereo-hardware's hook (`share/wireplumber/sparky-stereo-new-output.lua`) moves the default only to a `bluez_output.*` or `device.bus = usb` sink that appears after WirePlumber's first 10 seconds, which a Throw sink is not.
The sound is encoded by libavcodec in the stream's container: FLAC, 24 bit (samples as 32-bit integers, the encoder keeps the top 24), in Matroska and MP4; Opus at 256 kbit/s in WebM, which carries Opus or Vorbis only (the page says it is compressed and why); a speaker or a group gets a Throw of the sound alone, FLAC in Ogg (`audio/ogg`).
A reader that connects gets the current group of pictures moved to now and the sound of the last 3 seconds from that time on, so picture and sound start together.

**The codecs:** `data/devices.json` lists per model every video codec of Google's "Supported Media for Google Cast" page (read 2026-11-25; the page gives no date), with profile, level and the modes it allows, in the order the daemon prefers them (AV1, HEVC, H.264, VP9, VP8 where listed; VP9 and VP8 after H.264 while our KPipeWire's libvpx encoders hold 25 frames, the trap below).
The table's pick is the first codec this computer encodes, as KPipeWire's own `PipeWireBaseEncodedStream::suggestedEncoders()` says (H264Main from h264_vaapi, h264_nvenc, libx264 or libopenh264; HEVCMain from hevc_vaapi, hevc_nvenc or libx265; VP8 from libvpx; VP9 from libvpx-vp9 is listed by KPipeWire but gives no live picture in 6.7.4, so the daemon does not count it; KPipeWire 6.7.4 has no AV1 encoder, nor has its master branch on 2026-11-25).
What our FFmpeg itself encodes, run in the rig (lane script `scripts/c/encoders.sh`, one second of a 1920x1080 test picture each): libx264, h264_nvenc, libx265, hevc_nvenc, libvpx, libvpx-vp9, libsvtav1 and libaom-av1 encode; av1_nvenc writes no packet on the station's NVIDIA card; the VA-API encoders were not measured there, since no VA-API render node reaches the rig. So AV1 for a Google TV Streamer waits on an AV1 encoder in KPipeWire, not on FFmpeg.
The container follows the codec: Matroska for H.264 (row 81's review; Google's page names MP4 and WebM, not Matroska), fragmented MP4 for HEVC (`frag_keyframe+empty_moov+default_base_moof`, a fragment at least every half second), WebM for VP8 and VP9.
The person's codec and mode for a device are kept by its identity in `sparky-stereo-throwrc [Device][<id>] Codec= Mode=` (D-Bus `SetChoice`, the command's `choose`, the device's page); a choice the device does not take is refused, and a Throw whose choice this computer cannot encode is refused with the reason, never made in another codec. A device that gets less than it can show is told why on its page (`Codecs::plan`, the sentence "It shows up to … in …; this computer has no encoder for it, so it gets … in …").

**The stream's server:** it listens on this computer's address that faces the device (a UDP socket "connected" to the device names it and sends nothing), answers the device's address only (another address is closed at once), and closes a connection that sends no request line within 5 seconds. The picture and sound travel unencrypted, as the device's own player fetches them.

**The kit for a real device** (lane script `scripts/c/kit/kit.sh "NAME" SECONDS RESULT_DIR`): one container on the host's network with a headless Stereo KWin +66, the staged package and its own Avahi publishing nothing; it throws KWin's capture fixture pair (moved each second, the moving mark) and a 997 Hz tone to one device given by its name, records `sparky-stereo-throw status` each second (player state, idle reason, bytes fetched), stops, checks the screen is gone, and writes `result.json` and `records.jsonl`. With `--loopback-proof` the same container gets no network, a dummy interface and one software device of that name. It installs nothing on the station and changes no setting of the device; it is run by the main session, never by a lane.

## What a Cast device lets the computer set (read at the source, 2026-11-25)

Daniel's aim (2026-11-25): configure a Cast device from the PC as the Google Home app does, with the Google account from KDE's Online Accounts where a setting needs one.

| Interface | Reads or changes | Without the account? | Source | Proved how |
|---|---|---|---|---|
| DNS-SD `_googlecast._tcp` | identity, name, model, address, port (a group on another port) | yes | pychromecast discovery; openscreen | run against the software receiver (rows D1 to D4) |
| CASTv2 receiver namespace | `GET_STATUS` (volume level, muted, control type `attenuation`, `fixed` or `master`, running apps); `SET_VOLUME` (level, muted); `LAUNCH`, `STOP` | yes | pychromecast `controllers/receiver.py`; openscreen | run against the software receiver (I3, V1, V2, T3, T4) |
| CASTv2 multizone namespace | `GET_STATUS`, `GET_CASTING_GROUPS`: the groups a speaker is in | yes, read only | pychromecast `controllers/multizone.py` | read only |
| `/setup/eureka_info?params=device_info,name` (HTTPS 8443, then HTTP 8008) | name, model, maker, whether it has a screen (`capabilities.display_supported`) | yes in pychromecast's daily use, though GHLocalApi's specification marks every endpoint with the token | pychromecast 14.1.1 `dial.py`; GHLocalApi `GHLocalApi.openapi3.json` (global `security`) | run against the software receiver (I1); real devices read only |
| `eureka_info?params=build_info` | the firmware (`cast_build_revision`) | not settled: no public sender reads it without the token | GHLocalApi | the software receiver only (I2); the page says "not given by the device" when it is missing |
| `eureka_info?params=multizone` | the groups | yes | pychromecast `dial.py` (`get_multizone_status`) | read only |
| `/setup/set_eureka_info` | name, locale, time zone, opt-ins | no: `cast-local-authorization-token` | GHLocalApi | read only |
| `/setup/reboot` | restart, factory reset | no: the token | GHLocalApi | read only |
| `/setup/scan_wifi`, `scan_results`, `configured_networks`, `connect_wifi`, `forget_wifi` | Wi-Fi | no: the token | GHLocalApi | read only |
| `/setup/bluetooth/*` | pairing a speaker | no: the token | GHLocalApi | read only |
| `/setup/assistant/*`, `user_eq/set_equalizer`, `supported_locales`, `supported_timezones` | alarms, night mode, do not disturb, equalizer, the lists | no: the token | GHLocalApi | read only |
| Ambient screen and photos, guest mode, creating groups, setup of a new device over Bluetooth Low Energy | | | none of the sources read | not found |

**The token's only open route** (glocaltokens' `client.py` and `const.py`): an Android master token through gpsoauth (the person's password, or a cookie taken from a browser sign-in), then an access token asked as Google's own Android Home app (its package `com.google.android.apps.chromecast.app` and signing hash, service `oauth2:https://www.google.com/accounts/OAuthLogin`), then Google's Foyer `GetHomeGraph` over gRPC (`googlehomefoyer-pa.googleapis.com`), whose answer carries each device's `local_auth_token`.
So the route signs in as another company's app; a desktop account (KDE's or any other) has no such client of its own. A lead from the Astra consult, the scope `cast.backdrop`, is not what glocaltokens uses.
**KDE's Online Accounts** (kaccounts-providers at 1dbb050941, `google.provider.in` and its services): the Google provider asks for email, profile, calendar, tasks, contacts and YouTube upload, and its services are disabled; no scope reaches the Home graph, so no route gives the token today. That is work for queue row 683 (online accounts signed in once); the page says "Sign in under Online Accounts" and why the settings cannot be changed here yet. Nothing of ours asks for or keeps a Google password.
**Generations:** the receiver and setup interfaces are the same on every Chromecast generation as the sources tell them; a speaker has no screen (`display_supported` false), so it has no Throw, only its volume and groups; the assistant and equalizer endpoints are a speaker's. How a Google TV (an Android TV with Cast built in) answers `/setup` was not found in the sources.

**Google's own interfaces (read 2026-11-25, input for queue row 683):**
- The Home APIs (developers.home.google.com/apis): SDKs for Android and iOS apps only; OAuth set up for each app, a grant per structure and per device type (`requestPermissions()`); the device types are Matter's (a speaker: OnOff, LevelControl; `GoogleTVDevice`: media, channel, level, application launcher), and the `Google*` types "are not Google-branded devices (such as Google TV)"; no device name, Wi-Fi, time zone, language, reset, ambient screen, guest mode or groups. Google's speakers and displays are hubs of these APIs, not devices they configure.
- Device Access (the SDM API, scope `https://www.googleapis.com/auth/sdm.service`): thermostats, cameras, doorbells and the Nest Hub Max's camera; nothing of Cast.
- The Cast sender SDK (`cast.framework.CastSession`): volume, mute, media, an app's own message namespace, ending the session; no setting and no setup.
- Google's help: "Set up your Chromecast with a mobile device, as computers do not support the setup process" (Streaming Help answer 2998456); Wi-Fi is changed in the Google Home app on a Chromecast of the 3rd generation or older, an Ultra or an Audio, and on the TV itself on a Chromecast with Google TV or a Google TV Streamer (answer 7331010).

So no Google interface lets another program change a Cast device's settings; the one Google scope a KDE Online Accounts provider (OAuth 2.0) could carry here is SDM's, which has no Cast setting.

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
Its successor for the daemon's proof is the package's `tests/fake-cast-device.py`: the same namespaces on the device's own address, `LOAD` fetched with `ffmpeg -c copy` into `capture-N.mkv` and handed to `ffprobe`, `SET_VOLUME` held and answered, and the device's setup interface on 8008 and 8443 (`eureka_info` with `name`, `device_info` and `build_info`; any other `/setup` path answers 401, and every request is logged with whether it carried a token).
Its modes make the failures: `launch-error` (answers `LAUNCH_ERROR` `NOT_FOUND`), `load-failed`, `no-pong` (stops answering the heartbeat).

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
The stream is H.264 only in 0.1.0, so a row's mode is what its H.264 level allows: the Chromecast Ultra lists 4K only in HEVC and VP9, and its H.264 High 4.2 gives 1080p, so `devices.json` throws to it at 1920x1080 at 30 Hz, not at the 3840x2160 of the table above; the Google TV Streamer's H.264 level 5.2 gives 3840x2160 at 30 Hz.
The model name `Chromecast` does not tell the generations apart, so it takes the first generation's limits.

## The loopback proof (run 2026-11-25)

One container, `--network none`, `--cap-add NET_ADMIN` (the dummy interface) and `--cap-add SYS_NICE` (KWin's file capability), the NVIDIA card through CDI; a dummy interface `dummy0` with 10.81.0.1 to .5, a system bus and Avahi bound to `dummy0` only; five software devices as uid 1000, each announced with `avahi-publish -a -R` (its host name and address) and `avahi-publish -s -H` (the service with `id`, `fn`, `md`, `ca`); then the person's session: a session bus, a stand-in notification server, PipeWire, WirePlumber, `kwin_wayland --virtual` at 1280x1440 (tall, so that a device's page, sized to the screen by a KWin script, shows whole in one capture), the daemon, `tests/loopback/scenario.py`.
The devices: Living room TV (Chromecast, plays), Bedroom TV (Chromecast Ultra, refuses to launch the player), Study screen (a model not in the table), Hall TV (Chromecast, stops answering the heartbeat), Den TV (Google TV Streamer, 4K).
The rows (lane script `scripts/b/run-loopback.sh`; 31, and 32 with the installed package): the five devices found and named, the table's rows, the list ordered by name; the Throw, its network screen at the table's mode, `LAUNCH` and `LOAD` as the device logged them, Stop removing the screen and the device told; the stream the device fetched read by `ffprobe` (H.264 Main, 1920x1080, 30 frames a second at most, level 4.1 at most); the pair on the thrown screen (half side by side: the last frame of the device's capture, left half the left eye's red, right half the right eye's blue; the next Throw comes back in that format; 2D one view); each failure said, its screen removed and kept in the problems engine; what the person is told, read from a stand-in notification server on the session bus (`tests/loopback/notifications.py`); the unknown model at the first generation's limits, told once; the 4K device; the read side and the volume without a token; the page captured in English and in Brazilian Portuguese; with the installed package, the daemon started by the session bus from its service file and KWin's permission check on.
The stream's side by side frame (the last frame of the device's capture, through `ffmpeg -sseof`) is kept marked: `mark_pns.py` of skill stereo-proof-rig writes PNG's `sTER` (mode 1, left eye first) and reads it back; the 2D frame stays a plain PNG; no red-cyan copy is made.
Red: the same session with no Throw (the published set and KWin +66 only) fails every row, the rows of an absence included, since each also measures its presence (the device listed, the screen made, the setup interface asked); the daemon without B11's two methods on the bus fails the read side, volume and device page rows only (C2, C3, I1 to I4, V1, V2).

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
- **Symptom:** rows and checkerboard in the stream show the second eye first, columns are right.
  **Cause:** the pattern shader counts `gl_FragCoord` from GL's bottom row (on a scanout buffer that is its first line), while the stream's storage is mapped top-left first, so the receiver's first row is GL's last; with an even height the parity flips.
  **Fix:** take the receiver's first pixel from `storage.map(Rect(0, 0, 1, 1), frameSize)`, count its row as `height - 1 - y`, and set the shader's `rightFirst` from that parity.
  **How found:** the stream test's per-parity means (even rows blue, odd rows red) and the columns row passing.
- **Symptom:** a network screen offers fewer 3D formats than a monitor: no rows, columns, checkerboard or side by side full.
  **Cause:** the first +66 built its own short list (side by side half, top and bottom, the anaglyphs) instead of following a monitor's.
  **Fix:** the twins follow `DrmConnector::withVirtualStereoModes` under the same conditions, the device's mode being its native raster; frame sequential alone is left out, with its reason in the code.
  **How found:** the design check before the hand-back, against "a screen like the others" and "the whole specification, never a subset".
- **Symptom:** a proof row comparing versions fails although the right package is installed: expected `6.7.4-2+stereo3d66+lc1`, measured `4:6.7.4-2+stereo3d66+lc1`.
  **Cause:** KWin's Debian version has the epoch 4; package file names leave it out, `dpkg-query -W` and apt's `Inst` lines print it.
  **Fix:** compare with the epoch.
  **How found:** the rerun's first pass, row by row against its own logs.
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

### Traps of the daemon (part B, 2026-11-25)

- **Symptom:** a device on a still screen gets nothing: its fetch ends with "Stream ends prematurely at 0", while a Throw with a window moving on the screen plays.
  **Cause:** KWin sends one frame when the stream starts (`OutputScreenCastSource::resume` emits `frame()`) and then frames on damage only; KPipeWire repeats the last frame once, 2 frame intervals later, only to flush its encoder (`m_frameRepeatTimer`, single shot). Both are encoded before the device connects, and a reader that waits for the next keyframe waits for ever.
  **Fix:** the streamer keeps the current group of pictures (the last keyframe and every packet after it; libx264's group is libavcodec's default of 12 frames, VAAPI's 100) and gives it to a reader at once, then the live packets; a group past 32 MiB is let go and a keyframe asked for.
  **How found:** loopback row T5 failed on one run and passed on another; the device's log had `fetch-end` with no bytes and the daemon's had no "first keyframe" line for the first Throw, while the second Throw (the fixture window moving) had it at once.
- **Symptom:** the page's failure line is gone after a Throw failed; the page and the command show the device idle.
  **Cause:** the daemon deleted a finished session, and `Devices()` read the state from the live session only.
  **Fix:** the last state and its detail are kept per device until the next Throw to it.
  **How found:** loopback row F4.
- **Symptom:** `Cannot start recording on a stream without a node ID`.
  **Cause:** KPipeWire 6.7.4's recorder checks the node id even when the object serial (which the protocol says to prefer) is set.
  **Fix:** set both, `setNodeId(node)` always.
- **Symptom:** undefined references to `PipeWireBaseEncodedStream` at link time.
  **Fix:** link `K::KPipeWireRecord` beside `K::KPipeWire`; the proof image needs `libkpipewirerecord6`.
- **Symptom:** `kwin_wayland: Operation not permitted` at the start of a session in a container.
  **Cause:** KWin's postinst gives the binary the file capability `cap_sys_nice`; a container without it cannot execute it.
  **Fix:** `--cap-add SYS_NICE`.
- **Symptom:** the Google TV Streamer's row finds no stream on a loaded machine.
  **Cause:** software H.264 at 3840x2160 takes seconds for its first keyframe when the machine is busy (load 24 to 28 on the station's other lanes).
  **Fix:** the row waits for the daemon's "first keyframe" line (90 s at most), then reads 4 s.
- **Symptom:** the page in Brazilian Portuguese shows English sentences, while System Settings' list of pages is translated.
  **Cause:** the image's environment sets `LC_ALL=C.UTF-8` and has no other locale, so gettext translates nothing; the pages' names come from their JSON metadata, which Qt translates by `LANGUAGE` (skill stereo-proof-rig, lessons-2026-11).
  **Fix:** `locales` with the locale generated, and `LANG`, `LC_ALL` and `LANGUAGE` set together for the page; the page's QML names its domain (`i18ndc("sparky-stereo-throw", ...)`), so the daemon, the command and the page share one catalogue and the capture shows that it is read.
- **Symptom:** a sentence of the device table (a model's generation words) is English in every language.
  **Cause:** it is data, not code, so no extraction sees it.
  **Fix:** the table's words are in the translation table under their own context and the daemon translates them when it describes a device; a product's own name stays as it is.
- **Symptom:** the page's icons and its icon-only Details button are blank in the proof's captures.
  **Cause:** a bare session has no KDE platform theme, so Qt does not use Breeze even with `breeze-icon-theme` installed.
  **Fix:** none needed for the proof (a desktop session has the theme); say it when describing a capture.
- **Symptom:** the package build stops at once: `copy-recipe: No such file or directory: 'git'`; with git added, at `No such file or directory: 'dch'`.
  **Cause:** the edition's `build.sh` copies the recipe as git tracks it, and `lean.debian_prepare` writes the `+lc1` changelog entry with `dch`; a builder image made from the package's Build-Depends has neither.
  **Fix:** the builder image carries `git` and `devscripts`, beside the Lean Code stages' `node-acorn`, `nodejs` and `python3-yaml` (lane script `scripts/b/make-throw-builder.sh`).
- **Symptom:** `dpkg-shlibdeps: error: no dependency information found for /usr/lib/x86_64-linux-gnu/sparky-stereo-problems/libsparky-stereo-problems.so.0`.
  **Cause:** the problems engine keeps its C library in a private folder and ships no shlibs file.
  **Fix:** `override_dh_shlibdeps: dh_shlibdeps -l$(shell pkg-config --variable=libdir sparky-stereo-problems) -- --ignore-missing-info`, with the engine named in Depends (as `sparky-stereo-cec`'s build does).
- **Symptom:** the link gate cannot resolve `kwin-wayland (>= 4:6.7.4-2+stereo3d66+lc1)`.
  **Cause:** +66 is staged, not published.
  **Fix:** a flat local archive of the +66 runtime packages in the gate's archive folder, signed with a throwaway key made in a container (`dpkg-scanpackages`, a Release written by hand with the SHA256 of `Packages` and `Packages.gz` because no image had `apt-ftparchive`, `gpg --clearsign` for `InRelease`), and its entry in `sources.json` with suite `./` (the lane's `scripts/b/make-link-archive.sh`).
- **Symptom:** the red session (no Throw installed) passes four rows: no screen before the Throw, the screen gone after a failure (twice), no token sent.
  **Cause:** each row checked an absence, which holds on a system without the feature; a page row that checked only "a capture was taken" would pass the same way.
  **Fix:** every row of an absence measures its presence too (the device listed, the screen made for that Throw by the daemon's log, the setup interface asked), and the page rows read the window's caption and the device's own log; the red session then fails every row.
  **How found:** the red session's rows, read before the green one was trusted.
- **Symptom:** the daemon's notices never reach anything in the proof's container (`kf.notifications: Failed to notify "The name org.freedesktop.Notifications was not provided"`).
  **Fix:** a stand-in notification server on the session bus (`tests/loopback/notifications.py`, the Desktop Notifications Specification's four methods) that logs each `Notify`; the rows read what the person would be told.
- **Symptom:** a chunked message written with pychromecast's generated module cannot carry `continued` or `remaining_length`.
  **Cause:** pychromecast's `cast_channel_pb2` predates fields 8 and 9 and `CASTV2_1_2`.
  **Fix:** the test writes those frames by hand from openscreen's proto; the codec moves a joined `payload_binary` to `payload_utf8` for a STRING message.

### Traps of part C (0.2.0, 2026-11-25)

- **Symptom:** a VP8 or VP9 Throw shows nothing: the device fetches 0 bytes and the Throw stays "throwing"; KPipeWire's log says `Error setting option tune to value zerolatency` and `No encoder could be created`.
  **Cause:** KPipeWire 6.7.4's `Encoder::buildEncodingOptions` gives every encoder x264's options for the Speed preference (`preset=ultrafast`, `tune=zerolatency`); libvpx and libvpx-vp9 have a `tune` option that refuses that value, so the encoder is not made; KPipeWire then says nothing on its API (no `errorFound`). Upstream's current `encoder.cpp` sets only `threads` there.
  **Fix:** VP8 and VP9 get the NoPreference preference (no `tune`; their own realtime deadline), and the streamer fails a Throw whose encoder gives no picture within 30 seconds. Our KPipeWire's successor should carry upstream's change.
  **How found:** loopback rows E1 and E3, then the daemon's log beside the device's empty capture, then upstream's file.
- **Symptom:** with the tune fixed, a VP9 Throw to a still screen still gives no picture, and after 30 seconds the Throw fails ("no picture came from the encoder").
  **Cause:** KPipeWire 6.7.4's libvpx encoders keep libvpx's default lag of 25 frames; KWin sends a frame only when the screen changes (one at the stream's start, KPipeWire repeats it once), so the encoder never gives its first frame. Upstream's VP9 encoder sets `lag-in-frames` 0 since ("frames arrive on damage").
  With the screen moving, VP9 still gave nothing in 30 seconds (VP8 gave its picture); so 0.2.0 does not count VP9 as encodable (`Codecs::encodable`), and a VP9 choice is refused at once with that reason.
  **Fix:** the table orders VP9 and VP8 after H.264; VP9 waits for our KPipeWire to carry upstream's VP9 settings; a picture that never comes is said by the streamer's 30-second watchdog; the loopback rows for VP8 and H.264 chosen move a window on the thrown screen.
  **How found:** loopback row E1 failing on the watchdog after the tune fix, again with a window moving on the screen (KWin's log names the screen 57 times), then upstream's `libvpxvp9encoder.cpp`.
- **Symptom:** in a long loopback session every page capture shows "The screen locker is broken and unlocking is not possible anymore", while the page rows pass.
  **Cause:** KWin's screen locker locks after its idle time; a container has no logind to unlock; the page rows measured the window's caption and the device's requests, not the screen.
  **Fix:** `kscreenlockerrc [Daemon] Autolock=false, LockOnResume=false` in the session's home before KWin starts; the page rows also fail when KWin's log shows the lock (the `"locked"` event, the greeter).
  **How found:** opening the captures before describing them.
- **Symptom:** a row that times a change of the picture finds the picture already changed at 0 s.
  **Cause:** when the same device's network screen is made again, KWin puts back on it the windows that were on it before (by the screen's identity).
  **Fix:** minimize the window before the Throw and restore it at the instant measured.
- **Symptom:** the last frame of a captured live stream is wrong (half black, or the picture from before a change).
  **Cause:** a live Matroska stream has no index, so `ffmpeg -sseof` lands between keyframes; "the second-to-last packet" misses a change that sent one frame.
  **Fix:** decode the capture in order from the start and keep the last frame (`-update 1`); the stream ends whole at Stop, the muxer writes its trailer before the connection closes.
- **Symptom:** the software device's fetch passes the server's address check in the rig but would not on a real network.
  **Cause:** in one network namespace every address is local, so the route to a device's address starts from that same address.
  **Fix:** the software device fetches from its own address (`source_address`), and the row from another address binds 10.81.0.3.
- **Symptom:** in one run of the loopback proof out of several, the row on the daemon's own words in Brazilian Portuguese measures English words; `throwd-pt_BR.log` is one line, `org.sparky.Throw is already taken on the session bus`.
  **Cause:** the scenario's restart ended the daemon, started its own copy with the language set, and at once ran `sparky-stereo-throw list`. While the copy was still starting, the command found the name without an owner, and the session bus started the installed daemon from its D-Bus service file, in the session's own language. Whichever took the name first won; in the other runs the copy won.
  **Fix:** the language goes where a person's session puts it, in the bus's activation environment (`UpdateActivationEnvironment`, sent with `busctl --address=$DBUS_SESSION_BUS_ADDRESS`, since `dbus-send` cannot send the empty value that returns to the session's language). Then the daemon is ended, and the bus starts it again (`StartServiceByName`); anything that asks for the name in between gets the same language. Before reading words, the row checks who answers: the process that holds the name (`GetConnectionUnixProcessID`) and its `/proc/PID/environ`. A session that starts its own copy, for the log the rows read, runs the scenario only once that copy owns the name.
  **How found:** the main session's rerun; the one-line log; then the bus's own output (the session's `setup.log`), which says `Activating service name='org.sparky.Throw' requested by ... sparky-stereo-throw list` in each restart's gap.
  **Proof that it cannot race:** a file `activate-in-gap` beside the scenario makes every restart ask for the name while nobody owns it. The old restart, given the same ask, fails the row as that run did (English words, the copy's one-line log, the bus's line for the command). The restart through the bus passes it, and each restart's record (`throwd-<lang>.txt`) shows the ask, then `StartServiceByName` answering 2 (already running: the ask had started it, in the language), then the language of the process holding the name. A daemon the bus starts writes to the bus's own output, so the record names where its log went.

## A live stream a real receiver plays (0.3.0, part D)

**What a real Chromecast did** (model name `Chromecast`, first to third generation, on a television; the kit's probe, 2026-11-25; a person at the television confirmed picture and sound for the variant that played):
- A live stream whose pictures stop never plays. KWin sends a screen's frame only when it changes and KPipeWire 6.7.4 repeats the last one once, so a Throw of a still desktop carried a picture at 0 s, one near 0.08 s, then none while its sound went on. The receiver fetched it and reported BUFFERING at its time 0 for as long as it ran.
- The same receiver played H.264 at a constant 30 frames a second, a still picture included.
- How long it took to start after LOAD, still picture at 30 frames a second, by sound: 24-bit or 16-bit PCM stereo in Matroska 1 to 2 s; Dolby Digital (AC-3) 5.1 17 s; FLAC 24 bit 21 s (twice); AAC 40 s. A moving picture with FLAC: about 2 s. The start comes sooner as the data rate rises, but no single byte count explains all of them: a measured rule, not an explained one.
- Its request: one `GET` with `Range: bytes=0-`, a `CAST-DEVICE-CAPABILITIES` header (`"hi_res_audio_supported":false`) and a Chrome 90 user agent on armv7l.

So 0.3.0 keeps the picture coming (KPipeWire's `setConstantFramerate`, below) and takes 24-bit PCM, lossless and the quickest to start, as the default sound in Matroska.

**The sound** is a choice on the device's page, by default the best stereo sound the stream carries that has not failed on that device: PCM 24 bit, FLAC, PCM 16 bit, Opus, AAC, Vorbis, MP3 in Matroska (no PCM or Vorbis in MP4; Opus or Vorbis only in WebM; FLAC, Opus or Vorbis in Ogg), and Dolby Digital or Dolby Digital Plus 5.1 as the person's choice (a stereo source then plays on the front speakers; nothing is upmixed; the sink "Throw: <device>" has six channels).
A Throw that reaches PLAYING records its sound as played on that device (`SoundsPlayed=` in `sparky-stereo-throwrc [Device][<id>]`); one the device does not play within 60 seconds is ended and said with what the device reported, and its sound is recorded as failed (`SoundsFailed=`), so the next Throw takes the next one.

**Every Cast message** is in the daemon's debug log (`QT_LOGGING_RULES=org.sparky.throw.debug=true`: `cast out`, `cast in`), the stream's address token taken out of any URL.

**What each sender does** (read at the source, 2026-11-25):

| Sender | Container and options | Picture | Sound | LOAD and after | Pacing |
|---|---|---|---|---|---|
| VLC 3.0.x (`modules/stream_out/chromecast`, LGPL-2.1-or-later) | Matroska or WebM through libavformat, `live=1`, `reset-ts` | H.264 (x264 veryfast, CRF 21 to 23) or VP8; 24 frames a second forced when the rate is unknown or above 30 | AAC (two channels at most), Vorbis, Opus, MP3 passed on; AC-3 and E-AC-3 only with its passthrough option; anything else, FLAC included, made MP3 320 kbit/s or Vorbis quality 4 | `streamType LIVE`, `"autoplay":"false"` (a JSON string); PLAY only when the person un-pauses; IDLE while buffering is a failed load, and a retry rebuilds the chain | its HTTP server sends at least 512 kB at a time, paces its input at 2 MB |
| GNOME Network Displays (`src/cc`) | `matroskamux`, `webmmux` or `mp4mux` | `pipewiresrc` into `intervideosink`, the encoder reads `intervideosrc` (`timeout` G_MAXUINT64): the last frame at a constant 30 a second; x264 zerolatency, VA-API H.264, VP8 | AAC, Vorbis, Opus | | |
| mkchromecast (MIT) | fragmented MP4 (`frag_keyframe+empty_moov`; on Wayland `mp4mux fragment-duration=1000 streamable=true`) | x11grab at a fixed `-r`; on Wayland `pipewiresrc`, `videorate` and caps at a fixed rate; key frame every 2 s | AAC (Vorbis on X11) | `stream_type LIVE`, autoplay, waits for the media session | |
| catt (BSD-2-Clause) | the file as it is | | | `BUFFERED` | `Range`, `206`, `Content-Length`, `Access-Control-Allow-Origin: *` |
| BigNetScreen (BigLinux and BigCommunity, GPL-3.0-or-later, read only) | mirroring: no container; its HTTP form: MPEG-TS (`video/mp2t`) | H.264 | mirroring: Opus; HTTP: AAC | mirroring: `LAUNCH 0F5096E8` ("Chrome Mirroring"), `OFFER`/`ANSWER` on `urn:x-cast:com.google.cast.webrtc`, RTP with AES-CTR-128 payloads and RTCP feedback, target delay 150 ms; HTTP: the Default Media Receiver | per-stream pacing on a shared budget |
| the Throw 0.2.0 | Matroska `live`, `cluster_time_limit`; each reader from 0 | frames on change only: two, then none | FLAC 24 bit | `LIVE`, autoplay; BUFFERING counted as "throwing" | per packet |
| the Throw 0.3.0 | the same | a constant rate (the last frame again) | 24-bit PCM by default, a choice per device | the same; not PLAYING in 60 s: ended and said | the same |

The other transport, Cast mirroring as BigNetScreen and Chrome do it (Open Screen's `cast/streaming`), has no player buffer: its delay is the target delay, not seconds. In the Throw it would need the encoded packets into RTP instead of libavformat, AES-CTR, the OFFER and ANSWER instead of LOAD, RTCP, and Opus; it is the next part, a person's option beside the buffered stream.

**A stand-in that plays at LOAD proves nothing.** The software device said PLAYING at LOAD, so 0.2.0 passed every loopback row and never played on a real one. Since 0.3.0 the rig has a device whose player is real: `fake-cast-device.py --player chromium` plays the stream in a media element of Debian's Chromium (headless, a fixed version from the snapshot) and reports PLAYING only while the element's time advances, BUFFERING while it waits, with its real `currentTime`. 0.2.0's stream fails on it as on the real device (readyState 0, BUFFERING for 40 s), and the constant streams play on it in the real device's order (PCM before FLAC before AAC). It is more lenient than the real receiver: it played two pictures with PCM sound, which is why the rig also counts the pictures a second in the stream.

**The kit's probe** (`kit.sh NAME SECONDS OUT --probe VARIANTS.json`): a reference sender in the same container throws one live test stream per variant (container, picture still, moving or stopping, sound and channels, `streamType`, `autoplay`), one FFmpeg per request so each reader starts at 0, records every Cast message and the media status each second from LOAD on, stops the receiver after each variant and writes one table (`probe.tsv`, with a column a person fills: what the screen showed); `timeline.py` prints each variant's states. The tone is 997 Hz at -30 dBFS; the 5.1 test plays one channel a second in the order FL FR FC LFE BL BR.

### Traps of part D (0.3.0, 2026-11-25)

- **Symptom:** a Throw of a still screen is fetched by a real Chromecast and never plays (BUFFERING at time 0), while every loopback row passes.
  **Cause:** frames on change only (two pictures, then none); the software device said PLAYING at LOAD.
  **Fix:** KPipeWire encodes the last frame again at the mode's rate (`setConstantFramerate`); the rig's Chromium device plays the stream.
  **How found:** the kit's runs on the real device, then the captures' picture times (`ffprobe -show_entries packet=pts_time`), then GNOME Network Displays' `intervideosrc`.
- **Symptom:** with the constant rate on, the stream has exactly 10 pictures a second.
  **Cause:** KPipeWire makes its repeat timer in `initialize()`, queued after `start()` had already set the rate, with a fixed 100 ms.
  **Fix:** the timer's first interval follows the constant rate.
  **How found:** KPipeWire's frame statistics (`QT_LOGGING_RULES=kpipewire_record_framestatistics.debug=true`: "Processed 10 frames in the last second"), exactly 10.
- **Symptom:** the repeats stop after the first frames.
  **Cause:** the last frame kept was one with no picture (a cursor update, an empty buffer).
  **Fix:** in constant mode only a frame with a picture is kept for repeating.
- **Symptom:** headless Chromium in a container exits at once; its log ends "chrome_crashpad_handler: --database is required".
  **Cause:** a home it cannot write.
  **Fix:** a writable `HOME`, `--disable-crash-reporter --disable-breakpad`.
- **Symptom:** the stand-in's capture is cut at a few hundred bytes.
  **Cause:** the Throw's server serves the newest connection of a device, and the stand-in fetched twice (its capture and its player).
  **Fix:** the player's relay is the device's one reader and keeps the capture.
- **Symptom:** a probe variant meant to stop its pictures sends only its header.
  **Cause:** FFmpeg's muxer waits for the stopped video stream (`select` filter), so the sound stops too.
  **Fix:** prove that red with the daemon's own stream (the kit's loopback proof with 0.2.0).
- **Symptom:** the Lean Code build stops at its link gate: "/: free space ... is below root floor 12884901888".
  **Cause:** not the house floor (1 GiB since ORDER 638, in build main's `lean/archive.py` and `lean/debhelper.py`): the published kpipewire +stereo3d8 carries its own copy of the gate in `debian/sparky-lean` (the 19 October adapter), whose `Archive()` refuses a root floor under 12 GiB; `dpkg-buildpackage` of that tree runs that copy.
  **Fix:** make the successor with `repo/lc-successor.py --in-place`, which replaces the bundled toolkit with build main's (part D's second half, below).
  **How found:** `grep -rn root_min_free_gib` in the unpacked source's `debian/sparky-lean` against build main's `sparky-os/lean`.
- **Symptom:** the software device logged a CONNECT and never the LAUNCH sent 1 ms after it.
  **Fix:** the probe sends them 50 ms apart.

## As packages, and 0.3.0's own stream on a real receiver (part D's second half)

**KPipeWire's successor** is `6.7.4-1+stereo3d10`, recipe `sparky-os/packages/kpipewire-constant-framerate-81d`:
- It follows ORDER 740's `+stereo3d9` (HEVC stereo packing; staged and accepted, KRdp `+stereo3d9` depends on it), not the published `+stereo3d8`: a second, different `+stereo3d9` would collide with 740's, and a later version without 740's patch would take the HEVC packing away. `next-source.sh` takes only the `.dsc` 740 staged (its SHA-256 is in the script) and appends this patch to 740's series.
- The published line has no `+lc1` in its versions (the 19 October adapter: a bundled toolkit in `debian/sparky-lean`, the `lc1` mark in each package's `Sparky-Lean-Code` field). `lc-successor.py --in-place` keeps that shape, so the successor is `+stereo3d10` itself, and it swaps the bundled toolkit for build main's (whose link gate has the house floor of 1 GiB).
- `build.sh` makes the source and the packages in one container of the Lean Code migration image (a lane names its own tag of `sparky-lc-migration:20261020` in `SPARKY_BUILD_IMAGE`; the container's name prefix is `BUILD_NAME_PREFIX`), with the link gate against 740's packages and the build record from `lean.release check-debs`.
- File by file against 740's `+9` and the published `+8`: no path left a runtime package, no `NEEDED` changed; `libKPipeWireRecord.so.6` exports two more symbols (`setConstantFramerate`, `constantFramerate`), in `libkpipewirerecord6.symbols` at `6.7.4-1+stereo3d10`, so the Throw depends on `libkpipewirerecord6 (>= 6.7.4-1+stereo3d10)`.
- KPipeWire's clients (`apt-cache rdepends` over Debian testing and the round): the record library's `kde-spectacle`, `krdp` and `plasma-mobile`; the other libraries' `krdp` and `krfb`; the QML module's `plasma-desktop`, `plasma-workspace` and `xdg-desktop-portal-kde`. On a person's Plasma desktop (apt proof) Spectacle's program and KRdp's library and settings module link it; a person's update with the stages moves KWin `+64` to `+66` and KPipeWire `+8` to `+10` and removes nothing. The constant rate is off unless a client asks: Spectacle's recording on `+10` keeps KPipeWire's own pictures, one or two for each change of the screen (loopback row DK1).

**The Throw 0.3.0** builds against it in a builder that has `+10`'s development package. A builder image made by committing a container run with `--entrypoint bash` keeps that entrypoint, and the recipe's `docker run IMAGE sh -c ...` then runs `bash sh -c ...` ("cannot execute binary file", exit 126); run the setup container with the command `bash -c ...` and no `--entrypoint` (`docker commit --change 'ENTRYPOINT []'` did not clear it).

**0.3.0's own stream on a real Chromecast** (model `Chromecast`, the kit version 3, 2026-11-25; two minutes each, a 997 Hz tone at -30 dBFS):

| Picture | Sound | "throw" to steady playing | playing / buffering of 120 s | behind the screen | the device's clock against the wall clock |
|---|---|---|---|---|---|
| still | PCM 24 bit | 3.8 s | 120 / 0 s | 3.8 s | 1.002 |
| still | FLAC 24 bit | 45.9 s (a first PLAYING at 12 s) | 88 / 32 s | 45.4 s | 0.994 |
| still | Dolby Digital (AC-3) 5.1 | 3.5 s | 120 / 0 s | 3.55 s | 1.000 |
| moving | PCM 24 bit | 3.6 s | 120 / 0 s | 3.6 s | 1.001 |
| moving | FLAC 24 bit | 40.4 s (a first PLAYING at 12 s) | 94.5 / 25.5 s | 39.8 s | 0.998 |
| moving | AC-3 5.1, the channel test | 3.6 s | 120 / 0 s | 3.4 s | 1.000 |
| still | Dolby Digital Plus (E-AC-3) 5.1 | 3.6 s (1.3 s after LOAD) | 75 / 0 s of 75 | 3.35 s | |
| still | Vorbis | 48.2 s (45.3 s after LOAD, a PLAYING at time 0 first) | 38 / 37 s of 75 | 47.3 s | |

The first six runs had the build before the false-start rule; the last two the final build, whose daemon recorded the starts as 1.3 s and 45.3 s after LOAD (the device's PLAYING at time 0, the third status of the Vorbis run, not counted).
Through the kit's reference sender (45 s each), which has no group of pictures to hand over at once: E-AC-3 5.1 and Vorbis never played (PLAYING once at time 0, then buffering at 0); Opus played from 23.5 s, MP3 from 21.3 s.
A person at the television heard the AC-3 5.1 channel test of part D (the reference stream) from more than the television's two speakers; which speakers, and whether each channel came from its own place, is not known.
So the default, 24-bit PCM stereo, starts in under 4 s and stays under 4 s behind; Dolby Digital and Dolby Digital Plus 5.1 from this daemon's stream start as fast (17 s and never from the reference stream); FLAC and Vorbis start after about 40 to 48 s and stay that far behind.

**The delay a person lives with** is read from the device's own time: the status gives `readerZeroAt` (the wall clock of the stream's time 0 for the device: the streamer's clock at its start, on the epoch, plus the reader's first packet time) and `statusAt` (when the device's last MEDIA_STATUS came), and the device plays at `statusAt` what this computer had encoded at `readerZeroAt + currentTime`: it is `(statusAt - readerZeroAt) / 1000 - currentTime` seconds behind the screen, the delay of a pointer move here to the same move there, plus the television's own display delay, which nothing measures.
The method is checked from both ends on the stand-in: the kit's clock page (`scripts/c/kit/clock.html`, the lane's) draws the wall clock as a 28-cell code across the top band; the Chromium stand-in reads it back from the pictures it plays and logs its own clock minus the code. Both gave 2.83 to 2.85 s.
What was measured shows that the delay behind the screen is about the time the device took to start: the device starts at its time 0, and everything it waits for after that it plays late.

**The hardware encoders under the constant rate** (`THROW_ROWS=cost`, loopback row CK1: a still screen for 35 s, processor and GPU sampled between 10 s and 30 s; KWin on the NVIDIA card, VA-API on the AMD card's render node; `KPIPEWIRE_FORCE_ENCODER` names the encoder; every figure contended: the station's GPUs serve its desktop and other lanes):

| Encoder | Build | Pictures in the stream | A second | The daemon's processor (a core is 100 %) | KWin's | The GPU |
|---|---|---|---|---|---|---|
| libx264 | 0.3.0, constant rate | 932 | 31.0 | 67.6 % | 0.4 % | |
| libx264 | 0.2.0 | 2 | | 0.6 % | 0.3 % | |
| h264_nvenc (NVIDIA, through CDI) | 0.3.0, constant rate | 928 | 31.0 | 49.6 % | 0.4 % | NVENC 4.2 % |
| h264_nvenc | 0.2.0 | 2 | | 0.7 % | 0.3 % | NVENC 0 % |
| h264_vaapi (the AMD card's render node) | both | none: "could not resolve the current session render node", no encoder made; the Throw failed and said so after 30 s | | | | |

So a still screen at the constant rate costs about half to two thirds of a processor core at 1920x1080 and 30 a second, against under 1 % for 0.2.0's two pictures; most of it is not the encoding (NVENC's own engine is at 4 %) but each repeated frame passing KPipeWire's filter again (the picture converted on the processor). Keeping the converted frame and handing it to the encoder again would take that away: not built.
VA-API is not measured: our KPipeWire encodes with VA-API only on the GPU that draws the session (the `could not resolve the current session render node` line), and this rig runs KWin on the NVIDIA card or on llvmpipe, never as a loop on the AMD card; on a machine whose desktop is drawn by its AMD or Intel GPU, KPipeWire's own order picks VA-API first.
Load average 8 to 12 during these rows (other lanes on the station): the processor shares are contended figures.

**The kit, version 3** (`scripts/c/kit`, the lane's): `KIT_SOUND` (a sound's id, set with the command's `sound` verb before the Throw and cleared after), `KIT_PICTURE` (`still`, `moving`: the pair moved each second, `clock`: the clock page full screen on the Throw's screen), `KIT_TONE` (`tone`, or `channels`: the 5.1 channel test, each channel a second in the sink's order FL FR FC LFE SL SR, LFE at 60 Hz), `KIT_THROW_DIR` and `KIT_KPW_DIR` (the Throw and KPipeWire folders, the newest staged by default; `none` keeps the image's KPipeWire, for 0.2.0's red); records twice a second with the wall clock; the summary gives "throw" to the first and to steady playing, LOAD to playing, seconds playing and buffering, the delay behind the screen and the device's clock.

### Traps of part D's second half (2026-11-25)

- **Symptom:** a Throw whose device never really plays would sit "throwing" before the television's loading screen with nothing said, and the device's page says a sound started after 10 s while the picture came after 40 s.
  **Cause:** a real Chromecast says PLAYING at its time 0 and then buffers there: for ever with E-AC-3 and Vorbis from the kit's reference stream, 20 to 45 s with FLAC, Opus and MP3 from it and with FLAC and Vorbis from the daemon's own stream. The daemon took that first PLAYING as playing: the sound recorded as played, the 60 s limit stopped.
  **Fix:** the device plays once its time has run past a second; its start is the status's time less its own time. The software device's time runs from its LOAD, and its mode `false-start` (the loopback's Stuck TV) says PLAYING once at 0 and then buffers (row DP5). On the real device the final build recorded Vorbis's start at 45.3 s after LOAD past that PLAYING at time 0.
  **How found:** the kit's records twice a second, `BUFFERING` from the first record although the daemon's first PLAYING came 10 s after LOAD; then every MEDIA_STATUS of the daemon's debug log.
- **Symptom:** the kit's clock page shows in an ordinary window on the Throw's screen, not full screen; KWin's log: "Cannot assign KWin::Rect to KWin::RectF".
  **Cause:** `w.frameGeometry = s.geometry` in a KWin script (a `Rect` into a `RectF`); the script had already set `fullScreen = false`.
  **Fix:** give the geometry as `{x, y, width, height}` and set `fullScreen = true`.
- **Symptom:** a still picture with 24-bit PCM through the reference sender sends 646 bytes and stops, with `-max_interleave_delta 0` or `500000` alike.
  **Cause:** FFmpeg's command line holds the sound behind a picture that stops; not settled.
  **Fix:** none yet; a sparse picture with PCM is not proved on a real device.
- **Symptom:** the kit's daemon run played its tone at about -10 dBFS, above the -30 dBFS asked for runs on a person's television.
  **Cause:** the daemon run's tone was written at 0.3; only the probe had -30 dBFS.
  **Fix:** both at 0.0316 (-30 dBFS), said in `kit.txt`.
- **Symptom:** the Throw's package build stops at `override_dh_builddeb`: "/: insufficient space: 3782213632 free, 4294967296 requested, floor 1073741824", although the gate's scratch is on another disk.
  **Cause:** the gate asks a gibibyte per archive source of its `sources.json` (four for the Throw: Debian, deb-multimedia for the FFmpeg it links, the round, the local archive of the stages) and reserves it on `/` as well; other work on the machine had filled `/` for a while.
  **Fix:** build again when `/` has the room (it had 11 GB minutes later); the stage script refuses a build folder without its `.dsc`, so a failed build never touches the stage.
- **Symptom:** Spectacle's screen recording from the command line writes nothing in the rig.
  **Cause:** Spectacle asks KWin which screen (`queryWindowInfo`) and waits for a click; through NVENC in the rig it also got no frame.
  **Fix:** a click through KWin's fake input (the rig skill's `fakeinput`; KWin takes it only with its permission checks off, so the row has its own session), libx264, and a screen that changes while it records.

## Upstream, as searched on 2026-11-24

- **KDE** (merge requests updated since 2026-10-01 in KWin, KRdp, KPipeWire, xdg-desktop-portal-kde, plasma-workspace): nothing for Cast, network displays or a networked output. Close to the work: KWin 10190 (merged, consumer-picked scale of virtual outputs), 10427 (open, only the creating stream resizes a virtual output), 10355 (merged, screencast plugin ported away from OpenGL, which the next rebase of our screencast patches meets); KRdp 290 (open, drops the zkde_screencast path for the portal only), 275 (open, scale), 239 (open, an audio sink KRdp makes the default, which our design does not do).
- **GNOME Network Displays:** fifteen commits since 2026-10-01, all Miracast or translations; its Cast code last changed on 2026-01-23 (8c6a4de2, Christian Glombek).
- **KPipeWire master** (read 2026-11-25, for part C): no AV1 encoder in `src/`; `encoder.cpp` no longer gives every encoder x264's preset and tune, and `libvpxvp9encoder.cpp` sets `lag-in-frames` 0 (the two traps of part C); ef110be4 (Khudoberdi Abdujalilov, 2026-06-19, "recording: Add PipeWire audio capture") records the default output's monitor or the default input for a recording and makes no sink, so it is not the Throw's "Throw: <device>" output, which stays the daemon's own.
- **openscreen:** 43 commits under `cast/` since 2026-10-01, nearly all Cast Streaming (path B, a later milestone); for the channel, message chunking (64d7c985d1); a new mirroring app id `015B5861` (f2b951181d, Shawn Quereshi).

## Credits

GNOME Network Displays (Benjamin Berg, Christian Glombek, Anupam Kumar, whose commits brought its Chromecast media factory, and the contributor credited in its NEWS for the Chromecast protocol, @kyteinsky), pychromecast (Paulus Schoutsen, Erik Montnemery), the Open Screen Library (The Chromium Authors; Taesun Yeoum for message chunking), KRdp and KPipeWire (Aleix Pol Gonzalez, Arjen Hiemstra and the KDE contributors), and the edition's phone headset work that made the v7 request.
For the study of what a device lets the computer set: GHLocalApi (the community documentation of the Google Home local API, `rithvikvibhu/GHLocalApi`), glocaltokens (`leikoilja/glocaltokens`, the route to the local tokens), kaccounts-providers (KDE's Online Accounts providers), and Astra, the edition's partner for Android, whose answer was a lead checked against those sources.
