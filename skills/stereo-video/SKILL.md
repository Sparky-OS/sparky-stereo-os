---
name: stereo-video
description: >-
  How stereo 3D video keeps its 3D through every program that touches it on Sparky Stereo OS, from encoder to container, server, decoder and player: the standard marks, the detection order, what a player must offer, 360 and VR180, quality, and how to prove it. Load the general sparky-stereo skill first.
---

# Stereo video, end to end

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; a player also loads [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md) for its video layer.

## The marks a video carries

A side-by-side or top-and-bottom video is an ordinary 2D picture unless something says it holds two views. The standard marks, each linked from awesome-stereoscopy's [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md):

- **In the stream:** the H.264 and H.265 **frame packing arrangement SEI** (Table D-8: side by side, top and bottom, temporal interleaving and the older packings; `content_interpretation_type` gives the eye order; persistence says how long it holds). A 3D television reads this one and switches by itself.
- **In MP4:** the `st3d` box of Spherical Video V2 (with `sv3d` for 360 and VR180).
- **In Matroska and WebM:** `StereoMode` ([RFC 9559](https://www.rfc-editor.org/rfc/rfc9559)).

**Every program in the chain must carry the mark through, never drop it.** Most 3D breakage is a program in the middle silently writing a plain 2D file.

## Writers: encoders, muxers, editors, servers

| Program | What carries the mark | Where |
|---|---|---|
| x264 (through HandBrake) | `--frame-packing` writes the SEI | [HandBrake #8100](https://github.com/HandBrake/HandBrake/pull/8100), merged |
| x264 (through VLC) | the input's layout signalled by default | [VLC !10366](https://code.videolan.org/videolan/vlc/-/merge_requests/10366), in review |
| x265 | `--frame-packing` writes the H.265 SEI | [x265 #986](https://github.com/Multicorewareinc/x265/pull/986) and the single-SEI fix [#988](https://github.com/Multicorewareinc/x265/pull/988), both in review |
| mkvmerge | `StereoMode` from the H.264 SEI, then from the HEVC SEI | [MKVToolNix !6311](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6311) (merged), [!6312](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6312) (in review) |
| Kdenlive and MLT | a clip knows its packing, the render writes the SEI and `StereoMode` | [Kdenlive `stereo3d-26.08`](https://invent.kde.org/danielcamposramos/kdenlive/-/tree/stereo3d-26.08), [MLT `stereo3d-7.40`](https://github.com/danielcamposramos/mlt/tree/stereo3d-7.40) |
| Universal Media Server | H.264 transcodes keep the SEI | [#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330), in 15.9.0 |
| PeerTube | a container's packing kept through transcoding, right eye first included | [#7816](https://github.com/Chocobozzz/PeerTube/pull/7816), in review |
| Android's Media3 | the SEI read in MP4 and fragmented MP4, right-eye-first modes, `StereoMode` in the WebM muxer | [androidx/media #3439](https://github.com/androidx/media/pull/3439), in review |

**Test every way the mark can be written.** An encoder option is not done when the common case passes: x265's option was correct with each SEI in its own unit, and a reviewer found stale bytes in `--single-sei` mode, a bug older than the option. Enumerate the modes (single SEI or not, access unit delimiters on and off, repeated headers on and off, every packing type) and check each stream with an independent parser and with FFmpeg's `trace_headers`.

## Readers: decoders and players

- **Decoders:** our FFmpeg keeps the SEI's declaration for as long as the standard says, also when it is sent only on keyframes ([FFmpeg #24628](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24628), in review), and prefers the stream's own mark as the side data says ([#24643](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24643), in review). Qt Multimedia names every packing in `QVideoFrameFormat::StereoMode` and fills it from the FFmpeg backend ([danielcamposramos/qtmultimedia `stereo3d-6.11`](https://github.com/danielcamposramos/qtmultimedia/tree/stereo3d-6.11)); in the edition's build its video output also takes the views apart itself, so a Qt Quick player keeps only its QML and its 3D menu.
- **Frame sequences** (temporal interleaving, Table D-8 type 5): pair the frames in stream order on the input side, never from a queue that drops the oldest frame; trust per-frame view marks only when they alternate, and never let a stream-wide Matroska tag flip the eyes.
- **A side-by-side Matroska file is authored with one eye's display size.** With the pair's full width as the display size, FFmpeg doubles the sample aspect ratio and a player pre-scales the picture before the views are taken apart.
- **Where a player finds 3D, in this order:** the stream's mark (SEI, `st3d`, `StereoMode`), then tags (`yt3d:` on YouTube), then, last, the frame's shape: a display aspect ratio of at least 2.5 is full side by side.
- **What a player shows:** every packing unpacked to full side by side, the video in its own layer declared to Stereo KWin, the controls, subtitles and on-screen display in the 2D part, identical in both eyes. A player with output modes of its own loses them in the edition's build.
- **For video that declares nothing,** a menu with the input format (every packing, both eye orders), Swap Eyes, left or right only, and not 3D. Examples: [Dragon Player `stereo3d-26.04`](https://invent.kde.org/danielcamposramos/dragon/-/tree/stereo3d-26.04), [Haruna `stereo3d`](https://invent.kde.org/danielcamposramos/haruna/-/tree/stereo3d) with [MpvQt](https://invent.kde.org/danielcamposramos/mpvqt/-/tree/stereo3d), [mpv](https://github.com/danielcamposramos/mpv/tree/stereo3d) (its stream detection merged upstream as [#18490](https://github.com/mpv-player/mpv/pull/18490)), [VLC Stereo `3.0.24-3d-stereo`](https://github.com/danielcamposramos/vlc/tree/3.0.24-3d-stereo).
- **360 and VR180:** the projection comes from the stream (mpv's `demux-projection`, the `sv3d` box); the player shows a flat view the viewer turns with the mouse or keys, the same direction in both eyes; FFmpeg's `v360` filter converts projections.

## Android's media path (checked 2026-10-07)

- **Keep the layout beside the decoded frames.** Media3 carries it in [`Format.stereoMode`](https://github.com/androidx/media/blob/main/libraries/common/src/main/java/androidx/media3/common/Format.java); decoding to a MediaCodec `Surface` is a separate step from presenting each eye.
- **The MP4 work is still in review.** [Media3 #3439](https://github.com/androidx/media/pull/3439) adds H.264/H.265 frame packing SEI detection in MP4 and fragmented MP4 when the container has no stereo value. It adds right-eye-first modes and writes the four side-by-side/top-and-bottom eye orders in WebM's `StereoMode` ([RFC 9559, Table 5](https://www.rfc-editor.org/rfc/rfc9559.html#section-5.1.4.1.28.3)). A container value wins in this patch; test conflicting marks before treating it as the edition's detection policy.
- **Do not assume portable MediaCodec stereo side data.** The [Android 16 `MediaFormat` source](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-16.0.0_r1/media/java/android/media/MediaFormat.java) defines no public stereo-layout key. On API 31 and later, [`getSupportedVendorParameters()` and `subscribeToVendorParameters()`](https://developer.android.com/reference/android/media/MediaCodec) can expose a codec's vendor metadata through its output format. Check the named codec and the meaning of each field before using it; keep extractor metadata when no stereo field is available.

## Quality

In the edition: decode at the source's depth (10, 12, 16 bits), keep each eye at full resolution (a high-quality filter, not a plain stretch, when a half-width or half-height source is scaled up), pass the colour description on (BT.709 or BT.2020, PQ or HLG, range), and play audio at 24-bit 48 kHz or more wherever the hardware offers it, with float output and SoXR for any resampling. In a patch offered upstream, keep the project's own defaults and make these paths available.

## Proof for this kind of work

As in the general skill, with a fixed set of clips, each LEFT red and RIGHT blue with a frame number: the SEI side by side and top and bottom, left eye first and right eye first; the same in Matroska; a clip whose SEI comes only on keyframes (ordinary x264 output: many players lose the mark after the first frame); an undeclared 32:9 clip; a plain 2D clip. For each: both eyes captured over time with the same frame number, the right colour in each eye, one declaration per stereo clip, none for the 2D clip, and the player's 2D parts identical in both eyes. For writers: the mark checked byte by byte against an independent writer, in every mode, and read back by a second program.
