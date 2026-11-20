# A queued job that fails must not loop or hold the boot

Symptom first: after an update the boot takes a minute more, `systemd-analyze` puts the graphical target at 1 min 32 s against 33 s the boot before, and `systemctl --failed` lists a `.path` unit and its `.service` with `Result=start-limit-hit` ("Start request repeated too quickly").
Seen on the A10 on 2026-11-19 with `sparky-stereo-language-tasks` (ORDER 756): its migration failed, its path unit started it again, and `multi-user.target` waited for each run.

## Cause

Three things together, each ordinary:

1. **The service was `WantedBy=multi-user.target`.** A target is ordered after the units it wants, so a oneshot that runs apt for a minute holds the target for that minute.
2. **The path unit used `PathExists=` on the queue file.** `PathExists=` fires again as long as the file exists, so a run that fails and leaves the queue starts again. `StartLimitIntervalSec=infinity` with `StartLimitBurst=1` turned the second start into a failure of the service and of the path unit, which is worse than a quiet wait: two failed units at every boot, and the engine's generic "service failed" record beside the real one.
3. **The failure said the wrong thing.** The message was the same for every failure ("Check the network and retry the update") although apt had refused to remove a package.

## The measured red (real systemd as PID 1 in a container)

`docker run -d --cgroupns=private --security-opt writable-cgroups=true --tmpfs /run --tmpfs /tmp IMAGE /lib/systemd/systemd`, the machine's state reproduced, the published package installed, then `docker restart` with the queue still pending.
Read `systemctl show multi-user.target -p ActiveEnterTimestampMonotonic` and the service's `InactiveExitTimestampMonotonic` and `InactiveEnterTimestampMonotonic`, all against `UserspaceTimestampMonotonic` (a monotonic clock of the host in a container).
Published 1.0.8: the service ran from 0.5 s to 20.8 s and multi-user.target was reached at 20.9 s (a second measure on a busier machine: 0.8 s to 33.7 s and 33.8 s); the service was started twice in the boot and both units ended failed (`start-limit-hit`).

## The fix

- **No `[Install]` on the service.** It is started by the path unit, by a timer and by the package's own retry command, never by the target. The package's postinst removes the old `multi-user.target.wants` link of an earlier version.
- **`PathChanged=` on the queue file** reacts to a new queue (the program writes it by renaming a temporary file over it, which is an inotify move-in), not to its existence. A run that fails leaves the queue, and nothing starts it again.
- **A timer, `OnStartupSec=30s`,** starts the service once after the manager starts. `ConditionPathExists=` on the queue file in the service makes it a quiet no-op when nothing is queued (the unit is skipped, not failed).
- **`Wants=network-online.target` with `After=`.** A service started by a path unit early in the boot would otherwise run before the network is up; the `Wants=` pulls the target in for this job and nothing else waits for it.
- **A new request is the next package transaction.** The dpkg post-invoke hook runs `languages retry`, which resets the failed state of the three units and starts the service again.
- **No start limit of our own.** Every start is now caused by an edge (a change of the queue, the timer, the hook), so a limit would only make the next request fail after a success.
- **The message names the cause.** The program classifies a failure: packages apt would remove (named), a fetch that failed (the network message), anything else (apt's own error lines).

Measured after the fix, same rig and a blocker that apt must not remove (a stand-in package that needs tasksel 3.91 exactly): the install's run fails once with the message that names the blocker; after `docker restart` multi-user.target is reached at 0.2 to 1.0 s (three boots), the timer starts the service once 30 s later, it fails once again, `NRestarts=0`, the path and timer units stay active, and nothing starts it a third time; removing the blocker makes the next dpkg run (the post-invoke hook) finish the migration by itself. The only failed unit left is the service itself, with its record in the problems engine, which is the honest state of a migration that could not be done.

## Traps

- **`ConditionPathExists=!/run/.../blocked` on the service with `PathExists=` on the path unit is not a fix.** The skipped start is not a state change, the path unit starts it again at once, and the path unit fails with `Result=trigger-limit-hit` (200 triggers in 2 s). Found by `systemctl show PATH.path -p Result` after the first green run.
- **`systemd-analyze critical-chain` shows the target's chain, not the wait of a oneshot it wants.** Compare the target's `ActiveEnterTimestampMonotonic` with the service's start and end times, as above, and take the journal's "Starting" lines of the boot with `-b`: in a container `-b` is the host's boot, so count from a timestamp instead.
- **`systemctl is-system-running` says `degraded` for any failed unit,** including a leftover of an earlier boot's `reset-failed` that never happened.
- **A container image keeps `/etc/default/locale` only until systemd starts:** Debian's tmpfiles rule recreates it as a link to `/etc/locale.conf`. Write the locale to `/etc/locale.conf` after the boot when a case depends on the system language.
