# The Sound page's Speaker Setup: the channel map, level, delay and crossover, and the rig that measures them

**Check freshness first.**
Written on 2026-11-19 by Claude Sonnet 5.5 (ORDER 23), on plasma-pa 6.7.4 with the edition's +stereo3d4, PipeWire 1.6.9-2, WirePlumber 0.5.19-1 and sparky-stereo-audio 0.1.0.
PipeWire's plugin labels and control names change between releases: read the builtin plugin's ports in a graph dump of the installed version before trusting a name here.

Daniel, 2026-10-10 (item 23): "on multi speaker configs - virtual or not - per speaker volume dedicated page per device that's multi-channel enabled - not able, enabled".
The page is offered for a device whose **current profile** has more than two channels; a device with fewer shows it disabled, with the reason in a sentence on the row.
With every speaker at its defaults nothing is in the signal path (hifi-audio-system-wide, Daniel 2026-11-16).

## What the page is

A page pushed from a "Speaker Setup..." button on each playback device's row (beside "Test" and "Show Channels", which stay), with a device selector, an "every account" box like Sound Quality's, the room (the speakers at the angles of ITU-R BS.775-4), and for the selected speaker its level, a test button; distances; bass management; the output.
Source: `src/kcm/ui/SpeakerSetup.qml`, `src/qml/speakersetup.{h,cpp}` (the QML type `SpeakerSetup`), `src/speakersetupconf.{h,cpp}` (the validated state and the drop-in text, shared with the KAuth helper in `src/kauth/speakershelper.cpp`), `src/speakertestsignal.{h,cpp}` (the pink noise).

## The channel map

