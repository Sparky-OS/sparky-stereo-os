# A screenshot of a 3D screen

## Recipe

1. Use the [isolated proof rig](../../stereo-proof-rig/SKILL.md), with a private runtime directory and session bus, the published Spectacle package and the exact KWin package under examination.
   Do not use a person's desktop.
2. Record `kscreen-doctor -j` after selecting the requested mode, including the current mode's `stereo3D`, view size and output name.
   A capture's `stereo` flag alone does not establish the output mode.
3. Take the rows below, first on the published package, then on a plain build of the fork, and finally on the installed candidate package.
   Reset configuration and start a fresh compositor session per case.
   Record the command, saved format, dimensions, format-native stereo mark, Spectacle's text key `stereo`, and the expected result.
4. If a capture endpoint returns only one eye in a 3D session, retain its raw reply and metadata and hand the missing behavior to KWin's owner before changing Spectacle.
   Do not fabricate the second eye or substitute a different capture mode.
5. Read each saved pair with a parser independent of its writer, then measure eye order.
   Read ordinary exports as single eyes and run the same capture modes on a 2D-only output as the control.

## Capture-mode table

These are design expectations, not a completed green matrix.
The mode decides stereo even when both eyes contain identical flat content.

| Capture mode | 3D session default | 2D-only session default | Required check |
| --- | --- | --- | --- |
| Full screen, one output | Marked stereo, MPO | Ordinary mono format | Two complete eyes at output view size |
| Current screen | Marked stereo, MPO | Ordinary mono format | Same output in both eyes |
| Active window | Marked stereo, MPO | Ordinary mono format | Same window in both eyes |
| Window under cursor, including popup variants | Marked stereo, MPO | Ordinary mono format | Same selected window in both eyes |
| Rectangular region | Marked stereo, MPO | Ordinary mono format | Same logical region in both eyes |
| Region over flat content | Marked stereo, MPO | Ordinary mono format | Pair retained even when eyes are equal |
| Background, command line, D-Bus forms | Same capture rules | Ordinary mono format | No loss of mode or mark across entry points |
| Several screens as a strip | Mono panorama | Mono panorama | Stereo formats blocked |
| All monitors 2D / 3D; this monitor 2D / 3D | Explicit Spectacle choices before or after capture | Mono default | Duplicate a mono monitor into both eyes of an explicitly selected stereo composition |
| Capture on a 2D screen copied onto a 3D target | Marked stereo, MPO | Not applicable | Session stereo state and both eyes returned |

An explicit ordinary format saves one eye, the left by default and the right selectable.
A person's explicit format choice is retained.
PNG may hold a pair only when the stack's writer emits `sTER`; Spectacle never injects the chunk.
Do not add program-side eye swapping or output packing choices.

## Trap: a wide PNG with both eyes and no mark

**Symptom:** a 1920×1080 3D output gives a 3840×1080 PNG, with no `sTER` and a `stereo` text value of `false`; the default save is not MPO.

**Cause:** in the published kde-spectacle `4:6.7.4-1+stereo3d2+lc1`, the combined-image path clears the stereo flag while retaining both eyes' pixels.
Its format selection consequently does not choose MPO.
Work on the fork is not proof that the published package contains it.

**Fix status:** the required correction preserves stereo state through every capture/save path, defaults 3D captures to MPO, and extracts the selected eye for an ordinary format.
This is not yet an installed-package fix established by this recipe.
The first preflight also found a KWin prerequisite: `CaptureActiveWindow` on `+stereo3d60` returned one 706×513 image with `stereo=false` while `CaptureActiveScreen` in the same 1920×1080 3D session returned 3840×1080 with `stereo=true`.
Spectacle work stopped at that owning-layer boundary.

