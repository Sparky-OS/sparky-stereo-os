# KDE input monitoring and combined recording

Implementation work on Plasma 6.7.4, pulseaudio-qt 1.9.0 and PipeWire 1.6.9, November 2026.
The virtual-stream controls ship in plasma-pa +stereo3d1; the +stereo3d2 successor adds the two optional routing features, staged for review.

## Working recipe

Use the [plasma-pa recipe](https://github.com/Sparky-OS/sparky-stereo-os-build/tree/main/sparky-os/upstream/plasma-pa) in a throwaway container, without sound devices or a host session socket.
Give the test user a private home, runtime directory, D-Bus and display, and disable core dumps.
For prototype checks build into `/opt/order19b`. For package proof remove prototype prefixes and set `PA19_INSTALLED=1` so the probes use only installed files. Use a new WORK for every session.

1. Run `dbus-run-session -- python3 RECIPE/prototype-mix.py` to check combine-stream source mode with two independent tones.
2. Run `dbus-run-session -- python3 RECIPE/rig-routes.py WORK` to check the actual KDED interface, content, recording coexistence, negative output, repeats, missing-device recovery and service lifetime.
3. Run `dbus-run-session -- python3 RECIPE/rig-route-ui.py WORK 1`, then a fresh session at `1.25`, to drive the real Sound page and capture its controls and errors.
4. Install the sound-defaults package and run a 96 kHz source through the same route; inspect `pw-top` and `pw-dump` during playback, including the source, route and driver formats.
5. Repeat from the installed successor package, with the prototype prefix removed, before calling the package tested.

Both features are initially off.
The page chooses an input and output explicitly; a missing target stops its route and reports the missing device.
The KDED module owns the helper independently of the settings window.
Its preferences are in its own `plasmaparc` groups; no PipeWire or WirePlumber file is rewritten.
Do not set a fixed rate or latency on a PipeWire loopback, and do not add `node.linger` to client-owned streams.

## Traps and how they were found

- **A combine-stream module never publishes a source when hosted with `pw-cli -d`.** That switch makes pw-cli a daemon with its own core. Use `pw-cli -m load-module libpipewire-module-combine-stream JSON`; `-m` keeps the client alive after loading. Found by comparing the missing Pulse source with pw-cli's argument parsing and module lifetime in the 1.6.9 source.
- **The combined source exists but its content is unproved.** Map each contributor's channels to the same combined channels, set `stream.capture.sink=true` only for the output-monitor rule, and record both independent tones through the resulting single source. PipeWire's module merges each rule's properties and adds overlapping channels through `mix_f32` and `ringbuffer_mix`; the two-tone recording checks that interpretation.
- **Listen says Active but remains silent until another application records or plays.** Setting `node.passive=true` on both monitoring streams leaves their devices suspended. Continuous monitoring must activate its streams. The idle graph exposed this defect even though the earlier simultaneous-recording content test passed.
- **A native PulseAudio combined sink fails with `Invalid properties`.** Module arguments and property lists are separate parsers. `pa_modargs_get_proplist()` intentionally reads the raw argument, so JSON-escaping both nested levels leaves backslashes in the property list. Use outer single quotes and inner double-quoted property values, escaping literal apostrophes. Found by the module error and `modargs.c`/`proplist.c`, then the native-server content run.
- **An exact-bin tone test reports too little native PulseAudio audio.** `module-loopback` adjusts its rate to compensate independent clocks. State a detection band and retain the measured result; the rig uses 0.5 percent. A two-phase test isolates Listen from Combined Recording so monitoring the microphone does not also add it to the chosen output's mix during the combined-source measurement.
- **Hidden controls appear in an accessibility tree but have no component interface.** Select a matching accessible object with real positive component extents before clicking it. Found when a hidden playback delegate's monitoring selector matched before the visible input selector.
- **Moving an owned stream leaves a saved choice stale.** Route KDE's page selector, widget menu and drag action through the owning service for these streams, with a stable route ID, and verify the new target on the server. Native PulseAudio's `source_dont_move` and `sink_dont_move` protect against automatic rescue; the service recreates its own module at the requested target. Other applications' streams keep their existing move operation.
- **The default-input assertion compares `@DEFAULT_SOURCE@` with a real microphone.** A newly published source does not mean WirePlumber has selected its default yet. Wait for the initial default before taking the control value. The saved before/after values exposed this rig race; creating the combined source must keep the established choice.
- **Native teardown reports failure although the module is gone.** Removing a source can automatically unload a loopback before the Qt module cache receives its removal event. After a failed unload, query the server's actual module list before retaining the ID as a failure. Found by the missing-input row: the source had gone, but the immediate cached ID still existed.
- **PulseAudio's sample specification says 48 kHz while PipeWire runs at 96 kHz.** The compatibility layer can report a nominal rate for a graph-following stream. Read PipeWire's Format and the driver/stream rows in `pw-top`; do not force a rate from the compatibility layer's value. The 96 kHz content row showed graph-following F32P route parameters and the actual 96 kHz driver separately.

The native backend unloads only IDs it created, marks modules with a per-user owner token and reclaims its own orphan modules after a service restart.
Keep native PulseAudio's clock compensation distinct from PipeWire's graph-following streams when interpreting a frequency or latency measurement.
No null-device test proves a microphone, speaker, hardware loopback or physical end-to-end latency.

- **The microphone is doubled when its monitoring output is also recorded.** Combined Recording adds the literal output mix plus microphone; Listen can put the same microphone into that mix. The page warns when both choices match. Verify the warning appears after moving the owned playback stream to the selected combined output and clears when moved away. Found by the two-tone recording with both features enabled; keep independent feature content phases to avoid confusing this interaction with a mixer defect.
- **A null-device latency number is presented as hardware latency.** State the graph and capture method. The simultaneous four-channel noise marker measured 2048 samples at 48 kHz (42.67 ms) through the synthetic monitoring/probe branches, correlation 1.0. PulseAudio reported about 197 ms of loopback plus sink buffering in its separate case. Neither is a physical microphone-to-headphone measurement, and neither justifies a claim of a few milliseconds on a real card.

The final installed probes also keep the existing What U Hear client bridge targeted while USB headset, USB speaker and Bluetooth null outputs take the default. Explicit monitoring and combined routes stay on their chosen devices. Every feature failure needs a visible translated reason and an explicit retry path; missing/exiting helper cases are negative controls. The built package's 29 routing messages are read from all nine translated catalogues, alongside English source messages.
