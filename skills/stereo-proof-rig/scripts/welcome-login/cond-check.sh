#!/bin/bash
# cond-check.sh: inside a rig session (APP_CMD), the Welcome Center started with the session's own environment (read from
# plasmashell, started by startplasma after its env scripts, as kded's children are), showing PAGES; the session's
# XDG_CONFIG_DIRS goes to $CASE/cond/xdg-config-dirs.txt, the first page shown to $CASE/cond/first.png.
set -u
OUT=$CASE/cond; mkdir -p "$OUT"
p=$(pgrep -x plasmashell | head -1)
dirs=$(tr '\0' '\n' < /proc/$p/environ | sed -n 's/^XDG_CONFIG_DIRS=//p')
echo "$dirs" > "$OUT/xdg-config-dirs.txt"
XDG_CONFIG_DIRS=$dirs plasma-welcome --pages "$PAGES" > "$OUT/welcome.log" 2>&1 &
sleep 8
python3 /lane/kwin-windows-icons.py "$CASE/login1/session.log" > "$OUT/windows.json"
python3 "$RIG/login-splash/shot.py" Virtual-0 "$OUT/first.png" >> "$OUT/shots.jsonl" 2>&1
