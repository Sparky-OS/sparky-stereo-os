---
name: stereo-video
description: >-
  Preserve and verify stereo layout and colour metadata from codec/container through editor, server, player and transport.
---

# Stereo video, end to end

## Working recipe

1. Read the shared project decisions named in the task brief, then identify stream/container marks, their origin, eye order, sample aspect, colour description and any explicit per-file override.
2. Trace decode, preview, effects, export and playback as separate boundaries; use labelled moving fixtures and an independent metadata reader.
3. Return per-eye geometry/timecodes and round-trip metadata. A correct preview does not establish a correct export, HDR path or network receiver.

For detection, conflicting marks or half/full packing, read [metadata precedence and per-eye geometry](references/metadata-and-geometry.md).
These are settled rules; check the existing shared policy and its callers before designing another detector.

**Check freshness first.**
Written on 2026-10-07; metadata precedence and geometry clarified on 2026-10-20.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; a player also loads [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md) for its video layer.

## The marks a video carries

A side-by-side or top-and-bottom video is an ordinary 2D picture unless something says it holds two views.
The standard marks, each linked from awesome-stereoscopy's [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md):

- **In the stream:** the H.264 and H.265 **frame packing arrangement SEI** (Table D-8, which H.264 V15 (08/2024) numbers D-8 and V16 (06/2026) D-9: side by side, top and bottom, temporal interleaving and the older packings; `content_interpretation_type` gives the eye order; persistence says how long it holds). A 3D television reads this one and switches by itself.
- **In MP4:** the `st3d` box of Spherical Video V2 (with `sv3d` for 360 and VR180).
- **In Matroska and WebM:** `StereoMode` ([RFC 9559](https://www.rfc-editor.org/rfc/rfc9559)).

**Use the format's own mark, and register it.** Each container and codec above has its own stereo field; use that one, never a private tag.
A format without one gets a mark of ours only with its specification page first, like [SVGStereo](https://github.com/Sparky-OS/svgstereo).
Every mark is registered in [stereo-layer](https://github.com/Sparky-OS/stereo-layer) and on the shared standards page before a program writes it.

**Every program in the chain must carry the mark through, never drop it.**
Most 3D breakage is a program in the middle silently writing a plain 2D file.

## Writers: encoders, muxers, editors, servers

| Program | What carries the mark | Where |
|---|---|---|
| x264 (through HandBrake) | `--frame-packing` writes the SEI | [HandBrake #8100](https://github.com/HandBrake/HandBrake/pull/8100), merged |
| x264 (through VLC) | the input's layout signalled by default | [VLC !10366](https://code.videolan.org/videolan/vlc/-/merge_requests/10366), in review |
| x265 | `--frame-packing` writes the H.265 SEI | [x265 #986](https://github.com/Multicorewareinc/x265/pull/986) and the single-SEI fix [#988](https://github.com/Multicorewareinc/x265/pull/988), both in review |
| mkvmerge | `StereoMode` from the H.264 SEI, then from the HEVC SEI | [MKVToolNix !6311](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6311) (merged), [!6312](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6312) (in review) |
| Kdenlive and MLT | a clip knows its packing, the render writes the SEI and `StereoMode` | [Kdenlive `stereo3d-26.08`](https://invent.kde.org/danielcamposramos/kdenlive/-/tree/stereo3d-26.08), [MLT `stereo3d-7.40`](https://github.com/Sparky-OS/mlt/tree/stereo3d-7.40) |
| Universal Media Server | H.264 transcodes keep the SEI | [#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330), in 15.9.0 |
| PeerTube | a container's packing kept through transcoding, right eye first included | [#7816](https://github.com/Chocobozzz/PeerTube/pull/7816), merged |
| Android's Media3 | the SEI read in MP4 and fragmented MP4, right-eye-first modes, `StereoMode` in the WebM muxer | [androidx/media #3439](https://github.com/androidx/media/pull/3439), in review |

**Test every way the mark can be written.**
An encoder option is not done when the common case passes: x265's option was correct with each SEI in its own unit, and a reviewer found stale bytes in `--single-sei` mode, a bug older than the option.
Enumerate the modes (single SEI or not, access unit delimiters on and off, repeated headers on and off, every packing type) and check each stream with an independent parser and with FFmpeg's `trace_headers`.

## Readers: decoders and players

- **Decoders:** our FFmpeg keeps the SEI's declaration for as long as the standard says, also when it is sent only on keyframes ([FFmpeg #24628](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24628), in review), and prefers the stream's own mark as the side data says ([#24643](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24643), in review). Qt Multimedia names every packing in `QVideoFrameFormat::StereoMode` and fills it from the FFmpeg backend ([Sparky-OS/qtmultimedia `stereo3d-6.11`](https://github.com/Sparky-OS/qtmultimedia/tree/stereo3d-6.11)); in the edition's build its video output also takes the views apart itself, so a Qt Quick player keeps only its QML and its 3D menu.
- **Frame sequences** (temporal interleaving, Table D-8 type 5 in H.264 V15, 08/2024, D-9 in V16, 06/2026): pair the frames in stream order on the input side, never from a queue that drops the oldest frame; trust per-frame view marks only when they alternate, and never let a stream-wide Matroska tag flip the eyes.
- **A side-by-side Matroska file is authored with one eye's display size.** With the pair's full width as the display size, FFmpeg doubles the sample aspect ratio and a player pre-scales the picture before the views are taken apart.
- **Automatic precedence:** applicable codec SEI first, then container metadata (`StereoMode`, `st3d`), then descriptive tags, then detection as a last safety net. An explicit user override is separate. Read declared per-eye geometry before inferring half/full packing; use the shared policy's tested fallback instead of copying historical aspect thresholds into each application. See [the decision and proof recipe](references/metadata-and-geometry.md).
- **What a player shows:** every packing unpacked to full side by side, the video in its own layer declared to Stereo KWin, the controls, subtitles and on-screen display in the 2D part, identical in both eyes. A player with output modes of its own loses them in the edition's build.
- **For video that declares nothing,** a menu with the input format (every packing, both eye orders), Swap Eyes, left or right only, and not 3D. Examples: [Dragon Player `stereo3d-26.04`](https://invent.kde.org/danielcamposramos/dragon/-/tree/stereo3d-26.04), [Haruna `stereo3d`](https://invent.kde.org/danielcamposramos/haruna/-/tree/stereo3d) with [MpvQt](https://invent.kde.org/danielcamposramos/mpvqt/-/tree/stereo3d), [mpv](https://github.com/Sparky-OS/mpv/tree/stereo3d) (its stream detection merged upstream as [#18490](https://github.com/mpv-player/mpv/pull/18490)), [VLC Stereo `3.0.24-3d-stereo`](https://github.com/Sparky-OS/vlc/tree/3.0.24-3d-stereo).
- **360 and VR180:** the projection comes from the stream (mpv's `demux-projection`, the `sv3d` box); the player shows a flat view the viewer turns with the mouse or keys, the same direction in both eyes; FFmpeg's `v360` filter converts projections.

## Android's media path (checked 2026-10-07)

- **Keep the layout beside the decoded frames.** Media3 carries it in [`Format.stereoMode`](https://github.com/androidx/media/blob/main/libraries/common/src/main/java/androidx/media3/common/Format.java); decoding to a MediaCodec `Surface` is a separate step from presenting each eye.
- **The MP4 work is still in review.** [Media3 #3439](https://github.com/androidx/media/pull/3439) adds H.264/H.265 frame packing SEI detection in MP4 and fragmented MP4 when the container has no stereo value. It adds right-eye-first modes and writes the four side-by-side/top-and-bottom eye orders in WebM's `StereoMode` ([RFC 9559, Table 5](https://www.rfc-editor.org/rfc/rfc9559.html#section-5.1.4.1.28.3)). A container value wins in this patch; test conflicting marks before treating it as the edition's detection policy.
- **Do not assume portable MediaCodec stereo side data.** The [Android 16 `MediaFormat` source](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-16.0.0_r1/media/java/android/media/MediaFormat.java) defines no public stereo-layout key. On API 31 and later, [`getSupportedVendorParameters()` and `subscribeToVendorParameters()`](https://developer.android.com/reference/android/media/MediaCodec) can expose a codec's vendor metadata through its output format. Check the named codec and the meaning of each field before using it; keep extractor metadata when no stereo field is available.

## Quality

In the edition: decode at the source's depth (10, 12, 16 bits), keep each eye at full resolution (a high-quality filter, not a plain stretch, when a half-width or half-height source is scaled up), pass the colour description on (BT.709 or BT.2020, PQ or HLG, range), and play audio at 24-bit 48 kHz or more wherever the hardware offers it, with float output and SoXR for any resampling.
In a patch offered upstream, keep the project's own defaults and make these paths available.

## Proof for this kind of work

As in the general skill, with a fixed set of clips, each LEFT red and RIGHT blue with a frame number: the SEI side by side and top and bottom, left eye first and right eye first; the same in Matroska; a clip whose SEI comes only on keyframes (ordinary x264 output: many players lose the mark after the first frame); an undeclared 32:9 clip; a plain 2D clip.
For each: both eyes captured over time with the same frame number, the right colour in each eye, one declaration per stereo clip, none for the 2D clip, and the player's 2D parts identical in both eyes.
For writers: the mark checked byte by byte against an independent writer, in every mode, and read back by a second program.

## Screen-content codec comparisons (checked 2026-10-14)

Compare codecs at matched decoded text quality and unchanged eye geometry, not equal QP numbers.
Record each eye's text-region SSIM, the tolerance used to match it, frame count, refresh, GOP and B-frame/lookahead settings, and encoded packet bytes separately from container and network overhead.
Keep a coarse-quality negative control and an eye-swap control.
A short static-text chart with a moving window is not a sustained bandwidth or latency qualification.
Use Matroska's registered `StereoMode` for fixtures and preserve the mark after transport.

[Upstream x265 SCC](https://x265.readthedocs.io/en/master/cli.html#screen-content-coding-scc-options) needs an `ENABLE_SCC_EXT` build and describes intra-block-copy modes.
This does not prove palette or adaptive colour transform support.
The measured FFmpeg/x265 combination logs `Unknown option: scc` but returns success and writes ordinary Main-profile HEVC.
Reject that result as an SCC comparison; check the emitted profile/extension and decoder support as well as the exit status.
A VA-API profile query and a real encode are required before claiming hardware support; an encoder listed in FFmpeg help is insufficient.
Credits: FFmpeg, x264/VideoLAN, x265/Multicoreware, Mesa, libva and Android developers.

## Editing, playback and transport boundaries (2026-10-19)

Kdenlive's render-comparison approach suggests a small reusable regression project: a labelled stereo clip, one title/overlay, one effect and an export.
Check source metadata, timeline preview, proxy/transcode, render output and independent playback separately; effects may assume an ordinary single view.
Keep per-eye history separate where needed, and compare an unchanged 2D project.
A successful monitor preview does not qualify every effect or higher-bit-depth MLT path.

Keep input eye-order correction separate from the display output format.
Offer the same Swap Eyes action in applicable playback menus and preserve an explicit per-file override without modifying the source implicitly.
Include portrait mono clips: being taller than wide is not sufficient evidence for top-and-bottom stereo.
Compare fullscreen controls, double-click behavior and restored file choices as interaction checks, separately from decoded pixels.

For a slow phone stream, measure source playback, compositor capture, conversion/encode, socket delivery, decode and presentation separately.
Start with a fixed synthetic moving chart over a stable route, then the same clip, resolution, codec and duration over USB, ordinary Wi-Fi and Direct Wi-Fi.
Confirm the actual route; a USB cable connected for diagnostics does not establish the streaming route.
Link utilization alone cannot locate the bottleneck. Packet-size changes need loss, latency and queue evidence; do not assume jumbo or tiny packets improve delivery.
Record viewer-reported usability as an observation, not a measured frame rate or universal performance claim.
