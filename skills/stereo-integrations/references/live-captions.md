# Kaption, captiond and Vibe

Package the author's release before designing a bridge. Kaption is a live caption
frontend; Vibe handles files and transcript editing. Keep both programs intact.

## Working recipe

1. Pin both release tags and archive hashes, compare their default branches, and
   run REUSE on the unpacked release. Read storage and network call sites rather
   than treating the announcement as a runtime result.
2. Build captiond against the distribution's Whisper and ggml. Split its SONAME
   library, ordinary development files and testing helpers. Keep both the user
   service and socket disabled at installation. Build Kaption and Qaption as
   separate coinstallable binaries with shared data.
3. Use an offline container for builds and tests. Retain signed archive indexes
   and the selected package bytes before running the Lean Code and link gates.
   The build record must name a clean packaging commit and immutable image.
4. For a frontend proof without a model, use the release's
   `captiond::testing::StandInDaemon` from `captiond/testing/stand_in.hpp`.
   It speaks the real Unix socket protocol, sends a greeting on connection,
   accepts `caption_event` updates and records client commands. Set
   `CAPTIOND_SOCKET` to its private socket. Label every result synthetic.
5. Capture installed Kaption in isolated Stereo KWin over a declared stereo
   clip and the desktop. Record the layer-shell role, window geometry, horizontal
   disparity and residual error, at 100 and 125 percent scale. Save each pair as
   a PNG with its sTER chunk. Follow [the proof rig](../../stereo-proof-rig/SKILL.md).
   Do not infer desktop depth from the Overlay role, or from a bounding box alone.
6. Listen for the AT-SPI announcement event carrying the settled phrase. Separately
   record the PipeWire nodes opened before and after selecting an input. Neither
   a QAccessible unit test nor a visible microphone icon proves these routes.

## Release facts

At 0.1.0, captiond's tag is `36f582427c9c321c284319cf7e0bd599996d2475`
and Kaption's is `c9fc9d433c7b1dfac2700177ab6590d24e791fed`.
Their fetched default branches matched those tags on 22 November 2026.
The release archives pass REUSE: 161 files for captiond and 190 for Kaption.
Captiond's daemon is AGPL, its client library has the accepted LGPL alternatives,
captionctl and the frontends are GPL; inspect the file-level expressions when
writing DEP-5 rather than assigning one licence to the whole source.

`Messages.sh` is KDE's extraction entry point. Captiond has one gettext domain
for its daemon, command and client messages; Kaption and Qaption share another.
Extraction with KDE's xgettext keywords finds 233 captiond and 420 frontend
message entries, including 1 and 6 plural entries respectively. These are
translation units, not a count of grammatical sentences. Neither release ships
translated catalogues. Template headers intentionally contain placeholders;
compiling a POT as if it were a completed PO is not a translation validity test.

Captiond uses `captiond/captiond.conf` under the XDG configuration directory,
`captiond/models` under the XDG data directory, and
`captiond/captiond.sock` under the XDG runtime directory. Its extra model search
paths include `CAPTIOND_MODEL_PATH`. The frontend downloads only on Install,
streams into a temporary file, checks the exact size and SHA-256, then commits it.
Kaption and Qaption have separate `kaptionrc` and `qaptionrc` settings. Their live
history stays in memory until the person exports TXT, SRT or VTT.

The daemon's `behind` status is measured during recognition; the frontend's
Overview displays it. Its `--latency` estimate is a different thing and must not
be reported as measured end-to-end delay. The model advisor uses catalogue
expectations rather than a benchmark on the person's machine.

## Traps found while packaging

- **Symptom:** WebRTC echo cancellation is missing despite installing
  `libwebrtc-audio-processing-dev`. **Cause:** the Debian snapshot's 1.3 package
  exports `webrtc-audio-processing-1`, while captiond requires API 2.
  **Found by:** the pkg-config module and CMake feature summary. **Disposition:**
  preserve upstream's detection and report the missing feature. Separate streams
  do not cancel loudspeaker audio heard by a microphone. No API compatibility
  patch has been proven.
- **Symptom:** source preparation stops with `No such file or directory: dch`.
  **Cause:** debhelper alone does not install the toolkit's changelog tool.
  **Fix:** prepare `devscripts` with the build environment, before the offline
  build. **Found by:** `lean.debian_prepare`'s error before compilation.
- **Symptom:** a launcher returns success after an inner command failed.
  **Cause:** `docker start -a` does not propagate this daemon's container exit
  status. **Fix:** inspect `State.ExitCode` after attachment and fail on nonzero.
  Keep the inner log and container identity.
- **Symptom:** the edition's FFmpeg dependency cannot resolve `libaom3`.
  **Cause:** the edition's media stack also needs the signed deb-multimedia
  archive. **Fix:** include it alongside the dated Debian snapshot and the
  edition pin; explicitly retain the intended Whisper/ggml versions because
  deb-multimedia also offers them with a higher epoch.

- **Symptom:** the privacy-documentation link test fails after native projection:
  `TrayMenu.cpp has 184 lines`, while its link names lines 195–199.
  **Cause:** those source files are also text/line-number inputs to
  `tools/check-doc-links.py`; compiler equivalence does not qualify that consumer.
  **Fix:** preserve all eleven C/C++ files cited by the release documentation
  through a reasoned source-consumer plan passed to `lean.debian_prepare`.
  Keep the checker unchanged. The authored release passes it before projection.
