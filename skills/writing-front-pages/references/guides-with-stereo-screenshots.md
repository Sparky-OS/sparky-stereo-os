# Guides that carry stereo screenshots

Written from ORDER 38, the guide "View stereo pairs and photos on any monitor" (2026-11-19).
A guide with stereo screenshots is a front page with a rig behind it: every picture is captured from the published packages, marked, measured and shown in a form GitHub can display.

## The recipe

1. **Reconcile first.**
   Unpack the published packages of every program the guide shows (`dpkg-deb -x`) and read what they really ship: the menu entries, the context-menu files, the file types.
   Search the whole unpacked package and the repository's own pages for the name before writing "the edition does not do X" (see [check upstream before fixing](../../search-upstream-first/SKILL.md)).
   List the README and docs lines the guide may rely on, with their line numbers, in the claims table.
2. **The pre-flight table** is the hidden claims table `docs/guides/.NAME.claims.tsv`: one row per screenshot and per load-bearing sentence, with the program, the file shown, what the reader must be able to see, the proof row and the result (`proved`, `not proven`, `work`).
   The guide never carries it.
3. **Fixtures first.**
   `scripts/stereo-guides/mkfix.py` makes a labelled pair (left view red with LEFT, right view blue with RIGHT) and a real pair in every packing: marked MPO, JPS and PNS written with the writers of `sparky-stereo-align`, and the unmarked plain files (side by side, top and bottom, half side by side, right eye first, flat).
   `check_marks.py` reads the marks back with a second parser: the JPS `_JPSJPS_` descriptor, the PNG chunk order and CRC with `sTER` mode 1, and an MPO through Pillow's own reader (two frames).
