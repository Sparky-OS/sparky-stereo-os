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
An independent reconstruction later captured the first NVIDIA desktop frame at
0 pixels, with 3 white-mask differences among 13,694 glyph pixels; its later
video frame was again -2 pixels with zero differences. The cause of that change
is unresolved. The specified result is now zero disparity: captions are subtitles, identical
at the same coordinates in both eyes. A -2 result is a failed screen-plane row,
not a baseline to preserve. Measure timing as well as position before treating
one snapshot as the program's permanent placement.
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
  occur between the window query and capture. In 0.1.0, CaptionBox restarts its
  ten-second clear timer only when the computed captionBlock string changes.
  Repeated equal final utterances eventually leave that string unchanged; the
  timer clears the box, and the next utterance shows it again. The Wayland
  trace records client layer-surface destruction and null-buffer unmap, so this
  is not evidence of a lost compositor buffer or interrupted audio feed.
  **Found by:** a failed glyph-witness check and matching hide/re-show protocol
  logs during an independently reconstructed rig run.
  **Fix for the measurement fixture:** retain the failing frame, then wait within
  a fixed 60-second deadline for caption ink in both eyes and measure that exact
  frame with its contemporaneous window geometry. Keep the disparity and glyph
  equality checks unchanged. This does not fix or conceal application latency.


## Screen plane and the compositor's separate layer rules

KWin's stacking layer and stereo depth role are different classifications.
In the packaged +stereo3d59 source, `LayerShellV1Window::scopeToType` does not
recognize `kaption-overlay`, so it is a normal window. `StereoDepth::roleOf`
exempts a top layer-shell overlay only when its frame covers the whole output.
A partial, inactive caption therefore becomes Sunk. The first sunk rank is
one fifth of the negative limit: at a ten-pixel physical limit it is -2 pixels,
including at 125 percent logical scale. Inspect the exact package source and
contemporaneous stacking snapshot; a different working checkout is not proof.

The smallest proposed compositor correction is a narrow caption-role exemption
at the depth classifier, retaining ordinary partial overlays as controls.
No compositor or application patch is included in this integration. A transient
zero-disparity frame is not explained by the steady classification alone:
remapping, deletion/fade handling and depth motion need a frame-specific trace.
Retain unresolved frames and repeat them; do not infer an internal motion value
from a window-list snapshot taken before or after the render.

For Kaption's idle rule, the proposed application correction is to restart the
activity timer on the relevant channel's new utterance event even when the text
is equal. Test repeated equal final utterances with distinct IDs beyond the idle
timeout, then real silence, and verify that microphone activity does not hold
system captions open. This is a source-backed proposed correction, not a patch
in the package or a claimed upstream acceptance.

## The optional Partners adapter

The adapter uses the page's Settings cascade, KConfig writer, metered policy and
shared Graphics inventory. It adds no independent hardware detector or renderer.
One disabled user unit owns captiond and Kaption. Start is explicit; login and
microphone are separate choices. The frontend starts only after a compatible
socket status confirms the requested recognition route. A mismatch stops the
pair and is kept by the Problems engine. The recognizer's measured `behind`
status supplies the cannot-keep-up message; the assumed command-line latency
estimate does not.

The shared file stays at its original absolute path or in captiond's native
model folder. Verify byte count and SHA-256 without calling a model loader.
Keep Vibe closed while updating its native model.path and models_folder; accept
only an absent store, an exact edition seed, or this adapter's unchanged receipt.
Refuse unknown, changed, read-only or symlink stores. Exclusive publication of
a first file must reject an application that creates the name in between.
Removing the package must not remove models or personal settings.

- **Symptom:** the recognition route agrees with a device listing but ignores
  the page's card. **Cause:** the shared compute wrapper intentionally preserves
  inherited CUDA/HIP/ROCR/ggml visibility as a caller override. **Fix:** the
  page-owned session removes inherited compute visibility before asking the
  shared wrapper for both its device listing and its session. **Found by:**
  reading the wrapper while checking route agreement; a model-free regression
  asserts that stale visibility and CAPTIOND_INPUT cannot leak into the child.
- **Symptom:** the user-unit package build rejects `--no-start`. **Cause:** that
  switch is not accepted by dh_installsystemduser. **Fix:** use its supported
  `--no-enable`, as the Partners engine packages do, and prove installed state
  and upgrade behavior separately. **Found by:** the offline debhelper build.
- **Symptom:** source tests pass but no candidate survives the build. **Cause:**
  the mandatory archive-backed link gate lacks an explicit signed-archive
  configuration and sibling package closure. **Disposition:** retain the failed
  row and prepare that closure; never bypass the gate or call source tests a
  qualified package. **Found by:** the integration's first source-package build.

