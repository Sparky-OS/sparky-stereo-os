---
name: audio
description: Sound on Sparky Stereo OS: the audio house format, routing every stream in KDE, formats and rates from the hardware, passthrough by EDID, virtual surround, MIDI and emulators. Load it for any work on PipeWire, WirePlumber or KDE's Sound page.
---

# Audio on Sparky Stereo OS

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

- Each device reports what it takes (ALSA through PipeWire); an HDMI sink's EDID lists the LPCM rates and depths and the encoded formats the TV accepts (CTA-861 audio data blocks).
- **Being built:** KDE pages that show these, pre-select "Automatic (best this device supports)", and pre-fill the passthrough codecs (AC-3, E-AC-3, DTS, TrueHD, DTS-HD) from the EDID instead of asking the user.
- Name features by what they do: "matrix surround, compatible with Dolby Surround and Pro Logic II content", never "Dolby" (a trademark). Ship only openly licensed head-response sets (MIT KEMAR first); users may import their own.

## MIDI and emulators

FluidSynth and the FluidR3 and TimGM6mb soundfonts are in Debian; the MuseScore General and OPL3 soundfonts are too.
Munt (MT-32), libADLMIDI and libOPNMIDI (FM synthesis) and DOSBox Staging are not, so the edition packages them from upstream; MT-32 ROMs are the user's own.
**Being built:** a soundfont synthesizer running as a user service so emulators and games play MIDI out of the box.

## Standards

AES5 (preferred sampling frequencies; 48 kHz for professional use); the CD Red Book (44.1 kHz, 16 bit); IEC 60958 and IEC 61937 (PCM and encoded audio over S/PDIF and HDMI); CTA-861 (audio data blocks in the EDID); ITU-R BS.775 (multichannel speaker layouts); AES69 (SOFA files for head-related transfer functions).