4. **Capture** with the rig of [stereo-proof-rig](../../stereo-proof-rig/SKILL.md): a fresh container and a fresh Stereo KWin session for every case (`scripts/stereo-guides/run.sh`, `case.sh`).
   Steps are a small file: `max` (put the window at 0,0 over the whole output), `in m:X,Y b:272 k:29+50 s:MS` (fake input), `cap TAG` (ScreenShot2, both eyes side by side, left first), `kd ARGS` (kscreen-doctor, for example `output.1.mode.2` for the side-by-side twin a thumbnail needs), `win TAG` (KWin's window list).
   Find a menu's coordinates from a first capture, then write the steps; Gwenview's menu is **View, 3D** (`Ctrl+M` shows the menu bar), and the whole path is `in m:106,50 b:272`, `in m:150,175 b:272`, `in m:530,208 b:272` on a 1280x800 output.
5. **Prove each picture** with `eyes.py` (mean colour per eye in a box, pixels that differ outside the picture: expect none outside it), `shift.py` (the horizontal shift of a patch between the eyes against the same patch in the source, scaled by the zoom: Gwenview at 96 % measured -8.12 px against the source's -8.11) and a swap check (the left eye after the swap must equal the right eye before, 0 differing pixels).
   Check the file's SHA-256, size, modification and change time and extended attributes before and after a choice that must not touch it.
6. **Mark and show.**
   Every stereo capture becomes an MPO, left eye first (`deliver.py`); the page shows its red-cyan anaglyph as a JPEG with a link to the MPO's raw address, as the README's screenshots do, and says in one line that red-cyan glasses show it.
   A page needs no JPS or PNS of its own for this: the MPO is the form `docs/screenshots/` uses today.
   A capture that is not stereo (a flat control, a menu on a flat picture) stays an ordinary PNG or JPEG and says so.
7. **The sample set:** each pair pinned by address, hash and licence, credited by name; a file whose licence allows redistribution may be committed, anything else is linked; strip location data from any photo.
8. **Cold readers** as in the rules above, with the coverage you really had.

## The sample set of ORDER 38

| Pair | Where | Licence | In the repository |
|---|---|---|---|
| Topographic, rendered from an elevation model | USGS 3DEP, the National Map service's `exportImage` for a 0.2 by 0.14 degree box around Mount Rainier; SHA-256 of the answer in the sample page | USGS-produced data are in the U.S. Public Domain (USGS Copyrights and Credits) | the MPO and the renderer |
| Stereo camera, a Nintendo 3DS | Wikimedia Commons, left and right pictures of one photograph, SHA-1 equal to Commons' record | CC BY-SA 4.0, credit the photographer | linked |
| Planetary left and right pair | NASA's image API finds anaglyphs and unregistered pairs only (the Mars Reconnaissance Orbiter views of the Schiaparelli site are two separate observations); the PDS Imaging Node's rover products carry true left and right frames as `.IMG` files | NASA media | open: needs a pair converted from the PDS frames |

Wikimedia's API answers 429 after a few dozen calls in a minute: wait, never retry in a loop.
A site that answers an automated request with a refusal is not worked around.

## Traps

- **Symptom:** ScreenShot2 answers `Cancelled` although KWin started. **Cause:** no render node in the container. **Fix:** `--device /dev/dri/renderD128 --group-add RENDER_GID`, with software GL for the program only. **Found by:** `Failed to open drm node` in KWin's log.
- **Symptom:** every capture is one eye wide and `stereo` is false. **Cause:** the program declared nothing (a flat file, a program with 3D off): this is the 2D control, not a failure.
- **Symptom:** Dolphin's thumbnails are flat in both eyes. **Cause:** the output is not in a 3D mode; thumbnails follow the screen (`Stereo::ScreenMode`). **Fix:** `kscreen-doctor output.1.mode.2` (the `3D-SBS` twin of a virtual output made with `KWIN_VIRTUAL_STEREO_MODES=1`).
- **Symptom:** sView says "X, could not open display". **Cause:** an X11 program. **Fix:** KWin with `--xwayland` and `DISPLAY=:0`.
- **Symptom:** Showfoto or digiKam shows a "Download Required Model Files" or a Welcome wizard instead of the picture. **Cause:** first run. **Fix:** close the dialog with a click (Showfoto) or seed the configuration (digiKam); do not let a capture of a first-run dialog stand for the program.
- **Symptom:** "Save the correction into the file" is refused on a PNG: "A correction can be saved into JPEG, JPS and MPO pictures only". **Cause:** Gwenview's save writes those three; use a JPEG for the demonstration of the save.
- **Symptom:** after the save the open picture is shown flat, and a fresh Gwenview shows the saved file in 3D. **Cause:** not found (the view is not made again after the save); reproduced three times, 10 s after the save too.
- **Symptom:** a half-width side-by-side picture shows its eyes narrow after "Side by side, left eye first". **Cause:** the menu has no "half" choice: each eye is handed over as it is, and nothing doubles its width. **Fix:** a half-width flag in the shared picture engine's menu is the missing piece; demonstrate with full-width pairs.
- **Symptom:** `spectacle -b -f -o x.png` gives both views in a PNG with `stereo=false`.
  **Cause:** All Screens deliberately clears the stereo flag in `ImagePlatformKWin::takeScreenShotWorkspace`; the current monitor route preserves KWin's metadata.
  **Fix:** use Current Monitor (`spectacle -b -m -n -o x.png`) for a stereo screen: the published +stereo3d2 package saves `x.mpo`, even with a forced PNG suffix; default PNG saves and the GUI's Save action also write MPO, and default JPG writes a marked JPS.
  **Found by:** the published source patch, `strings -a -el` (the key is UTF-16), the active mode from `kscreen-doctor -o`, both routes on the same labelled scene, and independent file parsers.
  Qt reads the MPO back as `Stereo3DLayout=multiViewLeftFirst`; two 1280 by 800 frames match the corresponding raw eyes with mean absolute error below 0.04 on the 0 to 255 scale.
  A flat picture on a 2D output stays a one-view PNG with `stereo=false`.
  The GUI check selected Current Monitor with `-m` and saved with Ctrl+S; it did not exercise the GUI capture-mode selector.
- **Symptom:** Pillow warns "Image appears to be a malformed MPO file" when it opens a JPEG taken out of an MPO. **Cause:** the extracted picture still holds the MPF segment. **Fix:** harmless; the file written by Align stereo pair has two frames.
- A privacy pass on every capture: window titles and breadcrumbs show only the rig's own folders; strip anything else, and never put location data in a committed photo.

## Continuing the proof with digiKam and Plasma

- **Seed a collection instead of accepting a first-run assistant as the program.**
  Follow [driving digiKam with a collection](../../stereo-pictures/references/joining-the-per-file-choice.md#driving-digikam-with-a-collection-in-the-rig).
  Prove the album preview, light table and slide show separately; a positional file argument opens another preview window and establishes none of those three.
  The published +stereo3d5 package showed the labelled left and right eyes in all three views.
  Its album-grid thumbnails showed the left view in both eyes; keep that as work in digiKam's item view, never as a guide limitation.
- **Bound a flat control to the window it tests.**
  In a light table with two populated panes, Enable 3D acts on the focused pane; switch both panes off.
  An inactive main window remains visible behind the light table at sunk depth, so whole-screen eye equality is the wrong expectation.
  The foreground's opaque body and both photo areas measured zero differing pixels after the two switches; album preview and full-screen slide show measured zero over the whole capture.
  The labelled photo and the terrain sample stayed byte-identical to their source files.
- **Use the output verb, not the help text, to test anaglyph.**
  In a real Plasma rig, `kscreen-doctor output.Virtual-0.anaglyph.enable` changed the serialized output's `anaglyph` from false to true.
  Selecting its mode 4, the twin whose `stereo3D` is 5, changed `currentModeId` from 1 to 4; System Settings showed `(anaglyph, modern screens)` in Resolution.
  Mode IDs are local to that output: read the list before choosing one.
  This checks the state and selection on a virtual output, not physical scanout or the GUI checkbox.

## The showcase capture

Use the [showcase recipe](../../stereo-proof-rig/SKILL.md#a-showcase-stereo-screenshot): a real Plasma panel, the volume pop-up pinned, the program refocused, and three menu levels open.
Keep a fake-input client alive and allow 300 ms between moving the pointer over the panel icon and clicking: an immediate move/click gave only a tooltip; the delayed click opened the applet.
Read the pop-up's current frame from KWin, click its pin at frame-right minus 16 and frame-top plus 30, then refocus the program and verify that the pop-up remains.
The published Spectacle Current Monitor route can capture the menus on a delay without taking focus (`-b -m -n -d 1500 -o capture.png` writes `capture.mpo`).
Read the two frames, parse their marks and verify the active program and all three popup windows in KWin's window list after the capture.
The ORDER 38 scene measured window and panel 0 px, volume +3 px, and the three menus +3, +5 and +8 px, with zero vertical disparity.
These are measurements of that scene, not new depth defaults or a physical-output test.
Keep the raw scene as marked PNS for exact pixels; the Markdown page retains the repository's anaglyph JPEG and MPO download link.
