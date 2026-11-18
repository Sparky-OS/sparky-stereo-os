#!/bin/bash
# verdict-theme-fb.sh RUNS SET THEME: the frame-buffer renderer cases (batch-theme-fb.sh) against the main screen's left eye at the
# bench laptop's limits (R): each frame-buffer display must hold that eye and nothing of the other, the eye's own edge continued
# where the display is larger, the eye's middle where it is smaller. Exit 0 only when every case passes.
set -uo pipefail
here=$(dirname "$(readlink -f "$0")")
cd "$1"; set=$2 theme=$3
eye=$set-$theme-R-panel-left-1-eDP-1.ppm
fail=0 total=0
check() { total=$((total + 1)); "$@" || fail=$((fail + 1)); }
python3 -I "$here/fb0-png.py" $set-$theme-fbdev-fb0.info $set-$theme-fbdev-fb0.raw $set-$theme-fbdev-fb0.ppm > /dev/null
check python3 -I "$here/check-eye.py" "$eye" $set-$theme-fbdev-fb0.ppm "$set $theme: frame-buffer renderer on the guest's fbdev (1366x768 visible)"
for size in 1920 1024; do
	python3 -I -c "from PIL import Image; Image.open('$set-$theme-fbkept$size-fbend.png').convert('RGB').save('$set-$theme-fbkept$size-fbend.ppm')"
	check python3 -I "$here/check-eye.py" "$eye" $set-$theme-fbkept$size-fbend.ppm "$set $theme: frame-buffer renderer on the firmware framebuffer kept, ${size} wide"
done
echo "VERDICT frame-buffer $set $theme: $((total - fail)) of $total checks pass"
[ $fail = 0 ]
