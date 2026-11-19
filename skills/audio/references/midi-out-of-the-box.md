# MIDI ready out of the box

A MIDI file and a MIDI port are different playback paths.
VLC can already synthesize a file internally with FluidSynth and TimGM6mb while PipeWire has no synthesizer destination for a game or keyboard.
Test both before changing any file association.

## The candidate packages

ORDER 735 adds `sparky-stereo-midi` beside `sparky-stereo-audio` 0.3.0.
The former is a small native libfluidsynth/PipeWire renderer; the latter retains the existing audio engine and adds its MIDI command, translations and dedicated user unit.
This is implemented and tested in isolated containers, awaiting edition review and publication.
Real USB hardware and a real desktop login are separate tests.

The dedicated `sparky-stereo-midi.service` starts `sparky-stereo-audio midi --serve` using Debian's libfluidsynth directly.
Debian's CLI package cannot be the minimal dependency: its Qsynth recommendation pulls the 119.6 MB FluidR3 font even when TimGM6mb is already installed.
An actual APT simulation exposed that chain; the library-backed service avoids it.
Debian's existing fluidsynth.service remains independent and is not overridden or enabled.
Turn this service off before selecting another General MIDI daemon.
The unit uses Type=notify and requests PipeWire and WirePlumber.
A vendor dependency of default.target starts it at login.
The wrapper sends READY=1 after the MIDI input has opened and its font has loaded.
The problems engine stores a startup or rendering failure.
An offline target-graph check is required; is-enabled alone does not show vendor-directory dependencies.

ALSA programs see a FluidSynth sequencer client called `Sparky General MIDI` when `/dev/snd/seq` is available.
The package requests `snd_seq` through modules-load on the installed system; a container test never loads a module on the host.
Without that device, the renderer exposes a PipeWire JACK MIDI input named `sparky-midi:midi_00` and reports that ALSA-only games still need the sequencer device.
A PipeWire MIDI producer and one explicit `pw-link` connection provide the container surrogate.
This proves MIDI event delivery and rendering, not enumeration of a physical USB interface.

The MIDI input stays alive while the audio stream exists only for notes and their effects tail.
FluidSynth 2.6.1 no longer supports changing its synthesis rate after creation.
The renderer therefore selects the maximum rate its settings API supports, 96000 Hz in the tested version, and seventh-order interpolation.
Its PipeWire stream requests no graph rate; PipeWire converts once at the graph edge using the edition's existing quality policy.
After voices finish and the rendered output stays below half a signed 24-bit step for half a second, the stream closes.
The real output can then suspend and the next PCM file can choose its rate.
PipeWire changes device rate while idle; this does not promise a rate change in the middle of several active streams.

## Choices

```sh
sparky-stereo-audio show
sparky-stereo-audio midi --font auto
sparky-stereo-audio midi --font /absolute/path/personal.sf2
sparky-stereo-audio midi --driver auto
sparky-stereo-audio midi --connect yes
sparky-stereo-audio midi --connect no
sparky-stereo-audio midi --service off
sparky-stereo-audio midi --service on
sparky-stereo-audio midi --play /absolute/path/music.mid
```

TimGM6mb is the minimal dependency.
Automatic follows Debian's `default-GM.sf3` alternative first, then the SF2 fallback, so an installed higher-priority GM font is used.
This order matters: MuseScore General registers only the SF3 group, while TimGM6mb and FluidR3 register both.
An explicit per-person font wins; a person's existing `~/.config/fluidsynth` SOUND_FONT is respected in Automatic.
The JSON choices live under the person's XDG configuration directory.
A failed service restart rolls back a changed choices file.
No file-player default is changed.

The app center offers FluidR3 GM, MuseScore General HQ, MuseScore General Small and OPL3 SoundFont as optional installs, using the existing APT planner to say download and installed sizes before installation.
The OPL3 SoundFont is a sampled SoundFont, not an OPL chip emulator.
No install-time downloader or soundfont copy is added to the edition package.

Automatic hardware MIDI connection remains off.
The explicit connection is visible and changeable with PipeWire tools, and FluidSynth's connection option is exposed by the command.
No design found: Daniel's call on enabling connections automatically.
The two-versus-four-processor dense-file measurement does not establish a universal weak-machine boundary.
Propose two or fewer logical processors as a conservative light-font default, but retain today's alternatives behavior until Daniel decides; processor speed, voice count and available memory matter too.

## One bridge

WirePlumber's `monitors/alsa-midi.lua` already creates PipeWire's `api.alsa.seq.bridge` and watches the sequencer device.
Do not start a2jmidid beside it.
a2jmidid remains a Debian offer for a separately managed JACK environment, not a dependency or enabled second bridge here.
ALSA/PipeWire device access remains owned by the existing desktop device policy.

## Optional emulators and their data

- Munt uses the person's MT-32 control and PCM ROMs selected in its own ROM settings.
  No ROM is included, acquired or downloaded.
  The Qt frontend forwards a missing-ROM failure to the translated problems engine.
- libADLMIDI is built with embedded banks and its demo player disabled.
  All supplied banks and generated bank databases are excluded before assembling the source package.
  A compatible consumer must provide an authorized WOPL bank.
