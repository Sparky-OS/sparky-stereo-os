# Metadata precedence and per-eye geometry

Daniel reaffirmed these existing decisions on 20 October 2026.
Apply them before proposing another stereo detector.

## Read the declarations first

Keep an explicit user override separate from automatic classification.
The edition's automatic order is applicable codec frame-packing SEI, container stereo metadata, descriptive tags, then image/shape detection.
A valid SEI arrangement wins over a conflicting Matroska `StereoMode` or MP4 `st3d` arrangement.
Container fields can still supply complementary display geometry; precedence does not mean discarding every field from a lower-priority source.
Keep the value's origin and validity beside it.

The decoder owns SEI lifetime, cancellation and coded-sequence boundaries.
Do not replace that behavior with a player indefinitely remembering the first stereo frame.
An explicit mono declaration is different from missing metadata.
The existing FFmpeg work covers [frame-packing persistence](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24628) and [side-data preference with a conflicting container](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24643).
Inspect its actual source and tests before implementing the same behavior elsewhere; a linked submission is not evidence of upstream acceptance or of the decoder version installed.

## Full and half describe packing relative to one eye

Full packing doubles one dimension relative to the intended one-eye picture.
Half packing fits both views into that picture's ordinary 2D frame dimensions.

For a square-pixel 1920×1080 picture per eye:

| Layout | Full packed frame | Half packed frame |
| --- | --- | --- |
| Side by side | 3840×1080 | 1920×1080 |
| Top and bottom | 1920×2160 | 1920×1080 |

This is a relationship, not a requirement that every source be 1080p or 16:9.
Read the actual geometry, crop, sample aspect ratio and display units for the source.
[RFC 9559 §18.10](https://www.rfc-editor.org/rfc/rfc9559.html#section-18.10) defines Matroska `PixelWidth`/`PixelHeight` as the stored combined picture and pixel-unit `DisplayWidth`/`DisplayHeight` as one plane's display size.
For codec signalling, interpret the frame-packing arrangement together with the stream's sample aspect and the applicable codec's aspect semantics; a layout enum alone is not a dimension field.
See the frame-packing semantics in [ITU-T H.264](https://www.itu.int/rec/T-REC-H.264) and [ITU-T H.265](https://www.itu.int/rec/T-REC-H.265), naming the edition when citing a clause.

Use valid supplied geometry directly.
Do not replace it with a guessed aspect threshold, and do not reject the ordinary metadata-driven path merely because unmarked files also exist.
When metadata is absent, defaulted, contradictory or lost by an API, identify that condition and the boundary where it occurs before choosing a fallback.
Demuxers may fold display dimensions into sample aspect; applying that expansion twice squeezes or stretches the eyes.
Verify the resulting eye geometry, not only the text label “half” or “full”.

## Reuse the policy, verify the inputs

The shared stereo policy already has video layout, view geometry, Matroska plane recovery, filename-tag and halves-comparison functions.
Find the versions used by the target application and its existing test vectors.
A Java or C++ mirror can contain the right formula while its caller supplies placeholder SAR, zero plane dimensions or an unknown aspect flag.
Trace actual values from the file reader through the policy call to the filter arguments and output pixels.
Record separately what is decided, implemented, exercised and shipped.

## Detection is the fallback

For missing metadata, comparing corresponding regions of the two candidate halves can help distinguish SBS from TAB.
A single pixel or one 5×5 patch cannot establish stereo: black borders, flat areas and repeated textures can match by accident.
Use multiple textured regions, tolerate stereo disparity and compression differences, and test ordinary 2D counterexamples.
Stereo correspondence is normally displaced horizontally even when the views are packed top and bottom.
Similarity identifies a possible pair; squeezing both views preserves their similarity, so it does not independently establish their intended display aspect.
Use the existing detector and its confidence/unknown result before considering a new implementation.
Keep the user able to correct layout, eye order and 2D/stereo interpretation.

## Proof that distinguishes the cases

Use correctly authored full and half SBS/TAB fixtures with explicit per-eye display geometry, then counterparts with those fields absent.
Check what the actual metadata API reports; a wrongly authored fixture must be corrected, not used to justify changing correct reader behavior.
Include conflicting SEI/container marks, explicit mono, keyframe-only SEI, cancellation and a 3D-to-2D transition where that decoder path changes.
Verify decoded eye dimensions/aspect, order and time alignment, plus ordinary 2D and a non-16:9 source.
Retain a failing control for each changed behavior.
Do not claim metadata extraction from tests that inject geometry directly into a policy function.
