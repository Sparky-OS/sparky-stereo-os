# A film without sound says so (ORDER 579)

A film with a picture and no audio track shows a volume control at its usual level, which reads as a broken system (Daniel, 2026-11-14, "true, good measure!" to the proposal).
Every player the edition ships and maintains now says "This film has no sound.", in ten languages, and its volume control stays usable.

## The recipe

1. **One sentence, one rule, one place.** The stereo layer (stereo-layer 1.21.0) holds the sentence in its catalogue (`po/LANG/stereo-layer_qt.po`, context `Stereo::NoSound|`) and the rule: the tracks are known, there is a picture, there is no audio track (`Stereo::NoSound::applies(loaded, hasVideo, audioTracks)`, QML singleton `org.sparky.stereo` `NoSound` with `text` and `saysFor()`). Audio-only files are never said to have no sound; a file whose tracks are not read yet is not said anything.
2. **Each player keeps knowing its tracks the way its engine does** and tells the sentence in its own way, beside its volume control and once when the film opens, never as a dialog and never through sparky-stereo-problems:

   | Player | Where it learns the tracks | How it tells |
   |---|---|---|
   | Dragon Player | Qt Multimedia `MediaPlayer.hasVideo`, `audioTracks` | a Kirigami InlineMessage for 8 s; the volume button's tooltip and accessible description |
   | Plank Player | Qt Multimedia `Video.hasVideo`, `hasAudio` | a banner for 8 s; a label in the OSD (it has no volume control) |
   | Haruna | mpv's `track-list` in `MpvItem::loadTracks` (signal `tracksLoaded`) | its OSD once per file; tooltips of the volume slider and mute button |
   | Bino | `MetaData` video and audio tracks | the sentence on the picture for 6 s in place of a missing subtitle (its subtitle overlay); an info line in the Media menu |
   | sView | `StVideo::hasVideoStream`, `hasAudioStream` | a description box for 6 s; a line under the cursor on the volume button and bar; string 2115 in `StMoviePlayer/lang/*` |
   | VLC Stereo | Qt `InputManager`: `video-es` and `audio-es` choice counts | `vout_OSDMessage` once; the volume widget's tooltips |

   Dragon, Plank, Haruna and Bino take both sentence and rule from the layer. sView (its own toolkit and language files) and VLC (its own gettext catalogue) keep a copy, and `tests/no-sound-wording/check.py` in the build tree fails when a copy differs from the layer's in any language: `check.py --layer-po LAYER/po --sview-lang SVIEW/StMoviePlayer/lang --vlc-patch PATCH --self-test`.
3. **Fixtures** (the rig's `make-fixtures.sh`, ffmpeg and x264 of the edition): a marked full side-by-side film, video only (Matroska with StereoMode and the frame packing SEI; MP4 with the SEI), the same with audio (the control), audio starting 4 s late, two audio tracks, an audio-only file, a 2D film with and without audio.
4. **Proof rows**, each with a repeat command (`rig/drun.sh IMAGE OUT PLAYER LANG SCALE FILES STEPS`): said for the silent film; not said for the control; said again for the next silent file of a playlist and gone for the next with sound; German and Japanese read on screen; 100 % and 125 %; both eyes of the 3D film unchanged against the published build; the 2D film unchanged.

## Traps

- **Dragon's upstream disables the volume controls instead** (invent.kde.org/multimedia/dragon merge request 99, merged 2026-11-03, after the 26.04.0 base): silent, and it contradicts "nothing disabled to make the point". When Dragon rebases onto a release that has it, keep the sentence and give the disabled button a way to show it (a disabled button shows no tooltip).
- **A rule evaluated on a model that is cleared first flickers.** Haruna's audio track model is cleared and refilled at every load; a QML binding on its `rowCount` said "no sound" for every film. Decide once, from one signal sent after the tracks are loaded.
- **Symptom: Dragon's controls bar shows only the seek slider in the rig.** Cause: no Qt Quick Controls style (and no desktop name), so the buttons are not drawn. Fix: `QT_QUICK_CONTROLS_STYLE=org.kde.desktop` and `XDG_CURRENT_DESKTOP=KDE` (and `breeze-icon-theme`, `kdeglobals [Icons] Theme=breeze`). Found by loading the same bar with the style set.
- **The bar appears only when two pointer motions arrive within 50 ms** (Dragon's `mainHoverHandler` resets its first point after `veryShortDuration`): send the `m:X,Y` steps back to back, not with `s:` waits between.
- **Rig, `kwin_wayland: Operation not permitted`:** needs `--cap-add SYS_NICE`. **ScreenShot2 `Cancelled`:** no render node. **dbus "Could not get password database information":** the container needs a passwd entry for the uid. **No Qt Wayland shell integration:** install `qt6-wayland`.
- **`dpkg -i deb-multimedia-keyring` in an image breaks apt** (it needs gpgv): extract the key file with `dpkg-deb -x` instead.
- **Making the next source:** `repo/lc-successor.py --in-place --overlay DIR --next V --item TEXT [--depends OLD NEW]` adds a patch to a published `+lc1` source (its "patches hard link" warnings are harmless); it needs `DEBFULLNAME` and `DEBEMAIL` (`dch` prompts without them) and a source date. A native source (sView) and a source with a new orig tarball (the layer) are remade from their commit with `lean.debian_prepare` (it needs `sparky-os/packages/dpkg-stereo/LICENSE` in a sparse checkout). The build script must call `sparky_provenance_init` and pass `SPARKY_PROV_ARGS`, or `lean.release` says "release blocked: the build script did not call sparky_provenance_init".
- **A recipe in the build tree is not what ships.** The tree's sView recipe was at +stereo3d5 (ORDER 529, fork commit 41bddfc6) while +stereo3d4 was published and no +5 package was staged; the next version builds on the newest recipe, or it would regress it when +5 is published.
