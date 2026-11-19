# What HandBrake does with a 3D source (ORDER 36, measured 2026-11-19)

A study of HandBrake, the transcoder Daniel wants a stereo preview in.
Measured on Debian testing's HandBrakeCLI 1.11.2+ds1-1+b3 (what the edition ships; the edition carries no HandBrake of its own in `/var/tmp/sparky-repo-current`), in a Debian testing container with FFmpeg 9.0.2, x264 r3108, the x265 HandBrake bundles (4.0), and MKVToolNix 103.0.
No display was used; everything below is either a measurement on that version or a file:line read of upstream master (28cae12c0, 2026-11-18).

## Making the marked samples

Generate the two eyes yourself, mark each eye differently (a red "L" and a blue "R" in `drawtext` over `testsrc2`), stack them, declare the stacking with the `stereo3d` filter, and keep every file a few seconds of 640x360 per eye:

```sh
ffmpeg -f lavfi -i "testsrc2=size=640x360:rate=25,drawtext=text='L':fontcolor=white:fontsize=220:x=140:y=70:box=1:boxcolor=red@0.7[l]" \
       -f lavfi -i "testsrc2=size=640x360:rate=25,drawtext=text='R':fontcolor=white:fontsize=220:x=380:y=70:box=1:boxcolor=blue@0.7[r]" \
       -filter_complex "[l][r]hstack=inputs=2,stereo3d=sbsl:sbsl[v]" -map "[v]" \
       -t 2 -c:v libx264 -crf 22 -x264-params frame-packing=3 sbs-h264.mkv
```

