# A scripted effect that keeps a window that died

Found on 2026-11-24 (queue row 862) on a desktop where every window stayed translucent when selected, after Xwayland had died.
Written for KWin 6.7.4 with the edition's patches; upstream KWin's master had the same code on that day.

## The symptom

- What the person sees: the selected window does not become opaque any more; every window, selected or not, stays at the inactive opacity of the Translucency effect (91 % in the edition's `/etc/xdg/kwinrc`, `[Effect-translucency] Inactive=91`).
- What the journal says, once at each window switch, from the compositor:

  ```
  kwin_wayland_wrapper[PID]: <Unknown File>:171: Error: Window property references invalid window
  ```

  `<Unknown File>` is a scripted effect (KWin evaluates its `main.js` without a file name); the number is the line in the installed file, which the edition installs without comments, so line 171 there is line 184 of the authored file (`set({window: window, ...})` in `inactive.animate`).
- What came before it: Xwayland went away while an X11 window was the selected one (`kwin_xwl: The X11 connection broke (error 1)`), and Xwayland started again.

## The cause

1. When Xwayland goes away, KWin releases its X11 windows through `Workspace::cleanupX11()` and `X11Window::releaseWindow(true)`, the shutdown path, which skips `activateNextWindow()`.
   `Workspace::removeWindow()` then set `m_activeWindow` to null without emitting `windowActivated`, so effects and scripts were never told that the selected window went.
   Effects do get `windowClosed` and `windowDeleted` for those windows; only the activation is missing.
2. The Translucency effect keeps the active window in `translucencyEffect.activeWindow` and, at each activation, first animates the previous active window to the inactive opacity, then stores the new one.
   Its stored window was the X11 window; once KWin destroyed that window's `EffectWindow`, the JavaScript object stayed but its `QObject` was gone: every property reads `undefined`, so none of the guards in `inactive.animate` (`window.deleted === true`, `window.managed === false`) stops it, and `set()` throws (`ScriptedEffect::animate_helper()`: `qobject_cast<EffectWindow *>` gives null).
3. A throw ends the JavaScript function there (Qt's `QJSEngine::throwError()` "will interrupt the normal flow of execution"), so the new window was never stored and its inactive animation never cancelled; the next activation met the same dead window again, for ever.

A program killed, a window closed and a window closed during its own closing animation do not do this: those paths call `activateNextWindow()` before the window is removed.
Only a window released without an activation after it does.

## The fix (in the edition's KWin from +stereo3d65)

- **The engine:** `removeWindow()` changes the active window through `setActiveWindow(nullptr)`, so `windowActivated(nullptr)` reaches every effect and script, as for any other change. It also clears `_NET_ACTIVE_WINDOW` and the window's disabled global shortcuts. `Window::setActive()` returns at once for a deleted window, so the call is safe on every removal path.
- **The effect:** it forgets its stored window in `effects.windowDeleted` (what upstream did for the C++ Dim Inactive effect, Vlad Zahorodnii, d57be742ff, bug 442222: "a window can be deleted without prior windowClosed signal"), and it stores and reverts the newly active window before it animates the previous one, so a failure on the previous window is still printed but can no longer leave every later window translucent.
- **Every effect that keeps a window between calls needs the same:** clear the stored window in `windowDeleted`, and never let work on an old window come before the new state is stored. Read on 2026-11-24: of the scripted effects and scripts KWin 6.7.4 ships, only Translucency kept a window; Slide, Slide Back and Dim Inactive (C++) already clear theirs in `windowDeleted`.

## How it was found

The journal line's file and line led to the installed `main.js`; `grep -rn "references invalid window" src` found the throw in `scriptedeffect.cpp`; reading who emits `Workspace::windowActivated` (only `setActiveWindow()`) and every caller of `removeWindow()` showed the shutdown path that skips the activation.
The rig ([stereo-proof-rig, Xwayland killed under a virtual KWin](../../stereo-proof-rig/references/xwayland-death-and-opacity.md)) reproduced it: the selected window read 0.91 of white on the capture after Xwayland was killed, and 1.00 with a killed X11 client instead.

## Relief on a running desktop (no restart)

Reload the effect; its stored window starts again from the current active window:

```
qdbus6 org.kde.KWin /Effects unloadEffect translucency
qdbus6 org.kde.KWin /Effects loadEffect translucency
```

## The tests

KWin's own integration tests from +stereo3d65: `testTranslucencyXwayland` (Xwayland killed with an X11 window selected, then two Wayland windows selected in turn; it fails on the script error and on an opacity the effect holds below 100 % on the selected window) and `testXwaylandServerCrash` (the compositor must say that no window is selected after the selected X11 window went with Xwayland).
Measured on 2026-11-24 on the NVIDIA card: on +stereo3d64 with the tests added, `testTranslucencyXwayland` fails twice (`<Unknown File>:184: Error: Window property references invalid window`, then the selected window held at 91) and `testXwaylandServerCrash` once (no `windowActivated` after the crash); with the fix both pass, and testTranslucency, testWorkspaceTeardown, testX11Window (248) and testXwaylandServerRestart pass as before.

The effect's state is not public to a test (`AnimationEffect::state()` is protected); `Effect::debug()` lists each animated window by its caption with each animation's attribute and target, so the test titles its windows and reads the lowest `To:` of an `Opacity` animation.

## A trap met on the way: a library call at the compositor's start moved a race

The first form of the edition's Xwayland notice (KWin's notice through sparky-stereo-problems that Xwayland stopped) cleared an old notice at KWin's start.
Symptom: `testXwaylandServerRestart` failed 4 runs in 5 (15 s each, `stoppedSpy.count()` 0), and passed 5 in 5 without that call. Cause: when Xwayland dies, KWin reads either the dead process first (`XwaylandLauncher::handleXwaylandFinished()`, which the test waits for) or the broken X11 connection first (`Xwayland::dispatchEvents()`, whose `stop()` disconnects the process's signals); the call at the start moved which came first, though it changed no signal disposition and left no descriptor open (both measured with a probe around `dlopen` and the call). Fix: nothing is called at the start. How found: five runs each of the red build, the green build, the green build without the call and with the call deferred (0, 4, 0 and 1 failures).
