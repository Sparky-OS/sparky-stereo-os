# Reading a real output back: the frame the display gets, and every buffer the program committed

Learned on a declared scene that showed one eye twice on a side by side (full) output while every rig capture showed two eyes (ORDER 555, November 2026).
The question a capture cannot answer is what the output's own frame holds, and which layer made it so: the program, its toolkit, Mesa or the compositor.

## Why a ScreenShot2 capture on a virtual output is not enough

- ScreenShot2 draws each eye itself from the scene, and the `--virtual` backend's output has no eyes: a fault in the output's path does not show ([relaunch-soak.md](relaunch-soak.md), "Which compositor path a capture proves").
- A capture is one moment. A program that hands over two eyes in most frames and one picture in a few shows two eyes in a capture taken at the usual time, and the flat picture stays on the screen when the scene stops moving.
- So a proof for a real output has three readings of the same session, and they must agree: every buffer the program committed, to the last one; the frame the output scans out; and the compositor's own choice for each frame.

## Recipe

1. **A guest with a DRM output in a 3D mode, no card.**
   The vkms-stereo bench's kernel and initramfs, the rig image exported to a folder as the root (9p, read only), one VKMS HDMI-A connector that reads an EDID listing the HDMI 3D structures, KWin with `--drm` ([vkms-stereo](../../vkms-stereo/SKILL.md)).
   `tools/vkms-stereo-bench/realoutput/run.sh NAME CASE.sh [ROOT]` boots one guest per case; `steps.sh` starts KWin, and gives the case `setmode sbs-full` (also `plain`, `sbs-half`, `tab`, `fp`), `grab TAG` and `passes TAG`.
2. **The output's frame:** `grab` runs the bench's `drm-grab` until two grabs a second apart are equal and saves the frame as a PPM.
   `halves.py FRAME.ppm` counts the pixels that differ between the two halves of a side by side (full) frame, says where they are and gives each half's mean colour there.
   0 differing pixels with a stereo scene on the screen is one eye twice.
3. **Every committed buffer, to the last:** preload the recorder (`scripts/wlrec.c`) into the program with `WLREC_MAX` larger than the number of commits in the run, and check that the log ends before the limit.
   `halves_raw.py DIR` prints the same count for each buffer in commit order; the last line is the buffer left on the screen.
   The recorder's default keeps the first eight buffers: a run cut there says nothing about the picture that stays.
