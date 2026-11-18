# The Sound page's format and rate controls (Sound Quality), and the rig to prove them

**Check freshness first.**
Written on 2026-11-18 by Claude Sonnet 5.5 (ORDER 20), on plasma-pa 6.7.4 with the edition's +stereo3d3, PipeWire 1.6.9-2, WirePlumber 0.5.19-1 and sparky-stereo-audio 0.1.0.
PipeWire's property names change between releases: read `man pipewire-props` of the installed version before trusting a name here.

Daniel, 2026-10-10 (item 20): "bit depth and sample rate per hardware and for the internal graph ... every automatic choice shown and changeable".
The defaults are the engine's ([system defaults](system-defaults.md)); this page only shows them and lets the person change them.

## What the page is

A page pushed from the Sound page's toolbar ("Sound Quality…", beside "Rename Devices…", KDE's own pattern for a second page).
Source: `src/kcm/ui/SoundFormats.qml`, `src/qml/soundformats.{h,cpp}` (the QML type `SoundFormats`), `src/soundformatconf.{h,cpp}` (the drop-in writer, shared with the KAuth helper in `src/kauth/`).
The main page's device rows gain one line, the format in use.

## Where each value is read and written

| Shown or set | Read from | Written to |
| --- | --- | --- |
| The engine's choice: rates, resting rate, quality, per-card outputs | `/var/lib/sparky-stereo-audio/choices.json` (the engine's own state) | never written by the page |
| The reason, in the person's language | the output of `sparky-stereo-audio show` (its own sentences, ten languages) | never |
| The graph now: rate, allowed rates, quantum, min and max quantum, forced rate | `pw-metadata -n settings` | `pw-metadata -n settings 0 KEY VALUE` for the running graph, and the files below for the next start |
| A device's supported rates and formats, the format in use | `pw-dump`: the node's `EnumFormat` (rate as `{default,min,max}`, intersected with the standards' list) and `Format` | rule in `monitor.alsa.rules` (`audio.format`, `audio.rate`, `audio.allowed-rates`, `dither.method`) |
| A display's audio blocks (LPCM channels, rates, bits; encoded formats) | the kernel's `/proc/asound/cardN/eld#C.D`, the card from the node's `api.alsa.pcm.card` | never |
| A Bluetooth device's codec | the node's `api.bluez5.codec` | never (the codec decides the rate and the format) |
| The person's own settings | `50-sound-page.conf` in `~/.config` (this account) or `/etc` (every account, through KAuth) | the same files |

The person's files are four, all named `50-sound-page.conf` and all starting with one mark line: `pipewire/pipewire.conf.d` (rates, quantum), `pipewire/client.conf.d` and `pipewire/pipewire-pulse.conf.d` (`resample.quality`), `wireplumber/wireplumber.conf.d` (quality rules and per-device rules).
"Back to automatic" rewrites the state without the key; a file with no wanted content is removed, and only a file that carries the mark is ever removed or replaced.

## The application of a change (and what says no)

1. Validate the state (rates 8000 to 768000, at most 32; quantum a power of two inside 32..2048 unless min and max say otherwise; quality 0 to 14; a node name `alsa_|bluez_(output|input).NAME`; a format from the five PipeWire names) and let `spa-json-dump` read each generated file.
2. Write the files (the KAuth helper for every account: `org.kde.plasma.pa.soundformats.write`, `auth_admin`, session persistence).
3. Apply: values of the graph only set go into the running graph at once; every removal and every device or quality change restarts WirePlumber and PipeWire (`systemctl --user restart wireplumber.service pipewire.service`, as plasma-pa's own rename page does), then the engine's `apply` gives the graph its automatic answer again.
4. Check: graph values read back, a running stream that pins the rate (`node.force-rate`) outside the chosen list is named; quality seen on the output nodes; for an output device a half second of silence is sent with `pw-cat --raw --target NODE` in the chosen rate and format and the sink's `Format` is read while it runs (the node going to `error` or running at another rate is a refusal).
5. On any failure the earlier files are written back, the services restarted, and the page says why and that the earlier settings stay.

## The rig (bench/page-rig)

Everything runs in containers with the fake devices of `bench/rig` (a DAC taking 44.1 to 192 kHz, a 48 kHz-only device, a 16-bit-only device, an HDMI television with an ELD block, a Bluetooth-like sink with `api.bluez5.codec = aac`).
`rig-alsa-nodes.lua` here adds `api.alsa.pcm.card` and the codec to the stand-in nodes.

- `page-run.sh [--proto] COMMAND`: as root it prepares the fixtures, runs the engine's `detect --write` against `/opt/sa631/proc-asound`, puts a `systemctl` in front that restarts the private session the way systemd would, optionally starts a system bus and polkitd (`PG_POLKIT=yes|no` decides the Sound page's action), then runs the command as the unprivileged user in a private PipeWire, WirePlumber and pipewire-pulse session.
- `harness.qml` + `qml-steps.sh STEPS.json`: the real `SoundFormats` type driven from a JSON list of steps (`apply`, `dump`, `wait`) under `qml6`; no screen needed. `steps-flow.json` is the main flow, `steps-sys.json` the every-account flow, `steps-no.json` the polkit refusal, `pin.sh` the pinned-stream refusal.
- `ui.sh` + `ui.py`: the real page in System Settings under Xvfb, driven through AT-SPI and xdotool, with screenshots.

## Traps (symptom, cause, fix, how found)

- **The engine overrides the person's rates at login.** Symptom: after a restart the graph was back at 48000 with the full list although the person's file said 96000. Cause: the engine's `apply` skips a key only when a file that is not its own matches `^\s*KEY\s*=`; a JSON-quoted `"default.clock.rate": 96000` never matches. Fix: write PipeWire's `key = value` form in the PipeWire and client files (WirePlumber's rules stay JSON, as plasma-pa's rename page writes them). Found by running `apply` after a refusal rollback in the harness.
- **A device's choice narrows what the device then offers.** Symptom: after choosing S24LE at 96000 the page listed only that format and rate. Cause: `audio.format` and `audio.rate` on the node limit its `EnumFormat`. Fix: when the person has a choice, the lists are the union with the card's reading in the engine's `choices.json`.
- **`Policy=auth_admin_keep` makes `kauth-policy-gen` print "Wrong policy" and the build stops.** KAuth's values are `yes`, `no`, `auth_self`, `auth_admin`; the keep behaviour is `Persistence=session`. Translated Name and Description lines with commas need quoting.
- **`pw-cat -p -` says "Format not recognised".** Reading raw samples from standard input needs `--raw`.
- **A rate pin is visible in the node properties.** `node.force-rate` on a running stream makes the graph and the sink run at that rate whatever `clock.allowed-rates` says; the sink's `Format` shows the graph's rate while it runs.
- **A Repeater whose model is reassigned every few seconds closes an open combo box.** Emit the device list's signal only when the list really changed and keep the volatile "format in use" in a separate map.
- **Kirigami.FormLayout rows lose their labels inside a Repeater delegate.** Use a GridLayout with explicit labels for per-device blocks.
- **No `kcmshell6` in Debian testing's `kde-cli-tools`.** Open the page with `systemsettings kcm_pulseaudio`.
- **Without a window manager Xvfb gives System Settings an 837x585 window.** Resize it with `xdotool search --onlyvisible --classname systemsettings windowsize`, after each page push.
- **`qml6` is the package `qml-qt6`; it treats the last argument as the file to load,** so the harness reads its steps from a fixed path (`/tmp/steps.json`) with `QML_XHR_ALLOW_FILE_READ=1`.
- **The lane's evidence folder is not writable by the container's uid 1001:** mount a world-writable scratch folder and copy the results out.
- **A published-repository gate cannot see a package that is staged and not yet published.** The link gate of the plasma-pa recipe failed on `Depends: sparky-stereo-audio`; the recipe now reads `SPARKY_LC_SIBLINGS_FILE` from `PREVIOUS_DEBS_DIR/siblings.txt`.
- **Docker refuses a bind mount whose source is a symlink** (`/var/tmp/sparky-repo-current`): pass the real path.

## Standards on the page, and what could be read at the source

AES5-2018 (r2023), read from its abstract on aes.org through the Wayback Machine (the standard itself is paid): "A sampling frequency of 48 kHz is recommended for the origination, processing, and interchange of audio programs employing pulse-code modulation. Recognition is also given to the use of a 44.1-kHz sampling frequency related to certain consumer digital applications, the use of a 32-kHz sampling frequency for transmission-related applications, and the use of a 96-kHz sampling frequency for applications requiring a higher bandwidth or more relaxed anti-alias filtering."
The display's list is the CTA-861 audio data block, read by the kernel as short audio descriptors (`drm_edid_to_sad()` in drivers/gpu/drm/drm_edid.c, with the sampling frequencies of `include/linux/hdmi.h`, Linux v7.3); CTA-861 itself, IEC 60958 and IEC 61937, IEC 60908 (the audio CD), the Blu-ray specification and the Bluetooth A2DP specification were not readable here, so the page makes no numeric claim from them.
The resampler quality scale, the buffer size and the dither have no standard on the page; it says so.
