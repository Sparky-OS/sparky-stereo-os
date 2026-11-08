# A session's start order: which screen the first windows open on

Load this when new windows, a password prompt or an autostart program open on a screen that is not the one marked main in Display Settings right after a login, and they follow the pointer once it moves.

## What it is

Stereo KWin starts its active output on the screen marked main (priority 1 of Display Settings, the front of `Workspace::outputOrder()`), and a window is placed on the active output until the pointer moves.
Something between KWin's start and the first program window can still move the active output, so the rig must run the session's real order, not a single client.

## Recipe: reproduce the start red

The script `scripts/session-start-order/session-start-order.sh` runs inside a plasma rig image (kwin-wayland, plasmashell, kactivitymanagerd, a Wayland test client) and does this, in the order of a login:

1. A private session bus (without kded6, baloorunner, krunner and KSplash service files: they abort in a container and the host logs the crash).
2. `kwin_wayland --virtual --output-count 3` once, so KWin writes `kwinoutputconfig.json`; stop it with SIGTERM; set the person's order in the `setups` section (`priority` per `outputIndex`, 0 is the main screen) so that it differs from the backend's order; this is how the saved order of a three-output person is made without a hand-written file.
3. The person's focus settings in `kwinrc`: `[Windows] FocusPolicy=FocusFollowsMouse`, `DelayFocusInterval=300`, `AutoRaise=true`, `AutoRaiseInterval=750`, `ClickRaise=true`, `SeparateScreenFocus=true`.
4. A KWin script (`scripts/session-start-order/startlog`) enabled in `kwinrc` `[Plugins] startlogEnabled=true`, in a data folder of the session, so it runs from KWin's first moment: it prints, with the time, every `windowActivated`, `windowAdded` (with the output the window is on) and the active screen at that moment.
5. KWin again with the saved order, then (with `SPLASH=1`) `ksplashqml` with the session's theme, then kactivitymanagerd, then plasmashell, then, after `DELAY` seconds, the autostart program, before any pointer motion. With the splash: it is closed a few seconds later (`SPLASH_TAIL`) and a second program maps after it is gone. Do not delete the KSplash service from the rig's bus and leave the splash out: on a real login the splash is up for about 35 seconds and the autostart programs map while it is.

Expected on a build with the defect: `active=` flips from the main screen to another output on the first plasmashell `ACTIVATED ... desktop=true` line, and the program opens on that output.
Use `DELAY` of 8 or more: with a short delay the program maps before Plasma's desktops, becomes the active window, and the case passes by luck (the first run of lane 466 did).

## Recipe: name the code path

A KWin build with a trace in `Workspace::setActiveOutput()` that prints the old and new output, the active window and `backtrace_symbols_fd` (guarded by an environment variable, kept out of the commit), run with its `libkwin.so` and `kwin_wayland` mounted over the packaged ones (`KWINBIN` and `LD_LIBRARY_PATH`).
The frames name the function; `addr2line` is needed only for the unnamed ones.
`gdb` inside the rig was not usable (the plasma image's gdb refused to execute); the build image's gdb was not tried with a breakpoint on this path, so a printed backtrace is the recipe that worked.

## Trap: the session's own surfaces take the active output as they map

- Symptom: after a login with the pointer untouched, the KDE Wallet prompt, OpenRGB or any autostart program opens on a screen that is not the main one; clicking the main screen's desktop once cures it. Upstream: bugs.kde.org 500904, 501527, 489904, no fix on KWin master or Plasma/6.7.
- Cause, two surfaces of the session's shell, same line: `Workspace::setActiveWindow()` ends in `setActiveOutput(window->output())`, and `Workspace::addWaylandWindow()` activates a new window that accepts focus when it may be activated or when no window is active.
  - Plasma maps one desktop window per output in the order of its screens; the first, activated because nothing else is, takes the active output (the trace: addWaylandWindow, activateWindow, requestFocus, setActiveWindow, setActiveOutput).
  - `ksplashqml` makes one overlay layer-shell window per screen with the exclusive keyboard, and each is activated as it maps: the active output ends on the screen the splash served last, not on the main screen (the first run of this lane left the splash out of the rig and missed it; on the station the autostart programs map while the splash is up).
  - It does not depend on the focus policy.
- Fix: `setActiveWindow()` does not move the active output for a desktop (`isDesktop()`) or a layer-shell window (`LayerShellV1Window`); the pointer, `performMouseCommand`, `switchToOutput` and the activation of a program's own window still do. A launcher (KRunner, a layer-shell launcher) opens on the active output, so activating it moves nothing. Chosen over the narrow form (an exemption around the one `activateWindow()` in `addWaylandWindow()`, which needed a flag member and so a header change): a layer-shell surface can also be activated later, from `LayerShellV1Window::handleAcceptsFocusChanged()` (not seen in the trace, but in the code), and the one guard covers every path.
- How it was found: the logger above showed `active=` changing on the first `ACTIVATED plasmashell ... desktop=true`, and, with the splash, on each `ACTIVATED ksplashqml`; the trace build named the path for both.
- Why a short rig missed the splash and `testOutputOrder` passed: the first maps no desktop or splash window. With the main screen last in the splash's order the splash is right by luck, so the test and the rig must put the main screen first and in the middle too (`testSessionStart`).
- A layer-shell surface must be given the client's `wl_output` by index (`Test::waylandOutputs().value(i)` for the workspace's i-th output): looking it up by position gives the first output while the position events have not arrived, and the test passes or fails by timing.

## Trap: a dev `libkwin.so` over the packaged plugins

- Symptom: a rig that mounts a freshly built `libkwin.so` and `kwin_wayland` over the packaged ones crashes at start ("KCrash: Application 'kwin_wayland' crashing", plasmashell then waits a minute for the bus).
- Cause: a member added in the middle of `Workspace` in `workspace.h` moves the members behind it, and the packaged plugins read them through inline accessors with the old offsets.
- Fix: add a new member at the end of the private members, or mount the plugins from the same build. Found by: the same binaries ran until the header changed.
