# Surround that follows a stream, and passthrough that follows an output

ORDER 21 implements this in `sparky-stereo-audio` 0.2.0. It extends the existing engine and WirePlumber policy. Its package is a review candidate until the edition accepts and publishes it.

```sh
sparky-stereo-audio show
sparky-stereo-audio surround --output NODE --layout 7.1
sparky-stereo-audio surround --output NODE --headphones yes
sparky-stereo-audio surround --output NODE --profile /absolute/personal.sofa
sparky-stereo-audio surround --output NODE --profile /absolute/personal.wav --kind hesuvi
sparky-stereo-audio surround --output NODE --matrix decode
sparky-stereo-audio surround --output NODE --matrix upmix
sparky-stereo-audio surround --output NODE --matrix off
sparky-stereo-audio passthrough --output NODE --codec AC3=auto --codec DTS=off
```

A headphone output and a stream with more than two channels get a temporary binaural sink. Stereo streams link directly to the physical output, including while a multichannel stream plays. The default head profile is MIT KEMAR; 5.1 or 7.1 follows the stream unless chosen explicitly. No filter requests a graph rate. The physical default stays owned by the existing default policy. An active analog port's type is stronger evidence than a device name; USB and A2DP alone cannot establish that a device is headphones. The command's per-output override handles ambiguous hardware.

The optional passive matrix decoder has front attenuation, split rear coefficients, 7 kHz lowpass and 20 ms rear delay, following Steve Davies' MPlayer decoder. It has crosstalk and a phantom center. It does not claim active steering. Decode and PSD upmix default to off for stereo music; discrete multichannel bypasses both. There is no reliable general flag for matrix-encoded stereo. Automatic activation requires a design decision rather than a guessed content classifier.

## Reconcile the installed stack first

PipeWire 1.6.9's named KEMAR example uses an external WAV convolver response; that response is not in Debian's package. Debian's libmysofa instead supplies `MIT_KEMAR_normal_pinna.sofa`, and PipeWire supplies a SOFA spatializer plugin. The two upstream examples whose names contain the matrix-surround trademarks are encoders from six channels to two, not decoders. The matrix spatializer is a width effect. Do not mistake any of those for the requested decoder.

PipeWire's ALSA ACP code already reads ELD controls, matches the connector and publishes `iec958.codecs.detected` on that route. WirePlumber saves `iec958Codecs` with route state. The Pulse device-restore API used by pavucontrol writes those route properties with `save=true`; `pactl set-sink-formats` reaches the same implementation. Keep this as the persistence authority. Never combine capability lists from different displays. A sink with no encoded descriptors gets no detected encoded codecs. An explicit codec override is still available.

A player must retry decoded PCM after encoded negotiation is refused. The edition hook rejects an unsupported encoded request on the selected sink; otherwise stock WirePlumber may quietly send it to another capable output. This changes no physical default.

## Private fake-device proof

The package's tracked `tests/render-surround.py` runs a private D-Bus, PipeWire and WirePlumber session and a null headphone or multichannel speaker sink. It needs Python, NumPy, SciPy, libmysofa, its utilities and the PipeWire/WirePlumber programs. `tests/passthrough/proof.py` additionally needs GCC, libasound and libpulse development packages and FFmpeg. It compiles an ALSA ioplug that takes timed buffers into a file; it opens no real sound device. Mount the recipe at `/work/src/build/sparky-os/packages/sparky-stereo-audio`, a writable scratch directory at `/work`, and an evidence directory at `/evidence`. Run as an ordinary user under `dbus-run-session`, in a container with no sound devices or host session sockets. Use the lane's HTTPS-only APT preparation before installing dependencies. No network is needed during rendering.

```sh
AS21_AUTOMATIC=1 AS21_INSTALLED=1 dbus-run-session -- python3 -I tests/render-surround.py
AS21_AUTOMATIC=1 AS21_INSTALLED=1 AS21_LAYOUT=7.1 dbus-run-session -- python3 -I tests/render-surround.py
AS21_AUTOMATIC=1 AS21_INSTALLED=1 AS21_MODE=stereo dbus-run-session -- python3 -I tests/render-surround.py
AS21_AUTOMATIC=1 AS21_INSTALLED=1 AS21_MODE=switch dbus-run-session -- python3 -I tests/render-surround.py
AS21_AUTOMATIC=1 AS21_INSTALLED=1 AS21_MODE=unplug dbus-run-session -- python3 -I tests/render-surround.py
AS21_AUTOMATIC=1 AS21_INSTALLED=1 AS21_PROFILE=hesuvi AS21_RATES=48000 dbus-run-session -- python3 -I tests/render-surround.py
AS21_INSTALLED=1 dbus-run-session -- python3 -I tests/passthrough/proof.py
```

