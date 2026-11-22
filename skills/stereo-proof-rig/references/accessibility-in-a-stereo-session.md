# Accessibility in a stereo session

## Establish the inputs first

Source audit dated 2026-11-22: KWin 6.7.4 with the edition's +stereo3d64 patches, plasma-desktop 6.7.4 +stereo3d4, Orca 51.1, at-spi2-core 2.62.1 and speech-dispatcher 0.12.1. The source audit establishes these inputs. Isolated AMD and NVIDIA runs subsequently verified the speech file sink, actual sticky/slow/bounce input and the Zoom/Magnifier measurements below. A result remains scoped to its recorded package closure and session.

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
**Fix:** do not use that module as a silence guarantee. Keep audio access outside the container and validate a file-output module before starting Orca. Use the validated generic file-output recipe below.
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

A virtual ScreenShot2 pair establishes compositor rendering. It does not establish physical display scanout. Retain the session logs, load, configuration, raw captures and measured results with the private test record. The following recipes were exercised in those isolated sessions. Preserve the raw logs and captures alongside each result.

## Validated speech file output

Use one private session bus shared by KWin, kaccess, Plasma, Orca and the test clients. Do not mount sound devices, a host audio socket or a host runtime directory. The following was run with speech-dispatcher 0.12.1.

Configure `speechd.conf` with `AddModule "filelog" "sd_generic" "filelog.conf"`, `DefaultModule "filelog"`, a private Unix socket, `LogLevel 5` and a log directory under the test output. Set `AudioOutputMethod "alsa"` and `AudioALSADevice "null"`: the generic module still initializes its audio backend, even when the synthesis command only writes text. Without this initialization it tried PulseAudio, failed and the server selected another module.

In `modules/filelog.conf`, use a `GenericExecuteSynth` command that passes the module's escaped `$DATA` substitution to a file writer through standard input. The tested command was `printf %s \'$DATA\' | python3 /rig/speech-sink.py`; the Python writer appended JSON containing the received text and a timestamp. Also set `GenericDefaultCharset "utf-8"`, `GenericLanguage "en" "en"`, `AddVoice "en" "MALE1" "filelog"` and `DefaultVoice "filelog"`. These are fixture settings, not desktop defaults.

Start the server once in the private session, with `speech-dispatcher -s -t 0 -C CONFIG_DIRECTORY -P PRIVATE_PID_FILE`. Check an explicit `spd-say -o filelog -w` witness: the test recorded its text in the file sink, `702 END` in the dispatcher log and exit zero. A startup line alone is insufficient. Stop an old server and observe its exit before restarting; an overlapping restart led to an autospawn/socket race during setup.

### kaccess needs the private Xwayland display

**Symptom:** kaccess exits with an xcb display connection error although KWin and Plasma run on Wayland.
**Cause:** this kaccess version explicitly chooses xcb. The private Wayland socket alone is insufficient.
**Fix:** start KWin with Xwayland and give kaccess the display of that private Xwayland instance, on the same private session bus. Never inherit a host display.
**How found:** kaccess startup log, followed by a successful launch with the container's Xwayland display.

### Zoom changes disparity as well as size

An isolated virtual SBS run with the audited KWin measured a flat Qt witness at 1920 pixels per eye. Its circular mark grew from 48 to 96 to 192 pixels in width at 1x, 2x and 4x, equally in both eyes; its disparity grew from 4 to 8 to 16 pixels. This fails the design that plain zoom keeps constant parallax. `ZoomEffect::paintScreen()` scales the already rendered offscreen scene. Treat this as a measured failure, not a supported-mode exception.

The same run measured the Magnifier border at zero disparity at both 2x and 4x. Its area did not come forward as the design requires. At 4x a 200-pixel magnifier clipped the 192-pixel circular mark; do not infer full enlargement from a clipped bounding box. Retain the raw marked pair and the border measurement separately. The AMD and NVIDIA stereo paths reproduced the 4, 8 and 16 pixel Zoom disparities and the zero-disparity Magnifier frame. Debian and edition 2D controls are separate rows, not inferred from those stereo captures.

### Replacing Orca in a container stalls on stale PIDs

**Symptom:** `orca --replace --debug-file ...` reports a cleanup timeout, then produces only periodic cache messages instead of speech initialization.
**Cause:** a container whose PID 1 does not reap adopted children retains terminated Orca processes as zombies. Orca's replacement scan finds those stale PIDs. A second race occurs if the replacement is started while the shortcut-launched instance is still initializing: the two replacement scans can terminate each other.
**Fix:** start the test container with Docker's `--init`. Before replacing a page- or shortcut-launched instance for debug logging, observe its completed startup utterance in the file sink. Test startup and debug replacement as separate operations.
**How found:** `/proc/PID/status`, the replacement log's PID list, and the process list before and after adding an init process. The isolated session then reached logged focus reading and real sticky/slow-key input.

### A process-title change is not process exit

**Symptom:** the test says Orca exited almost immediately after launch.
**Cause:** Orca changes its command line from the Python script invocation to `orca`. A probe matching only `/usr/bin/orca` misses the live process.
**Fix:** match both forms and inspect the process state; retain the PID and the speech evidence. A process appearing is not yet evidence that its speech startup completed.
**How found:** the same PID remained sleeping with name `orca` in `/proc/PID/status`.

### Native accessible coordinates need their window origin

