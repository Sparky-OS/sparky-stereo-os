# The shape of an eye in a Matroska pair

A side-by-side or top-and-bottom Matroska track says how wide its picture is shown with `DisplayWidth` and `DisplayHeight`.
Whether that size is the whole frame or one eye decides whether an eye is shown at its shape or as a strip twice too wide (or a picture squeezed to half its height).
This page has the clauses, what each writer and reader does, the rule the edition applies (ORDER 577, agreed by Daniel on 2026-11-15), the fixture that measures it and the traps met.

## What the specification says

[RFC 9559](https://www.rfc-editor.org/rfc/rfc9559) gives two answers that do not agree:

- Section 18.10, "Multi-planar and 3D Videos": "The pixel count of the track (PixelWidth/PixelHeight) is the raw number of pixels (for example, 3840x1080 for full HD side by side), and the DisplayWidth/DisplayHeight in pixels is the number of pixels for one plane (1920x1080 for that full HD stream)."
  The section has no MUST or SHOULD; it describes.
- Sections 5.1.4.1.28.12 and .13 (`DisplayWidth`, `DisplayHeight`): "Width of the video frames to display. Applies to the video frame after cropping", and, when `DisplayUnit` is 0, "the default value for DisplayWidth is equal to PixelWidth - PixelCropLeft - PixelCropRight".
  So a track that gives no display size declares the whole frame, which section 18.10 would read as one plane: a full side-by-side file without the elements is two eyes of 32:9.
- Section 5.1.4.1.28.14, `DisplayUnit`: 0 pixels, 1 centimeters, 2 inches, 3 display aspect ratio, 4 unknown; for units 1 to 3 the two elements have no default, for every unit only their ratio is a shape.
- StereoMode (5.1.4.1.28.3, Table 5): 1 and 11 side by side, 3 and 2 top and bottom (left first, right first), 9 and 8 column interleaved, 7 and 6 row interleaved, 5 and 4 checkerboard, 10 and 12 anaglyph, 13 and 14 both eyes laced in one block; IANA's registry adds 15 to 20, picture and depth.

For comparison, ISO/IEC 14496-12:2026 13.5.4 (StereoVideoBox) is unambiguous: "width and height document the pixel counts of a frame-packed picture" and "the PixelAspectRatioBox documents the pixel aspect ratio of each view", typically "2:1 or 1:2" for spatial packings; and H.264 V16 D.2.26 NOTE 2 makes a codec's sample aspect ratio the packed frame's (see [metadata and geometry](metadata-and-geometry.md)).

## What writers write

- **FFmpeg's muxer** (`matroskaenc.c`, Michael Niedermayer 2013, James Almer 2016) writes one plane: DisplayWidth = width × SAR / 2 for side by side and columns, DisplayHeight = height / 2 for top and bottom and rows.
- **mkvmerge** writes the whole frame unless `--display-dimensions` says otherwise (MKVToolNix 103.0: `--stereo-mode 0:1` on a 2560x720 track writes DisplayWidth 2560).
- **BD3D2MK3D** and the films people own follow mkvmerge: jellyfin#11355 (2024, closed "not planned") is a 3840x1080 full side-by-side file shown as 64:9.
- **The edition's own writer** (stereo-layer's `stereo_mark_save_views`) writes one plane, as section 18.10 says.

The films of ORDER 577, read with `mkvmerge -J`: Broken.mkv pixels 2560x720, display 2560x720 (two whole 1280x720 eyes); Coyote Falls.mkv 1920x540, display 1920x544; a half side-by-side film 1920x1080, display 1920x1080; Knights Quest.mkv 854x480, display 1707x480 (its own 2:1).

## The rule (ORDER 577)

Daniel, 2026-11-15, "I agree" to: double only when an eye, at the file's own declared shape, is narrower than 4:3 (a squeezed half); otherwise keep the declared shape. The same for top and bottom.

Read the declared size as the whole frame first, then:

| Packing | The eye at the declared shape | Read the size as one plane (double the stacked axis) when |
|---|---|---|
| Side by side, columns | (DisplayWidth / 2) : DisplayHeight | that is narrower than 4:3, i.e. DisplayWidth : DisplayHeight < 8:3 |
| Top and bottom, rows | DisplayWidth : (DisplayHeight / 2) | that is 8:3 or wider, i.e. DisplayWidth : DisplayHeight ≥ 4:3 |