### Preparing the archive and sibling inputs

Keep an explicit signed archive configuration, including the Debian snapshot,
deb-multimedia and the published edition. A local mirror retains the original
InRelease and its hashed Packages files; HTTPS downloads are a separate step
from the network-disabled build. Reusing a cached package requires its size and
SHA-256, and the gate checks it again against the signed index it selected.
Supply the accepted edition packages through `SPARKY_LC_SIBLINGS_FILE`; an
installed build dependency is not a runtime sibling in the gate's empty system.

Check the minimum versions in the successor's control before assuming the
accepted pool closes its dependencies. Partners 0.1.3 requires Graphics 0.2.17;
a pool containing Graphics 0.2.15 and a published archive containing 0.2.14
cannot qualify it. The unchanged APT solver reports that relation and
`[no choices]`. Keep the full failed build log and solver record, obtain the
accepted dependency, then rebuild. Do not lower the dependency, replace it with
a test double or label a removed candidate as a package.

A failed conventional recipe must copy its complete build log out of its
throwaway work directory before its cleanup trap runs. Keep the source date and
recipe commit unchanged through the build; the successful build record is
written only after every gate passes. Package closures and retained proof files
belong in durable stage and evidence directories, separate from disposable
archive caches and object trees.

An accepted dependency can be staged outside the publication round. Read that stage's checksum manifest, verify each needed source/binary before and after copying
to private scratch, and offer the copied binaries as explicit gate siblings.
They do not become an archive. Replace the older same-name round sibling rather
than offering two authoritative versions. Supply the accepted previous Partners
package through the predecessor directory and a coherent previous sibling list;
the successor still qualifies against the dated public archives.

For the installed packaging proof, install the accepted predecessor first and
read APT's `Inst` lines for the successor and adapter, and its `Remv` lines for
removal. Keep synthetic personal configuration/model-file witnesses in the rig
and compare their hashes after removal. A text witness checks preservation; it
is never a real speech-model or transcription result. Installed lifecycle proof
does not replace the separate page-controlled session and both-eye proof.


## Proving the installed Partners switch

Run the installed KCM with `kcmshell6 kcm_sparkystereo_partners`, then invoke its
accessible controls by their translated names. Check each resulting service,
configuration and socket state; an accepted accessibility action alone is not
proof of the requested change. Save the accessible page and a marked stereo
capture in English and Brazilian Portuguese. Check the known fixture sentence
at AT-SPI, rather than accepting any nonempty caption.

Use a real systemd user manager in a private container cgroup, as the
[Partners rig](partners.md) does. Start `graphical-session.target` as a dependency
of a disposable session target: it deliberately refuses direct manual starts.
Enable the caption unit only through the page's login control, stop/start the
session target and verify both the enabled and disabled cases. Add the render
supplementary group before starting the user manager; otherwise its services
retain the old groups even if a later `runuser` compositor can access the GPU.

The model-free integration fixture replaces the daemon executable boundary and
the model catalogue only inside the disposable container. A short text witness
satisfies the fixture catalogue's checksum without entering any model loader.
The installed adapter, KCM, user unit and Kaption remain unchanged. The stand-in
speaks captiond's protocol to both clients, reports an explicitly synthetic
route, and opens private null-sink/source capture streams according to the
adapter's generated configuration. Check that Off removes its processes,
private socket and capture streams. This proves coordination, not recognition
quality or real-model interoperability; those require known words on the bench.

- **Symptom:** normal Off briefly reports that captiond or Kaption stopped
  unexpectedly, and the user unit ends failed despite removing every child.
  **Cause:** `KillMode=control-group` sends SIGTERM to the coordinator and its
  children together; the protocol can reach EOF before the coordinator handles
  its stop flag. **Fix:** `KillMode=mixed` signals the coordinator first, allowing
  its existing orderly child cleanup, while retaining systemd's final group kill
  at the stop deadline. **Found by:** the installed KCM's Off action and the user
  journal. Require `Result=success` after Off as well as absence of children,
  sockets and streams; mere absence passed even before the correction.
- **Symptom:** a private PipeWire socket exists but the first registry dump fails.
  **Cause:** the user manager's socket activation races a directly started
  server in a minimal rig without its complete D-Bus user-service packaging.
  **Fix for this rig:** stop that container's stock PipeWire socket/service before
  starting its private daemon, then wait for a successful registry dump, not
  just the socket pathname. Do not touch the workstation's PipeWire.
- **Symptom:** playback visibly loops but an advancing-time check times out.
  **Cause:** the loop returns to timestamp zero and a truth-value readiness
  helper discards it. **Fix:** return a nonempty observation containing zero;
  retain the distinct positions and keep the original deadline.

