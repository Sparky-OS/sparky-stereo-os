#!/bin/bash
# SPDX-License-Identifier: MIT
# diag-xtest.sh OUT: does xdotool (the X server's XTEST extension) reach an X window in the rig? xev is the witness.
set -u
out=$1; rm -rf "$out"; mkdir -p "$out/rt" "$out/home"; chmod 700 "$out/rt"
export XDG_RUNTIME_DIR=$out/rt HOME=$out/home KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
main() {
	mkdir -p "$HOME/.config"; [ -n "${XWAYLAND_EIS_NOPROMPT:-}" ] && printf "[Xwayland]\nXwaylandEisNoPrompt=true\n" > "$HOME/.config/kwinrc"
	kwin_wayland --virtual --xwayland --socket=w --width 1920 --height 1080 > "$out/kwin.log" 2>&1 & kp=$!
	for i in $(seq 1 160); do test -S "$XDG_RUNTIME_DIR/w" && break; sleep .25; done; sleep 1
	export WAYLAND_DISPLAY=w DISPLAY=:0
	stdbuf -oL xev -geometry 400x300+500+300 > "$out/xev.log" 2>&1 & xp=$!
	sleep 3
	xdotool getwindowfocus getwindowname > "$out/focus.txt" 2>&1
	xdotool key space f Escape > "$out/xdotool.log" 2>&1
	xdotool mousemove 600 400 click 1 >> "$out/xdotool.log" 2>&1
	sleep 1
	kill $xp $kp; wait
}
export -f main; export out
dbus-run-session -- bash -c "$(declare -f main); main"
echo "KeyPress: $(grep -c '^KeyPress' $out/xev.log)  ButtonPress: $(grep -c '^ButtonPress' $out/xev.log)  focus: $(cat $out/focus.txt)"
