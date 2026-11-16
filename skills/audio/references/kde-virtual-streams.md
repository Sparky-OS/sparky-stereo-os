# KDE virtual streams and an isolated audio rig

Measured on Plasma 6.7.4, pulseaudio-qt 1.9.0, PipeWire 1.6.9 and WirePlumber 0.5.19, November 2026.
The visibility changes described here are a tested edition candidate, not a published package.

## Models and routes

PulseAudio calls playback streams sink inputs and recording streams source outputs.
These are distinct from sinks (output devices) and sources (input devices).
`pulseaudio-qt/src/stream_p.h` classifies a stream as virtual when `pa_*_info.client` is `PA_INVALID_INDEX`.
That does not mean the stream cannot be moved.

`plasma-pa/src/qml/PulseObjectFilterModel.qml` filters the models consumed by both interfaces.
The released `applet/main.qml` and `src/kcm/ui/main.qml` unconditionally exclude the `VirtualStream` role.
The applet's `showVirtualDevices` setting applies only to device models in the release.
The candidate adds an invalidating `filterVirtualStreams` property, binds the applet's stream models to the existing setting, and adds a separate `ShowVirtualStreams` key in `plasmaparc`, default false, for the Sound page.
Keep the libcanberra exclusion, accepting a null client before inspecting its name.

The page's playback delegates need `paSinkModel` and recording delegates need `paSourceModel` as their device selector model.
The selector's `DeviceIndex` assignment and the applet's `ListItemMenu` use pulseaudio-qt's existing stream move operation.
No new routing implementation is needed just to expose virtual streams.

PipeWire 1.6.9's `module-protocol-pulse/pulse-server.c`, `fill_sink_input_info()` and `fill_source_output_info()`, deliberately omit client IDs when `pw_manager_object_is_virtual()` is true.
The latter reads `node.virtual` in `manager.c`.
A real PipeWire client may therefore appear client-less through PulseAudio when its node is virtual.
Keep this classification; choose visibility in KDE instead of changing every PulseAudio client's view.

## Working rig recipe

Use a throwaway container with its own D-Bus, Xvfb, PipeWire, pipewire-pulse and WirePlumber.
Give it no sound device, host runtime socket, host display or host home.
Run the fixture processes as an ordinary user, with core dumps disabled.
The reproducible scripts live in [the build repository's plasma-pa recipe](https://github.com/Sparky-OS/sparky-stereo-os-build/tree/main/upstream/plasma-pa); they are staged work until the corresponding branch is integrated.

1. Install the published release, build the candidate into a separate prefix, and record actual package versions.
2. Create two null sinks with `pactl load-module module-null-sink`, and two sources with `pw-cli create-node adapter` using `factory.name=support.null-audio-sink`, `media.class=Audio/Source` and `object.linger=true`.
3. Load `module-loopback` between one source and one sink.
   Start a real filter-chain with a builtin copy node, a capture-side `Audio/Sink` and a playback stream targeted at the same sink.
   Copy the `context.spa-libs` mappings from the installed `filter-chain.conf` when using a standalone configuration.
4. Start a `pw-loopback` control with `node.virtual=false` on both streams, as a client-backed bridge.
   Use explicit fixture targets with `node.dont-fallback=true`; never give client-owned streams `node.linger=true`.
5. Read `pactl -f json list sink-inputs`, `source-outputs` and `pw-dump`.
   The module and filter streams have no PulseAudio client and `node.virtual=true`; the bridge has a client and `node.virtual=false`.
6. Open the actual page with `kcmshell6 kcm_pulseaudio` and the actual widget with `plasmawindowed org.kde.plasma.volume`.
   The published page and widget hide the virtual streams, even with the widget's virtual-device setting enabled.
   The candidate exposes them when enabled; move each through the UI and independently verify its selected sink or source with `pactl`.
7. Capture the windows at 100% and 125%, then hide the streams again.
   Compare the unchanged page content against the published page, reporting the new toolbar action and any deliberate defect repair separately.
   A selector whose model was broken in the release cannot honestly be called pixel-identical after repair.
8. Load the edition's existing new-output hook in the private session only.
   After its startup grace period, add synthetic USB and Bluetooth sinks, check the live default changes, remove them, and require the saved choice to return.
   The explicitly targeted bridge must remain on its selected sink throughout.
9. Stop every fixture and session process and remove the container by its literal name.

## Traps

- **A toggle changes once but the list stays unchanged.**
  Cause: a function stored inside the filter array closes over a setting without changing the array binding or invalidating the proxy.
  Fix: an explicitly bound filter property with `on...Changed: invalidate()`.
  Found by checking the model's invalidation signals before the live toggle proof.
- **The recording stream has no device selector.**
  Cause: the 6.7.4 page assigns `deviceModel: sourceModel`, which is undefined in that delegate.
  Fix: `deviceModel: paSourceModel`.
  Found by the published window's `ReferenceError` and its empty selector, then a successful candidate move verified through PulseAudio.
- **The candidate looks exactly like the release.**
  Cause: a CMake prefix installs plugins under `lib/.../plugins` and QML under `lib/.../qml`, whereas Debian uses `lib/.../qt6/plugins` and `lib/.../qt6/qml`.
  Fix: read `install_manifest.txt` and set `QT_PLUGIN_PATH`, `QML_IMPORT_PATH`, `LD_LIBRARY_PATH` and `XDG_DATA_DIRS` to those actual paths.
  Found by the absent new action and the installed manifest.
- **The window has no accessible children.**
  Cause: Qt starts before the accessibility bus exists.
  Fix: request `org.a11y.Bus.GetAddress` before starting Qt, with accessibility enabled in the private session.
  Found by an empty AT-SPI desktop tree while the captured window was visibly populated.
- **A click works at 100% and misses at 125%.**
  Cause: Qt's AT-SPI rectangles use logical coordinates while xdotool uses X pixels.
  Fix: multiply the coordinates by the tested scale with the window placed at the origin.
  Found by comparing the accessible rectangle with the actual screenshot and the unchanged configuration key.
- **The applet menu appears in the image but not the accessible tree.**
  Cause: the native menu is a separate override-redirect X window.
  Fix: read that window's geometry with `xwininfo` and click the visible entry, then assert the stream list and server state changed.
  Found by the screenshot, X window tree and absent AT-SPI menu children.

## What CA0132 source can establish

Linux's `sound/hda/codecs/ca0132.c` (formerly `sound/pci/hda/patch_ca0132.c`) defines a dedicated `CA0132 What U Hear` capture PCM on `adcs[2]` and capture gain/mute controls on node `0x0a`.
Several DSP initialization paths select a WUH source and set that internal connection to 48 kHz.
The driver also explicitly disables an older input-loopback route because it was unreliable.
A playback-capture path is not proof of microphone-to-headphone monitoring, a simultaneous microphone mix, or zero measured latency.
The generic [ALSA HD-audio control documentation](https://docs.kernel.org/sound/hd-audio/controls.html) describes codec-specific loopback controls; it does not document a CA0132 microphone mixer guarantee.
A bench run must isolate the microphone and playback signals, record each capture path separately with WUH off/on, check the selected output, and measure the impulse delay and negotiated format before promising either hardware mixing or zero-latency monitoring.
