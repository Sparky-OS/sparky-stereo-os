---
metadata:
  requires-packages: pipewire
name: audio
description: >-
  PipeWire, WirePlumber and KDE's Sound page in the edition: the audio house format (24-bit 48 kHz or more, float,
  SoXR), routing the streams KDE hides (node.virtual, node.linger, pw-loopback), sample rates and allowed-rates,
  passthrough (AC-3, DTS, bitstream over HDMI), virtual surround filter chains, RNNoise, MIDI and emulators, and the
  sound defaults package (rates from the devices, resampler quality, dither). Load it when a stream is missing from the
  Sound page, a loopback or virtual sink disappears, the rate is stuck at 48000, passthrough fails, VLC's PipeWire
  output plays silence until a seek, a game or emulator has no MIDI, a player or the sound system resamples, or apt
  keeps PipeWire back after Debian moved it (the AAC Bluetooth codec's exact libspa pin).
---

# Audio on Sparky Stereo OS

**Check freshness first.**
Written on 2026-10-10.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## Working recipe

1. Record source rate/channels, selected sink, negotiated format and the existing graph with pw-dump.
2. Change the graph or shared routing layer; keep a private PipeWire session for tests. Check reconnect and teardown for duplicate nodes.
3. Return the before/after graph and negotiated formats. Parameter updates alone do not prove rendered audio, latency or a physical speaker path.

Written on 2026-10-10 from measurements on the development machine; the parts marked **being built** are queued work, not yet in the edition.

## The house format for audio

PCM at the source's own rate, never reduced in the middle; the edition's floor is 24 bit at 48 kHz ([house formats](../../docs/house-formats.md)).
The sound server follows the source's rate instead of resampling, and a file whose rate the device cannot take is converted once, at the highest quality the processor carries.
Since ORDER 631 the package `sparky-stereo-audio` ships this as system defaults: [what it sets, where each value comes from, the traps and the proof rows](references/system-defaults.md).
Conversions happen at the edges only: the decoder on the way in, the device's format on the way out.

## System defaults (sparky-stereo-audio), in one screen

- Read a machine: `pw-metadata -n settings`, `pw-top -b -n 2`, `pw-dump`, and the kernel's `/proc/asound/cardN/{codec#M,eld#C.D,stream0}`; the package's own readout, in the person's language, is `sparky-stereo-audio show`.
- Rates: 44100 and 48000 Hz always (the audio CD; AES5's 48 kHz), plus every rate the computer's own devices take. PipeWire then follows the source and never picks a rate a sink cannot open.
- Quality: `resample.quality` 14 where one conversion of the heaviest kind (192000 to 48000 Hz) takes at most 20 percent of one core, measured at install; lower on a processor that cannot, never below PipeWire's 4.
- Format: PipeWire already opens a device in its best format (24 or 32 bit where there is); a 16 bit-only device gets triangular dither.
- A person's files win: the package's are `00-sparky-stereo-audio.conf`; `~/.config` and any later name in `/etc` override them.
- Proof: `bench/rig` plays five rates to four fake devices with the published set (4 of 20 rows right) and with the package (20 of 20).

## The Sound page's format and rate controls (ORDER 20)

- Read the automatic choice from the engine (`choices.json`, `sparky-stereo-audio show`), the devices from `pw-dump`, a display from `/proc/asound/cardN/eld#*`; write only `50-sound-page.conf` files in PipeWire's `key = value` form (the engine's `apply` only recognises that form as the person's).
- Every change is checked against the running graph or device and written back when it fails; the rig and the traps are in [sound-page-formats](references/sound-page-formats.md), the scripts in `bench/page-rig`.

## An HDMI sound device that "could not be read"

The problems list says "The sound devices NVidia, Generic could not be read" with the displays lit: the reader of sparky-stereo-audio 0.1.0 to 0.3.0 took an HDA output only when its node had a `Device:` line, and the kernel prints that line for an HDMI or DisplayPort codec only while a PCM is open.
Fixed in 0.3.1: a card with `eld#` files or HDMI/DP pins is a graphics card's audio, its outputs are the displays connected, what a display told is kept by its ELD identity, and a hotplug is noticed through the graphics driver's DRM event.
Fixtures must be copied idle as well as playing; a read made while PipeWire holds the sink looks fine. [Cause with the kernel's lines, the events, the rig and the traps](references/hdmi-sound-device-could-not-be-read.md).

## Why KDE hides some streams, and how to make them routable

- KDE's audio library (pulseaudio-qt, `src/stream_p.h`) marks a stream **virtual** when it has no client application, and KDE's Sound page and volume widget hide virtual streams (plasma-pa, `src/kcm/ui/main.qml` and `applet/main.qml`, the `VirtualStream` filter).
- A loopback or filter loaded as a module in `pipewire.conf.d` has no client, so it never appears, and its output cannot be chosen in KDE (pavucontrol lists it).
- Running it as a client program (`pw-loopback` from a systemd user service) gives it a client; pipewire-pulse still reports no client while the node carries `node.virtual = true` (the loopback's default), so set `node.virtual = false` in both stream property sets.
- Every edition loopback or filter carrying `node.dont-fallback = true` also carries `node.linger = true`. Its owner must explicitly unload it when its stream or target goes away; do not solve lifetime bugs by dropping the required linger property.
- The edition's plasma-pa 4:6.7.4-1+stereo3d1+lc1 extends the applet's existing virtual-device option to streams and adds an independent Sound-page option, both off by default; both are proved from the installed package.
- How the models, stream routes, isolated null-device rig and controls fit together: [KDE virtual streams](references/kde-virtual-streams.md).
- The staged +stereo3d2 successor adds optional "Listen to this device" and a combined recording source (output mix plus microphone); its rebuild uses a self-contained wired recipe, and both interfaces name owned streams in the person’s language.

## What PipeWire already ships

For the optional Listen and combined-source implementation and its content tests, see [KDE audio routes](references/kde-audio-routes.md).

PipeWire supplies convolution, SOFA spatialization, PSD upmix, LFE and noise-removal examples. Its named KEMAR example uses an external WAV file; Debian's libmysofa separately ships MIT KEMAR SOFA. Its two named matrix-surround examples are encoders, not decoders.
The ORDER 21 engine candidate adds automatic per-stream headphone insertion, optional passive matrix decoding and upmix, and per-output codec controls through the existing ELD and route state. [The commands, fake-device proof, licence boundaries and traps](references/surround-and-passthrough.md) distinguish what is implemented from what is accepted and published.
**Built since ORDER 23 (plasma-pa +stereo3d5):** a Speaker Setup page for every playback device whose current profile has more than two channels: the room at ITU-R BS.775-4's angles, a level that is the device's own channel volume (the value Show Channels shows, live, no file, no restart), a distance applied as a delay and bass management with a crossover as one PipeWire filter that exists only for those two and waits for its device, a pink noise test signal, and a sentence before Apply says sound stops for a moment. [The channel map, how each control is written and measured, the rig and the traps](references/speaker-page.md), the scripts in `bench/speaker-rig`.

## Formats, rates and passthrough

- Each device reports what it takes (ALSA through PipeWire); an [HDMI®](https://www.hdmi.org/resource/brand) sink's EDID lists the LPCM rates and depths and the encoded formats the TV accepts (CTA-861 audio data blocks).
- **Built since ORDER 20 (plasma-pa +stereo3d3):** the Sound page's "Sound Quality…" page shows each device's rates, formats, format in use, a display's audio blocks and a Bluetooth codec, pre-selects "Automatic (best this device supports)" and writes the person's choice as their own drop-in: [where each value is read and written, the rig and the traps](references/sound-page-formats.md). **Still to build:** pre-filling the passthrough codecs (AC-3, E-AC-3, DTS, TrueHD, DTS-HD) from the EDID instead of asking the user.
- Name features by what they do: "matrix surround, compatible with Dolby Surround and Pro Logic II content", never "Dolby" (a trademark). Ship only openly licensed head-response sets (MIT KEMAR first); users may import their own.

## MIDI and emulators

FluidSynth and the FluidR3 and TimGM6mb soundfonts are in Debian; the MuseScore General and OPL3 soundfonts are too.
Munt (MT-32), libADLMIDI and libOPNMIDI (FM synthesis) and DOSBox Staging are not, and require an archive and licence audit before edition packaging; MT-32 ROMs are the user's own. Debian already supplies a FluidSynth user service. The ORDER 21 table records the configuration and role entries still needed.
**Implemented and container-tested, awaiting review/publication (ORDER 735):** an idle-closing FluidSynth renderer, per-person font choice, bank-free emulator packages and optional app-center entries. See [MIDI out of the box](references/midi-out-of-the-box.md) for the route, proof boundaries, personal ROM requirements and traps.

## The AAC Bluetooth codec (our plugin beside Debian's PipeWire)

Debian builds PipeWire without Fraunhofer's AAC library, so the edition builds the one plugin, `pipewire-bluez5-codec-aac`, from PipeWire's own source against deb-multimedia's `libfdk-aac2`, pinned to the exact `libspa-0.2-bluetooth` it was built with.
The day Debian testing moves PipeWire, apt keeps PipeWire back on every installed edition until the codec is rebuilt: `watch-exact-pins.sh` sees it the same day, and [aac-codec](references/aac-codec.md) has the rebuild, the codec's own checks without a Bluetooth device (load, a tone through encode and decode, the decoder's buffer bound) and the traps.

## Bluetooth voice (HFP) and dongles

A headset microphone needs a SCO link, which is separate from A2DP.
When voice fails, find the refusing layer before changing a codec or a profile: the controller's buffers, the kernel's decision, the connect, the USB alternate settings, then the profile.
The commands, the two-machine test (a disposable gateway VM with the adapter, a real headset-side machine, a known tone as its microphone) and the traps are in [references/bluetooth-voice-dongles.md](references/bluetooth-voice-dongles.md); `bench/tone-check.py` and `bench/pwctl.py` are the checker and the card helper.
For the CSR clone whose SCO the kernel disables (0a12:0001, LMP subversion 0x2312), the same page has the kernel series that gives it a voice setting and its proof without the device: KUnit on `hci_cc_read_buffer_size()` and a virtual USB clone in a VM.

## Standards

AES5 (preferred sampling frequencies; its 2018 abstract: "A sampling frequency of 48 kHz is recommended for the origination, processing, and interchange of audio programs employing pulse-code modulation", with recognition of 44.1 kHz for consumer applications, 32 kHz for transmission and 96 kHz for higher bandwidth; read from the Wayback Machine, the standard itself is paid); the CD Red Book (44.1 kHz, 16 bit); IEC 60958 and IEC 61937 (PCM and encoded audio over S/PDIF and HDMI®); CTA-861 (audio data blocks in the EDID); ITU-R BS.775 (multichannel speaker layouts); AES69 (SOFA files for head-related transfer functions).

## Lessons from the lanes, October to November 2026

From the lanes of 25 October to 16 November 2026; add the next lesson here as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

- The Speaker Setup page's traps: a filter's playback stream with `node.dont-fallback` and no `node.linger` is destroyed by WirePlumber before its card exists, and the whole setup vanishes with nothing in the log (both flags together, bisected in `bench/speaker-rig/bisect-linger.sh`); a QML property named like its own id binds to itself (ORDER 20's "format in use" line never showed); moc stops at a raw string literal so a green run quietly has fewer rows; a QML `new RegExp(string)` with `\p{L}` throws and leaves Apply dimmed: [speaker-page](references/speaker-page.md#traps-symptom-cause-fix-how-found). (lane speaker-setup-kde-23)
- An HDMI card "could not be read" whenever nothing played: the kernel's `Device:` line exists only while a PCM is open, so a reader and a fixture made during playback pass and the idle machine fails ([hdmi-sound-device-could-not-be-read](references/hdmi-sound-device-could-not-be-read.md)). (lane audio-hdmi-read-757)
- The edition shipped Debian's PipeWire settings (48000 only, quality 4) until ORDER 631; before saying what a machine's graph does, read it (`pw-metadata -n settings`), never assume the defaults are ours. The traps of building the defaults and their rig (a container masks `/proc/asound`, an ALSA plugin needs `-DPIC`, nodes made from a WirePlumber script need a global table, dither on a 16 bit device costs bit perfection, a row that fails only in the green image) are in [system-defaults](references/system-defaults.md#traps-symptom-cause-fix-how-found). (lane system-audio-defaults-631)

- Result of the VLC PipeWire fix: MOV004.mp4 20 s three times, +stereo3d8 no sound and 44 to 50 flushes, +stereo3d9 sound at the track's first sound (1.08 s) with 0 flushes and 0 silences; after four seeks sound at every target; drift view +0.6 ms (MOV004) and +3.3 ms (48 kHz stereo). With 24 kHz audio resampled to 96 kHz VLC's own drift view reads -21 ms (old) and -27 ms (fixed) because the SoX resampler latency is not counted; VLC corrects only above 40 ms. (lane players-shared-layer)

HDMI®, HDMI® High-Definition Multimedia Interface and the HDMI® Logo are trademarks or registered trademarks of HDMI Licensing Administrator, Inc.
