# Counting what a system does not read

Written from queue row 845 (2026-11-23). The claim to count: "every file a program reads is smaller, so the same work takes less processing". This page is how to turn it into a number that survives a reviewer: a count from a trace, never a timing.

## The recipe

1. **Records.** On an installed Lean Code system two kinds of record say what was shortened: `/usr/share/dpkg-stereo/lc/PACKAGE/ARCH.json` (build-time, lc1: each `files` entry has `status` `projected|unchanged|left`, `bytes` installed, `bytes_hr` authored) and `/var/lib/dpkg-stereo/records/PACKAGE.tsv` (install-time: `bytes_orig`, `bytes_lean`, `handler`). `dpkg-stereo --status` summarises the second kind only.
2. **Trace** the work inside a container of your own: `strace -f -y -qq -s 0 -e signal=none -e trace=openat,open,close,read,pread64,readv,preadv,mmap,dup,dup2,dup3 -o RUN.st COMMAND`. `-y` prints the path after every descriptor, already resolved through symlinks.
3. **Join** with `sparky-os/packages/dpkg-stereo/bin/dpkg-stereo-read-count --root / --strace RUN.st --json RUN.json` (a plain list of opened paths, as fatrace gives, is `--paths`; it has no byte counts, so every open is taken as a whole read and every row says so; `--static` prints what the disk does not hold).
4. **Two rows per open:** the open, and the bytes the program really took (read, pread, readv, an mmap's length counted apart). One open of a shortened file saves `bytes_hr - bytes` when it was read whole; a part read is a proportional estimate in its own column; an open with no read saves nothing and is counted as "opened, not read". Unattributed opens get their own rows (virtual, not owned by a package, owned but no record, stale), never dropped.
5. **Cross-check** at least a script, a program start and a compile: `dpkg-stereo --restore PACKAGES` (install-time files) and `dpkg-stereo --hr PATH` copied over the path (lc1 files), trace the same command again, and compare per path: bytes read with the authored form minus bytes read with the lean form must equal the tool's saving. Row 845: 77 paths in three workloads, every one equal.
6. **Lines** are counted from the two forms: authored from the restored file or `--hr`, lean from the lean file or from the lc1 package's own .deb (`dpkg-deb --fsys-tarfile P.deb | tar -xO ./path`).

## Traps (symptom, cause, fix, how it was found)

- **Rig installs fail on the day's snapshot.** `libkf6xmlgui6 Depends libkf6iconthemes6 (>= 6.32.0~)`: Debian testing at 2026-11-21 had KDE Frameworks 6.32, the published tree 6.30. Take the instant the tree was made against (dated-snapshot-rig.md): 20261119T023717Z for r1118a.
- **A player or the app center will not install in a rig.** `libavcodec63 Depends libaom3 (>= 1:3.15.3)`: our FFmpeg builds on deb-multimedia, which has no snapshot; Gwenview pulls it through Qt Multimedia. Fix: add deb-multimedia to the rig (not frozen: say so; install `gpgv` before `dpkg -i deb-multimedia-keyring`). `sparky-aptus-stereo-appcenter` also needs SparkyLinux's own repository.
- **The rig has no `node`.** `dpkg-stereo --status` said `check failed: no independent tokenizer (node with acorn)` for 312 files: JavaScript and QML stay whole and a count of a Qt program is too low. Install `nodejs node-acorn`, run `dpkg-stereo --project`, trace again.
- **`kwin_wayland` fails with "Operation not permitted" in a container.** It carries file capabilities (CAP_SYS_NICE) the container does not have. Copy the binary to `/usr/local/bin` (a copy loses the capability) and put that first in PATH; it says once that real-time priority failed.
- **strace never exits after a session run.** It waits for every traced descendant: `dbus-launch`'s daemon and a `kactivitymanagerd` that left its process group stay alive. Kill them by name at the end of the script (`pkill -9 -x kactivitymanage`; the name is cut at 15 letters), then the group.
- **A `docker exec` on a container whose PID 1 is `sleep` leaves zombies** (`dpkg-preconfigu`, `kioworker`, `dbus-daemon` in state Z). They cost nothing; do not read them as running work.
- **The second install of a package does nothing.** apt deletes a package's .deb from the cache after installing it (`Keep-Downloaded-Packages` off), so runs 2 and 3 of an install ran 2,800 trace lines against 15,000 for the first. Keep the .deb outside the cache and `apt-get install /path/x.deb`. Compare the line counts of the three runs before trusting them.
- **A compile that never compiled.** `pkg-config` was missing, so `g++ $(pkg-config --cflags Qt6Widgets)` failed at once (153 trace lines against 4,647). Give the include paths explicitly; read the line count of every run.
- **Anonymous mappings** (`mmap(NULL, ..., -1, 0)`) have no path: a parser that treats every unmatched `mmap` line as unparsed reports thousands of false "unparsed" lines. The tool counts truly unparsed lines and says so.
- **`<unfinished ...>` and `<... read resumed>`** lines split one call: join them per process or the read bytes are lost.
- **Descriptors open before the trace began** (232 in a session) appear in `read` lines with their path; the tool opens a row for them and counts them as "fds already open".
- **Pipes, sockets and /proc** are in the read calls too: a program's "bytes read" from netdata or strace includes them. The denominator of a share says which reads it contains; the first table of row 845 counts all of them, so it is the smallest honest share.
- **Root-owned files in your scratch folder.** A container running as root leaves them; chown from inside at the end of each run.

## What the count cannot show

- Time. Fewer bytes are not fewer milliseconds until measured on the machine that is meant to show it (the A10, by the main session).
- Compiled QML. Plasma compiles most of its QML into its libraries; the loose files a program opens are a small part.
- Page cache. A file read from the cache is still a read call; the count is of what the program took, not of what the disk delivered.
- Work the trace did not do: a program that opens a file and reads none of it counts as "opened, not read".
- Anything netdata calls "reads": it counts every read call of every process of that name, containers included, so hourly figures cannot be split into files.
