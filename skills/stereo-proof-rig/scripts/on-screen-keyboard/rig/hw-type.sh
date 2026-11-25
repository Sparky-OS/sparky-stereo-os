#!/bin/bash
# hw-type.sh: inside a rig session (kb-login.sh STEP=hw-type.sh) in a Japanese session: a hardware keyboard types through
# Fcitx 5 as before. Kate opens a file; a mouse click gives its text the focus (no on-screen keyboard: the last input is the
# mouse); Ctrl+Space turns Mozc on (Fcitx 5's trigger key); "nihongo", Space and Enter come from KWin's fake keyboard
# (evdev keys); the file is read back. Then the same after the on-screen keyboard was shown by a touch: the first physical
# key leaves Fcitx 5's keyboard mode and the on-screen keyboard hides. Env: CASE, LANE, RIG, FAKEINPUT, SESSION_LOG.
set -u
: > "$CASE/typed.txt"
kate -n "$CASE/typed.txt" > "$CASE/kate.log" 2>&1 &
sleep 9
cg=$(python3 "$LANE/kwin-windows.py" "$SESSION_LOG" | python3 -c "
import json, sys
for w in json.load(sys.stdin)['windows']:
    if w['cls'] == 'org.kde.kate' and w['normal']:
        x, y, ww, hh = w['cg']; print('%d,%d' % (x + ww // 2, y + hh // 3)); break")
mkfifo "$XDG_RUNTIME_DIR/fi-in" "$XDG_RUNTIME_DIR/fi-ack"
"$FAKEINPUT" --serve "$XDG_RUNTIME_DIR/fi-in" "$XDG_RUNTIME_DIR/fi-ack" > "$CASE/fakeinput.log" 2>&1 &
exec 3> "$XDG_RUNTIME_DIR/fi-in" 4< "$XDG_RUNTIME_DIR/fi-ack"
run() { echo "$1" >&3; read -r a <&4; echo "$1 -> $a" >> "$CASE/inputs.txt"; }
kb() { python3 "$LANE/kwin-windows.py" "$SESSION_LOG" | python3 -c "
import json, sys
ws = json.load(sys.stdin)['windows'] or []
# as type-case.py's keyboard_window: Plasma Keyboard for Fcitx 5 is a layer; KWin's input panel holds KWin's own keyboard
# or Fcitx 5's candidate popup
vis = [w for w in ws if not w.get('hidden') and not w.get('deleted')]
print('layer' if any('plasma-keyboard' in (w.get('cls') or '') or 'plasma.keyboard' in (w.get('cls') or '') for w in vis)
      else 'panel' if any(w.get('inputMethod') for w in vis) else 'no')"; }
# 1. the mouse and the hardware keyboard only
run "m:$cg s:400 b:272 s:2000"
echo "keyboard after the click: $(kb)" >> "$CASE/hw.txt"
run "k:29+57 s:800"
for k in 49 23 35 24 49 34 24; do run "k:$k s:150"; done
run "k:57 s:800"
run "k:28 s:1500"
sleep 3
cp "$CASE/typed.txt" "$CASE/typed-hardware.txt"
echo "typed with the hardware keyboard: $(cat "$CASE/typed-hardware.txt" | head -c 200)" >> "$CASE/hw.txt"
# 2. a touch shows the on-screen keyboard; the first physical key hides it
run "t:1900,30 s:800"
run "t:$cg s:3000"
echo "keyboard after the touch: $(kb)" >> "$CASE/hw.txt"
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/after-touch.png" > /dev/null
run "k:49 s:1500"
echo "keyboard after a physical key: $(kb)" >> "$CASE/hw.txt"
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/after-key.png" > /dev/null
exec 3>&- 4<&-
for p in $(pgrep -x kate); do kill -TERM "$p"; done
cat "$CASE/hw.txt"