- Read from `pw-dump`: the sink node's `audio.position` (a list in any separator: `[ FL FR ]` or `FL,FR`), else its `Format` or `EnumFormat` `position` array; the count is the profile's, so a card that could have 7.1 and runs 5.1 shows 6.
- Names the page knows: FL FR FC LFE RL RR SL SR RC (PipeWire's); any other name makes the device ineligible, with its sentence. A node named `speaker_setup.*` is the setup of another device and is never offered a setup of its own.
- Angles, degrees clockwise from the front centre (ITU-R BS.775-4, read in full from the ITU's PDF): C 0, L and R 30 (Fig. 1); the surrounds of a 5.1 at 110, the middle of the 100 to 120 sector (Fig. 1); with side and rear pairs, equal intervals on the arc from 60 to 150 (Note 4), which for two pairs is 90 and 120. The Recommendation puts no angle on the subwoofer.
- Read in the same Recommendation (Annex 7): the LFE band is 20 to 120 Hz; the film LFE channel is encoded 10 dB down and is to be reproduced with +10 dB; "the bass from the main channels may be added to the LFE signal, and the combination then fed to a subwoofer"; no crossover frequency is fixed (its Fig. 12 uses 50, 80 and 120 Hz as examples). The page's 80 Hz default is the brief's; its source (THX, Dolby) was not read.

## Where each control is written

| Control | Written as | Check |
| --- | --- | --- |
| Level, dB, -30 to +15 | a `linear` builtin node, `Mult` = 10^(dB/20), `Add` 0, only on the speakers whose level is not 0 | the node's `Props` `params` in `pw-dump`: `g_FL:Mult` |
| Distance, metres 0.3 to 30 (feet an option of the same field) | a `delay` builtin node with `Delay (s)` = (farthest - d) / 343, only where it is above 0; `max-delay` 0.5 s | `d_FC:Delay (s)`; measured as an impulse's position |
| Small speakers, crossover 40 to 250 Hz (80) | per small speaker two `bq_highpass` (to the speaker) and two `bq_lowpass` (to a `mixer` that sums them with the subwoofer's own channel), `Q` 0.7071 each: a fourth order Linkwitz-Riley pair, 24 dB per octave | `hp1_FL:Freq` and the other three; measured with tones |
| Test signal | `pw-cat --playback --raw --target SINK --channel-map ... --format f32 -` fed pink noise, one speaker or each in turn | the fake device's file |

Everything is one `filter-chain` module per device in `pipewire/pipewire.conf.d/50-speaker-page.conf` (`~/.config` for this account, `/etc` through KAuth `org.kde.plasma.pa.speakers.write`), made of a virtual sink `speaker_setup.NODE` whose playback stream targets the device (`target.object`).
Levels are filter gains and not the device's channel volumes: the channel volumes are WirePlumber's own saved state (the "Show Channels" sliders write them) and not a person's file, and two controls on one value would fight.
The state is also written as a `# state:` comment line, so the page reads back what it wrote; a file without the mark is never overwritten or removed.
Applying restarts WirePlumber and PipeWire (as Sound Quality does), waits for the sink, checks the filter's controls, the graph's `clock.force-rate` (the setup never pins the rate), the default output and a half second of silence through the sink on the device (its `Format` channels), and writes the earlier file back when any check fails.
The setup's sink becomes the account's default output when the person leaves that box ticked (it is by default); other accounts choose it themselves.

## The rig (bench/speaker-rig)

Containers only, `--network none`, `--ulimit core=0`. Fake ALSA devices (`../rig/pcm_sa631.c`): a 5.1 card, a 7.1 card, a stereo card, as sinks made by `rig-alsa-nodes.lua` with their channel maps in `audio.position`.

- `build-rig.sh BASE NEW`: the image (a base with pipewire, wireplumber, pipewire-pulse, pulseaudio-utils, libasound2-dev, gcc, python3-numpy, qml6, plus the package under test).
- `rig-run.sh NAME IMAGE COMMAND...`: one container per case; root prepares `/run/sa631`, a `systemctl` that restarts the private session as systemd would (and keeps each PipeWire log as `/tmp/pw-N.log`), and optionally hides the filter-chain module (`SP_HIDE_MODULE=1`) or overlays a build tree (`SP_BUILD`); then COMMAND runs as the user `rig` inside a private PipeWire, WirePlumber and pipewire-pulse session.
- `harness.qml` + `qml-steps.sh`: the real `SpeakerSetup` type under `qml6`, no screen (`apply`, `dump`, `wait`, `test`, `stop`).
- `case.py ROW` and `rows.sh IMAGE`: the proof rows. `defaults` (no file, no sink, every channel bit exact), `level`, `distance`, `bass`, `testsignal`, `refusal`, `stereo71`. Each plays a known file, reads what the fake device received (`sp.py`) and judges it against a prediction computed from the design.
- `ui.sh` + `ui.py`: the real page in System Settings under Xvfb, driven through AT-SPI and xdotool, with screenshots (`SP_LANG`, `SP_LANGUAGE`, `SP_SCALE`).
- The native tests: `autotests/speakersetupconftest.cpp` and `speakertestsignaltest.cpp`; they build with `moc` and `g++` against `qt6-base-dev` alone.

How to measure (the prediction first, then the number):

- Level: the RMS of a channel with the setup over the same noise without it, in dB, equals the level on that channel and 0.00 on the others. Measured: -6.00, +3.50, -12.00 dB and 0.00 elsewhere.
- Delay: an impulse per channel; the farthest speaker's first non-zero frame is the reference; `(farthest - d) / 343 * rate` samples earlier for the others. The plugin truncates to whole samples (predicted 419.83, measured 419).
- Crossover: a tone on a front channel; the LFE channel's level is the input plus 20 log10 of the Linkwitz-Riley low pass, 1 / (1 + (f / fc)^4) (predicted -15.58 dBFS, measured -15.58 at 40 Hz and 80 Hz crossover; at 1 kHz predicted -102.8, measured -102.85) and the speaker's is the high pass.
- Bit exact: play 24 bit values in 32 bit words (the low byte zero) so the 32 bit float of the graph holds them, and compare the device's words with the file's.
- Test signal: -20 dBFS is the root mean square level of the burst on the chosen channel; every other channel holds exact zeros.

## Traps (symptom, cause, fix, how found)

- **"PipeWire did not make the output of the speaker setup", with nothing in PipeWire's log.** Cause: `node.dont-fallback = true` (and `node.dont-reconnect = true`) in the filter's `playback.props` made both of the filter's nodes invisible to every client (`pw-cli ls Node`, `pw-dump`), although the daemon's own debug log showed them created. Fix: leave both out; WirePlumber then links the stream to `target.object` (`pw-link -l` shows the links). Found by bisecting the generated file in standalone sessions, one property per variant.
- **A QML property bound to itself.** `soundFormats: soundFormats` in a delegate binds the row's own property to itself, so the property is undefined: ORDER 20's "format in use" line never showed on a device row (measured with a 6 channel stream: no line before the rename, "48000 Hz, 32 bit" after). Give the model an id that is not the property's name.
- **moc stops reading a test class at a raw string literal that holds quotes and braces.** Symptom: a green run with fewer rows than the file has (116 became 106, no error). Cause: moc mis-parses `R"({"a":1})"` in a class body. Fix: ordinary literals; compare the Totals line's count with the rows written.
- **The log line `n_inputs 0` of the filter chain is not an error.** The module logs the explicit port count as 0 and uses the graph's unlinked ports; the channel order was proved by the level row (each level lands on its own channel).
- **The sink is not there the moment the device is.** The filter's output is made when PipeWire loads the module, around the device's return: the check polls for it for five seconds before it says the setup did not come up.
- **The delay is whole samples.** `Delay (s)` is truncated; a prediction of 419.83 samples measures 419. Judge within one sample.
- **Distances are all or none.** A delay is relative to the farthest speaker, so the state names every position or none; the page fills 3.0 m for all when the box is ticked, which is no delay.
- **Apply dimmed, no error on the page, after a change that looks right.** Cause: a QML `new RegExp(string, "gu")` with `\p{L}` throws "SyntaxError: Invalid regular expression" in Qt 6.11's engine (a regular expression literal with the same classes did not), so the binding that composes the device's state had no value and the button stayed off; the message was only in the KCM's own log (`systemsettings` stderr). Fix: build text for a root file in C++ (`SpeakerSetupConf::sanitiseLabel`), never in a QML regular expression; grep the log for `SyntaxError` and `TypeError` after every page run.
- **The page showed the defaults again after Apply.** Cause: `savedDevice: setup.deviceState(...)` is a method call, so the binding never saw the state change. Fix: read the scope's state property (`scopeState.devices[deviceName]`), which notifies.
- **A translated test finds nothing.** The overlay of a development build (`SP_BUILD`) installs the fork's own `.mo` files over the package's, so the added sentences are English and `press:` names that are not found: use the installed package for any language run, the overlay for English only.
- **A name that is a Latin word in one language is not a Chinese one.** The room shows PipeWire's channel names (FL, FC, LFE) and the translated name as a tip and in the heading, so no translation can overflow a speaker.
- **A file the page did not write.** `50-speaker-page.conf` without the mark line is never replaced or removed; the page says the file was left alone.
- **The input check of a root helper** is `SpeakerSetupConf::validate` for every key; the patterns end with `\z`; every refusal has a row with an unsafe character and each was shown red by loosening the check (class to `.`, `\z` to `$`, the limit removed, a range opened); the helper's path is also tested with the state as JSON carries it.