- **Symptom:** application-icon and both tray-platform suites get empty or
  transparent icons. **Cause:** `libqt6svg6` does not install Qt's SVG icon/image
  plugins. **Fix:** require `qt6-svg-plugins` at build and runtime. The same three
  compiled suites pass once it is installed, without a source change.

## Installed daemon without a speech model

The packaged testing library's `PrivatePipeWire` plus `Daemon` with
`--engine stub --no-gpu` measures capture routing without speech inference.
Record `pw-dump` before start, output-only, separate-input, input-off and pause.
The installed 0.1.0 daemon opens `captiond` with `stream.capture.sink=true` and
`target.object=captiond-test-sink`; explicitly selecting input adds
`captiond-input`, targeting `captiond-test-source` with `node.dont-fallback=true`.
Disabling input removes that node alone. Pausing removes both capture nodes.
The fixture uses only private null sink/source nodes, not sound hardware.
A checker must fail when the microphone target is changed to the system sink;
this negative control catches a test that merely counts two nodes.

## Installed frontend measurements

On the published edition's Stereo KWin at a 1920-wide virtual output, installed
Kaption 0.1.0 has layer-shell layer 3 (Overlay) and KWin stacking layer 9.
AMD/radeonsi and NVIDIA RTX 3060, at 100 and 125 percent scale, gave a
left-minus-right text disparity of -2 physical pixels over both the desktop and
a declared stereo video. The white glyph masks were identical after alignment.
The translucent backgrounds composite different scene pixels; equality of the
whole RGB rectangle is not the right test. No caption depth was assigned.
These are ScreenShot2 eye renders, not physical scanout evidence.
Each case delivered the fixed settled phrase as AT-SPI `object:announcement`.
No speech output or recognition model ran.

First install leaves the service and socket disabled. Opening Kaption alone
reports that captiond is not running, matching the README's separate start step.
Explicitly starting captiond with empty model search directories opens the model
offer. Neither traced process made an internet syscall before Install.

- **Symptom:** first model offer says 0 KiB free and no model fits, although the
  filesystem has room. **Cause:** `ModelAdvisor::environment()` calls
  `QStorageInfo` on a model directory that does not exist yet; `bytesAvailable()`
  is -1, then clamped to zero. **Found by:** the installed first-start screen and
  a Qt probe comparing the missing directory, its existing parent and the newly
  created directory. **Proposed fix, not applied:** query the nearest existing
  ancestor and distinguish unknown capacity from zero. The downloader already
  creates the directory before checking its own free space.

## Shared model paths and bench timing

Vibe's native store is `app_config.json` in the application data directory
`github.com.thewh1teagle.vibe`, with literal keys `models_folder` and `model.path`.
Point its model folder and captiond's extra search path at one existing directory;
never move or duplicate the person's files as a discovery step.
The native Vibe listing and `captionctl list-models` both found one 52-byte path
witness with one checksum. Vibe correctly rejected it as incomplete or corrupt.
This proves path discovery only: it is plain text, not a speech model.
A common Whisper ggml `.bin` is supported by both sources, but usability of the
same real weights still needs the bench. Vibe's server `/v1/models` lists loaded
models, so it is unsuitable for a model-free disk-listing proof.

Measure final caption arrival against the known audio's end, separately from
model-load time. Record every caption, actual accelerator, processor usage and
host load. A requested GPU that becomes CPU is a failed route, not a timing row.
Use a fresh daemon for each repeated phrase trial so late text from the previous
trial cannot satisfy the next one. A private null-sink playback drain measures
settled-text delay; it is not a physical speaker or display timing measurement.
A bench installer records the original package set, refuses version changes to
existing packages, prints every download's source and size, and removes only its
own additions after checking the removal plan.

## Repeating a model-free rig

Retain the exact installed package versions and the input archives' source,
size and checksum, alongside the base image identity. Reconstruct offline from
those archives, rather than depending on a mutable image tag or current archive
candidate. Download preparation is a separate step. Missing bytes or changed
checksums must fail the rerun. A rerun writes its logs and container ledger in a
new output directory, prints expected/found rows, and removes its exact temporary
containers and image even after a failed row. Rechecking saved captures is useful
but must be labelled separately from new installed-program measurements.

- **Symptom:** repeated known phrases appear to have very low delay after an
  earlier slow trial. **Cause:** a late settled caption can match the next copy
  of the same phrase. **Prevention:** use a fresh daemon per trial, with its own
  event log and load interval. **Found by:** review of the bench helper's event
  matching, before any model run.

Actual recognition, real-weight sharing and physical output remain bench work.

- **Symptom:** a mapped caption window has no text in a captured desktop frame.
  **Cause:** mapping is not visible-content readiness; an idle hide/re-show can
  occur between the window query and capture while the frontend catches up.
  **Found by:** a failed glyph-witness check and matching hide/re-show protocol
  logs during an independently reconstructed rig run.
  **Fix for the measurement fixture:** retain the failing frame, then wait within
  a fixed 60-second deadline for caption ink in both eyes and measure that exact
  frame with its contemporaneous window geometry. Keep the disparity and glyph
  equality checks unchanged. This does not fix or conceal application latency.
