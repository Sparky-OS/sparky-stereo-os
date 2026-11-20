# A 2D source copied onto a 3D target

Baseline reconciliation on Stereo KWin 6.7.4 +stereo3d60, plasma-wayland-protocols +stereo3d12, and libstereo-declare 1.11.1 (ORDER 763).
This is a baseline recipe, not a claim that the requested desktop depth has been implemented.

## Recipe

1. Use the DRM backend on two VKMS HDMI connectors inside an isolated guest, with a 1920×1080 mode on each.
   Follow [real output readback](real-output-readback.md) for the guest and root, and create a primary plane, CRTC and encoder for each connector.
   Enable the device only after linking both connector chains and setting their EDIDs.
   Run the guest through an init process if Docker runs `timeout` as its first program.
2. Start KWin once and keep `kwinoutputconfig.json` and `kscreen-doctor -o` from that session.
   Restore the configuration before each fresh compositor start.
   In the `outputs` section, retain each output's UUID and set its mode flags; in the matching `setups` entries, set the target's `replicationSource` to the source's UUID and give both position 0,0.
   Read the restored configuration and doctor output back before judging a capture.
3. Run these four cases separately, with ordinary undeclared windows first:

   | Case | Source | Replica target | Readback |
   | --- | --- | --- | --- |
   | a | 2D mode | side by side full, 1920×1080 per eye | both connectors' scanouts |
   | b | 2D mode | modern anaglyph twin | both scanouts; the filtered target is not a pair of raw eyes |
   | c | 2D mode | native split-eye phone panel | source scanout and actual PipeWire frame |
   | d | side by side full | side by side full | both scanouts and replica-copy log |

   A native SBS-full mode has flag `0x100`; the modern anaglyph twin has `0x20000 | 0x200`, with `anaglyph: true`.
   These flags come from that source version's `OutputModeline`, not DRM's mode flags.
   A 3D-capable monitor also lists a plain 2D mode; that remains the existing way to keep its copy flat.
4. Start two ordinary windows, place them on the source, and capture the source and target independently.
   The layer fixture `subdecl --no-declare` makes an ordinary window; without that option its declared area gives red to the left eye and blue to the right.
   Keep the window and its frame callbacks alive throughout capture.
   Distinguish a moving frame marker from a change to the desktop's geometry when comparing captures taken at different times.
5. Select each connector explicitly with the bench's reader:

   ```sh
   source_id=$(cat /sys/class/drm/card0-HDMI-A-1/connector_id)
   target_id=$(cat /sys/class/drm/card0-HDMI-A-2/connector_id)
   drm-grab /dev/dri/card0 source.ppm "$source_id"
   drm-grab /dev/dri/card0 target.ppm "$target_id"
   ```

   The optional third argument is the numeric connector ID.
   Without it, `drm-grab` retains its original first-active-CRTC behavior.
   A missing or inactive requested connector fails; it never captures another connector instead.
6. For the phone, use the same existing v7 request as KRdp: `stream_virtual_output_with_properties`, a persistent synthetic identity, panel pixels, refresh in millihertz, scale, physical size and `headset=1`.
   A 3840×1080 panel gives two 1920×1080 eye viewports at scale 1.
   Keep the requesting client connected; closing it removes the panel.
   Save the panel's configuration, set its replica source and reconnect it with the same identity to exercise restoration.
   Receive the actual PipeWire frame, rather than taking a screenshot of the source.
7. Enable `QT_LOGGING_RULES=kwin_core.debug=true` and retain the full log.
   Count `scene pass (one)`, `scene passes (one per eye)` and `scene passes 0, eye copies 2` separately by output.
   The phone's `OutputScreenCastSource::renderStereo()` paints each stream eye separately; these stream paints are not counted by the compositor's `stereo-replica` log.
   Do not report that log as the total number of phone stream paints.
8. Probe swap with the declared fixture as well as with the ordinary desktop.
   Change only one output's `stereoSwapEyes`, restart with the saved topology, and capture both outputs.
   An ordinary flat pair alone cannot distinguish left from right.
   Check the installed KScreen page and its model role separately from the compositor setting.

## What the baseline establishes

In case a, the actual target scanout contains two 1920×1080 regions with zero differing pixels under two ordinary windows.
The source is one 1920×1080 picture.
The compositor logs one source pass and one pass per target eye.
Case c also delivers a real 3840×1080 PipeWire frame with zero differing pixels between its eye regions.
The source and virtual panel each log single display scene passes; the stream's own per-eye paints are separate.
Case d takes the existing replica-copy path: the replica logs zero scene passes and two eye copies, and the captured eyes differ.
These results expose the missing ordinary-desktop depth on a replica of a 2D logical output.
The initial four-case captures do not establish a complete desktop level table or a corrected implementation.

