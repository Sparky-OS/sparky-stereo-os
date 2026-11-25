#!/bin/bash
# twoscreens.sh: inside a rig session with two outputs side by side (kb-login.sh OUTPUTS=2 STEP=twoscreens.sh): which screen
# the on-screen keyboard shows on. Two Kate windows, one on each output; the desktop of the first output takes the first
# touch, then a touch on the field of the window on the second output, then one on the field of the window on the first.
# After each: KWin's window list (the keyboard window's output and frame). Env: CASE, LANE, RIG, FAKEINPUT, SESSION_LOG.
set -u
: > "$CASE/doc1.txt"; : > "$CASE/doc2.txt"
kate -n "$CASE/doc1.txt" > "$CASE/kate1.log" 2>&1 &
sleep 7
kate -n "$CASE/doc2.txt" > "$CASE/kate2.log" 2>&1 &
sleep 8
python3 "$RIG/kwin_script.py" "$SESSION_LOG" 'var ws = workspace.stackingOrder; var n = 0; for (var i = 0; i < ws.length; i++) { var w = ws[i]; if (String(w.resourceClass) == "org.kde.kate" && w.normalWindow) { if (String(w.caption).indexOf("doc2") >= 0) { w.frameGeometry = {x: 1920 + 460, y: 100, width: 1000, height: 500}; } else { w.frameGeometry = {x: 460, y: 100, width: 1000, height: 500}; } } }'
sleep 3
python3 "$LANE/kwin-windows.py" "$SESSION_LOG" > "$CASE/windows-placed.json"
mkfifo "$XDG_RUNTIME_DIR/fi-in" "$XDG_RUNTIME_DIR/fi-ack"
"$FAKEINPUT" --serve "$XDG_RUNTIME_DIR/fi-in" "$XDG_RUNTIME_DIR/fi-ack" > "$CASE/fakeinput.log" 2>&1 &
exec 3> "$XDG_RUNTIME_DIR/fi-in" 4< "$XDG_RUNTIME_DIR/fi-ack"
run() { echo "$1" >&3; read -r a <&4; echo "$1 -> $a" >> "$CASE/inputs.txt"; }
where() { # the keyboard window's output and frame, and which output each Kate is on
	python3 "$LANE/kwin-windows.py" "$SESSION_LOG" > "$CASE/windows-$1.json"
	python3 - "$CASE/windows-$1.json" "$1" <<'PY'
import json, sys
ws = json.load(open(sys.argv[1]))["windows"] or []
vis = [w for w in ws if not w.get("hidden") and not w.get("deleted")]
kb = next((w for w in vis if w.get("inputMethod") or "plasma-keyboard" in (w.get("cls") or "")), None)
active = next((w for w in vis if w.get("active")), None)
print("%s: keyboard %s on %s frame %s; active window %s on %s" % (sys.argv[2], "layer" if kb and not kb.get("inputMethod") else ("panel" if kb else "none"),
      kb and kb.get("output"), kb and kb.get("fg"), active and active.get("caption"), active and active.get("output")))
PY
}
# the edition's focus follows the mouse (delayed focus 300 ms, auto-raise): the pointer, which starts at the first screen's
# centre over the first Kate, rests where no window is, so the touches alone decide which window is active
run "m:1700,1000 s:1500"
run "t:200,900 s:1500"
run "t:2880,300 s:3000"
where second >> "$CASE/twoscreens.txt"
python3 "$RIG/login-splash/shot.py" Virtual-1 "$CASE/second-screen.png" > /dev/null
run "t:960,300 s:3000"
where first >> "$CASE/twoscreens.txt"
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/first-screen.png" > /dev/null
exec 3>&- 4<&-
for p in $(pgrep -x kate); do kill -TERM "$p"; done
cat "$CASE/twoscreens.txt"
