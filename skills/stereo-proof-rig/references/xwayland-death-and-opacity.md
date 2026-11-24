# Xwayland killed under a virtual KWin, and a window's opacity read from a capture

For a fault that shows only after Xwayland went away: one fresh session per case, an X11 window selected, then Xwayland killed (or, as controls, the X11 client killed, or nothing), then Wayland windows selected in turn, with a ScreenShot2 capture after each step.
Written on 2026-11-24 for queue row 862 (every selected window stayed translucent after Xwayland died); the scripts are in [`scripts/xwayland-death`](../scripts/xwayland-death/).

## The recipe

1. **The image:** the edition's packages from the published tree on Debian testing of a dated snapshot ([dated-snapshot-rig.md](dated-snapshot-rig.md)), plus `dbus`, `libglib2.0-bin` (`gdbus`), `python3-gi`, `python3-numpy`, `python3-pil` and a compiler with `libwayland-dev`, `wayland-protocols` and `libxcb1-dev` for the two test clients:
   - `wl-solid APP_ID W H [RRGGBB]`: an xdg toplevel of one opaque colour (`wl_shm`, XRGB8888), title and app id both APP_ID; it reads its socket every turn, so KWin's pings are answered.
   - `x11-solid NAME W H [RRGGBB]`: an X11 window of one colour, `WM_NAME` and `WM_CLASS` both NAME; it prints the error and exits 3 when the X connection ends.
   Build them with `wayland-scanner client-header` and `private-code` from `stable/xdg-shell/xdg-shell.xml`.
2. **The desktop's configuration:** mount the shipped `/etc/xdg/kwinrc` of the look package read-only at `/etc/xdg/kwinrc` (the edition's has `translucencyEnabled=true` and `[Effect-translucency] Inactive=91`); KWin reads it through `XDG_CONFIG_DIRS`.
3. **The session** (`session.sh OUT CASE`, under `dbus-run-session`, as an ordinary user, `RIG_BIN` and `CAPTURE` set): `kwin_wayland --virtual --xwayland --socket=sub --width 1280 --height 800` with `KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1`; two Wayland windows, then the X11 window; a KWin script (`org.kde.kwin.Scripting.loadScript`, then `run`) places them (`w.frameGeometry = {...}`) and selects the X11 one (`workspace.activeWindow = w`), with `print()` lines that reach KWin's log through `QT_LOGGING_RULES='kwin_scripting.debug=true'`.
4. **The cases:** `xwayland-killed` (`kill -9 $(pidof Xwayland)`), `client-killed` (the X11 client killed), `close-during-animation` (the X11 client killed and a Wayland window selected within 50 ms, while the closing effect runs) and `control` (nothing goes). KWin's default crash policy restarts Xwayland at the next X11 connection.
5. **The measurement** (`measure.py OUT`): white windows over KWin's black desktop, so a window's opacity is the median red value of a 40x40 patch in its middle divided by 255; a background patch must read 0. Each capture names the window that should be selected: it must read 1.00 and the other Wayland window the inactive opacity.
6. **The container:** a render node and its group, `--cap-add SYS_NICE` (kwin_wayland's file capability), `--ulimit core=1`, `--network none`. Loops go on a card that drives no one's screens (an NVIDIA card through CDI: `--device nvidia.com/gpu=0` and the render group).

## The rows, measured on KWin 6.7.4 +stereo3d64 (published), NVIDIA card

| Case | X11 window selected | after: wl-a selected | after: wl-b selected | journal lines |
| --- | --- | --- | --- | --- |
| Xwayland killed | x11-a 1.00, wl-a 0.91, wl-b 0.91 | wl-a **0.91**, wl-b 0.91 | wl-b **0.91**, wl-a 0.91 | 2 (`Window property references invalid window`) |
| X11 client killed | the same | wl-a 1.00, wl-b 0.91 | wl-b 1.00, wl-a 0.91 | 0 |
| killed during its closing animation | the same | wl-a 1.00, wl-b 0.91 | wl-b 1.00, wl-a 0.91 | 0 |
| control (nothing goes) | the same | wl-a 1.00, wl-b 0.91, x11-a 0.91 | wl-b 1.00, wl-a 0.91, x11-a 0.91 | 0 |

The cause and the fix: [stereo-window-3d-area, a scripted effect that keeps a window that died](../../stereo-window-3d-area/references/effect-keeps-a-dead-window.md).

## What the person is told: a stand-in notification server

`fake-notifyd.py OUT` owns `org.freedesktop.Notifications` on the session's private bus (Desktop Notifications 1.2: `Notify`, `GetCapabilities`, `GetServerInformation`, `CloseNotification`) and writes every `Notify` as one JSON line; start it before KWin (`FAKE_NOTIFY=1` in `session.sh`).
With Xwayland killed, KWin 6.7.4 sent no `Notify` at all: KWin reads the broken X11 connection first (`kwin_xwl: The X11 connection broke`), and `XwaylandLauncher::stop()` disconnects the process's `finished` signal, so the "Xwayland has crashed" popup (`kwin.notifyrc`, `xwaylandcrash`, `Action=Popup`, translated in the ten languages) is never reached on that path.
Read the person's problems store too (`$XDG_STATE_HOME/sparky-stereo-problems`).

## Traps

- **Symptom:** every capture fails with `org.kde.KWin.ScreenShot2.Error.Cancelled: Screenshot got cancelled`, and KWin's log says `Configured compositor not supported by Platform. Falling back to defaults`. **Cause:** no render node in the container, so the virtual backend has no OpenGL and no effects; `LIBGL_ALWAYS_SOFTWARE=1` does not help. **Fix:** give the container a render node. **How found:** the first lines of KWin's log.
- **Symptom:** a change to a scripted effect's `main.js` does not reach a KWin test that was built before. **Cause:** `kwin_add_script` and `kwin_add_scripted_effect` copy the package into the build tree's `bin/` with `file(COPY)` at configure time. **Fix:** run CMake again before the tests, or mount the new `main.js` over the installed one in the rig.
- **Why the session waits 1.5 s after the kill** (read in the source, not measured as a failure): while a closing effect still holds the dead window as a deleted window, `window.deleted === true` stops the Translucency effect without an error, so a selection made then can pass on the old build; wait longer than the closing animation before selecting another window.
