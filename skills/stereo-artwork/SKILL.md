---
name: stereo-artwork
description: >-
  How to make the edition's artwork: copy an existing style exactly (its own pixels, missing letters built and checked against the typeface, new letters from a calibrated recipe), turn 2D art into a stereo pair with a measured separation, animate in both eyes, and deliver editable files with the right stereo marks. Load the general sparky-stereo skill first.
---

# Stereo artwork

**Check freshness first.** Written on 2026-10-07, from the SparkyOS boot screen ("SPARKYOS / POWERED BY DEBIAN / STEREO 3D EDITION"). The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; [`stereo-pictures`](../stereo-pictures/SKILL.md) has the file formats.

## Copy a style exactly

1. **Reuse the original's own pixels** wherever the letters or shapes already exist: cut them from the original image, alpha and all. A copy is exact by construction.
2. **Identify the typeface by measurement before using it.** Render the same word in each candidate and compare letter by letter: the width ratio and the overlap (IoU) after fitting. The right typeface matches every letter's width within a few percent. A wordmark often adds a uniform extra weight and tighter tracking, which shows as the same small difference on every letter.
3. **Build a missing letter from existing ones when the typeface agrees.** Example: an "O" from a "U" whose rounded bottom half is mirrored to the top. Check the construction against the typeface's own glyph (97.8% overlap here) and correct the width by repeating the straight middle columns, never by stretching: stretching changes the rim width.
4. **New letters come from a recipe calibrated on the original letters:** font size, extra weight, rim width and placement, fill colour and opacity. Search those parameters to minimise the difference from the original letters, then check each letter. Where a letter exists in the original, keep the original.
5. **Keep the canvas size** when a script scales the image by its width (Plymouth themes do), and centre elements by their measured bounding boxes. "Looks centred" is a measurement.

**Fonts:** most desktop font licences permit rendered images and logos, but never the font file itself. Keep the font out of every repository. Logos ship as images or SVG, never as web fonts. Web text uses CSS stacks of fonts people already have (`Verdana, Geneva, "DejaVu Sans", sans-serif`), so nothing is hosted.

## From 2D art to a stereo pair

- **The background stays identical in both eyes**, at the screen plane (disparity 0). Foreground elements shift by +d/2 in the left eye and −d/2 in the right: crossed disparity, in front of the screen.
- **Take d from a measured reference**, not a guess. One way: a professionally mastered 3D clip. Block-match a face against its background in a few frames, and use the face's separation from the background as a fraction of the eye width. In a half side-by-side source with a 2:1 sample aspect, one coded pixel is two display pixels. The SparkyOS screen uses 0.473% of the eye width (9.08 px at 1920 per eye, each eye shifted by half of it).
- **Verify on the result:** block-match each element in the pair you made. The foreground must measure d and the background exactly 0.
- **Preview without a 3D display:** a red/cyan anaglyph (Dubois matrices). The background shows no colour fringes and the foreground floats.

## Animation in both eyes

When an animated element follows a path drawn on the image (orbits, a progress line), each eye computes the path from its own shifted elements. Both eyes run from one animation clock, so the motion stays in step. Everything that can appear (messages, password prompts, progress) is drawn in both eyes, on the screen plane unless it belongs to a floating element. Nothing may appear in one eye only.

## Deliverables

- **Editable:** layered OpenRaster (`.ora`, opens in Krita) with named layers. For the pair, one group per eye ("Left eye", "Right eye"), so a layer's depth changes by moving it in one group.
- **The pair:** full side by side, left eye first, saved as `.pns` with the PNG `sTER` chunk, mode 1. See [`stereo-pictures`](../stereo-pictures/SKILL.md): many tools drop that chunk.
- **The recipe:** a small JSON with the measurements and shifts, so the pair can be rebuilt or retuned.
- Each eye's flat image and the anaglyph preview.
