# The Game Mode applet takes plasmashell down at login

A core limit of exactly 1 suppresses the piped core helper; a zero limit does not, as the [crash trap](../../stereo-proof-rig/SKILL.md#traps-that-fooled-us) explains.

Symptom first: plasmashell dies with SIGSEGV a few seconds after login, systemd-coredump keeps several dumps, and the stack is in `libplasma-gamemode.so`: `QObject::deleteLater` called from the lambda in `GamesModel::reload()` (`src/gamesmodel.cpp`), reached from `QDBusPendingCallWatcher::finished`.
The journal shows `GamesModel::reload()` twice, the lambda twice, then the crash.
The applet is Debian's `plasma-gamemode` (Harald Sitter's applet, version `0.0~git20240315.4d60358-2`) on the edition's panel.
Seen on the A10 on 2026-11-19 (ORDER 755), six dumps.

## Cause

`reload()` runs when the model is made and again when the `com.feralinteractive.GameMode` service gets an owner (a `QDBusServiceWatcher`), so a service that starts while the first `ListGames` answer is on its way makes it run twice.
Each run calls `reset()` (which gives up the old watcher and sets `m_getManagedObjectsWatcher` to null), then makes a new watcher and stores it in the member.
The handler of every watcher did `m_getManagedObjectsWatcher->deleteLater(); m_getManagedObjectsWatcher = nullptr;`, reading the member, not its own watcher.
When both answers wait in the event queue together, the first handler deletes the second watcher and clears the member, and the second handler calls `deleteLater()` on a null pointer.
Why the old watcher's handler still runs: `reset()` makes a blocking D-Bus call (`isServiceRegistered`) before it calls `deleteLater()` on the old watcher, and the first answer arrives while it waits, so the answer is in the queue before the `DeferredDelete`.

## The fix and its search

Upstream (invent.kde.org/sitter/plasma-gamemode, searched 2026-11-19): no commit after 4d603583 of 2024-03-15, issue 1 and merge requests 1 to 3 are about Plasma 6 and translations; Debian's tracker has no bug for the source or the binary (SOAP `get_bugs`, `package` and `src`).
So the fix is ours, a patch on Debian's source with a DEP-3 header (`Origin: vendor`, `Forwarded: no`): the handler captures its watcher and deletes that one, clears the member only when `m_getManagedObjectsWatcher == watcher`, and `reset()` calls `disconnect(this)` on the watcher it gives up.
No functionality changes: the applet stays on the panel and lists the games.

## The test that fails before and passes after

`sparky-os/packages/plasma-gamemode/tests/` in the build tree:

1. `standin.py` owns `com.feralinteractive.GameMode` on a private session bus (Gio, no gamemoded and no game), answers `ListGames` with one game and the game's properties.
2. `race-test.cpp` builds the real `gamesmodel.cpp` and its generated D-Bus classes against the source folder given, makes the model inside the event loop, blocks the thread for 100 ms, calls `reload()` again, blocks 300 ms more (the shell busy loading the panel), then runs the loop and exits 0 only when the model ends not waiting, with the one game.
3. `run.sh SRC [N]` starts `dbus-run-session`, the stand-in and the test N times and counts crashes.

Rerun in a container with the Qt 6 and KDE build packages: `bash tests/run.sh /path/to/plasma-gamemode/src 200`.
Measured 2026-11-19: Debian's source, 29 of 30 runs crash with signal 11 (gdb: `#0 QObject::deleteLater()`, `#1` the lambda at `gamesmodel.cpp:214`, `QDBusPendingCallWatcher::finished`); the patched source, 200 of 200 runs end 0.

## Traps

- **A test that calls `reload()` twice at once does not crash.** The second `reload()` deletes the first watcher before any answer arrives. The crash needs the first answer in the queue before the second reload: block the thread between the two calls (`QThread::msleep`) and make the stand-in answer at once (`DELAY_MS=0`).
- **A stand-in that answers after 400 ms crashes 1 run in 20.** The blocking call inside `reset()` returns before the answer arrives, so the order of the queue changes from run to run. Fix: answer at once and hold the thread.
- **`dbus-run-session` as a user with no passwd entry stops with "Looking up user ID 1000: not found"** in a container. Run the test as root, with `--ulimit core=1`.
- **gdb's timing hides the crash** unless the stand-in's delay is set to 0 in the gdb run too.