The renderer compares each speaker's impulse with an independent libmysofa lookup at the requested azimuth. At 48 kHz the measured R-minus-L peaks are +12/-12 samples for front left/right and +33/-33 for side left/right; the center and LFE are symmetric. At 96 kHz they are +25/-25 and +65/-65. Maximum response error is below 1.2e-8. The direct stereo and discrete multichannel controls are bit exact. The encoded transport fixture finds the complete IEC burst bytes in the fake receiver capture and requires a decoded PCM retry on the LPCM-only output. This proves software transport, not a physical receiver handshake or an ELD hardware control implementation.

## Traps: symptom, cause, fix, how found

- Filter nodes never appear and the app waits: holding an asynchronous select-target event open blocks the node-added events that register its new target. A simple hook stops the current selection and schedules another linking scan after registration. WirePlumber debug event logs exposed the dependency cycle.
- The first impulse is missing: the filter input existed before its playback link became active. Require the output SiLink's ACTIVE feature before linking the application. A signal starting at frame zero, rather than after a half-second silence, exposed it.
- Stereo plays through an unwanted downmix or the default becomes a temporary sink after unplug: never change physical default metadata for a per-stream filter, exclude owned temporary sinks from default candidates, and unload the LocalModule explicitly when its stream or target goes away. The switch and unplug controls inspect the live graph while playback is active.
- SOFA azimuth looks right but timing is lost: PipeWire 1.6.9's plugin ignores separate `Data.Delay`. Reject imports with a nonzero separate delay until that upstream limitation is fixed. MIT's supplied KEMAR stores its delay in the impulse itself. Read the plugin and compare libmysofa delays with the samples.
- A compact JSON module configuration fails near the next module: the PipeWire module parser modifies an args delimiter in place. Pretty JSON avoids adjacent closing delimiters. The parse_modules warning identified the location.
- Settings appear unsaved immediately after a restart: WirePlumber saves state after a delay. The test waits for its actual `sm-settings` file, rather than the unrelated stream-properties file, before restarting and then waits for the saved setting to be restored.
- Pulse reports PCM for an encoded-only stream: PipeWire 1.6.9's create-playback reply initializes the encoding as PCM even while the graph negotiates IEC958/AC3. Inspect actual Node and Link formats and compare the receiver bytes; never treat this reply alone as proof of decoded audio.
- Bubblewrap cannot create namespaces under Docker's default sandbox: run the isolated qualification container with the documented seccomp, AppArmor and systempaths exceptions. Keep it disposable, without host devices or session mounts. A minimal unprivileged bwrap probe distinguishes this environment issue from a package defect.

## Licences and standards

MIT's KEMAR release permits unrestricted use with author citation: Bill Gardner and Keith Martin. The dependency supplies its file; this package does not duplicate it. SADIE II v1.4 is Apache-2.0 with attribution. The inspected ARI `dtf_nh2.sofa` explicitly declares CC BY-SA 3.0; do not generalize that to every file. IRCAM LISTEN requires a file-specific redistribution verdict before packaging. HeSuVi imports are the person's files; a channel convention is not a redistribution licence for every preset.

CTA-861 describes EDID audio blocks, IEC 60958 and IEC 61937 describe the transport, AES69 describes SOFA, and ITU-R BS.775 describes multichannel layouts. The ORDER 21 normative CTA, IEC and AES texts were unread: the implementation and rig do not establish standards conformance. Keep that distinction when repeating this proof.
- An advertised codec is refused but no problem appears: ALSA can reject the format before a PipeWire Link is exported. The policy owns IEC958 SiLink activation using the stock linking flags and reports its `link-error` to the problems monitor. The rig's `AS21_REJECT=1` returns EIO from its S16 hardware-parameter negotiation and requires a retained LOCAL41 problem. A separate Lua ObjectManager requests all features and cannot observe a link that never activates; using it is too late.
- A response disappears after being selected: validate the response again when its temporary sink appears, report unreadable or unsupported files, and monitor the owned node's error state. A deleted personal SOFA exercises this path. PipeWire's graph-start log alone is not a translated problem report.
