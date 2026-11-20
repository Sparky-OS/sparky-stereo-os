#!/usr/bin/python3
"""Start a Type=dbus service (geoclue.service unless --unit) COUNT times under real systemd; record each verdict.

    startloop.py LABEL COUNT [--bt-after S] [--bt-max N] [--unit NAME.service]

Each start: stop and reset the unit, `systemctl start geoclue.service` (blocking, the unit's own 90 s timeout),
then read the unit's Result and the journal of that invocation. While a start is still waiting after S seconds,
gdb takes every thread's backtrace of the unit's main process (at most N times per run); systemd's verdict is
still the one recorded. Results go to /out/LABEL/: starts.tsv, summary.txt, bt-K.txt, journal-K.txt.
"""
import argparse
import os
import subprocess
import sys
import time

UNIT = "geoclue.service"  # --unit changes it


def run(*args, check=False):
    return subprocess.run(list(args), capture_output=True, text=True, check=check)


def set_unit(name):
    global UNIT
    if not name.endswith(".service") or "/" in name:
        sys.exit("--unit must be a service unit name")
    UNIT = name


def prop(name):
    return run("systemctl", "show", "-p", name, "--value", UNIT).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("count", type=int)
    ap.add_argument("--bt-after", type=float, default=15.0)
    ap.add_argument("--bt-max", type=int, default=2)
    ap.add_argument("--unit", default=UNIT)
    a = ap.parse_args()
    set_unit(a.unit)
    if not a.label.replace("-", "").isalnum():
        sys.exit("label must be letters, digits and dashes")
    out = os.path.join("/out", a.label)
    os.makedirs(out, exist_ok=True)
    owner = os.environ.get("OWNER", "")
    glib = run("dpkg-query", "-W", "-f", "${Version}", "libglib2.0-0t64").stdout
    rows = []
    bts = 0
    with open(os.path.join(out, "starts.tsv"), "w") as tsv:
        tsv.write("n\trc\tseconds\tresult\tactive\tbt\n")
        for n in range(1, a.count + 1):
            run("systemctl", "stop", UNIT)
            run("systemctl", "reset-failed", UNIT)
            cursor = run("journalctl", "--show-cursor", "-n", "0", "-q").stdout.strip().split("cursor: ")[-1]
            t0 = time.monotonic()
            p = subprocess.Popen(["systemctl", "start", UNIT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            took_bt = ""
            while p.poll() is None:
                time.sleep(0.25)
                if not took_bt and bts < a.bt_max and time.monotonic() - t0 > a.bt_after:
                    pid = prop("MainPID")
                    if pid.isdigit() and pid != "0":
                        bts += 1
                        took_bt = f"bt-{bts}.txt"
                        with open(os.path.join(out, took_bt), "w") as f:
                            f.write(f"start {n}, pid {pid}, {time.monotonic() - t0:.1f} s after the start, GLib {glib}\n")
                            f.flush()
                            subprocess.run(["gdb", "-p", pid, "-batch", "-nx",
                                            "-ex", "set pagination off", "-ex", "set print pretty off",
                                            "-ex", "info threads", "-ex", "thread apply all bt full"],
                                           stdout=f, stderr=subprocess.STDOUT, timeout=120)
            rc = p.returncode
            dt = time.monotonic() - t0
            result = prop("Result")
            active = prop("ActiveState")
            jr = run("journalctl", "--after-cursor", cursor, "-u", UNIT, "--no-pager", "-o", "short-monotonic").stdout
            if rc != 0:
                with open(os.path.join(out, f"journal-{n}.txt"), "w") as f:
                    f.write(jr)
            rows.append((n, rc, dt, result))
            tsv.write(f"{n}\t{rc}\t{dt:.2f}\t{result}\t{active}\t{took_bt}\n")
            tsv.flush()
            print(f"{n}\trc={rc}\t{dt:.2f}s\t{result}\t{active}\t{took_bt}", flush=True)
        run("systemctl", "stop", UNIT)
    timeouts = sum(1 for r in rows if r[3] == "timeout")
    failed = sum(1 for r in rows if r[1] != 0)
    with open(os.path.join(out, "summary.txt"), "w") as f:
        f.write(f"label {a.label}\nlibglib2.0-0t64 {glib}\nstarts {len(rows)}\nfailed {failed}\ntimeout {timeouts}\n"
                f"rate {timeouts}/{len(rows)}\nok-seconds-max "
                f"{max([r[2] for r in rows if r[1] == 0] or [0]):.2f}\n")
    if owner:
        subprocess.run(["chown", "-R", owner, out])
    print(open(os.path.join(out, "summary.txt")).read())


if __name__ == "__main__":
    main()
