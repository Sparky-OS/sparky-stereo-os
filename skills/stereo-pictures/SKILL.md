---
name: stereo-pictures
description: How stereo photographs and images (MPO, JPS, side-by-side pictures) are read, shown, captured and kept on Sparky Stereo OS: the formats, the eye order, what a viewer must offer, screenshots of a stereo desktop, and how to prove it. Load the general sparky-stereo skill first.
---

# Stereo pictures

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; a viewer also loads [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md) for its picture area.

## The formats

- **MPO** (Multi-Picture Object, CIPA DC-007): one file holding two complete JPEG pictures, each eye at full size, with tags saying which is which. The format of the twin-lens cameras (Fujifilm FinePix Real 3D, Nintendo 3DS, the 2011 phones). The specification is linked from awesome-stereoscopy's [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md).
- **JPS:** one JPEG holding both views side by side. Files are commonly saved cross-eyed (the right view on the left); a `_JPSJPS_` block in the file can state the layout and order. Read the block when it is there; when it is not, assume the common order and let the user swap.
- **A plain side-by-side or top-and-bottom picture** (PNG, JPEG, TIFF): nothing in the file says it is stereo. A viewer offers the input format by hand, and may guess from the shape last (a width of at least twice the height suggests side by side), never before the file's own tags.

## What the pieces do

- **Reading and writing in every Qt and KDE program:** our KImageFormats gains a JPS and MPO plugin with their MIME types ([danielcamposramos/kimageformats `stereo3d`](https://invent.kde.org/danielcamposramos/kimageformats/-/tree/stereo3d)), checked by reading the written files back with Pillow and exiftool. Any program using Qt's image loading can open them.
- **Showing:** a viewer shows the pair through its own 3D area, declared as full side by side, left eye first, both eyes at full size; the rest of the window stays 2D. For files that say nothing: the input format, Swap Eyes, left or right only, not 3D, as in the video players. Gwenview, digiKam, KPhotoAlbum and Koko are planned on this pattern.
- **Capturing a stereo desktop:** Spectacle saves a capture side by side when a window or an output in it is 3D, as JPS for its JPG choice and as MPO for its PNG choice ([danielcamposramos/spectacle `stereo3d`](https://invent.kde.org/danielcamposramos/spectacle/-/tree/stereo3d)).
- **Painting:** Krita treats a document as a side-by-side pair when it is at least twice as wide as tall, or when its metadata says stereo or side by side, with right-eye-first respected ([Krita `sparky/stereo-painting`](https://invent.kde.org/danielcamposramos/krita/-/tree/sparky/stereo-painting)).
- **Televisions:** a 3D television's own photo player reads MPO over USB or DLNA; the sony-bravia-linux notes measure what one family of Sony sets accepts ([3D photos on BRAVIA](https://github.com/danielcamposramos/sony-bravia-linux/blob/main/docs/3d-photos-on-bravia.md)).

## Proof for this kind of work

- Test pictures with LEFT in the left view and RIGHT in the right view, in every format and order: MPO, JPS with and without the `_JPSJPS_` block, JPS saved in both orders, plain side by side and top and bottom.
- For readers and writers: the views read back byte for byte or pixel for pixel by a second program, and the eye order correct.
- For viewers: both eyes captured, LEFT in the left eye, one declaration on the picture's area, the window's 2D parts identical in both eyes, and the 2D control against the distribution's build.
