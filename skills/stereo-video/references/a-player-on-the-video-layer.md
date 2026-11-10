# A player on the engine's video layer

Learned from ORDER 453 and 453b (November 2026): Dragon Player and Plank Player, both built on Qt Multimedia's `VideoOutput` stereo layer since 7 October 2026, made to say when the desktop refuses to show a video in 3D.

## What the player keeps, what the engine does

- **The engine (Qt Multimedia's `VideoOutput` / `Video`)** takes every packing apart, declares the video's own surface to Stereo KWin as full side by side, attaches nothing until the declaration is taken, and says a refusal in `stereoLayerFailure` (a string, empty while all is well; `stereoLayerActive` is false while it is set).
  A player has no stereo layer, no declaration and no drawing of its own: a program that still carries one is a superseded recipe (see the first trap).
- **The player** keeps its menu bound to the output's properties (`stereoView`, `stereoInput`, `stereoSwapEyes`, `stereoShapeFallback`, the depth properties for Dragon), its per-file store next to the resume position (Dragon: `dragonplayerrc`, group `[StereoVideo]`, key = SHA-256 of the file's URL, `.input` for the packing, `.depth` for the depth options), the offer to save the correction into the file (Dragon), and the message.

## The refused declaration shown (the one piece a player adds)

The sentence is one for both players, in the nine languages, with the engine's own reason (English) in the brackets: "This video is shown flat: the desktop refused to show it in 3D (%1)."

- Dragon: a `Kirigami.InlineMessage` of the warning type over the video, `visible: video.stereoLayerFailure.length > 0`.
- Plank Player: a banner over the video in the theme's own warning colours (`Kirigami.Theme.neutralBackgroundColor`, `neutralTextColor` for its border, `textColor` for the text), never a fixed colour: a fixed orange ignored the person's colour scheme.
- The video itself is the ordinary picture (one view), so the person sees a picture and is told why it is flat. Nothing else changes: every input, the per-file choices and the depth options stay.
- `qmllint` of stock Qt says "Member stereoLayerFailure not found": the property exists only with Qt Multimedia +stereo3d15, so the player depends on it.

## Recipe: prove a player on the layer, red and green

