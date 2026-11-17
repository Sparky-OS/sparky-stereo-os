#!/bin/bash
# batch-late.sh OUTDIR SET... : the cases where a screen arrives after the splash was laid out, on each set's image:
# a laptop's order (two AMD GPUs, the firmware's 1024x768 framebuffer, then the GPU's driver 12 s later, after Plymouth's 8 s device
# timeout, taking the framebuffer away) with both lines, and the television connected 5 s after the panel alone.
set -uo pipefail
here=$(dirname "$(readlink -f "$0")")
out=$1; shift
: "${KVER:?}" "${RIGOUT:?}"
PANEL='plymouth.stereo=eDP-1:anaglyph-modern:mode=1366x768@60005:popped=3.25:sunk=8.13'
TV='plymouth.stereo=HDMI-A-1:frame-packing:mode=1920x1080@30000:popped=4.72:sunk=11.8'
for set in "$@"; do
	for line in panelline tvline; do
		[ $line = panelline ] && L=$PANEL || L=$TV
		tag=$set-fw-$line
		timeout 300 python3 -I "$here/run-case.py" "$out" "$tag" "$RIGOUT/run-$set.img" "$L rig.screens=both rig.drm=12 rig.unbindfb=1" --fw \
			| grep -aE '^(HDMI|eDP)|saved|^[A-Za-z/].*(left eye|not named|cannot show|does not list)' | sed "s/^/$tag: /"
		tag=$set-late-tv-$line
		timeout 300 python3 -I "$here/run-case.py" "$out" "$tag" "$RIGOUT/run-$set.img" "$L rig.screens=both rig.drm=0 rig.tvlate=5" \
			| grep -aE '^(HDMI|eDP)|saved|^[A-Za-z/].*(left eye|not named|cannot show|does not list)' | sed "s/^/$tag: /"
	done
done
