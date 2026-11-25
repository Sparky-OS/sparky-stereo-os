#!/bin/bash
# step3-3d-moved.sh: inside a rig session on a 3D output (kb-login.sh STEP=step3-3d-moved.sh MODE=3d): a declared stereo
# window that holds a text field stands in the lower half of the screen, so the on-screen keyboard covers its field and
# KWin has to move it to keep the field in view (row 71, step 3). The window is a Qt Quick window run by Qt's qml tool:
# the stereo layer's StereoPicture (a declared 3D area) showing a marked picture (PNS: left view red, right view blue,
# white stripes 12 px apart between the eyes), a text field under it. The desktop takes a first touch, then the field;
# both eyes are captured before and after (the window at 460,480 1000x520, its field at y 926 to 986). Measured by
# measure-moved.py. Env: CASE, LANE, RIG, FAKEINPUT, SESSION_LOG.
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
cat > "$CASE/stereo-field.qml" <<'QML'
import QtQuick
import QtQuick.Controls
import org.sparky.stereo
Window {
    width: 1000
    height: 520
    visible: true
    title: "Row71 stereo field"
    color: "#202020"
    StereoPicture {
        id: pic
        anchors { left: parent.left; right: parent.right; top: parent.top; bottom: field.top; margins: 10 }
        source: Qt.resolvedUrl("pair.pns")
        onStereoActiveChanged: console.log("stereoActive", stereoActive, "stereo", stereo, "failure", stereoFailure)
    }
    TextField {
        id: field
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 10 }
        height: 60
        placeholderText: "Row 71"
        onTextChanged: console.log("text", text)
    }
    Component.onCompleted: console.log("stereoActive", pic.stereoActive, "stereo", pic.stereo, "failure", pic.stereoFailure)
}
QML
/usr/lib/qt6/bin/qml "$CASE/stereo-field.qml" > "$CASE/qml.log" 2>&1 &
sleep 8
python3 "$RIG/kwin_script.py" "$SESSION_LOG" 'var ws = workspace.stackingOrder; for (var i = 0; i < ws.length; i++) { var w = ws[i]; if (String(w.caption).indexOf("Row71 stereo field") >= 0) { w.frameGeometry = {x: 460, y: 480, width: 1000, height: 520}; } }'
sleep 3
mkfifo "$XDG_RUNTIME_DIR/fi-in" "$XDG_RUNTIME_DIR/fi-ack"
"$FAKEINPUT" --serve "$XDG_RUNTIME_DIR/fi-in" "$XDG_RUNTIME_DIR/fi-ack" > "$CASE/fakeinput.log" 2>&1 &
exec 3> "$XDG_RUNTIME_DIR/fi-in" 4< "$XDG_RUNTIME_DIR/fi-ack"
# the pointer rests on the desktop (focus follows the mouse), the desktop takes the first touch where it has no icon,
# the touch on the field activates the window, as on a computer used as a tablet. The window ends at y 1000: in tablet
# mode the hidden panel's band at the bottom (62 px in Japanese, 44 px in English) does not pass a touch to the window
# under it (KWin: "Detected a touch that never started")
echo "m:1700,150 s:1000 t:1700,150 s:1500" >&3; read -r a <&4
# a touch on the picture makes the window active with no field focused (no keyboard): the edition's depth rules draw an
# inactive window a step behind the screen, so both captures are of the active window and its pair compares
echo "t:960,700 s:2000" >&3; read -r a <&4
python3 "$LANE/kwin-windows.py" "$SESSION_LOG" > "$CASE/windows-before.json"
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/before.png" > "$CASE/shot-before.json"
echo "t:960,956 s:4000" >&3; read -r a <&4
python3 "$LANE/kwin-windows.py" "$SESSION_LOG" > "$CASE/windows-after.json"
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/after.png" > "$CASE/shot-after.json"
sleep 2
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/after2.png" > "$CASE/shot-after2.json"
exec 3>&- 4<&-
for p in $(pgrep -x qml); do kill -TERM "$p"; done
