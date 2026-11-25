# Subtitles from local speech in Kdenlive

Source reconciliation on 2026-11-25 covered Kdenlive 26.08.1, including the edition's `26.08.1-1+stereo3d13+lc1` source.
The staged predecessor has VOSK and Python Whisper.
The Vibe successor adds **Use the system default** and **Vibe (local)** to Automatic Subtitling and the Speech Editor.

## Trace the two entry points

1. Read the installed package's source series before editing.
   The staged Kdenlive source includes patches 0001 through 0027 and five catalogue patches.
   Its companion MLT source is `7.40.0-1+stereo3d12+lc1`, and the package recipe builds with stereo-layer 1.23.2.
   Use the exact staged closure as the baseline for any successor.
2. Search the current Kdenlive source and its merge requests on Invent, then KDE Bugzilla.
   Search for `whispercpp` as well as `whisper.cpp`; [KDE bug 499430](https://bugs.kde.org/show_bug.cgi?id=499430) uses the spelling without the dot.
3. Trace the speech setting and engine selection through `src/kdenlivesettings.kcfg`, `src/core.cpp` and `src/pythoninterfaces/`.
   `SpeechToTextVosk` and `SpeechToTextWhisper` use Python, and the engine values live in `src/definitions.h`.
   The Speech Editor and the timeline's Automatic Subtitling dialog both read the selection.
   In `src/dialogs/speechdialog.cpp`, the timeline transcribes to an SRT that `SubtitleModel::importSubtitle` inserts at the selected zone's start.
4. Read the Partners speech interface and model choice for `org.kde.kdenlive` before wiring its system-default path.
   Run `sparky-stereo-partners resolve --kind speech --program org.kde.kdenlive` inside the rig to read the interface, model and compute environment.
   The program's choice precedes the system choice. An empty Partners model uses the Vibe store. A named unreadable model produces an error.
   Explicit **Vibe (local)** uses the native Vibe model. A stored `speechEngine=` is an explicit legacy VOSK choice.
   Keep the existing subtitle import boundary and leave the legacy Python engines available in the Speech Editor.
5. Follow the [Vibe dictation recipe](../../stereo-integrations/references/partners.md) for the private, per-job `vibe-server` lifecycle.
   Start the server with the model on loopback and an ephemeral port, read that child's ready line and release the child on completion, cancellation or failure.
   Its store is at `$XDG_DATA_HOME/github.com.thewh1teagle.vibe/app_config.json`; the language comes from `transcription.modelOptions.lang`.
   Request `response_format=verbose_json` and `word_timestamps=true`. Omit `language` for automatic detection.
   Vibe 3.3.5 returns seconds in `segments[].words[]` as `text`, `start` and `end`.
   The local Silero file `ggml-silero-v6.2.0.bin` lives in Vibe's `models_folder`, or in its app data directory by default.
   If present, pass its path as `vad_model` with `stable_timestamps=true`. Vibe's own settings are where the person acquires that file.
   The timeline builds SRT from the corrected cue extents and imports it through the existing subtitle model.
   The Speech Editor places the same words into the shared editor format. An anchor such as `2#1.24:1.53` stores the clip ID followed by the word boundaries in seconds, including the selected clip zone offset.
   Speech regions and their quiet gaps are stored as editor blocks. Removing non-speech zones and saving an edited playlist use Kdenlive's existing actions.
6. Carry [Erich Seifert's autosave fix](https://invent.kde.org/multimedia/kdenlive/-/merge_requests/1097) in the inherited speech dialog before extending it.
   The dialog releases the XML read lock before its event processing can deliver an autosave callback.
   The follow-up moves the MLT consumer into the existing `kdenlive_render` process. Track settings and zone selection come from the exported timeline scene.
   The editor's timer watches bytes written and kills an unresponsive renderer after 20 seconds without audio.

## Traps

- **Symptom:** a search for a second implementation turns up a source file called `speechtotextwhisper.cpp`.
  **Cause:** an unbounded search for `whisper.cpp` matches the end of the C++ file name of Kdenlive's Python Whisper adapter.
  **Fix:** match whole engine names, then check the engine enum, build files and invocation.
  **How found:** the package archive search matched the name in `src/pythoninterfaces/CMakeLists.txt`, and the source class identifies itself as `EngineWhisper`.
- **Symptom:** a request that enables `detect_language` succeeds with empty text.
  **Cause:** Vibe 3.3.5 interprets it as a language-only request.
  **Fix:** send the language only when Vibe names one.
  **How found:** the row 72 recipe records real-server responses with an explicit language, with neither field and with `detect_language`.
- **Symptom:** live-caption test logs show Vibe's HTTP server, but the live service offers a Unix socket.
  **Cause:** the test checks that a model file also works in Vibe, while the [live-caption service](../../stereo-integrations/references/live-captions.md) starts captiond and Kaption.
  **Fix:** use the ktextaddons Vibe job as the production lifecycle reference for a Kdenlive client.
  **How found:** compare the service's executable list with the live-caption test's separate model-compatibility probe.

- **Symptom:** the predecessor opens Speech to Text with Whisper selected on a blank profile.
  **Cause:** the original Kdenlive setting defaults to Whisper and stores VOSK as an explicit empty value.
  **Fix:** test an unset choice separately from a saved empty choice when changing the default.
  **How found:** read the generated KConfig and opened the installed predecessor's Plugins page with a fresh profile.
- **Symptom:** the small model recognises the English fixture but returns incorrect Portuguese words.
  **Cause:** the accepted Vibe study also measured higher Portuguese word error from small models on synthetic speech.
  **Fix:** use the medium-q8_0 fixture for the Brazilian Portuguese proof and record its checksum.
  **How found:** post the same Portuguese PCM fixture to the same packaged server with each model and compare the SRT to the spoken words.
- **Symptom:** a cue starts before the generated PCM is active.
  **Cause:** the server sends padded segment boundaries. Even with Stable Timestamps some Whisper word times can precede their VAD window.
  **Fix:** use timed words and Vibe's own VAD when available. Bound them to the voice-activity window and trim clearly measured quiet edges in the same exported WAV.
  **How found:** the real English verbose JSON returned words beginning at 4.63 seconds for the segment beginning at 6.03 seconds, while the second sentence's PCM started at 6.014 seconds.
- **Symptom:** Automatic Subtitling freezes with “Starting audio export” and a zero-byte WAV.
  **Cause found in the rig:** the GUI thread was waiting on `consumer-stopped` inside `Mlt::Consumer::run()`. An unnamed avformat thread in the stripped library was in a condition wait.
  **Fix:** isolate the export from the editor's event loop and enforce its progress deadline. Retain the full thread stack for any consumer that still stalls.
  **How found:** run repeated exports with a missing model to end each successful export before recognition; attach the container's debugger at the stall and collect `thread apply all bt`.
  The related [MLT PR 1366](https://github.com/mltframework/mlt/pull/1366) corrects an avformat running-state race. A stack waiting for the stopped event alone cannot identify that race.

## Run the fixed clips

The build branch's `sparky-os/tests/kdenlive-vibe/make-speech-fixture.py` creates an eSpeak NG narration and Kdenlive project for each language.
The fixture records active PCM intervals. Keep the same audio and text for each engine comparison.
Install the engines' fixtures before disabling the rig network. Use a fresh Kdenlive profile for each route.
In the staged predecessor, VOSK's Python venv took 5.38 seconds and 45,025,649 bytes. Python Whisper CPU's venv took 41.47 seconds and 2,274,070,185 bytes.
Processing to subtitle import took 3.99 seconds with VOSK and 5.88 seconds with Python Whisper.
The model sizes were 70,898,967 installed bytes for VOSK and 75,571,315 bytes for Whisper tiny.en.
The Vibe successor imported both English cues with small in 4.90 seconds and both Brazilian Portuguese cues with medium-q8_0 in 13.49 seconds.
The models occupied 487,601,967 and 823,369,779 bytes. Kdenlive created no Python environment for either Vibe job.
The two saved projects contained the expected words. The old segment-based route missed the PCM by up to 1.20 seconds.
The follow-up gates both directions separately. Cue starts may be at most 0.30 seconds early or 0.15 seconds late. Ends may be at most 0.15 seconds early or 0.30 seconds late.
A cue cannot span a pause of one second or more between sentences.
Set these limits from the editing need before seeing model output.
The two fixed waveforms, a 4.5-second leading-silence variant and a speech-over-music variant have both raw and Stable Timestamps server replies to replay.
Against the synthetic waveforms, the compiled timing function retained all words and placed each cue inside those limits.
Test real recordings separately and count which cues have verified boundaries. A fragment whose text starts or ends mid-sentence needs a word-level reference before its timing can be scored.

Read the project's subtitle file after saving. Measure cue text and times against the reference. Keep each unsuccessful run as a separate control.
For stereo, give the monitor different known fills in the two eyes, capture using Stereo KWin, and compare the glyph masks in the text region of a marked `.pns` pair.
Use a capture without a subtitle and an artificially shifted glyph mask to check the comparison itself.

On the isolated Stereo KWin output, the English subtitle occupied the same 236 bright glyph pixels in both eyes over independently coloured views.
The best measured displacement was zero in both axes, with 1.0 intersection over union.
A five-pixel horizontal shift registered as five pixels, and the capture without a subtitle gave zero glyph pixels.

- **Symptom:** the virtual compositor starts but ScreenShot2 cancels every capture.
  **Cause:** it has no render node and falls back to a compositor without the stereo capture path.
  **Fix:** give the rig the permitted render node, select a virtual 3D twin through the rig's own KScreen session, and verify that ScreenShot2 reports both stereo flags.
  **How found:** the CPU-only case logged the missing render node. The NVIDIA CDI case returned a marked 3200 by 900 capture with two identified 1600 by 900 eyes.
- **Symptom:** an accessible control on native Wayland responds at the wrong screen position.
  **Cause:** Qt reported the position in the client window's coordinate system.
  **Fix:** activate standard accessible buttons directly and locate menu text in the rig capture before sending pointer clicks.
  **How found:** the trace clicked Sequence at x=230, y=13 while the capture placed it at x=497, y=103.
- **Symptom:** the subtitle dialog shows terminal colour escapes mixed into a refused-model diagnostic.
  **Cause:** the packaged server writes colour-formatted tracing output to stderr even as a child process.
  **Fix:** remove terminal sequences and show the final diagnostic in the dialog.
  **How found:** open the installed-editor refusal capture from a corrupt model file, then run the native refusal and a coloured fixture again.
- **Symptom:** the virtual compositor cannot start and the shell reports Operation not permitted.
  **Cause:** the installed executable's scheduling capability exceeds the disposable container's capability set.
  **Fix:** use a byte-identical test copy without the capability and confirm which compositor PID answers the private session bus.
  **How found:** the copy and original had the same SHA-256 and the copy announced its private socket.
- **Symptom:** an older package gate offers a Debian Qt version even though Graphics requires the edition's exact runtime.
  **Cause:** both archives have candidates and the newer Debian candidate wins without explicit matching inputs. A dated Debian index can also lack Frameworks 6.32 for the edition's KIO.
  **Fix:** use the matching signed edition Qt binaries and a qualified Debian index with the necessary Frameworks version.
  **How found:** the package solver first reported the exact Qt conflict and then identified the unsatisfied Frameworks dependency.
