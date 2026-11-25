#!/bin/bash
# touch-measure.sh MODE: inside a rig session (welcome-login.sh's APP_CMD), what a mouse click and a tap of one finger
# do in the desktop's Folder View, in Dolphin and in the task manager, read from KWin's own window list after each.
# The account has ~/Desktop/TouchTest/Inner (USER_SETUP) and the click setting of the case (kdeglobals [KDE] SingleClick,
# or nothing for KDE's default). MODE calibrate: Dolphin opened on TouchTest, the desktop and the window captured (to
# read ICON_AT and ITEM_AT from the pictures); MODE run: the rows.
# Env: CASE, RIG, FAKEINPUT, ICON_AT (x,y of the TouchTest icon on the desktop), ITEM_AT (x,y of the Inner item,
# relative to Dolphin's client area).
set -u
LOG=$CASE/login1/session.log; OUT=$CASE/touch; mkdir -p "$OUT"
win() { python3 /lane/kwin-windows-icons.py "$LOG" > "$OUT/$1.json" 2>>"$OUT/errors.txt"; }
shot() { python3 "$RIG/login-splash/shot.py" Virtual-0 "$OUT/$1.png" >> "$OUT/shots.jsonl" 2>>"$OUT/errors.txt"; }
mark() { echo "$1 $(date +%s.%N)" >> "$OUT/marks.txt"; }
close_dolphin() { for p in $(pgrep -x dolphin); do kill -TERM "$p"; done; sleep 2; }
client() { # client geometry of the first window of class $2 in snapshot $1: x y w h
	python3 -c "
import json, sys
for w in json.load(open('$OUT/$1.json'))['windows'] or []:
    if w['cls'] == '$2' and w['normal']:
        print(*w['cg']); break
"; }
icon() { # centre of the task button of the first window of class $2 in snapshot $1
	python3 -c "
import json
for w in json.load(open('$OUT/$1.json'))['windows'] or []:
    if w['cls'] == '$2' and w['normal']:
        x, y, ww, hh = w['icon']; print('%d,%d' % (x + ww // 2, y + hh // 2)); break
"; }
if [ "$1" = calibrate ]; then
	shot desktop; win desktop
	dolphin "$HOME/Desktop/TouchTest" > "$OUT/dolphin.log" 2>&1 &
	sleep 8; win dolphin; shot dolphin
	exit 0
fi
# 1, 2: the desktop's Folder View, the TouchTest icon
mark folder-click; "$FAKEINPUT" m:${ICON_AT} s:500 b:272 s:3500 > "$OUT/fi-folder-click.txt" 2>&1; win folder-click; shot folder-click; close_dolphin
mark folder-tap; "$FAKEINPUT" m:5,5 s:300 t:${ICON_AT} s:3500 > "$OUT/fi-folder-tap.txt" 2>&1; win folder-tap; shot folder-tap; close_dolphin
# 3, 4: Dolphin, the Inner item of TouchTest
for how in click tap; do
	dolphin "$HOME/Desktop/TouchTest" > "$OUT/dolphin-$how.log" 2>&1 &
	sleep 7; win dolphin-$how-open
	set -- $(client dolphin-$how-open org.kde.dolphin)
	if [ $# = 4 ]; then
		x=$(( $1 + ${ITEM_AT%,*} )); y=$(( $2 + ${ITEM_AT#*,} ))
		mark "dolphin-$how $x,$y"
		if [ $how = click ]; then steps="m:$x,$y s:500 b:272 s:3000"; else steps="m:$(( $1 + 5 )),$(( $2 + 5 )) s:500 t:$x,$y s:3000"; fi
		"$FAKEINPUT" $steps > "$OUT/fi-dolphin-$how.txt" 2>&1
	fi
	win dolphin-$how; shot dolphin-$how; close_dolphin
done
# 5 to 8: the task manager, with Dolphin and System Settings open, System Settings in front: one tap, then two taps, then
# a mouse click on Dolphin's button (not the active window's: a click on the active one minimizes it), then a long touch
# on System Settings' button (a menu is a window plasmashell adds)
dolphin "$HOME/Desktop/TouchTest" > "$OUT/dolphin-tm.log" 2>&1 &
sleep 6
systemsettings > "$OUT/systemsettings.log" 2>&1 &
sleep 8; win tm-before; shot tm-before
at=$(icon tm-before org.kde.dolphin); mark "tm-tap dolphin $at"
[ -n "$at" ] && "$FAKEINPUT" m:960,300 s:300 t:$at s:2500 > "$OUT/fi-tm-tap.txt" 2>&1
win tm-tap; shot tm-tap
[ -n "$at" ] && "$FAKEINPUT" t:$at s:300 t:$at s:2500 > "$OUT/fi-tm-tap2.txt" 2>&1
win tm-tap2; shot tm-tap2
# System Settings in front again, then the mouse
at2=$(icon tm-before systemsettings)
[ -n "$at2" ] && "$FAKEINPUT" m:$at2 s:400 b:272 s:2000 > "$OUT/fi-tm-front.txt" 2>&1
win tm-front; mark "tm-click dolphin $at"
[ -n "$at" ] && "$FAKEINPUT" m:$at s:500 b:272 s:2500 > "$OUT/fi-tm-click.txt" 2>&1
win tm-click; shot tm-click
mark "tm-hold systemsettings $at2"
[ -n "$at2" ] && "$FAKEINPUT" m:960,300 s:300 h:$at2 s:1500 > "$OUT/fi-tm-hold.txt" 2>&1
win tm-hold; shot tm-hold
"$FAKEINPUT" k:1 s:800 >> "$OUT/fi-tm-hold.txt" 2>&1
for p in $(pgrep -x systemsettings); do kill -TERM "$p"; done
close_dolphin
mark done