**How found:** on 2026-11-19, isolated virtual KWin `4:6.7.4-2+stereo3d60+lc1`, protocols `1.21.0-1+stereo3d12+lc1`, and the signed published Spectacle package.
Both `spectacle -b -n -f -o full-screen.png` and the same command with an extensionless output produced the same defective PNG.
A PNG chunk walker checked every CRC and found no `sTER`; Pillow read the dimensions and text key.
A plain QML window supplied the active-window witness, and KWin's own window list established its geometry.
No physical display, fork build, 2D control, region result or corrected package is claimed by this observation.
The initial attempt without a render node timed out without a screenshot; the successful preflight used the authorized AMD render node.

## ScreenShot2 method reconciliation on KWin +stereo3d60

The continuation measured every method in the staged interface XML, in 32 fresh virtual sessions: ordinary or declared full-side-by-side target, on a 1920×1080 output in its 3D or ordinary 2D mode.
Each scene has a desktop-role wallpaper and an inactive ordinary window behind the active target, so desktop depth and declared eye identity have separate witnesses.
Both interactive kinds were selected using KWin's private fake-input connection, and their returned window IDs were checked against the selected target.

| Method | Input signature | 3D ordinary target | 3D declared target |
| --- | --- | --- | --- |
| CaptureWindow | `(sa{sv}h)` | 640×360, stereo=false: one eye | 1280×360, stereo=true: pair |
| CaptureActiveWindow | `(a{sv}h)` | 640×360, stereo=false: one eye | 1280×360, stereo=true: pair |
| CaptureArea | `(iiuua{sv}h)` | 2400×400, stereo=true: pair | 2400×400, stereo=true: pair |
| CaptureScreen | `(sa{sv}h)` | 3840×1080, stereo=true: pair | 3840×1080, stereo=true: pair |
| CaptureActiveScreen | `(a{sv}h)` | 3840×1080, stereo=true: pair | 3840×1080, stereo=true: pair |
| CaptureInteractive, kind 0 window | `(ua{sv}h)` | 640×360, stereo=false: one eye | 1280×360, stereo=true: pair |
| CaptureInteractive, kind 1 screen | `(ua{sv}h)` | 3840×1080, stereo=true: pair | 3840×1080, stereo=true: pair |
| CaptureWorkspace | `(a{sv}h)` | 3840×1080, stereo=false: both eyes, wrong flag | 3840×1080, stereo=false: both eyes, wrong flag |

These are red observations, not a fixed KWin result.
The area is the same requested 1200×400 logical rectangle in both eyes.
On the 2D-only ordinary-target control, all methods return mono: window 640×360, area 1200×400, screen/workspace 1920×1080.
On the 2D-only declared-target control, +60 still returns pairs from those content-bearing captures, with the workspace flag still false.
That existing 2D behavior is a preservation baseline for the screenshot-plugin change, not proof of a stereo output mode.

**Trap: CaptureArea appears absent.**
Symptom: D-Bus reports UnknownMethod for CaptureArea despite the method appearing in the interface.
Cause: the caller used `(iiiia{sv}h)`; the XML requires unsigned width and height, `(iiuua{sv}h)`.
Fix: generate input signatures from the actual interface XML and compare them with runtime introspection before classifying a capture failure.
How found: the original incorrectly signed call failed; the corrected call returned both 1200×400 eyes on +60.

Keep raw bytes and the original reply metadata together.
A marked JPS made from a raw reply by the stack's writer is a viewing derivative; its valid mark does not change the original KWin reply's stereo=false result.

## Read back independently

Run inside the proof container, using this skill folder as `PICTURES`:

```sh
python3 -I "$PICTURES/scripts/stereo_verify.py" mpo capture.mpo
python3 -I "$PICTURES/scripts/stereo_verify.py" jps capture.jps
python3 -I "$PICTURES/scripts/stereo_verify.py" pns capture.pns
python3 -I "$PICTURES/scripts/eye_order.py" decoded-pair.png 0 0 1920 1080 1920 0 1920 1080 "$NEAR_X" "$NEAR_Y" "$FAR_X" "$FAR_Y" 64
```