- libOPNMIDI is a library for compatible consumers with their own WOPN bank.
  Supplied banks and Yamaha rhythm PCM ROM tables are excluded; GENS and Nuked OPN2 are enabled without OPNA rhythm emulation.
  The API does not make an unrelated emulator use this library automatically.
- DOSBox Staging defaults to its FluidSynth backend and Debian's default GM SoundFont.
  The person can select another device/font in its own configuration.
  Its MT-32 backend still needs personal ROMs and reports their absence through the problems engine.
  Its licensed guest DOS utilities, keyboard layouts and CPI fonts retain their terms and matching upstream source snapshots.

Read Debian ITP 1123050 and the complete libADLMIDI issue 301 before revisiting bank distribution.
The bank-free build avoids assuming that a bank called clean has independently verified redistribution terms.
DOSBox Staging ITP 973822 includes older guest-binary/source concerns; bug 825604's October 2026 maintainer reply says the ITP stalled after dependency work.
That is not a current blanket licence rejection.
Munt and libOPNMIDI have no documented Debian exclusion reason found in this audit; absence is not a ban.

## Proof and traps

Use the existing audio bench rig in a container with no host sound devices, PipeWire socket or desktop settings mounted.
Start the installed user-unit command with a private notification socket and require READY=1.
Capture real PCM at the fixture output; require nonzero sample data, then absence of the synthesizer audio node and a suspended fixture sink.
Run the 44100 and 96000 Hz rig rows before and after and compare actual captured samples, not just advertised formats.
Stop the synth after the green test and require the MIDI producer to fail without a target.
Temporarily hide the font inside the container, restore it in a finally block, and require both a failed command and the stored problem in all ten languages.
An offline systemd target-graph check proves dependencies; a direct command/notification test does not claim a real systemd login was exercised.

- Symptom: a synth renders silence forever after notes finish, or stale audio grows on every callback.
  Cause: `fluid_synth_process` adds to caller-owned buffers; it does not clear them.
  Fix: clear each output segment, mix the effects into it, and measure silence on the completed output.
  Found by tracing voice count to zero while output peak never decayed and checking the upstream rendering API's buffer rule.
- Symptom: a dense MIDI file uses almost a whole core even while events wait for their sample time.
  Cause: the control loop polled a nonempty queue instead of waiting for the renderer or a new MIDI event.
  Fix: wait on the condition variable unless opening, closing or failing actually needs work.
  Found by the required dense-file CPU test rather than the single-note proof.
- Symptom: a PipeWire filter advertises a new rate but produces no MIDI audio.
  Cause: FluidSynth's old live-rate setter is unsupported in 2.6.1.
  Fix: choose the supported synthesis rate before creating the synth and use one PipeWire edge conversion.
  Found by checking the library's error output and a zero-sample capture; a negotiated rate alone was a false green.
- Symptom: a virtual MIDI producer exists but no notes arrive.
  Cause: its unconnected initial event burst can be lost, and WirePlumber does not create an automatic target for this custom Midi/Sink class.
  Fix: create one explicit link, include a lead-in in dense timing fixtures, and require captured audio as well as a port list.
  Found by a no-audio dense test that misleadingly reported tiny CPU use.
- Symptom: a named PipeWire MIDI link fails.
  Cause: `pw-midiplay`'s output is `output_1`, not `out_0`.
  Fix: discover the port and direction from `pw-dump` or `pw-link` rather than guessing its suffix.
- Symptom: DOSBox Staging's Meson build tries to copy a nonexistent shaders/misc directory.
  Cause: the current project uses CMake; leftover Meson files are obsolete.
  Fix: read its tagged build-linux instructions, use system libraries with CMake, and carry John Novak's upstream system-zlib detection fix when zlib-ng is absent.
- Symptom: a translated failure prints correctly but the stored-text check returns English.
  Cause: the problems engine's text command needs its explicit `--lang` argument for that probe.
  Fix: request each catalog language and compare the stored message with the engine's translated output.

## Primary records

[FluidSynth audio rendering](https://www.fluidsynth.org/api/group__audio__rendering.html), [MIDI settings](https://www.fluidsynth.org/api/settings_midi.html), [idle driver request](https://github.com/FluidSynth/fluidsynth/issues/1630), [Debian libADLMIDI ITP](https://bugs.debian.org/1123050), [bank audit](https://github.com/Wohlstand/libADLMIDI/issues/301), [DOSBox Staging ITP](https://bugs.debian.org/973822), [Debian DOSBox maintainer record](https://bugs.debian.org/825604), [upstream system-zlib fix](https://github.com/dosbox-staging/dosbox-staging/commit/482477a6f48ba30520920c0a09732371ba1cd772).

- Symptom: the supposedly small default announces a 120 MB installation despite a TimGM6mb dependency.
  Cause: Debian fluidsynth recommends Qsynth, which recommends FluidR3 directly.
  Fix: use Debian libfluidsynth with the small renderer's own user unit; leave the CLI package optional and independent.
  Found by running the actual app-center APT planner against a healthy fixture package status, including Recommends as the install action does.
