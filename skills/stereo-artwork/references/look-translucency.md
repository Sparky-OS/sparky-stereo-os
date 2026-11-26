# A look's translucency, measured and transplanted

Load this when a look must carry another look's translucency ("Sparky Black's levels in both stereo looks", queue row 125, 2026-11-26), when a panel is "not transparent enough", or when a text must stay readable over a translucent surface.
The levels are numbers in files, so they are measured from the files first, then in a real Plasma login, then written into the other look's generator and measured again.

## Where a look keeps its levels

- **The Plasma style's frame SVGs**, one per surface: `widgets/panel-background` (the panel), `dialogs/background` (pop-ups, notifications, the launcher's pop-up), `widgets/tooltip`, `widgets/background` (applets on the desktop) and `widgets/translucentbackground` (their alternate background).
  The level is the alpha of each frame element (`center`, the edges and corners); a panel has one set per edge prefix (`north`, `south`, `east`, `west`, and a centre without a prefix), and Oxygen adds `thick`.
  A floating bottom panel in Plasma 6.7 draws the `south` set (measured: Sparky Black's floating panel showed its `south-center` gradient, 0.37 to 0.56 across its thickness).
- **The variants:** `translucent/` is drawn only when KWin's Background Contrast effect runs, `solid/` for a panel the person set to Opaque (or Adaptive beside a maximised window), `opaque/` without compositing ([develop.kde.org, theme elements](https://develop.kde.org/docs/plasma/theme/theme-elements/)).
  KSvg falls back to the plain file when a style has no such folder, so a style without `solid/` (Sparky Black) shows its translucent panel even when the person chose Opaque.
- **The style's own keys** in `metadata.desktop` or `plasmarc`: `[ContrastEffect]`, `[BlurBehindEffect]` (on unless a style says otherwise) and `[AdaptiveTransparency]` (libplasma's `theme.h`).
  The edition turns KWin's blur and contrast effects off in `/etc/xdg/kwinrc`, so these change nothing it shows.
- **KWin's Translucency effect** for windows (`kwinrc [Effect-translucency]`: inactive windows, dialogs, menus): the edition's values sit in `/etc/xdg/kwinrc` and every look inherits them (Kubabbar Glass repeats them in its defaults), so they are equal across the looks before anything is transplanted.
- **The panel's opacity mode**, Plasma's scripting property `panel.opacity` (`adaptive`, `opaque`, `translucent`): the edition's default panel reports `translucent`.

## The recipe

1. Render every frame centre as KSvg draws it: [`svg_render.py`](../scripts/look-translucency/svg_render.py) `STYLE_DIR ...` in a container with PyQt6's QtSvg (`QSvgRenderer.render(painter, elementId, bounds)`), resolving each variant the way KSvg falls back. It prints the mean, the lowest and the highest alpha and the alpha by row (a panel's gradient across its thickness).
2. Measure in a real login: the proof rig's [translucency probe](../../stereo-proof-rig/scripts/translucency-probe/probe.sh) captures the panel, a notification, the launcher's pop-up and two plain windows (one inactive, one dialog) over a black and then a white wallpaper, with KWin's frames; [`analyze.py`](../scripts/look-translucency/analyze.py) `CASE` gives each surface's alpha, 1 − (white − black)/255, as the median of its drawn background (pixels between 0.03 and 0.97: icons and text are opaque, a floating gap is empty).
3. Take the source's 8-bit level per surface and edge (the mean of the render; for a gradient, say the range beside it) and write it into the target look's generator, keeping the target's own colours and drawing.
   Qt's painter rounds an opacity in 256 steps: write `k/256` with the smallest `k` for which `(255 * k + 128) // 256` is the level (`233/256` gives 232), then render again: every surface of the target must equal the source's level.
4. Keep the target's `solid/` and `opaque/` at its own level, so the person's Opaque choice still gives an opaque panel; that is the target's design, not part of the source's levels.
5. Texts: a text over a translucent surface stands on `alpha * surface + (1 - alpha) * wallpaper`.
   [`contrast_over_wallpaper.py`](../scripts/look-translucency/contrast_over_wallpaper.py) gives every `Foreground*` of the style's Window, View, Button, Header and Tooltip groups its worst contrast (1st percentile of the pixels behind the surface) on the look's own wallpaper; [`readable_colours.py`](../scripts/look-translucency/readable_colours.py) moves each failing colour in CIE L* only, chroma reduced only as far as sRGB requires, to 4.55:1, and keeps the meaningful pairs (negative, positive, neutral, link and visited, each against the normal text) at least 5 apart (CIEDE2000).
   A look whose colours were spread for several kinds of colour vision needs that table run again on the new colours.
