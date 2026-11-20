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
