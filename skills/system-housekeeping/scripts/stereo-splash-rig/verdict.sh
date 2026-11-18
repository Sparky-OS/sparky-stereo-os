#!/bin/bash
# verdict.sh RUNS SET [REF]: every frame check of ORDER 639 for one package set's runs (batch.sh and batch-late.sh
# with SET), against the single-screen frames of REF (the published set, "pub", by default) and the main screen's
# left eye (SET-panel-leftline when it exists, else REF's): each main screen shows what it shows alone, each screen that
# is not converted shows the main screen's left eye. Exit 0 only when every check passes.
set -uo pipefail
here=$(dirname "$(readlink -f "$0")")
cd "$1"
set=$2 ref=${3:-pub}
left=$set-panel-leftline-1-eDP-1.ppm
[ -f "$left" ] || left=new-panel-leftline-1-eDP-1.ppm
fail=0 total=0
check() { total=$((total + 1)); "$@" || fail=$((fail + 1)); }
for kind in both fw late-tv; do
	check python3 -I "$here/compare.py" $ref-panel-panelline-1-eDP-1.ppm $set-$kind-panelline-1-eDP-1.ppm "$set $kind panel main: eDP-1 (anaglyph) against the panel alone"
	check python3 -I "$here/compare.py" $ref-tv-tvline-1-HDMI-A-1.ppm $set-$kind-tvline-1-HDMI-A-1.ppm "$set $kind television main: HDMI-A-1 (frame packing) against the television alone"
	check python3 -I "$here/check-eye.py" "$left" $set-$kind-panelline-1-HDMI-A-1.ppm "$set $kind panel main: HDMI-A-1 (not named)"
	check python3 -I "$here/check-eye.py" $ref-tv-tvline-1-HDMI-A-1.ppm $set-$kind-tvline-1-eDP-1.ppm "$set $kind television main: eDP-1 (not named)"
done
echo "VERDICT $set: $((total - fail)) of $total checks pass"
[ $fail = 0 ]
