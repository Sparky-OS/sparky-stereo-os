# Proving an animated stereo icon in Plasma

Use this when a theme icon stays on its first frame, either eye gets a frame ahead, or a reader returns deep colour that the Qt Quick item reduces.
The reference was checked on Plasma 6.7.4, Qt 6.11.2 and KImageFormats 6.30.0 in the edition's r1118a packages, against Debian snapshot 20261119T023717Z.
The published packages and the staged Frameworks 6.32 icon engine have different dependency closures.

## Identify the icon route

1. Read the applet's QML and the package that installs it.
   Weather Report uses `Kirigami.Icon` in its compact, current condition and forecast items. The panel adds the `-symbolic` suffix.
   Advanced Weather Widget 1.9.0 uses `Kirigami.Icon` for a theme name, Qt Quick `Image` for a bundled SVG, and `Text` for a weather-font glyph.
2. Test a **theme name** and a **file URL** as separate rows.
   KIconThemes 6.30.0 `src/kiconloader.cpp:716–745,876–878` reads one image and resolves the usual PNG, SVG, SVGZ and XPM extensions. Its old `loadMovie` and `loadAnimated` paths were deprecated in Frameworks 6.5.
   Kirigami's `animated` property controls transitions between icon images. [KIconThemes deprecation](https://github.com/KDE/kiconthemes/commit/2d922281eedc135db0c7ddefdc7349110433930f), [Kirigami !1645](https://invent.kde.org/frameworks/kirigami/-/merge_requests/1645)
