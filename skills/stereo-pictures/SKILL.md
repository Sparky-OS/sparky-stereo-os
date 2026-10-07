---
name: stereo-pictures
description: How stereo photographs and images (MPO, JPS, side-by-side pictures) are read, shown, captured and kept on Sparky Stereo OS: the formats, the eye order, what a viewer must offer, screenshots of a stereo desktop, and how to prove it. Load the general sparky-stereo skill first.
---

# Stereo pictures

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; a viewer also loads [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md) for its picture area.

## The formats

- **MPO** (Multi-Picture Object, CIPA DC-007): one file holding two complete JPEG pictures, each eye at full size, with tags saying which is which. The format of the twin-lens cameras (Fujifilm FinePix Real 3D, Nintendo 3DS, the 2011 phones). The specification is linked from awesome-stereoscopy's [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md).
- **JPS:** one JPEG holding both views side by side. Files are commonly saved cross-eyed (the right view on the left); a `_JPSJPS_` block in the file can state the layout and order. Read the block when it is there; when it is not, assume the common order and let the user swap.
- **PNG with an `sTER` chunk:** the PNG specification already has a stereo mark, the registered chunk `sTER` (Extensions to the PNG 1.2 Specification, version 1.3.0 and later), placed before the image data: mode 0 is cross-fuse (the right eye's picture on the left), mode 1 diverging (the left eye's picture on the left, which is our full side by side). Read it whatever the file is named, and write it, mode 1, in every stereo PNG you save. A side-by-side PNG named `.pns` is the older convention for the same thing.
- **A plain side-by-side or top-and-bottom picture** (PNG, JPEG, TIFF): nothing in the file says it is stereo. A viewer offers the input format by hand, and may guess from the shape last (a width of at least twice the height suggests side by side), never before the file's own tags.

## What the pieces do

- **File types:** `image/x-jps`, `image/x-pns` and `image/x-mpo`, sub-classes of JPEG and PNG, offered to freedesktop's shared-mime-info so every file manager names them. A type is only the file: stereo inside an ordinary file (the `sTER` chunk in a `.png`, the frame packing SEI in a video) is found by reading it, in the metadata extractors and the thumbnailers.
- **Reading and writing in every Qt and KDE program:** our KImageFormats gains a JPS and MPO plugin with their MIME types ([danielcamposramos/kimageformats `stereo3d`](https://invent.kde.org/danielcamposramos/kimageformats/-/tree/stereo3d)), checked by reading the written files back with Pillow and exiftool. Any program using Qt's image loading can open them.
- **Showing:** a viewer shows the pair through its own 3D area, declared as full side by side, left eye first, both eyes at full size; the rest of the window stays 2D. For files that say nothing: the input format, Swap Eyes, left or right only, not 3D, as in the video players. Gwenview, digiKam, KPhotoAlbum and Koko are planned on this pattern.
- **Capturing a stereo desktop:** Spectacle saves a capture side by side when a window or an output in it is 3D, as JPS for its JPG choice and as MPO for its PNG choice ([danielcamposramos/spectacle `stereo3d`](https://invent.kde.org/danielcamposramos/spectacle/-/tree/stereo3d)).
- **Painting:** Krita treats a document as a side-by-side pair when it is at least twice as wide as tall, or when its metadata says stereo or side by side, with right-eye-first respected ([Krita `sparky/stereo-painting`](https://invent.kde.org/danielcamposramos/krita/-/tree/sparky/stereo-painting)).
- **Televisions:** a 3D television's own photo player reads MPO over USB or DLNA; the sony-bravia-linux notes measure what one family of Sony sets accepts ([3D photos on BRAVIA](https://github.com/danielcamposramos/sony-bravia-linux/blob/main/docs/3d-photos-on-bravia.md)).

## Proof for this kind of work

- Test pictures with LEFT in the left view and RIGHT in the right view, in every format and order: MPO, JPS with and without the `_JPSJPS_` block, JPS saved in both orders, plain side by side and top and bottom.
- For readers and writers: the views read back byte for byte or pixel for pixel by a second program, and the eye order correct.
- For viewers: both eyes captured, LEFT in the left eye, one declaration on the picture's area, the window's 2D parts identical in both eyes, and the 2D control against the distribution's build.


## Writing the marks (2026-10-07)

Many tools lose a stereo mark when they write a file, which silently turns a stereo picture into a plain one.

- **PNG `sTER`:** Pillow 11.3 writes only the public chunks it knows (plus private ones), so it drops `sTER` both when writing and when re-saving. libpng 1.6 has no `sTER` API, and programs built on it (Qt, GIMP, Krita, ImageMagick) keep the chunk only if they opt in to unknown chunks, which they do not. Until those are patched, insert the chunk yourself: right after IHDR, one byte (1 for diverging, the left view on the left), with its CRC. Check the right view starts on a multiple of 8 columns.
- **Verify with a chunk parser that can fail:** the chunk order `IHDR sTER … IDAT … IEND`, every CRC valid, the mode byte, and the picture still decodes.
- **Name it `.pns`** (or `.jps` for JPEG with the JPS block). `file` still reports a `.pns` as a plain PNG, so the extension and shared-mime-info carry it until libmagic learns the chunk.
- **Patches upstream,** engine first: libpng (read and write `sTER`), then Pillow, then the programs that re-save pictures (Krita first, then GIMP), keeping the mark on export.
