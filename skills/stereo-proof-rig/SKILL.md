---
name: stereo-proof-rig
description: How to prove stereo 3D work on Sparky Stereo OS without a 3D display: a headless Stereo KWin in a container, captures of both eyes, the Wayland log of every declaration, key events for menus, the test material (LEFT and RIGHT clips, pictures, scenes), the checks and their numbers, and the traps that fooled us. Load the general sparky-stereo skill first; every other skill's proof section relies on this one.
---

# The proof rig

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill says what counts as proof; this one says how to produce it. No 3D display is needed: the rig captures what Stereo KWin hands to an output, both eyes side by side.

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
- **Menus and keys:** KWin's [fake input protocol](https://invent.kde.org/libraries/plasma-wayland-protocols/-/blob/master/src/protocols/fake-input.xml) sends key events to the focused window, so a remote-control menu or a 3D menu is driven exactly as a user would, without a desktop.

## Test material that a script can read

- **Video:** two coloured sources, the left view red with "LEFT" and the right view blue with "RIGHT", both stamped with the same frame number, packed side by side or top and bottom, either eye first; marked with the frame packing SEI (x264's `--frame-packing`, also a clip whose SEI comes only on keyframes) or Matroska's `StereoMode`; plus a plain 2D clip and an undeclared 32:9 clip.
- **Pictures:** the same views as MPO, as JPS with and without the `_JPSJPS_` block in both eye orders, as PNG with the `sTER` chunk, plain side by side and top and bottom, and an ordinary photo.
- **Scenes:** programs that draw (globes, plots, molecules) are measured against a closed-form prediction instead ([`stereo-two-cameras`](../stereo-two-cameras/SKILL.md)).

## The checks

1. Each eye shows its view (red in the left half, blue in the right) and both halves show the same frame number, over several captures in time.
2. Exactly one declaration per stereo surface, on the right surface, and none for 2D content.
3. 0 differing pixels between the eyes outside the 3D area: menus, toolbars, on-screen displays.
4. The 2D control: the same container with the distribution's own packages instead of ours, the program with stereo off, 0 differing pixels. When a program animates, freeze it (a deterministic mode and `libfaketime`) and measure the noise between two runs of the same build first.
5. For drawn scenes: block-match the two eyes (for example 17x17 blocks, sum of absolute differences) along the same row only, and report the vertical profile separately; report the median error, the share within one pixel and the vertical shift.
6. Rerun everything from the packages installed in a fresh container, not only from the build tree.
7. For a scaling filter (a half-width or half-height source brought to full size): PSNR against FFmpeg's own output of the same filter, not a judgement by eye. For audio formats: a PipeWire of the container's own, read with `pw-dump`, shows the format and rate the program negotiated.

## Traps that fooled us

- **Searching vertical offsets** in block matching picks false matches on repeated patterns; match on the same row and check the vertical profile on its own.
- **A window capture on Wayland includes the compositor's title bar:** offset the analysis by it.
- **A colour classifier mislabels correct captures** whose views carry large white areas; look at one capture before trusting a label.
- **Captures are 8 bits per channel:** a deep-colour proof is the surface's configuration and a readback, not the capture.
- **A test that cannot fail proves nothing:** break the expectation once and see it fail.
- **Debian source builds in a container:** keep the version's epoch colon out of the build directory's name (CMake's translation targets fail on it).
- **A background wait with `pgrep -f` or `pkill -f`** on a pattern that also appears in its own command line matches itself and never ends; match the process name, or keep a PID.
- **The virtual KMS driver (`vkms`) needs a virtual machine:** on a desktop the running compositor takes the virtual device as one more GPU.