Why 8:3 is "the same" for top and bottom: call r the real shape of an eye.
A writer that follows section 18.10 declares r for the plane; one that writes the whole frame declares r × 2 side by side and r / 2 stacked.
Side by side, the rule reads both writers right exactly when 4:3 ≤ r < 8:3 (a one-plane size gives an eye of r / 2 < 4:3 and is doubled; a whole-frame size gives r ≥ 4:3 and is kept).
Stacked, the threshold that gives the same band is 8:3 on the eye at the declared shape: a one-plane size gives an eye of 2r ≥ 8:3 and is doubled, a whole-frame size gives r < 8:3 and is kept.
4:3 is the narrowest ordinary picture, and twice it the widest the rule takes as whole: every film shape from 4:3 to 2.39:1 and 2.55:1 is inside the band, for both writers and both packings.
Outside it: an eye of 8:3 or wider written as one plane (Ultra Panavision's 2.76:1 by FFmpeg's muxer) is read at half its width, and a portrait eye narrower than 4:3 written as the whole frame (a phone held upright) is read twice as wide.

The rule decides only the shape an eye is shown at: no sample is resized in the reader (the program hands its views at their resolution, Stereo KWin resizes once).
It is not a detector: the StereoMode says the file is stereo and is never second-guessed; the rule reads the one field the specification leaves ambiguous.
A packing the person stored for the file (the shared per-file store) still comes first, as it did.

Values with no stacked axis keep no multiplier, before and after: checkerboard (each eye has half the samples over the whole frame), anaglyph (one picture), both eyes in one block (each frame is a whole view).
FFmpeg 9.0.2 reads StereoMode 15 to 20 as no packing, so the rule does not reach them there.
`DisplayUnit` 4 (unknown): FFmpeg takes no sample aspect ratio from the container, before and after, and the codec's applies.

## Where the edition applies it

- **FFmpeg** (`libavformat/matroskadec.c`, `mkv_stereo_mode_display_mul()`, ffmpeg-dmo +stereo3d14, patches 0074 and 0075): the multiplier Aaron Colwell added in 2015 (ec83efd4d3, "matroskaenc.c applies divisors to the display width/height when generating stereo content. This patch adds the corresponding multipliers"), now applied only by the rule. Every program that takes FFmpeg's stream sample aspect ratio follows: Qt Multimedia (Dragon Player, Plank Player, Bino), sView, MLT, the Dolphin thumbnailer through stereo-layer's `matroskaPlane()`.
- **mpv** reads Matroska with its own demuxer: `demux/demux_mkv.c` (mpv-dmo +stereo3d10, patch 0061) applies the same rule and hands its filters the shape one view is shown at; before, patch 0040 doubled every display size that differed from the frame and the filters took that size as one view. Haruna and PlasmaTube use the same engine.
- **stereo-layer** (1.21.1): `stereo_policy_matroska_one_plane()` is the rule, and `stereo_policy_video_views()` takes a given size that is the whole frame of two whole pictures as full views; before, a size with the frame's shape counted as one plane, so half views. VLC Stereo reads Matroska with its own demuxer, folds the size into its sample aspect ratio as the whole frame and asks this function, so it needs no patch of its own. `stereo_policy_matroska_plane()` (for players that read FFmpeg's ratio) gives the shape one view is shown at under either FFmpeg.

## Measured (ORDER 577, 2026-11-15)

The circle of the left eye, published build first, then the edition's FFmpeg +stereo3d14, mpv +stereo3d10 and stereo-layer 1.21.1 (1.00 is right; both eye orders and the right eye read the same):

| Reader | 2560x720 as 2560x720 | 854x480 as 1707x480 | 1920x540 as 1920x544 | 1280x1440 as 1280x1440 | 854x480 as 854x960 | 960x1080 as 960x1088 | half 1920x1080, one plane 2560x720 as 1280x720, 2D |
|---|---|---|---|---|---|---|---|
| FFmpeg (its SAR) | 2.00 → 1.00 | 2.00 → 1.00 | 2.00 → 1.00 | 0.50 → 1.00 | 0.50 → 1.00 | 0.50 → 1.00 | 1.00, pixel-identical |
| Dragon Player, Plank Player, Bino | 2.00 → 1.00 | 2.00 → 1.00 | 2.00 → 1.00 | 0.50 → 1.00 | 0.50 → 1.00 | 0.50 → 1.00 | 1.00 |
| Dolphin's thumbnail | 2.05 → 1.00 | 2.05 → 1.00 | 2.07 → 1.00 | 0.50 → 1.01 | 0.50 → 1.01 | 0.50 → 1.00 | 1.00 |
| mpv | 1.00 → 1.00 | 2.00 → 1.00 | 2.00 → 1.00 | 1.00 → 1.00 | 0.50 → 1.00 | 0.50 → 1.00 | 1.00, pixel-identical |
| VLC Stereo | 1.00 → 1.00 | 1.00 → 1.00 | 2.00 → 1.00 | 1.00 → 1.00 | 1.00 → 1.00 | 0.50 → 1.00 | 1.00 |

