# The sound defaults of the edition: reading a machine's graph, what ships, the traps

**Check freshness first.**
Written on 2026-11-16 by Claude Sonnet 5.5 (ORDER 631), on PipeWire 1.6.9-2, WirePlumber 0.5.19-1 and the package sparky-stereo-audio 0.1.0.
PipeWire's settings change from release to release: read `man pipewire-props` of the installed version before trusting a name here.

Daniel, 2026-10-10 (ORDER item 20): "bit depth and sample rate per hardware and for the internal graph, pre-filled from the hardware and the standards, user freedom to spend processing on audio or elsewhere, auto-detection that never compromises capable hardware but provides on weak hardware".
Daniel, 2026-11-16: "hi fidelity audio is a must across all audio systems, leaving only the file that's lower or higher to be resampled with a decent quality".

## Recipe: read a machine's graph and device rates

1. What the graph may do: `pw-metadata -n settings` shows `clock.rate` (idle rate), `clock.allowed-rates`, `clock.force-rate` (0 means not forced). Debian's stock is 48000 and `[ 48000 ]`.
2. What it does now: `pw-top -b -n 2` lists, per running node, its RATE and FORMAT (the driver row is the graph); `pw-dump` gives each node's `info.params.Format` (the rate and format it runs in) and `EnumFormat` (what a device offers, as a rate range min..max, so a gap in the list is not visible there).
3. What a stream carries: the stream node's `info.props` shows `resample.quality` only when something set it (unset means PipeWire's 4); a stream with a rate different from the driver's is converted in its own adapter, a driver whose device was opened at another rate converts in the sink's adapter. Count the conversions: one at most.
4. What a device really takes: the kernel's own text, `/proc/asound/cardN/codec#M` (HDA: `rates [0x..]: ...` and `bits [0x..]: ...` under each `Audio Output` converter; an analog or S/PDIF output is named by its `Device:` line, but a graphics card's HDMI or DisplayPort codec has that line only while a PCM is open and lists its rates under `Default PCM:` when a converter has no `PCM:` of its own, see [the HDMI reference](hdmi-sound-device-could-not-be-read.md)), `eld#C.D` (a connected display's audio block: `monitor_present`, `eld_valid`, then `sadN_coding_type [0x1] LPCM`, `sadN_rates`, `sadN_bits`) and `stream0` (USB: `Format:`, `Rates:` as a list or `LOW - HIGH (continuous)`, `Bits:`; format of sound/usb/proc.c). Read them as the person's user; nothing opens a device.
5. What the package decided and why, in the person's language: `sparky-stereo-audio show`; the files are `00-sparky-stereo-audio.conf` in `/etc/pipewire/pipewire.conf.d`, `client.conf.d`, `pipewire-pulse.conf.d` and `/etc/wireplumber/wireplumber.conf.d`.
6. The sample the device was opened with: nothing but the device tells it (PipeWire's `Format` is the graph side). On a real card read `/proc/asound/cardN/pcmMp/sub0/hw_params` while it plays; in the rig the fake device writes `OUT.params`.

## What PipeWire and WirePlumber already do (the reconcile, measured in the rig)

- With `default.clock.allowed-rates` listing several rates, the graph switches to the rate a stream asks for (`node.rate`, `node.latency` N/RATE), and it **never picks a rate the sink cannot open**: with the full standards list and a 48 kHz-only device the graph stayed at 48000 for every source; for a 32 kHz source on a device taking 32 to 96 kHz with a list that did not hold 32000 it ran at 96000 (a whole multiple), converting once.
- A device is opened "with a rate as close to the graph rate as possible" and in "the best possible bits (32/24/16/8)" (`man pipewire-props`, ALSA device properties `audio.rate`, `audio.format`): the 24 bit floor needs no setting, and forcing `audio.format` would only take 32 bit away.
- The sink's own adapter converts when the device cannot take the graph rate; `audio.allowed-rates` on a device node limits the rates it is opened with (default empty: any).
- Debian ships `/usr/share/pipewire/pipewire.conf.avail/10-rates.conf` (`[ 44100 48000 88200 96000 ]`) as an example nobody enables; nothing in the stock install sets a rate list, a quality or dither.
- `dither.method` is applied only to a conversion into fewer than 24 bits.

## What the package sets, and where each value comes from

| Setting | Value | Source |
| --- | --- | --- |
| `default.clock.allowed-rates` | 44100 and 48000 always, plus every rate the computer's devices take (the union), the standards' list when a card cannot be read | AES5-2018 abstract: "A sampling frequency of 48 kHz is recommended for the origination, processing, and interchange of audio programs employing pulse-code modulation. Recognition is also given to the use of a 44.1-kHz sampling frequency related to certain consumer digital applications, the use of a 32-kHz sampling frequency for transmission-related applications, and the use of a 96-kHz sampling frequency for applications requiring a higher bandwidth or more relaxed anti-alias filtering." (aes.org standards page for AES5-2018 (r2023), read from the Wayback Machine); the audio CD (Red Book, IEC 60908): 44.1 kHz, 16 bit; Blu-ray: up to 192 kHz, 24 bit LPCM; a display's LPCM rates: CTA-861 short audio descriptors, enumerated by the kernel as `HDMI_AUDIO_SAMPLE_FREQUENCY_*` in include/linux/hdmi.h (32, 44.1, 48, 88.2, 96, 176.4, 192 kHz) and read by drm_edid_to_sad() |
| `default.clock.rate` | 48000 where any output takes it, else 44100, else the highest | ORDER item 20 (c): "the edition's floor: 24 bit, 48 kHz" |
| `resample.quality` (client streams, pipewire-pulse, sink adapters of ALSA and Bluetooth) | the highest of 14, 13, 12, 10, 8, 6, 4 whose heaviest conversion (192000 to 48000 Hz, stereo, PipeWire's own `spa-resample`) takes at most 20 percent of one core, never below 4 | ORDER item 20 (b) "resampler quality" and (c) "provides on weak hardware"; the 20 percent figure is ours, no recorded design |
| Sample format | PipeWire's own choice (best bits) | `man pipewire-props` |
| `dither.method = triangular` on `alsa_output.*` | TPDF, effective only below 24 bit | Lipshitz, Wannamaker and Vanderkooy, "Quantization and Dither: A Theoretical Survey", JAES 40(5), 1992 (not retrieved here); measured in the rig: a 1:2:1 spread of -1, 0 and +1 steps of 16 bit |

Resampler cost, PipeWire 1.6.9's `spa-resample -q N`, 20 s of stereo float, processor time as a share of one core in real time, on a 12-thread desktop processor with a kernel build running (so a ceiling): 192000 to 48000 Hz: q4 0.6 percent, q8 1.5, q10 1.85, q12 2.85, q13 9.5, q14 10.65; 44100 to 48000 Hz: q4 0.2, q12 0.65, q13 2.4, q14 2.7. Quality 13 and 14 cost four times quality 12. Measured with the package's own five-second test: 10.4 to 13.6 percent at q14 on the same machine, so the limit sits above the measurement noise of a capable processor and well below a small machine's.

## Who wins

PipeWire reads `pipewire.conf.d`, `client.conf.d` and `pipewire-pulse.conf.d` from `/usr/share/pipewire`, then `/etc/pipewire`, then `~/.config/pipewire`; WirePlumber reads `/usr/share/wireplumber`, `/etc/wireplumber`, then `~/.config/wireplumber`; inside a folder the files are read in name order and the last value wins. The package's files start with 00, so anything of the person's wins (measured: `~/.config/pipewire/pipewire.conf.d/99-clock-rates.conf` with `[ 44100 96000 ]` kept the graph in that list, a client quality of 7 and a WirePlumber rule with `resample.quality = 6, dither.method = none` reached the nodes). `monitor.alsa.rules` and `monitor.bluez.rules` arrays are appended across fragments, so a person's later rule updates the same properties after the package's. `sparky-stereo-audio apply` never sets a runtime value for a key a person's own file sets.

## Traps (symptom, cause, fix, how found)

- **The detection finds no card in a container.** Docker masks `/proc/asound` with an empty tmpfs (`mount | grep asound`). Point `SPARKY_STEREO_AUDIO_PROC` at a fixture tree (the rig's `proc-asound/`, built from the real files' format) for the install and the tests.
- **A fake ALSA device cannot be opened: `undefined symbol: snd_dlsym_start`.** An ioplug plugin must be built with `-DPIC`; without it alsa-lib's header builds the static-link form.
- **`IOPLUG: invalid parameter type 0`.** The access type takes a list (`snd_pcm_ioplug_set_param_list(.., SND_PCM_IOPLUG_HW_ACCESS, ..)`), not a min and a max.
- **`hdmi is not a compound`.** `hdmi` is a predefined ALSA name; name the fake devices `sa_...`.
- **WirePlumber nodes created from a script vanish (`unknown resource`).** The `Node("adapter", props)` objects were collected with the script's locals; keep them in a global table. The stand-in monitor (`rig-alsa-nodes.lua`) applies `monitor.alsa.rules` with `JsonUtils.match_rules_update_properties`, the call monitors/alsa.lua makes, so a rule reaches the rig's nodes exactly as it reaches a card's.
- **A green run that never tested the new device.** `update-rig.sh` under `set -e` stopped at a failed `apt-get` and never committed the image, so the rig lacked `sa_hot` and the headset-hook row failed in green only. A row that fails in green and passes in red: run the same row on the image before the package (bisect), and check that the node exists (`pw-cli ls Node`).
- **`dither.noise = 2` alone alternates between two values; with `dither.method = triangular` it spreads over -2..+2 steps.** The method alone (noise 0) is the textbook TPDF of plus or minus one step. Found with the error histogram of `proof.py dither`.
- **Dither costs bit perfection on a 16 bit device with a 16 bit file.** PipeWire cannot tell that no word length is lost; red is exact, green spreads over -1, 0, +1. The default keeps the dither (24 bit files, and every software volume below 100 percent, need it); the person's `dither.method = none` rule gives the exact path back.
- **`jack.conf` has `jack.properties` and no `stream.properties`.** JACK clients run at the graph's rate and are not converted, so the package writes no JACK file.
- **A Lean Code build says `Source output exists`.** `lean.standalone` writes a fresh output folder; clean the scratch output between builds. It also needs the recipe's authoring folder tracked by git (commit first).
- **`lc1: build record NOT complete, unrecorded: buildinfo`.** A hand-assembled package (dpkg-deb) has no `.buildinfo`; the record says so and nothing is guessed. The host facts come from `build-provenance.sh` (`sparky_provenance_init IMAGE` before the `docker run`, `"${SPARKY_PROV_ARGS[@]}"` on it).
- **A package's own programs and tests run in a container, never on the host.** The detection only reads `/proc/asound`, but the house rule holds for every package program.

## The proof rows as scripts (bench/rig)

`pcm_sa631.c` is a fake ALSA sound device that takes exactly the rates and formats it is told, paces itself at the wall clock and writes what it received to a file (and the parameters it was opened with to `OUT.params`). `asound.conf` defines four of them (a DAC taking 44.1 to 192 kHz in 16, 24 and 32 bit, a 48 kHz-only device, a 16 bit-only device, an HDMI television taking 32 to 96 kHz) and a Bluetooth-like and a hot-plugged one. `rig-alsa-nodes.lua` turns them into sinks through WirePlumber's own rules. `session.sh` starts a private PipeWire and WirePlumber (and pipewire-pulse with `SA631_PULSE=1`) as an unprivileged user. `proof.py` plays a deterministic 24 bit file (`mkwav.py`) at a given rate to a device with `pw-cat` or `paplay` and prints one JSON row: the graph's rate, the stream's rate and quality, the rate and format the device was opened with, whether a conversion happened and where, and whether the samples that reached the device equal the file's bit for bit. `table.py` judges the rows against the design: a rate the device takes plays unconverted, bit for bit on a 24 or 32 bit path; any other rate is converted once, to a rate the device takes, at the chosen quality. `scenarios.sh` runs the matrix and the other rows (pipewire-pulse, Bluetooth-like sink, dither on a 24 bit and a 16 bit file, a person's own files, `apply` after a hot-plug, a weak processor, the headset hook of sparky-stereo-hardware, the What U Hear bridge as a `pw-loopback` client).

Run: build the image of the published set (Debian's PipeWire and WirePlumber, the edition's repository, the rig files), `scenarios.sh IMAGE red EVIDENCE`; install the staged package by apt in a copy (`prep-green.sh`), `scenarios.sh IMAGE green EVIDENCE`; `table.py EVIDENCE`. The result of ORDER 631: the published set follows the design in 4 of 20 rows (the four 48 kHz files), the package in 20 of 20.

## Found, left as it is

- A `pw-loopback` bridge (What U Hear) that is running holds the graph at 48000 Hz: its two streams ask for the default rate and are the first to start, so a 96 kHz file played to the captured sink is converted once to 48000, with the published set and with the package alike. The bridge is a person's own file; to follow the source it needs its streams to take their rate from the graph, which was not changed.

## Not proven (as of 2026-11-16)

A real sound card, a real HDMI display, Bluetooth codecs (the rule for `bluez_output.*` is proved on a stand-in sink only), the WirePlumber rules on a node made by the udev monitor (the rig applies the same rules by the same call), a weak processor (the rule is proved with a given cost, the measured figures are one machine's), the systemd units at a real boot and login (their syntax is verified).
