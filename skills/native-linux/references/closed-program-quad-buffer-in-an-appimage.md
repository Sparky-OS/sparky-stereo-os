# A closed program's quad buffer in an AppImage

Written on 2026-11-14 from one test: Open Cascade's CAD Assistant 1.6.0 for Linux (a closed program, free of charge, published as an AppImage on Open Cascade's own page; Qt 5.9.9 with Qt Quick, Open CASCADE Technology 7.6 linked in), run on Stereo KWin with the edition's Mesa on an AMD card and on an NVIDIA RTX 3060 through zink.
Load it with [native-linux](../SKILL.md) when a program we cannot rebuild says it has an OpenGL quad buffer mode ("shutter glasses", "quad buffer", "active stereo") and must be shown in stereo, measured, and put in an app center.
A closed program is not changed, patched or disassembled: its licence usually forbids it, and nothing here needs it.
The result of the test: the program's quad buffer mode reaches Stereo KWin as two eyes with one declaration and no launcher variable, on both cards; the one fault found was in Mesa, not in the program.

## Recipe

1. **Their terms and their file first.**
   Read the vendor's page and the licence text (it is usually inside the file) before running anything: what installing accepts, whether a third party may fetch the file for a person, whether redistribution is allowed and in which form, and the clause on reverse engineering.
   Ask the server for the file's size before fetching (`curl -sIL URL`, the `content-length` after the last redirect), fetch it into an empty folder, record the SHA-256, and say whether the vendor publishes a checksum (this one publishes none, so the pinned checksum is "the file as downloaded on that day").
