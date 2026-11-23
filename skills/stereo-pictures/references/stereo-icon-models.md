# Author a stereo icon model and its loop

Start from the geometry and the theme's native sizes. Both eyes see the same pose and each eye retains its intended size.
Weather icon models live beside the Kubabbar Glass icon studio at `sparky-os/packages/kubabbar-glass/tools/icons3d/weather` in the distribution build tree.
Use [two cameras](../../stereo-two-cameras/SKILL.md) for the projection and [animated stereo icons](animated-stereo-icons.md) for the applet and compositor proof.

## Build the two looks

1. Describe each solid in camera-facing scene units. Positive z is toward the viewer. Keep thickness, the nearer ray ends, the farther stars and the falling particles in the model. Keep the view's framing in x and y.
2. Take the same theme name, family parameters and phase for both looks. `geometry.py` returns the contour, closed mesh, colour and opacity. `picture.py` projects each contour into both eyes. `render.py` puts the solids in the Kubabbar Glass studio for the photoreal run.
3. Use the studio's `rig`, `separation` and `place_eyes`. Fit the depth range across the loop and hold the cameras fixed while the model moves. The current authoring candidate gives the same disparity in pixels at each native size. A different approved candidate can use the same solids.
4. Remove the floor from a floating model's studio. Set film transparency. Downsample premultiplied linear RGBA, then encode straight-alpha sRGB. Write the photoreal masters and loops at 16 bits per channel.
5. Write each picture's mark. PNG Extensions 1.4 §3.6 requires `sTER` mode 1 before IDAT for this left-first layout. Use `(-eye_width) % 8` transparent columns between the views. At 22 px per eye the canvas is 46 px wide. The complete PNG has 22 left columns, two padding columns and 22 right columns. Check the decoded alpha and dimensions in addition to the chunk CRCs. [PNG Extensions 1.4](https://www.libpng.org/pub/png/spec/register/pngext-1.4.0-pdg.html#C.sTER)
6. In a native-size review sheet, place each eye's asset at the same integer position and share the labels at screen depth. Start with a 1920×1080 canvas per eye. Split the set across sheets when the assets and readable captions exceed one canvas.

## Keep the loop and measure it

