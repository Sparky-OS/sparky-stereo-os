---
metadata:
  requires-packages: kwin-wayland
name: stereo-proof-rig
description: >-
  Run isolated compositor captures and negative controls for stereo identity, geometry, timing, UI and installed-package behavior.
---

# The proof rig

## Working recipe

1. Select the test layer, package versions, synthetic fixture and a control that would expose the suspected defect.
2. Start an isolated compositor/runtime, wait for actual readiness, capture both eyes and declarations, and inspect a representative image.
3. Return commands, hashes, counts, control result and limits. A black or stale frame is not a valid successful stereo witness.

**Check freshness first.**
Written on 2026-10-07, the NVIDIA card added on 2026-10-16, KWin's shrink and the X11 view size on 2026-10-22.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill says what counts as proof; this one says how to produce it.
No 3D display is needed: the rig captures what Stereo KWin hands to an output, both eyes side by side.

## The rig, in a throwaway container

- **Image:** `debian:testing`, the edition's packages from its repository with a pin above Debian's (Stereo KWin, Mesa, Qt, Xwayland, the declaration library), the program under test as a package. Run the container as your user, `--platform linux/amd64`, and give it only the render node (`--device /dev/dri/renderD128`) when you want the GPU; without it, `LIBGL_ALWAYS_SOFTWARE=1` gives Mesa's software renderer. Run both: they fail differently.
- **The compositor:** inside `dbus-run-session`, start KWin with a virtual output and no permission prompts:
  ```
  KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 \
    kwin_wayland --virtual --xwayland --socket=sub --width 1280 --height 800 &
  ```
  wait for the socket in `$XDG_RUNTIME_DIR`, then start the program with `WAYLAND_DISPLAY=sub` and `QT_QPA_PLATFORM=wayland` (or `DISPLAY=:0` and `QT_QPA_PLATFORM=xcb` for the X11 route through Xwayland).
