#!/usr/bin/python3
"""Start a Type=dbus service (geoclue.service unless --unit) until one start hangs; run a gdb script on it.

    catchhang.py LABEL GDBSCRIPT [--max-starts N] [--wait S] [--unit NAME.service]

A start counts as hung when the unit is still activating S seconds after `systemctl start --no-block`.
gdb runs GDBSCRIPT on the unit's main process, the output goes to /out/LABEL/gdb.txt, then systemd's own
timeout is awaited and its Result is recorded. Exit 0 when a hang was caught, 1 when none in N starts.
"""
import argparse
import os
import subprocess
import sys
import time

UNIT = "geoclue.service"  # --unit changes it


def set_unit(name):
    global UNIT
    if not name.endswith(".service") or "/" in name:
        sys.exit("--unit must be a service unit name")
    UNIT = name


def prop(name):
    return subprocess.run(["systemctl", "show", "-p", name, "--value", UNIT],
                          capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("gdbscript")
    ap.add_argument("--max-starts", type=int, default=100)
    ap.add_argument("--wait", type=float, default=10.0)
    ap.add_argument("--unit", default=UNIT)
    a = ap.parse_args()
    set_unit(a.unit)
    if not a.label.replace("-", "").isalnum():
        sys.exit("label must be letters, digits and dashes")
    out = os.path.join("/out", a.label)
    os.makedirs(out, exist_ok=True)
    for n in range(1, a.max_starts + 1):
        subprocess.run(["systemctl", "stop", UNIT], capture_output=True)
        subprocess.run(["systemctl", "reset-failed", UNIT], capture_output=True)
        t0 = time.monotonic()
        subprocess.run(["systemctl", "start", "--no-block", UNIT], check=True)
        while time.monotonic() - t0 < a.wait and prop("ActiveState") != "active":
            time.sleep(0.1)
        if prop("ActiveState") == "active":
            continue
        pid = prop("MainPID")
        with open(os.path.join(out, "gdb.txt"), "w") as f:
            f.write(f"start {n}, pid {pid}, {time.monotonic() - t0:.1f} s after the start, still {prop('ActiveState')}\n")
            f.flush()
            subprocess.run(["gdb", "-p", pid, "-batch", "-nx", "-x", a.gdbscript],
                           stdout=f, stderr=subprocess.STDOUT, timeout=180)
        while prop("ActiveState") == "activating":
            time.sleep(0.5)
        with open(os.path.join(out, "verdict.txt"), "w") as f:
            f.write(f"start {n}: Result={prop('Result')} ActiveState={prop('ActiveState')} "
                    f"after {time.monotonic() - t0:.1f} s\n")
        subprocess.run(["chown", "-R", os.environ.get("OWNER", "0:0"), out])
        print(open(os.path.join(out, "verdict.txt")).read(), end="")
        return 0
    print(f"no hang in {a.max_starts} starts")
    return 1


if __name__ == "__main__":
    sys.exit(main())
