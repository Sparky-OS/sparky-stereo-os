# Stereo icons and theme parts

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

## The depth ruling and the source

Daniel's 23 October 2026 ruling rejects an added scale cue and a scale option on stereo screens.
The earlier description of bigger and nearer is perceptual; the stereo transform is the gentle eye shift.
Ordinary 2D pop comes from the desktop's existing effects.
Do not invent a scale formula to reconcile that older wording.
In the inspected KWin `6.7.4-2+stereo3d54+lc1` source, `StereoDepth::parallax()` and `eyeShift()` provide disparity and horizontal shifts.
`WorkspaceScene::paintWindow()` translates the window's copy.
[SVGStereo 0.4 procedural depth](https://github.com/Sparky-OS/svgstereo/blob/main/DEPTH.md) also specifies no added scale cues.
The authoring control must share those operations, not duplicate their arithmetic by hand.

## Traps

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

The probe builds on KDE's KIconThemes API and the edition's stereo extension by Daniel Campos Ramos.
No external artwork or model is included.
