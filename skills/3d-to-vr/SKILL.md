---
name: 3d-to-vr
description: >-
  How stereo content and the stereo desktop of Sparky Stereo OS reach a headset or a phone viewer: the headset as one more output of the desktop, 360 and VR180 video, what open software exists today, and what is planned. An early skill; load the general sparky-stereo skill first.
---

# From 3D content to a headset

**Check freshness first.**
Checked on 2026-10-11.
The phone display has an emulated integration proof; release packaging and physical-device qualification remain.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## The principle

A headset is a stereoscope you wear, so in the edition it is **one more output of Stereo KWin**: programs keep handing over full side by side, exactly as for a 3D television, and the headset's output filter does what only a headset needs (lens correction, head tracking, placing the picture in space).
No program has to know a headset exists.

- **Flat stereo content** (a 3D film, a stereo photo, a 3D window) appears on a virtual screen in front of the viewer, each eye seeing its own view.
- **360 and VR180 video** carries its projection in the stream (`sv3d` in MP4, mpv's `demux-projection`); in a headset the viewer looks around by turning their head, on the other registered outputs by the mouse, from the same file ([`stereo-video`](../stereo-video/SKILL.md)).
- **The phone viewer** (Cardboard-style lenses) is the cheapest headset: the same output filter with the phone's lens correction, the picture streamed from the PC.

## What open software exists today

Each a piece, none the whole desktop out of the box; awesome-stereoscopy's [desktop in a headset](https://github.com/danielcamposramos/awesome-stereoscopy#the-desktop-in-a-headset-2018-to-2026) section lists them with sources:

- [Monado](https://monado.dev), the open OpenXR runtime;
- xrdesktop (KDE and GNOME windows in VR), Safespaces, Simula and Stardust XR;
- KWin's own "VR Mode" draft ([plasma/kwin !8671](https://invent.kde.org/plasma/kwin/-/merge_requests/8671)), closest to KDE itself;
- [ALVR](https://github.com/alvr-org/ALVR) and [PhoneVR](https://github.com/PhoneVR-Developers/PhoneVR) with the open [Cardboard SDK](https://github.com/googlevr/cardboard), to wear a phone;
- on the web, the [WebXR Layers API](https://www.w3.org/TR/webxrlayers-1/), whose `stereo-left-right` and `stereo-top-bottom` layouts are the web's only standard stereo vocabulary, inside an immersive session.

## Android XR as a destination (checked 2026-10-07)

[Jetpack XR's spatial-video guide](https://developer.android.com/develop/xr/jetpack-xr-sdk/add-spatial-video) connects Media3 ExoPlayer to a SceneCore `SurfaceEntity` with `StereoMode.SIDE_BY_SIDE`.
This is a route for a stereo film on a virtual screen in a headset.
MV-HEVC uses `MULTIVIEW_LEFT_PRIMARY` or `MULTIVIEW_RIGHT_PRIMARY` and requires Media3 1.6.0 or later plus a device with MV-HEVC decoding support.
Keep this decoder capability separate from displaying a packed side-by-side pair.
The guide also provides hemisphere and sphere shapes for 180° and 360° content.
These APIs do not by themselves implement the edition's desktop-to-headset transport; the phone integration is described below.

## Phone display implementation (checked 2026-10-11)

Build on Fabian Druschke's [desktop receiver handoff](https://invent.kde.org/network/kdeconnect-kde/-/merge_requests/996) and [Android RDP client](https://invent.kde.org/network/kdeconnect-android/-/merge_requests/673).
KDE Connect is an optional authenticated discovery path.
Standalone discovery uses pupnp SSDP, a first-use desktop approval, and a TLS channel pinned to the phone certificate identity.
It authenticates the phone to the desktop; it does not provide mutual certificate authentication.
A shared KRdp owner deduplicates transport leases and removes the virtual output after the last connection closes.
USB tethering reuses this IP path; a charging cable alone and Android Open Accessory are not qualified.

The native-panel request uses screencast v7 and output-device v25 viewports.
A 2400×1080 panel has two 1200×1080 eyes at the reported rational refresh.
KWin sets identity, geometry and stereo mode before output announcement.
Capture renders each native eye into its own half without compressing a full-width desktop.
The Android client applies Cardboard lens correction after decode; the desktop sends the unwarped panel.
Use the SDK default viewer profile until a measured viewer profile is available.
No-lenses mode permits inspection without a viewer.
Touch is suppressed, and volume keys change only the foreground window's brightness.

KPipeWire retains VA-API and software encoding and adds FFmpeg h264_nvenc.
The NVENC path prepares YUV on the CPU and encodes on the GPU; it is not zero-copy.
A passing configuration test without libcuda is not GPU performance evidence.
Hardware encode/decode, radio latency, physical USB, heat and optical comfort require separate device measurements.

## DLNA movie path

Movie mode advertises MediaRenderer:3 with AVTransport, RenderingControl and ConnectionManager through pupnp.
UMS ContentDirectory supplies media URLs; the phone decodes native resources with Media3 and normalizes them to full SBS before the same lens transform.
Mono fills both eyes with the same image.
SOAP play, pause, native-file seek, brightness, volume and mute have independent runtime checks.
GENA carries initial and changed LastChange events.
Movie mode creates no desktop virtual output.
This is an interoperable proof path, not DLNA certification.

ConnectionManager's sink list carries container MIME types.
Panel dimensions and Android decoder MIME/profile declarations are explicit device-description extensions; do not call them standard SinkProtocolInfo fields.
The Flat Headset UMS profile requests full SBS and uses a bounded panel declaration from the HTTP identity or device description.
H.264 compatibility must not bypass required stereo conversion.
After FFmpeg stereo3d, materialize sample aspect into square pixels before fitting the panel.
Matroska DisplayWidth/DisplayHeight describe one eye: Media3 must account for horizontal or vertical packing when deriving packed-frame pixel aspect.
See the [Matroska stereo specification](https://www.matroska.org/technical/notes.html#multi-planar-and-3d-videos).

Native full-SBS MP4, half-SBS Matroska and mono pass every pixel under stated H.264 error bounds, with zero wrong-eye pixels.
Seeking checks a changing frame marker as well as SOAP state.
Lens output is compared with an SDK-rendered reference; this does not independently validate Google's optical model.
Actual audio gain and mute are measured on an isolated sink.
Transcoded MPEG-TS seeking, multichannel binaural audio and PC/phone synchronization remain separate qualifications.
[UPnP AV3](https://openconnectivity.org/developer/specifications/upnp-resources/upnp/mediaserver4-and-mediarenderer3/) includes optional CLOCKSYNC and SyncPlay; it is incorrect to say that the specification defines no synchronized playback.
Support and shared-clock behavior must be measured on both endpoints before promising synchronized PC audio.

## Reproduce safely

Use an immutable private guest base and a disposable overlay for each proof.
Hash the base before and after; never use a shared development VM as a mutable backing file.
In the isolated KWin test session, disable the screen locker explicitly so its error screen cannot replace the fixture.
Check captured images yourself, and use wrong-eye, protocol-version and rate mutants that fail.
Keep exact raw-pixel checks separate from bounded lossy-codec comparisons.
Report decoded-frame handoff timing separately from compositor presentation or photon latency.

## PhoneVR migration checkpoint (checked 2026-10-12)

Continue Harsha Raghu's existing [PhoneVR PR #410](https://github.com/PhoneVR-Developers/PhoneVR/pull/410) before writing another client.
PhoneVR master uses ALVR 20.8.0; the draft targets a December 2024 core.
Both JNI callers compile against their pinned headers and fail against current ALVR `ebec107b` (21.0.0-dev14).
That development revision is distinct from the latest stable release, 20.14.1.
Use a matching upstream client core and server; changing the protocol identifier cannot make incompatible packets compatible.

The current [C API](https://github.com/alvr-org/ALVR/blob/ebec107b7e5f81677fb9c631d239daf2110bf573/alvr/client_core/src/c_api.rs) separates decoder creation, frame acquisition and frame metadata.
Check the frame-acquisition result before using its timestamp.
Match the source eye poses to the decoded frame, then reproject that image to the current pose, including presentations with no new frame.
The draft's latest-tracking quaternion is not the decoded frame's source pose: an isolated synthetic case applies 15 degrees where 45 are required.
Cardboard's neck-model position is also discarded by the draft's pose function.
Keep these failures as regression cases; a header compile or synthetic pose test does not qualify streaming, shader pixels, optical comfort or device latency.

## Current caller and emulated reprojection (checked 2026-10-12)

The continuation of Harsha Raghu's PR #410 and the PhoneVR/ALVR developers' work now builds with matching current client/server cores.
It supplies decoder configuration bytes, preserves the decoded frame's source pose, and retains the neck-model translation.
Release renderers on the GL thread before releasing their borrowed EGL context.
Initialize wgpu staging textures before writing them through GLES, so first-use clearing cannot erase the decoded picture.
Retain the active Android image independently of an overflow queue.
Choose the transfer correction for the actual target; a Cardboard UNORM target must not receive a second SDR conversion.
These are local proposed changes, not an upstream acceptance claim.

A clean x86_64 emulated startup and pause/resume each pass all 3,932,160 checked eye pixels.
The source comparison allows lossy H.264 error; the analytic reprojection checks every pixel, including rasterized boundaries and black disocclusions.
Keep decoded timestamp/source poses fixed while injecting positive and negative yaw with no new frame.
A wrong-rotation reference must fail.
The proof uses actual ALVR transport and Android decoding, but injected poses and pre-lens eye captures.
It does not qualify physical sensors, ARM APKs, SteamVR games, optics or device latency.
Respond to ALVR's IDR requests in a synthetic sender and wait for a keyframe before accepting interframes.
A shell wrapper's zero status is insufficient when the underlying Android command failed; assert explicit counts and output.

## Head-tracked audio proposals (checked 2026-10-12)

Keep the original multichannel bed and source rate until the headphone or speaker edge.
Record whether the game already rotates or binaurally renders its listener; do not rotate that mix twice.
For a world-fixed bed, [PipeWire SOFA](https://docs.pipewire.org/page_module_filter_chain.html) exposes runtime Azimuth, Elevation and Radius for each directional channel.
Recorded ALVR identity and 30-degree poses set a private SOFA node to 0 and 330 degrees, with a wrong-sign control failing.
This proves parameter plumbing, not a rendered binaural mix or its latency.
Fons Adriaensen's packaged AMB rotator passes isolated impulse rotations with zero added sample delay after its controls settle.
Its 256-frame control ramp is separate from device, convolution and scheduling latency.
First-order ambisonics cannot preserve five or seven independent directional channels; keep LFE separate and test a sufficient-order zero-yaw roundtrip.
[IEM SceneRotator](https://plugins.iem.at/docs/plugindescriptions/) and its existing [OSC controls](https://plugins.iem.at/docs/osc/) are candidates for a PC-side implementation, not a measured IEM runtime here.
Reuse the pose already received by ALVR; no new phone transport is needed.
Coordinate the actual audio graph with the [audio skill](../audio/SKILL.md).

## Later work

Continuously driven multichannel rendering, audio-time pose alignment and physical headset qualification remain separate work.
360/VR180 projection and the Stereo Spectator's reverse path remain separate integrations.
No camera tracking or foveated streaming is introduced by these proofs.

## Headset desktop quality and codec qualification (checked 2026-10-14)

Keep the headset viewport in KWin's output configuration: fitted, full-height with panning, zoomed region, and native standalone with KDE fractional scaling.
Fitted remains the default; optional active-window centering starts off and must not move windows on the real monitor.
Match the capture and encode geometry to the panel identity, and adapt bitrate to measured delivery without silently discarding native pixels.
Treat lost worker wakeups, decoder queues and presentation/readback as separate latency stages.
An offline decode speed or a selected low-latency encoder flag is not a display-latency measurement.
The connected, visible Android session owns keep-screen-on and supported sustained-performance mode; bounded wake leases must be released on pause and disconnect.
Sustained-performance mode does not promise to prevent thermal throttling.

H.264 stays the compatible default.
[MS-RDPEGFX](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpegfx/31c6e2b1-335b-4a75-9454-bb2309958c21) negotiates AVC graphics, not an HEVC codec identifier.
A locally qualified HEVC transport prototype uses a separately named [dynamic virtual channel](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpedyc/3bd53020-9b64-4c9a-97fc-90a79e7e1e06) inside the existing authenticated RDP connection.
It checks version and capabilities before selecting a codec, waits for decoder acknowledgement, and leaves standard graphics available for older clients or failed negotiation.
The initial prototype transferred bounded fixtures; the live integration below supersedes that transport limit.
It remains a local proposal, not a released viewer option.

A decoder MIME type is insufficient: check profile, bit depth, colour format, panel size and rate, then decoder initialization.
The emulated Android HEVC decoder accepts a 2340×1080 fixture but declares that size at 30 Hz, not 60 Hz; its faster offline batch decode must not override the declared rate limit.
[Android VideoCapabilities](https://developer.android.com/reference/android/media/MediaCodecInfo.VideoCapabilities) owns the size-and-rate check.
Keep H.264 when HEVC cannot meet the requested panel mode.
Do not infer HEVC Screen Content Coding support from HEVC Main support; qualify the specific tools at both ends.
Credits: KDE, Fabian Druschke and KDE Connect, FreeRDP, Google Android and Cardboard, FFmpeg, Mesa and libva developers.

## Live HEVC integration (checked 2026-10-15)

Keep codec negotiation and access units on the existing authenticated RDP connection.
H.264 remains the default and the recovery path.
Bound queued bytes, queued access units and unacknowledged frames separately; pause capture under pressure rather than discarding dependent HEVC frames.
The qualified implementation permits two unacknowledged frames and rebuilds the H.264 encoder after a failed optional HEVC session.
Treat decoder startup separately from steady-state acknowledgement deadlines.
Reduce VAAPI frame-rate rationals before initializing the encoder; equivalent 30000/1000 and 30/1 inputs did not behave identically on the tested driver.
Keep the conversion matrix, range and encoded colour metadata consistent.

On the tested Android image, legacy OMX.google software codecs omit the software-only attribute.
Recognize the platform implementation names as well as that flag before choosing the presentation path.
Hardware decoders retain their direct surface route; software decoders expose cropped YUV planes for explicit conversion.
Check row stride, pixel stride, crop bounds and the potentially short final row when packing those planes.
The actual MediaCodec YUV samples and all 2,527,200 native rendered RGB pixels match an independent HEVC decode exactly; swapped eyes and inverted rows fail.
An acknowledgement means decoded and submitted to GL, not physical scanout.
A 30 Hz capability negotiation is not a promise of 30 frames per second on an emulated CPU decoder.
Physical hardware decoder colours, thermal performance and end-to-end latency still require device qualification.
Credits: Fabian Druschke and KDE Connect, KDE KRdp/KPipeWire, FreeRDP, Google Android/Cardboard, FFmpeg, Mesa/libva and x265 developers.

## Phone link formats and late-frame recovery (checked 2026-10-15)

Keep KWin's internal capture full side by side and recompute it from the current output view after a mode change.
Test the real viewer through a mode change and back, replication changes and reconnect; a reference decoder alone misses viewer fit errors.
Recompute the texture fit from each incoming frame while keeping the physical panel and lens profile fixed.

Offer Native, full SBS 720p (2560×720), half TB 720p (1280×720), half SBS 720p (1280×720), and full TB 720p (1280×1440).
Native remains the default.
Half TB preserves horizontal detail; half SBS preserves vertical detail; full formats retain both 1280×720 eyes.
Repack each eye independently at the encoder edge to avoid blending across the eye boundary.
Use H.264's standard frame-packing SEI, LEFT first, and unpack before applying the lens transform.
KDE per-output scaling and the reading preset remain separate from transport sampling.

When dropping queued AVC, discard dependent frames until a fresh IDR arrives.
Request that IDR on the next encoder input without reopening the codec or filter graph.
Test repeated requests, ordinary intervening P frames, shutdown before the first input, and a no-op request mutant.
Keep only the newest decoded bitmap awaiting GL and discard expired queued bitmaps; do not discard arbitrary compressed P frames before decoding.
Measure each queue separately with injected receiver work and renderer stalls.
Codec-produced bytes include frames dropped before transmission, so compare them with socket byte deltas rather than calling them network traffic.

Show Wi-Fi standard, frequency, Tx/Rx PHY rates and signal without reading network identifiers or requesting location for these fields.
PHY rate is a hint, not measured available bandwidth.
An optional Automatic choice can use recent local render delay and frame cadence at connection time; preserve every manual choice and show the reason.
Acquire [Android's low-latency Wi-Fi lock](https://developer.android.com/reference/android/net/wifi/WifiManager#WIFI_MODE_FULL_LOW_LATENCY) only while the display session is connected and resumed, and release it on pause or disconnect.
Request AF41 on both RDP sockets where allowed; [RFC 8325](https://www.rfc-editor.org/rfc/rfc8325.html) and [Linux wireless queue mapping](https://wireless.docs.kernel.org/en/latest/en/developers/documentation/mac80211/queues.html) explain its video-priority mapping.
Verify packet markings against an unmarked control, but reserve radio contention, router policy, power and thermal claims for a physical device.
An ordinary app cannot force the radio to refuse low rates.
Credits: Fabian Druschke and KDE Connect, KWin, Arjen Hiemstra and KRdp, Aleix Pol Gonzalez, Marco Martin and KPipeWire, FreeRDP, FFmpeg, Google Android and Cardboard developers.

## Throw waiting scenes (checked 2026-10-15)

Keep the network headset distinct from a local output before announcing it, so the desktop can offer Throw without renaming Move to Screen for local monitors.
Use Throw consistently in approval, settings and phone status, and include all required translations in message extraction.
Validate the installed catalogs as well as their source strings.

Bundle waiting assets locally, with separate connecting and reconnecting clips and a marked still for reduce motion.
Choose a different scene for each wait when several exist.
Use a fixed camera; the reconnect scene drops the ball and throws it again.
Read the standard stereo mark from the media, never infer it from a filename or catalog entry.
Require full side by side, left first; use the existing per-eye lens renderer.
For stills, validate [PNG sTER](http://www.libpng.org/pub/png/spec/register/pngext-1.4.0-pdg.html), mode 1, before image data, including its CRC and eye padding.
A packed width divisible by 16 avoids that padding for equal-size eyes.

Select hardware video decoders, disable audio and loop only while waiting and resumed.
Keep legacy software decoder names out of the hardware path even if their capability flag is wrong.
Missing artwork or unavailable hardware falls back to the marked still, then to identical status text in both eyes.
Handle unsupported video tracks as well as player errors; an empty hardware decoder selection may report only the former.
Clear player ownership before release so synchronous callbacks cannot release it twice.
Release the waiting decoder on the first submitted desktop frame, pause, stop or destruction.
Drain queued GL cleanup before detaching its surface; a renderer's exit request can precede queued cleanup.
Do not dismiss waiting because an empty GL surface redrew itself.
Test connecting, reconnecting, reduce motion, invalid marks, decoder rejection and arrival/pause/close separately.
A debug-only software-decoder fixture tests the loop and renderer; it does not qualify hardware decoding, power or latency on a phone.
Credits: KDE and Fabian Druschke's KDE Connect work, FreeRDP, Google Android/Cardboard and AndroidX Media3 developers.

## Combined-build regression gate (checked 2026-10-16)

Keep the compositor core, screencast plugin and integration fixture from one coherent build when backend structures change.
Record loaded library hashes, not only the package names or source branch.
Run each fitted, full-height, zoom, pointer-following and active-window view in a fresh compositor session, including reconnect.
Check the decoded cursor at both eyes' edges and corners, then check its disparity against the window underneath.
A forced wrong fit and a missing-cursor capture must fail their checks.

Correlate encoder and receiver timings with both payload hashes when the transport inserts a stereo SEI before sending.
Strip only the known inserted marker for the encoder correlation; keep the complete wire hash for the receive correlation.
Require a complete stage chain for every valid displayed timestamp, including the slowest frame.
A short instrumentation smoke test does not replace the scheduled five-minute latency gate or a physical-phone measurement.

## Plasma Mobile receiver study (checked 2026-10-16)

Plasma Mobile uses KWin and Wayland; its mobile startup selects the mobile shell and configuration overlay.
Offer a Kirigami Catch frontend on stock Plasma Mobile and a Stereo KWin headset output as separate choices.
Recommend the stock frontend first for deployment reach, without claiming it wins a performance comparison.
In the Stereo KWin path the receiver supplies declared full side by side; lens correction, scaling and cursor presentation belong to the compositor output.
Do not warp the image in both places.

The accepted KDE Connect Linux receiver checks for KRDC but opens the default `rdp://` handler.
Its URL handoff omits the Throw packet's panel descriptor and certificate pin.
Use an authenticated structured handoff for the Catch frontend, preserving ordinary RDP links.
Share KRDC's FreeRDP session instead of creating another transport.
Its current QWidget view scales a complete image; each-eye unpacking, fitting and lens correction still need implementation.

Keep all five link layouts, the same panel identity and approval rules, fitted/QR/uncorrected profiles, stereo waiting scenes and nine locales.
Measure physical panel pixels through output metadata rather than treating Qt's scaled window dimensions as native resolution.
Cardboard's profile and distortion math can be reused, but its Android build includes JNI and platform-specific services; a Linux adapter is work to implement.

The `iio-sensor-proxy` API supplies discrete orientation, not a timestamped gyro or head quaternion.
Qt Sensors' Linux proxy plugin has the same boundary; the audited SensorFW build is disabled.
A head-fixed screen needs no pose integration.
For optional world-fixed reprojection, qualify a timestamped sensor backend and frame association separately.
Release sensor claims and power inhibitors when the connection ends; never promise to disable thermal protection.

Use an emulated arm64 Plasma Mobile session before a physical phone window.
Separate source audit, guest boot, pixel/transport proof and real-device performance in the report.
A receiver-only phone does not need a local streaming server; rebuilding Stereo KWin does require matching private-API plugins, including Plasma Mobile's task switcher.
Debian/Mobian packages and Alpine-based postmarketOS packages need separate native builds.

Sources: [Plasma Mobile startup](https://invent.kde.org/plasma/plasma-mobile/-/blob/91971ee78079c699d6970a91bd971ccc42d0759c/bin/startplasmamobile.in), [KDE Connect receiver](https://invent.kde.org/danielcamposramos/kdeconnect-kde/-/blob/e1b0792b5/plugins/virtualmonitor/virtualmonitorplugin.cpp), [KRDC presentation](https://invent.kde.org/network/krdc/-/blob/fc11f278f5e4c15ec3e0c978a60a70494f087072/rdp/rdpview.cpp), [sensor API](https://hadess.pages.freedesktop.org/iio-sensor-proxy/gdbus-net.hadess.SensorProxy.html), [Qt sensor backends](https://code.qt.io/cgit/qt/qtsensors.git/tree/src/plugins/sensors/CMakeLists.txt?id=78f4791c27f0c86b021356f6277f0352abd50583), [current distributions](https://plasma-mobile.org/get/).

### Cardboard QR without Google Play services (checked 2026-10-16)

Cardboard 1.35.0's Android QR scanner depends on Mobile Vision even though its lens math is open source.
Replace that dependency in the SDK QR package with [ZXing core](https://github.com/zxing/zxing/tree/zxing-3.5.4/core), not a second scanner app.
Decode the camera's NV21 luminance plane locally and keep Cardboard's profile parser, saved parameters and per-eye distortion meshes.
Retain a bounded camera worker and release it when the scanning activity pauses.
A complete `google.com/cardboard/cfg?p=...` QR carries its profile and can be parsed offline; shortened URLs still require their redirect provider.
Audit every debug and release runtime dependency and the packaged DEX for service references.
AndroidX, Material, protobuf, Guava and the open Cardboard library are not Google Play services.
Prove scanning through the camera API on an AOSP emulator image without Play services, with networking disabled.
Compare both eye captures with independently encoded reference parameters, and reject default-profile and eye-swap controls.
An emulator proves decoding and profile application, not a physical viewer's optical calibration or GrapheneOS device compatibility.
Credits: Google and the Cardboard contributors, the ZXing authors, Fabian Druschke and the KDE Connect developers.

## Native Catch frontend checkpoint (checked 2026-10-16)

Share KRDC's FreeRDP session between its widget view and a Kirigami receiver.
Make an owned frame copy before the FreeRDP worker overwrites its GDI buffer.
Keep one pending frame and one notification; replace an unconsumed frame instead of queuing images.
Derive each-eye fitting from the current decoded dimensions at paint time.
Use KScreen's native mode and scale for the panel descriptor, not Qt's logical window size.

Use the existing KRdp discovery, TLS control and owner-lease path end to end in the proof.
An owner returning a nested `QJsonObject` inside a D-Bus `QVariantMap` can crash while marshalling its reply.
Return `toVariantMap()` and explicitly decode the nested `QDBusArgument` before converting the reply to JSON.
A direct `krdpserver` test bypasses that boundary and cannot qualify discovery.
Verify the RDP certificate through FreeRDP's external certificate callback; a changed pin must fail before a frame arrives.
Bind the RDP destination to the TLS control peer and keep credentials out of command arguments and history.

Run the receiving app on an unmodified KWin as well as the edition's stack.
Capture its own window, decode the source timecode in each eye, and correlate it with the producer's record across reconnect.
An eye-swap control must fail identity; a frozen frame with correct eye labels must fail progress.
Disable all capture and mutation hooks in production builds.
Keep translation catalogs and translated desktop entries in distribution patches, separate from KDE source commits.
The amd64 H.264 and uncorrected-view checkpoint does not qualify ARM hardware decoding, optics, sensors or the native compositor output choice.
Credits: KRDC, Urs Wolfer, Tony Murray, Arjen Hiemstra, the KDE Kirigami, Qt and FreeRDP developers, Fabian Druschke and the KRdp/Flat Headset contributors.

## ARM64 Catch qualification (checked 2026-10-16)

Build ARM64 and amd64 from the same Debian source package, with production capture and mutation hooks disabled.
If cross-build dependency metadata rejects an Architecture: all provider for the foreign architecture, use a native ARM64 guest build instead of inventing a dependency package.
Compare every architecture-independent data file and symlink, then verify the installed ARM64 executable against the package hash.
Keep the ordinary KRDC RDP and VNC plugins in that package.

Boot stock Plasma Mobile on a fresh disposable overlay for each live or negative-control case.
Use the production Catch button and the existing discovery, TLS approval and owner-lease path.
When QEMU user networking forwards the descriptor and control listeners, bind them to the private sender interface so the normal subnet policy still applies.
Do not relax certificate or peer-address checks for an emulator.
Capture the guest framebuffer through QMP and correlate both eye timecodes with the real source before and after reconnect.
A swapped-source control must receive changing frames with reversed eye identities; a blank receiver is not a passing negative control.
A frozen-source control must preserve the eye labels while failing progress on both connections.
A wrong certificate pin must fail before a Throw output appears.

Give TCG enough startup and handshake time, but keep pixel and liveness gates unchanged.
State the stimulus and sender encoder for every result.
A passing functional chart does not clear a failed high-motion stress run; keep both results and their limits visible.
This qualifies ARM64 software reception and per-eye fitting on stock Plasma Mobile.
It does not measure a physical phone's decoder, optics, sensors, battery, thermals or latency, and does not qualify the native compositor headset-output choice.
Credits: the KRDC, KRdp, KDE Plasma Mobile, Kirigami, Qt and FreeRDP developers, the Debian contributors, Fabrice Bellard and the QEMU developers.