6. Pictures for a person to choose a level: capture the panel on a 3D output over known wallpapers and hand over marked pairs (`.pns` with `sTER` mode 1, [stereo-pictures](../../stereo-pictures/SKILL.md)), never red-cyan.

## Measured (queue row 125, 2026-11-26, Plasma 6.7.4, Stereo KWin +stereo3d64)

8-bit alpha; "render" is `svg_render.py`, "login" the median `analyze.py` read in a real login on a 2D output.

| Surface | Sparky Black, render | Sparky Black, login | Sparky Stereo Oxygen and Kubabbar Glass before | after, render | after, login |
|---|---|---|---|---|---|
| Panel, bottom edge (`south`) | 129 (102 to 148 across) | 131 (the gradient's median) | 232 | 129 | 129 |
| Panel, top and sides | 44 (14 to 72 across) | 46 (the gradient's median, a floating top panel) | 232 | 44 | 44 (Kubabbar Glass' menu bar) |
| Panel without an edge | 164 | | 232 | 164 | |
| Pop-ups, notifications, the launcher | 157 | 157 | 232 | 157 | 157 |
| Tooltips | 157 | | 232 | 157 | |
| Applets on the desktop | 80 | | 232 | 80 | |
| Their alternate background | 60 | | 232 | 60 | |
| Inactive windows and dialogs (KWin) | 232 | 232 | 232 | unchanged | 232 |

On each look's own wallpaper, 19 of Sparky Stereo Oxygen's 40 shell text colours and 25 of Kubabbar Glass's 32 fell under 4.5:1 at these levels (none and four before, all at the most transparent surfaces); after `readable_colours.py` every one is at 4.5:1 or more there.
Over a pure black or white wallpaper no colour reads at every level, Sparky Black's own included: a level is a choice with that cost, and the pictures show it.

## Traps

- **Symptom:** after the transplant the top panel and the applets rendered 45, 81 and 61 where Sparky Black's are 44, 80 and 60. **Cause:** the opacity was chosen as `floor(255 * k / 256)`; Qt rounds. **Fix:** `(255 * k + 128) // 256`. **Found by:** rendering both styles with `svg_render.py` after generating them, surface against surface (68 equal after the fix).
- **Symptom:** a style generator rewrites files that have nothing to do with the change (Kubabbar Glass' `keepabove.svg`, a `metadata.json` that has its ten languages only in the tree). **Cause:** the tree's files were edited after the generator last ran. **Fix:** run the generator on a scratch copy and bring back only the files of the change; check that the untouched variants come out byte for byte the same. **Found by:** diffing the generator's output with the tree.
- **Symptom:** `derive_oxygen.py` fails writing its record. **Cause:** its `study/` folder is no longer in the recipe. **Fix:** run it on a scratch copy with the folder made there.
- **Symptom:** a validator's panel check matched every panel SVG of the recipe. **Cause:** it tested `"kubabbar-glass" in path.parts`, and the recipe folder has that name. **Fix:** test the path relative to the recipe.
- **Symptom:** the wallpaper never "shows" for one look. **Cause:** that look's layout puts desktop applets across the band the check read. **Fix:** compare the median per pixel over the whole screen above the panel. **Found by:** the capture, with an applet's error box at the top.
- **Symptom:** the probe's test windows never appear; their log says Qt could not connect to the xcb display. **Cause:** the probe runs in a shell the session did not start, without `WAYLAND_DISPLAY`. **Fix:** `QT_QPA_PLATFORM=wayland WAYLAND_DISPLAY=wayland-0`.
- **Symptom:** the launcher's pop-up is not found among KWin's pop-up windows. **Cause:** it is window type 18, an applet's pop-up, with `popupWindow` false. **Fix:** wait for `type:18`.
- **Symptom:** a slice error reading a floating dock. **Cause:** its frame is at half pixels. **Fix:** round the frame.
- **Symptom:** a saturated red could not reach 4.5:1 however light it was asked to be. **Cause:** raising L* with its chroma leaves sRGB, and clipping darkens it. **Fix:** reduce the chroma only as far as sRGB requires at each L*.