Start with twelve samples at 100 ms. At the wrap, advance the last phase one step and evaluate the model against phase zero. Compare vertex positions and opacity and also measure the absolute sample difference from the last decoded frame back to the first. The last displayed frame is normally a different phase.
Use a geometric period that closes for the motion, such as one sector of a nine-ray sun. For precipitation, fade to zero on both sides of the position reset. Render the whole scene once at each sampled time for the two eye views.
For exact Qt SVG samples, use its controlled document animator with the same time for both views. With 100 ms poses, sample current intervals at their middles and compare 50 ms and 1250 ms for the wrap. Qt SVG 6.11.2 keeps the public renderer's repaint rate and the document's frame clock in different state. [Qt SVG animator](https://github.com/qt/qtsvg/blob/v6.11.2/src/svg/animation/qsvganimator.cpp#L99)

Retain phase zero as the static asset. Use one SVGStereo document with `sideBySideLeftFirst` for the loop, and one complete packed frame per JPEG XL tick. Read all twelve decoded frames, their delays and the loop count. Compare the sample arrays with the encoder input. [SVGStereo 0.4](https://github.com/Sparky-OS/svgstereo/blob/66a673d/README.md), [ISO/IEC 18181-1:2024 §§D.3.4, F.2](https://previewnorm.com/iso/ISO%20IEC%2018181-1-2024%20PDF.pdf)

For an off-axis photograph, predict the horizontal shift at distance z from the camera as `f × baseline × (1/z − 1/convergence)`. Match the same feature by its alpha edge in both views, fitting x and y together. Use an isolated render with the same pose and camera when another solid covers the feature. For a curved feature, report the range from the mesh's depth extents and the fit for the visible edge. Record the vertical residual, since the cameras predict zero vertical disparity.

At every rendered size, check that the first and last row and column of each eye have alpha exactly zero. Count the interior pixels whose alpha is 1 to 15, both in the stored precision and after conversion to 8-bit. These counts distinguish a soft intended silhouette from a large faint layer.

## Judge the icon where the person sees it

1. Read the look's own files for the panel, not a review colour. The edition's default look names its Plasma style in `default/org.sparkystereo.desktop/contents/defaults`; that style's `widgets/panel-background.svg` gives the panel centre's fill and opacity (black at 0.91015625), and its `plasmarc` says whether blur and contrast change what shows through (both off). What shows through a bottom panel is the wallpaper, so composite the panel over the default wallpaper's bottom rows (grey 24.8 gives `#020202`).
2. Take the text colour from the same style's `colors` file, `[Colors:Window] ForegroundNormal`. A symbolic icon takes that colour on the panel.
3. Put each sheet on the dark panel first, then on the second look's panel, then on a light fill, at native sizes. A 22 px icon is judged at 22 px, then magnified with nearest-neighbour sampling, never only at 64.

## The symbolic treatment

KDE's weather applet asks for the `-symbolic` name in a panel ([KDE HIG, icons](https://develop.kde.org/hig/icons/): at 22 px icons are "almost always symbolic"). A KDE symbolic icon is one colour: its SVG paths use the class `ColorScheme-Text` with `fill:currentColor`, and the icon loader replaces the stylesheet's colour with the panel's text colour (Oxygen 6.30's `applets/22x22/weather-few-clouds-symbolic.svg` is one such path).
The stereo symbolic proposal keeps the model's cameras and depth and draws every solid in that one colour. Two consequences to show the person before choosing:

- **A plate of the same colour hides its glyph.** Draw a sign's plate as an outline (two overlapping open contours for a disc, three quads for a triangle) so the glyph stays visible; check that the four status signs still differ at 22 and 24 px (half-alpha silhouettes compared pairwise).
- **Overlapping solids merge in one colour.** A storm's bolt in front of its cloud, or a moon behind a cloud, become one silhouette in each view at 22 px; only the disparity separates them. Put the coloured icon beside the symbolic one on the same sheet so the difference is seen, not described.

## Tell two names apart at 22 px

Colour alone does not tell two names apart in a panel, because the symbolic icon has one colour. Measure the difference of the two left views' silhouettes at 22 px: the pixels whose alpha is on different sides of one half, and the sum of the alpha differences in pixels.
A direction cue must change the silhouette: an arrow below a horizon line, up for sunrise and down for sunset, with a wide head on a thin stem, so that turning it over swaps where the head and the stem are.
Keep the measurement in the sheet script as an assertion, so a later change of the model that makes the two names alike again stops the sheets.

## Pale models on a light background

A pale pigment (a moon of `#f9dda0`, flakes of `#d6ecff`) keeps a median contrast near 1.1 against a light fill: the icon fades.
Propose a darker shade of the same solids (pigment only) and show it beside the present colour on the dark, the second and the light background. Check that the camera records and scene extents of the proposal equal the original's, so the depth did not change.

## Pop one element of a flat sign

A sign whose plate stands at the icon's plane can still have one element in front of it. Give the plate the depth that puts the camera's convergence on its face, the same depth the sun's disc has (`1/(2/D − 1/(D − z_near)) − D` for a nearest element at `z_near`), place the element at `z_near`, and take the solids' front ring as the outline both looks measure.
If the renderer gives status signs a flat camera, keep that exception for the signs that stay flat only; otherwise the popped element renders flat and every check still passes.

## Verify a metadata rewrite

Use the same JPEG XL codestream with three inputs: standalone XML, one XMP packet with a custom property, and the marked XMP packet with a second XML box on either side.
Inspect the output independently for `xml ` and Brotli-wrapped `xml ` under ISO/IEC 18181-2:2026 §§9.6–9.7. Parse the declaration by the namespace URI and local property name. Count the output frames as a separate result.
An unrelated ExifTool 13.55 edit retained the custom XMP property and all twelve frames. The standalone form was readable with `-u`, and the same write replaced it.
KImageFormats 6.30.0 read the first XML box. The libjxl 0.13.0 CLI re-encode and the `djxl` to PNG to `cjxl` round trip retained the last XML box. A one-image KImageFormats `write()` preserved the metadata it read and emitted a still. [JPEG XL Part 2](https://standards.iteh.ai/catalog/standards/iso/db9e07be-4d7d-465a-8dc9-eba2215ce61d/iso-iec-18181-2-2026), [XMP Part 1](https://www.iso.org/standard/75163.html)

## Traps

- **Symptom:** a sun looks like a square on a different background. **Cause:** the studio floor's shadow catcher contributes faint alpha throughout the tile. **Fix:** remove the floor for floating weather models and measure the alpha of every outer row and column. **How found:** opening the old pilot on contrasting colours revealed the outline and the alpha scan found values of 15 to 19 at the tile edge in 8-bit readback.
- **Symptom:** a 16 px tile still has faint alpha on its edge after floor removal. **Cause:** an extreme ray enters the reconstruction filter's support near the smallest raster boundary. **Fix:** increase the model's x/y margin at authoring time, then render it again with the same z geometry and convergence rule. **How found:** the initial 16 px sun had border alpha 1365 in its left 16-bit view. The margin-adjusted render passed the outer-pixel check.
- **Symptom:** a 22 px marked image has an odd-width split or shifts one view. **Cause:** `sTER` requires the right eye's first column at an eight-column boundary. **Fix:** calculate padding from the per-eye width, split the views around the padding, and check both actual widths. **How found:** the zero-padding validator accepted the 64 px pair and rejected the correctly padded 22 px pair.
- **Symptom:** Qt SVG holds the first pose or shows several silhouettes on top of it. **Cause:** Qt SVG 6.11.2 ignores general SMIL `animate`. The tested CSS group-opacity recipe left multiple ray poses visible. **Fix:** use a shared `animateTransform` timeline for the two view drawings. The sampled-pose export positions inactive poses outside the canvas and uses uniform values at integer milliseconds for Qt's interpolation. **How found:** fixed-time SVG grabs showed a multiple-ray silhouette with CSS opacity and one clean pose with the transform. [Qt SVG 6.11.2 handler](https://github.com/qt/qtsvg/blob/v6.11.2/src/svg/qsvghandler.cpp#L1655)
- **Symptom:** a metadata tool displays a stereo mark and the mark disappears after editing a title or description. **Cause:** a bare XML box can be read as metadata and replaced by an XMP packet on write. **Fix:** place the namespaced property in the same XMP packet as the ordinary properties. **How found:** ExifTool's unrelated description edit preserved the XMP form and replaced the standalone form.
- **Symptom:** a decoder reports the right mark but a rewrite leaves a still. **Cause:** a one-image API does not write a timeline. **Fix:** compare the frame count and delay as well as the XMP value, and use an animation-aware writer. **How found:** KImageFormats read twelve frames and wrote one despite keeping the XMP packet.
- **Symptom:** an SVG seek reports unequal first and wrapped phases. **Cause:** setting QSvgRenderer's repaint rate leaves the document's own seek rate at 30 fps. **Fix:** in the fixed-time probe, load `QSvgDocument` with `AnimatorType::Controlled`, set the time in milliseconds, advance and draw. **How found:** the public probe rendered repeated poses at the wrong reported times. The controlled readback made the first and wrapped sun images byte-identical.
- **Symptom:** the verifier stops with `IndexError` at `isolated[0].outline` after many names passed. **Cause:** the model file was changed while the render job ran; Blender had imported the old geometry at its start and the verifier imported the new one later, so a recorded feature name (`status`) no longer existed (`status-0`). **Fix:** commit the geometry before a render job starts, never edit it while a job runs, and render and check a name in the same job from the same commit. **How found:** the job's start time was earlier than the model file's modification time, and the names that failed were exactly the ones whose solids the edit renamed.
- **Symptom:** sunrise and sunset are told apart in colour but are the same picture in a symbolic panel. **Cause:** the cue was a small arrow in a corner, one to two pixels of silhouette at 22 px. **Fix:** an arrow below the horizon line whose head and stem trade places when it turns over; 6 to 8 half-alpha pixels and about 8 pixels of alpha differ at 22 px in either look. **How found:** comparing the 22 px left views' half-alpha masks, with the colours replaced by one tint.
- **Symptom:** a narrow snowflake edge fits outside the camera's predicted interval at 64 px. **Cause:** the isolated feature spans too few pixels along its contour to support a stable shift fit. **Fix:** re-render that feature at 256 px with the same model and the native-size camera rule. Keep both measurements and test the same tolerance. **How found:** the scattered snow branch fit was −1.34 px at 64 and −0.96 px at 256, inside its predicted −0.983 to −0.920 px interval.