3. Test `Image` and `AnimatedImage` for all three formats, and `VectorImage` for SVG.
   `VectorImage` makes Qt Quick nodes from the SVG and exposes a pause and repeat count. Qt 6.11 supports transform, colour, opacity and offset-path animation. See the documented feature table before using another property. [Qt 6.11 vector image formats](https://doc.qt.io/qt-6.11/topics-vectorimageformats.html)

## Make the fixture and measure the reader

Make two equal views on one source canvas, with opposite marker colours and matching marker positions on one timeline. Put a translucent gradient below the markers.
Use one SVG document with the SVGStereo 0.4 layout and a repeating `animateTransform`.
For the raster files, feed twelve whole left-first packed frames at 100 ms each to libjxl and libavif.
Use 16-bit RGBA and an open loop in JPEG XL. Use 12-bit AV1 YUV 4:4:4 with an alpha sequence and an open loop in AVIF.
Read all twelve images, delays, loop count, format and alpha through QImageReader. Read one QMovie frame and compare its format.
Read the marks separately. The JPEG XL draft uses an XMP property in the standard XML box. [Metadata rewrite checks](stereo-icon-models.md#verify-a-metadata-rewrite) explain how the carrier was chosen. The timed AVIF experiment uses the ISOBMFF stereoscopic-video advisory scheme.
The HEIF `ster` entity group pairs two still image items by their IDs; its members cannot be timed tracks. [SVGStereo 0.4](https://github.com/Sparky-OS/svgstereo/blob/66a673d/README.md#animated-drawings), [AVIF v1.2.0 §§3, 4.1, 5.2](https://aomedia.org/docs/AV1%20Image%20File%20Format%20%28AVIF%29%20v1.2.0.pdf), [ISO/IEC 14496-12:2026 §13.5.4.2](https://webstore.iec.ch/en/publication/113218)

## Read the whole path

| Format | Ordinary icon and Image | Animation item | Precision measured on the tested path |
|---|---|---|---|
| SVG | The theme name and file URL show one image. Image and AnimatedImage retain a still. | VectorImage changes at the virtual output's refresh rate. | The SVG image plugin returns ARGB32 premultiplied. VectorImage builds a scene of primitives, so it has no single input image texture. The grab returned RGBA8888 premultiplied. |
| JPEG XL | The file URL and Image show one image. The theme extension lookup rejects the name. | AnimatedImage advances the 100 ms frames at about 10 fps. | QImageReader returns RGBA64 with alpha for the 16-bit source. QMovie returns ARGB32 premultiplied and the QRhi texture is BGRA8 with alpha. |
| AVIF | The file URL and Image show one image. The theme extension lookup rejects the name. | AnimatedImage advances the unmarked 100 ms frames at about 10 fps. The native advisory packing control does not preserve the full samples. | QImageReader returns RGBA64 with alpha for the 12-bit source. QMovie returns ARGB32 premultiplied and the QRhi texture is BGRA8 with alpha. |

Read the QImageReader format, the QMovie image, and the Qt Quick image item's texture format and alpha on the render thread.
A window grab is an independent readback; it cannot establish the precision of an upstream decoder or a physical display link.
Measure process CPU time after warm-up and divide by measured wall time. Record the peak resident size and the host load alongside each row.
Use three fresh sessions at 22, 48, 64 and 256 px per eye.
A changing frame count comes from the movie or scene, and the captured pixels establish that the content moved.
A temporary fixture applet can run the same item types in plasmashell. Use three item grabs to confirm that both the still and animated routes behave the same there.

## Keep the two times equal

Use one animation instance for the packed fixture. Declare one full side-by-side surface through libstereo-declare. For a stable theme pair this declaration belongs to the flow described in [themed icons per eye](themed-icons-per-eye.md).
Set the virtual Stereo KWin output to the 1920×1080 SBS mode. See the [dated rig recipe](../../stereo-proof-rig/references/dated-snapshot-rig.md).
For each of three moments, wait for the probe's declaration and a rendered buffer, then capture with ScreenShot2.
Split the 3840×1080 result into two 1920×1080 views. Find the left colour only in the left eye and the right colour only in the right eye, and match the marker's position across eyes.
Require three different positions to catch a stuck frame. Store the SBS capture with PNG Extensions 1.4 §3.6 `sTER` mode 1 and verify the mark before review.
A surface-level proof on a probe establishes compositor eye selection and synchronization for that route. The theme-driven applet proof needs the staged engine and a real pair in its theme.

## Check the installed theme route before changing the engine

On r1123a, Weather Report uses `Kirigami.Icon` in its compact, temperature-and-icon, top and forecast components. Its panel condition name has the `-symbolic` suffix. KIconThemes 6.32.0-1+stereo3d1 has a separate `KIconLoader::loadStereoIcon()` for explicit callers. Normal lookup still reads one image. A directory named by `X-StereoDirectories` is not evidence that a program asks for the pair.

To check an installed stack, start a real plasmashell on Stereo KWin's 1920 × 1080 virtual SBS output. Make a test theme with a marked pair whose eyes have two disjoint marker colours. Provide the left view under the same name in the theme's normal directory. Put a Kirigami icon with that name on the test desktop, capture with ScreenShot2 and check the two halves. First run the same classifier on the known packed pair. In the r1123a control the known picture gave 2,210 marker pixels of the expected colour in each eye. The shell gave 2,210 left-colour pixels in each eye. Keep both the marked capture and the package versions.

The PNG `sTER` padding for an eye of width `w` is `(-w) % 8` pixels between the views (PNG Extensions v1.4, §3.6). For a 22 px eye the file is 46 px across. The layer removes the padding before passing the two 22 px views on. The output's own full SBS buffer does not carry that padding.

## Read an animated pair: one clock, one frame, a reason

A program never decodes the two views of an animated pair on its own, and never runs a timer per view.
The stereo layer's `Stereo::AnimatedPicture` (stereo-layer, `src/picture/animatedpicture.h`) opens the file once, takes the decision `Picture::load()` makes for it (the person's per-file choice, the file's mark, the shape) on the first frame, and keeps that decision for every frame.
The caller keeps one clock and calls `pairAt(msecs)`: both views come from the one frame shown at that time, decoded or drawn once.

1. **A raster** (JPEG XL, or any animated format the image readers know): every frame is read once through `QImageReader` with `setAutoTransform(true)`, with its delay from `nextImageDelay()` read after that frame. `frameCount()`, `delays()` and `loopCount()` are what the file declares; `loopCount()` follows `QImageReader` (-1 for ever, otherwise how many plays after the first, so JPEG XL `num_loops` 2 is 1). After the last play the last frame stays.
2. **A drawing** (SVG): one document loaded with Qt SVG's controlled animator (`QSvgDocument::load(..., QtSvg::AnimatorType::Controlled)`), set to the clock's time in milliseconds and drawn whole, both views in one drawing, then split. `frameCount()` is 0 and `duration()` is the document's.
3. **16 bits stay 16 bits.** The views are copies of the decoded frame: a 16-bit JPEG XL gives `QImage::Format_RGBA64` views with the file's sample values.
4. **A reason, never an empty picture.** No reader for the format, a frame that cannot be decoded, a timed AVIF with the ISOBMFF stereo video scheme: `pairAt()` returns a null picture and `reason()` gives a sentence the caller shows. A frame that cannot be decoded ends what is shown: no time after it is given a picture, and the animation does not wrap over the frames that did decode.
5. **The callers.** An icon engine keeps one `AnimatedPicture` per icon file, starts its clock on hover and asks `pairAt(elapsed, size)` for each repaint, drawing the left view in the left eye's pass and the right view in the right eye's; a Qt Quick item does the same from its own animation driver and uploads both views of the one frame before the scene is drawn.

Tests and fixtures: stereo-layer `autotests/animatedpicturetest.cpp`, `animatedpicturenoreadertest.cpp` and `autotests/readers/jxlstereo` (the generator writes the frames' green samples as 1000 times the frame number plus 1000, so a test reads the frame and the precision from one sample).

## Traps

- **Symptom:** a packed RGBA64 image fails an equality check against its unpacked eyes. **Cause:** Qt 6.11.2 `QImage::operator==` compares `QColorSpace` as well as format, size and samples. **Fix:** preserve the views' common colour space and copy the premultiplied 16-bit scanlines when packing the compositor buffer. Check both views against their native, premultiplied forms. **How found:** the same comparison failed even after a direct copy of the samples. The Qt equality implementation identified the additional comparison. [Qt 6.11.2 `qimage.cpp`](https://github.com/qt/qtbase/blob/v6.11.2/src/gui/image/qimage.cpp)
- **Symptom:** a full Moon has almost no visible relief after opening the phase. **Cause:** the crescent's lamp strength clips the newly lit face. **Fix:** keep the camera and geometry and test lower Moon-only lamp strengths. Measure a wide crop of the face in addition to the two small-icon panel contrast checks. **How found:** at 256 px the old lamp strength of 24 clipped 99.5% of a 50 × 50 interior crop even though the small contrast checks passed. Strength 4 clipped none in the same crop.

- **Symptom:** a JPEG XL pair is split across the wrong axis, or one view holds both colours. **Cause:** KImageFormats' JPEG XL reader keeps the orientation for the caller (`jxl.cpp`, `JxlDecoderSetKeepOrientation`) and reports it as `ImageTransformation`; `QImageReader` applies it only when `setAutoTransform(true)` is set or the plugin claims `TransformedByDefault`, which this one does not. **Fix:** set auto-transform before reading a JPEG XL, and take the even-width rule from the presented size (`reader.size()` transposed for a quarter turn). **How found:** a fixture stored 4 × 16 with orientation 6 came out as a 4-wide picture whose left half held red and blue.
- **Symptom:** an animation keeps looping smoothly although its file is cut short. **Cause:** a reader that cannot count the frames of a damaged file reports none, and a loop over the frames that did decode wraps over them as if the file were whole. **Fix:** a decode failure ends the timeline at the last good frame, and every later time gives no picture and the reason. **How found:** the fixture `animated-pair-truncated.jxl`, the same file without its last 40 bytes.
- **Symptom:** an unmarked SVG is not recognised as a drawing at all. **Cause:** the mark reader returns a null string both for "not an SVG" and for "an SVG without the attribute". **Fix:** ask whether the bytes start an SVG document (`isSvgDocument()`) apart from reading its layout.
- **Symptom:** a timed AVIF of a stereo pair shows one eye wide. **Cause:** libavif 1.4.2 takes the track header's per-view width as the output width and rescales the packed sample (see the AVIF trap below). **Fix:** until the reader keeps the packed samples, the layer refuses such a file before decoding, by the `stvi` scheme in its movie box, and says why.

- **Symptom:** a theme name resolves through `QIcon::hasThemeIcon()`, but the Kirigami item reports Error. **Cause:** Qt's explicitly set test theme and the KDE platform theme's configured theme can differ. **Fix:** select the isolated theme in `kdeglobals` and load the KDE platform theme. **How found:** Kirigami's reported status changed from Error to Ready and the fixture appeared.
- **Symptom:** both KImageFormats readers return RGBA64, yet the animated item uploads BGRA8. **Cause:** Qt's QMovie stores a QPixmap (`qtbase/src/gui/image/qmovie.cpp:370–377,399–405`) and the Qt Quick item takes its image (`qtdeclarative/src/quick/items/qquickanimatedimage.cpp:35–43`). **Fix:** preserve the frame as an image into a texture route that supports the desired format. **How found:** QImageReader reported RGBA64, QMovie reported ARGB32 premultiplied and the scene's QRhi texture reported BGRA8 with alpha. This is a path to qualify in the shared engine.
- **Symptom:** the first ScreenShot2 image has no movie marker. **Cause:** the capture ran before the client mapped and committed the declared pair. **Fix:** wait for the declaration and draw before the three samples, and fail on any missing marker. **How found:** the first captures showed the virtual desktop while the second and third held both markers.
- **Symptom:** the private D-Bus daemon exits before Plasma starts. **Cause:** the numeric test UID has no passwd entry in the image. **Fix:** add a container-local entry and drop to that account before launching programs. **How found:** `dbus-daemon` named the missing UID.

- **Symptom:** marked AVIF reports an alpha decode error or gives a decoded canvas one eye wide. **Cause:** the ISOBMFF stereo scheme places per-view presentation dimensions in the track header while the sample-entry dimensions describe the packed frame; libavif 1.4.2 uses the track width as its output tile width and rescales the packed sample (`src/read.c:6227–6237,6782–6791`). **Fix:** the stereo-aware read path must preserve the coded packed samples and their matching alpha, or retain the static pair with a reason. **How found:** a 128×64 packed sequence with a 64×64 colour presentation and a 128×64 alpha presentation failed alpha decode; with both presentations at 64×64 the same coded image opened at 64×64. [ISOBMFF edition 8 §§13.5.2–13.5.4.2](https://webstore.iec.ch/en/publication/113218), [libavif 1.4.2 source](https://github.com/AOMediaCodec/libavif/blob/v1.4.2/src/read.c#L6782)
- **Symptom:** the direct Kirigami file URL reports Ready with a blank item. **Cause:** status can precede a successful pixel decode when the imageformat plugin is absent. **Fix:** a shared animation loader checks that it owns a decoded frame, returns the static pair when appropriate, and reports which reader is missing. **How found:** hiding each plugin separately yielded grabs with only the background. In the Qt SVG control, VectorImage continued to animate.
- **Symptom:** the file changes every tick but two compositor captures cover the same phase. **Cause:** the wall interval includes the D-Bus capture, assembly and PNG write, so a later request can land after a wrap. **Fix:** classify the returned marker on each capture, discard repeated phases and require three distinct values. **How found:** the AVIF source advanced by frame log while the first sampling pass returned a duplicate marker.
