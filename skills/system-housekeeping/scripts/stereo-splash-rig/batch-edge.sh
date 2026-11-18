#!/bin/bash
# batch-edge.sh OUTDIR SET...: the cases of the review's change (a screen larger than the eye continues the eye's edge):
# batch.sh and batch-late.sh, the panel alone named "left" (the main eye's reference), and both screens with the panel
# main kept 10 s, past Plymouth's device timeout, so the guest's own fbdev is a frame-buffer display larger than the eye
# (its /dev/fb0 is saved).
set -uo pipefail
here=$(dirname "$(readlink -f "$0")")
out=$1; shift
: "${KVER:?}" "${RIGOUT:?}"
PANEL='plymouth.stereo=eDP-1:anaglyph-modern:mode=1366x768@60005:popped=3.25:sunk=8.13'
for set in "$@"; do
	bash "$here/batch.sh" "$out" "$set"
	bash "$here/batch-late.sh" "$out" "$set"
	timeout 300 python3 -I "$here/run-case.py" "$out" "$set-panel-leftline" "$RIGOUT/run-$set.img" \
		'plymouth.stereo=eDP-1:left:mode=1366x768@60005:popped=3.25:sunk=8.13 rig.screens=panel rig.drm=0' > /dev/null
	timeout 300 python3 -I "$here/run-case.py" "$out" "$set-fbdev-panelline" "$RIGOUT/run-$set.img" "$PANEL rig.screens=both rig.drm=0 rig.wait=10" \
		| grep -aE '^(HDMI|eDP)|left eye' | sed "s/^/$set-fbdev-panelline: /"
done