Columns and rows follow the same axes in FFmpeg (2.00 and 0.50 to 1.00 for the full files); the thumbnailer's interleaved fault is below.
A packing stored for the file still wins: with "side by side, right eye first" stored for a left-first file, the thumbnail's left view turns blue, both views round.
Haruna, in the cases where its window showed the picture, reads as mpv: 854x480 as 1707x480 went from 1.99 to 1.00, 854x480 as 854x960 and 960x1080 as 960x1088 read 0.50 before; the other cases' windows were black in the rig.
sView is not measured: in the rig it sometimes showed another fixture than the one it was given.

## The fixture: a circle in each eye

`scripts/matroska-eye-shape/fixtures.py` draws each eye at the shape it is meant to be shown at (a white circle and a white square; the left eye's view on red, the right eye's on blue, a 2D picture on green), resizes it to the eye's coded size, packs it, encodes it losslessly (FFV1, 30 frames at 1 fps, so a player that stops at the end of a film is still showing it when captured) and muxes it with mkvmerge with the StereoMode and display size of each case, both eye orders.
Check every fixture with an independent reader before use: `mkvinfo` (the elements present or absent), `mkvmerge -J`, `mediainfo`.

Measure the circle's width over its height in the picture a reader shows (`measure.py`): 1.0 is right, 2.0 is a strip twice too wide, 0.5 a picture squeezed to half.
- FFmpeg's own reading: `probe-ffmpeg.py` takes ffprobe's sample aspect ratio, decodes the first frame at its coded size, cuts each eye by the fixture's packing and applies the ratio; and renders the left eye with ffmpeg itself (`crop`, then `scale=w='trunc(iw*sar/2)*2':h=ih,setsar=1`).
- A player: `rig-case.sh` starts a fresh Stereo KWin on a virtual output, the player on the fixture, captures both eyes through ScreenShot2, and `analyze-capture.py` finds each eye's picture by its colour and measures it.
- The Dolphin thumbnail: `thumb-driver` runs the ffmpegthumbs plug-in through KIO's `ThumbnailCreator` API, as the thumbnail worker does, and the same analysis measures each view.

## Traps