**Symptom:** a pointer click intended for a field hits a label or another control.
**Cause:** native Qt and GTK component bounds are relative to their client window in this rig. Browser bounds can include an estimated frame origin.
**Fix:** use the component bounds relative to the accessible frame, then add KWin's actual client origin. First activate the window with a titlebar click; verify the selected page or field before sending the next input. Preserve the raw bounds and the actual injected point.
**How found:** raw AT-SPI trees, KWin's `clientGeometry`, screenshots, and the fixture's received-text log. A guessed first-field point missed the field; the measured point delivered it.


## Runtime row recipe

1. Start the Accessibility page, a Qt form with two labelled fields, a GTK form with two labelled fields, a local browser form, Dolphin and Gwenview on the private bus.
   Wait for their visible accessible controls, not a fixed startup delay.
   The page's screen-reader switch and Meta+Alt+S are independent startup cases.
   Observe a completed startup utterance before replacing Orca with `orca --replace --debug-file OUTPUT/orca-debug.log` for the reading rows.
2. Dump AT-SPI through `pyatspi.Registry.getDesktop(0)`.
   For each non-null application, recurse over `getChildAtIndex()` and retain `name`, `getRoleName()`, states, component bounds, relations and ordered children.
   Bound the walk by node count and depth, record a vanished application slot or an exception, and never dump password contents.
   For the caret fixture, retain its text length and caret offset; these establish that Home and End reached the field.
3. Capture the panel, launcher, Dolphin, Accessibility page, notification and real lock greeter separately.
   Compare roles, names and ordered children independently of bounds and transient focus/visibility states; retain the latter in the raw dump.
   Normalize only identified changing labels such as clock time, and state the normalization in the comparison record.
   A semantic difference is not automatically a compositor fault: the Debian control may need matching Qt, Mesa and client builds because the edition's packages declare Breaks on the older compositor.
4. Mark each focus transition in a timestamped event log, then match the target names against both Orca's `SPEECH OUTPUT` lines and the speech file sink.
   A tree containing a label does not prove that Orca spoke it.
   A process existing does not prove that its speech startup completed.
5. Enable each keyboard aid through the page, apply, focus the receiving field and inject through KWin's fake-input protocol.
   Sticky: release Shift, then press A; the receiving field gets `A`.
   Slow: a short B is rejected and a held A passes; the tested 500 ms acceptance setting used a 1200 ms held key.
   Bounce: three A presses, with the middle gap 100 ms and the final gap 1000 ms under a 500 ms rejection setting, produce `aa`.
   Record actual input timestamps, received text and the page states; disable each test setting through the page before the next independent row.
6. Use a deterministic coloured witness at 1x, 2x and 4x.
   Wait for repeated stable measurements, then compare against the expected dimensions.
   Do not wait until the expected dimensions appear: that confuses a wrong result with unfinished rendering.
   Measure `left_x - right_x` at the output's 1920-pixel eye width, both eye widths/heights, and pointer and caret responses independently.
   Global-accelerator D-Bus invocation isolates rendering from shortcut interception; label it as such instead of claiming a shortcut-input test.
7. Keep a separate labelled eye-identity image: one eye green, one blue, with geometric landmarks.
   Count opposite-eye colours in a documented interior region at each magnification.
   Measure a flat window's desktop-plane disparity separately from intrinsic disparity in the stereo image.
   Zero opposite-eye pixels in that region is a bounded observation, not a proof about every frame or output arrangement.
8. Capture normal, shaken and explicitly enlarged cursors with a background capture from the same position.
   Compare only the pointer region so clock or notification updates cannot become false cursor pixels.
   Report each eye's bounding box and the change in disparity; different stacking orders can put the same pointer coordinate over different desktop planes.
9. Lock the real private session last through its ScreenSaver interface, capture its accessible password role and marked pair, then remove the container.
   A testing-mode greeter is a different row and must not substitute for the session lock.

### A clipped marker gives a false disparity

**Symptom:** the 4x Magnifier's circular witness appears narrower and its centroid disparity falls below the expected shift.
**Cause:** the default 200-pixel area clips the enlarged circle differently in the two eyes.
**Fix:** retain the clipping as evidence, measure the frame separately, and register a common interior image region over horizontal shifts.
Do not infer scale or disparity from the clipped centroid.
**How found:** the black frame measured 210 pixels including its borders; the interior matched exactly after an 8-pixel shift at 2x and a 16-pixel shift at 4x, despite the clipped centroid.

### A browser coordinate click can land behind its window

**Symptom:** a requested browser-field transition is followed by Gwenview speech and a Gwenview screenshot.
**Cause:** the injected point did not identify the browser control reliably; the accessible coordinate estimate and native window geometry were insufficient for that click.
**Fix:** for the screen-reader focus row, raise the intended window and use the field's AT-SPI Component `grabFocus()`, then verify the focused node and utterance.
Keep actual KWin key injection for keyboard-filter rows.
**How found:** timestamped click points, focus trees, captured window contents and the speech sink; the corrected browser row spoke both field names.

### Preserve native picture pixels in a PNS fixture

A real stereo photograph complements the labelled synthetic identity fixture.
Pack its decoded left and right pictures without resizing; put `(-eye_width) % 8` padding columns between them and write `sTER` mode 1 before IDAT.
Read the packed result back and compare each extracted eye byte for byte with its decoded source.
This is the PNG extension's packing padding, not a change in either eye's geometry.
Retain source hashes, provenance and a declaration trace; the extension alone is not proof that the viewer created a stereo area.
