# What HandBrake does with a 3D source (ORDER 36, measured 2026-11-19)

A study of HandBrake, the transcoder Daniel wants a stereo preview in.
The original study measured Debian testing's HandBrakeCLI 1.11.2+ds1-1+b3, in a Debian testing container with FFmpeg 9.0.2, x264 r3108, the x265 HandBrake bundles (4.0), and MKVToolNix 103.0.
That is a Debian baseline; the edition also enables deb-multimedia, whose candidate is different, as the reconciliation below measures.
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
- HEVC SEI: check the encoder used by HandBrake separately from the system CLI. For a build without the option, construct a prefix SEI payload following H.265 D.2.16, payload type 45, and insert it before the first VCL NAL; use the HEVC syntax, not the H.264 tail syntax, and verify it through an independent decoder.
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
On master, 1d2087644 ("libhb: preserve the stereo 3d metadata") reads `AVStereo3D` from the demuxer's coded side data (libhb/stream.c:6149-6153, coded side data only: decoded frame-level stereo data is not copied into the title) and reports it in the scan JSON (libhb/hb_json.c:399-412); the enum crosses FFmpeg's boundary by a straight field copy (libhb/hbffmpeg.c:726-745 `hb_stereo_3d_ff_to_hb`, numerically identical enums).

For the outputs, re-encode every sample to x264 and to x265, into Matroska and into MP4, and read each output back with the same three tools above (SEI via frame side data after decode, StereoMode via mkvinfo, `st3d` via the byte scan).
The lane's loop and table are `evidence/readback3.sh` and `evidence/survival-table-1.11.2.txt`.

## What survives

Measured on Debian's HandBrakeCLI 1.11.2, 9 sources × (x264, x265) × (mkv, mp4) = 36 encodes: **all 32 marked-source outputs lost their 3D marks, with no message**.
1.11.2 has no 3D-stereo path in libhb at all (`git grep -i stereo` on the tag finds audio layouts and the `HB_FRAME_PACKING = 45` constant only).
The 2D control stays correctly unmarked in all four of its outputs.

The two relevant stereo commits on upstream master of 2026-11-18 are 1d2087644 and b0145ad9f; source inspection predicts that a master-level build would instead:

