#!/bin/bash
# batch-theme.sh OUTDIR SET THEME... : for each theme of the image run-SET.img, the cases of ORDER 715 at the three limits:
#   the panel alone (eDP-1, 1366x768) as the left eye, the right eye and anaglyph-modern; the television alone
#   (HDMI-A-1, the HX855's EDID) in frame packing; both screens (panel main, television not named: one eye; television main, panel
#   not named); the 2D boot (no plymouth.stereo=). Limits: D (4 and 10, the display's defaults), L (8 and 20), Z (0 and 0), and
#   R (3.25 and 8.13, the line a laptop's boot wrote). Up to 3 guests at a time.
set -uo pipefail
here=$(dirname "$(readlink -f "$0")")
out=$1 set=$2; shift 2
: "${KVER:?}" "${RIGOUT:?}"
declare -A LIM=([D]='popped=4:sunk=10' [L]='popped=8:sunk=20' [Z]='popped=0:sunk=0' [R]='popped=3.25:sunk=8.13')
jobs_file=$(mktemp)
for theme in "$@"; do
	for l in ${LIMITS:-D L Z R}; do
		lim=${LIM[$l]}
		P="eDP-1:LAYOUT:mode=1366x768@60005:$lim"
		T="HDMI-A-1:frame-packing:mode=1920x1080@30000:$lim"
		for lay in left right anaglyph-modern; do
			echo "$set-$theme-$l-panel-$lay|plymouth.stereo=${P/LAYOUT/$lay} rig.screens=panel rig.drm=0 rig.theme=$theme" >> "$jobs_file"
		done
		echo "$set-$theme-$l-tv-fp|plymouth.stereo=$T rig.screens=tv rig.drm=0 rig.theme=$theme" >> "$jobs_file"
		echo "$set-$theme-$l-both-panelmain|plymouth.stereo=${P/LAYOUT/anaglyph-modern} rig.screens=both rig.drm=0 rig.theme=$theme" >> "$jobs_file"
		echo "$set-$theme-$l-both-tvmain|plymouth.stereo=$T rig.screens=both rig.drm=0 rig.theme=$theme" >> "$jobs_file"
	done
	echo "$set-$theme-2d-panel|rig.screens=panel rig.drm=0 rig.theme=$theme" >> "$jobs_file"
	echo "$set-$theme-2d-tv|rig.screens=tv rig.drm=0 rig.theme=$theme" >> "$jobs_file"
done
export here out RIGOUT KVER set
run_one() {
	tag=${1%%|*} args=${1#*|}
	timeout 300 python3 -I "$here/run-case.py" "$out" "$tag" "$RIGOUT/run-$set.img" "$args" > "$out/$tag.console" 2>&1
	echo "done $tag"
}
export -f run_one
tr '\n' '\0' < "$jobs_file" | xargs -0 -P "${JOBS:-3}" -I{} bash -c 'run_one "$1"' _ {}
rm -f "$jobs_file"
