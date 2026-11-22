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

## Scope still to prove

These notes establish source and packaging preparation. They do not yet claim
an installed package, stereo disparity, AT-SPI event, shared model listing or
real recognition latency. Add the measured results only after those rows run.
