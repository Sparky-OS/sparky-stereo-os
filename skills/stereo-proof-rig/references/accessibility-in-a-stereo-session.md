# Accessibility in a stereo session

## Establish the inputs first

Source audit dated 2026-11-22: KWin 6.7.4 with the edition's +stereo3d64 patches, plasma-desktop 6.7.4 +stereo3d4, Orca 51.1, at-spi2-core 2.62.1 and speech-dispatcher 0.12.1. These are source findings. The three-session accessibility test, silent speech output and eye measurements have not yet run.

1. Follow the [dated snapshot recipe](dated-snapshot-rig.md). Record the published tree, accepted package additions, Debian snapshot, image digest and the candidates of `orca`, `at-spi2-core`, `speech-dispatcher`, `kwin-wayland` and `plasma-desktop`. A candidate is not an installed version or proof that the whole dependency set installs.
2. Obtain the matching source descriptors and their components. Verify their SHA256 and size fields; unpack with `dpkg-source -x`. Read the applied source, not an older development checkout. Retain the descriptor hashes and patch series with the private test record. Check signatures separately; a matching checksum alone does not authenticate an author.
3. Compare the applied effect files with the upstream original tarball. In this audit, `zoom.cpp`, `zoom.kcfg`, `textcarettracker.cpp`, `focustracker.cpp`, `magnifier.cpp`, `magnifier.kcfg`, `shakecursor.cpp`, `stickykeys.cpp`, `slowkeys.cpp`, `bouncekeys.cpp` and `keynotification.cpp` were byte-identical to upstream. This does not say that the shared compositor path is unchanged.
4. Inspect the startup chain and the speech module before launching anything. Use a private container session bus and runtime directory, with neither sound devices nor host sound sockets. The module called `dummy` is not a silent sink in this version.
5. Keep source findings apart from runtime results. Record an expected version mismatch as a failed input row, even if every other source comparison passes.

## Paths to read

| Feature | Source path and finding |
| --- | --- |
| Accessibility page | plasma-desktop `kcms/access/ui/ScreenReader.qml` stores the screen-reader setting; `kcms/access/kcmaccess.cpp` checks `orca --version` and offers `orca --setup`. |
| Startup and shortcut | plasma-desktop `kaccess/kaccess.cpp` registers Meta+Alt+S. `setScreenReaderEnabled()` runs `gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled true`; only a successful exit starts `orca --replace`. Verify the schema and the process on the container's session bus. |
| Wayland keyboard monitor | KWin `src/a11ykeyboardmonitor.cpp` checks the caller against the bus owner of `org.gnome.Orca.KeyboardMonitor`. Orca and KWin must share the private session bus. |
| Speech observations | Orca `src/orca/orca_bin.py.in` exposes `--debug-file`; `src/orca/speech_presenter.py` emits `SPEECH OUTPUT`. These are observation points, not proof that speech-dispatcher accepted or completed the utterance. |
| Sticky, slow and bounce keys | KWin `src/plugins/stickykeys`, `slowkeys` and `bouncekeys` watch `kaccessrc` changes. `keynotification` emits modifier notifications when the corresponding option is enabled. Test the page switches and actual delivered input. |
| Zoom | KWin `src/plugins/zoom/zoom.cpp` renders an offscreen scene and scales it. Default zoom factor is 1.2, initial zoom 1, with focus and caret tracking off. Read the trackers before selecting the caret fixture. |
| Magnifier | KWin `src/plugins/magnifier/magnifier.cpp` blits a pointer-centred source region, then draws the magnifier. The source has no caret tracker or explicit stereo depth assignment. Measure its output before judging the shared compositor path. |
| Looking glass | There is no `src/plugins/lookingglass` plugin in this source package. Distinguish it from the shipped Magnifier and Zoom. |
| Shake cursor | KWin `src/plugins/shakecursor/shakecursor.cpp` draws an enlarged overlay item at the cursor position. Measure that item and the normal cursor in each eye. |

