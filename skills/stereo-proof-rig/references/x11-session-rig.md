# An X11 player in the rig: one fresh session per case

Learned proving VLC Stereo's X11 path (ORDER 265, November 2026).
The scripts are in `../scripts`: `x11_props.py`, `x11_propagation.py`, `eyes_share.py`, `kwin_script.py`, `vlc_mpris.py`, `support-shim.c`, `make-barcode-fixtures.sh`, `columns.py`.

## Recipe

1. Container as the proof-rig skill says, the image holding the edition's Stereo KWin, its Xwayland and the player. Give it a passwd and group file that name the user it runs as, mounted read-only over `/etc/passwd` and `/etc/group`: without a passwd entry for the user, `dbus-run-session` cannot start the bus.
2. Give the container a GPU: Stereo KWin's virtual output needs a render node. With none, KWin logs `Failed to open drm node` and falls back to software drawing that has no stereo, and ScreenShot2 answers `Cancelled`. On a machine where the integrated GPU is off limits, the NVIDIA card through CDI (`--device nvidia.com/gpu=0` and the render group) is enough: the player's own GL runs on whichever card the container sees.
3. Per case, inside `dbus-run-session`: start `kwin_wayland --virtual --xwayland --socket=w --width 1920 --height 1080`, wait for the socket, start the player with `QT_QPA_PLATFORM=xcb` and `DISPLAY=:0` (the X11 path) or `wayland`, wait about six seconds, then act.
4. Act and read back, one step each:
   - the screen: ScreenShot2 `CaptureActiveScreen` (`scripts/capture.py`); a stereo capture is twice the output's width, so `stereo` true and 3840 by 1080 means both eyes were drawn;
   - the colours: `scripts/eyes_share.py` gives the share of the clip's red (left view) and blue (right view) in each half;
   - the declarations: `scripts/x11_props.py` walks the X window tree and prints every window with `_KDE_NET_WM_STEREO_CONTENT*` properties (and `_CHILDREN` on the top-level), with the root's support version;
   - window size and full screen: `scripts/kwin_script.py LOG 'JS'` runs one KWin script (`workspace.activeWindow.frameGeometry = {...}`, `.fullScreen = true`);
   - the second file and stop: `scripts/vlc_mpris.py open FILE`, `stop`, `status` on the player's MPRIS name.
5. The 3D clip: two 960 by 540 views, the left red and the right blue, a white box in each (at different columns so the eyes differ), H.264 with the frame packing SEI type 3, in Matroska with one view's display size. Make a static one (every frame equal) for byte comparisons, and a 2D clip with a fixed box.

## Traps

- **Full screen through key presses or clicks of the fake input client did not reach the player on X11** even for the distribution's own VLC, in this rig, while the pointer, the tooltips and the window all worked. Start the player with `--fullscreen` for the full-screen case, and use `kwin_script.py` for window size changes.
- **`Fullscreen state changed` in VLC's log is not a full screen**: it is printed when the video output starts.
- **The window manager's full screen is not the player's**: `workspace.activeWindow.fullScreen = true` sets KWin's flag but VLC keeps its menu bar and controls; only the player's own full screen resizes the video child.
- **`No space left on device` from dbus-daemon about inotify** is the host's inotify limit, harmless for the case.
- **The negative paths**: preload `support-shim.so` (`cc -shared -fPIC`) so that `stereo_supported_x11()` returns `$STEREO_SHIM_SUPPORT` (4: no child windows; 7: no places of views); set the variable in the same `LD_PRELOAD=... STEREO_SHIM_SUPPORT=N` word list you give the player, the container does not pass it on. `STEREO_SHIM_WAYLAND` is not needed: the shim also refuses `stereo_declare_wayland()`, which tests the Wayland notice. The program must have said why each time.
- **Pointer events through a window that selected none**: `x11_propagation.py` selects pointer motion on the video window's parent, moves the pointer over the child with xdotool and prints the events the parent received; button events are not selectable there because Qt holds ButtonPress on its window (one client only, a silent `BadAccess`). xdotool's clicks did not toggle pause or full screen in this rig even for an unmodified player, so a click is not a test here.
- **A top-level window listed as child**: in `x11_props.py`'s output the video child has `_KDE_NET_WM_STEREO_CONTENT` = 3 and the top-level `_CHILDREN` = the child's id; both must be gone after the video closes.

## The installed package, not the build tree

Run the case in a container that installs the packages first: as root, add the user to the container's own `/etc/passwd` and `/etc/group` (do not mount a replacement over them: `dpkg` stops on `unknown system group 'messagebus'`), `dpkg -i` the `.deb` files of the candidate, then `setpriv --reuid=UID --regid=GID --groups=RENDERGID` into the case. The published version in the image is the negative control: the same cases, the same clips, no packages added.

## Results to expect

For a 3D clip on the X11 path through Xwayland, the published VLC Stereo +stereo3d16 gives a capture one output wide (`stereo` false) with the left view only, and +stereo3d17 gives two outputs wide with the left half red and the right half blue (86 to 100 percent of each half, depending on how much of it the video covers), the interface identical in both halves, and the same after a resize and in full screen. The Wayland captures of the two versions are equal pixel for pixel, and so are the captures of a 2D clip.

## Every column of each eye

`scripts/make-barcode-fixtures.sh` makes a full side by side clip whose columns each carry their number (ten luma bands) and the eye (a band), and `scripts/columns.py CAPTURE EYE X0 Y0` reads them back from a stereo capture (twice the output's width), searching a few pixels around the corner. Use a window the video fills exactly (`960 x (540 + chrome)`), so that nothing is resized between the clip and the capture: a path that resamples loses columns (the half layout keeps 480 of 960), a path that copies keeps all 960. The grey bands survive 4:2:0 and a lossless x264 (`qp=0`, frame packing SEI type 3).