4. **The compositor's choice:** `QT_LOGGING_RULES=kwin_core.debug=true` makes KWin print `scene passes (one per eye)` or `scene pass (one)` for each frame of a DRM output; `passes TAG` counts them since the last call.
5. **Read the three together.**
   - The last buffer's halves differ and the frame's do not: the fault is after the program (the compositor's output path). Check the passes.
   - The last buffer's halves are equal: the compositor shows what it was handed; the fault is in the program, its toolkit or Mesa. Go to step 6.
   - Both differ by the same count: a pass.
6. **Tell Mesa from the toolkit with the smallest real client.**
   `vk2layer.c` is one xdg toplevel whose Vulkan swapchain has two array layers, red in layer 0 and green in layer 1, a blue level counting the frames, `SWAPCHAINS` swapchains one after the other and `FRAMES` frames on each (`SAME=1` is the control with both layers red).
   Build it with `wayland-scanner`'s code for `xdg-shell.xml`, `-lvulkan -lwayland-client`, and run `cases/vk2layer.sh`.
   Every buffer must differ and the frame must be red in the left half and green in the right; then Mesa's packing, its declaration and the compositor are right, across swapchain recreation, and the fault is above them.
7. **The control route:** the same program through its other declaring route, or with stereo off, in the same guest.
8. **A guest with virtio-gpu and no GL** (an installed image under QEMU, `-device virtio-vga`): QMP `screendump` is the output's frame; run `halves.py` on it. With `virtio-vga-gl` under `egl-headless`, `screendump` answers `no surface`: read KWin's passes and a recorder run instead.

Measured with this recipe on Stereo KWin +stereo3d46 and +stereo3d54 with Mesa +stereo3d17 and +stereo3d19 (VKMS, software rendering): `vk2layer` with three swapchains of three frames, all nine buffers differ (230,400, 241,920 and 253,440 pixels, each the whole view), and the frame is red left and green right over 253,440 pixels.
The control with both layers red (`SAME=1`): 0 differing pixels in every buffer and in the frame, so the two readings can fail.

## Stressing a window drawn once per eye: the events that end in an expose

A window drawn as a pair is at risk wherever the toolkit draws a frame outside its ordinary path: a window hidden and shown, minimized and restored, on another desktop and back, resized while still, closed while it is being exposed, and every frame whose callback came late.
The stress runs each of those on the smallest window that can be read, in the guest, and reads the output's frame after each.

1. **The window:** `pairstress/pairstress.cpp` (Qt Quick, `_q_stereo_depth` on the window, a reference square at the screen and a square with `_q_stereo_parallax` 8). Its cases: `still`, `hideshow`, `minimize`, `resize`, `two` (two pair windows), `closeexpose` (twenty windows, each closed during or right after its first expose), `cycles` (200 hides and 200 shows, 60 ms apart). It prints `READY` and then stays still.
2. **The reading:** `pairs.py FRAME.ppm` gives each window's disparity, the near square against the reference square in the left half minus the same in the right half. A pair reads 8.0 px, one picture in both eyes 0.0, a window off the screen `absent`. Reading against the reference square leaves out whatever depth the compositor gives the window as a whole.
3. **What the program cannot do itself, KWin does:** a KWin script loaded over D-Bus (`org.kde.kwin.Scripting.loadScript`, then `run` on `/Scripting/ScriptN`) restores a minimized window (`w.minimized = false`) and places two windows side by side (`w.frameGeometry`); `org.kde.KWin.setCurrentDesktop` on `/KWin` changes the desktop, with `[Desktops] Number=2` in the `kwinrc` the case brings (`/mnt/kwinrc`).
   Grab once while the window is away (minimized, other desktop): `absent` proves the event happened.
4. **The watchdog:** a timer in the gui thread writes the time every 100 ms; a second thread prints `WATCHDOG` and sends the gui thread a signal whose handler writes its backtrace (`backtrace_symbols_fd`, the program linked with `-rdynamic`) when the time is older than 5 s. A change that makes the gui thread wait for the render thread is not proved without it.
5. **Count the events,** from `qt.scenegraph.renderloop=true`: `polishAndSync (in expose)` and `polishAndSync (normal)` per case. A case with no expose proved nothing.
6. **Both libraries, the same session script** (`cases/stress.sh`; `/mnt/lib` holding `fixed` puts the library under test first): the old library must read 0.0 where the new one reads 8.0.

Measured (ORDER 555, Stereo KWin +stereo3d54 over the published set, software rendering, side by side full): with qt6-declarative +stereo3d2 the cases hideshow, minimize, desktops, resize, both windows of two, and cycles (302 exposes) end at 0.0; with the fix every one ends at 8.0, with 399 exposes in cycles and 56 in closeexpose, and the watchdog never spoke.

## A Plasma window with Stereo Union's element depth

`cases/plasma.sh` starts System Monitor and the application launcher (`plasmawindowed org.kde.plasma.kickoff`) with `QT_QUICK_CONTROLS_STYLE=org.kde.union` and `XDG_CURRENT_DESKTOP=KDE`, the person's limits written as System Settings writes them (`/mnt/limits`: sunk, popped, element; `10,4,12` is the measuring scale, never a default), minimizes and restores each by KWin script, and grabs before, while away and after.
`halves.py` on the frame counts the pixels that differ between the eyes: the window is the active one, at the screen, so every differing pixel is an element's depth.
A window that repaints by itself hides the fault from a single grab: System Monitor draws an ordinary frame a moment after every expose, so one grab nearly always shows a pair.
`cases/plasma-sample.sh` samples the output instead, twelve times while steady and thirty times after the event (minimize and restore, or with `/mnt/event` holding `desktops` the other desktop and back), and names each sample pair, flat (the window is there and the eyes are equal) or away.
Pick the window by what it does, not by its name: the launcher shown with `plasmawindowed` is drawn as a pair on the wire but has no element at depth (its content is Plasma's own components, not the style's), so its eyes are equal with any library and it proves nothing.

Measured (ORDER 555, the published set with Stereo KWin +stereo3d54, `ElementLimit` 12 as the measuring scale): System Monitor steady, 12 of 12 samples a pair with both libraries; after the other desktop and back, 1 of 30 samples flat with qt6-declarative +stereo3d2 (0 differing pixels with the window on the screen, between samples of 10,430) and 0 of 30 with the fix; after minimize and restore 0 of 30 flat with both.
One flat sample in thirty is a thin red: on a window that repaints, the stress above is the proof and the Plasma window the confirmation.

## Traps

- **Symptom:** a declared Qt Quick scene shows one eye twice on a real 3D output, in a guest that draws in software or after the window was hidden, while the program says it draws two eyes and captures in the rig show two.
  **Cause:** the edition's Qt Quick drew a frame made for an expose as one picture into both eye targets and asked for no frame after it; on Wayland a window is exposed again whenever a frame callback came late (Qt's 100 ms limit, `QT_WAYLAND_FRAME_CALLBACK_TIMEOUT`), which software rendering does all the time, and the swapchain is made again each time.
  **Fix:** Qt Quick draws an expose's frame as a pair too: the left eye synchronized as in any frame, the gui thread held until the right eye is rendered and both are presented (qt6-declarative 6.11.2+dfsg-3+stereo3d3, patch s3-0001, "Quick: draw a frame made for an expose as a pair too"). Asking for one more frame after the expose does not settle: where that frame's callback is late again, the picture alternates between one eye and two.
  **How found:** the recorder run to the last buffer (halves equal in the first frame of every new swapchain, different in the others), `qt.scenegraph.renderloop=true` (each `polishAndSync (in expose)` followed by a flat commit, each `polishAndSync (normal)` by a pair), and two runs that must then show two eyes and did: `QSG_RENDER_LOOP=basic`, and `QT_WAYLAND_FRAME_CALLBACK_TIMEOUT=0`. Qt's own test `tst_qquickwindowstereo` (`drawsThePairAfterAnExpose`) holds it: it needs a compositor that gives the surface two views, and on Stereo KWin older than +stereo3d54 the test client loses its connection on `kde_stereo_depth_v1` ([versioned-events.md](versioned-events.md)).
