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

## Traps

- **Symptom:** a declared Qt Quick scene shows one eye twice on a real 3D output, in a guest that draws in software or after the window was hidden, while the program says it draws two eyes and captures in the rig show two.
  **Cause:** the edition's Qt Quick drew a frame made for an expose as one picture into both eye targets and asked for no frame after it; on Wayland a window is exposed again whenever a frame callback came late (Qt's 100 ms limit, `QT_WAYLAND_FRAME_CALLBACK_TIMEOUT`), which software rendering does all the time, and the swapchain is made again each time.
  **Fix:** Qt Quick draws an expose's frame as a pair too: the left eye synchronized as in any frame, the gui thread held until the right eye is rendered and both are presented (qt6-declarative, "Quick: draw a frame made for an expose as a pair too", from the build that carries it). Asking for one more frame after the expose does not settle: where that frame's callback is late again, the picture alternates between one eye and two.
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
