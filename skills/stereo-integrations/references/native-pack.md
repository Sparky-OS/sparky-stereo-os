# A native pack: a compiled module for another program

Written on 2026-11-20 from the first native pack, `sparky-stereo-obs` (ORDER 61, milestone 1), a module for OBS Studio 33.0.1 as deb-multimedia ships it; extended on 2026-11-21 (milestone 2) with the default and the program rebuilt as ours, and on 2026-11-22 (milestone 3) with the preview as a 3D area and scenes in one eye's space.
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

## 3D on by itself (a capture program's default)

A capture or recording program starts in 3D when the desktop is in 3D, and in 2D when it is not (Daniel, 2026-11-19, on Spectacle: "the default mode is 3D when 3D is active"; "in 2d only, the default is also a 2D picture"; "no matter what's underneath").
An opt-in switch is a defect; "Enable 3D" is the off switch (stereo-integrations-auto-enable, 2026-11-18).

- **One signal:** the stereo layer's `Stereo::ScreenMode`, one per `QScreen`, through the edition's libkscreen (the current mode's `Stereo3D` field and the output's `stereoPairMode`); 3D is active when any screen reads Stereo or Anaglyph. Spectacle +stereo3d3 reads exactly this (`ImagePlatformKWin::updateStereoOutputs()`); a 2D screen copied to a 3D target counts through the target. Link `Stereo::Layer` (`find_package(StereoLayer)`), never a second detector.
- **Decide once a start, after the modes are read:** ScreenMode is Unknown until libkscreen's first configuration arrives (about 0.1 s in the rig); wait for it with a bound (5 s) and tell when it cannot be read.
- **Never over the person:** their own choice in the program's dialog is kept from then on; a profile that already holds their work (OBS: any scene item) keeps its canvas and is told once, with the action.

## The program rebuilt as ours (when a module cannot reach the writers)

A module could not make OBS 33's VA-API, NVENC or Quick Sync write the frame packing SEI, nor its muxers write StereoMode or `st3d` (above). The edition then rebuilds the program (`sparky-os/packages/obs-studio-dmo`): deb-multimedia's source, patches appended to its `debian/patches/series` with DEP-3 headers, a `+stereo3dN` entry dated from the recipe, `lean.debian_prepare`, the link gate.