- **Symptom:** a fixture-based check says 2.0 for the half file too. **Cause:** none of the reader's; the fixture's eye was drawn at the coded size, not at its display shape. **Fix:** draw at the display shape, then resize to the coded size. **How found:** the half file must read 1.0 on the published build (the control).
- **Symptom:** mpv aborts in the rig: `vo_x11_init: Assertion '!vo->x11' failed`. **Cause:** on llvmpipe mpv's Wayland OpenGL context reports "Suspected software renderer" and falls through to an X11 context. **Fix:** `--gpu-sw`. **How found:** `mpv -v` in the rig session.
- **Symptom:** every ScreenShot2 capture fails with `Screenshot got cancelled`. **Cause:** no render node in the container, so KWin composites without OpenGL. **Fix:** give the render node and its group, and start the container as the user (`--user 1000:1000 --group-add GID`); `runuser` drops the group. **How found:** the proof-rig skill's lessons, then the session log's "Failed to open drm node".
- **Symptom:** Dragon Player's and Plank Player's windows are black at the capture although they declared a stereo surface. **Cause:** a 2-second fixture had ended; a Qt Multimedia player stops and clears its picture at the end. **Fix:** fixtures long enough to be playing at the capture (30 frames at 1 fps). **How found:** mpv (paused on its first frame) and Bino (holding its last) showed the same fixtures.
- **Symptom:** VLC Stereo says `no suitable interface module`. **Cause:** its default interface list does not reach Qt in a session without a desktop. **Fix:** `-I qt`. With `--start-paused` it then shows its cone and opens no video output: leave it playing.
- **Symptom:** sView prints `StSearchMonitors, X: could not open display`. **Cause:** it is an X11 program. **Fix:** `DISPLAY` of the session's Xwayland.
- **Symptom:** Bino's eye reads 1.48 while the picture is plainly a strip. **Cause:** the colour finder took the red pixels of Bino's window icon into the eye's box. **Fix:** keep only rows and columns that are mostly the background colour.
- **Symptom:** an interleaved fixture's eyes show no red or blue. **Cause:** in 4:2:0 each chroma sample covers both views, so their colours mix. **Fix:** measure the picture as any lit, non-white area and do not judge the eye order from colour there; use an RGB fixture for the order.
- **Symptom:** an out-of-tree FFmpeg build of deb-multimedia's source stops at `xfade-easing.h: No such file or directory`. **Cause:** `debian/rules` copies that header into `libavfilter/` before building. **Fix:** copy `debian/xfade-easing.h` into the source's `libavfilter/` (and exclude it from git).
- **Symptom:** a package build that links the edition's FFmpeg stops at the link gate with `predecessor failed archive-qualified resolution: /usr/bin/mpv: undefined av_multiview_real_to_double` after every package was built. **Cause:** `release/build-from-lc-dsc.sh` hands the gate no list of the published edition's files, so it resolves `libavutil61` from deb-multimedia, which versions it higher, and the published program's calls into the edition's FFmpeg look undefined. **Fix:** build such a source with `packages/depth-source/build.sh` and the published pool as the siblings list (`find pool -name '*.deb'` as `/repo/...`), `SPARKY_BINARY_ONLY=1`. **How found:** the gate's own line at the end of the build log, then build.sh's usage text, which names this case.
- **Symptom:** the new package's version is already taken: another lane's stage holds a different build with the same version (mpv-dmo 0.41.0-dmo9+stereo3d9+lc1, ORDER 346a, staged on 2026-11-02 and not yet published). **Cause:** the version was chosen from the published pool alone; a merged recipe whose stage waits for a round is invisible there. **Fix:** list every stage's descriptors before choosing (`find /mnt/build/*/stage -name 'SOURCE_*.dsc'`), make the new source from the newest one that is owed (its changelog and patches stay in), number the new patch after its last, and version above it (+stereo3d10 on 346a's +9). The link gate then needs one edition snapshot: give `depth-source/build.sh` the staged build as PREVIOUS_DIR and a siblings list without the package's published files (`grep -v '/pool/main/m/mpv-dmo/'`), or it stops at `previous edition dependency qualification failed ... conflicting supplied package: libmpv2; provide one authoritative edition snapshot`. **How found:** the hand-back's check that the version is above every staged one.
- **Symptom:** a staged package's build record names a recipe commit that is on no branch (`recipeCommit` 9873115b, while the branch ends at 38ec54e8). **Cause:** the package was built while that commit was the branch's head; amending the last commit afterwards (for another package of the same branch) replaced it, so the record points at a commit nobody can fetch and the published provenance could not be verified. **Fix:** amend or rebase before building, or rebuild every package whose record names the old head (a binary-only rebuild from the staged source is enough) and restage its record. **How found:** reading `recipeCommit` of every staged `.sparky-build.json` against the branch before the hand-back.
- **Symptom:** a staged source's descriptor differs from the one its producer made twice identically. **Cause:** `depth-source/build.sh` without `SPARKY_BINARY_ONLY=1` runs a full `dpkg-buildpackage`, which packs the source again with other directory times. **Fix:** `SPARKY_BINARY_ONLY=1`, and stage the producer's source. **How found:** `sha256sum` of the two descriptors.
- **Symptom:** Haruna's window is black at the capture while it declared its video. **Cause:** not found; the same engine on mpv's command line draws at once. **Fix:** count only cases whose eyes show their colour, and prove the engine with mpv.
- **Symptom:** sView's 2D control shows a red and blue pair, and a top-and-bottom case shows the 2D film's green. **Cause:** not found; sView sometimes shows another fixture of the same folder in a rig that runs many cases in one container. **Fix:** none yet: sView's rows are not proof until each case runs in a container of its own.
- **Symptom:** a Haruna or sView measurement reads 8.8 or 1.13 where the picture is plainly round. **Cause:** the player's own controls (a play bar, a time) are white and fell into the shape's box. **Fix:** measure only the connected white shape grown from the longest white run (`measure.py`).
- **Symptom:** interleaved Matroska thumbnails are twice too wide (columns) or squeezed to half (rows), before and after the rule; before it, a full interleaved file's thumbnail was four times off (3.91 and 0.25). **Cause:** the thumbnailer takes interleaved views apart at the frame's size (each view stretched back to the frame, the codec SAR's reading) and then also applies FFmpeg's Matroska SAR, which for rows and columns already describes one view. **Fix:** not built in ORDER 577: for a Matroska track with rows or columns, give each compacted view the stream's SAR as side by side does. **How found:** `thumb-driver` on the column and row fixtures; FFmpeg's own reading of the same fixtures is right.
