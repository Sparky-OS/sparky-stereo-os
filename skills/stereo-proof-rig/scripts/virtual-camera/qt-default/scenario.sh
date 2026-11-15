#!/bin/bash
# The cases of ORDER 582, as the lane's user in the container. Every line of the log is a fact the report quotes.
set -uo pipefail
RIG=${RIG:?the scripts/virtual-camera folder}
W=${WORK:?a scratch folder}
OUT=$W/evidence/$NAME-cases.log
exec > >(tee "$OUT") 2>&1
ulimit -c 0
cc -shared -fPIC -O1 -o "$W/vcam-shim.so" "$RIG/vcam-shim.c" -ldl
sh "$RIG/session-start.sh" >/dev/null
. "$XDG_RUNTIME_DIR/env.sh"
PROBE=${PROBE:-$W/probe-build/b/camera-default-probe}
probe() { # a fresh program; stderr (Qt's log) follows the facts
	LD_PRELOAD=$W/vcam-shim.so timeout 30 "$PROBE" "$@" 2>&1 | grep -v '^$'
}
settle() { sleep "${1:-4}"; }
setdefault() { pw-metadata -n default 0 default.configured.video.source "{ \"name\": \"$1\" }" Spa:String:JSON >/dev/null; settle 3; }
cleardefault() { pw-metadata -n default -d 0 default.configured.video.source >/dev/null 2>&1; settle 3; }
startcam() { sh "$RIG/virtual-camera.sh" "$1" >/dev/null 2>&1 & echo $!; }
echo "== versions"; pipewire --version | tail -1; wireplumber --version 2>&1 | tail -1
PA=$(startcam a); PB=$(startcam b); PS=$(startcam held)
settle 5
echo "== session"; python3 "$RIG/pwcams.py"

echo "== case 1: nobody chose a default camera (the first camera stays the default, nothing is said)"
probe

echo "== case 2: the person chose cam-b (the second camera, /dev/video21) as the session's default"
setdefault cam-b
python3 "$RIG/pwcams.py" | grep default
probe

echo "== case 3: a program's own choice stays (OWN line above: chosen and kept are equal)"

echo "== case 4: the default changes while a program runs"
( probe --watch 16 > "$W/watch-$NAME.log" 2>&1 ) &
WP=$!
settle 5
setdefault cam-held
settle 2
setdefault cam-a
settle 2
setdefault cam-b
wait $WP
cat "$W/watch-$NAME.log"

echo "== case 5: the chosen camera (cam-b) is unplugged, then plugged in again, while a program runs"
( probe --watch 20 > "$W/watch2-$NAME.log" 2>&1 ) &
WP=$!
settle 5
kill $PB; wait $PB 2>/dev/null; rm -f "$VCAM_ROOT/video21.cfg" /dev/video21
settle 4
echo "-- a fresh program while it is unplugged"
probe
PB=$(startcam b); cp "$RIG/vcam/video21.cfg" "$VCAM_ROOT/video21.cfg"; ln -s /nonexistent-camera /dev/video21
settle 4
wait $WP
echo "-- the program that ran through the unplug and the plug"
cat "$W/watch2-$NAME.log"

echo "== case 6: a name that matches no camera"
setdefault nothing-like-a-camera
probe

echo "== case 7: no PipeWire session"
setdefault cam-b
for p in $(ps -eo pid,comm | awk '$2=="wireplumber"||$2=="pipewire"||$2=="pipewire-pulse"{print $1}'); do kill $p; done
settle 3
probe
echo "== done"
for p in $PA $PB $PS; do kill $p 2>/dev/null || true; done
