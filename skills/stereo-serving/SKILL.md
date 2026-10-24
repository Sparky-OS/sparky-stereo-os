---
metadata:
  requires-packages: kcm-ums
name: stereo-serving
description: >-
  Serve or stream stereo media to another device (DLNA and UPnP renderers, media servers, casting, network players) in exactly the frame format that device takes, at its raster, declared; never in the desktop's internal format.
---

# Serving stereo to another device

## Working recipe

1. Find out what the receiving device takes: its profile, its capabilities, its manual. Find out which profile the server actually matched, in the server's own log, before any test.
2. If the device takes the source's packing, send the source as it is. No conversion is the best conversion.
3. If a conversion is needed, repack, then scale to the raster the device declares (never an assumed one), with square pixels; encode in a codec that can carry the declaration, and declare the result.
4. Prove it on the real device with a labelled fixture: the matched profile, the server's decision line, the exact encoder command, the output's size and aspect, and what the person sees with glasses.

**Check freshness first.**
Written on 2026-10-23, after the first real-renderer test of a Universal Media Server change on a Sony KDL-46EX725.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; for decoding and marks, also [`stereo-video`](../stereo-video/SKILL.md).

## The boundary: the desktop is not the network

| | A program on the desktop | A server feeding another device |
|---|---|---|
| Who receives the picture | Stereo KWin | a television, a player, a phone, a cast receiver |
| The frame it gets | full side by side: two views, left first, each at its own resolution, declared once | exactly the frame format that device takes, at its raster |
| Who resizes | Stereo KWin, once, at the output | the server, to the device's raster, as the format defines |
| A half top-and-bottom 1920x1080 source | one 3840x540 buffer | sent as it is, if the device takes half top and bottom; otherwise repacked and scaled to 1920x1080 in the device's format |

The desktop rule ([full side by side at any resolution](../sparky-stereo/SKILL.md)) is about what a program hands the compositor.
A server is an output, like Stereo KWin's outputs: the device decides.
Describing a television's frame in the desktop's terms ("two views at their own resolution") is the mistake this skill exists to stop.

## The device's formats

- **Half side by side** and **half top and bottom**: the two views squeezed into one frame at the device's raster, each view half the width or half the height. Every 3D television of the HDMI 1.4 era takes these at 1920x1080, and the 4K 3D televisions of 2015 and 2016 at 3840x2160.
- **Frame packing**: two full views and an active space in one tall frame (1920x2205 for 1080p24). A television takes it over HDMI and from its own player; over the network, take it only if the device's profile says so.
- **2D**: one view, for a device or client that shows no stereo. Choose the left view unless the person chose otherwise.
- **Anaglyph** only when the person or the profile asks for it, never by default.

## Converting

- **FFmpeg's `stereo3d` never resamples.** Between half formats it only repacks and changes the sample aspect: half top and bottom 1920x1080 to half side by side (`ab2l:sbs2l`) gives 3840x540 with a sample aspect of 1:4, not 1920x1080. Follow it with a scale, and check the result with ffprobe (width, height, sample aspect).
- **The raster comes from the device, never from an assumption.** Read it from the device's declared parameters, such as its profile's maximum width and height in UMS, or the capabilities it reports. Then:
  - a half-to-half repack keeps the source frame's raster (half top and bottom 3840x2160 becomes half side by side 3840x2160 on a 4K 3D television);
  - only then apply the device's limits, as the server already does for 2D;
  - when the device declares nothing, keep the source's raster. Choosing a size the device never stated is out of the server's scope.
  - Never hard-code 1920x1080.
