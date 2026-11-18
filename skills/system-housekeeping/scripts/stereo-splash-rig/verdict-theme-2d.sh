#!/bin/bash
# verdict-theme-2d.sh PUBRUNS FIXRUNS: the 2D look (ORDER 715). (1) sparkyos, the 2D theme, on the published set against the successor's, on every
# capture of the batch (2D boots and every stereo layout: a theme that does not declare Stereo= gets its one picture on both
# eyes): the electrons move between runs, so at most 2 % of the pixels may differ by more than 48, as in ORDER 639.
# (2) sparkyos-stereo of the successor on a 2D boot against sparkyos of the same set: the same picture. (3) the published
# sparkyos-stereo on a 2D boot against sparkyos: the squeezed pair (red).
set -uo pipefail
here=$(dirname "$(readlink -f "$0")")
P=$(realpath "$1") F=$(realpath "$2")
fail=0 total=0 worst=0
for f in "$P"/pub-sparkyos-*-1-*.ppm; do
	f=${f##*/}
	case "$f" in pub-sparkyos-stereo-*) continue ;; esac
	g=fix-${f#pub-}
	[ -f "$F/$g" ] || continue
	total=$((total + 1))
	out=$(python3 -I "$here/measure.py" one "$P/$f" "$F/$g" "$g") || { fail=$((fail + 1)); echo "FAIL  $out"; continue; }
	p=$(echo "$out" | sed -n 's/.*: \([0-9.]*\) % of pixels.*/\1/p'); worst=$(python3 -I -c "print(max($worst, $p))")
done
echo "sparkyos (2D theme), published against successor: $((total - fail)) of $total captures equal within the electrons' phase, worst $worst % of pixels"
for s in 2d-panel-1-eDP-1 2d-tv-1-HDMI-A-1; do
	python3 -I "$here/measure.py" one "$F/fix-sparkyos-$s.ppm" "$F/fix-sparkyos-stereo-$s.ppm" "successor, 2D boot, $s: sparkyos-stereo against sparkyos" || fail=$((fail + 1))
	python3 -I "$here/measure.py" one "$P/pub-sparkyos-$s.ppm" "$P/pub-sparkyos-stereo-$s.ppm" "published, 2D boot, $s: sparkyos-stereo against sparkyos (red)" || true
done
exit $((fail > 0))
