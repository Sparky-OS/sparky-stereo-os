#!/bin/bash
# SPDX-License-Identifier: MIT
# input_case.sh OUT PLAYER PLATFORM CASE: one input case, inside the rig container (ORDER 441). Environment: TOOLS = this folder, BIN = the folder with fakeinput, CLIP = a video that plays for a while.
# A fresh headless Stereo KWin (virtual 1920x1080, Xwayland) in a D-Bus session of its own, a fresh HOME, the player
# (PLAYER: stock = deb-multimedia's vlc, stereo = vlc-stereo) on PLATFORM (xcb or wayland), then CASE:
#   dbl    double click on the video: full screen false -> true
#   f      key F: full screen false -> true
#   esc    full screen set true through MPRIS first, then key Esc: true -> false
#   space  key space: Playing -> Paused
#   neg    a second window (xev) takes the focus, key space: VLC stays Playing and xev logs the KeyPress
# The program's own state is read back through MPRIS (PlaybackStatus, Fullscreen) before and after; the result is OUT/result.json
# and the exit status is 0 only when the state changed as expected. $INPUT_TOOL=fakeinput (default) or xdotool (X11 only).
set -u
out=$1 player=$2 platform=$3 case=$4
bin=${BIN:?} tools=${TOOLS:?}
rm -rf "$out"; mkdir -p "$out"
export HOME=$out/home LANG=C.UTF-8 LC_ALL=C.UTF-8 XDG_RUNTIME_DIR=$out/rt
mkdir -p "$HOME" "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
export QT_LOGGING_RULES="kwin_scripting.debug=true;js.debug=true;qml.debug=true"
echo "$player $platform $case ${INPUT_TOOL:-fakeinput}" > "$out/case.txt"
main() {
	mkdir -p "$HOME/.config"
	[ "${INPUT_TOOL:-fakeinput}" = xdotool ] && printf "[Xwayland]\nXwaylandEisNoPrompt=true\n" > "$HOME/.config/kwinrc"
	kwin_wayland --virtual --xwayland --socket=w --width 1920 --height 1080 ${KWIN_EXTRA:-} > "$out/kwin.log" 2>&1 & kp=$!
	for i in $(seq 1 160); do test -S "$XDG_RUNTIME_DIR/w" && break; sleep .25; done
	sleep 1
	export WAYLAND_DISPLAY=w DISPLAY=:0
	local exe=vlc-stereo; [ "$player" = stock ] && exe=vlc
	local wl=""; [ "$platform" = wayland ] && wl="WAYLAND_DEBUG=client"
	env QT_QPA_PLATFORM=$platform $wl $exe -I qt --no-qt-privacy-ask --no-audio --loop -vv --avcodec-hw=none ${VLC_EXTRA:-} "${CLIP:?}" > "$out/vlc.log" 2>&1 & vp=$!
	echo "$vp" > "$out/vlc.pid"
	sleep 6
	python3 "$tools/mpris_state.py" > "$out/state0.json" 2>> "$out/capture.log"
	python3 "$tools/kwin_windows.py" "$out/kwin.log" > "$out/win0.json" 2>> "$out/capture.log"
	local pt; pt=$(python3 - "$out/win0.json" <<'PY'
import json, sys
w = [w for w in (json.load(open(sys.argv[1]))["windows"] or []) if w["normal"] and not w["popup"]]
w.sort(key=lambda w: -w["cg"][2] * w["cg"][3])
cg = w[0]["cg"]
print("%d,%d" % (cg[0] + cg[2] // 2, cg[1] + int(cg[3] * 0.4)))
PY
)
	echo "target $pt" >> "$out/steps.log"
	[ -n "$pt" ] || { echo "rig: no window to aim at (KWin lists no normal window)" | tee -a "$out/steps.log" >&2; touch "$out/INPUT-FAILED"; }
	mkfifo "$XDG_RUNTIME_DIR/in" "$XDG_RUNTIME_DIR/ack"
	"$bin/fakeinput" --serve "$XDG_RUNTIME_DIR/in" "$XDG_RUNTIME_DIR/ack" >> "$out/steps.log" 2>&1 & fp=$!
	exec 7>"$XDG_RUNTIME_DIR/in" 8<"$XDG_RUNTIME_DIR/ack"
	inp() {
		local IFS=" " r=""
		echo "$*" >&7; read -r r <&8
		[ "$r" = ok ] || { echo "rig: input refused or fakeinput gone: $*" | tee -a "$out/steps.log" >&2; touch "$out/INPUT-FAILED"; }
	}
	inp s:300
	local tool=${INPUT_TOOL:-fakeinput}
	key() { if [ "$tool" = xdotool ]; then xdotool key "$1"; else inp "k:$2" s:2500; fi; }
	case $case in
		esc) python3 "$tools/mpris_state.py" set-fs 1 > /dev/null 2>> "$out/capture.log" ;;
		neg) stdbuf -oL xev -geometry 300x200+1400+600 > "$out/xev.log" 2>&1 & xp=$!; sleep 3
			python3 "$tools/kwin_windows.py" "$out/kwin.log" > "$out/win1.json" 2>> "$out/capture.log" ;;
	esac
	python3 "$tools/mpris_state.py" > "$out/state1.json" 2>> "$out/capture.log"
	case $case in
		dbl) inp "m:$pt" s:200
			if [ "$tool" = xdotool ]; then xdotool mousemove "${pt%,*}" "${pt#*,}" click --repeat 2 --delay 90 1; else inp d:272 s:2500; fi ;;
		f) inp "m:$pt" s:200; key f 33 ;;
		esc) inp "m:$pt" s:200; key Escape 1 ;;
		space|neg) [ "$case" = space ] && inp "m:$pt" s:200; key space 57 ;;
	esac
	sleep 1
	python3 "$tools/mpris_state.py" > "$out/state2.json" 2>> "$out/capture.log"
	python3 "$tools/kwin_windows.py" "$out/kwin.log" > "$out/win2.json" 2>> "$out/capture.log"
	[ -n "${xp:-}" ] && { kill $xp 2>/dev/null; wait $xp 2>/dev/null; }
	kill $vp 2>/dev/null; sleep 1; kill -9 $vp 2>/dev/null; wait $vp 2>/dev/null
	exec 7>&- 8<&-; wait $fp 2>/dev/null
	kill $kp 2>/dev/null; wait $kp 2>/dev/null
}
export -f main 2>/dev/null
export out player platform case bin tools
dbus-run-session -- bash -c "$(declare -f main); main"
rm -rf "$XDG_RUNTIME_DIR"
[ -e "$out/INPUT-FAILED" ] && { echo "{\"pass\": false, \"error\": \"an input step was refused\"}" > "$out/result.json"; cat "$out/result.json"; exit 3; }
python3 "$tools/input_verdict.py" "$out" "$case" > "$out/result.json"; rc=$?
cat "$out/result.json"
exit $rc
