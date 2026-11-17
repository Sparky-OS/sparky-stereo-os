# Stereo icons and theme parts

Sparky Stereo Plasma Theme Studio is the authoring program; its package and recipe folder are sparky-stereo-plasma-theme-studio.
Its product and edition identities are data in one identity.json, used to generate the C++ identity, desktop entry, About data and the untranslated product-name entry in every compiled catalogue.

## Reconcile before authoring

1. Read the published KIconThemes source and run [the loader probe](icon-loader-probe.cpp) against that package.
   The ordinary lookup and the stereo lookup are different APIs.
   A successful stereo lookup does not mean every application draws icons per eye.
2. Read the theme's `index.theme`, its source licence and the SVG's actual groups.
   Preserve the plain inherited theme and work on a copy in the person's chosen project folder.
3. Before implementing a depth control, find the current shared geometry operation in Stereo KWin and its toolkit consumers.
   Check the recorded design ruling as well as disparity, rounding and eye split.
   Daniel's 23 October 2026 ruling rejects an added scale cue on stereo screens; do not infer a new scale law from the older description.
4. Hand back only what was measured.
   The editor and its compositor proof are separate from the packaged-loader probe below.

## The icon representation and the loader

A stereo icon holds two square views side by side, left first: `2N × N` for a declared view size `N`.
It is one picture, not an adjacent file for the right eye.
The published KIconThemes 6.30.0 edition build with patch `stereo-icons.patch` uses this theme extension:

```ini
[Icon Theme]
Name=Example stereo theme
Inherits=oxygen
Directories=plain/16x16/actions
X-StereoDirectories=stereo/32x32/places

[plain/16x16/actions]
Size=16
Type=Fixed
Context=Actions

[stereo/32x32/places]
X-StereoSize=32
Type=Fixed
Context=Places
X-StereoLayout=sbs-left-first
```

