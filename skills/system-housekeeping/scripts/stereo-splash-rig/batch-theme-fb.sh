#!/bin/bash
# batch-theme-fb.sh OUTDIR SET THEME... : the frame-buffer renderer cases of ORDER 715 on the image run-SET.img, with a laptop's
# limits (popped 3.25, sunk 8.13), the panel main and both screens connected:
#   fbdev       the guest's own fbdev, kept 10 s past Plymouth's 8 s device timeout (VKMS's /dev/fb0, the size of the smaller screen)
#   fbkept1920  the firmware's 1920x1080 framebuffer (efifb under OVMF) kept beside the GPU's screens: larger than the eye
#   fbkept1024  the same at 1024x768: smaller than the eye
set -uo pipefail
here=$(dirname "$(readlink -f "$0")")
out=$1 set=$2; shift 2
: "${KVER:?}" "${RIGOUT:?}"
PANEL='plymouth.stereo=eDP-1:anaglyph-modern:mode=1366x768@60005:popped=3.25:sunk=8.13'
for theme in "$@"; do
	tag=$set-$theme-fbdev
	timeout 300 python3 -I "$here/run-case.py" "$out" "$tag" "$RIGOUT/run-$set.img" "$PANEL rig.screens=both rig.drm=0 rig.wait=10 rig.theme=$theme" > "$out/$tag.console" 2>&1
	for size in 1920x1080 1024x768; do
		tag=$set-$theme-fbkept${size%%x*}
		timeout 300 python3 -I "$here/run-case.py" "$out" "$tag" "$RIGOUT/run-$set.img" "$PANEL rig.screens=both rig.drm=12 rig.unbindfb=0 rig.theme=$theme" --fw=$size > "$out/$tag.console" 2>&1
	done
	echo "done $set $theme"
done