Keep the caption's expected disparity at zero. List nonzero caption rows apart
as waiting for the compositor correction, preserving their measured disparity
and aligned glyph error. Readiness checks for KWin wait for its bus ownership
and actual reply within a declared deadline; do not rely on a five-second sleep.

## Bench kit and the complete rerun

Keep real recognition behind an explicit bench-machine guard and a separate
model-download choice. Exercise the same integration worker in a model-free
container with two declared substitutions: the daemon/model catalogue, and the
file recognizer's HTTP boundary. Require the known clip's complete words in
both the daemon's settled caption and Kaption's AT-SPI announcement. A nonempty
caption or HTTP 200 is not a speech result. Save negative controls for unrelated
words, an incomplete sentence, and an empty transcription response.

Use a temporary bench account, its own user manager, virtual compositor and
private PipeWire. Disable physical ALSA and Bluetooth monitors in that account;
do not capture the person's default microphone, which can change when a USB
microphone is plugged in. Select each card through Partners using Graphics'
stable inventory, not a ggml ordinal. Refuse an ambiguous route. Turn the actual
integration on and off and retain its generated configuration and actual route.

- **Symptom:** a player stream exists and a synthetic caption appears, but the
  known WAV never drains. **Cause found in the private rig:** the graph had not
  connected the player/monitor path; stream presence did not establish audio
  progress. **Fix for the measuring fixture:** wait for the named ports and link
  the private mono player to both null-sink playback ports and that sink's monitor
  to the private caption input, as captiond's own testing helper does. Keep the
  graph before and after, require player exit zero, and keep the original trial
  deadline. This is no claim about a physical speaker route.
- **Symptom:** a shell kit exits while reading temperature on an older machine.
  **Cause:** it assumes thermal_zone files exist. **Fix:** read the `k10temp`
  hwmon device's `temp1_input`, tolerate a failed read and record its reason.
  Retain the bench's thermal stop bound. The station mechanics test uses a
  synthetic hwmon tree; applying the laptop's bound to the station's sensor is
  a fixture error, not a reason to raise that bound.
- **Symptom:** package cleanup could purge an existing package after refusing an
  upgrade. **Cause:** the planned additions were saved before checking for
  existing package states. **Fix:** validate the complete Inst/Remv plan first,
  then remember only new additions; check purge's plan against that set and
  restore automatic/manual marks. Test an existing installed and config-only
  state as negative controls. Never use an unrestricted autoremove.

Measure settled-caption and accessible-announcement arrival against monotonic
playback drain, with CPU ticks, load and sampling interval recorded. Report what
that metric is: delay after this known clip's end, excluding model load; not
per-word alignment or physical acoustic latency. Performance is information;
missing known words or a failed requested route is a failed correctness row.

For Vibe 3.3.5, `vibe-server serve --host 127.0.0.1 --port 0` prints its allocated
port when ready. Load the same absolute file via `POST /v1/models/load` with
`path`, `gpu_device` and `no_gpu`; `GET /v1/models` lists the loaded basename.
Transcription uses `POST /v1/audio/transcriptions` and multipart `file`, not a
JSON pathname. Check the returned words and retain the selected path, native
listing and model hash/inode before and after. Unload and stop the private server.
These shapes come from the release's server/routes source; the stand-in must
reject a wrong request shape rather than manufacture a successful answer.

A whole rerun accepts a new output folder and explicit local input configuration.
Verify immutable image IDs and stage hashes, run the unchanged package gates,
install the staged packages fresh, exercise apt Inst/Remv and preservation,
native capture separation, both cards/scales, and the bench worker's synthetic
mechanics. Put every log, ledger and generated helper under that output. Check
the actual container exit, not just `docker start -a`. Remove exact temporary
container/image names in cleanup, including a failed run.

Print known compositor-depth waits separately from ordinary rows. Zero remains
the expectation. A known -2-pixel scope/depth fault with identical glyphs and
layer 9 may wait for the separately assigned correction; a glyph mismatch,
different layer or unexplained disparity is a new failure and exits nonzero.
Do not turn every nonzero disparity into an exception. A complete run's table
and exit are part of the hand-back; real-model bench measurements remain clearly
unrun until the person runs that kit.

## Merge qualification and full-page text geometry

Run the unchanged supply-chain wiring test on a scratch merge with the current
main branch, in addition to package gates. The wiring checker recognizes the
standard `docker run` launcher; a `docker create` launcher can be rejected even
when provenance initialization precedes it. Use the standard detached run form,
initialize provenance first, record its container ID, and inspect its final exit.
Keep the red checker result and its green successor; do not edit the checker.