The placeholder ordinary directory must exist.
`X-StereoDirectories` keeps old loaders from reading the pairs as flat icons.
`KIconLoader::loadStereoIcon(name, size, scale, &left, &right)` reads a pair and returns separate pixmaps.
Ordinary `loadIcon()` does not read those directories: it resolves the plain inherited icon, which need not equal the pair's left view.
Do not claim ordinary lookups implement left-view cropping based only on a successful stereo request.
The extension follows the [Icon Theme Specification's extension namespace](https://specifications.freedesktop.org/icon-theme-spec/latest/).

For raster pairs delivered for viewing, use `.pns` with PNG `sTER` mode 1, check every chunk CRC and the right view's eight-column alignment, and decode the result independently.
Theme-loader filename support must be tested separately before selecting an installed icon extension.
Keep authored SVG and depth choices editable in the project.
For authored SVG pairs, consult [SVGStereo](https://github.com/Sparky-OS/svgstereo); a procedural SVG and an already authored pair are different paths.

## Run the packaged-loader probe

Compile and run inside an isolated container containing the edition's Qt development files and KIconThemes library and headers.
Use an image approved by the workspace, a private writable home, no network, no display or runtime socket from the host, and a zero core limit.
The probe creates and removes its own temporary theme fixtures; it does not open an installed theme for writing.

```sh
c++ -std=c++17 -Wall -Wextra -Werror -fPIC icon-loader-probe.cpp \
  $(pkg-config --cflags --libs Qt6Widgets) \
  -I /usr/include/KF6/KIconThemes -l:libKF6IconThemes.so.6 \
  -o icon-loader-probe
QT_QPA_PLATFORM=offscreen ./icon-loader-probe
QT_QPA_PLATFORM=offscreen ./icon-loader-probe --expect-ordinary-left
```

The first run must exit 0 and report three passes: distinct left/right views at 32 × 32, the plain inherited icon on ordinary lookup, and a missing pair refused.
The second must exit 1, rejecting the deliberately wrong expectation that an ordinary request returns the pair's left view.
Record the installed package version and the runtime library hash.
This is a loader probe, not proof of a stereo editor or compositor output.

For the real authored Oxygen `video-television` fixture, pass `--theme-pair PROJECT/icons NATIVE_PROOF_FOLDER`.
The optional row compares the published loader's pixmaps with separately rendered `left-N.png` and `right-N.png` at sizes 8, 16, 22, 24, 32, 48, 64, 128 and 256.
Qt's SVG renderer library is insufficient for this path: the matching `qt6-svg-plugins` image-reader plugin must also be present.

## Helper 1 acceptance recipe

The intended helper doubles an SVG drawing without a 3D camera.
The author selects SVG groups and sets their place with one control using the desktop's shared geometry operation.
Each group retains its paint order, transform, clip, mask, opacity, filters and text.
Keep the original source and plain drawing; render each view independently at each declared theme size, then assemble the pair.
Do not silently assign unselected parts by paint order or split a group that the author chose as one object.
Nested selection needs one owner per part so a parent and child are not transformed twice.
Save only on the person's action, through an atomic replacement of project-owned files.

These are required acceptance rows, not results of the loader probe:

| Row | Expected evidence |
| --- | --- |
| A real licensed Oxygen SVG, groups at sunk, screen and popped | Independent per-group disparity predictions from the shared desktop operation, compared with measured views at every exported size |
| Stereo KWin virtual session, output in a 3D mode | Both eyes captured, one full side-by-side declaration on the preview area, none on the surrounding editor UI |
| Disable the preview declaration | The stereo assertion goes red |
| 2D output and zero depth | Plain reference comparison; no unexplained transform or changed pixels |
| Odd positive and negative disparities | Desktop rounding and asymmetric eye split preserved |
| Resize and fractional scale | Preview and controls remain aligned; no extra application resize of the eyes |
| Open, edit, cancel, save and reopen | Source theme unchanged; no write before save; exported pair and project choices read back |
| Invalid group, unavailable source or unwritable destination | A specific error, no partial project or invented replacement |

The pair capture checks compositor eye composition.
It does not prove a physical display's scanout or a completed package.
See [the proof rig](../../stereo-proof-rig/SKILL.md) for those distinctions.

When Python GI is unavailable, [capture-qt.cpp](capture-qt.cpp) calls ScreenShot2 with Qt DBus and drains its native file descriptor in a separate thread.
Build with Qt6Core, Qt6Gui, Qt6DBus and `-pthread`, and run only in the rig's own D-Bus session and runtime directory.
Keep its raw capture in scratch; mark the delivered stereo raster as PNS and independently parse every chunk.
Do not infer the active output mode from ScreenShot2's `stereo` flag: declared content can make that flag true even on an ordinary 2D output.
Record `kscreen-doctor -o` after applying the requested mode.
Compare that 2D capture's left view with a plain undeclared reference using the same UI and source.

## The depth ruling and the source

Daniel's 23 October 2026 ruling rejects an added scale cue and a scale option on stereo screens.
The earlier description of bigger and nearer is perceptual; the stereo transform is the gentle eye shift.
Ordinary 2D pop comes from the desktop's existing effects.
Do not invent a scale formula to reconcile that older wording.
In the inspected KWin `6.7.4-2+stereo3d54+lc1` source, `StereoDepth::parallax()` and `eyeShift()` provide disparity and horizontal shifts.
`WorkspaceScene::paintWindow()` translates the window's copy.
[SVGStereo 0.4 procedural depth](https://github.com/Sparky-OS/svgstereo/blob/main/DEPTH.md) also specifies no added scale cues.
The authoring control must share those operations, not duplicate their arithmetic by hand.

The first helper slice generates an adapter from the exact published source functions, enum, reference width and KConfig defaults and records their SHA-256 hashes.
Read the desktop settings once for both eyes and all sizes in an export.
Integer disparity is a visible limitation at small icon sizes: with the inspected defaults, the full sunk and popped limits both round to zero through 64 pixels per view.
At 128 full sunk is minus one pixel and full popped is zero; at 256 they are minus one and plus one.
Report those measured results rather than calling every exported size visibly stereo.
Daniel settled the icon rule on 16 November 2026: no wider authoring range, and a nonzero part receives the smallest visible step where the desktop budget allows it.
Compute the rounded full-limit capacity with the source-derived KWin operation at each size.
Keep zero at the screen; if capacity is zero, report that one pixel has no room; otherwise clamp the requested magnitude between one raster pixel and that capacity, with its sign.
Do not ceil the capacity or add a separate icon range.
At the inspected defaults, both signs have zero capacity through 64 pixels, popped has none at 128, sunk permits one at 128, and both signs permit one at 256.
This is an honest no-room result for more sizes than the original 8/16 examples.
Measure fractional choices as well as full-limit presets: a ten-percent sunk choice at 128 is the red control on the earlier 0.1.3 slice.

## A continuous control and useful selection

Sunk, screen and popped name places, not three fixed depth presets.
Use one signed continuous value per part, with zero on the screen and both ends derived from the person's desktop limits.
Read KWin's source defaults and the person's configuration; use the same source-derived operation for preview, export and the per-size disparity table.
Show zero explicitly when a nonzero authoring value rounds to no disparity at an icon size.
A selected SVG group needs a visible highlight in both previews and a thumbnail cropped to its painted bounds; IDs alone are insufficient.
Keep highlighting out of exported artwork.
Test fractional edits, actual keyboard delivery, Undo, Redo, and rejection of a parent and child both receiving depth.
Read every message back from all ten compiled catalogues, including country-specific locales falling back to bare French and Spanish.

## Build the core without stereo

Configure Sparky Stereo Plasma Theme Studio with -DSTUDIO_STEREO=OFF.
The core uses Qt Widgets/Xml/Svg/DBus and KDE Config; it does not find or link stereo-layer, generate KWin geometry, render the second view, declare a stereo surface or export paired assets.
The depth provider has a small interface with an all-zero ordinary implementation.
The depth, preview and pair-export implementations live in the stereo folder; the ordinary preview/provider live in plain.
Prove the resulting installed tree in an image with no stereo-layer package: start, open an icon theme, change and save a scheme through KDE's native colour editor, then save the project with no pair exports.
Record actual package absence and ELF dependencies; hiding a checkbox on a stereo-linked binary is insufficient.
Changing identity.json can rebrand the application and generated metadata without rewriting the core.
This keeps an option open; it is no offer or promise to another project.

## Select a painted part

Draw each part alone over a readable neutral checker; a small context inset can locate thin outlines without deforming the isolated drawing.
Use the source element's title or label, with its ID as fallback.
SVGs may paint loose paths and rectangles beside groups, as Oxygen's television does.
Expose those as neutral authoring groups in the working DOM, retaining original source bytes and IDs; zero-depth pixels must still match the original.
Use the same rendered alpha and transforms for hit testing that the preview uses for painting.
Search in reverse document paint order, and repeat a click through the overlapping stack.
The real television's bottom screen area selects studio-part-rect3370, then studio-part-rect3335 underneath; these are working wrappers of the original rectangle IDs.
Prove that with real fake input and read the selected ID back, then compare the selected highlight in both captured views.
On Wayland the client does not know its global window origin: read KWin's client geometry for the rig, then add the preview's client-local position.

## One project and KDE tool round trips

Keep the ordinary copied icon theme, colour schemes and complete copied Plasma theme in one project, alongside the selected drawings, depth choices and separate paired exports.
Do not overwrite ordinary Plasma element IDs with eye-prefixed authored pairs before the consumer understands them.
A Plasma atlas can be rectangular: preserve its source view box, derive the per-view height from its width, and compare its zero-depth pixels with KDE's original drawing.
Validate each vector pair against independent renders of both views, including non-square sources and translated parents.

KDE's native colour editor can be used without applying a desktop colour scheme.
Give the child a private XDG_DATA_HOME, XDG_CONFIG_HOME and XDG_CACHE_HOME, put the working .colors file under color-schemes, and pass its file stem to kcolorschemeeditor with --overwrite.
The editor's saved scheme name can produce a different filename: read the native tool's returned stem, validate it stays inside the private colour-schemes directory, and import those bytes when the child closes successfully.
Keep the imported colour changes in memory until the person saves the project.
Refuse a conflicting project operation while the child is open, and report launch, read and child-exit failures.

Before handing a theme to an external editor, materialize links within the selected theme as independent writable files, and visibly reject outside, dangling or cyclic links.
A preserved alias must never let the editor write back into the source theme or another user file.
For plasmathemeexplorer, copy the complete source theme under the private data directory's plasma/desktoptheme/ID, preserve the metadata identifier, and pass --theme ID.
Prove that the explorer used this copy, rather than a system fallback.
On successful return, compare the private theme tree with the source and retain changed files as a project working copy, preserving valid group depth choices.
A changed source must be revalidated before replacing the current drawing.
The explorer's ordinary preview and the author's paired SVG preview are separate acceptance rows.
A screenshot of the explorer alone does not prove that Plasma draws the paired parts per eye.

## Package and installed acceptance

Build a native package from a committed recipe with ten compiled catalogues, then run the edition's source and payload Lean Code checks, archive-backed link/start gate, complete build record and lintian.
The build record must have no unrecorded inputs and identify a clean recipe commit.
Install the actual candidate in the lane's own rig image, with its required runtime tools, and capture the editor at 100 percent and 125 percent.
Record the active output mode separately from the screenshot's stereo flag.
Check both eyes, the ordinary output, an undeclared flat reference, selected-part alignment and the surrounding screen-plane controls.
Drive the native colour tool through real input, save and close it, then save and reopen the shared project and compare the imported bytes.
Native project tests should also reject invalid inputs and verify that the source themes stay unchanged.

## Traps

- **Symptom:** a click intended for the preview selects nothing while Wayland logs show a real button event.
  **Cause:** the client-local preview coordinates were used as global pointer coordinates; a Wayland client does not know its compositor placement.
  **Fix:** in the rig, add KWin's actual client origin before sending fake input, and compare the selected ID before and after.
  **How found:** the pointer event landed above the canvas, and KWin's window script supplied the missing origin.
- **Symptom:** clicking a visible screen selects only the icon's entire root group.
  **Cause:** that screen is a loose SVG rectangle rather than a named group.
  **Fix:** put loose painted siblings in neutral working-DOM groups, preserving original bytes and IDs, then alpha-test the paint stack.
  **How found:** inspect Oxygen's rect3370 and validate the original pixels plus the real first and second click results.
- **Symptom:** lintian rejects a package description containing only the newly chosen product name.
  **Cause:** description-is-pkg-name requires the package's function, too.
  **Fix:** keep the central identity placeholder and describe icon/theme authoring around it.
  **How found:** the final native package reached lintian after all Lean and link checks, then that exact tag went red.

- **Symptom:** the package's stereo API passes, so every icon is reported stereo.
  **Cause:** the probe never checked ordinary lookup.
  **Fix:** give the inherited plain icon a third colour and test both APIs.
  **How found:** the packaged source separates the directories, and the ordinary-left negative control exits 1.
- **Symptom:** an old brief seems to require an extra scale formula absent from KWin.
  **Cause:** the older wording was read without the later ruling.
  **Fix:** apply the no-added-scale ruling and share KWin's eye shifts.
  **How found:** read the complete depth memory, including the 23 October decision, before treating a source difference as a blocker.
- **Symptom:** a source checkout seems to lack a feature already in the archive.
  **Cause:** its working branch predates the published patches.
  **Fix:** extract and apply the published source package before drawing conclusions.
  **How found:** compare the branch revision and published `debian/patches/series`.
- **Symptom:** the exported drawing shrinks to a corner after setting its icon size.
  **Cause:** the source has an implicit view box derived from its width and height.
  **Fix:** preserve the original renderer's view box explicitly before changing dimensions.
  **How found:** compare an unmodified screen-plane render with the source at the same size.
- **Symptom:** a valid XML pair renders blank in Qt SVG Tiny.
  **Cause:** nested SVG roots are unsupported by that reader.
  **Fix:** flatten each root to a group with the equivalent view-box transform, prefix all IDs and rewrite their references, and clip each eye separately.
  **How found:** compare the vector pair's halves with the two independent eye renders at every exported size.
  General stylesheets and filters need their own acceptance rows; refuse unsupported input visibly.
- **Symptom:** references collide across eyes even after a wildcard DOM query.
  **Cause:** `QDomElement::elementsByTagName("*")` did not enumerate the elements in this path.
  **Fix:** traverse child elements recursively when collecting IDs.
  **How found:** the independently rendered vector-pair comparison caught the incorrect gradient references.
- **Symptom:** a 22-pixel icon produces an invalid marked PNG or loses its rightmost pixels.
  **Cause:** the PNG stereo extension aligns the right view to an eight-column boundary.
  **Fix:** insert the specified padding between the views, keeping the editable SVG pair exactly `2N × N`; decode the padding from the marked PNG's width when splitting it.
  **How found:** an independent chunk parser checks CRCs, mode, alignment and both decoded views.
- **Symptom:** a saved pair differs by a colour bit around translucent edges.
  **Cause:** the packer changes the premultiplied image format or composites it a second time.
  **Fix:** retain the eye image format and use source composition while packing.
  **How found:** compare decoded PNG eyes pixel for pixel with separately saved flat views.
- **Symptom:** the library renders SVG directly, but the icon loader says unsupported image format.
  **Cause:** the Qt SVG image-reader plugin is absent from the runtime plugin path.
  **Fix:** provide the matching plugin package and record the loaded package version.
  **How found:** the real authored-theme loader row fails while the synthetic PNG loader row passes.
- **Symptom:** the copied theme index cannot be reopened correctly.
  **Cause:** a generic INI writer does not reproduce KDE's index semantics.
  **Fix:** use KConfig, preserve the ordinary directories, and prepend the new stereo generation without overwriting earlier authored directories.
  **How found:** save, reopen and Save As from that reopened project, then load it through the published KIconLoader.
- **Symptom:** the virtual session starts but its screenshot is cancelled.
  **Cause:** the unprivileged process cannot open the mapped render node.
  **Fix:** query that node's group ID and add the supplementary group to the container.
  **How found:** KWin reports permission denied before it rejects the configured compositor; a successful socket alone was not readiness proof.
- **Symptom:** an amd64 audit reports i386 packages.
  **Cause:** a cached image tag points to another architecture despite the run's platform request.
  **Fix:** inspect the image architecture, pin its verified ID and assert `dpkg --print-architecture` before querying packages.
  **How found:** compare the runtime architecture and archive metadata, with identical apt source overrides for update and policy.

- **Symptom:** an external editor can write through a working-copy alias into the original theme.
  **Cause:** the copy preserved symlinks rather than separating their file contents.
  **Fix:** materialize internal targets, refuse targets outside the selected theme and detect directory cycles before launching the native tool.
  **How found:** review the copy options, then use a real filesystem alias in the subprocess handoff row and require the original target and outside file to remain unchanged.
- **Symptom:** selecting a small SVG group leaves its thumbnail apparently blank.
  **Cause:** the whole atlas was reduced to thumbnail size.
  **Fix:** crop the isolated group's painted alpha bounds before scaling the thumbnail; keep the full canvas for the stereo preview.
  **How found:** inspect the real television group list at fractional display scale.
- **Symptom:** a Plasma disparity check has the right magnitude and the wrong sign.
  **Cause:** the measurement subtracted left from right while KWin's signed disparity is left minus right.
  **Fix:** keep the measured coordinate convention explicit and compare it with the source operation.
  **How found:** the real south-center group moved from x=30 in the left view to x=31 in the right for predicted disparity minus one.
- **Symptom:** source preparation loses its working directory after dch.
  **Cause:** dch renamed the version-named source directory when the Lean Code version gained +lc1.
  **Fix:** create the source in its final version directory before preparation.
  **How found:** the shared preparation traceback still named the old directory.
- **Symptom:** lintian rejects a valid Lean Code debug archive for non-debug files.
  **Cause:** the required independent payload manifest is installed beside the debug objects.
  **Fix:** document an override limited to that package's manifest directory and the override metadata itself; still run the manifest and identity validators.
  **How found:** the final payload checks pass and lintian identifies only those exact metadata paths.

The probe builds on KDE's KIconThemes API and the edition's stereo extension by Daniel Campos Ramos.
No external artwork or model is included.