- H.264 SEI: `-x264-params frame-packing=3` (side by side) or `=4` (top and bottom). The `stereo3d` filter's metadata does not reach x264 on its own; the x264 option is what writes the frame packing SEI (payload type 45).
- Matroska StereoMode: `mkvmerge -q -o out.mkv --stereo-mode "0:side_by_side_left_first" in.mkv` (values `mono`, `side_by_side_left_first`, `top_bottom_left_first`, …, one per StereoMode number).
- MP4 `st3d`: has no direct writer in FFmpeg 9.0's muxer options, so remux a StereoMode-marked Matroska with `ffmpeg -i in.mkv -map 0:v -c copy -movflags +faststart out.mp4`; the demuxer's coded side data becomes the muxer's `st3d` box (movenc.c `mov_write_st3d_tag`).
- HEVC SEI: the x265 in this HandBrake has no frame-packing option, so there is no encoder route. Build the payload natively per H.265 D.2.2 (payloadType 45, syntax order: id ue, cancel u1, arrangement type u7: 3 is side by side, 4 top and bottom , , quincunx u1, content_interpretation_type u6 = 1, then the display/self-contained flags; the H.264 tail order differs, do not reuse its writer) and splice the prefix SEI NAL into the Annex B stream before the first VCL NAL with a small Python injector (the lane's `evidence/inject-hevc-sei.py`).
- Always include a plain 2D control file with no mark at all; a read that finds a mark in the control is reading something else.

Verify every sample before trusting any downstream result:

```sh
ffprobe -v error -show_entries stream_side_data=side_data_type -of default=nw=1 file        # coded (container) side data
ffprobe -v error -show_frames -select_streams v -read_intervals "%+#8" -of json file        # frame side data: the SEI, via the decoder
mkvinfo file | grep -i "stereo mode"                                                        # Matroska StereoMode
d=$(grep -abo st3d file.mp4 | head -1 | cut -d: -f1); dd if=file.mp4 bs=1 skip=$((d+8)) count=1 | od -An -tu1   # st3d stereo_type byte (payload starts at type+8)
```

## Reading HandBrake's scan and outputs

`HandBrakeCLI --scan --json -i sample` prints one JSON document.
On 1.11.2 the scan of a stereo file has no Stereo3D key at all: every 3D mark is invisible to it.
On master, 1d2087644 ("libhb: preserve the stereo 3d metadata") reads `AVStereo3D` from the demuxer's coded side data (libhb/stream.c:6149-6153, coded side data only: frame-level SEI is never decoded at scan) and reports it in the scan JSON (libhb/hb_json.c:399-412); the enum crosses FFmpeg's boundary by a straight field copy (libhb/hbffmpeg.c:726-745 `hb_stereo_3d_ff_to_hb`, numerically identical enums).

For the outputs, re-encode every sample to x264 and to x265, into Matroska and into MP4, and read each output back with the same three tools above (SEI via frame side data after decode, StereoMode via mkvinfo, `st3d` via the byte scan).
The lane's loop and table are `evidence/readback3.sh` and `evidence/survival-table-1.11.2.txt`.

## What survives

Measured on HandBrakeCLI 1.11.2, 9 sources × (x264, x265) × (mkv, mp4) = 36 encodes: **every 3D mark dropped, 36/36, no message**.
1.11.2 has no 3D-stereo path in libhb at all (`git grep -i stereo` on the tag finds audio layouts and the `HB_FRAME_PACKING = 45` constant only).
The 2D control stays correctly unmarked in all four of its outputs.

Upstream master of 2026-11-18 differs by exactly two commits, and a master-level build would instead:

- read container marks and the pre-muxed SEI's coded side data at scan (stream.c:6149-6153) and report Stereo3D in JSON (hb_json.c:399-412): but not a frame-level-SEI-only source, which scans as plain 2D with no notice;
- write Matroska StereoMode / MP4 `st3d` on every encoder/container pair, by attaching `AV_PKT_DATA_STEREO3D` coded side data at the mux (libhb/muxavformat.c:674-686);
- write the H.264 frame packing SEI on x264 encodes of marked sources (libhb/encx264.c:404-414, our PR #8100, mapping to `i_frame_packing` 3/4; SBS and TAB only);
- still write no SEI for x265: HandBrake's encx265.c has no mapping. x265 itself gained `--frame-packing` on 2026-10-28 (multicoreware commit 1cf669d, closing issue #970, via PR #986), so the remaining gap is HandBrake's side of the call.

The per-mark matrix (every H.264 and HEVC arrangement type 0-6, Matroska StereoMode 0-14, `st3d` types 0/1/2, `sv3d`) is in the lane's `evidence/marks-table.md`; its anaglyph StereoModes 10/12 have no `AVStereo3D` value in FFmpeg 9.0 (matroska.h STEREOMODE_STEREO3D_MAPPING), and `mov_write_st3d_tag` warns and skips anything but 2D/TAB/SBS.

## The preview's path (master GTK 4 front end, read-only, nothing built)

The summary preview draws one decoded still: `gtk/src/preview.c` drives the decode and hands the frame to a GtkPicture widget (`gtk/src/hb-backend.c` `hb_backend_video_frame` / the scanlib title decode), so the surface is an ordinary GTK texture, one flat picture, with no notion of eye packing.
The stereo layout is available at the seam where the still is produced: the same `hb_title_t` Stereo3D fields the scan JSON already serializes (hb_json.c:399-412): before the frame reaches preview.c.
What step 2 needs there: decode any packing, rearrange to full side by side, present the 1280-wide surface, and declare it once to KWin per the house contract (flat as the opt-out). How a GTK 4 application declares a stereo surface from its own process is an open step-2 question.

## Traps met on the way

- **x265 writes no frame packing SEI.** Symptom: HEVC samples made "the same way" as the H.264 ones have no SEI in ffprobe. Cause: the x265 in Debian's HandBrake (4.0) has no frame-packing option; only x265 ≥ the 2026-10-28 commit (1cf669d) does. Fix: inject the SEI NAL natively per H.265 D.2.2 with a tiny Python writer. Found by diffing the sample verification: H.264 files had frame-level Stereo 3D, HEVC files did not, and x265's option list has no such switch.
- **mkvmerge rewrites your container mark.** Symptom: a stream meant to be SEI-only (no container mark) still showed StereoMode 1 in mkvinfo. Cause: MKVToolNix 103.0 auto-derives StereoMode from the frame packing SEI (!6311 merged 2026-09-21, !6312 2026-10-11). Fix: for a true SEI-only sample, inject into the elementary stream and remux to MP4 (`-c copy`), whose muxer does not inspect the SEI. Found when the "SEI-only" mkv control failed its own absence check.
- **1.11.2 drops every mark silently.** Symptom: all 36 encode outputs read back unmarked, including sources HandBrake itself could not have misparsed. Cause: no 3D path in libhb on that tag at all. Fix: none in 1.11.2; the edition needs a master-level HandBrake or a backport of 1d2087644 + b0145ad9f. Found by the full-matrix run, after the 2D control ruled out a readback error.
- **Master's scan is blind to SEI-only sources.** Symptom (source-verified): a stream whose only mark is the frame packing SEI reports no Stereo3D in `--scan --json`. Cause: stream.c:6149-6153 reads coded side data only; the scan never decodes a frame. Fix for step 2: during scan, decode a few frames and harvest frame-level side data. Found by reading the scan path after container-marked sources did report.
- **`st3d` sits eight bytes past its atom type.** Symptom: reading the byte at the `grep -abo st3d` offset gives the ASCII "s". Cause: the atom's size (4) and type (4) precede the payload. Fix: `skip=$((offset+8))`. Found on the first byte read.

