#!/bin/bash
# One rig session: an X11 window is the selected one, then Xwayland dies (or the X11 client, or nothing), then two
# Wayland windows are selected in turn, with a capture after each step. Runs inside a throwaway container as an ordinary
# user under dbus-run-session, with a render node for KWin. RIG_BIN holds wl-solid and x11-solid, CAPTURE is capture.py.
# Usage: session.sh OUT CASE      CASE: xwayland-killed | client-killed | close-during-animation | control
set -uo pipefail
OUT=$1
CASE=$2
mkdir -p "$OUT"
export XDG_RUNTIME_DIR=$(mktemp -d /tmp/rt.XXXXXX) HOME=/home/rig
chmod 700 "$XDG_RUNTIME_DIR"
export QT_LOGGING_RULES='kwin_scripting.debug=true'
export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
B=${RIG_BIN:?the folder with wl-solid and x11-solid}
CAPTURE=${CAPTURE:?the path of ../capture.py}
HERE=$(cd "$(dirname "$0")" && pwd)
step() { printf '%s %s\n' "$(date -u +%T.%3N)" "$*" >> "$OUT/steps.txt"; }

if [ "${FAKE_NOTIFY:-0}" = 1 ]; then
    python3 "$HERE/fake-notifyd.py" "$OUT/notifications.jsonl" 2> "$OUT/fake-notifyd.err" &
    for _ in $(seq 50); do grep -q ready "$OUT/notifications.jsonl" 2>/dev/null && break; sleep 0.1; done
fi
kwin_wayland --virtual --xwayland --socket=sub --width 1280 --height 800 > "$OUT/kwin.log" 2>&1 &
KWIN=$!
for _ in $(seq 100); do [ -S "$XDG_RUNTIME_DIR/sub" ] && break; sleep 0.1; done
[ -S "$XDG_RUNTIME_DIR/sub" ] || { step "FAIL no Wayland socket"; exit 3; }
for _ in $(seq 100); do ls /tmp/.X11-unix/X* >/dev/null 2>&1 && break; sleep 0.1; done
DISP=:$(ls /tmp/.X11-unix/ | sed -n 's/^X//p' | sort -n | head -1)
step "kwin $KWIN wayland sub x11 $DISP"

# a KWin script; its print() lines reach kwin.log through kwin_scripting
kscript() {
    local f="$OUT/script-$1.js"
    printf '%s\n' "$2" > "$f"
    local id
    id=$(gdbus call --session --dest org.kde.KWin --object-path /Scripting --method org.kde.kwin.Scripting.loadScript "$f" "rig-$1" | sed -n 's/^(\([0-9-]*\),)$/\1/p')
    [ -n "$id" ] && [ "$id" -ge 0 ] || { step "FAIL script $1 not loaded"; return 1; }
    gdbus call --session --dest org.kde.KWin --object-path "/Scripting/Script$id" --method org.kde.kwin.Script.run > /dev/null
    sleep 0.3
    gdbus call --session --dest org.kde.KWin --object-path /Scripting --method org.kde.kwin.Scripting.unloadScript "rig-$1" > /dev/null
}
find_js='function find(c) { for (const w of workspace.stackingOrder) { if (w.caption === c) return w; } return null; }'
place() {  # CAPTION X Y
    kscript "place-$1" "$find_js
const w = find('$1'); if (w) { w.frameGeometry = {x: $2, y: $3, width: 500, height: 320}; } print('rig: placed $1 ' + (w !== null));"
}
select_window() {  # CAPTION
    kscript "select-$1" "$find_js
const w = find('$1'); if (w) { workspace.activeWindow = w; }
print('rig: active ' + (workspace.activeWindow ? workspace.activeWindow.caption : 'none'));"
}
capture() {  # NAME
    python3 "$CAPTURE" "$OUT/$1.png" > "$OUT/$1.json" 2>> "$OUT/capture.err" || step "FAIL capture $1"
    step "capture $1 errors-so-far $(grep -c 'references invalid window' "$OUT/kwin.log")"
}

WAYLAND_DISPLAY=sub $B/wl-solid wl-a 480 280 > "$OUT/wl-a.log" 2>&1 &
sleep 1
WAYLAND_DISPLAY=sub $B/wl-solid wl-b 480 280 > "$OUT/wl-b.log" 2>&1 &
sleep 1
DISPLAY=$DISP $B/x11-solid x11-a 480 280 > "$OUT/x11-a.log" 2>&1 &
X11=$!
sleep 2
place wl-a 40 40
place wl-b 640 40
place x11-a 40 420
select_window x11-a
sleep 1
capture 0-x11-selected

case "$CASE" in
xwayland-killed)
    XW=$(pidof Xwayland)
    step "kill -9 Xwayland $XW"
    kill -9 $XW
    ;;
client-killed)
    step "kill -9 x11-solid $X11"
    kill -9 $X11
    ;;
close-during-animation)
    # the window is closed while its own closing effect runs, and selection moves at once
    step "kill -9 x11-solid $X11, select wl-a within 50 ms"
    kill -9 $X11
    sleep 0.05
    ;;
control)
    step "no window goes"
    ;;
esac
[ "$CASE" = close-during-animation ] || sleep 1.5
select_window wl-a
sleep 1
capture 1-wl-a-selected
select_window wl-b
sleep 1
capture 2-wl-b-selected
grep -E 'rig:|references invalid window|Xwayland|X11 connection' "$OUT/kwin.log" > "$OUT/kwin-lines.txt"
pidof Xwayland > "$OUT/xwayland-after.txt" || true
ls -la "$HOME/.local/state/sparky-stereo-problems" > "$OUT/problems-store.txt" 2>&1 || true
kill $KWIN 2>/dev/null
wait $KWIN 2>/dev/null
step "end"
exit 0
