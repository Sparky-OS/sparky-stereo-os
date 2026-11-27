#!/bin/bash
# proof.sh: the rig rows of row 182, each in a fresh container. red: the published state (no package, KDE's Overview);
# old: the reviewed 0.1.0 build (image sm182-rig:v010); green: the staged package (image sm182-rig:green), its hook the
# autostart entry's command. Machines: a recorded one-GPU machine (the station's Cezanne alone), the A10's two AMD cards
# (recorded), the station's AMD+NVIDIA (its own sysfs read-only, the RTX through CDI), and the station with a cpuinfo
# fixture mounted over /proc/cpuinfo (SMT siblings sharing core ids with gaps, processor 5 offline).
# Env as run-case.sh: DOCKER_HOST, OUT, PKG, CONTAINER_IDS, RIGS (MACHINES optional).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
case_run() { bash "$HERE/run-case.sh" "$@"; }
verify() { python3 -I "$HERE/verify.py" "$OUT/$1" "$2" "$3" "$4" "$PKG/lang" > "$OUT/$1/verify-$4.txt" 2>&1; echo "$1: $(tail -n 1 "$OUT/$1/verify-$4.txt")"; }
green() { IMAGE=sm182-rig:green bash "$HERE/run-case.sh" "$@"; }
old() { IMAGE=sm182-rig:v010 bash "$HERE/run-case.sh" "$@"; }
# 1. red and green for each machine
for m in one-amd:/machines/one-amd-station.umockdev a10:/machines/a10.umockdev station:live; do
	name=${m%%:*}; machine=${m#*:}
	case_run "red-$name" MACHINE="$machine" HOOK=0 WAIT=8; verify "red-$name" "$name" en red
	green "green-$name" MACHINE="$machine" HOOK=1 INSTALLED=1 WAIT=8; verify "green-$name" "$name" en green
done
# 2. the strings rendered in pt_BR and German, on the recording whose page carries the notes
green green-a10-pt_BR INSTALLED=1 MACHINE=/machines/a10.umockdev HOOK=1 WAIT=8 LOGIN_LANG=pt_BR.UTF-8; verify green-a10-pt_BR a10 pt_BR green
green green-a10-de INSTALLED=1 MACHINE=/machines/a10.umockdev HOOK=1 WAIT=8 LOGIN_LANG=de_DE.UTF-8; verify green-a10-de a10 de green
# 3. the titles: every preset shown in the sidebar and measured on screen in the ten languages at Noto Sans 11 pt (a
#    fresh account from SparkyLinux's account template), and the three widest at KDE's own 10 pt; the 0.1.0 build as red
for l in en:en_US pl:pl_PL pt_BR:pt_BR fr:fr_FR de:de_DE es:es_ES ja:ja_JP ko:ko_KR zh_CN:zh_CN zh_TW:zh_TW; do
	green "titles-${l%%:*}" INSTALLED=1 MACHINE=live HOOK=1 POST_HOOK=/rig/show-all-presets.sh FONT_PT=11 WAIT=6 LOGIN_LANG="${l#*:}.UTF-8"
	verify "titles-${l%%:*}" station "${l%%:*}" green
done
for l in en:en_US de:de_DE zh_TW:zh_TW; do
	green "titles10-${l%%:*}" INSTALLED=1 MACHINE=live HOOK=1 POST_HOOK=/rig/show-all-presets.sh WAIT=6 LOGIN_LANG="${l#*:}.UTF-8"
	verify "titles10-${l%%:*}" station "${l%%:*}" green
done
# 4. the thread labels: the 0.1.0 build three times on the station (its facegrid's cells share one configuration group,
#    so which labels repeat changes from run to run; it shows when the start is slow, as under the station's load of
#    round 1, so LOAD=8 busy loops run while System Monitor starts) and on the cpuinfo fixture; the staged build under
#    the same load on both
for n in 1 2 3; do
	old "old-station-$n" INSTALLED=1 MACHINE=live HOOK=1 WAIT=8 LOAD=8; verify "old-station-$n" station en old
done
green green-station-load INSTALLED=1 MACHINE=live HOOK=1 WAIT=8 LOAD=8; verify green-station-load station en green
[ -f "$HERE/machines/cpuinfo-smt-gaps" ] || python3 -I "$HERE/make_cpuinfo_fixture.py" "$HERE/machines/cpuinfo-smt-gaps" > /dev/null
for n in 1 2; do
	old "old-smt-$n" INSTALLED=1 MACHINE=live HOOK=1 WAIT=8 LOAD=8 CPUINFO="$HERE/machines/cpuinfo-smt-gaps"; verify "old-smt-$n" station en old
done
green green-smt INSTALLED=1 MACHINE=live HOOK=1 WAIT=8 LOAD=8 CPUINFO="$HERE/machines/cpuinfo-smt-gaps"; verify green-smt station en green
# 5. the person's switch to KDE's Overview, a next login and a restart
green switch-station INSTALLED=1 MACHINE=live HOOK=1 ACT=/rig/switch.sh BETWEEN=/rig/relogin.sh WAIT=6 STARTS=2
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
# 6. a control: KDE's own History page (line charts) in the same rig, published state
case_run control-history MACHINE=live HOOK=0 WAIT=8 "APP_ARGS=--page-id history.page"
