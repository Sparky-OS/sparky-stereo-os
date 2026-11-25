#!/bin/bash
# step6-3d.sh: inside a rig session on a 3D output (kb-login.sh STEP=step6-3d.sh MODE=3d): a stereo window under the
# on-screen keyboard. Gwenview shows a marked stereo picture (PNS, left view red, right view blue, a grid of its own
# depth) over the whole screen, Kate stands small above it; both eyes are captured, then a touch on Kate's text brings
# the keyboard, which opens over the lower part of Gwenview's picture, and both eyes are captured again. Measured by
# measure-3d.py. Env: CASE, LANE, RIG, FAKEINPUT, SESSION_LOG.
set -u
python3 - "$CASE/pair.png" <<'PY'
import sys
from PIL import Image, ImageDraw
w, h = 960, 540
img = Image.new("RGB", (2 * w, h))
for eye, colour, shift in ((0, (200, 40, 40), 6), (1, (40, 60, 200), -6)):
    v = Image.new("RGB", (w, h), colour)
    d = ImageDraw.Draw(v)
    for x in range(0, w, 80):
        d.rectangle([x + shift + 10, 0, x + shift + 30, h], fill=(240, 240, 240))
    for y in range(0, h, 60):
        d.rectangle([0, y + 20, w, y + 26], fill=(20, 20, 20))
    img.paste(v, (eye * w, 0))
img.save(sys.argv[1])
PY
python3 "$RIG/mark_pns.py" "$CASE/pair.png" "$CASE/pair.pns" > "$CASE/pair-mark.txt"
gwenview "$CASE/pair.pns" > "$CASE/gwenview.log" 2>&1 &
sleep 8
python3 "$RIG/kwin_script.py" "$SESSION_LOG" 'var ws = workspace.stackingOrder; for (var i = 0; i < ws.length; i++) { var w = ws[i]; if (String(w.resourceClass) == "org.kde.gwenview") { w.setMaximize(true, true); } }'
sleep 3
: > "$CASE/typed.txt"
kate -n "$CASE/typed.txt" > "$CASE/kate.log" 2>&1 &
sleep 8
python3 "$RIG/kwin_script.py" "$SESSION_LOG" 'var ws = workspace.stackingOrder; for (var i = 0; i < ws.length; i++) { var w = ws[i]; if (String(w.resourceClass) == "org.kde.kate") { w.setMaximize(false, false); w.frameGeometry = {x: 560, y: 60, width: 800, height: 420}; } }'
sleep 3
mkfifo "$XDG_RUNTIME_DIR/fi-in" "$XDG_RUNTIME_DIR/fi-ack"
"$FAKEINPUT" --serve "$XDG_RUNTIME_DIR/fi-in" "$XDG_RUNTIME_DIR/fi-ack" > "$CASE/fakeinput.log" 2>&1 &
exec 3> "$XDG_RUNTIME_DIR/fi-in" 4< "$XDG_RUNTIME_DIR/fi-ack"
# the edition focuses the window under the pointer and raises it (focus follows the mouse): Kate is kept above, the pointer
# rests on Gwenview's upper part, and the touch on Kate's text is what activates it (as on a computer used as a tablet)
python3 "$RIG/kwin_script.py" "$SESSION_LOG" 'var ws = workspace.stackingOrder; for (var i = 0; i < ws.length; i++) { var w = ws[i]; if (String(w.resourceClass) == "org.kde.kate") { w.keepAbove = true; } }'
echo "m:200,300 s:1500" >&3; read -r a <&4
python3 "$LANE/kwin-windows.py" "$SESSION_LOG" > "$CASE/windows-before.json"
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/before.png" > "$CASE/shot-before.json"
echo "t:1900,300 s:900" >&3; read -r a <&4
echo "t:960,300 s:4000" >&3; read -r a <&4
python3 "$LANE/kwin-windows.py" "$SESSION_LOG" > "$CASE/windows-after.json"
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/after.png" > "$CASE/shot-after.json"
sleep 2
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/after2.png" > "$CASE/shot-after2.json"
exec 3>&- 4<&-
for p in $(pgrep -x gwenview) $(pgrep -x kate); do kill -TERM "$p"; done
