---
metadata:
  requires-packages: pipewire
name: audio
description: >-
  PipeWire, WirePlumber and KDE's Sound page in the edition: the audio house format (24-bit 48 kHz or more, float,
  SoXR), routing the streams KDE hides (node.virtual, node.linger, pw-loopback), sample rates and allowed-rates,
  passthrough (AC-3, DTS, bitstream over HDMI), virtual surround filter chains, RNNoise, MIDI and emulators. Load it
  when a stream is missing from the Sound page, a loopback or virtual sink disappears, the rate is stuck, passthrough
  fails, VLC's PipeWire output plays silence until a seek, a game or emulator has no MIDI, or a player resamples.
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
The sound server follows the source's rate instead of resampling: PipeWire's `default.clock.allowed-rates` set to `[ 44100 48000 88200 96000 176400 192000 ]`, with the default rate the device's best (96 kHz on the development machine's Sound Blaster).
Conversions happen at the edges only: the decoder on the way in, the device's format on the way out.

## Why KDE hides some streams, and how to make them routable

- KDE's audio library (pulseaudio-qt, `src/stream_p.h`) marks a stream **virtual** when it has no client application, and KDE's Sound page and volume widget hide virtual streams (plasma-pa, `src/kcm/ui/main.qml` and `applet/main.qml`, the `VirtualStream` filter).
- A loopback or filter loaded as a module in `pipewire.conf.d` has no client, so it never appears, and its output cannot be chosen in KDE (pavucontrol lists it).
- Running it as a client program (`pw-loopback` from a systemd user service) gives it a client; pipewire-pulse still reports no client while the node carries `node.virtual = true` (the loopback's default), so set `node.virtual = false` in both stream property sets.
- With a client program, do **not** set `node.linger = true`: the nodes would outlive each restart and multiply. Keep `node.dont-fallback = true` on a stream that must never fall back to another device (to avoid feeding a card its own output), and let systemd restart the client (`Restart=always`) when WirePlumber removes the stream because its target is gone.
- **Being built:** a "Show virtual streams" option on KDE's Sound page, "Listen to this device" for any input, and a combined recording source (the output mix plus a microphone).

## What PipeWire already ships

`/usr/share/pipewire/filter-chain/` holds ready filter graphs: binaural 5.1 for headphones with the MIT KEMAR recordings through libmysofa (`sink-virtual-surround-5.1-kemar.conf`), 7.1 with HeSuVi head responses (`sink-virtual-surround-7.1-hesuvi.conf`), matrix surround decoders (`sink-dolby-surround.conf`, `sink-dolby-pro-logic-ii.conf`), upmixing (`sink-upmix-5.1-filter.conf`), a subwoofer channel (`sink-make-LFE.conf`) and microphone noise removal (`source-rnnoise.conf`).
**Being built:** switching them on by themselves (headphones plus multichannel content), and a speaker setup page per multichannel device (levels in dB, test signal, distance as delay, bass management).

## Formats, rates and passthrough

- Each device reports what it takes (ALSA through PipeWire); an [HDMI®](https://www.hdmi.org/resource/brand) sink's EDID lists the LPCM rates and depths and the encoded formats the TV accepts (CTA-861 audio data blocks).
- **Being built:** KDE pages that show these, pre-select "Automatic (best this device supports)", and pre-fill the passthrough codecs (AC-3, E-AC-3, DTS, TrueHD, DTS-HD) from the EDID instead of asking the user.
- Name features by what they do: "matrix surround, compatible with Dolby Surround and Pro Logic II content", never "Dolby" (a trademark). Ship only openly licensed head-response sets (MIT KEMAR first); users may import their own.

## MIDI and emulators

FluidSynth and the FluidR3 and TimGM6mb soundfonts are in Debian; the MuseScore General and OPL3 soundfonts are too.
Munt (MT-32), libADLMIDI and libOPNMIDI (FM synthesis) and DOSBox Staging are not, so the edition packages them from upstream; MT-32 ROMs are the user's own.
**Being built:** a soundfont synthesizer running as a user service so emulators and games play MIDI out of the box.

## Bluetooth voice (HFP) and dongles

A headset microphone needs a SCO link, which is separate from A2DP.
When voice fails, find the refusing layer before changing a codec or a profile: the controller's buffers, the kernel's decision, the connect, the USB alternate settings, then the profile.
The commands, the two-machine test (a disposable gateway VM with the adapter, a real headset-side machine, a known tone as its microphone) and the traps are in [references/bluetooth-voice-dongles.md](references/bluetooth-voice-dongles.md); `bench/tone-check.py` and `bench/pwctl.py` are the checker and the card helper.

## Standards

AES5 (preferred sampling frequencies; 48 kHz for professional use); the CD Red Book (44.1 kHz, 16 bit); IEC 60958 and IEC 61937 (PCM and encoded audio over S/PDIF and HDMI®); CTA-861 (audio data blocks in the EDID); ITU-R BS.775 (multichannel speaker layouts); AES69 (SOFA files for head-related transfer functions).

## Lessons from the lanes, October to November 2026

From the lanes of 25 October to 6 November 2026; add the next lesson here as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

- Result of the VLC PipeWire fix: MOV004.mp4 20 s three times, +stereo3d8 no sound and 44 to 50 flushes, +stereo3d9 sound at the track's first sound (1.08 s) with 0 flushes and 0 silences; after four seeks sound at every target; drift view +0.6 ms (MOV004) and +3.3 ms (48 kHz stereo). With 24 kHz audio resampled to 96 kHz VLC's own drift view reads -21 ms (old) and -27 ms (fixed) because the SoX resampler latency is not counted; VLC corrects only above 40 ms. (lane players-shared-layer)

HDMI®, HDMI® High-Definition Multimedia Interface and the HDMI® Logo are trademarks or registered trademarks of HDMI Licensing Administrator, Inc.