2. **List what it bundles without running it.**
   An AppImage is an ELF runtime followed by a squashfs: the offset is the end of the ELF section headers (`e_shoff + e_shentsize * e_shnum`), and `unsquashfs -o OFFSET -d OUT FILE` unpacks it in a container.
   Read `usr/lib` (which system libraries it replaces: an old `libgbm`, `libwayland-client`, `libxcb-glx`, `libX11-xcb` are the ones that can clash with the system's Mesa), `usr/plugins/platforms` (Qt with only `libqxcb.so` runs through Xwayland, whatever the session), the binary's `NEEDED` list (`libGL.so.1` without a bundled copy means the system's OpenGL), and the licence and the open source list.
   File lists, the dynamic section, version strings and the program's own messages are enough; do not disassemble.
3. **Plain 2D first, from the unpacked tree,** in the proof rig ([stereo-proof-rig](../../stereo-proof-rig/SKILL.md)), on each card: `/proc/PID/maps` of the running program says which of the bundled libraries were really loaded and which Mesa.
4. **Find the mode's name and its settings key.**
   The program's settings file after one run, and one change made through its own windows, give the key names; then a settings file per case replaces clicking.
   This program: `Settings` (gear), second page `Visualization options`, group `Stereoscopic output`, `Stereo output mode` = `Shutter glasses`, then a restart; in `~/.config/OpenCASCADE/<start name>.ini` that is `stereoMode2=11`, with `stereoCamIOD` (default 30) and `stereoCamZFocus` (default 50).
5. **Which configuration it is offered.**
   `glxinfo` in the same session lists stereo visuals only while the compositor announces stereo (`_KDE_NET_WM_STEREO_CONTENT_SUPPORTED` on the root window).
   `apitrace trace --api gl` on the program, then `apitrace dump | grep -E 'glXChooseFBConfig|glDrawBuffer|glXSwapBuffers'`, shows whether it asks for `GLX_STEREO` and how it draws a frame: here left eye to `GL_BACK_LEFT`, right eye to `GL_BACK_RIGHT`, then `glDrawBuffer(GL_BACK)` and the 2D interface, then the swap.
   Tracing the calls a program makes into our own OpenGL library is not reading its code.
6. **Both eyes, the declaration, the 2D parts.**
   ScreenShot2 gives a capture two outputs wide; `x11_props.py` must show `_KDE_NET_WM_STEREO_CONTENT` = 3 on the window that draws.
   Compare the program's 2D parts (tool strip, logo) between the eyes: they must be equal pixel for pixel.
7. **Tell the program's fault from the stack's with the smallest client that does the same calls.**
   When an eye lacks something, write a GLX program of a hundred lines that repeats the traced sequence, one variant per drawing path (a core profile shader with its own output, `gl_FragColor`, a scissored clear, fixed function), and check each eye by colour.
   A variant that fails on a sequence the OpenGL specification defines is the stack's fault, with a reproducer that fails before the fix and passes after it.
   [`scripts/glx-back-both-eyes.c`](../scripts/glx-back-both-eyes.c) is that client for `GL_BACK` (`MODE=out`, `fragcolor`, `clear`, `fixed`; `NOBACK=1` is the control that must fail), with [`check-glx-back-both-eyes.py`](../scripts/check-glx-back-both-eyes.py) for the capture.
8. **Geometry without the camera.**
   A closed program does not give its field of view or camera distance, so test the two laws every parallel-axis stereo camera obeys: changing the eye distance multiplies every block's disparity by one ratio, and moving the zero-parallax plane adds one constant to every block; and the vertical shift is zero.
   [`scripts/eyes-disparity.py`](../scripts/eyes-disparity.py) block-matches a stereo capture along the row (`--win X Y W H`, `--json OUT`) and checks the vertical shift.
   Block-match along the row only and compare block by block between two settings (here: ratios within 3 %, the constant within 0.25 px, the program's orientation cube at 0 in every case).
9. **A cursor the program draws itself** is found by colour in each eye near the pointer; its disparity must equal the scene's under the pointer at a near and at a far point, on the same row.
   `XFixesGetCursorImage` with the pointer inside the view says whether the program hides the system pointer (a cursor image without one visible pixel).
10. **What the person sees when stereo cannot start,** each case run and written down: the compositor announces no stereo (the root property removed), and a driver without stereo configurations (NVIDIA's own OpenGL).
11. **The launcher line** is whatever the green runs needed and nothing else; here nothing: the link to the program, started under its own name.

## Traps

- **Symptom:** in quad buffer mode the program's tool strip, panels and logo are in the left eye only, while the 3D scene is right in both eyes; the same on radeonsi and on zink.
  **Cause:** the program draws its 2D parts with `glDrawBuffer(GL_BACK)`, which OpenGL 4.6 core 17.4.1 defines as both back buffers of a stereo window ("zero, one, two, or four buffers ... to which fragment color zero is written"); Mesa's drivers write `gl_FragColor` to every color buffer but a shader's own output at location 0 only to the first, and a Qt Quick core profile context uses such shaders.
  **Fix:** in Mesa's state tracker, a fragment shader variant while one draw buffer constant names several buffers of the window's framebuffer (the edition's Mesa patch 0037, with the test `glx-back-both-eyes.c`); nothing in the program and nothing in its launcher.
  The package that carries it is Mesa 26.1.6-1+stereo3d21; its own test `glx-back-both-eyes` (debian/tests) fails on +stereo3d20 and passes on +stereo3d21, and the regression set that goes with such a change is in [edition-packaging's lessons](../../edition-packaging/references/lessons-2026-11.md#a-state-tracker-change-in-mesa-the-regression-set).
  **How found:** the trace showed `GL_BACK` before the interface; the small client was red only in the variant with a declared output and green for `gl_FragColor`, a clear and fixed function.
- **Symptom:** a double click or `./file.appimage` ends with `dlopen(): error loading libfuse.so.2` and "AppImages require FUSE to run".
  **Cause:** AppImages made before 2022 carry a runtime that loads the FUSE 2 library, which Debian testing no longer has (`apt-cache policy libfuse2t64` shows no candidate there; Debian 13 still has it).
  **Fix:** `./file.appimage --appimage-extract-and-run` for a single start, and in an app center entry unpack once with `--appimage-extract` and start the program from the unpacked tree.
  **How found:** the plain start in a container, then `strings` on the runtime (`libfuse.so.2`), then the archive.
- **Symptom:** with `APPIMAGE_EXTRACT_AND_RUN=1` the same file still stops on libfuse.
  **Cause:** that old runtime knows the option, not the variable.
  **Fix:** the option. **How found:** both tried.
- **Symptom:** the stereo mode written into the settings file does nothing when the program is started through the AppImage.
  **Cause:** the program names its settings file after the name it was started with: `AppRun.ini` through the AppImage, `CADAssistant.ini` from the unpacked tree or a link of that name.
  **Fix:** start it under one name everywhere (the link in `/usr/bin` carries the program's own name), and in a test write the file for the name under test.
  **How found:** the list of files the run left in the test home.
- **Symptom:** on NVIDIA's own OpenGL the program in quad buffer mode shows "Internal error happened while redrawing the view. SIGSEGV ... Please restart the application."
  **Cause:** NVIDIA's GLX lists no stereo configuration under Xwayland; Qt falls back to a plain one and the program draws to a right buffer that does not exist.
  **Fix:** the edition's default for such desktops, Mesa on NVIDIA's Vulkan driver (zink), where the same mode passes; see [nvidia-opengl.md](nvidia-opengl.md).
  **How found:** the same case with `__GLX_VENDOR_LIBRARY_NAME=nvidia` and the capture of the program's own dialog.
- **Symptom:** on a desktop that announces no stereo, the program in quad buffer mode shows one flat picture without its tool strip, and says nothing.
  **Cause:** no stereo visual is offered there, and the program does not check.
  **Fix:** none on our side; say it on the page for people on other desktops. **How found:** the root property removed before the start.
- **Symptom:** a settings value changes by itself during a test of the settings window (a slider moved, the scene went dark).
  **Cause:** the scroll wheel over a slider changes its value. **Fix:** scroll with the pointer over the labels. **How found:** the settings file after the run.
- **Symptom:** the first click after the program starts does nothing.
  **Cause:** it only gives the window the focus. **Fix:** one click on empty background first.
- **Symptom:** a measured cursor disparity is too small at one spot once the 2D parts are in both eyes.
  **Cause:** a panel of the program covers half of the cross in one eye there. **Fix:** measure where no panel is near.
- **Symptom:** a `.pns` picture opened in a text viewer floods the screen.
  **Fix:** look at a copy named `.png`.

## The frame a real output gets

Read on 2026-11-14 with the real-output bench ([real-output-readback.md](../../stereo-proof-rig/references/real-output-readback.md)): a guest without a card, a VKMS output in the side by side (full) mode, KWin started with `--drm --xwayland`, the program on the software renderer.

- The bench's session starts KWin without Xwayland; an X11 program needs `--xwayland` added and `/tmp/.X11-unix` made in the guest's `/tmp` (a fresh tmpfs has none, and KWin logs `/tmp/.X11-unix does not exist`).
- The buffer recorder reads Wayland clients only. For an X11 program take a ScreenShot2 capture in the same guest session and compare it with the scanned-out frame pixel by pixel: here they were equal within 8 levels in all 4,147,200 pixels, so the output path draws what the capture draws.
- `XGetImage` of a quad buffer window returns one view (the X window stays one eye wide and the presented buffer is twice as wide), so it is not the committed buffer.
- **Symptom:** in that guest each eye shows half of one picture, stretched: the tool strip and the left of the model in the left eye, the right of the model in the right eye; a disparity search finds no block.
  **Cause:** Xwayland without glamor (a machine or guest without any GPU). The same picture comes in a rig on a GPU with `XWAYLAND_NO_GLAMOR=1`, with the program on the GPU or on the software renderer, and with glamor the same software-rendered program is a correct pair; so it is neither the program, nor Mesa's software renderer, nor the output path.
  **Fix:** not built yet; it belongs to the Xwayland path that takes a quad buffer window's wider buffer.
  **How found:** one difference at a time: software renderer with glamor (a pair), glamor off (the split), then the capture against the scanout in the guest.
  Until it is fixed, a quad buffer X11 program is not shown in stereo in a virtual machine without 3D acceleration.

## The 3D mouse

A program that reads a 3D mouse on Windows may have no reader at all on Linux; the notes of this one say "on Windows".
Measure it instead of reading it: a stand-in spacenavd on `/var/run/spnav.sock` with a control client that must be served ([3d-mouse-libspnav.md](3d-mouse-libspnav.md)), `strace -f -e trace=openat,connect` on the program (no spacenav socket, no `hidraw`, no `/dev/input`), `xlsatoms` (none of the spacenav X11 atoms `MotionEvent`, `ButtonPressEvent`, `CommandEvent`), and a capture before and after simulated motion (0 differing pixels).
The boundary is then a fact: such a program moves only by pointer and keyboard events, so a 3D mouse reaches it only if its vendor adds a reader or the desktop turns the device into the events the program already takes.

## What this recipe does not prove

- The scanned-out frame of a correct pair: the bench's guest has no GPU, so its Xwayland has no glamor and the pair is lost before the compositor (above); what was shown is that the output path equals the capture.
- An absolute disparity against a closed form: the camera's numbers are the program's.
- The start through FUSE on a system that has the old library.