## Traps: symptom, cause, fix and how found

### “Dummy” speech still attempts audio

**Symptom:** a supposedly silent configuration names the dummy module.
**Cause:** speech-dispatcher `src/modules/dummy.c`, `_dummy_child()`, tries `play`, then `aplay`, then `paplay` on `dummy-message.wav`.
**Fix:** do not use that module as a silence guarantee. Keep audio access outside the container and validate a file-output module before starting Orca. A working file-output recipe is still pending.
**How found:** direct source inspection of the three command strings and their `system()` calls; no audio program was launched in this audit.

### The wrong source tree answers the question

**Symptom:** a development checkout has an older package revision than the accepted binary pool.
**Cause:** the checkout and the package under test represent different revisions.
**Fix:** unpack the exact accepted `.dsc`, compare its applied files against the original tarball, and record both hashes.
**How found:** the package revisions differed; eleven selected effect files in the accepted source matched upstream byte for byte. This narrowed the subsequent stereo investigation to their interaction with the compositor, without declaring that interaction correct.

### The switch depends on more than Orca being installed

**Symptom:** the UI can find Orca, but the launch path contains another prerequisite.
**Cause:** `setScreenReaderEnabled()` starts Orca only after `gsettings` succeeds. The UI's `orca --version` probe does not test that operation.
**Fix:** verify the schema and capture the `gsettings` exit and resulting Orca process during the switch test. Do not replace the page test with a manual Orca launch.
**How found:** reading the UI probe and the conditional launch in the same plasma-desktop source. No switch failure has yet been reproduced.

### A quick fake key does not prove slow-key acceptance

**Symptom:** a press immediately followed by a release produces no character with slow keys enabled.
**Cause:** `SlowKeysFilter::keyboardKey()` consumes the first press; acceptance is evaluated on a later press or repeat after the configured interval.
**Fix:** use the [input-delivery recipe](input-delivery.md), preserve the connection, observe hold/repeat events and verify the focused client's received text. Include a deliberately rejected short press. Do not make compositor speed the acceptance gate.
**How found:** the first-event map and time comparison in `slowkeys.cpp`; the acceptance test remains to be run.

## Runtime evidence still required

Run the same fixtures in stereo, with stereo off, and with Debian's KWin from the same snapshot. Dump AT-SPI roles, names, states and relations for the panel, launcher, Dolphin, System Settings, notifications and the lock password field; omit secrets. Keep the raw trees as well as any normalized comparison. Record each normalization and preserve differences in roles, names and accessible state. The `SHOWING` state matters when locating visible Qt controls.

For speech, first prove that a file sink receives an utterance without device access. Then correlate Orca's debug output, speech-dispatcher logs and the triggered focus/menu/notification event. Verify both the page switch and the shortcut. A log line alone is not an end-to-end pass.

At 2x and 4x, capture both eyes as marked stereo files and measure scale, corresponding points, disparity and opposite-eye contamination. Use distinguishable per-eye content. Plain zoom must retain the window's existing parallax; the magnifier area must come toward the viewer. Measure an aid's unspecified depth without assigning one. Measure focus/caret markers, key indicators and both cursor representations where present. Separate pointer tracking from caret tracking; the native and legacy tracker paths differ.

The X11 legacy focus/caret trackers are guarded by `KWIN_WAYLAND_ZOOM_FORCE_LEGACY_FOCUS_TRACKING` and `KWIN_WAYLAND_ZOOM_FORCE_LEGACY_TEXT_CARET_TRACKING`. Do not enable these overrides and call it a default-session pass. Read the source comments about blocking accessibility calls before considering a diagnostic run.

A virtual ScreenShot2 pair establishes compositor rendering. It does not establish physical display scanout. Retain the session logs, load, configuration, raw captures and measured results with the private test record. This reference will gain runnable speech, tree-dump and zoom-measurement recipes only after those rows have run.
