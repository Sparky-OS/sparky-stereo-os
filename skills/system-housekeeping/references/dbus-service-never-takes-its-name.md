# A D-Bus service that never takes its name

A core limit of exactly 1 suppresses the piped core helper; a zero limit does not, as the [crash trap](../../stereo-proof-rig/SKILL.md#traps-that-fooled-us) explains.
The kernel control supports this core-limit correction; the systemd startup variant with `DefaultLimitCORE=1:1` has not been rerun.

**For whoever meets a `Type=dbus` unit that times out at start:** tell a hang from a crash, take every thread's backtrace with symbols, name the thread that holds the lock, and prove the fix with a start loop.
Written 2026-11-19 from ORDER 768: geoclue 2.8.2 on GLib 2.90.1, Debian testing.

## Symptom

- `systemctl start geoclue.service` waits 90 s, then `geoclue.service: start operation timed out. Terminating.` and `Failed with result 'timeout'`.
- A program that asked over D-Bus (the browser asking for the location) waits 25 s: `Failed to activate service 'org.freedesktop.GeoClue2': timed out (service_start_timeout=25000ms)`.
- `busctl --system monitor` shows the process connect and say `Hello`, and never `RequestName`.
- It does not happen every time: a start by hand can reach `g_main_loop_run()` and work.

## Hang, crash or early exit

| What the journal and systemd show | What it is |
| --- | --- |
| `start operation timed out`, and during the 90 s `systemctl show -p ActiveState,MainPID` says `activating` with a live PID | a hang: the process is alive and waits |
| `Main process exited, code=dumped` or `code=killed, status=11/SEGV` | a crash |
| `Main process exited, code=exited, status=N` before the timeout | an early exit: the daemon left before taking its name (thermald on an AMD CPU) |
| `status=217/USER` or `226/NAMESPACE` at once | systemd could not set up the unit's sandbox (in a container: see the rig below) |

A hang whose threads all sit in `futex` or `syscall` waits, with no system call in progress, is a lock or a GOnce: read the stacks, not `strace`.

## Every thread's backtrace, with symbols

1. Debian's debug symbols live in the debug archive: `Types: deb`, `URIs: https://deb.debian.org/debian-debug`, `Suites: testing-debug`, `Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp`; then install `libglib2.0-0t64-dbgsym`, `geoclue-2.0-dbgsym`, `glib-networking-dbgsym`, `libproxy1v5-dbgsym` (the libraries on the path), at the exact versions installed.
2. While the start still waits (`ActiveState=activating`): `gdb -p PID -batch -nx -ex 'set pagination off' -ex 'info threads' -ex 'thread apply all bt full'`.
   Do it as root; a process of another user needs `CAP_SYS_PTRACE` (in a container, `--cap-add SYS_PTRACE`).
3. Without the symbols, frames are named after the nearest exported function and lie: the first read of this hang named `g_vfs_get_default()` for four pool threads, and with symbols three of them waited in `g_proxy_resolver_get_default()`.

## Name the thread that holds the lock

GLib's `GRecMutex` wraps a pthread mutex, and its owner is written in it.
In the frame that waits (here `_g_io_module_get_default`, whose static `default_modules_lock` it is):

```
frame function _g_io_module_get_default
print *(pthread_mutex_t *) default_modules_lock.p
print ((pthread_mutex_t *) default_modules_lock.p)->__data.__owner
```

`__owner` is the kernel thread id: match it with the `LWP` column of `info threads`; `__count` is how many times that thread holds it.
A GOnce records no owner, but `print 'gthread.c'::g_once_init_list` lists every location being initialised right now; the holder is the thread whose stack is inside that function past its `g_once_init_enter()`.
The script used here is [`lockowner.gdb`](../scripts/dbus-service-hang/lockowner.gdb), run with `gdb -p PID -batch -nx -x lockowner.gdb`; [`catchhang.py`](../scripts/dbus-service-hang/catchhang.py) starts the unit until a start hangs and runs it on that process.

## The cause found here (GLib 2.89.2 to 2.90.1)

geoclue builds its sources in `on_bus_acquired()`, before it asks for its name.

- The web source's `constructed()` calls `g_network_monitor_can_reach_async()` (src/gclue-web-source.c:496).
- Since GLib's commit e73abdb8 (merge request 5222), `GNetworkMonitorNetlink`, which `GNetworkMonitorNM` extends, runs that check in a pool thread (`can_reach_thread`, gio/gnetworkmonitornetlink.c:925).
- The first proxy enumerator built there constructs the default `GProxyResolver` inside `_g_io_module_get_default()`, with `default_modules_lock` held (gio/giomodule.c:968).
- For a system service that resolver is glib-networking's `GLibproxyResolver`, and libproxy 0.5's config-sysconfig plugin calls `g_file_new_for_path()` (config-sysconfig.c:86): the pool thread now needs the GOnce of `g_vfs_get_default()` (gio/gvfs.c:355).
- Meanwhile the main thread reaches the static source's `check_monitor()` (src/gclue-static-source.c:431), calls `g_file_new_for_path()`, wins that GOnce and waits for `default_modules_lock`.

Each waits for the other; the name is never requested; systemd's 90 s run out.
Measured in the rig: the `__owner` field of `default_modules_lock` named the pool thread whose stack is inside the resolver's construction, and `g_once_init_list` held exactly `vfs_default_singleton` and `proxy_resolver_default_singleton`.

The fix is GLib's: Thomas Hebb's commit builds the enumerator on the calling thread and keeps only the resolution asynchronous (main afa628df, glib-2-90 4301b496; GLib issue 4078, geoclue issue 226).
On 2026-11-19 it was on the glib-2-90 branch and in no tagged release; Debian's 2.90.1-2 did not carry it.

## The proof: a start loop and a reproducer

- **The start loop** ([`startloop.py`](../scripts/dbus-service-hang/startloop.py), `--unit NAME.service`): stop, `reset-failed`, `systemctl start` (blocking, the unit's own timeout), read `Result`; repeat; it writes `/out/LABEL/starts.tsv` and `summary.txt`, and takes every thread's backtrace of a start still waiting after 15 s.
  Count systemd's `timeout` verdicts, never a script's own wait. On Debian's GLib 2.90.1-2, 20 starts gave 2 timeouts and 200 starts gave 28 (14 %); with upstream's commit carried on the same source, 200 starts gave none.
- **A race needs a number of starts:** at about one in ten (10 to 14 % here), 50 starts show none about once in 200 runs, 20 starts once in eight; use 200 for a red and green pair, run back to back on an idle machine.
- **The reproducer** ([`reproducer/`](../scripts/dbus-service-hang/reproducer/repro.c), build lines in each file's header): a GIO proxy-resolver module whose construction pauses and then makes a `GFile`, and a program that calls `g_network_monitor_can_reach_async()` and then `g_file_new_for_path()` on its main thread.
  With `GIO_EXTRA_MODULES=DIR GIO_USE_PROXY_RESOLVER=g768-slow GIO_USE_NETWORK_MONITOR=netlink` under `timeout 20`, Debian's 2.90.1-2 hung in 10 runs of 10 and the fixed build finished all 10 in 0.6 s.

## A real-systemd rig for a sandboxed unit

The base recipe is in [lessons](lessons-2026-11.md) (ORDER 460, 463).
A unit with `User=`, `ProtectSystem=strict` and `PrivateTmp=` needs more, and each step below was met in this order:

- `Failed to keep CAP_SYS_ADMIN: Operation not permitted`, then `status=217/USER`: systemd needs `CAP_SYS_ADMIN` to set up the sandbox before it drops to the user. Add `--cap-add SYS_ADMIN`.
- With `CAP_SYS_ADMIN`, systemd as PID 1 stops at once with `Failed to set RLIMIT_CORE: Operation not permitted` under the former `--ulimit core=0`. Add `--cap-add SYS_RESOURCE` and give PID 1 `DefaultLimitCORE=1:1` (a file in `/etc/systemd/system.conf.d`), and start with `--ulimit core=1`, so each unit uses soft and hard limits of 1; check `/proc/PID/limits` of the service.
- `Failed to remount root directory as MS_SLAVE: Permission denied`, `Failed to start up manager`: AppArmor's docker-default profile refuses systemd's mounts. Add `--security-opt apparmor=unconfined`.
- systemd as PID 1 prints nothing in `docker logs` without a terminal: add `-t` to read why it stopped.
- `ModemManager.service ... skipped, unmet condition check ConditionVirtualization=!container`: run its binary as a transient unit (`systemd-run --unit=NAME /usr/sbin/ModemManager`) when the service under test watches its bus name.
- `--network none` keeps the rig off every network; geoclue's web source calls `can_reach` whether or not a network is up, so the race needs no network.

## Traps

- **`GIO_USE_VFS=local` does not avoid it.** Every extension point (VFS, proxy resolver, settings backend, network monitor) shares one `default_modules_lock`; choosing the local VFS still goes through it. The same holds for `GSETTINGS_BACKEND=memory`: the path goes through libproxy's config-sysconfig, not dconf.
- **One good start proves nothing.** A run by hand reached the main loop while the service hung three times in three: count starts.
- **A timeout raised, a restart loop or a masked unit hides it** and keeps the person's program waiting; the fix is in the library.
