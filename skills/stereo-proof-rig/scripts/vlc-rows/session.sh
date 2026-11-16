#!/bin/bash
# SPDX-License-Identifier: MIT
# one fresh session in the rig container: PipeWire with a null sink (no host sound device), Stereo KWin --virtual (Xwayland,
# stereo twins), VLC Stereo on Wayland with a film, captures at given seconds after the start of VLC, the volume control driven by
# fake input. Everything in env: OUT (empty folder), LOCALE (de_DE.UTF-8), SCALE (1 or 1.25), FILE, MODE (twin mode index for the 3D
# output, empty = 2D output), CAPS (seconds, space separated), HOVER (seconds at which the pointer goes over the volume slider), HOVER2 (the same over the speaker icon, which carries the mute tooltip),
# KEYS (seconds:evdev code, e.g. "9:103" = Up arrow at 9 s: the volume rises), TOOLS (stereo-proof-rig scripts), BIN (fakeinput).
set -u
: "${OUT:?}" "${FILE:?}"
rm -rf "$OUT"; mkdir -p "$OUT"
export HOME=$OUT/home XDG_RUNTIME_DIR=$OUT/rt LANG=${LOCALE:-C.UTF-8} LC_ALL=${LOCALE:-C.UTF-8}
export LANGUAGE=${LANG%%.*}
mkdir -p "$HOME" "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 KWIN_VIRTUAL_STEREO_MODES=1
export QT_LOGGING_RULES="kwin_scripting.debug=true;js.debug=true"
export PIPEWIRE_RUNTIME_DIR=$XDG_RUNTIME_DIR PULSE_RUNTIME_PATH=$XDG_RUNTIME_DIR/pulse
tools=${TOOLS:-/tools} bin=${BIN:-/fakeinput}
main() {
	pipewire > "$OUT/pipewire.log" 2>&1 & pw=$!
	sleep 1.5; wireplumber > "$OUT/wireplumber.log" 2>&1 & wp=$!; pipewire-pulse > "$OUT/pulse.log" 2>&1 & pp=$!; sleep 1.5
	pw-cli create-node adapter '{ factory.name=support.null-audio-sink node.name=rig-null media.class=Audio/Sink object.linger=true audio.position=[FL FR] }' > "$OUT/sink.log" 2>&1
	sleep 1; wpctl status > "$OUT/wpctl.txt" 2>&1
	kwin_wayland --virtual --xwayland --socket=w --width 1920 --height 1080 > "$OUT/kwin.log" 2>&1 & kp=$!
	for i in $(seq 1 160); do test -S "$XDG_RUNTIME_DIR/w" && break; sleep .25; done
	sleep 2
	export WAYLAND_DISPLAY=w DISPLAY=:0
	kscreen-doctor -o > "$OUT/outputs0.txt" 2>&1
	if [ -n "${KSD:-}" ]; then for a in $KSD; do kscreen-doctor "$a" >> "$OUT/ksd.log" 2>&1; sleep 1.5; done; fi
	kscreen-doctor -o > "$OUT/outputs1.txt" 2>&1
	( WAYLAND_DEBUG=client QT_QPA_PLATFORM=wayland ${GDBPFX:-} vlc-stereo -I qt --no-qt-privacy-ask -vv --avcodec-hw=none ${VLC_EXTRA:-} "$FILE" > "$OUT/vlc.log" 2>&1; echo "$(date +%s.%N) exit $?" > "$OUT/vlc.rc" ) & vp=$!
	t0=$(date +%s.%N)
	mkfifo "$XDG_RUNTIME_DIR/in" "$XDG_RUNTIME_DIR/ack"
	"$bin/fakeinput" --serve "$XDG_RUNTIME_DIR/in" "$XDG_RUNTIME_DIR/ack" >> "$OUT/steps.log" 2>&1 & fp=$!
	exec 7>"$XDG_RUNTIME_DIR/in" 8<"$XDG_RUNTIME_DIR/ack"
	inp() { local IFS=" " r=""; echo "$*" >&7; read -r r <&8; echo "$* -> $r" >> "$OUT/steps.log"; }
	# events sorted by time: cap N, hov, key CODE
	ev=""
	for c in ${CAPS:-}; do ev="$ev$c cap\n"; done
	for h in ${HOVER:-}; do ev="$ev$h hov\n"; done
	for h in ${HOVER2:-}; do ev="$ev$h hov2\n"; done
	for v in ${VOLS:-}; do ev="$ev$v vol\n"; done
	ev="${ev}${PLACEAT:-3} place\n"
	for k in ${KEYS:-}; do ev="$ev${k%%:*} key ${k#*:}\n"; done
	n=0
	printf "$ev" | sort -n | while read -r at what arg; do
		now=$(date +%s.%N); w=$(python3 -c "print(max(0,$at-($now-$t0)))"); sleep "$w"
		case $what in
			cap) n=$((n+1)); python3 "$tools/capture.py" "$OUT/cap-$at.png" > "$OUT/cap-$at.json" 2>> "$OUT/capture.log" ;;
			place) python3 "$tools/kwin_script.py" "$OUT/kwin.log" "var ws=workspace.stackingOrder; for (var i=0;i<ws.length;i++){var w=ws[i]; if (w.normalWindow && !w.popupWindow && String(w.resourceClass).indexOf('vlc')>=0) { w.frameGeometry = {x:0,y:0,width:${PLACEW:-1280},height:${PLACEH:-800}}; }}" >> "$OUT/capture.log" 2>&1 ;;
			hov2) python3 "$tools/kwin_windows.py" "$OUT/kwin.log" > "$OUT/win-$at.json" 2>> "$OUT/capture.log"
				pt=$(python3 - "$OUT/win-$at.json" <<'PY'
import json, sys
w = [w for w in (json.load(open(sys.argv[1]))["windows"] or []) if w["normal"] and not w["popup"]]
w.sort(key=lambda w: -w["cg"][2] * w["cg"][3])
cg = w[0]["cg"]
print("%d,%d" % (cg[0] + cg[2] - 118, cg[1] + cg[3] - 13))
PY
)
				echo "mute icon $pt" >> "$OUT/steps.log"
				inp "m:$pt" s:300 "m:${pt%,*},$(( ${pt#*,} - 1 ))" s:2200 ;;
			hov) python3 "$tools/kwin_windows.py" "$OUT/kwin.log" > "$OUT/win-$at.json" 2>> "$OUT/capture.log"
				pt=$(python3 - "$OUT/win-$at.json" "${SCALE:-1}" <<'PY'
import json, sys
w = [w for w in (json.load(open(sys.argv[1]))["windows"] or []) if w["normal"] and not w["popup"]]
w.sort(key=lambda w: -w["cg"][2] * w["cg"][3])
cg = w[0]["cg"]
print("%d,%d" % (cg[0] + cg[2] - 60, cg[1] + cg[3] - 20))
PY
)
				echo "slider $pt" >> "$OUT/steps.log"
				inp "m:$pt" s:300 "m:${pt%,*},$(( ${pt#*,} - 1 ))" s:2200 ;;
			vol) python3 /rig/mpris_vol.py >> "$OUT/vol.jsonl" 2>> "$OUT/capture.log" ;;
			key) inp "k:$arg" s:300 ;;
		esac
	done
	python3 "$tools/mpris_state.py" > "$OUT/state.json" 2>> "$OUT/capture.log"
	kill $vp 2>/dev/null; sleep 1; kill -9 $vp 2>/dev/null; wait $vp 2>/dev/null
	exec 7>&- 8<&-; kill $fp 2>/dev/null; kill $kp $pp $wp $pw 2>/dev/null; sleep 1
}
export -f main
export OUT FILE tools bin
dbus-run-session -- bash -c "$(declare -f main); main"
grep -E "kde_stereo_content|set_content|wl_subsurface|error|invalid" "$OUT/vlc.log" | grep -v -E "wl_subsurface#[0-9]+\.(set_position|place)" | head -60 > "$OUT/vlc-wire.txt" 2>/dev/null
gzip -f "$OUT/vlc.log"
