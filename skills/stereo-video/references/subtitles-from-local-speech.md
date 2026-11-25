# Subtitles from local speech in Kdenlive

Source reconciliation on 2026-11-25 covered Kdenlive 26.08.1, including the edition's `26.08.1-1+stereo3d13+lc1` source.
The editor has two speech engines at this version.
The Vibe integration and its subtitle measurements are pending.

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
   The Partners catalogue currently marks Kdenlive as using its own engines, and the resolver already accepts per-program and system model choices.
   Preserve the editor's saved engine choices and use the existing subtitle import boundary.
5. Follow the [Vibe dictation recipe](../../stereo-integrations/references/partners.md) for the private, per-job `vibe-server` lifecycle.
   Start the server with the model on loopback and an ephemeral port, read that child's ready line and release the child on completion, cancellation or failure.
   Its store is at `$XDG_DATA_HOME/github.com.thewh1teagle.vibe/app_config.json`; the language comes from `transcription.modelOptions.lang`.
   The Kdenlive client needs timestamps as well as text, so verify the timed response against the packaged server before choosing an import format.

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

For an eventual runtime proof, record the spoken words and speech intervals before running the fixture.
Run the packaged predecessor and successor on the same input, read back the project's subtitle file, then compare the glyph region in both eyes of a marked project-monitor capture.
A passing subtitle import alone establishes neither the timestamps nor the screen-plane placement.
