# A relaunch soak: a stereo client killed and started many times

Learned chasing a declared video that showed flat after many relaunches (ORDER 49, November 2026).
The question is whether Stereo KWin keeps showing a declared 3D area per eye after hundreds of clients were killed, started, and had their 3D area torn down and made again in one compositor session.

## Recipe

1. **Two clients, to tell the toolkit from the compositor.**
   The player under test (a full-screen QML `Video` through the edition's Qt Multimedia, which prints `stereoVideo` and `stereoLayerActive` as they change) and a plain Wayland client that builds the same shape by hand: the window's surface grey with a transparent hole, a subsurface below it, desynchronized, placed with `wp_viewporter`, holding both eyes (left red, right blue), declared once with libstereo-declare.
   Make the plain client in the order Qt's layer uses (window mapped first, then the subsurface made, declared and committed, then the window committed again), print a line on the first frame callback of the 3D area, and read the socket every frame.
   Give it a `--no-declare` switch: the same surfaces and buffers with nothing declared is the control that must fail.
   `../scripts/subdecl.c` is that client (`--fullscreen`, `--no-declare`, SIGUSR1 for a new area); build it with the client code `wayland-scanner` makes from `xdg-shell.xml` and `viewporter.xml` and `$(pkg-config --cflags --libs wayland-client stereo-declare)`.
   `../scripts/scanout_eyes.py` names a frame read from a DRM output (side by side twin, anaglyph twin or 2D).
2. **One compositor session for the whole soak**, as a long desktop session would have; a fresh session per soak.
3. **Each cycle:** start the client; wait for its ready line (the plain client's first frame callback, the player's `stereoLayerActive true`); wait a settle time; capture; name the result; kill the client, SIGKILL and SIGTERM in turn (a Qt program has no SIGTERM handler, so both end the connection without a single destroy request); wait for it to exit; start the next one at once.
4. **Name each capture with a fixed vocabulary** and keep only the captures that are not the expected one:
   - STEREO: the left eye shows the left view, the right eye the right view;
   - PACKED (or FLAT): both views side by side in one picture, the same in both eyes, which is what the compositor shows for a surface it does not take as declared (the `--no-declare` control looks exactly like this);
   - LEFT: the left view in both eyes, which is what a compositor shows when it draws the scene once instead of once per eye;
   - OTHER: nothing drawn yet, a hole, anything else (retry twice, half a second apart, before naming it).
5. **Count the declarations from the compositor's side:** `WAYLAND_DEBUG=server` on KWin and, at the end, one `kde_stereo_content_manager_v1.create` and one `set_content(3)` per started client.
6. **Inside one client too:** a signal (SIGUSR1 here) makes the plain client tear its 3D area down in Qt's order (`stereo_remove_wayland`, then the viewport, the subsurface and the surface destroyed) and make a new declared one on the same window; capture after each new area's first frame, and kill the client every so many areas so the two kinds of teardown interleave.
7. **Bound it:** stop at the first non-STEREO capture (keep KWin's protocol log around it and its `supportInformation`), or at the number of cycles the brief sets, and say which.

Measured on Stereo KWin +stereo3d46 with Qt Multimedia +stereo3d14 (ORDER 49): 400 player and 400 plain-client runs and 400 areas remade inside 17 clients on the virtual backend, 200 runs of both on +stereo3d43, and in the VM 400 runs on VKMS with depth off, 200 with the shipped depth and 400 on virgl with depth off, all STEREO; the undeclared control PACKED or FLAT every time.
The October report (a packed frame, no anaglyph, while Qt said `stereoVideo` and `stereoLayerActive` true) is the picture of a surface the compositor did not take as declared.

## Which compositor path a capture proves

- **ScreenShot2 draws each eye itself.** With stereo content on the screen, or an output that has eyes, it renders the scene once per eye on its own and hands both side by side. So a ScreenShot2 capture proves the surface's declaration and the eye quads of its item, not the compositor's own choice to draw the output once per eye.
- **The `--virtual` backend never draws its own output per eye.** Its output layer is the base `OutputLayer`, whose `hasStereoEyes()` is false, so the compositor's pass for that output is always one; only the logical output says it has eyes (which is why ScreenShot2 answers stereo). A failure of the per-eye trigger cannot show on the virtual backend.
- **On a 2D output, ScreenShot2's stereo answer is the trigger's own predicate.** There `screenShotIsStereo()` is true only when a window that `holdsStereoContent()` is on that output, the test the compositor makes before drawing per eye on a 3D output; a one-picture capture (narrower than three times its height) names a window KWin did not find stereo.
- **The real output needs the DRM backend: VKMS in a virtual machine.**
  The station's own kernel (the edition's, whose VKMS reads an EDID through configfs) boots in QEMU with KVM, with an initramfs of a static BusyBox and the modules the guest loads (9p, overlay, the DRM helpers, `vkms` with `create_default_dev=0`), a VKMS device made in configfs with an HDMI-A connector, and the rig image exported to a folder as the root, shared read only over 9p under a tmpfs overlay.
  KWin runs with `--drm` on the VKMS card (Mesa's software renderer, no render node), and the vkms-stereo bench's `drm-grab` reads the frame KWin scans out: the real anaglyph or side by side picture.
  `QT_LOGGING_RULES=kwin_core.debug=true` makes KWin print its choice for each frame of a DRM output: `stereo-replica: NAME scene passes (one per eye)` or `scene pass (one)`.
- **virtio-gpu with virgl (the GPU of the contributor VM where the October report came from), on the RTX 3060:** QEMU's `-device virtio-vga-gl,xres=1920,yres=1080 -display egl-headless,rendernode=NODE` in a container with the card through CDI (`GBM_BACKEND=nvidia-drm`, `GBM_BACKENDS_PATH=/usr/lib/x86_64-linux-gnu/gbm`); the guest loads `virtio_dma_buf` and `virtio-gpu`, and KWin and the clients draw through Mesa's `virtio_gpu` driver.
  QEMU's `screendump` answers `no surface` for its GL scanout under `egl-headless`, and `drm-grab` maps dumb buffers only (not tried on virgl's scanout).
  Read instead KWin's own choice for the frames of one second after the client is ready (the byte range of `kwin.log` that grew in that second, counted for `scene passes (one per eye)` and `scene pass (one)`) and both eyes through ScreenShot2 in the guest; with depth off, a single frame drawn once while the declared area is on the screen names the cycle ONCE.
  The `--no-declare` control in that guest: FLAT, 0 frames per eye and 64 drawn once in the second; the declared clients: STEREO, 46 to 59 frames per eye and 0 drawn once.
- **Desktop depth hides the trigger.** With the shipped limits (`SunkLimit` 10, `PoppedLimit` 4, effects 30 and 12) KWin draws every output that has eyes once per eye, stereo content or not. To test that a declared surface alone turns the eye passes on, write `[StereoDepth]` `SunkLimit=0`, `PoppedLimit=0`, `EffectSunkLimit=0`, `EffectPoppedLimit=0` in `kwinrc` before KWin starts; run with the shipped limits as well.

## Putting a DRM output in a 3D twin without Display Settings

`kscreen-doctor` has no switch for an output's Anaglyph and Other stereo formats toggles.
Start KWin once, set the plain mode (`kscreen-doctor output.NAME.mode.ID`), stop KWin, then edit `$XDG_CONFIG_HOME/kwinoutputconfig.json`: in the `outputs` section set `"anaglyph": true` (or `"otherStereoFormats": true`) and add to the mode's `flags` `VirtualStereo` (0x20000) and the layout (`Stereo3DAnaglyphModern` 0x200, `Stereo3DSideBySideHalf` 0x20; `src/core/output.h`), with `Preferred` (0x1) cleared; the next KWin restores the twin (`canRestoreVirtualMode`).
The side by side twin is the easiest to read: the left half of the frame is the left eye.
The anaglyph (modern) filter on a scanout of a red left view and a blue right view gives (170, 0, 255); red in both eyes gives (169, 154, 0) and blue in both (111, 0, 255), the two halves of the undeclared control.

## Traps

- **Symptom:** the soak's shell stops at the end with `Syntax error: "}" unexpected` (or runs half a line).
  **Cause:** `dash` reads a script as it runs it; the script was edited while the soak was running, and after its loop it read on from its old offset in the new file.
  **Fix:** run a copy of the script, or never edit a script (or a script a guest runs over 9p) while it runs; to change a client binary under a running soak, build a new file and rename it over the old one.
- **Symptom:** the player in the VKMS guest never prints `stereoLayerActive` and the frame is black.
  **Cause:** Qt's FFmpeg backend probes the hardware decoders and takes a Vulkan device (`Checking HW context: vulkan`, `Using above hw context.`), which in a guest without a GPU is lavapipe; the player then shows nothing.
  **Fix:** `QT_FFMPEG_DECODING_HW_DEVICE_TYPES=,` (a set but empty list: no hardware decoding) and `LIBGL_ALWAYS_SOFTWARE=1` for the client.
  **How found:** `QT_LOGGING_RULES='qt.multimedia.*=true'` in one guest cycle.
- **Symptom:** none, a near miss. A process ID written by a client inside a container is that container's PID namespace number; on the host the same number is another process (here a kernel worker).
  **Fix:** kill it inside the container (`docker exec ... kill PID`), never from the host.
- **Symptom:** a KWin script run right after a kill still lists the killed client's window.
  **Cause:** a closed window stays in `workspace.stackingOrder` while it closes; three seconds later the list was empty in every round.
  **Fix:** wait before counting windows, or read `deleted`.
- **Symptom:** the plain client ends after a few in-process teardowns (here after 9 and after 16 areas), and the soak's next signal finds no process; KWin's protocol log shows the area's destruction and a `sync`, then nothing.
  **Cause:** the test client's own bug, not the compositor's: the frame callback of the area being torn down was dispatched inside the roundtrip that followed `wl_surface_destroy`, and its handler drew the next frame on the destroyed surface (a segmentation fault in `wl_proxy_marshal_flags`).
  **Fix:** forget the surface before the roundtrip and ignore callbacks of an area that is gone; then 150 teardowns 0.25 s apart ran clean.
  **How found:** the client under `gdb -batch -ex 'handle SIGUSR1 nostop noprint pass' -ex run -ex bt` (backtrace `next_frame` from `frame_done` from `wl_display_roundtrip_queue`). Make the soak say when a client ends on its own and go on with a new one, rather than stop.
- **Symptom:** the VKMS connector with the bench's 3D EDID lists no `(3D-...)` mode under the station kernel.
  **Fix:** use the virtual twins (above), which every output has; the HDMI 3D modes from an EDID are the vkms-stereo bench's kernel and its patches.

- **Symptom:** `rm -rf` of the exported guest root fails with "Permission denied" on `run/systemd/dissect-root`.
  **Cause:** `docker export | tar -x` as your user keeps the image's modes, and that folder has none for you.
  **Fix:** `chmod -R u+rwX` the root first.

## Perks

- The plain client and the player use the same layer shape, so a difference between them points at the toolkit, and the same result in both points at the compositor.
- The undeclared control is the exact picture of the failure (PACKED), so the classifier is checked against it before the soak.
- One VM image serves every KWin build: the guest root is the rig image exported to a folder; replace KWin in the image, export again, boot.