Authored DEP-5 files name contributors without copying their contact addresses.
Audit every added line of the whole branch diff before handing it back. The
original upstream archives remain byte-identical. A packaging-only correction
increments the Debian revision, not the upstream release. Rebuild the source
closure as well as binaries. Create stage retention markers before generating
SHA256SUMS, include hidden regular files, and reject unlisted files. Retain the
predecessor closure with verified sums until acceptance. Compare every payload,
control and source archive member with the predecessor.

- **Symptom:** the full Partners page clips its caption controls at 125 percent,
  even though their labels already have Text.Wrap. **Cause:** minimum widths of
  other rows and combo boxes force the containing column wider than its scroll
  viewport. **Fix:** allow those layout children to shrink, and let each program's
  choice controls flow onto another line when needed. Keep long text wrapping
  inside the real page width; a standalone caption component cannot prove this.
- **Symptom:** a geometry checker reports every native combo label clipped.
  **Cause:** the native style item's contentWidth is a style size hint including
  the widest menu entry, not the displayed glyph width. **Fix for the observer:**
  measure the current text using the control's actual font and available width;
  use contentWidth/contentHeight for ordinary QQuickText. Require neither
  truncation nor horizontal overflow; vertical content must remain reachable
  within the scroll content height.
- **Symptom:** initial labels momentarily occupy tiny widths and fail the check.
  **Cause:** asynchronous QML layout has not settled. **Fix for measurement:**
  require several fresh equal geometry snapshots within the existing readiness
  deadline, then evaluate them, including a stable failing layout. Never wait
  until the verdict becomes green.

Load a test-only geometry observer into the installed KCM and capture the full
page. Check every catalogue found in the installed Partners and caption packages,
with both cards at 100 and 125 percent. Supply verified locale data so KDE uses
the selected language; an English fallback is not a translated page. Eight
caption catalogues still need translation, although the surrounding Partners
page already has all ten. Catalogue discovery adds their rows when they arrive;
verify that the adapter actually uses each installed caption catalogue.

- **Symptom:** the bench kit ends in a Python traceback while apt cannot plan
  installation against an older published package set. **Cause:** an exception
  escapes the install-plan stage. **Fix:** say that installation cannot be planned,
  include apt's exact unmet dependency explanation, then run the normal cleanup
  path and exit nonzero. Test the real apt solver against an isolated empty
  archive with a deliberately unavailable dependency; assert no fetching or
  installation, no traceback, and a written cleanup record. This test does not
  authorize running the real bench kit or loading a model on the station.

A minimal rig can have translated CJK strings but lack their fonts. Missing-glyph
boxes can fit where the real text would not. Verify the font inputs, capture the
rendered page, and reject zero glyph indexes in the laid-out text before treating
its geometry as a pass. This is a rig-input correction, not a translation.

- **Symptom:** Kaption's live-daemon test sees its output source but immediately
  fails to find the private input source. **Cause in the test:** it waits for
  outputSources, then checks inputSources with an immediate QVERIFY although
  their updates arrive separately. **Proposed upstream test fix, not applied:**
  wait for the input source independently within the existing readiness bound.
  Retain the failed log and rerun the unchanged recipe; a retry pass does not
  erase the race. This is separate from the installed microphone-routing proof.
- **Symptom:** the link gate refuses conflicting supplied package versions.
  **Cause:** a successor's own predecessor binaries were also supplied as current
  siblings. **Fix:** exclude the source's produced binary names and generated
  companions from current siblings. Keep predecessor packages in the predecessor
  directory, with a coherent separate predecessor sibling list when other staged
  sources have also advanced. Do not change the solver or discard its failed row.

When the rig already has Qaption and captiond's development/testing packages,
upgrade that whole co-installed source cohort together. Their exact-version
relations otherwise make apt plan removals when only the six runtime targets
are offered. Read and reject every Remv line during upgrade, and run apt-get
check after the fresh installation. This is a rig dependency closure, not a new
runtime dependency of the integration or bench kit.

Do not rely on a standalone `! grep` or `! pgrep` under `set -e`: shell negation
is exempt from errexit, so a forbidden match can be ignored. Use an explicit
conditional failure or a checked parser. Retain the actual rejected apt plan;
negative controls must reject a removed companion and an unrelated installation,
as well as accept the complete intended upgrade set.

For a checkout using host Git alternates, a container clone cannot resolve the
host-only alternate path. Make a self-contained bundle under the new output,
clone it inside the container, and perform the scratch merge there. Keep the
fetched base and tested tip in the record; do not mount another checkout writable.
