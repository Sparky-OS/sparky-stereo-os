---
metadata:
  requires-packages: kwin-wayland | docker.io
name: stereo-proof-rig
description: >-
  Run isolated Stereo KWin captures of both eyes and negative controls in a throwaway container (kwin_wayland --virtual,
  ScreenShot2, WAYLAND_DEBUG, fake input, a real plasmashell session) for stereo identity, geometry, timing, UI, element
  depth and installed packages; find why the two eyes differ; the unpacking checks (one resize at KWin); the showcase
  screenshot. Load it when a capture is black, transparent, stale or cancelled, the right eye is brighter than the left,
  Show Screen Contents says the process is not authorized to take a screenshot, testTabBoxStereo or another KWin
  autotest fails, kf.package reports invalid metadata, timeout as PID 1 exits 125, the Wayland socket path is too long,
  runuser drops the render group, keys or clicks sent through fake input or xdotool do nothing, LIBGL_ALWAYS_SOFTWARE changes nothing, a proof exits 127 under LD_BIND_NOW or a PNS
  fixture does not decode, translated text does not appear, or a popup or lock-screen depth must be measured.
---

# The proof rig

## Working recipe

1. Select the test layer, package versions, synthetic fixture and a control that would expose the suspected defect.
2. Start an isolated compositor/runtime, wait for actual readiness, capture both eyes and declarations, and inspect a representative image.
3. Return commands, hashes, counts, control result and limits. A black or stale frame is not a valid successful stereo witness.

**Check freshness first.**
Written on 2026-10-07, the NVIDIA card added on 2026-10-16, KWin's shrink and the X11 view size on 2026-10-22, eyes that differ under an opaque region on 2026-11-01, the showcase screenshot on 2026-11-02.
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
- **Menus and keys:** KWin's [fake input protocol](https://invent.kde.org/libraries/plasma-wayland-protocols/-/blob/master/src/protocols/fake-input.xml) sends key events to the focused window, so a remote-control menu or a 3D menu is driven exactly as a user would, without a desktop. Keep one client connected, read the program's own state before and after, and fail when it did not change: [input-delivery.md](references/input-delivery.md) (it also says why ORDER 265 thought keys did not arrive).

When the question needs a real machine, a cable or a 3D television, the rig is the first step and [`test-bench`](../test-bench/SKILL.md) is the next: baselines, recoverable changes and the television rules.

## An X11 player (the X11 path through Xwayland)

One fresh session per case, a passwd entry for the user, a render node for KWin, the declarations read from the X window tree, and the stereo capture read per eye: [x11-session-rig.md](references/x11-session-rig.md), with its scripts (`x11_props.py`, `x11_propagation.py`, `eyes_share.py`, `kwin_script.py`, `vlc_mpris.py`, `support-shim.c`, `make-barcode-fixtures.sh`, `columns.py`).

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

## Element depth inside a window