With the declared fixture on the 2D source, its normal scanout is red and its swapped scanout is blue, while the target's red/blue eye witnesses retain their order.
Swapping the physical replica exchanges its witnesses; swapping the native phone panel leaves the received stream's witnesses in their original order on this baseline.
KScreen +stereo3d14 gates the swap loader on the output's swap capability and whether any advertised mode is stereo, rather than the session's current eye composition.
The measured phone output advertises no swap capability, so that loader stays hidden there.
These page conclusions combine an actual output-device trace with the shipped QML and model binding; they are not an interaction test of an opened settings page.

## Preserve the complete level table before changing the engine

Use a static fixture with one layer-shell desktop, one layer-shell dock, six ordinary toplevels, and a menu with a submenu.
Put a narrow white vertical probe in every surface on a solid background, with the six windows at distinct vertical positions, and make the sixth window active.
Create the menu chain only after window placement has settled.
Capture both connectors from the same guest and measure each probe's left and right x bounds at a fixed row.
Keep the settings, output configuration, actual loaded library hash, captures and the ten measured rows together.
Compare the modified 3D-source control and the modified 2D-source replica against this table without changing the fixture, EDID, scale, settings or measurement.
The existing display policy can multiply the person's limits for the output's physical size; compare the measured baseline exactly rather than substituting the configured numbers for measured pixels.

The +60 continuation fixture measured matching source and replica rows: wallpaper −13, dock 0, the six windows −13/−10/−8/−5/−3/0, menu +5 and submenu +10 pixels of left-minus-right parallax.
These are the results of that EDID and fixture, not universal depth defaults.
No depth arithmetic was changed to obtain them.

## Traps

- **Both calls capture the same output.**
  The original `drm-grab` accepts only a card and filename and reads the first active CRTC.
  Select a connector by its sysfs connector ID; the reader resolves its current encoder and CRTC.
  Found by the reader's usage error and by checking a 1920-wide source against a 3840-wide SBS-full target.
- **A PNS file decodes but has no stereo mark.**
  Pillow's `PngInfo.add(b'sTER', ...)` does not preserve this public chunk through its PNG writer.
  Write the PNG pixels, then use the existing `stereo-pictures/scripts/stereo_pack.py pns INPUT.png OUTPUT.pns` writer and run `stereo_verify.py pns OUTPUT.pns`.
  Found by parsing every chunk and CRC: the first attempt had only IHDR, IDAT and IEND; the edition's writer produces IHDR, sTER, IDAT and IEND with mode 1.
  Reopen the result and compare its pixels with the captured pair.
- **A source PNS looks like a measured stereo source.**
  A mono screen has one measured picture.
  Repeating that picture twice permits stereo-picture viewing, but the caption must say so; it does not measure a second source eye.
- **D-Bus script loading reports “Fewer items found in D-Bus signature than in Python arguments”.**
  Qt exports both one-argument and two-argument `loadScript` methods, and dbus-python's introspection selected the one-argument form.
  Use an explicit `ss` signature, as the existing Gio script helper does, and let the asynchronous script run before unloading it.
  Found by the traceback and `Scripting::loadScript` declaration.
- **The guest exits before a doctor result, then its init panics.**
  The rig lacked `qt6-wayland`, and `kscreen-doctor` aborted because no shell integration loaded.
  Install that package and preserve the child's failure status while still shutting the guest down normally.
  Found by the doctor's “No shell integration named xdg-shell” error; KWin itself had already initialized OpenGL and both outputs.

- **A layer-shell panel sinks with ordinary windows in the level fixture.**
  KWin classifies the layer-shell namespaces `desktop` and `dock` specially; arbitrary fixture namespaces do not acquire those roles from the layer alone.
  Give the wallpaper namespace `desktop` and the panel namespace `dock`, then repeat the unchanged baseline capture.
  Found by comparing the fixture's namespace strings with `LayerShellV1Window::scopeToType()` after the first diagnostic capture.
- **A non-root test's D-Bus reports an allocation failure and EOF before any test starts.**
  The container has no password-database entry for the numeric test UID.
  Supply an entry for that disposable user before `dbus-run-session`; keep the test unprivileged.
  Found by the preceding “Could not get password database information for UID” diagnostic.
- **KWin configures for packaging but its test build cannot find `libei-1.0`.**
  The integration tests use the libei client library in addition to the libeis server library required by the production build.
  Install the available `libei-dev` in the disposable test builder, then configure the tests again.
  Found by the test-enabled CMake package check; this is a test-builder dependency, not a new runtime dependency.

Use libstereo-declare with the output-proxy teardown fix, commit `bc7d18f`, when running these clients.
Versions 1.11.0 and uncorrected 1.12.0 can leave output proxies on a private event queue after `finish()` and abort the client when that queue is destroyed.
The rig's 1.11.1 source carries that fix; verify the library actually loaded, not just the package database's version after an overlay install.
