# A native pack: a compiled module for another program

Written on 2026-11-20 from the first native pack, `sparky-stereo-obs` (ORDER 61, milestone 1), a module for OBS Studio 33.0.1 as deb-multimedia ships it.
Use it when an integration must link against the program (a plug-in, a module, a filter), not only drop files where it scans.

## Recipe

1. **Build against the program the edition installs.** Find its development package at the same version as the program (`apt-cache policy PROGRAM PROGRAM-dev` with deb-multimedia added the edition's way: `sparky-os/media/scripts/dmo-setup.sh`). No development package at that version is a stop: say so before writing code.
   OBS: deb-multimedia's source `obs-studio-dmo` builds `obs-studio`, `obs-plugins`, `libobs0t64` and `libobs-dev` at one version; `libobs-dev` carries the CMake packages `libobs` and `obs-frontend-api` (`find_package(libobs 33)`, `find_package(obs-frontend-api)`, targets `OBS::libobs` and `OBS::obs-frontend-api`).
2. **Read the program's source at that version** for: where it looks for modules, what it does at each frontend event, what reaches each encoder or writer, and what a module can change before the program reads it. Record each answer with the file and function.
3. **Write the module in the program's own form** (OBS: `OBS_DECLARE_MODULE()`, `OBS_MODULE_USE_DEFAULT_LOCALE()`, `obs_module_load()`), with the program's own catalogue format for its sentences (OBS: `data/locale/xx-YY.ini`, `obs_module_text()`), in the ten languages; the words the stereo layer shares with every program come from the layer's own catalogue (context `Stereo::FileChoiceMenu`, `/usr/share/locale/LANG/LC_MESSAGES/stereo-layer_qt.qm` through a `QTranslator`), never a copy.
4. **Package it** as the other compiled packages of ours (`sparky-os/packages/sparky-stereo-camera` is the model): `debian/` in Paweł's formula, `build.sh` with `lean.debian_prepare` and `lean.release check-debs`, `build-in-container.sh` with the provenance helper and the link gate's archive folder. `Depends: ${shlibs:Depends}, PROGRAM (>= VERSION)`, `Enhances: PROGRAM`. One row in `lists/integrations.tsv` with kind `native`.
5. **Prove it in a throwaway container**: the program driven without a person (below), each claim red without the module and green with it, a 2D control compared byte for byte, the installed package loading from the program's system folder, install and purge with and without the program (`dpkg --audit` after each step).

## How OBS 33 finds a module with nothing to click

OBS 33's plug-in manager (`frontend/plugin-manager/PluginModuleLoader_Linux.cpp`) loads, in Full mode (not in safe mode):

| Where | Binary | Data |
|---|---|---|
| System, the pack's place | `/usr/lib/<triplet>/obs-modules/plugins/<name>.so` | `/usr/share/obs/obs-modules/plugins/<name>/` |
| The person's | `$XDG_DATA_HOME/obs-studio/plugins/<name>/<name>.so` (`~/.local/share`) | `.../<name>/data/` |
| Legacy | `/usr/lib/<triplet>/obs-plugins/`, `~/.config/obs-studio/plugins/<name>/bin/64bit/` | |

OBS's own modules live in `obs-modules/core` and are "core modules", loaded in safe mode too; a pack never installs there.
OBS's Plugin Manager can switch a third-party module off: that is the program's own switch for the pack.
OBS loads native modules by itself and never loads a script by itself (scripts are the person's list in Tools, Scripts).

## What reaches OBS's encoders and muxers (33.0.1)

- **Frontend events are early.** `OBS_FRONTEND_EVENT_RECORDING_STARTING` fires in `OBSBasic::StartRecording()` before the output handler rebuilds its encoder settings (`SimpleOutput::UpdateRecording()`, `AdvancedOutput::UpdateRecordingSettings()`) and before `obs_output_start()` creates the encoders. libobs has no hook between the two: no encoder signal, nothing before `info.start` in `obs_output_actual_start()`.
- **Settings merge.** `obs_encoder_update()` applies (`obs_data_apply`) the new settings over the encoder's own, so a key the module set survives unless the frontend writes that key. The frontend writes `x264opts` only from the person's own options (Simple: "Enable Advanced Encoder Settings" with x264 options, on the stream encoder; Advanced: `x264opts` in `recordEncoder.json` or `streamEncoder.json`). So the module adds `frame-packing=3` to every x264 encoder of the main canvas that is not running, at every `*_STARTING`, and predicts the person's own options from the same files to tell before the start.
- **x264** reads its option string with `x264_param_parse()` (`plugins/obs-x264/obs-x264.c`), so `frame-packing=N` reaches x264, which writes the frame packing arrangement SEI on each keyframe, content interpretation 1 always.
- **VA-API** in OBS is FFmpeg's `h264_vaapi` and `hevc_vaapi` through `plugins/obs-ffmpeg/obs-ffmpeg-vaapi.c`; its `ffmpeg_opts` string goes to `av_opt_set()`, but the edition's FFmpeg writes the mark only from `AV_FRAME_DATA_STEREO3D` on the frames or `AVCodecContext.decoded_side_data`, which only OBS's own code can set.
- **NVENC** is OBS's own NVENC code (`plugins/obs-nvenc`; the legacy FFmpeg NVENC is off at build, and the `ffmpeg_nvenc` id is a compatibility name of the native encoder): no SEI payload route. **QSV** (`obs-qsv11`) sends payloads for HDR only. **AV1** has no frame packing message.
- **Containers.** The recording muxer is a helper process, `obs-ffmpeg-mux`, given codec, size and colour on its command line; it writes the header before the first packet and adds `codecpar` side data for HDR only. The frontend rewrites `muxer_settings` from the person's configuration at every start. So neither Matroska's StereoMode nor MP4's `st3d` can be written from a module; hybrid MP4 is OBS's own muxer (`obs-outputs`), also untold.
- **A runtime check** is possible: `obs_output_add_packet_callback()` (libobs 31 and later) hands every interleaved packet to the module; read the first video keyframe for payload type 45 and tell when it is missing.

## Driving OBS in a rig

- Xvfb and Mesa's software renderer (`LIBGL_ALWAYS_SOFTWARE=1`, `QT_QPA_PLATFORM=xcb`), a fresh configuration per case under `XDG_CONFIG_HOME`:
  - `obs-studio/global.ini`: `[General] LastVersion=...` (no automatic configuration wizard);
  - `obs-studio/user.ini`: `[General] FirstRun=true`, `[Basic] Profile`, `ProfileDir`, `SceneCollection`, `SceneCollectionFile`;
  - `obs-studio/basic/profiles/NAME/basic.ini`: `[Video] BaseCX BaseCY OutputCX OutputCY FPSType=1 FPSInt`, `[Output] Mode`, `[SimpleOutput] FilePath RecFormat2 RecQuality RecEncoder` or `[AdvOut] RecType RecFilePath RecFormat2 RecEncoder Encoder` with `recordEncoder.json` beside;
  - `obs-studio/plugin_config/obs-websocket/config.json`: `{"first_load": false, "server_enabled": true, "server_port": 4455, "auth_required": false}`.
- obs-websocket 5 with `python3-websocket`: Hello (op 0), Identify (op 1, `rpcVersion` 1), requests (op 6) and their responses (op 7). `CreateInput` with `image_source`, `CreateSourceFilter`, `StartRecord` and `StopRecord` (its `outputPath`), and `GetSourceScreenshot` (PNG of the source after its filters, at the filtered size): a filter's output read exactly, with no recording in between.
- End OBS with SIGTERM and wait; then copy `obs-studio/logs/*.txt` for the module's lines.

## Reading the result

- `ffmpeg -v info -i FILE -map 0:v:0 -c copy -bsf:v trace_headers -f null -` prints "Frame Packing Arrangement" and its fields; `ffprobe -show_frames` shows `side_data_type=Stereo 3D` and the H.264 decoder's `TAG:stereo_mode`; `mkvinfo` for StereoMode; a box scan for `st3d`.
- For the 2D control, `ffmpeg -i FILE -map 0:v:0 -c copy -frames:v 30 -f framemd5 -` of the run with the module and the run without: with a static picture the lines are identical, timestamps included.

## Traps

| Symptom | Cause | Fix, and how it was found |
|---|---|---|
| The module never loads; nothing in OBS's log | OBS 33 reads a person's plug-ins from `$XDG_DATA_HOME/obs-studio/plugins/<name>/`, not from `~/.config/obs-studio/plugins` (the legacy layout wants `bin/64bit/`) | Install there, or as the package does in the system folder; found in `PluginModuleLoader_Linux.cpp` after the log's "Loaded Modules" list lacked the module |
| The driver's first request fails with code 207, "OBS is not ready to perform the request" | obs-websocket answers before the frontend has loaded its scene collection | Repeat `GetCurrentProgramScene` until it is not 207 |
| `trace_headers` prints nothing | it logs at info level; `-v error` hides it | `-v info` |
| The rig cannot install the layer's library from a stage | `libstereo-layer1` pins `libstereo-policy1` at its exact version and needs the same `libstereo-dibr1` | Install the stage's cohort together (layer, policy, dibr), never one of them over a published other |
| `dpkg-checkbuilddeps: unmet build dependencies: node-acorn nodejs python3-yaml` | `lean.debian_prepare` adds the toolkit's own build dependencies to the prepared source | Put them in the builder image |
| The build stops in `override_dh_builddeb`: "check-link needs --archive-config / --scratch" | the Lean Code `dh_builddeb` runs the link gate during the build | Pass `SPARKY_LC_ARCHIVE_CONFIG` (Debian, deb-multimedia for a program of theirs, the published tree as `file:/repo`), `SPARKY_LC_SCRATCH`, and `SPARKY_LC_SIBLINGS_FILE` for edition packages newer than the published tree; the container needs the network for the public archives and the bubblewrap security options |
| A person's x264 options leave the recording unmarked | the frontend writes their whole `x264opts` after the module's start event | Told before the start, with the person's string and `frame-packing=3` to add; the module never edits the person's settings |
