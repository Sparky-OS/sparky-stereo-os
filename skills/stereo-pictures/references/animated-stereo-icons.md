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
Read the marks separately. The JPEG XL lane draft uses a standard XML box for its proposed declaration. The timed AVIF experiment uses the ISOBMFF stereoscopic-video advisory scheme.
The HEIF `ster` entity group pairs two still image items by their IDs; its members cannot be timed tracks. [SVGStereo 0.4](https://github.com/Sparky-OS/svgstereo/blob/66a673d/README.md#animated-drawings), [AVIF v1.2.0 §§3, 4.1, 5.2](https://aomedia.org/docs/AV1%20Image%20File%20Format%20%28AVIF%29%20v1.2.0.pdf), [ISO/IEC 14496-12:2026 §13.5.4.2](https://webstore.iec.ch/en/publication/113218)

## Keep the two times equal

Use one animation instance for the packed fixture. Declare one full side-by-side surface through libstereo-declare. For a stable theme pair this declaration belongs to the flow described in [themed icons per eye](themed-icons-per-eye.md).
Set the virtual Stereo KWin output to the 1920×1080 SBS mode. See the [dated rig recipe](../../stereo-proof-rig/references/dated-snapshot-rig.md).
For each of three moments, wait for the probe's declaration and a rendered buffer, then capture with ScreenShot2.
Split the 3840×1080 result into two 1920×1080 views. Find the left colour only in the left eye and the right colour only in the right eye, and match the marker's position across eyes.
Require three different positions to catch a stuck frame. Store the SBS capture with PNG Extensions 1.4 §3.6 `sTER` mode 1 and verify the mark before review.
A surface-level proof on a probe establishes compositor eye selection and synchronization for that route. The theme-driven applet proof needs the staged engine and a real pair in its theme.

## Traps

- **Symptom:** a theme name resolves through `QIcon::hasThemeIcon()`, but the Kirigami item reports Error. **Cause:** Qt's explicitly set test theme and the KDE platform theme's configured theme can differ. **Fix:** select the isolated theme in `kdeglobals` and load the KDE platform theme. **How found:** Kirigami's reported status changed from Error to Ready and the fixture appeared.
- **Symptom:** both KImageFormats readers return RGBA64, yet the animated item uploads BGRA8. **Cause:** Qt's QMovie stores a QPixmap (`qtbase/src/gui/image/qmovie.cpp:370–377,399–405`) and the Qt Quick item takes its image (`qtdeclarative/src/quick/items/qquickanimatedimage.cpp:35–43`). **Fix:** preserve the frame as an image into a texture route that supports the desired format. **How found:** QImageReader reported RGBA64, QMovie reported ARGB32 premultiplied and the scene's QRhi texture reported BGRA8 with alpha. This is a path to qualify in the shared engine.
- **Symptom:** the first ScreenShot2 image has no movie marker. **Cause:** the capture ran before the client mapped and committed the declared pair. **Fix:** wait for the declaration and draw before the three samples, and fail on any missing marker. **How found:** the first captures showed the virtual desktop while the second and third held both markers.
- **Symptom:** the private D-Bus daemon exits before Plasma starts. **Cause:** the numeric test UID has no passwd entry in the image. **Fix:** add a container-local entry and drop to that account before launching programs. **How found:** `dbus-daemon` named the missing UID.
