# Sending keys and clicks to a program in the rig, and knowing they arrived

Learned in ORDER 441 (November 2026), after ORDER 265 recorded that key presses and clicks did not reach VLC in the rig.
They do reach it: on X11 through Xwayland and on Wayland, for the distribution's own VLC and for VLC Stereo.
The loss was in the rig's own script, twice, and nothing in Stereo KWin was at fault.

## Recipe

1. Build the client in the rig: `scripts/build-fakeinput.sh OUTDIR` (wayland-scanner, a C compiler, libwayland-dev).
   `fakeinput` speaks KWin's `org_kde_kwin_fake_input` and needs `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1` in KWin's environment.
2. Keep one client connected for the whole case: `fakeinput --serve IN ACK` reads lines from the fifo IN, one line per call, and answers `ok` or `error` on the fifo ACK.
   KWin's fake input device, and with it the seat's pointer, lives only while the client is connected.
3. A line holds steps separated by white space; a comma belongs to a step and never separates steps:
   - `m:X,Y` move the pointer (logical pixels); `b:272` click; `d:272` double click; `k:57` press and release a key (evdev code, `k:29+35` is Ctrl+H); `s:MS` wait.
   - Common evdev codes: 33 F, 1 Esc, 57 space, 272 BTN_LEFT.
4. Move the pointer over the video first (`m:` the middle of the window's client area, read from KWin's window list), then send the key or the click.
   Keys go to the focused window; a click goes to the window under the pointer.
5. Read back the program's own state, before and after, and fail when it did not change: `scripts/mpris_state.py` prints VLC's `PlaybackStatus` and `Fullscreen` from its MPRIS name; KWin's window list (`kwin_windows.py`; `kwin_script.py` changes a window) gives the window's full screen flag.
   `scripts/input_case.sh OUT PLAYER PLATFORM CASE` does all of it for the cases `dbl`, `f`, `esc`, `space` and the negative control `neg`, and `scripts/input_verdict.py` decides.
6. The negative control: open a second window (`xev`, with `stdbuf -oL` so its log is not buffered) so that it takes the focus, send the key, and require two things at once: the player's state unchanged, and the second window's log showing the `KeyPress`. A control that only shows "nothing happened" proves nothing; the second window shows where the key went.

Expected on the rig of ORDER 441 (Stereo KWin 4:6.7.4-2+stereo3d43+lc1, Xwayland 2:24.1.13-1+stereo3d4+lc1, Qt 5.15.19): stock VLC 3.0.24, VLC Stereo +stereo3d16 and +stereo3d18, X11 and Wayland, 5 of 5 cases each.
A stock VLC started with `QT_QPA_PLATFORM=wayland` still runs through Xwayland (its log has no `xdg_toplevel` line); VLC Stereo's native Wayland window has them.

## Sending through the X server (xdotool) instead

`xdotool` uses the XTEST extension. Since KWin 6.1 Xwayland hands XTEST events to KWin through libei, and KWin asks the person to allow it (a prompt window, `kwin-xwayland-eis-prompter`).
In a headless session nobody answers, KWin drops the events, and nothing is logged.
Allow it in the rig's own `kwinrc`, as a user would: `[Xwayland]` `XwaylandEisNoPrompt=true` (`XwaylandEisNoPromptApps` names single programs).
`scripts/diag-xtest.sh OUT` shows the difference with `xev` as the witness: without the key 0 KeyPress and 0 ButtonPress, with it 3 and 1.
`INPUT_TOOL=xdotool` in `input_case.sh` writes that file.

## Traps

- **Symptom:** the pointer moves, tooltips appear, but keys and clicks do nothing, even for an unmodified player. **Cause:** a shell function `inp() { echo "$*" >&7; ... }` called inside a loop that set `local IFS=,` (to split a comma-separated list of steps). `"$*"` joins with the first character of IFS, so `m:960,500 s:60 k:33` became `m:960,500,s:60,k:33`, one token. `fakeinput` split on white space, read the token as `m:` with `sscanf("%lf,%lf")`, moved the pointer, ignored the rest and answered `ok`. **Fix:** `local IFS=" "` inside the function that joins; `fakeinput` now reads a step whole or refuses it (`error` on the fifo), and the session stops with `INPUT-FAILED` when a step is refused. **Found by:** `steps.log`. `fakeinput` prints every step it runs with its time; the lines of the failing runs held one long token with commas where the working runs of ORDER 249 had one line per step. Always read that log before blaming the compositor.
- **Symptom:** `xdotool key` or `xdotool click` changes nothing in the rig (and `xdotool getwindowfocus` names the right window). **Cause:** KWin's Xwayland input prompt, see above. **Fix:** `XwaylandEisNoPrompt=true` in the rig's `kwinrc`. **Found by:** `xev` as the witness (0 events), then `[xwayland ei] Unhandled event EI_EVENT_SYNC` in the log and the source of `src/plugins/eis/xwaylandeiscontext.cpp`.
- **Symptom:** a witness program's log shows no key although the key arrived. **Cause:** stdout redirected to a file is block buffered, and a program killed by a signal loses the buffer. **Fix:** `stdbuf -oL xev ...`.
- **Symptom:** a test that sends input passes although nothing was sent. **Cause:** the step ran without a check on the program. **Fix:** every case reads the program's state before and after; a case with no change is a failure. Run the case on a build you know ignores the input to see it fail (the old comma-joined line is one; `scripts/test-fakeinput.sh` is the tool's own red-green test).
- **Symptom:** a hand-made `Fullscreen` changes in MPRIS but the window does not. **Fix:** compare with KWin's window list (`fullScreen` of the normal window); `input_verdict.py` requires both.