- The origin's `debian/control` stays as it ships: the build's provenance step stamps the binaries (`Maintainer:` ours, `Original-Maintainer:` theirs, `Homepage:`, `Bugs:`).
- One fact in the program's core, read by every writer: libobs gains the canvas's layout (`obs_set_video_stereo3d()`, `obs_get_video_stereo3d()`, `obs_encoder_get_stereo3d()`), with FFmpeg's `AVStereo3DType` values, the whole set. New symbols only, so modules built for the shipped libobs still load; the shlibs minimum moves to the rebuild (`dh_makeshlibs -plibobs0t64 -V"libobs0t64 (>= VERSION~)"`, Debian Policy 8.6), so a module that calls them cannot be installed beside the shipped libobs.
- x264: `i_frame_packing` set after the person's own options, so they cannot remove it.
- VA-API: `AV_FRAME_DATA_STEREO3D` in `AVCodecContext.decoded_side_data` before `avcodec_open2()` and on the frame every surface copies with `av_frame_copy_props()`; the edition's FFmpeg writes the SEI from it.
- NVENC: an `NV_ENC_SEI_PAYLOAD`, payloadType 45, built bit by bit (H.264 D.1.26, H.265 D.2.16, with the payload's alignment bits); HEVC only types 3 to 5.
- The muxer helper: one more positional argument, then `AV_PKT_DATA_STEREO3D` in `codecpar->coded_side_data`; FFmpeg's MP4 muxer writes `st3d` only at `FF_COMPLIANCE_UNOFFICIAL` and only left eye first (`mov_write_video_tag()`, `mov_write_st3d_tag()`).
- OBS's own MP4 muxer: an `st3d` FullBox after `pasp` in each visual sample entry.
- The encoders and muxers are core modules in the `obs-studio` package (`/usr/lib/<triplet>/obs-modules/core/obs-x264.so`, `obs-ffmpeg.so`, `obs-nvenc.so`, `obs-outputs.so`), not in `obs-plugins`; read their `NEEDED` lines there: `obs-ffmpeg` links the edition's shared FFmpeg (which writes the VA-API SEI), `obs-x264` the shared libx264.

## What a screencast gives a recorder on a 3D desktop (KWin +stereo3d59, read at the source)

OBS records the screen through the portal, which asks KWin for a `zkde_screencast` stream. `OutputScreenCastSource::render()` draws the scene once with `StereoEye::None`, where a declared stereo surface shows its left view; both eyes are drawn only for a split-eye phone panel (`isSplitEyeCapture()`, `renderStereo()`). The stream's PipeWire format can say its layout (`SPA_FORMAT_VIDEO_multiviewMode`, `multiviewFlags`, `views`), and OBS's PipeWire source already parses it (`spa_format_video_raw_parse()`) without reading it. So a 3D desktop recorded through the portal is one picture of left views, unmarked, until KWin draws both eyes for any output in a 3D mode and announces `SPA_VIDEO_MULTIVIEW_MODE_SIDE_BY_SIDE`, and the program reads it.

## The preview as a 3D area, and scenes in one eye's space (milestone 3, 2026-11-22)

A capture program's preview of a 3D canvas is a 3D area: its own surface, declared full side by side, both eyes in it, the window around a 2D window (skill `stereo-window-3d-area`).
OBS draws each preview (the main one, studio mode's program view, projectors, filter dialogs) with EGL straight onto a native child widget's own `wl_surface` (`OBSQTDisplay`, `winId()`), so that surface is the area; no hole in the window is needed.
OBS's overlays (safe areas, the selection box and handles, spacing labels) are drawn into the same surface, so the surface holds two views and every overlay is drawn in each view at the place of what it marks there.
That only has an answer when the scene is laid out in one eye's space and drawn once per eye, so the preview and the scene composition are one change:

- **libobs** (patch 0008): a side by side main canvas lays its scenes out in one eye (`obs_get_video_eye_size()`: the scene's and the groups' size) and `render_main_texture()` draws the view once per eye on its half, `obs_get_render_eye()` telling sources which eye; a flat source comes out the same in both eyes (the screen plane), a source holding two views gives each eye its own. A display can hold two views (`obs_display_set_views()`): the swap chain is twice as wide, the draw callbacks run once per eye on that half with one view's size, and viewports set while the swap chain is the target are relative to the view. In an eye pass the canvas texture is drawn as that eye; outside one it is drawn whole, so a view one eye wide shows the left eye whole.
- **The frontend** (patch 0009): every scene-space use of the canvas size (preview and program layout, projectors, multiview, alignment, dropped files, spacing helpers, scroll limits) takes one eye; outputs and encoders keep the whole canvas. Each display widget carries its `obs_display` as the Qt property `obsDisplay`.
- **The pack**: follows every `OBSQTDisplay` (an application event filter: Show and the property's change), declares its surface with libstereo-declare 1.4 or later (protocol version 2: a declared surface with no viewport is one view wide), sets two views, and between the two disables the display so no frame is committed declared with one view or undeclared with two. Hidden: the declaration goes first (Qt destroys a hidden native window's `wl_surface`). X11, a desktop without the protocol, a refused declaration: one view, the left eye whole, and the status bar says why; a 2D screen: declared (KWin shows the left eye) and said.
- **The Stereo input filter** on a 3D canvas is one view wide and gives each eye pass its view.
- **The rig** (`m3-run.sh` in the lane folder): the milestone's libobs, frontend and pack copied over the installed build in a throwaway container, Stereo KWin's 3D twin mode, a fresh account (3D on by itself), a stereo picture through the filter and a flat picture placed by obs-websocket, ScreenShot2 for both eyes, a recording as the canvas's own eyes. Rows: one 16:9 preview rectangle in both eyes, each eye's colour at three places, the stereo square's disparity against −40 eye samples times the preview's scale, the flat picture at one place, 0 differing pixels around the preview, the overlays at the same pixels, each preview eye against the recording's eye.

## Driving OBS in a rig

- Xvfb and Mesa's software renderer (`LIBGL_ALWAYS_SOFTWARE=1`, `QT_QPA_PLATFORM=xcb`), a fresh configuration per case under `XDG_CONFIG_HOME`:
  - `obs-studio/global.ini`: `[General] LastVersion=...` (no automatic configuration wizard);
  - `obs-studio/user.ini`: `[General] FirstRun=true`, `[Basic] Profile`, `ProfileDir`, `SceneCollection`, `SceneCollectionFile`;
  - `obs-studio/basic/profiles/NAME/basic.ini`: `[Video] BaseCX BaseCY OutputCX OutputCY FPSType=1 FPSInt`, `[Output] Mode`, `[SimpleOutput] FilePath RecFormat2 RecQuality RecEncoder` or `[AdvOut] RecType RecFilePath RecFormat2 RecEncoder Encoder` with `recordEncoder.json` beside;
  - `obs-studio/plugin_config/obs-websocket/config.json`: `{"first_load": false, "server_enabled": true, "server_port": 4455, "auth_required": false}`.
- obs-websocket 5 with `python3-websocket`: Hello (op 0), Identify (op 1, `rpcVersion` 1), requests (op 6) and their responses (op 7). `CreateInput` with `image_source`, `CreateSourceFilter`, `StartRecord` and `StopRecord` (its `outputPath`), and `GetSourceScreenshot` (PNG of the source after its filters, at the filtered size): a filter's output read exactly, with no recording in between.
- End OBS with SIGTERM and wait (OBS 33 closes and saves on SIGTERM); then copy `obs-studio/logs/*.txt` for the module's lines.
- **A person's first start in Stereo KWin:** `kwin_wayland --virtual --xwayland` with `KWIN_VIRTUAL_STEREO_MODES=1` (the output gets its 3D twins; `kscreen-doctor output.Virtual-0.mode.N` picks one with `stereo3D` 1), `--cap-add SYS_NICE` on the container, `dbus-update-activation-environment WAYLAND_DISPLAY XDG_RUNTIME_DIR` as a Plasma session does, a fresh `HOME` with `~/Videos`, and OBS started with its desktop entry's own `Exec` line. "Told once" is proved by a second start of the same account, whose log has no notice.

## Reading the result

- `ffmpeg -v info -i FILE -map 0:v:0 -c copy -bsf:v trace_headers -f null -` prints "Frame Packing Arrangement" and its fields (H.264: `frame_packing_arrangement_type`, `content_interpretation_type`; H.265: `fp_arrangement_type`, `fp_content_interpretation_type`, so a reader greps both); `ffprobe -show_frames` shows `side_data_type=Stereo 3D` and the H.264 decoder's `TAG:stereo_mode`; `mkvinfo` for StereoMode; a box scan for `st3d`.
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
| `kwin_wayland: Operation not permitted` in a container | the binary carries a file capability | `--cap-add SYS_NICE` |
| OBS's `Stereo::ScreenMode` stays Unknown while `kscreen-doctor` works | libkscreen asks its backend launcher over D-Bus; a D-Bus-activated service does not get `WAYLAND_DISPLAY` unless the session puts it in the activation environment | `dbus-update-activation-environment WAYLAND_DISPLAY XDG_RUNTIME_DIR` after the compositor starts, as Plasma does |
| `StartRecord` is accepted, `StopRecord` answers 501 in a fresh account | OBS's first-run configuration wizard holds the window, or the default folder `~/Videos` does not exist (OBS refuses the path) | the rig writes OBS's own `[General] LastVersion` (no stereo setting) and makes `~/Videos`, which xdg-user-dirs makes on a real account |
| The rebuilt binaries show our `Maintainer:` and no `Original-Maintainer:` | the recipe rewrote `Maintainer:` in the source's `debian/control`; the build's provenance step (`repo/provenance.sh --tree`, run by Lean Code's `dh_builddeb`) derives `Original-Maintainer:` from the source's Maintainer, so the origin's name was already gone | leave the origin's `debian/control` as it ships (the edition's FFmpeg keeps deb-multimedia's Maintainer in its source); provenance stamps the binaries, found by `dpkg-deb -f` against a published rebuild |
| CMake: "Required submodule 'obs-websocket' not available" when building OBS by hand | the orig tree has an empty `plugins/obs-websocket`; deb-multimedia's rules remove it at clean and link the component tarball there | do the same, or build through `dpkg-buildpackage` |
| A person's x264 options leave the recording unmarked (OBS as shipped) | the frontend writes their whole `x264opts` after the module's start event | Fixed in the edition's OBS (x264's frame packing set after their options); with the shipped OBS, told before the start |
| An HEVC recording reads "type none" though the encoder logged the message | the reader grepped H.264's field names; FFmpeg's H.265 trace names them `fp_arrangement_type` and `fp_content_interpretation_type` | grep both names; found by reading the trace of a marked HEVC file |
| Two recordings compare identical, yet one of them was never read | OBS names files `YYYY-MM-DD HH-MM-SS.mkv`; an unquoted path splits at the space, both sides read nothing, and empty equals empty | quote every path and check the line count before the comparison (the 2D control compares 30 lines) |
| A module that calls the rebuilt libobs's new functions installs beside the shipped libobs and fails to load | deb-multimedia's shlibs say `libobs0t64 (>= 1:33.0.1)`, which the rebuild keeps unless told | `dh_makeshlibs -V` for libobs0t64 in the rebuild's rules; found by `dpkg-deb -e` of both builds' libobs0t64 |
| The right eye of a 3D canvas shows the left eye's picture after a filter or inside a transition | `gs_texrender_begin()` refuses a texrender already drawn since its reset (once per frame, at tick), so the second eye pass reuses the first eye's texture | A texrender records the pass it was drawn in, and each eye pass starts a new one (`gs_texrender_new_pass()`); 2D canvases never start one. Found by reading every `gs_texrender_reset` and `begin` before the first run |
| Every viewport of an eye pass lands on the left half of a two-view display, or filters draw at an offset | an offset added to every `gs_set_viewport()` also moves viewports set while a filter draws into its own texture | offset only while the swap chain is the render target (`device_get_render_target()` is NULL); `gs_get_viewport()` subtracts it, so push and pop stay paired |
| The eye being drawn reads "left" before any eye pass | libobs's core is zero-filled at start | store the eye plus one (0: no pass) |
| `QEvent is not a type`, `'Show' is not a member of 'QEvent'` when building the pack | `stereo-declare.h` includes Xlib, whose macros (`KeyPress`, `None`, `Bool`) break Qt's headers included after it | include it after every Qt header |
| A dev build of OBS loads no module and its data is missing | `OBS_INSTALL_PREFIX` took `CMAKE_INSTALL_PREFIX`'s default, /usr/local (debhelper passes /usr) | configure with `-DCMAKE_INSTALL_PREFIX=/usr` |
| obs-websocket answers nothing in a dev build | obs-websocket is a core module (`obs-modules/core`), loaded only when the frontend is built with `ENABLE_WEBSOCKET`; dropping `-DENABLE_WEBSOCKET=OFF` from the command line keeps OFF in CMake's cache | link the component's tree at `plugins/obs-websocket` as deb-multimedia's rules do and pass `-DENABLE_WEBSOCKET=ON` |
| The host cannot remove a case folder | the case ran as root to copy the build into `/usr` | the case script hands its folder back (`chown` to the host's IDs) at its end |
| A row says the right eye shows red, or the overlays differ between the eyes | OBS's selection lines are red and its safe areas translucent: a red line is invisible over the red eye, a translucent one takes each eye's colour | sample each eye's colour away from the overlays, and compare where overlays are drawn (masks with red and blue folded together), never their colours |
