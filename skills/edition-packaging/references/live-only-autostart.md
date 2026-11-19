# A live-only autostart entry on an installed system

Symptom first: after login the session shows a failed user unit "Sparky SetXKB" at every login, on a computer that keeps `sparky-backup-core-stereo` (the live session and ISO packer tools).
`systemctl --user status 'app-sparky\x2dsetxkb@autostart.service'` says `Main process exited, code=exited, status=1/FAILURE` after printing `It is NOT Live system! Exiting now...`.
Seen on the A10 on 2026-11-19 (ORDER 758, Daniel: "that sparky set unit - should be removed uppon install").

## What a fresh installation keeps (reconcile first)

SparkyLinux's installer module removes the live tools at the end of an installation: `modules/packages/packages.conf` of calamares-sparky (folders 6 to 9; folder 4-5 removed only `sparky-backup-core`) lists `sparky-backup-*`, `live-*` and `calamares` under `remove`.
`sparky-backup-*` matches `sparky-backup-core-stereo` and `sparky-backup-desktop`, `live-*` matches live-config and live-boot's tools.
The edition's `calamares-settings-sparky-stereo` adds steps to the sequence and ships no `packages.conf` of its own, so SparkyLinux's list applies.
A machine that still has the package got it another way: installed before the list had the glob, kept by the person to pack ISOs, or pulled back by an upgrade. Read `apt-cache rdepends --installed sparky-backup-core-stereo` and `/var/log/apt/history.log` on that machine.
No package of the edition's repository depends on it (checked against the published `Packages` indexes on 2026-11-19); SparkyLinux's `sparky-backup-desktop` depends on `sparky-backup-core`, which our package satisfies by `Provides`.

Removing the packer by hand is a trap: `apt-get remove sparky-backup-core-stereo` also lists `Inst sparky-backup-core` (SparkyLinux's package) because the desktop package still needs the name. The installer's own pattern removes both and installs nothing (`apt-get -s remove 'sparky-backup-*' 'live-*' calamares`, proved with stand-ins of the real names, `evidence/` of the lane).

## The fix: a condition on the unit, not an exit 1

The package keeps the program and the entry, because a machine that packs ISOs needs them, and the entry now does nothing outside a live session.
`systemd-xdg-autostart-generator` makes `app-sparky\x2dsetxkb@autostart.service` from `/etc/xdg/autostart/sparky-setxkb.desktop` at every `daemon-reload` of the user manager.
A drop-in, `/usr/lib/systemd/user/app-sparky\x2dsetxkb@.service.d/10-live-only.conf`, sets `ConditionKernelCommandLine=boot=live` (systemd.unit(5)): a live-boot medium always starts with `boot=live` (initramfs-tools runs `scripts/live` for it; the fork's own menus write `boot=live components`), an installed system never does.
The unit is then skipped (`skipped, unmet condition check ConditionKernelCommandLine=boot=live`), not started and not failed.
The generator also understands `TryExec=`, `AutostartCondition=` (GNOME's: `if-exists` and `unless-exists` look in `$XDG_RUNTIME_DIR`, not in `/run`) and `X-KDE-autostart-condition=` (a KConfig value), none of which tests a kernel command line, hence the drop-in.
The program's own `exit 1` stays for a person who runs it by hand on an installed system, where the message is true.

## The test: red and green under a real user manager

`sparky-os/packages/sparky-backup-core-stereo/tests/setxkb-live-only.sh DEB live|installed`, as root in a container with systemd as PID 1 (`--cgroupns=private --security-opt writable-cgroups=true --tmpfs /run --tmpfs /tmp`), `libpam-systemd` and `dbus-user-session` installed.
It unpacks the package with `dpkg-deb -x` (no dependency installed), starts `user@1000.service` for a user (named `Live` for the live case, because the program looks for a user of that name in `/etc/passwd`), reloads the user manager, starts the unit, and reads `ActiveState`, `Result`, the failed units and the journal.
Measured 2026-11-19: the published 20261117 on an installed system fails (`ActiveState=failed`, `Result=exit-code`, 1 failed unit, the "NOT Live" line); 20261119 on an installed system is `inactive`, 0 failed units, "skipped, unmet condition"; 20261119 and the published one in a live session both run the program (a stand-in `setxkbmap` logs its call) with 0 failed units.

## Traps

- **A container cannot replace `/proc/cmdline`** (the OCI runtime refuses a bind mount there). systemd reads `$SYSTEMD_PROC_CMDLINE` first (systemd(1)): give it to the user manager with a drop-in for `user@.service`. The program itself still reads the real `/proc/cmdline`, so the live case checks that it ran, not which layout it chose.
- **`useradd` and `systemctl start user@1000.service` fail with "PAM unable to dlopen(pam_systemd.so)"** until `libpam-systemd` is installed; `dbus-user-session` gives the user bus.
- **`ConditionResult` reads `no` after a unit that passed its condition has finished.** Read the journal's "skipped" line, not that property.
- **A recipe that takes a fork's folder pins a commit and a fingerprint** (`SOURCE_COMMIT`, `SOURCE_TREE` in the recipe): the new drop-in is a fork commit (f69e5b3 on top of 8c23411) and both values move with it.