A window whose elements show depth (Union on the edition's Qt, [Depth inside every window](../../docs/depth-inside-windows.md)) is measured element by element.

1. **A 3D mode on the virtual output.** Start KWin with `KWIN_VIRTUAL_STEREO_MODES=1`, which gives `--virtual` outputs the 3D twins a monitor gets, and restore a saved `kwinoutputconfig.json` in one of them (side by side half), so the window is awake from its first frame.
2. **The user's limits, written as System Settings writes them:** `kwinrc`, `[StereoDepth]`, `SunkLimit`, `PoppedLimit` and `ElementLimit`. Run the shipped values (`SunkLimit` 10, `PoppedLimit` 4, `ElementLimit` 1) and the measuring scale (`ElementLimit=12`): at 1 px, shares of 0.111 or 0.333 px change no pixel and 0.667 px changes one, so only the larger scale makes every share and every cut measurable. Never report 12 as a default.
3. **The prediction, from the theme, not from the code under test:** each element's parallax worked out by hand from the style's CSS (shadow strengths against the strongest in the window, nesting fitted into the limit, declared depths), compared with the measured disparity and with the parallax the style reports.
4. **The measurement:** for each element, the horizontal shift that best matches the same window drawn on a 2D output, searched in steps of 0.005 px with linear interpolation, in each eye; the disparity is the left shift minus the right. A deeper element is cut to its rectangle: also count the pixels that differ beside it (0 expected) and inside it (many).
5. **Controls:** the same case with Debian's Qt Quick (the elements off the screen plane measure 0, so the case must fail), limits 0/0/0 and a 2D output (0 differing pixels against the same window drawn without the depth packages: the edition as published, with the style built without its depth), and both Qt Quick render loops (`QSG_RENDER_LOOP=basic` and the threaded default).
6. **On the wire:** `WAYLAND_DEBUG=client` shows the style's `get_depth` and `depth_state`, Qt's `set_desktop_depth`, and the pair's one `set_content(3)` on the same commit.

## A showcase stereo screenshot

A picture for people rather than a check: it has to show every depth level of the desktop at once, or it undersells the work (Daniel, 2026-10-23).
Take it in a real Stereo KWin session with a 3D output, on a test machine, never on someone's own desktop.

1. **Real 3D content inside the program:** a beautiful, freely licensed stereo picture or scene, credited with its authors' names.
2. **Open the volume applet's pop-up and pin it** with its pin button: a pinned pop-up keeps its popped level while focus moves.
3. **Then focus the program's window,** so it sits at the screen and its menus pop.
   An unfocused program sinks with the windows behind it and reads flat.
4. **Open a menu several levels deep** (a menu, its sub-menu, the next sub-menu): each level sits one step further out.
5. **Capture with Spectacle's 3D capture, on a delay** (MPO for its PNG choice, as [stereo-pictures](../stereo-pictures/SKILL.md) says).
   Then measure each level's disparity in pixels and write it down; on 2026-10-13, Marble's window measured 0, a menu +2, its sub-menu +4 and the windows behind −3 to −10.
6. **A program under Wine:** first prove that its menus get their popped levels (override-redirect X11 menus under Xwayland).
   Menus that come out flat are work to fix, not a limit.
7. **Hand over both files:** the MPO and a side-by-side PNG built from it, left eye first, with the depth seen (which elements step forward or back, by how many pixels).
   Look at every frame for private details first: names, accounts, mail, places.
8. **Never attach them to a mailing-list post,** since lists cap a message's size (the X3D public list at 800 KB).
   Put the files in a public folder on the edition's download server, with a `README.txt` and `SHA256SUMS`, and link the folder.
9. **Capture with KWin +stereo3d37 or later.** Before [08453fd](https://github.com/Sparky-OS/kwin/commit/08453fd62972), ScreenShot2's `stereoImage()` painted each eye with source-over onto an image it had not filled, so the transparent parts of a stereo capture held leftover memory; it now copies each eye as it is.

## Plasma in the rig (notifications, on-screen displays, panels, popups)

A real `plasmashell` on the virtual Stereo KWin shows what a unit test with one surface cannot: stacks of notifications, an on-screen display over a notification, menus beside a floating panel.

1. **The session:** a throwaway container with the edition's `plasma-workspace` and `plasma-desktop`, a private session bus, `KWIN_VIRTUAL_STEREO_MODES=1` and a `kwinoutputconfig.json` that puts the virtual output in a 3D mode, `kwin_wayland --virtual --xwayland`, then `kactivitymanagerd` by hand (without it plasmashell stops with "Aborting shell load"), then `plasmashell` with its own `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME`.
   One fresh session per case: the on-screen display shows once per session, and a long session drifts.
2. **Triggers:** `notify-send -p` (`-u critical`, `-t` long enough to capture; `CloseNotification` by the printed id), the on-screen display by D-Bus (`org.kde.osdService` `volumeChanged`, `brightnessChanged`, `showText` on `org.kde.plasmashell`), panels through the shell's scripting call (`org.kde.PlasmaShell.evaluateScript`, for example a layout script from a look-and-feel package), clicks and hovers through KWin's fake input.
   Write `plasmanotifyrc` (`[Notifications]` `PopupPosition=`) before plasmashell starts; changing it live is not picked up.
3. **Frames from KWin itself:** a KWin script (`org.kde.kwin.Scripting.loadScript`) that prints `windowAdded` and `frameGeometryChanged` with type, role flags (`notification`, `criticalNotification`, `onScreenDisplay`, `tooltip`, `dock`) and `frameGeometry` gives exact logical geometry; never read geometry from the picture.
4. **Depth from the picture, per window:** with ScreenShot2 take both eyes (left half, right half), and for each window find the horizontal shift that makes the right eye's rows inside the window's frame (shrunk 8 px from its edges) equal the left eye's; the disparity is that shift in device pixels, and the residual error says whether the match is real.
5. **The red and the green:** the same sessions on the old and the new KWin build (an image per build, or the new `libkwin.so` mounted over the packaged one), and a 2D output as the control: frames and pictures must not change there.
6. **Seeing the level:** to learn why a level is what it is, mount a `libkwin` built with an environment-gated `qWarning` in `StereoDepth::level()` (caption, role flags, share `rank/count`, which other popped windows are on stage) and read `kwin.log`; remove it before the package.
   Only the built `libkwin.so.6.x` is replaced, and only in the throwaway container.

Traps met in this rig:

- **A difference box says "screen level" for a popped window.** Symptom: an on-screen display and the top-corner notifications read 0 to 1 px of disparity, so they looked unpopped. Cause: the box is the difference of the capture against a baseline of the same eye, and it picked the panel (OSD), a mid-slide frame and shadows. Fix: match inside the window's own frame (step 4); the same sessions then read 3 px, and the level log showed share 1/1. How found: the level log, then the cross-correlation with an error near 0.2 against 3 px.
- **One surface alone always passes.** Symptom: a unit test with one notification at the limit was green while the real session had notifications at 1, 2 and 3 px. Cause: popped surfaces share the limit, so the defect only shows with several. Fix: test the stack, the pair with an on-screen display and the pair with a menu, and keep the single surface as a control that passes before the change.
- **The wrapper forwards only the variables it names.** Symptom: both "layouts" results were the same layout, with `docks-default.json` inside the folder for the other one. Cause: the `docker run` line forwarded a fixed list of `-e` names, so the new `LAYOUT` was dropped without an error. Fix: add the names; print what the case actually applied (the panels' frames) into the result and read it before any table is made.
- **The container sees only what is mounted.** Symptoms: `PermissionError` creating the output folder, `FileNotFoundError` for a layout script. Cause: only the work folder and the lane folder were mounted. Fix: keep inputs and outputs under them.
- **CMake writes into the source it configures.** Symptom: `ninja` fails with "rebuilding 'build.ninja': subcommand failed" and the log says `Could not open file for write in copy operation /src/.git/hooks/pre-commit.tmp ... Read-only file system`. Cause: ECM's `kde_configure_git_pre_commit_hook` installs a hook when the tree has a `.git`, and the source was mounted read-only. Fix: keep the repository outside the tree (`git --git-dir=../src.git` with `core.worktree`).
- **Reuse a finished test build.** `cp -a` the earlier build folder (modification times kept) and mount the new source at the same path as before: ninja rebuilds only what changed (a library and the tests it feeds), minutes instead of hours; a cold build of KWin's tests takes much longer, and every `run` start installs the build dependencies again, so run all the tests of a round in one call.
- **The build dependencies of a package may need an earlier build of ours.** Symptom: `builddeps ... Depends libstereo-policy-dev (>= 1.15.0) but none of the choices are installable` in `build-dep.log`. Cause: the repository mounted at `/repo` did not carry that version. Fix: pass the folder with those `.deb` files as the build's `extra` directory.
- **Clicking where you think a widget is.** Symptom: a click on a panel's first item opened nothing, or a notification appeared instead. Cause: the item was not where the layout's order suggested (icons missing in the test image, spacing). Fix: capture the panel once, read the pixel positions from it, and write them into the case.
- **Killing by pattern.** `kill $(ps ... | grep matrix)` ran inside a command line that itself contained the pattern and ended the shell (exit 144); find the PID in one call and kill the number in the next.

## Traps that fooled us

- **Searching vertical offsets** in block matching picks false matches on repeated patterns; match on the same row and check the vertical profile on its own.
- **`LIBGL_ALWAYS_SOFTWARE=1` does not move KWin's scene to llvmpipe.** With a render node given, KWin's virtual backend draws through EGL on that card (radeonsi's shader statistics appear in `kwin.log` with `QT_LOGGING_RULES='kwin_*.debug=true'`), so the rig's "software" and `--gpu` runs give the same captures. KWin opens the first render node that opens: with Docker's CDI that is the NVIDIA card, without it the AMD one. Name a run by the card you gave it, and check the log.
- **A window capture on Wayland includes the compositor's title bar:** offset the analysis by it.
- **Eyes that differ only where a window has alpha under its own opaque region.** KWin's occlusion culling leaves the target unpainted below a window's opaque region, and a surface with an alpha channel still blends over what is left there (the Wayland protocol allows that artifact when a client declares a wrong opaque region).
  In 2D the leftover is usually the previous frame of the same picture, so it rarely shows; in stereo the capture draws the right eye over the left eye's finished picture in one target, and a 3D output's per-eye buffers keep their own history, so one eye came out lighter (found on 2026-10-31 with a program that blits with alpha below 1 under its opaque region).
  Stereo KWin since `+stereo3d40` clears the background below such windows in the eye passes; surfaces without alpha keep the culling, and 2D frames take upstream's path.
  To tell it from a content error, repeat the capture with a fixture that draws with alpha 1 where it declares itself opaque: a difference that goes away was this one, a difference that stays is the program's.
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

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (29 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