- **Symptom:** the recorder's buffers differ between their halves and the output's frame does not, so the compositor looks guilty.
  **Cause:** the recorder stopped at its limit and the buffers compared were the first ones, not the one on the screen.
  **Fix:** step 3; compare the last line with the frame.
- **Symptom:** a Vulkan program in the VKMS guest stops with `Unable to open device : No such file or directory (VK_ERROR_INCOMPATIBLE_DRIVER)`.
  **Cause:** VKMS has no render node, and Mesa's device selection layer opens the compositor's main device.
  **Fix:** `NODEVICE_SELECT=1` for the program.
- **Symptom:** `grab` waits its twenty tries on the empty desktop.
  **Cause:** it waits for a frame that is not black; a KWin session without a wallpaper is black.
  **Fix:** grab once a client is on the screen, or accept the wait.
- **Symptom:** the frame count of a still scene is small (some twenty frames in a minute).
  **Cause:** KWin draws on damage only. It is not a stall.
- **Symptom:** `kwin_wayland` copied to another name (to drop its file capability in a container) stops with `Could not load the Qt platform plugin "wayland-org.kde.kwin.qpa" ... even though it was found`.
  **Cause:** KWin's own platform plugin starts only in a program whose file name ends in `kwin_wayland`.
  **Fix:** copy it into a folder of its own and keep the name (`/tmp/kw/kwin_wayland`).
  **How found:** `QT_DEBUG_PLUGINS=1` showed no load error at all, only the refusal.
- **Symptom:** on the published Stereo KWin (+stereo3d46) a Qt Quick program with the Union style closes at once with `interface 'kde_stereo_depth_v1' has no event 1` and `The Wayland connection experienced a fatal error`.
  **Cause:** KWin sent `depth_limits` to a client bound at an older version of the interface.
  **Fix:** Stereo KWin +stereo3d54 (s54-0002); run depth clients and Qt's stereo autotest on it ([versioned-events.md](versioned-events.md)).
  **How found:** the client's last lines.
- **Symptom:** System Settings or Info Centre shows no element depth and no `get_depth` on the wire.
  **Cause:** their windows are Qt Widgets shells with Qt Quick inside a `QQuickWidget`, which is drawn off screen and never as a pair.
  **Fix:** prove element depth on a Qt Quick window of its own (System Monitor, the launcher).
- **Symptom:** two test windows read as one, the other `absent`.
  **Cause:** a Wayland client cannot place its windows, and KWin put one over the other.
  **Fix:** place them with a KWin script before the grab.
- **Symptom:** Qt's stereo autotest never gets a pair with `QSG_RHI_BACKEND=vulkan`, on NVIDIA's driver and on software Vulkan alike, though a two-layer Vulkan swapchain works there.
  **Cause:** the edition's Qt gives a window its two views in the Wayland EGL window only; the Vulkan RHI draws such a window flat ([native-linux](../../native-linux/SKILL.md), the routes).
  **Fix:** on NVIDIA run the test the way the edition runs Qt there, Mesa's GL on zink (`MESA_LOADER_DRIVER_OVERRIDE=zink`, Mesa's EGL vendor file first, NVIDIA's Vulkan ICD).
  **How found:** the same test on three backends, and the patch that asks for the views.
- **Symptom:** `tst_qquickwindow` and `tst_scenegraph` are not among the build's targets.
  **Cause:** `tests/auto/quick/CMakeLists.txt` adds them under `QT_FEATURE_private_tests`, which needs a developer build of Qt.
  **Fix:** none on a distribution's Qt; `tst_qquickwindowstereo`, its contract twin and `tst_nodestest` build without it.
