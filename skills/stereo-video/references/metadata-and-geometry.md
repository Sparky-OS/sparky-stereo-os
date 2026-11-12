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

A codec SAR and a container SAR mean different things for a packed frame: H.264 V16 D.2.26 NOTE 2 gives the packed frame's shape, which each upconverted view keeps, while Matroska's plane size (RFC 9559 §18.10) and ISO/IEC 14496-12 13.5.4.1's PixelAspectRatioBox give each view's.
FFmpeg folds a stereo Matroska track's plane size into the stream SAR, so that SAR is per view; a half-format stretch applied to it doubles the view. Decide which one a stream has from its declaration (the container and its StereoMode), never from the frame's shape ([lessons](lessons-2026-11.md)).

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

## A site's mark: YouTube's yt3d keywords

A video site can say how its videos hold their views outside the file: YouTube took the layout of a 3D upload from the video's keywords (tags) before 2011, and such tags remain on videos from then (verified 2026-11-05 with the watch pages of "Kate in 3D!", XTt_HGmTxf4, and "3D Maestro", uMTvaNomlWY, whose `<meta name="keywords">` carries them; Invidious and Piped hand the keywords on).
It is a convention of one site, never a web standard (the web has no mark for a video's layout outside WebXR), so it ranks as a **site mark**: the user's choice first, then the stream's and the container's marks, then the site's mark, then the file name's tag and the shape rule.
A video with no mark at all stays flat when the shape does not say two views, and the person's menu covers it.

**One reader, no copies.** `stereo_policy_site_mark()` and `stereo_policy_site_mark_list()` in libstereo-policy (stereo-layer 1.13, `docs/yt3d.md`) read every form, for the browser and for PlasmaTube alike; a program that shows YouTube videos calls it and keeps no table of the tags.
Every form, as the reader takes it (case, spaces and quotes do not matter; a malformed number is read as far as it can be, as in "Kate in 3D!", `yt3d:left=0_0._0.5_1`):

| Tag | Meaning |
| --- | --- |
| `yt3d:enable=LR`, `RL` | side by side, the left eye's view on the left (YouTube's recommended format) or the right eye's |
| `yt3d:enable=LonR`, `RonL` | top and bottom, the left eye on top or the right eye on top |
| `yt3d:enable=true` (1, yes, on) | the first form: what `yt3d:left` and `yt3d:right` place, else side by side with the **right eye first**: YouTube's player took such a video for cross-eyed |
| `yt3d:enable=false` (0, no, off) | the site says the video is not 3D |
| `yt3d:swap=true` (1, yes, on, or the bare tag) | the eyes the other way round, whatever else decided; with `enable=true` the left eye is first (parallel). "The yt3d:swap tag was still necessary to get the player to recognize the left eye frame was on the left" (stereo3dchannel.blogspot.com, 2011-02-21); Tim Dashwood, dvinfo.net: "if your video is in parallel format just add the tag yt3d:swap=true" |
| `yt3d:left=l_t_r_b`, `yt3d:right=l_t_r_b` | the rectangle of each eye as the left, top, right and bottom fractions of the frame; the two halves, side by side or one above the other, either way round, are the arrangements of the policy, any other rectangle gives no mark and the program says so (return value 2) |
| `yt3d:aspect=W:H` (W/H, a number such as 1.78) | the shape of one view as the site shows it: the plane size of the full or half rule above (a frame of that shape holds half views, one twice as wide or as tall full views) |

An explicit `enable=LR|RL|LonR|RonL` wins over rectangles, rectangles over the first form's side by side; `swap`, `aspect` or an unknown `enable` value alone carry no arrangement.
The order of the first form is measured, not only quoted: on "3D Maestro" (`enable=true`, `swap=true`) and "Kate in 3D!" (rectangles) the left half of the frame holds the left eye's view (a ground-plane and near-object disparity test, `eye-order.py` of the waterfox-stereo lane); PlasmaTube's first patch had the first form left eye first and `swap` right eye first, the reverse of this, and the shared reader corrects it.
Test it with a page that carries the keywords around an unmarked stream (`<meta name="keywords">` in the page, nothing in the stream or the container), one case per form, the marked-stream control with conflicting keywords (the stream's mark wins), the user's choice over the keywords, and a 2D video with ordinary keywords that stays flat; LEFT and RIGHT captures show the left eye's half in the left eye.

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