- **Declare what you send,** in the codec's own mark plus the container's where there is one (Matroska StereoMode, MP4 `st3d`). Then the television switches to 3D by itself.
  - **H.264 and H.265:** the frame packing SEI.
    - The edition's FFmpeg inserts or replaces it without re-encoding, with the `frame_packing` option of the `h264_metadata` and `hevc_metadata` bitstream filters: `frame_packing_type`, `frame_packing_view` (the eye order) and `frame_packing_quincunx`, and what they leave unset from the stream's or the packet's Stereo 3D side data. The message goes in front of each key frame. H.264 takes every type of its table D-8 in both eye orders, H.265 the three types of its table D.8.
    - It comes from the edition's patches 0010 to 0013 to ffmpeg-dmo (Daniel Campos Ramos, 2026-10-12). Upstream FFmpeg does not have it yet (master 179d083, checked 2026-10-23).
    - Without it, FFmpeg's libx264 wrapper writes the SEI from the frame's Stereo 3D side data (side by side 3, top and bottom 4), or x264's `frame-packing` parameter sets it; the wrapper drops the mark for a right-eye-first frame, with a warning. FFmpeg's libx265 wrapper reads no stereo side data.
  - **MPEG-2:** it cannot carry the frame packing SEI, but it has its own mark, the JP3D user data: `S3D_video_format_signaling`, the identifier `JP3D`, a length of 3 and a 7-bit `S3D_video_format_type` (0x03 side by side, 0x04 top and bottom, 0x08 2D). It is the `Stereo_Video_Format_Signaling` user data of Sony's patent [EP 2434767 A1](https://patents.google.com/patent/EP2434767A1/en) (Ikuo Tsukagoshi), in the user data of the picture or sequence header; its side by side carries the left view in the first half, and it has no eye-order field, so send the left view first. FFmpeg's `mpeg2video` encoder writes it from the frame's stereo 3D side data and its decoder reads it ([mpeg12enc.c](https://github.com/FFmpeg/FFmpeg/blob/master/libavcodec/mpeg12enc.c) and [mpeg12dec.c](https://github.com/FFmpeg/FFmpeg/blob/master/libavcodec/mpeg12dec.c), Vittorio Giovara, 2013).
  - Tested on 2026-10-23 on a Sony KDL-46EX725: an MPEG-2 half side-by-side clip carrying JP3D switched it to 3D by itself, and the same clip without JP3D stayed flat.
- **A conversion loses the mark in stock FFmpeg.** Its `stereo3d` filter copies the input frame's properties and never writes the output layout onto the frame, so the encoder writes no mark, or the input's. Check the output's mark with ffprobe, not only its size.
- **Universal Media Server's MEncoder engine carries no 3D:** it writes no mark and converts no layout; for a 3D source it only converts the subtitles. Use its FFmpeg engine for a 3D conversion.
- **Keep the eye order.** Read it from the stream's mark, the container's mark or the person's choice, as [`stereo-video`](../stereo-video/SKILL.md) says, and write the declaration with the order you actually send.
- **Subtitles** burned into a converted stream go into each view at the same place, at the screen plane, before packing.

## Profiles

- **A specific device profile must outrank the generic one.** In Universal Media Server, `LoadingPriority` decides: on 2026-10-23 the generic `Sony-BraviaEX.conf` (priority 2, pattern `KDL.+EX[3457]`) still won over `Sony-BraviaEX725.conf` (priority 1) for a KDL-46EX725, so the specific profile never applied. Check the log line "Matched media renderer ..." before testing anything else.
- **Leave `Output3DFormat` (or the server's equivalent) empty for a device that takes the source's packing.** Set it only for a device that needs a conversion, to the format it takes.

## Where it applies in the edition and its upstreams

- **Universal Media Server**: renderer profiles, 3D conversion and the frame packing declaration (our merged #6330 and #6389, and #6420).
- **Jellyfin**: flattening 3D to one view for 2D clients (#18060), and any 3D transcode for a client.
- **VLC Stereo**: its renderer output (Chromecast and UPnP) and its stream output (`sout`).
- **PeerTube**: transcoding profiles for 3D uploads (our merged #7816).
- **Kdenlive, HandBrake and FFmpeg presets** that export for a named device: same rule, the device's format.
- **Not this skill:**
  - The phone headset over KRdp (Flat Headset): it is one of Stereo KWin's outputs, see [`3d-to-vr`](../3d-to-vr/SKILL.md).
  - Anything a program hands the desktop: see [`sparky-stereo`](../sparky-stereo/SKILL.md).

## Proof on the real device

- **The fixture:** left view with "LEFT EYE" in red, right view with "RIGHT EYE" in blue, a white square shifted in each view so that it floats in front of the screen. Mark it only in the stream when the test is about detection, or in the container when it is about the mark.
- **What to record:**
  - the profile the server matched;
  - its decision ("forced to transcode to the format ...");
  - the exact encoder command;
  - the output's width, height and sample aspect;
  - whether the device switched to 3D by itself;
  - what the person sees: the right colour in each eye, and the square in front. If the square is behind the screen, the eyes are swapped.
- **Change one thing at a time.** Before converting anything, test the device with the source as it is, so a later failure can be placed.
- Example, 2026-10-23, KDL-46EX725: with its own profile and `Output3DFormat = sbs2l` set for the test, the server decided correctly and ran `stereo3d=ab2l:sbs2l`. The 3840x540 MPEG-2 output reached the television as a thin strip in the middle of the screen, without a 3D declaration. Both faults are in the conversion path, which this skill's Converting section now covers.
- Second example, the same day and television: the MPEG-2 half side-by-side control pair, with and without JP3D, as the Converting section says. Only the clip with the mark switched the television to 3D.
