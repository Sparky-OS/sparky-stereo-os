#!/bin/bash
# proof.sh: the rig rows of row 182, each in a fresh container: red (the published state, no hook: KDE's Overview) and
# green (the login hook, then System Monitor) for a recorded one-GPU machine (the station's Cezanne alone), the A10's two
# AMD cards (recorded) and the station's AMD+NVIDIA (its own sysfs read-only, the RTX through CDI); the A10 recording
# again in pt_BR and German; the person's switch to KDE's Overview, a next login and a restart on AMD+NVIDIA.
# Env as run-case.sh: DOCKER_HOST, OUT, PKG, CONTAINER_IDS, RIGS.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
case_run() { bash "$HERE/run-case.sh" "$@"; }
verify() { python3 -I "$HERE/verify.py" "$OUT/$1" "$2" "$3" "$4" "$PKG/lang" > "$OUT/$1/verify-$4.txt" 2>&1; echo "$1: $(tail -1 "$OUT/$1/verify-$4.txt")"; }
for m in one-amd:/machines/one-amd-station.umockdev a10:/machines/a10.umockdev station:live; do
	name=${m%%:*}; machine=${m#*:}
	case_run "red-$name" MACHINE="$machine" HOOK=0 WAIT=8; verify "red-$name" "$name" en red
	IMAGE=sm182-rig:green case_run "green-$name" MACHINE="$machine" HOOK=1 INSTALLED=1 WAIT=8; verify "green-$name" "$name" en green
done
IMAGE=sm182-rig:green case_run green-a10-pt_BR INSTALLED=1 MACHINE=/machines/a10.umockdev HOOK=1 WAIT=8 LOGIN_LANG=pt_BR.UTF-8; verify green-a10-pt_BR a10 pt_BR green
IMAGE=sm182-rig:green case_run green-a10-de INSTALLED=1 MACHINE=/machines/a10.umockdev HOOK=1 WAIT=8 LOGIN_LANG=de_DE.UTF-8; verify green-a10-de a10 de green
IMAGE=sm182-rig:green case_run switch-station INSTALLED=1 MACHINE=live HOOK=1 ACT=/rig/switch.sh BETWEEN=/rig/relogin.sh WAIT=6 STARTS=2
python3 -I - "$OUT/switch-station" <<'PY' | tee "$OUT/switch-station/verify-switch.txt"
import json, sys
case = sys.argv[1]
rc1 = open(case + "/start1/systemmonitorrc").read()
frames = [o["name"] for o in json.load(open(case + "/start2/atspi.json"))["objects"] if o.get("role") == "frame"]
checks = [("the person's start page is KDE's (no startPage key: KConfig's default overview.page)", "startPage=" not in rc1),
          ("the computer's preset hidden by the person", "hiddenPages=sparky-overview-every-gpu-many-threads.page" in rc1),
          ("the next login's hook ran and left the person's choice byte for byte",
           "relogin hook exit 0" in open(case + "/start1/between.log").read()
           and open(case + "/after-relogin.rc", "rb").read() == open(case + "/start1/systemmonitorrc", "rb").read()),
          ("the restart opens KDE's Overview", frames == ["Overview"])]
for what, ok in checks:
    print("PASS" if ok else "FAIL", what)
print("switch-station: %d checks, %d failed" % (len(checks), sum(1 for _, ok in checks if not ok)))
PY
# a control: KDE's own History page (line charts) in the same rig, published state
case_run control-history MACHINE=live HOOK=0 WAIT=8 "APP_ARGS=--page-id history.page"
