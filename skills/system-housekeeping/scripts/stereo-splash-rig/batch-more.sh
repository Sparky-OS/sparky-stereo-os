#!/bin/bash
# batch-more.sh OUTDIR: the 2D control (no plymouth.stereo=, both screens) on the published and the fixed image; a saved
# 3D mode the television does not list (1080p60 frame packing; the HX855 lists 1080i60, 1080p30 and 1080p24); the restart
# splash with the line of the start (panel main) and with the line saved now (television main), the television having
# been put in frame packing by the session before; the theme's own defect: the patched Plymouth with the published theme
# when the main screen comes later.
set -uo pipefail
here=$(dirname "$(readlink -f "$0")")
out=$1
: "${KVER:?}" "${RIGOUT:?}"
PANEL='plymouth.stereo=eDP-1:anaglyph-modern:mode=1366x768@60005:popped=3.25:sunk=8.13'
TV='plymouth.stereo=HDMI-A-1:frame-packing:mode=1920x1080@30000:popped=4.72:sunk=11.8'
run() { timeout 300 python3 -I "$here/run-case.py" "$out" "$1" "$RIGOUT/run-$2.img" "$3" ${4:-} | grep -aE '^(HDMI|eDP)|saved|^[A-Za-z/].*(left eye|not named|cannot show|does not list)' | sed "s/^/$1: /"; }
for set in pub fix; do
	run $set-2d-both $set "rig.screens=both rig.drm=0"
	run $set-2d-both-again $set "rig.screens=both rig.drm=0"
	run $set-tv-unlisted $set "plymouth.stereo=HDMI-A-1:frame-packing:mode=1920x1080@60000:popped=4.72:sunk=11.8 rig.screens=tv rig.drm=0"
	run $set-reboot-startline $set "$PANEL rig.screens=both rig.drm=0 rig.mode=reboot"
	run $set-reboot-savedline $set "$TV rig.screens=both rig.drm=0 rig.mode=reboot"
done
run pubply-fw-tvline pubply "$TV rig.screens=both rig.drm=12 rig.unbindfb=1" --fw
run pubply-late-tv-tvline pubply "$TV rig.screens=both rig.drm=0 rig.tvlate=5"
run fix-fw-tvline-again fix "$TV rig.screens=both rig.drm=12 rig.unbindfb=1" --fw
