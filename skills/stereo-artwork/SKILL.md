---
metadata:
  requires-packages: inkscape
name: stereo-artwork
description: >-
  Create and verify editable stereo artwork and themes with measured disparity, synchronized animation and preserved format marks.
---

# Stereo artwork

## Working recipe

1. Identify the source artwork, licence, requested style, per-eye dimensions and intended depth; inspect the source before editing.
2. Keep named layers, one timeline and a rebuild recipe. Measure disparity and check both eyes and ordinary 2D presentation.
3. Return editable sources, marked pair, flat views, preview and measurements. A reference disparity is a starting point, not a universal comfort limit.

**Check freshness first.**
Written on 2026-10-07, from the SparkyOS boot screen; looks and themes added on 2026-10-14 ("SPARKYOS / POWERED BY DEBIAN / STEREO 3D EDITION").
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; [`stereo-pictures`](../stereo-pictures/SKILL.md) has the file formats.

## Copy a style exactly

1. **Reuse the original's own pixels** wherever the letters or shapes already exist: cut them from the original image, alpha and all. A copy is exact by construction.
2. **Identify the typeface by measurement before using it.** Render the same word in each candidate and compare letter by letter: the width ratio and the overlap (IoU) after fitting. The right typeface matches every letter's width within a few percent. A wordmark often adds a uniform extra weight and tighter tracking, which shows as the same small difference on every letter.
3. **Build a missing letter from existing ones when the typeface agrees.** Example: an "O" from a "U" whose rounded bottom half is mirrored to the top. Check the construction against the typeface's own glyph (97.8% overlap here) and correct the width by repeating the straight middle columns, never by stretching: stretching changes the rim width.
4. **New letters come from a recipe calibrated on the original letters:** font size, extra weight, rim width and placement, fill colour and opacity. Search those parameters to minimise the difference from the original letters, then check each letter. Where a letter exists in the original, keep the original.
5. **Keep the canvas size** when a script scales the image by its width (Plymouth themes do), and centre elements by their measured bounding boxes. "Looks centred" is a measurement.

**Fonts:** inspect the actual font licence and notices before redistributing a font file; do not infer permission from its name or installed availability.
The edition's logo deliverable is an image or SVG. Keep font binaries out unless redistribution has been checked and is part of the task.
The current website uses system font stacks (`Verdana, Geneva, "DejaVu Sans", sans-serif`).

## From 2D art to a stereo pair

- **The background stays identical in both eyes**, at the screen plane (disparity 0). Foreground elements shift by +d/2 in the left eye and −d/2 in the right: crossed disparity, in front of the screen.
- **Take d from a measured reference**, not a guess. One way: a professionally mastered 3D clip. Block-match a face against its background in a few frames, and use the face's separation from the background as a fraction of the eye width. In a half side-by-side source with a 2:1 sample aspect, one coded pixel is two display pixels. The SparkyOS screen uses 0.473% of the eye width (9.08 px at 1920 per eye, each eye shifted by half of it).
- **Verify on the result:** block-match each element in the pair you made. The foreground must measure d and the background exactly 0.
- **Preview without a 3D display:** a red/cyan anaglyph (Dubois matrices). The background shows no colour fringes and the foreground floats.

## Animation in both eyes

When an animated element follows a path drawn on the image (orbits, a progress line), each eye computes the path from its own shifted elements.
Both eyes run from one animation clock, so the motion stays in step.
Everything that can appear (messages, password prompts, progress) is drawn in both eyes, on the screen plane unless it belongs to a floating element.
Nothing may appear in one eye only.
Animated artwork keeps its mark on every frame: an animated SVG uses the [SVGStereo](https://github.com/Sparky-OS/svgstereo) mark (0.2, animated drawings: one timeline, nothing crosses the boundary between the views), and animated raster artwork uses its format's own stereo field where its specification has one.
Every mark is registered in [stereo-layer](https://github.com/Sparky-OS/stereo-layer) and the shared standards documents first.

## Looks and themes: whose they are, and the glass

For a live theme/control, use [the toolkit/depth guidance](../stereo-window-3d-area/references/qt-kde-depth.md).
Keep appearance, motion and semantic depth separately editable; the proposed Theme Editor is not a shipped feature.
Preview focus/pressed/disabled states, high contrast, reduced motion and ordinary 2D alongside both eyes.
Edge-deep and centre-deep desktop designs are possible policies to prototype; stereo does not mandate one depth map.

Written on 2026-10-14, when the edition took two default looks: Oxygen, and a classic look in the spirit of Mac OS 8.

- **Find who made a look in its own files.** A Plasma style keeps it in `metadata.json` or `metadata.desktop` (`X-KDE-PluginInfo-Author`, `-Website`, `-License`); an Aurorae decoration and a Look and Feel package the same way. Follow the website to the author's repository or store page, and credit the person by name.
- **A missing licence file is a question, not a guess.** When the metadata names a licence but the repository has no licence file, ask the author to add one before a package cites it.
- **Inspired by a closed design means drawn by us.** A look in the spirit of a commercial system takes its ideas, never its bitmaps, fonts, logos or names. Before reusing a community theme's images, ask its author whether they are their own drawings; if they are not, or nobody can say, redraw them.
- **Tell the creators.** The people who made a look are the right ones to see what we do with it and to help: one short note each, in their own venue (an issue on their repository, a message on their store page).
- **The glass is KWin's Translucency effect, plain alpha with no blur.** In KWin 6 its id is `translucency`: `[Plugins] translucencyEnabled=true` and `[Effect-translucency]`. The old `kwin4_effect_translucency` names are ignored without a warning. The edition's values: inactive windows and dialogs at 91 %, full-screen windows opaque so a film on one screen does not fade when the mouse moves to another. Check a running session with `qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.isEffectLoaded translucency`.
- **On a stereo desktop the glass meets the depth rules:** sunk inactive windows and floating dialogs are the translucent ones, so the layers read as glass at their depths; on a 2D screen the look renders as it always did.

## Deliverables

- **Editable:** layered OpenRaster (`.ora`, opens in Krita) with named layers. For the pair, one group per eye ("Left eye", "Right eye"), so a layer's depth changes by moving it in one group.
- **The pair:** full side by side, left eye first, saved as `.pns` with the PNG `sTER` chunk, mode 1. See [`stereo-pictures`](../stereo-pictures/SKILL.md): many tools drop that chunk.
- **The recipe:** a small JSON with the measurements and shifts, so the pair can be rebuilt or retuned.
- Each eye's flat image and the anaglyph preview.
