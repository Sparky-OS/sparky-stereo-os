#!/bin/bash
# batch.sh OUTDIR SET... : the symptom-1 cases on each package set's image (run-SET.img): every screen alone (the
# reference), then the panel and the television together, with the panel-main and the television-main lines a laptop
# showed (sparky-stereo-boot 0.1.9's export).
set -uo pipefail
here=$(dirname "$(readlink -f "$0")")
out=$1; shift
: "${KVER:?}" "${RIGOUT:?}"
PANEL='plymouth.stereo=eDP-1:anaglyph-modern:mode=1366x768@60005:popped=3.25:sunk=8.13'
TV='plymouth.stereo=HDMI-A-1:frame-packing:mode=1920x1080@30000:popped=4.72:sunk=11.8'
for set in "$@"; do
	for line in panelline tvline; do
		[ $line = panelline ] && L=$PANEL || L=$TV
		for screens in panel tv both; do
			tag=$set-$screens-$line
			timeout 300 python3 -I "$here/run-case.py" "$out" "$tag" "$RIGOUT/run-$set.img" "$L rig.screens=$screens rig.drm=0 ${EXTRA:-}" \
				| grep -E '^(HDMI|eDP)|saved|said|^[A-Za-z].*(left eye|not named|cannot show|does not list)' | sed "s/^/$tag: /"
		done
	done
done