- read container marks and the pre-muxed SEI's coded side data at scan (stream.c:6149-6153) and report Stereo3D in JSON (hb_json.c:399-412): but not a frame-level-SEI-only source, which scans as plain 2D with no notice;
- write Matroska StereoMode / MP4 `st3d` on every encoder/container pair, by attaching `AV_PKT_DATA_STEREO3D` coded side data at the mux (libhb/muxavformat.c:674-686);
- write the H.264 frame packing SEI on x264 encodes of marked sources (libhb/encx264.c:404-414, our PR #8100, mapping to `i_frame_packing` 3/4; SBS and TAB only);
- still write no SEI for x265: HandBrake's encx265.c has no mapping.
  x265's option was merged through [PR #986](https://github.com/Multicorewareinc/x265/pull/986) on 2026-10-22; whether an installed encoder provides it must be measured.

The per-mark matrix (every H.264 and HEVC arrangement type 0-6, Matroska StereoMode 0-14, `st3d` types 0/1/2, `sv3d`) is in the lane's `evidence/marks-table.md`; its anaglyph StereoModes 10/12 have no `AVStereo3D` value in FFmpeg 9.0 (matroska.h STEREOMODE_STEREO3D_MAPPING), and `mov_write_st3d_tag` warns and skips anything but 2D/TAB/SBS.

## The preview's path (master GTK 4 front end, read-only, nothing built)

The summary preview draws one decoded still: `gtk/src/preview.c` drives the decode and hands the frame to a GtkPicture widget (`gtk/src/hb-backend.c` `hb_backend_video_frame` / the scanlib title decode), so the surface is an ordinary GTK texture, one flat picture, with no notion of eye packing.
The stereo layout is available at the seam where the still is produced: the same `hb_title_t` Stereo3D fields the scan JSON already serializes (hb_json.c:399-412): before the frame reaches preview.c.
What step 2 needs there: decode any packing, rearrange to full side by side, present the 1280-wide surface, and declare it once to KWin per the house contract (flat as the opt-out). How a GTK 4 application declares a stereo surface from its own process is an open step-2 question.

## Traps met on the way

- **An x265 release label does not establish the option.** Symptom: HEVC samples have no SEI, and the installed CLI rejects `--frame-packing 3`. Cause: this candidate lacks the option despite its upstream merge. Fix: build the encoder carrying the upstream option before adding the HandBrake mapping; injection serves fixtures only. Found by comparing a two-frame control encode with the same command plus the option, and by the parameter API, as detailed below.
- **mkvmerge rewrites your container mark.** Symptom: a stream meant to be SEI-only (no container mark) still showed StereoMode 1 in mkvinfo. Cause: MKVToolNix 103.0 auto-derives StereoMode from the frame packing SEI (!6311 merged 2026-09-21, !6312 2026-10-11). Fix: for a true SEI-only sample, inject into the elementary stream and remux to MP4 (`-c copy`), whose muxer does not inspect the SEI. Found when the "SEI-only" mkv control failed its own absence check.
- **1.11.2 drops every mark silently.** Symptom: all 36 encode outputs read back unmarked, including sources HandBrake itself could not have misparsed. Cause: no 3D path in libhb on that tag at all. Fix: none in 1.11.2; the edition needs a master-level HandBrake or a backport of 1d2087644 + b0145ad9f. Found by the full-matrix run, after the 2D control ruled out a readback error.
- **Master's scan is blind to SEI-only sources.** Symptom (source-inspected): the only stereo mark is frame-level side data. Cause: stream.c:6149-6153 reads coded side data only; the preview scan already decodes frames but does not harvest their stereo data. Fix for step 2: read stereo side data at that existing decode boundary. Found by following the scan path after container-marked sources did report.
- **`st3d` sits eight bytes past its atom type.** Symptom: reading the byte at the `grep -abo st3d` offset gives the ASCII "s". Cause: the atom's size (4) and type (4) precede the payload. Fix: `skip=$((offset+8))`. Found on the first byte read.

## Reconcile before rebuilding (ORDER 742, measured 2026-11-19)

Use a fresh amd64 container with Debian testing, deb-multimedia forky and the signed edition repository, together with preferences extracted from its published apt configuration package.
Run `apt-cache policy`, simulate the install and install the candidates.
The measured candidates and installed versions were:

| Package | Version | Archive |
| --- | --- | --- |
| handbrake, handbrake-cli, handbrake-gtk | 1:1.11.2-dmo3 | deb-multimedia |
| x265, libx265-217 | 1:4.3-dmo1 | deb-multimedia |
| ffmpeg, libavcodec63, libavformat63 | 10:9.0.2-dmo1+stereo3d15+lc1 | edition |

The package indexes mention HandBrake in the creator task's recommendations, and the build tree lists it in the applications list and app centre.
Those references do not constitute a HandBrake binary package or a build recipe.
Search all package indexes and the build tree before claiming an absence.

`handbrake` is a metapackage with the dependency `handbrake-cli | handbrake-gtk`.
Requesting it together with the CLI does not install the GTK program when recommendations are disabled; explicitly install `handbrake-gtk` for preview proof.
Discover executable names with `dpkg-query -L`, rather than assuming `/usr/bin/ghb`.

Generate two 64×64 Y4M frames with FFmpeg and run:

```sh
x265 --y4m --input input.y4m --output control.hevc --preset ultrafast --pools 1 --frame-threads 1
x265 --y4m --input input.y4m --output marked.hevc --preset ultrafast --pools 1 --frame-threads 1 --frame-packing 3
```

The first exited 0 and encoded two frames; the second exited 1 with an unrecognized-option message.
The installed library's `x265_param_parse` accepted `frame-threads=1` (0) and rejected `frame-packing=3` (−1).
Its version banner reported 4.0 despite the package version above; preserve both facts.
`x265 --fullhelp` also exits 1 on this build, so capture its status without treating it as a failed encode.

Inspect HandBrake's ELF `NEEDED` entries, Depends and the source returned by `apt-get source handbrake`.
The source is `handbrake-dmo`, whose packaging updates an included FFmpeg to 8.0.3.
The installed executables have no dynamic libavcodec or libx265 dependency.
Installing a newer system library alone therefore does not establish which encoder or decoder HandBrake uses.
Daniel's 2026-11-19 decision requires shared edition libraries: “handbreak should use our libraries, not be a snap like or flatpack like thing - if needed, fork a stereo handbreak instead”. Build the Sparky-OS/HandBrake fork on 1.11.2, adapt Debian's shared-library packaging without its ambient-viewing and Dolby Vision removal patches, and retain DMO's three binary names and encoder features. Audit HandBrake's contrib patches against each system library and carry missing library features into that library's edition package. Rerun the marked-source matrix: the Debian study does not qualify the deb-multimedia candidate.

Recheck upstream records through the project's own repository:

- [x265 commit 1cf669dfd8a4917a08f381012fd659a0869251d3](https://github.com/Multicorewareinc/x265/commit/1cf669dfd8a4917a08f381012fd659a0869251d3), by Daniel Campos Ramos, adds the option and the `framePacking` member, with X265_BUILD raised to 218.
  [PR #986](https://github.com/Multicorewareinc/x265/pull/986) merged on 2026-10-22; issue #970 closed on 2026-10-28.
  [PR #999](https://github.com/Multicorewareinc/x265/pull/999) concerns `--field`, its b-adapt restriction and tests, not the intra-refresh frame-packing fix; the latter is a commit within #986.
- HandBrake master remained at 28cae12c062ff68c6851fed5621fdbd56ca00cb7 on 2026-11-19.
  [Issue #5826](https://github.com/HandBrake/HandBrake/issues/5826) is titled “CALF Cam video stripped of 3D metadata” and is closed; it is not an open umbrella request dating to 2013.
  The frame-packing PR search returned #8100 only; that search does not establish an absence beyond its query.

Package preservation, the x265 mapping, SEI-only scan and stereo preview remain separate build and runtime proofs after this reconciliation.


## Shared-library working steps (ORDER 742)

The edition x265 successor imports PR #986's three merged commits (1cf669dfd8a4917a08f381012fd659a0869251d3, 143a263b2ee74866af04783f814bd1245d5a5413, 5143a2a00ad0cc600831654a248b96ec7307eb4a), plus HandBrake's ambient-viewing, Dolby RPU and other library fixes. The extra ambient API uses a separate SONAME; retain the old library for existing consumers and rebuild FFmpeg and HandBrake against the new development package. Check each actual bit depth, not only the default API.

Measured at this working step: nine of nine x265 encodes (arrangements 3, 4 and 5 at 8, 10 and 12 bits) decoded with their expected AVStereo3D type. Both the x265 and x264 successor package sets passed the edition's archive-qualified link gate and release checks. This does not yet qualify HandBrake's output or the preview.

A decoded-frame `ffprobe -show_frames` side-data entry may name Stereo 3D without printing its type. For an exact arrangement readback, decode independently with libavcodec and inspect AVStereo3D; the lane's read-stereo-frames.c does that. Presence alone is not proof of the right arrangement.
