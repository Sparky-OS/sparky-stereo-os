# Stereo files that open anywhere, and how each mark is written and read back (ORDER 644, 2026-11-17)

A stereo sample for another project's test repository has to pass that project's own measure first: it is an ordinary JPEG, PNG, MP4, MKV or WebM that opens as a picture or a film with default programs on any system.
A stereo-aware system shows depth as an extra, read from the format's own mark.
Nothing is red-cyan (the desktop's outputs make anaglyph when a screen needs it), and every file carries its mark, written by a writer that keeps it and read back by a parser that can fail.

## Working recipe

1. Source: real stereo pictures and films with a stated free licence (a CC0 photographer, NASA and other US federal pairs, a scan of a nineteenth-century stereo card, an open film's stereoscopic release). Wikimedia Commons' search finds them with `stereo pair` and a licence word; Flickr-reviewed CC0 pairs are marked on the file page.
2. Decide the eye order by measurement, not by the file name or the caption: [eye_order.py](../scripts/eye_order.py) matches a near block and a far block between the two halves; the nearer object has the larger `x_left - x_right`. Commons descriptions say "cross-eyed" when the right eye looks at the left picture, and that pair has to be swapped before packing.
3. Cut each eye on its own box (no card borders, no stray margins), the same size for both, and keep the pixels: `jpegtran -copy all -crop WxH+X+Y` cuts a JPEG without recompression when X, Y and the size sit on the MCU grid (16 px for 4:2:0) and keeps the EXIF.
4. Pack with the format's own mark, the writers in [scripts/](../scripts/) and [stereo-video/scripts/stereo-marks](../../stereo-video/scripts/stereo-marks/):
   - **MPO** (CIPA DC-007): `stereo_pack.py mpo LEFT.jpg RIGHT.jpg OUT.mpo`. First picture carries an APP2 `MPF` with the index (version 0100, two images, MP entries of type `0x020002` disparity, the first flagged representative) and an attribute IFD (B101 viewpoint 1, B204 base viewpoint 1); the second carries only its attribute IFD (B101 viewpoint 2). The second entry's offset counts from the MPF header (the byte order mark), not from the start of the file. This is the two-view layout stereo-layer's reader accepts (`src/policy/stereo-jpeg.c` in Sparky-OS/stereo-layer).
   - **JPS**: `stereo_pack.py jps SBS.jpg OUT.jps` inserts an APP3 `_JPSJPS_` block after the leading APPn run: 16-bit length 4, the descriptor `0x00040201` (type 1 stereo, layout 2 side by side, flag bit 18 left eye first, no half-size flags, no gap) and a zero comment length. VRex's General Purpose Stereoscopic Data Descriptor (1997) is the specification.
   - **PNS**: `stereo_pack.py pns SBS.png OUT.pns` inserts the registered `sTER` chunk (PNG Extensions 1.4.0, 3.6) right after `IHDR`, one byte, mode 1 (left eye on the left). The picture is the pair side by side with a width divisible by 16 and each eye's width divisible by 8, so the right view starts on a column multiple of 8.
   - **MP4**: encode the side-by-side frame with `x264 frame-packing=3` (H.264 frame packing arrangement SEI type 3, content interpretation 1) and add the `st3d` box with `stereo-marks/mp4_st3d.py IN OUT 2` (stereo_mode 2 is left-right, left eye on the left; the RFC at github.com/google/spatial-media, docs/spherical-video-v2-rfc.md). The box goes after the codec configuration box and before the optional `pasp` and `clap`; the parents' sizes grow by 13 bytes and, when `moov` precedes `mdat`, every `stco` entry shifts by 13.
   - **Matroska and WebM**: `mkvmerge -o OUT.mkv --stereo-mode 0:1 IN` writes `StereoMode` 1 (side by side, left eye first); `--webm` writes DocType `webm`, whose subset allows 0 to 3. mkvmerge also derives the value from the H.264 SEI, so set it explicitly anyway and read it back.
5. Read each mark back with a parser other than the writer, and keep the output (`evidence/stereo-readback.txt`):
   - MPO: `exiftool -G1 -a -MPF:all` (type "Multi-frame Disparity", image starts, `MPIndividualNum`, `BaseViewpointNum`); Pillow `Image.open(file).n_frames == 2` with each frame equal to the cut eye; stereo-layer's own C reader compiled from its sources in a scratch folder (`stereo_jpeg_inspect` returns layout 5, `right_first` 0) and the unmarked control returning layout -1.
   - JPS: the same reader returns layout 2, `right_first` 0, descriptor `0x00040201`; [stereo_verify.py jps](../scripts/stereo_verify.py) checks the one APP3 and its lengths.
   - PNS: [stereo_verify.py pns](../scripts/stereo_verify.py) checks `IHDR sTER IDAT... IEND`, every CRC, the mode byte and the width.
   - MP4: `mp4_st3d.py verify` (the box, its mode, the sibling order), `ffprobe -show_entries stream_side_data` ("Stereo 3D, side by side" comes from `st3d`), `ffprobe -show_frames -show_entries frame=side_data_list` (the first frame's "Stereo 3D" comes from the SEI), and the decoded video and audio MD5 equal to the copy without `st3d` (`ffmpeg -map 0:v -f md5 -`).
   - Matroska and WebM: `ebml_probe.py` (DocType, CodecID, `StereoMode`, pixel and display size), `mkvinfo`.

## What a plain viewer shows

- MPO: the first picture, the left eye, as an ordinary JPEG (Pillow, Dolphin and any viewer without MPF support). A stereo-aware viewer pairs the two.
- JPS: the whole pair side by side as one wide JPEG.
- PNS: the pair side by side as one PNG.
- MP4, MKV and WebM: a film whose picture is the pair side by side (2560x720 here, 32:9); sound and timing are ordinary.

## Traps: symptom, cause, fix, how it was found

- **Symptom:** a Commons stereo pair packed left-first shows reversed depth.
  **Cause:** the file was a cross-eyed pair (the description says "your right eye shall look at the left image"). **Fix:** swap the cut eyes before packing. **Found by:** `eye_order.py`: near minus far was -7 px with the file's left half as A, and the Commons description said cross-eyed.
- **Symptom:** the sign of one block's disparity gave the wrong order on a film frame.
  **Cause:** the zero-parallax plane lay behind the nearest object, so the far sky had a large negative `d` and a block that straddled the tree gave a small one. **Fix:** compare a near block with a far block; never read the sign of one block. **Found by:** six blocks on one frame: leaves +38, bird 2, sky -35.
- **Symptom:** Pillow's "malformed MPO file" warning on a file `exiftool` reads fine.
  **Cause:** it is raised when the second picture alone is opened (no index there). **Fix:** open the whole file and seek. See [sample files for another project's test repository](../../upstream-outreach/references/sample-files-for-another-projects-test-repository.md).
- **Symptom:** `st3d` sits after `pasp` and `btrt` in the sample entry.
  **Cause:** the first insert appended it at the end of the entry. **Fix:** insert before the first optional box (`clap` or `pasp`); the RFC's "must come after non-optional boxes ... and before optional boxes at the end". **Found by:** printing the entry's children in order after writing.
- **Symptom:** a ranged download of an open film ends with "Invalid NAL unit size ... partial file" and the cut is shorter than asked.
  **Cause:** `-ss` plus `-t` ran past the downloaded bytes. **Fix:** with `moov` at the start (`+faststart`) a `Range: bytes=0-N` head decodes up to its end; fetch enough (N = bitrate times the cut's end time, plus slack) and check the output duration.
- **Symptom:** an over-under release (`abl`, left eye on top) has 1920x2160 frames.
  **Cause:** each eye is 1920x1080. **Fix:** crop top and bottom, scale each eye on its own (1280x720 here, one resize), `hstack` the left eye first. A resize of the whole packed frame mixes the eyes at the seam.
- **Symptom:** `mkvmerge --webm` output reports container "Matroska" in `mkvmerge -J`.
  **Cause:** the JSON names the family. **Fix:** read the EBML DocType (`webm`) with `ebml_probe.py`.
