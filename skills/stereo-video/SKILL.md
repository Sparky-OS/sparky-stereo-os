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
- **In an MPEG-2 stream:** the JP3D user data (`S3D_video_format_signaling`: 0x03 side by side, 0x04 top and bottom, 0x08 2D; no eye-order field), which FFmpeg's MPEG-2 encoder writes and its decoder reads; a Sony KDL-46EX725 switched to 3D on it (2026-10-23). See [stereo-serving](../stereo-serving/SKILL.md).
- **In MP4:** the `st3d` box of Spherical Video V2 (with `sv3d` for 360 and VR180).
- **In Matroska and WebM:** `StereoMode` ([RFC 9559](https://www.rfc-editor.org/rfc/rfc9559)).

**Use the format's own mark, and register it.** Each container and codec above has its own stereo field; use that one, never a private tag.
A format without one gets a mark of ours only with its specification page first, like [SVGStereo](https://github.com/Sparky-OS/svgstereo).
Every mark is registered in [stereo-layer](https://github.com/Sparky-OS/stereo-layer) and on the shared standards page before a program writes it.

**Every program in the chain must carry the mark through, never drop it.**
Most 3D breakage is a program in the middle silently writing a plain 2D file.

## Writers: encoders, muxers, editors, servers

A server or caster that feeds another device (a DLNA television, a cast receiver) sends that device's own frame format at its raster, not the desktop's full side by side: see [stereo-serving](../stereo-serving/SKILL.md).

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
- **What a player shows:** every packing unpacked to full side by side by copying, each eye at the resolution the stream carries it (a half view stays half; Stereo KWin resizes once, see the proof rig's [Unpacking is a copy](../stereo-proof-rig/SKILL.md#unpacking-is-a-copy)), the video in its own layer declared to Stereo KWin, the controls, subtitles and on-screen display in the 2D part, identical in both eyes. A player with output modes of its own loses them in the edition's build.
- **For video that declares nothing,** a menu with the input format (every packing, both eye orders), Swap Eyes, left or right only, and not 3D. Swap Eyes is the per-file correction of the input, labelled "Swap left and right eyes", offered only while the video is shown in 3D, and kept with the player's own per-file state (the resume position); the player offers to save it to the file and writes the file only when the person chooses that, after which the file carries the correction and the per-file Swap Eyes is unmarked again. The definitive swap is the output's, in Display Configuration. Examples: [Dragon Player `stereo3d-26.04`](https://invent.kde.org/danielcamposramos/dragon/-/tree/stereo3d-26.04), [Haruna `stereo3d`](https://invent.kde.org/danielcamposramos/haruna/-/tree/stereo3d) with [MpvQt](https://invent.kde.org/danielcamposramos/mpvqt/-/tree/stereo3d), [mpv](https://github.com/Sparky-OS/mpv/tree/stereo3d) (its stream detection merged upstream as [#18490](https://github.com/mpv-player/mpv/pull/18490)), [VLC Stereo `3.0.24-3d-stereo`](https://github.com/Sparky-OS/vlc/tree/3.0.24-3d-stereo).
- **360 and VR180:** the projection comes from the stream (mpv's `demux-projection`, the `sv3d` box); the player shows a flat view the viewer turns with the mouse or keys, the same direction in both eyes; FFmpeg's `v360` filter converts projections.

## Rows, columns, checkerboard and frame sequences, unpacked by copying (2026-10-22)

The four packings that interleave the views (H.264 Table D-8 types 0, 1, 2 and 5, Table D-9 in V16; H.265 Table D.8) reach Stereo KWin like the others: two views side by side, left eye first, each at its own resolution, declared once.
The first view takes the even rows, the even columns, or the samples whose row and column add up to an even number; content_interpretation_type 2 (H.264 D.2.26) and Matroska's right-first StereoMode values 4, 6, 8 and 14 ([RFC 9559](https://www.rfc-editor.org/rfc/rfc9559) 5.1.4.1.28.3) put the right view there.

- **Rows and columns:** each view is every other row (a 1920x1080 frame gives two 1920x540 views, one 3840x540 picture) or every other column (two 960x1080 views). On the GPU, span the whole picture, move the texture coordinates half a source sample towards the view's own row or column (minus a half for the first view, plus a half for the second), and sample with `GL_NEAREST`: each output pixel lands on the centre of its own sample. Linear filtering at those coordinates averages the two views.
- **Checkerboard:** each view is half the width (960x1080 from 1920x1080), and its sample in a row alternates side from one row to the next. A linear texture coordinate cannot follow the row's parity: draw the view one row at a time, each row moved half a sample to its own side, or move the coordinate in the fragment shader.
- **What is exact:** RGB and 4:4:4 pictures are copied sample for sample. In 4:2:0 the luma is copied exactly and each chroma sample covers both views, so the nearest one is taken; nothing better exists in the stream.
- **Quincunx side by side** (side by side with quincunx_sampling_flag) is shown as side by side: each half already holds its view's own samples.
- **Frame sequence:** pair the frames where the decoder hands them over, before any queue that drops late pictures (VLC: the decoder core's queue, not the video output's filters). Follow the SEI's current_frame_is_frame0_flag in output order (FFmpeg's `AVStereo3D.view`: `LEFT` is frame 0, whatever the eye order) while the marks alternate: frame 0 starts a pair, a frame 1 without its frame 0 is dropped. Without marks (Matroska's StereoMode 13 and 14, a user's choice), pair two frames in turn from the first. Copy each pair into one side by side picture, each view at its own resolution, dated as frame 0; pictures in hardware surfaces cannot be copied, so refuse that output format and let the decoder fall back to decoding into memory.
- **The whole list, from every source:** the stream's SEI (in the packetizer, in the decoder's own reading of the first block, and in the frame side data), the container's mark, and the user's choice in the player's input menu, each packing with both eye orders.

Test it with address fixtures for each packing and eye order (the proof rig's `fsbs_ids.py make PACKING W H out.png [--right-first]`), lossless: FFV1 `gbrp` in Matroska with each StereoMode, unmarked copies for the user's choice, and lossless RGB H.264 with x264's `frame-packing` SEI.
x264 always writes content_interpretation_type 1, so a right-first SEI fixture is the same stream with the field rewritten; read every fixture back with an independent reader (FFmpeg's `showinfo` prints the type, the view and "inverted") before trusting it.
Add a flat 4:2:0 fixture (the first view gray 64, the second 192) for the luma, and for frame sequences a timed stream whose two views carry the pair's number.
A timed stream that starts with a lone second view is the control: marked, it pairs right; in a container without marks, the same frames pair one picture off, so the check is shown to fail.

## Quality

In the edition: decode at the source's depth (10, 12, 16 bits), hand each eye at the resolution it has (a half-width or half-height eye is rearranged into full side by side, never scaled up in the program; Stereo KWin resizes once, into the window or the screen), pass the colour description on (BT.709 or BT.2020, PQ or HLG, range), and play audio at 24-bit 48 kHz or more wherever the hardware offers it, with float output and SoXR for any resampling.
In a patch offered upstream, keep the project's own defaults and make these paths available.

## Proof for this kind of work

As in the general skill, with a fixed set of clips, each LEFT red and RIGHT blue with a frame number: the SEI side by side and top and bottom, left eye first and right eye first; the same in Matroska; a clip whose SEI comes only on keyframes (ordinary x264 output: many players lose the mark after the first frame); an undeclared 32:9 clip; a plain 2D clip.
For each: both eyes captured over time with the same frame number, the right colour in each eye, one declaration per stereo clip, none for the 2D clip, and the player's 2D parts identical in both eyes.
For writers: the mark checked byte by byte against an independent writer, in every mode, and read back by a second program.

## Android, screen-content codecs, editing and transport

These narrower topics have their own references:
- [Android's media path](references/android-media-path.md) (checked 2026-10-07): Media3's `Format.stereoMode`, the MP4 frame packing SEI work in review, and no portable MediaCodec stereo side data.
- [Screen-content codec comparisons](references/screen-content-codecs.md) (checked 2026-10-14): matched text quality, the controls, and x265 SCC that silently falls back to Main profile.
- [Editing, playback and transport boundaries](references/editing-playback-transport.md) (2026-10-19): a reusable editing regression project, the per-file eye swap, and a slow phone stream measured stage by stage.
