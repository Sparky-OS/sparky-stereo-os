# The browser's flat WebXR display keeps the screen's separation

Symptom first: in the stereo browser, a WebXR page in the flat display (an `inline` session asking for `inline-stereo`, WebXR 3.4, drawn through the page's canvas) shows its depth at half the person's limit in a window half as wide as the screen.
The person's depth limits are one setting, for the screen, in pixels of a view as wide as the output (Daniel, 2026-11-19: "one separation setting, centralized, tailored TO THE SCREEN not to the element size").
A window's, canvas's or buffer's width is only a unit conversion: limit x output width / 1920 x buffer width / shown width.

## What the code did (Waterfox 6.7.5, browser +stereo3d15)

`XRSession::GetWindowViews` (dom/vr/XRSession.cpp, patch 0003, later text from 0013) set the eyes' separation to `mFlatDepth.mSunkPx / 1920.0 * windowWidth`, `windowWidth` being the canvas's width in millimetres at the primary screen's dpi.
For an inline-stereo session the canvas is the window (`pixels` is its rectangle in device pixels), so the separation in the buffer was the limit over 1920 times the canvas's width.
An immersive session is different: the browser puts the session's canvas in full screen (`StartFlatPresentation`, WebXR 3.3 exclusive access), so `pixels` is the screen and the width of the window the page started in never matters.
Read the code's other places before changing one: CSS depth (`width` is the output's, from the compositor) and the WebGL camera (`sunk / 1920 * outputWidth / canvasWidth`) already follow the rule.

## The proof page and the two windows

`scripts/webxr-flat-xrtilt.html`: a grey ramp tilted in depth from 1.5 m to 150 m, a pure red square facing the viewer at the near end and a pure green one at the far end, each 0.06 of its distance wide.
`?mode=inline` makes the canvas as wide as the window and asks for `inline-stereo`; without it the page asks for `immersive-vr`.
The page records the session's views (projection and view matrices) and the framebuffer size in `data-` attributes, so a prediction needs no knowledge of the code under test.

Run, in the rig of [stereo-proof-rig](../../stereo-proof-rig/SKILL.md) with the browser started as `sparky-stereo-browser --marionette -remote-allow-system-access --profile P --new-instance` (`--kiosk` for the full-screen case, `-width 960 -height 1000` for the window) and the page served from a local `http.server`: case `xrinline` (or `xrtilt` for the immersive session) in a fresh Stereo KWin session on a 1920x1080 virtual output in its side-by-side twin, once with `kiosk=1` (full screen) and once with `kiosk=0 w=960` (a window about half as wide); capture with ScreenShot2.
`scripts/webxr-flat-measure.py CASEDIR` (a folder with `pair2.png`, the ScreenShot2 capture, and `result.json`, the page's `data-` attributes and its rectangle) finds each colour's centroid in the left and right half of the capture; the separation on the screen is right minus left (positive: behind the screen) and the prediction is from the recorded views, `(xr - xl) / 2 * eyeWidth`.

Measured, whole pixels (the eye picture is drawn without antialiasing, so each marker's edge snaps to a pixel: read the far point to within one pixel; the views' own prediction is in the last column). The limit is 10 px at 1920 wide on the rig's virtual output.

| Case | Canvas shown (px) | Far, published +stereo3d15 | Far, +stereo3d16 | Prediction from the views |
|---|---|---|---|---|
| inline, full screen | 1904 | 9 | 9 | 9.7 |
| inline, window | 890 | 5 | 9 | 9.8 |
| inline, window | 570 | 3 | 9 | 9.8 |
| immersive, full screen | the screen | 9 | 9 | 9.6 |
| immersive, small window | the screen (it goes full screen) | 9 | 9 | 9.6 |

The same numbers came from the AMD render node and from the NVIDIA card (CDI).
A far point at 150 m reaches 9.6 of the 10 px limit: the parallax of a point at distance z is the limit times (1 - plane / z), and the plane sits at 3.6 m here.
The near (red) point at 1.5 m of the immersive session measured 17 px in front of the screen against a popped limit of 4: the scene plane comes from the page's depth buffer (ORDER 473t) and is not changed by this fix; read it before relying on the nearest point.
A 2D page and an ordinary video show equal eyes (0 differing pixels) before and after, and the WebGL camera's pair is unchanged.

## Traps, each with symptom, cause, fix and how it was found

- **A narrower window shows no marker at all.** Symptom: the half-width capture has the grey ramp and no red or green. Cause: the views are the canvas as a window at the viewer's distance, so a narrower canvas has a narrower field of view and markers placed at a fixed angle fall outside it. Fix: keep the markers within 0.07 of their distance from the axis. Found by looking at the capture before trusting a null centroid.
- **The immersive session cannot show the fault.** Symptom: a half-width window and a full one measure the same. Cause: the canvas goes full screen at once. Fix: the inline-stereo session is the case that depends on the window; keep the immersive one as the control. Found in `StartFlatPresentation`.
- **The button under a canvas as wide as the window.** Symptom: the click lands on nothing in the full-screen window. Cause: a 16:9 canvas as wide as 1920 px fills the height and pushes the button off the page. Fix: a fixed button at the corner.
- **A rig image of Debian testing cannot install the browser.** Symptom: `libdav1d7 (>= 1:1.5.4)` has no candidate. Cause: the edition's FFmpeg libraries are built on deb-multimedia's epoch-1 dav1d; Debian's is 1.5.4-1 without an epoch. Fix: the rig image installs from the published tree with the edition's pin and deb-multimedia's `forky` source (trusted for the build of the image only).
- **A patch edited under a later one passes with fuzz and fails without it.** Symptom: none until the source package is built. Cause: lane 750b changed a line of patch 0003 that patch 0013 carries as context; `patch` with its default fuzz applies 0013, and dpkg-source uses `-F 0`: one of five hunks fails. Fix: change the text where the last patch leaves it, as a new patch on top of the series (0019), and check each new patch with `patch -F 0` in series order over the file's original text. Found by applying the published series to the original `XRSession.cpp` with and without the edit.
- **A commit in a clone made with `-n`.** Symptom: `git diff --stat` after the commit shows 469538 files changed, 67 million deletions. Cause: the working tree is empty, so any command that reads it sees every file deleted; the commit itself held one file. Fix: read `git show --stat HEAD`, never `git diff` against the empty tree, before bundling.
- **The build of the browser and the disks.** The recipe `waterfox-yt3d/build-browser.sh` with `BROWSER_JOBS=4` took 3 hours 45 minutes of wall time, restart included, on a loaded machine (a load average of 40), the objects 3 GB and the cargo target 4 GB at the first stop and about 20 GB in all; the source unpacks twice (about 11 GB beside the orig). Symptom: another lane filled `/mnt/games` from 7 GB to 0.7 GB in 10 minutes while the cargo target lived there. Fix: `docker stop` the build container, copy the cargo target to a disk with room, and run the same recipe again with `BROWSER_RESUME=1` and the new `BROWSER_RUST_DIR`: it went on from the compiled objects (the Rust crates were not rebuilt). Found by watching `df` of each disk every two minutes.
