#!/bin/bash
# tm-diag.sh: inside a rig session (APP_CMD), does a tap of one finger reach the panel? A tap on the panel's application
# launcher (a menu is a popup window of plasmashell), Escape; a tap, a click and a long touch on the button of a window
# that is not the active one, with KWin's windows after each.
set -u
LOG=$CASE/login1/session.log; OUT=$CASE/tmdiag; mkdir -p "$OUT"
win() { python3 /lane/kwin-windows-icons.py "$LOG" > "$OUT/$1.json" 2>>"$OUT/errors.txt"; }
shot() { python3 "$RIG/login-splash/shot.py" Virtual-0 "$OUT/$1.png" >> "$OUT/shots.jsonl" 2>>"$OUT/errors.txt"; }
icon() { python3 -c "
import json
for w in json.load(open('$OUT/$1.json'))['windows'] or []:
    if w['cls'] == '$2' and w['normal']:
        x, y, ww, hh = w['icon']; print('%d,%d' % (x + ww // 2, y + hh // 2)); break
"; }
dolphin "$HOME" > "$OUT/dolphin.log" 2>&1 &
sleep 6
systemsettings > "$OUT/systemsettings.log" 2>&1 &
sleep 8; win before; shot before
"$FAKEINPUT" m:960,300 s:300 t:35,1049 s:2500 > "$OUT/fi-launcher.txt" 2>&1; win launcher-tap; shot launcher-tap
"$FAKEINPUT" k:1 s:1000 >> "$OUT/fi-launcher.txt" 2>&1
at=$(icon before org.kde.dolphin)
"$FAKEINPUT" t:$at s:2500 > "$OUT/fi-tap.txt" 2>&1; win task-tap; shot task-tap
"$FAKEINPUT" t:$at s:300 t:$at s:2500 > "$OUT/fi-tap2.txt" 2>&1; win task-tap2; shot task-tap2
at2=$(icon before systemsettings)
"$FAKEINPUT" m:$at2 s:400 b:272 s:2500 > "$OUT/fi-click.txt" 2>&1; win task-click; shot task-click
"$FAKEINPUT" h:$at s:2000 > "$OUT/fi-hold.txt" 2>&1; win task-hold; shot task-hold
"$FAKEINPUT" k:1 s:800 >> "$OUT/fi-hold.txt" 2>&1
for p in $(pgrep -x systemsettings) $(pgrep -x dolphin); do kill -TERM "$p"; done