- **Captures:** KWin's own [ScreenShot2](https://invent.kde.org/plasma/kwin/-/blob/master/src/plugins/screenshot/org.kde.KWin.ScreenShot2.xml) D-Bus interface (`CaptureScreen`, `CaptureActiveWindow`). With stereo content on screen, Stereo KWin's capture holds both eyes side by side, left eye first, each at the output's full size (a 1280x800 output gives 2560x800), so a script reads each eye as one half.
- **Declarations:** run the program with `WAYLAND_DEBUG=client` and keep only the lines that matter (`kde_stereo_content`, `set_content`, `get_subsurface`, `place_below`, errors): the log proves which surface declared stereo, and how many times.
- **On the NVIDIA card:** Docker's CDI gives the container the card, its render node and NVIDIA's own libraries from the host (`--device nvidia.com/gpu=0`), so the host's driver version is the one under test. Query the selected render node’s group ID and add it with `--group-add` (125 was this rig’s ID, not a portable default) and `--cap-add SYS_NICE`, which `kwin_wayland`'s file capability needs to start. Give a library by its absolute path, because CDI mounts the host's copies over the image's (dpkg cannot replace a mounted file, so prove an egl-wayland upgrade in a container without the card), and choose NVIDIA's EGL platform library with `__EGL_EXTERNAL_PLATFORM_CONFIG_DIRS` when two are installed. For Mesa on NVIDIA's Vulkan driver (zink), list Mesa's EGL vendor first and NVIDIA's second (`__EGL_VENDOR_LIBRARY_FILENAMES`): NVIDIA's Vulkan driver does not start without its own EGL vendor. Run every case on the AMD card too: they fail differently.
- **PipeWire for screencasting:** KWin's screencasting tests need a PipeWire and a WirePlumber of the container's own, with the container's `XDG_RUNTIME_DIR`, never the desktop's; without them every casting test fails at its setup.
- **Geometry, not only colour:** draw a disc of known size in each eye (0.6 of the window's height, round in the width the program believes it has) and measure its area, diameter, aspect and centre in each half; a squeezed eye still shows the right colour.
- **Menus and keys:** KWin's [fake input protocol](https://invent.kde.org/libraries/plasma-wayland-protocols/-/blob/master/src/protocols/fake-input.xml) sends key events to the focused window, so a remote-control menu or a 3D menu is driven exactly as a user would, without a desktop.

## Test material that a script can read

- **Video:** two coloured sources, the left view red with "LEFT" and the right view blue with "RIGHT", both stamped with the same frame number, packed side by side or top and bottom, either eye first; marked with the frame packing SEI (x264's `--frame-packing`, also a clip whose SEI comes only on keyframes) or Matroska's `StereoMode`; plus a plain 2D clip and an undeclared 32:9 clip.
- **Pictures:** the same views as MPO, as JPS with and without the `_JPSJPS_` block in both eye orders, as PNG with the `sTER` chunk, plain side by side and top and bottom, and an ordinary photo.
- **Scenes:** programs that draw (globes, plots, molecules) are measured against a closed-form prediction instead ([`stereo-two-cameras`](../stereo-two-cameras/SKILL.md)).

## The checks

For eye-equality checks, disable desktop plane depth and use identical backgrounds or opaque UI witnesses.
Test intentional disparity separately against its prediction; translucent UI over different scene pixels need not be pixel-identical.
Reset state for each case. Repeat a live-preview result from a fresh process and installed package.

1. Each eye shows its view (red in the left half, blue in the right) and both halves show the same frame number, over several captures in time.
2. Exactly one declaration per stereo surface, on the right surface, and none for 2D content.
3. 0 differing pixels between the eyes outside the 3D area: menus, toolbars, on-screen displays.
4. The 2D control: the same container with the distribution's own packages instead of ours, the program with stereo off, 0 differing pixels. When a program animates, freeze it (a deterministic mode and `libfaketime`) and measure the noise between two runs of the same build first.
5. For drawn scenes: block-match the two eyes (for example 17x17 blocks, sum of absolute differences) along the same row only, and report the vertical profile separately; report the median error, the share within one pixel and the vertical shift.
6. Rerun everything from the packages installed in a fresh container, not only from the build tree.
7. For unpacking (a half-width or half-height source rearranged into full side by side): each eye must equal its region of the source sample for sample, nothing rescaled ([Unpacking is a copy](#unpacking-is-a-copy)). For Stereo KWin's one resize into a window or screen: PSNR against FFmpeg's own output of the same filter, not a judgement by eye. For audio formats: a PipeWire of the container's own, read with `pw-dump`, shows the format and rate the program negotiated.

## Unpacking is a copy

Full side by side is the layout, never a size: a program hands Stereo KWin the two eyes side by side, left eye first, each at the resolution it has, and KWin resizes them once, into the window or the screen.
A half top-and-bottom 1920x1080 frame becomes one 3840x540 buffer; half side by side goes as it is, two 960x1080 eyes; a row-interleaved frame gives two 1920x540 eyes; a PAL field-sequential DVD two 720x288 eyes.
The size an eye is shown at is the surface's: a `wp_viewport` destination on Wayland (each eye is a half of the buffer's source box), and on X11 the window's place, which a program whose views have another resolution declares with `_KDE_NET_WM_STEREO_CONTENT_ONE_VIEW_SIZE` ([native-linux](../native-linux/SKILL.md#x11-views-at-another-size-than-their-resolution)).
A program that stretches a half eye to full size, for KWin to squeeze it again for a half-format television, resizes twice.

To prove that a path copies:

1. **Fixtures with addresses.** `scripts/fsbs_ids.py make PACKING WIDTH HEIGHT out.png` writes every sample's eye, column and row into its 24 bits (R = x & 255, G = y & 255, B = eye << 7 | (x >> 8) << 3 | y >> 8), packed side by side or top and bottom (full or half), row or column interleaved, checkerboard, quincunx or frame packed. Give them to the program as its input: a picture, a lossless RGB video (FFV1 `gbrp` in Matroska with its `StereoMode`), a guest's framebuffer.
2. **The buffer handed over.** Build `scripts/wlrec.c` as a shared library and preload it into the program with `WLREC_DIR` set. It writes the shared-memory buffer committed on each surface declared full side by side, and reads back an EGL surface's back buffer at `eglSwapBuffers`, with the viewport destination and the position, one JSON line per commit in `log.jsonl`. It changes nothing the program sends.
3. **Every sample its own.** `scripts/fsbs_ids.py check BUFFER EYE_WIDTH EYE_HEIGHT --raw WxH:STRIDE` (`--rgba-bottom-up` for an EGL read-back, `--in-layer` where the buffer also holds black around each eye, a player's letterbox counted in samples). A resampled buffer fails: its size is wrong, or its samples mix their neighbours.
4. **One resize, at KWin.** Capture the screen (`scripts/capture.py`, ScreenShot2) and compare each eye's region with FFmpeg's own resize of the eye handed over (`scripts/one_resize.py`); `--twice WxH` also scores the eye first stretched to WxH, and the one resize must win. Use a window whose size differs from the eye's full size: in a full screen 1920x1080 window, one and two resizes of a 1920x540 eye give the same picture.
5. **The negative control.** The same run with the old build must fail step 3.

Traps:

- **A player's dither** (mpv's `dither-depth`) changes values by one level without moving any sample: run the sample check with it off, and the picture check with the defaults.
- **An aspect passed as text with six decimals** made mpv's destination a pixel short of its window and added a letterbox row; carry aspects with all their digits.
- **KWin's filter, the shrink rule:** from kwin +stereo3d30 a view drawn smaller than its resolution, on either axis, is the average of the samples each pixel covers, taken within its own view, and a view drawn at its size or larger is bilinear. Compare a shrink with FFmpeg's `area` (`one_resize.py --flags area`) and a magnification with its `bilinear`. Measured on the rig's AMD card with FFmpeg's `area` as the reference, eyes of 2880x1620 drawn at 1920x1080 (a 1.5x shrink) score 69 dB, where +stereo3d29's bilinear sampling gave 46 dB; the same release clamps a magnified eye's samples to the eye, so its inner edge no longer takes a quarter of the other eye's first column at 2x (half side by side at full screen: 64 dB against FFmpeg's `bilinear`, 51 dB before). Report the numbers with the filter compared against.
- **A subsurface's position applies with its parent's next commit:** a test window must repaint after placing its stereo surface.
- **On X11 the buffer is the window's own pixmap**, so an X11 program whose views have another resolution than their place declares the size one view is shown at (support version 6). Prove it in four parts: the X11 window's own size (`xcb_get_geometry`: both views at their resolution, 3840x540 for half top and bottom), its contents read back with `XGetImage` equal to the views handed over, sample for sample, each eye's region of the capture against FFmpeg's resize of the view to the declared size, and the same run on a KWin that announces 5 as the control. A half top-and-bottom 1920x1080 picture, a 3840x540 window declaring 1920x1080, scores 63 dB per eye against FFmpeg's resize of its 1920x540 view, and 8 dB on +stereo3d29, which shows each eye at 1920x540.

## Traps that fooled us

- **Searching vertical offsets** in block matching picks false matches on repeated patterns; match on the same row and check the vertical profile on its own.
- **`LIBGL_ALWAYS_SOFTWARE=1` does not move KWin's scene to llvmpipe.** With a render node given, KWin's virtual backend draws through EGL on that card (radeonsi's shader statistics appear in `kwin.log` with `QT_LOGGING_RULES='kwin_*.debug=true'`), so the rig's "software" and `--gpu` runs give the same captures. KWin opens the first render node that opens: with Docker's CDI that is the NVIDIA card, without it the AMD one. Name a run by the card you gave it, and check the log.
- **A window capture on Wayland includes the compositor's title bar:** offset the analysis by it.
- **A colour classifier mislabels correct captures** whose views carry large white areas; look at one capture before trusting a label.
- **Captures are 8 bits per channel:** a deep-colour proof is the surface's configuration and a readback, not the capture.
- **A test that cannot fail proves nothing:** break the expectation once and see it fail.
- **Debian source builds in a container:** keep the version's epoch colon out of the build directory's name (CMake's translation targets fail on it).
- **A background wait with `pgrep -f` or `pkill -f`** on a pattern that also appears in its own command line matches itself and never ends; match the process name, or keep a PID.
- **A Wayland client must read its socket:** a test program that only calls `wl_display_dispatch_pending()` never answers KWin's ping when the driver reads nothing for it (NVIDIA's Vulkan with explicit sync and `wp_fifo_v1`), and KWin then fades the window as "Not Responding". The window looked empty to a colour check; read the socket every frame (`wl_display_prepare_read`, `poll`, `wl_display_read_events`). A KWin script that lists `workspace.stackingOrder` tells a missing window from a faded one.
- **A race needs repeated runs and a control:** a race left NVIDIA's second view black in some runs only; 20 runs with the fix (all good) beside 20 with the fix switched off (8 black) showed it gone.
- **The virtual KMS driver (`vkms`) needs a virtual machine:** on a desktop the running compositor takes the virtual device as one more GPU.
- **Fix the inputs before blaming the program.** A frame picked by time (the last of a 40-second recording) changes with the machine's speed: pick a frame index. A program that reads memory it never set draws differently from run to run, and preloading any library moves that memory; find it with Valgrind's memcheck and fix the program, and run every producer with address randomisation off (`setarch -R`) for the rest.
- **`setarch -R` in a container needs one more personality, not seccomp off.** Docker's default seccomp profile refuses `personality(ADDR_NO_RANDOMIZE)`; add only that to Docker's own default profile. With seccomp off, Bubblewrap gets far enough to fail where it otherwise falls back, glycin's image loaders fail, and every program that loads a texture breaks.
- **Freeze a window only after the compositor has sized it.** KWin doubles a declared X11 window when it reads the declaration; a KWin busy writing its own configuration read it 5 to 16 seconds late, and a program frozen before that showed one eye. Wait until the X server reports the doubled width before the first frame, and keep a test that holds KWin still (`SIGSTOP`) after it maps the window to prove the wait.
- **No OpenStreetMap tiles in a test.** The OpenStreetMap Foundation's Tile Usage Policy does not permit offline use or tile archives: draw synthetic tiles at the coordinates the program asks for, run with the network off (`--network none`), and fail on any download the program attempts.
- **A per-scene tolerance hides one eye moved for all scenes.** A depth check that accepts a pixel of bias per scene passed 88 of 92 scenes with the right eye a pixel to the right; also bound the mean bias over all scenes (a quarter pixel caught a pixel either way and half a pixel).
