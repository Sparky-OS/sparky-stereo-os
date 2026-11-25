#!/bin/bash
# retouch.sh: inside a rig session (kb-login.sh STEP=retouch.sh): a text field that has the focus from the pointer (focus
# follows the mouse) is then touched. KWin's own keyboard shows again on such a touch; a keyboard that is not KWin's input
# method hears nothing of it (no activeChanged, no focus change). Env: CASE, LANE, RIG, FAKEINPUT, SESSION_LOG.
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
run "m:$cg s:400 b:272 s:2500"
echo "keyboard after the click: $(kb)" >> "$CASE/retouch.txt"
run "t:$cg s:3000"
echo "keyboard after a touch on the same field: $(kb)" >> "$CASE/retouch.txt"
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/after-retouch.png" > /dev/null
exec 3>&- 4<&-
for p in $(pgrep -x kate); do kill -TERM "$p"; done
cat "$CASE/retouch.txt"