1. **Two rig images.** Take lane 448's `:red` (Qt Multimedia +stereo3d14) and `:green` (+stereo3d15) rig images (Stereo KWin, a QML runtime, the NVIDIA card through CDI), and install the player's debs in a throwaway container as root with apt: the published tree as a file repository (`deb [trusted=yes] file:/repo mashtabba main`, the image's own `sparky-stereo.sources` removed), the round's debs as a flat repository (`dpkg-scanpackages -m . /dev/null > Packages` and a `Release` with `Origin: Sparky Stereo OS`, so apt keeps the +15 build), Debian over https (`https-only-apt.sh`), then `docker commit -c 'CMD ["sh"]'`.
   "Today" is the published players on +14; "yours" is the new players on +15, installed from the debs, so the Depends are proved too.
   Plank Player needs `qml6-module-org-kde-desktop`: `app/main.cpp` selects that Qt Quick Controls style before loading `main.qml`.
   The earlier rig added it explicitly because the package only recommended it; that workaround does not prove the package's dependencies.
   See [required QML modules](../../edition-packaging/references/required-qml-modules.md) for the installation test.
2. **One fresh Stereo KWin per case,** a fresh `HOME` and `XDG_CONFIG_HOME` (the per-file store of an earlier case must not decide a later one), the player started with a file argument, both eyes captured by ScreenShot2 after the video plays and again a few seconds later.
3. **The refuse case:** `LD_PRELOAD=refuse-shim.so STEREO_REFUSE=1` (the shim of the proof rig). Today: the packed frame, red left of blue, in both eyes, 0 `kde_stereo_content` requests and a buffer attached to the video's subsurface at every frame (249 and 327 in the two players' runs). Yours: the left view in both eyes, the message in the window, 0 attaches.
   Count the attaches, not the subsurfaces: the layer makes its subsurface before the declaration, so `get_subsurface` is 1 in both (`tools/subsurface_attaches.py` reads KWin's `WAYLAND_DEBUG=server` log: the surfaces made a subsurface and the buffers attached and committed to each).
4. **The controls** (same session without the shim): a clip marked left red, right blue is STEREO with 1 `create` and 1 `set_content`; the box of each view has the predicted aspect (the eye size, or the frame's for half views) and both eyes' boxes coincide within a pixel.
5. **The input choices** need input the way a person gives it. KWin's fake input protocol (`org_kde_kwin_fake_input`, with `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1`) drives a pointer and a keyboard: the proof rig's `scripts/fakeinput.c`, built with `scripts/build-fakeinput.sh` and used as [input-delivery.md](../../stereo-proof-rig/references/input-delivery.md) says (steps `m:X,Y`, `b:272`, `k:KEY+KEY`, `s:MS`). Search the skills' scripts before writing a driver: this lane wrote its own 100 lines before finding that one.
   Dragon's controls bar shows only after the pointer moved a few times (six short moves 100 ms apart), its menu button is the rightmost button, and every position is read from a capture, never guessed; Alt+Shift+W is its swap shortcut.
   Plank Player's on-screen display opens on the Down key, its 3D button is the third of the four buttons at the right, and its menu is a list that keys and Space drive (the Space key activates an entry; Return does not).
6. **Per-file store and the file:** after a choice, read the player's rc file from the session's config directory; the media file's SHA-256 before and after "Save the 3D Correction into the File..." with Cancel pressed is the same (the offer writes nothing).
7. **A 2D clip** (a flat green one): 0 declarations, the capture of today's and yours differ in 0 pixels, and every entry that corrects a 3D video is greyed: open the player's 3D menu on the 2D clip and look at each entry, the last ones included (Plank Player's list scrolls, and its Swap Eyes is the last entry).

## Traps

- **Symptom:** a brief says "move the players onto the shared video layer, removing their copies", and the lane finds both already on it.
  Cause: the build tree keeps the superseded +stereo3d1 and +stereo3d2 recipes (`upstream/dragonplayer`, `upstream/plank-player`) beside the shipped ones (`upstream/qtmultimedia/...` and `packages/depth-source`); a folder in the tree is not proof of what ships.
  Fix: before a brief or a change, list the published source's `debian/patches/series` and changelog (`tar tf` of the `.debian.tar.xz` in the pool) and name the shipped recipe's folder; mark a superseded folder with a README that says where the shipped recipe is.
  How found: the pool's Dragon series (0001 to 0008 and the po patch) had no layer of its own.
- **Symptom:** the player's window is black in a control run, 12 to 20 seconds after the start, and `get_subsurface` is 1 with a declaration.
  Cause: the clip was 10 seconds long and the player had reached its end; the layer is empty after it.
  Fix: clips of two minutes, captures within 15 seconds. How found: the 2D clip's last frame stayed green while the 3D clips went black, then `ffprobe`'s duration.
- **Symptom:** `build.sh dragon` ends with "conflicting supplied package: libqt6multimedia6; provide one authoritative edition snapshot" after a good compile.
  Cause: the link gate supplies the published +stereo3d14 from the siblings list and the +stereo3d15 of the round from the flat repository.
  Fix: `ROUND_SOURCES=qt6-multimedia` (the sources built earlier in the round are taken out of the published list). How found: the gate's one line, after `dh_builddeb`.
- **Symptom:** `plank-player` prints `module "org.kde.desktop" is not installed` and no window opens in the rig image.
  Cause: its `Depends` name the Bigscreen module but not the Qt Quick Controls desktop style (`qml6-module-org-kde-desktop`), which a Plasma desktop always has.
  Fix in the rig: install it (`apt-cache policy` first: the name is not `qqc2-desktop-style`). The package's `Depends` is a gap to close, reported with the evidence.
- **Symptom:** after adding `breeze-icon-theme` and `plasma-integration` to the rig image to see the icon-only buttons, Dragon's controls bar never appeared again under the same fake pointer moves.
  Cause: the KDE platform theme changed the application's behaviour (and the window decoration), so the rig no longer measured the package. Fix: no icon theme; the buttons are found by position and read from a capture of the menu they open.
- **Symptom:** Plank Player's 3D menu shows Swap Eyes enabled on a flat 2D clip, while Dragon greys it.
  Cause: the entry was listed with `needsStereo: false` (the Input Format entries are meant to stay open to a video that does not say it is 3D, and the swap was written beside them).
  Fix: `needsStereo: true` for the swap: a video that says nothing becomes 3D when the person picks its Input Format, and the entry is enabled from then on (Plank patch 0004).
  How found: the menu captured on the 2D clip and scrolled to its last entry; the same capture on the fixed build shows it greyed.
- **Symptom (open):** Dragon's "Save the 3D Correction into the File..." entry is enabled on a 2D clip. It is not a correction for that clip; what it does there was not run.
  Investigation of the `+stereo3d10` source found that `ControlsBar.qml::canOfferSave` already checks stereo content, a changed correction, the view and a local file.
  A minimal test on its Qt Quick Controls runtime reproduced a `Kirigami.Action` with `visible: false` whose generated menu item remained visible and enabled after opening the menu.
  Check `menu.itemAt(index).visible` with the menu open; a closed menu makes all its children's effective visibility false and gives a misleading pass.
  Bind the actual menu item's visibility and availability, and test the application's full offer and acceptance paths before calling the package fixed.
- **Symptom:** `STEPS= run case ...` in a POSIX shell function did not reach the case script. Cause: a prefix assignment before a function call is not exported. Fix: `export` the names inside the function.
- **Symptom:** `docker commit -c 'ENTRYPOINT []'` left `["sh"]` as the entry point and later `docker run IMAGE sh -c ...` failed with "sh: 0: cannot open sh". Cause: the image was built from a container started with `--entrypoint sh`. Fix: start the build container with the image's default entry point and `sh -c` as its command, and commit with `-c 'CMD ["sh"]'`.

## Follow-up source checks before changing a player

Plank Player `+stereo3d3` resets `stereoInput` to automatic and `stereoSwapEyes` to false in `app/qml/main.qml::onSourceChanged`.
Its application source has no resume-position or per-file settings store.
Do not mistake its seek bar's current position for a persisted resume position.
For a player without a store, put per-file choices in its own configuration location, using its existing application identity; Plank sets both the organisation and application name to `PlankPlayer` in `app/main.cpp`.
Record the actual settings path when the implementation is tested.
Keep the media files unchanged, key choices by file URL, and verify file A, file B, back to A and a fresh application process.
Returning a choice to its default should clear that choice's entry.
This describes the required follow-up; it does not claim that `+stereo3d3` persists either choice.

The three recurring Dragon QML diagnostics have distinct source sites:

- `PlayerPage.qml: ReferenceError: audioOutput is not defined`: the controls-bar `WheelHandler` refers to `audioOutput` outside the player's object scope.
  Upstream [merge request 86](https://invent.kde.org/multimedia/dragon/-/merge_requests/86), by Erich Seifert, contains commit `ae56fa67c9d5ff4742136a25b0071d18a4f7f047`.
  It binds to `player.audioOutput.volume` and restores the binding when scrolling ends, matching the video area's existing handler.
  The complete patch applies to the `+stereo3d10` source; it was open at the source audit, so recheck its state before carrying it with its author.
  Test a scroll from a nonzero volume and another after an external volume change, not just the absence of the diagnostic.
- `OverlayPopup.qml: ReferenceError: backgroundSource is not defined`: the effect's visibility reads an undeclared name although its shader source is a separately declared object.
  Trace the effect's actual `source` and the `ShaderEffectSource.sourceItem`; do not suppress the warning.
  Verify the background while the popup is open after fixing the reference.
- `IconToolButton.qml: Unable to assign [undefined] to QString`: the optional cast `(action as Kirigami.Action)?.tooltip` produces `undefined` for buttons without that action type, while `ToolTip.text` requires a string.
  Audit both action-backed and directly labelled buttons, and verify their tooltip text and activation.
  An error-free log alone does not prove those controls work.
