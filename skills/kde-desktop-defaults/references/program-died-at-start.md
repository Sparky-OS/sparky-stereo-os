# A program sent to a GPU that dies at start

Symptom first: the person starts a program from the menu, KRunner or Dolphin, nothing appears on screen and no message comes, and the program had been sent to a GPU by the Graphics page (a browser on the discrete GPU while the compositor draws on another).
The user journal has the answer already: `app-NAME@ID.service: Main process exited, code=dumped, status=11/SEGV`, then `Failed with result 'core-dump'`.
Nobody was told, because KIO's launcher finished its job when the program started.

## Where the watch lives, and why

KIO runs every program of a desktop entry as a transient systemd service, `app-NAME@ID.service` (`SystemdProcessRunner`, XDG standardization for applications on systemd.io/DESKTOP_ENVIRONMENTS), with `Type=simple`, `ExitType=cgroup`, `SourcePath` the desktop file and the whole launch environment in `Environment`.
systemd keeps how it ended (`Result`, `ExecMainStatus`, `ActiveEnterTimestampMonotonic`, `InactiveEnterTimestampMonotonic`).
So the watch is a systemd hook, and the edition runs no watcher of its own.
Measured alternatives, and what each misses:

- **A start-and-watch in `sparky-stereo-gpu-run`.** KIO does not call it: it asks `sparky-stereo-gpu-env --app` for the variables and starts the program itself, so the menu launch, which is the failure that happened, never passes through it. To watch, the wrapper must stay alive as the parent for the program's whole life (a process left running, a changed process tree for Steam and pressure-vessel). It would cover only Steam's launch options and a terminal, which have no desktop entry to name.
- **KIO's resolver (the 346g patch).** It runs before the program starts and can refuse; it cannot know how the program ends. Watching from `KProcessRunner` means a patch to carry on every KF6 update, in plasmashell's process, to learn what systemd already says.
- **systemd's `OnFailure=` and `OnSuccess=` on the `app-` units.** Costs no process while a program starts or runs, covers everything KIO starts, and the edition's engine already uses the same hook for failed system services. Misses a program started from a terminal, Steam's launch options, GLib's launcher (it makes a scope, and a scope keeps no exit status), KIO in forking mode (systemd older than 250) and `app-NAME@autostart.service` (no hexadecimal ID, and the autostart generator sends no GPU variables).

## Recipe

1. `share/systemd/user/app-.service.d/10-sparky-stereo-graphics.conf` names `OnFailure=sparky-stereo-gpu-died@%n.service` and `OnSuccess=sparky-stereo-gpu-survived@%n.service`. A drop-in directory named `app-.service.d` applies to every unit whose name starts with `app-` (systemd.unit(5), "foo-.service.d"). Use `%i` in the handlers, never `%I`: `%I` turns the `\x2d` of an escaped dash back into `-` before the handler parses the name.
2. `sparky-stereo-gpu-env --died UNIT` reads the unit over D-Bus and keeps a death only when the program was sent to a GPU by the page (the unit's `Environment` holds every line the resolver prints for its desktop entry, or KDE's own `PrefersNonDefaultGPU` key with a GPU variable), ended by a crash, a non-zero exit or another failed result within `[Launch] DiedWithin` seconds of the start (10 when unset, 0 turns the notice off), and was not killed. `--survived UNIT` ends the death of a program that ended cleanly after longer than the window.
3. The record goes to the problems engine under `died-NAME`, with the program's last journal lines and "Use NAME" for the GPUs its desktop entry can name (`--use-app ID GPU`: the desktop's GPU is `PrefersNonDefaultGPU=false`, the discrete GPU `true`, written in the person's copy of the entry as the page does). Nothing starts the program again.
4. `ConditionPathExistsGlob=%S/sparky-stereo-problems/sparky-stereo-graphics_died-*.json` on the survived handler: systemd skips it before any fork when no death is kept (`ConditionResult=no`, `ExecMainPID=0`), so a normal end of a program costs no process.

## Traps

- Symptom: a hand-over or a launcher raises a problem. Cause assumed, never true: with `ExitType=cgroup` the unit stays `active` while any process of its cgroup lives, so a launcher that forks and exits is not a failure, and an exit status of 0 is `Result=success`. Found by: starting `sh -c '(sleep 30 &); exit 1'` as a transient service and reading `ActiveState=active Result=exit-code`.
- Symptom: a person closing the program raises a problem. Cause: none, systemd counts exit by SIGTERM, SIGINT, SIGHUP and SIGPIPE as clean (`Result=success`); only SIGKILL gives `Result=signal`, which the handler leaves alone (the person's kill or the out-of-memory killer; the launch cannot tell which).
- Symptom: `systemd-run` with a `kill -s SEGV $$` test prints exit status 2 and `Result=exit-code`, not a core dump. Cause: systemd expands `$$` in `ExecStart`; write `$$$$` (KIO does the same escaping). Found by reading `ExecMainStatus=2` where 11 was expected.
- Symptom: `Unknown assignment: AddRef=yes` from `systemd-run -p`. Cause: `AddRef` exists only in the D-Bus call KIO makes. The test does without it; a failed unit stays loaded anyway, and the unit is still loaded when its `OnSuccess=` handler runs.
- Symptom: the second run of a test fails with `Unit app-x@y.service was already loaded or has a fragment file`. Cause: the first run's failed unit is kept. Run `systemctl --user reset-failed 'app-*'` first.
- Symptom: a kept record's text is the message with `%1 %2` unfilled. Cause: the engine renders from the installed journal catalog; a container that copied only the binaries has none. Build it with `sparky-stereo-problems catalog` as the recipe does, and give a new message its title in `--subject-map`.
- Symptom: the engine's record has no `details` key in a test. Cause: `actions`, `repair` and `text_en` are top-level fields of the stored record; the package's own fields are under `data`.
- Test a real systemd user manager in a container: `--cap-add SYS_ADMIN --security-opt apparmor=unconfined --cgroupns private --tmpfs /run`, command `mount -o remount,rw /sys/fs/cgroup && exec /usr/lib/systemd/systemd`, then `useradd -m -u 1000` and `loginctl enable-linger`, wait for `user@1000`. `docker cp` into a `--tmpfs /tmp` path silently copies nothing; use `/opt`. No `--privileged`, no host mount.
- Measure the window from the user journal of a real failure, not by design: `journalctl --user | grep 'app-.*service: \(Failed\|Consumed\)'`. Three real browser deaths on a hybrid workstation took 3.08, 4.41 and 5.94 seconds from start to failure, and every other failed app unit on it in two weeks (`variety`, `CoreCtrl`, Dolphin once, the Bluetooth wizard) was not sent to a GPU and raises nothing.
- Cost, four alternating rounds of 60 starts in a real user manager: about 1 ms more from the request to the program's first instruction, about 3 ms more for the whole cycle including its end, about 3 ms of manager CPU, and no process unless a program failed (the handler then runs 10 to 17 ms).
