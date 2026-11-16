#!/bin/bash
# ORDER 625's cases on Qt's PipeWire camera backend, in a private PipeWire and WirePlumber session inside a throwaway
# container (never the desktop's), as an ordinary user. Usage: scenario.sh NAME BUILD
# NAME labels the log (dev or branch); BUILD is the qtmultimedia build tree whose library and plugin are tested.
set -uo pipefail
NAME=$1 BUILD=$2
RIG=${RIG:?this folder} WORK=${WORK:?a scratch folder} QT_PREFIX=${QT_PREFIX:?the Qt prefix the build uses}
PROBE=${PROBE:?probe.cpp built against BUILD}
OUT=${EVIDENCE:?a folder for the log}/$NAME-cases.log
exec > >(tee "$OUT") 2>&1
ulimit -c 0
R=$WORK/run-$NAME
rm -rf "$R"
mkdir -p "$R/run" "$R/state" "$R/config" "$R/home"
chmod 700 "$R/run"
export HOME=$R/home XDG_RUNTIME_DIR=$R/run XDG_STATE_HOME=$R/state XDG_CONFIG_HOME=$R/config
export LD_LIBRARY_PATH=$BUILD/lib:$QT_PREFIX/lib QT_PLUGIN_PATH=$BUILD/plugins:$QT_PREFIX/plugins
export QT_QPA_PLATFORM=offscreen QT_MEDIA_BACKEND=ffmpeg QT_CAMERA_BACKEND=pipewire LANG=C.UTF-8
DBUS_SESSION_BUS_ADDRESS=$(dbus-daemon --session --fork --print-address --address="unix:path=$R/run/bus")
export DBUS_SESSION_BUS_ADDRESS

startwp() { wireplumber >>"$R/wireplumber.log" 2>&1 & WP=$!; sleep 3; }
pipewire >"$R/pipewire.log" 2>&1 &
PW=$!
sleep 1
startwp

cam() { # NAME EXTRA_PROPERTIES PATTERN: a PipeWire Video/Source node fed by GStreamer
	gst-launch-1.0 -q videotestsrc is-live=true pattern="$3" ! 'video/x-raw,format=BGRx,width=640,height=480,framerate=30/1' \
		! pipewiresink mode=provide stream-properties="props,media.class=Video/Source,node.name=$1,node.description=$1$2" \
		>/dev/null 2>&1 &
	echo $!
}
setconf() { pw-metadata -n default 0 default.configured.video.source "{ \"name\": \"$1\" }" Spa:String:JSON >/dev/null; sleep 3; }
links() { python3 "$RIG/links.py"; }
probe() { timeout 60 "$PROBE" "$@" 2>&1 | grep -v '^$'; }

echo "== versions $NAME"
pipewire --version | tail -1
wireplumber --version 2>&1 | tail -1
echo "library $(readlink -f "$BUILD/lib/libQt6Multimedia.so.6")"
A=$(cam cam-a ",device.api=v4l2,media.role=Camera" smpte)
B=$(cam cam-b ",device.api=v4l2,media.role=Camera" ball)
C=$(cam cam-c ",device.api=libcamera,media.role=Camera" snow)
sleep 5
echo "== session"
links

echo "== case 1: nobody chose a camera (WirePlumber's own pick is default.video.source)"
probe

echo "== case 2: the person chose cam-b, the second camera"
setconf cam-b
links | grep METADATA
probe

echo "== case 3: the default changes three times while a program runs (cam-c, cam-a, cam-b)"
(probe --watch 18 >"$R/w3.log") &
WAIT=$!
sleep 6
setconf cam-c
setconf cam-a
setconf cam-b
wait $WAIT
cat "$R/w3.log"

echo "== case 4 (Daniel b): cam-b chosen, unplugged, plugged in again, while a program runs"
(probe --watch 28 >"$R/w4.log") &
WAIT=$!
sleep 6
kill "$B"
sleep 4
echo "-- cam-b unplugged"
links | grep -E "METADATA|NODE"
echo "-- a fresh program while cam-b is away"
probe
B=$(cam cam-b ",device.api=v4l2,media.role=Camera" ball)
sleep 5
echo "-- cam-b plugged in again"
links | grep -E "METADATA|NODE"
wait $WAIT
echo "-- the program that ran through the unplug and the plug"
cat "$R/w4.log"

echo "== case 5 (Daniel a, the session's choice): cam-b chosen; a program that opened the default camera, through a hotplug, a list refresh and a restart"
(probe --start --watch 30 >"$R/w5.log") &
WAIT=$!
sleep 7
echo "-- running"
links | grep -E "METADATA|LINK"
Z=$(cam cam-0 ",device.api=v4l2,media.role=Camera" red)
sleep 6
echo "-- hotplug: cam-0 appeared (it sorts first)"
links | grep -E "METADATA|LINK"
kill "$Z"
sleep 6
echo "-- list refresh: cam-0 left again"
links | grep -E "METADATA|LINK"
wait $WAIT
cat "$R/w5.log"
echo "-- restart: the same program again"
(probe --start --watch 10 >"$R/w5b.log") &
WAIT=$!
sleep 7
links | grep -E "LINK"
wait $WAIT
cat "$R/w5b.log"

echo "== case 6 (Daniel a, the program's own choice): the program chose cam-c, the session's default is cam-a"
setconf cam-a
(probe --own pw:cam-c --start --watch 30 >"$R/w6.log") &
WAIT=$!
sleep 7
echo "-- running"
links | grep -E "METADATA|LINK"
Z=$(cam cam-0 ",device.api=v4l2,media.role=Camera" red)
sleep 6
echo "-- hotplug: cam-0 appeared"
links | grep -E "LINK"
kill "$Z"
sleep 6
echo "-- list refresh: cam-0 left again"
links | grep -E "LINK"
wait $WAIT
cat "$R/w6.log"
echo "-- restart: the program opens its saved choice, pw:cam-c, again"
(probe --own pw:cam-c --start --watch 10 >"$R/w6b.log") &
WAIT=$!
sleep 7
links | grep -E "LINK"
wait $WAIT
cat "$R/w6b.log"

echo "== case 7: the session's default is a video source that is not a camera (a screen share node)"
SCR=$(cam screen-share "" checkers-8)
sleep 4
setconf screen-share
links | grep -E "METADATA|NODE"
probe
echo "-- the same program asks again (said once per process)"
probe --watch 3
kill "$SCR"
sleep 4

echo "== case 8: no session manager (WirePlumber stopped), then WirePlumber back, while a program runs"
setconf cam-b
(probe --watch 24 >"$R/w8.log") &
WAIT=$!
sleep 6
kill "$WP"
wait "$WP" 2>/dev/null
sleep 4
echo "-- WirePlumber stopped"
links | grep -E "METADATA" || echo "no default metadata"
echo "-- a fresh program without a session manager"
probe
startwp
sleep 3
echo "-- WirePlumber back"
links | grep -E "METADATA"
wait $WAIT
cat "$R/w8.log"

echo "== case 9: a stream with no target, as a camera opened without a device would connect (GStreamer's pipewiresrc)"
setconf cam-c
gst-launch-1.0 -q pipewiresrc stream-properties="props,media.type=Video,media.category=Capture,media.role=Camera" ! fakesink >/dev/null 2>&1 &
G=$!
sleep 5
links | grep -E "METADATA|LINK"
kill "$G"

echo "== done"
for p in "$A" "$B" "$C" "$WP" "$PW"; do kill "$p" 2>/dev/null; done
