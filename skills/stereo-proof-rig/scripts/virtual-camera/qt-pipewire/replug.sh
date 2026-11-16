#!/bin/bash
# ORDER 625, Daniel's (b) for a program that is streaming: cam-b chosen and streaming, cam-b unplugged, plugged in again.
# Usage: replug.sh NAME BUILD (same environment as scenario.sh: RIG, WORK, QT_PREFIX, PROBE, EVIDENCE)
set -uo pipefail
NAME=$1 BUILD=$2
RIG=${RIG:?this folder} WORK=${WORK:?a scratch folder} QT_PREFIX=${QT_PREFIX:?the Qt prefix the build uses}
PROBE=${PROBE:?probe.cpp built against BUILD}
OUT=${EVIDENCE:?a folder for the log}/$NAME-replug.log
exec > >(tee "$OUT") 2>&1
ulimit -c 0
R=$WORK/run-replug-$NAME
rm -rf "$R"; mkdir -p "$R/run" "$R/state" "$R/config" "$R/home"; chmod 700 "$R/run"
export HOME=$R/home XDG_RUNTIME_DIR=$R/run XDG_STATE_HOME=$R/state XDG_CONFIG_HOME=$R/config LANG=C.UTF-8
export LD_LIBRARY_PATH=$BUILD/lib:$QT_PREFIX/lib QT_PLUGIN_PATH=$BUILD/plugins:$QT_PREFIX/plugins
export QT_QPA_PLATFORM=offscreen QT_MEDIA_BACKEND=ffmpeg QT_CAMERA_BACKEND=pipewire
DBUS_SESSION_BUS_ADDRESS=$(dbus-daemon --session --fork --print-address --address="unix:path=$R/run/bus")
export DBUS_SESSION_BUS_ADDRESS
pipewire >"$R/pipewire.log" 2>&1 & PW=$!
sleep 1
wireplumber >"$R/wireplumber.log" 2>&1 & WP=$!
sleep 3
cam() { gst-launch-1.0 -q videotestsrc is-live=true pattern="$3" ! 'video/x-raw,format=BGRx,width=640,height=480,framerate=30/1' \
	! pipewiresink mode=provide stream-properties="props,media.class=Video/Source,node.name=$1,node.description=$1$2" >/dev/null 2>&1 & echo $!; }
A=$(cam cam-a ",device.api=v4l2,media.role=Camera" smpte)
B=$(cam cam-b ",device.api=v4l2,media.role=Camera" ball)
sleep 4
pw-metadata -n default 0 default.configured.video.source '{ "name": "cam-b" }' Spa:String:JSON >/dev/null
sleep 3
echo "== case 10 (Daniel b, streaming): a program streams the default camera, cam-b; cam-b unplugged, then plugged in again"
(timeout 60 "$PROBE" --start --watch 30 2>&1 | grep -v '^$' >"$R/w10.log") &
WAIT=$!
sleep 8
echo "-- streaming"; python3 "$RIG/links.py" | grep -E "METADATA|LINK"
kill "$B"; sleep 6
echo "-- cam-b unplugged"; python3 "$RIG/links.py" | grep -E "METADATA|LINK"
B=$(cam cam-b ",device.api=v4l2,media.role=Camera" ball); sleep 8
echo "-- cam-b plugged in again"; python3 "$RIG/links.py" | grep -E "METADATA|LINK"
wait $WAIT
cat "$R/w10.log"
for p in "$A" "$B" "$WP" "$PW"; do kill "$p" 2>/dev/null; done
