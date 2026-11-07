#!/bin/bash
# SPDX-License-Identifier: MIT
# test-fakeinput.sh OUT: inside the rig. fakeinput must refuse a malformed step (the comma-joined line that ORDER 265's rig sent) and run
# a well-formed one; red on the old tool (it answered ok and ran only the first step), green on the strict one.
set -u
out=$1; rm -rf "$out"; mkdir -p "$out/rt"; chmod 700 "$out/rt"
export XDG_RUNTIME_DIR=$out/rt HOME=$out/home KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
mkdir -p "$HOME"
main() {
	kwin_wayland --virtual --socket=w --width 800 --height 600 > "$out/kwin.log" 2>&1 & kp=$!
	for i in $(seq 1 160); do test -S "$XDG_RUNTIME_DIR/w" && break; sleep .25; done
	export WAYLAND_DISPLAY=w
	mkfifo "$XDG_RUNTIME_DIR/in" "$XDG_RUNTIME_DIR/ack"
	"${FAKEINPUT:-$BIN/fakeinput}" --serve "$XDG_RUNTIME_DIR/in" "$XDG_RUNTIME_DIR/ack" > "$out/fi.log" 2>&1 & fp=$!
	exec 7>"$XDG_RUNTIME_DIR/in" 8<"$XDG_RUNTIME_DIR/ack"
	fails=0
	check() { # LINE EXPECTED
		echo "$1" >&7; read -r r <&8
		if [ "$r" = "$2" ]; then echo "ok   [$1] -> $r"; else echo "FAIL [$1] -> $r, expected $2"; fails=$((fails+1)); fi
	}
	check "m:100,100 s:10" ok
	check "m:100,100,s:10" error
	check "m:100 s:10" error
	check "k:57" ok
	check "k:57+x" error
	check "k:" error
	check "b:272x" error
	check "s:1o" error
	check "z:1" error
	exec 7>&- 8<&-; wait $fp 2>/dev/null; kill $kp 2>/dev/null; wait $kp 2>/dev/null
	return $fails
}
export -f main; export out BIN
dbus-run-session -- bash -c "$(declare -f main); main"