The last command is an example for two 1920×1080 views, decoded into a side-by-side scratch image.
Adjust both view boxes to the actual decoded size; pick near and far textured blocks in the left half, with their coordinates relative to that half.
The script matches each block along the same row in the right view and compares near disparity with far disparity; labelled fixtures provide a separate eye-identity control.
Equal eyes or an untextured block cannot establish eye order.
Do not call an unmarked wide PNG a successful stereo export because it decodes or looks like two eyes.
For a PNG, parse each chunk length, type, payload and CRC through `IEND`, record whether `sTER` exists and its mode, and separately read the image's text keys.
A text key saying `stereo=true` does not replace the format-native mark.
Keep defective unmarked pairs only in explicitly named disposable scratch; delivered stereo evidence must carry its format's mark.

## Output mode and paired content are different

KWin order772-kwin adds `stereoOutput` to ScreenShot2 version 7. It says whether a captured output composes two eyes. `stereo` keeps its pixel-pair meaning. Spectacle must follow the mode for its default: a declared pair on an ordinary 2D output is a mono export by default, with stereo offered as an option. Equal eyes in a 3D mode remain a pair.

The plugin-only plain build passes 34 new real-DBus QtTest rows, including a mono monitor at either side of a stereo workspace, and all 16 unchanged screenshot tests. All 32 fresh-session probes pass; each of the 16 2D-only raw images is byte-identical to its +60 baseline. This establishes KWin reply behavior, not a corrected Spectacle package.

Upstream ScreenShot3 is KWin MR10307, commit 5be042886b6404b220bc92df4707fe59d30f09be, the counterpart required by Spectacle dda3c729. It is a memfd transport port, not the stereo repair. The plain branch carries Xaver Hugl's ad655ed7 and Vlad Zahorodnii's dc8d2b7f context-restoration fixes with their author credit.

## Trap: a region selection closes but no file appears

**Symptom:** the published Spectacle accepts a rectangle in a stereo screenshot and then prints `Cannot save screenshot. Error while writing file.` The background process remains alive.

**Cause:** its ordinary canvas crop applies to the packed image, rather than the same rectangle in both eyes. The source path and a failing QtTest establish the single-rectangle crop; the published writer rejects the observed odd-width result. Do not classify a timeout alone as lost synthetic input.

**How found:** three isolated runs on the published package; the final run traced pointer press, motion and release reaching Spectacle, its full-screen overlay disappearing, and the writer error. KWin's before/after window inventory independently showed the overlay closing.

**Fix status:** the plain source correction crops the same rectangle in both eyes and passes the region QtTest and virtual-session region capture. Packaging and installed-package checks remain pending.

## Plain-build results, package still pending

The Spectacle source correction passes 92 QtTest cases, including 20 formerly failing mode/default rows and two region geometry rows. A further failing case required the explicit All Monitors 3D choice to retain a mono monitor in both eyes. The plain executable produces 201×121 views for the same 201×121 region in both eyes; a uniform wallpaper patch supplies the flat-content control. Its MPO contains two identical views and remains stereo because the output mode is 3D. These are plain-build results; no installed candidate package has been verified.

A source-rebuild builder needs packaging helpers in addition to the source descriptor's Build-Depends. Check `command -v git dch` before source preparation: `git` identifies the fork inputs and `dch` (devscripts) is used by Lean Code preparation. The ORDER 772 run stopped under its three-attempt rule when the third preparation reached missing `dch`, after patches and translation checks had succeeded. Installing it and rerunning has not been measured in this run.

Do not trust a flat-content label without measuring the two views: a patterned wallpaper at sunk depth has real disparity. Use a uniform patch with a margin larger than the desktop depth shift, decode both JPEGs independently, and compare their pixels. The proof must still read the MPO's native disparity-view and viewpoint entries.
