---
name: stereo-pictures
description: >-
  Preserve stereo image layouts, eye order and metadata through readers, writers, viewers, thumbnails and caches.
---

# Stereo pictures

## Working recipe

1. Use labelled fixtures and identify the file specification, metadata and explicit user override before guessing from dimensions.
2. Round-trip through an independent reader, inspect eye order and format fields, then check viewer/thumbnail behavior and stale-cache invalidation.
3. Return byte/field and pixel evidence separately. Preserving a chunk does not prove its mode was interpreted or rendered correctly.

**Check freshness first.**
Written on 2026-10-07, file managers added on 2026-10-13.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; a viewer also loads [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md) for its picture area.

## The formats

- **MPO** (Multi-Picture Object, CIPA DC-007): one file holding two complete JPEG pictures, one per eye, with tags saying which is which. The format of the twin-lens cameras (Fujifilm FinePix Real 3D, Nintendo 3DS, the 2011 phones). The specification is linked from awesome-stereoscopy's [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md).
- **JPS:** one JPEG holding both views side by side. Files are commonly saved cross-eyed (the right view on the left); a `_JPSJPS_` block in the file can state the layout and order. Read the block when it is there; when it is not, assume the common order and let the user swap.
- **PNG with an `sTER` chunk:** the PNG specification already has a stereo mark, the registered chunk `sTER` ([Extensions to the PNG 1.2 Specification, version 1.4.0](http://www.libpng.org/pub/png/spec/register/pngext-1.4.0-pdg.html), section 3.6; in the register since version 1.3.0), placed before the image data: mode 0 is cross-fuse (the right eye's picture on the left), mode 1 diverging (the left eye's picture on the left, which is our full side by side). Read it whatever the file is named, and write it, mode 1, in every stereo PNG you save. A side-by-side PNG named `.pns` is the older convention for the same thing.
- **A plain side-by-side or top-and-bottom picture** (PNG, JPEG, TIFF): nothing in the file says it is stereo. A viewer offers the input format by hand, and may guess from the shape last (a width of at least twice the height suggests side by side), never before the file's own tags.

## Android camera files (checked 2026-10-07)

- **LG Optimus 3D:** the camera's 3D mode captures with both rear cameras and saves a JPS pair in one JPEG, as documented in this [first-hand camera test](https://www.megatechnews.com/megatech-reviews-lg-optimus-3d-android-smartphone/). Keep both views when importing it; renaming the extension does not convert the pixels.
- **HTC EVO 3D:** switch the camera to 3D, then choose JPS or MPO in its settings ([HTC user guide, pages 67–73, mirrored by ManualsLib](https://www.manualslib.com/manual/513711/Htc-Evo-3d.html)). Both rear cameras supply the pair. Decode the chosen file format using the rules above; do not infer eye order from the phone model.
- **Verify with labelled fixtures first.** A camera manual establishes its capture options, not the eye order of every firmware's files. Check the file's stereo metadata and retain Swap Eyes for unmarked pairs.

## What the pieces do

- **File types:** `image/x-jps`, `image/x-pns` and `image/x-mpo`, sub-classes of JPEG and PNG, offered to freedesktop's shared-mime-info so every file manager names them. A type is only the file: stereo inside an ordinary file (the `sTER` chunk in a `.png`, the frame packing SEI in a video) is found by reading it, in the metadata extractors and the thumbnailers.
- **Reading and writing in every Qt and KDE program:** our KImageFormats gains a JPS and MPO plugin with their MIME types ([danielcamposramos/kimageformats `stereo3d`](https://invent.kde.org/danielcamposramos/kimageformats/-/tree/stereo3d)), checked by reading the written files back with Pillow and exiftool. Any program using Qt's image loading can open them.
- **Showing:** a viewer shows the pair through its own 3D area, declared as full side by side, left eye first, each eye at the picture's own resolution; the rest of the window stays 2D. For files that say nothing: the input format, Swap Eyes, left or right only, not 3D, as in the video players; a per-file choice is kept in the viewer's own per-file store, never written into or onto the picture. Gwenview, digiKam, KPhotoAlbum and Koko are planned on this pattern.
- **Capturing a stereo desktop:** Spectacle saves a capture side by side when a window or an output in it is 3D, as JPS for its JPG choice and as MPO for its PNG choice ([danielcamposramos/spectacle `stereo3d`](https://invent.kde.org/danielcamposramos/spectacle/-/tree/stereo3d)).
- **Painting:** Krita treats a document as a side-by-side pair when it is at least twice as wide as tall, or when its metadata says stereo or side by side, with right-eye-first respected ([Krita `sparky/stereo-painting`](https://invent.kde.org/danielcamposramos/krita/-/tree/sparky/stereo-painting)).
- **Televisions:** a 3D television's own photo player reads MPO over USB or DLNA; the sony-bravia-linux notes measure what one family of Sony sets accepts ([3D photos on BRAVIA](https://github.com/danielcamposramos/sony-bravia-linux/blob/main/docs/3d-photos-on-bravia.md)).

## Proof for this kind of work

- Test pictures with LEFT in the left view and RIGHT in the right view, in every format and order: MPO, JPS with and without the `_JPSJPS_` block, JPS saved in both orders, plain side by side and top and bottom.
- For readers and writers: the views read back byte for byte or pixel for pixel by a second program, and the eye order correct.
- For viewers: both eyes captured, LEFT in the left eye, one declaration on the picture's area, the window's 2D parts identical in both eyes, and the 2D control against the distribution's build.

## Writing the marks (2026-10-07)

Many tools lose a stereo mark when they write a file, which silently turns a stereo picture into a plain one.

- **Use the format's own mark, and register it.** Wherever a format's specification has a stereo field (PNG `sTER`, MPO's CIPA DC-007 tags, the JPS block), use that one.
  Only where none exists do we define a mark, specification page first ([SVGStereo](https://github.com/Sparky-OS/svgstereo) for SVG, animated drawings included since 0.2).
  Every mark is registered in [stereo-layer](https://github.com/Sparky-OS/stereo-layer) and in the shared documents (awesome-stereoscopy's [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md) and the edition's [house formats](../../docs/house-formats.md)) before any program writes it.
- **PNG `sTER`:** Pillow 11.3 writes only the public chunks it knows (plus private ones), so it drops `sTER` both when writing and when re-saving. libpng 1.6 has no `sTER` API, and programs built on it (Qt, GIMP, Krita, ImageMagick) keep the chunk only if they opt in to unknown chunks, which they do not. Until those are patched, insert the chunk yourself: right after IHDR, one byte (1 for diverging, the left view on the left), with its CRC. The specification pads the left view so that the right view starts on a multiple of 8 columns; check that it does.
- **Verify with a chunk parser that can fail:** the chunk order `IHDR sTER … IDAT … IEND`, every CRC valid, the mode byte, and the picture still decodes.
- **Name it `.pns`** (or `.jps` for JPEG with the JPS block). `file` still reports a `.pns` as a plain PNG, so the extension and shared-mime-info carry it until libmagic learns the chunk.
- **Patches upstream,** engine first: libpng (read and write `sTER`), then Pillow, then the programs that re-save pictures (Krita first, then GIMP), keeping the mark on export.

## File managers: thumbnails, tooltips and icons in 3D (2026-10-13, Dolphin)

A file manager shows a stereo file as a pair, never squeezed, through the shared layer and the standard thumbnail cache, and leaves a 2D screen exactly as it was.

- **One thumbnail serves both modes.** The thumbnailer keeps both views side by side, left view first, inside the cache's size box (the [Thumbnail Managing Standard](https://specifications.freedesktop.org/thumbnail-spec/latest/directory.html), section 4.1: a normal thumbnail "must not exceed 128x128", so each view gets half the width), and marks it with an extension key in the PNG, `X-KDE::Stereo3DLayout=sideBySideLeftFirst` (section 5.2: extensions use a key "in its own namespace ... prefixed by X-"). A flat view shows the left half; a 3D view gives each eye its half.
- **Decide with the shared policy, before decoding.** `Stereo::Picture::loadPair(path, bound, {})` (stereo-layer 1.2) applies the photo policy to what the reader says (the `Stereo3DLayout` mark, the format, the size) and decodes only files that can be pairs; `sideBySide()` gives the thumbnail. Videos use `Stereo::Video::layout()` with the stream's mark first (the frame packing SEI, H.264/H.265 Table D-8, which H.264 V15 (08/2024) numbers D-8 and V16 (06/2026) D-9), then the container's (Matroska `StereoMode` with its one-plane display size, [RFC 9559](https://www.rfc-editor.org/rfc/rfc9559) section 18.10; MP4 `st3d`), then the shape (3:1).
- **Each view as large as a flat preview.** Both views share the box a client asks for, so each has half its width. Where the preview is shown at its own size (a tooltip, an information panel), ask once more with twice the box when the first answer is a pair: the larger thumbnail lives in its own cache folder (512 in `x-large`, 1024 in `xx-large`), as the standard has it.
- **Stale thumbnails go.** MPO and JPS are JPEG subclasses, so the JPEG thumbnailer gets them; one that only read the first picture left one-eye thumbnails in every cache. Raising the thumbnailer's `ThumbnailerVersion` makes them again, provided the cache lookup checks the version written in the thumbnail's `Software` key ("KDE Thumbnail Generator JPEG Images (v2)"); prove it by running the new packages over a cache the old ones filled.
- **Carry the mark across the process border.** KIO's thumbnail worker sends pixels through shared memory, so the layout travels as worker metadata (`stereo3dLayout`) and the job writes the cache key; `KIO::PreviewJob::generated()` hands the client the image with its key. Raise a thumbnailer's `ThumbnailerVersion` when its output changes, and make sure every cache lookup checks it.
- **One stereo surface per view, holes only where the pairs are.** The item view is drawn once per eye into one subsurface below the window, declared full side by side; the window draws everything as before except the stereo pictures' rectangles, which it leaves transparent. Names, selection and every ordinary file stay in the window's own surface, identical in both eyes ([`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md)). Render the eyes with `QWidget::render()` of the viewport (a `QGraphicsView::render()` paints items with no widget, and Dolphin's items need it).
- **Only on a screen that shows two eyes.** Ask `Stereo::ScreenMode` for the window's screen: a stereo mode, a stereo pair of outputs or anaglyph draws per eye; a 2D screen draws the plain view and declares nothing, so it is pixel-identical to the program without stereo (Stereo KWin shows a declared surface on a straight 2D screen as its left eye, which for a stereo icon is a view a few pixels off the plain picture).
- **Tooltips and panels:** the hover tooltip and the information panel use `Stereo::WidgetLayer` on their preview widget; a tooltip that shows a pair in 3D gets its own window, prepared translucent before it is created, so ordinary tooltips stay as they were. A layer shows in any translucent window, and Breeze makes every tooltip translucent: give the layer its picture only after the 3D decision (setting As 3D, a screen that shows two eyes), so a Flat tooltip and a tooltip on a 2D screen declare nothing.
- **Stereo icon themes:** a theme lists folders of pairs (2N x N, left first) under `X-StereoDirectories`, each with `X-StereoSize` and `X-StereoLayout=sbs-left-first`, beside a plain theme it inherits; `KIconLoader::loadStereoIcon()` returns the two views (PNG or SVG), and the item draws them per eye; ordinary loaders never read those folders ([Icon Theme Specification](https://specifications.freedesktop.org/icon-theme-spec/latest/), `X-` for extensions).
- **Stereo SVG files:** SVG has no stereo mark; the edition reads the proposed SVGStereo mark, a `layout` attribute in its own namespace on the root `svg` element, which other renderers ignore ([SVG 1.1 Second Edition](https://www.w3.org/TR/SVG11/extend.html), 23.1). An unmarked drawing is one picture.

**Proof for a file manager:** captures of both eyes on a stereo output (each stereo thumbnail, video thumbnail, icon, tooltip and panel preview: the left view in the left eye, matched against the source's views), everything else 0 differing pixels; the left eye equal to the flat view; the same window on a 2D output pixel-identical to the unmodified program with the plain theme; a scrolled view still aligned; the declarations counted in each case's Wayland log (none for Flat and on a 2D output).
On a stereo pair of outputs even the unmodified program's tooltip, which declares nothing, differs between the eyes by a few pixels of position, so compare a Flat tooltip with the unmodified program's, not eye against eye.

## Preserving bytes and interpreting meaning are separate checks (2026-10-19)

The PhotoCraft work exposed a reusable distinction: an exporter can preserve `sTER` while an API still names its modes incorrectly.
Both PNG `sTER` modes describe side-by-side views; they differ in eye order, not side-by-side versus top-and-bottom.
Test preservation, enum semantics, pair extraction and actual display separately, against the format specification.
Carry layout/eye-order information through export and reopen; then exercise stereo-view close/reopen so a correct file does not hide a stale UI state.
Attribute an upstream implementation to its actual authors; filing a report or contributing a follow-up does not make the original implementation ours.
