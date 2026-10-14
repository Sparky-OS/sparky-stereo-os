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
This prototype transfers bounded fixtures; it is not yet a released live HEVC viewer option.

A decoder MIME type is insufficient: check profile, bit depth, colour format, panel size and rate, then decoder initialization.
The emulated Android HEVC decoder accepts a 2340×1080 fixture but declares that size at 30 Hz, not 60 Hz; its faster offline batch decode must not override the declared rate limit.
[Android VideoCapabilities](https://developer.android.com/reference/android/media/MediaCodecInfo.VideoCapabilities) owns the size-and-rate check.
Keep H.264 when HEVC cannot meet the requested panel mode.
Do not infer HEVC Screen Content Coding support from HEVC Main support; qualify the specific tools at both ends.
Credits: KDE, Fabian Druschke and KDE Connect, FreeRDP, Google Android and Cardboard, FFmpeg, Mesa and libva developers.
