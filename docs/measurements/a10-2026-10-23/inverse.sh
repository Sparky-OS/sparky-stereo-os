#!/bin/bash
# Daniel's full matrix (2026-10-23): every display setup x {idle desktop, 2D film, 3D film}; plus DPMS-off idle floors.
# KWin logs every frame of every output (drop-in); a 1 Hz sysfs logger runs throughout; marks give each window.
set -u
B=~/kwin-measure-2026-10-23; R=$B/matrix-inverse; mkdir -p $R; cd $R
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus WAYLAND_DISPLAY=wayland-0
V=~/Videos; F2D="$V/Tudo.em.Todo.Lugar.ao.Mesmo.Tempo.2022.mkv"; F3D="$V/[3D].Life.of.Pi.mkv"
WARM=60; REC=180; IDLE=120
up() { cut -d' ' -f1 /proc/uptime; }
mark() { echo "$1,$(up)" >> marks.csv; }
logger() {  # uptime, cpu busy %, cpu MHz avg, gpu busy % per card, gpu temps, cpu temp, apu power
  local pi pt; read -r _ a b c d e f g h _ < /proc/stat; pt=$((a+b+c+d+e+f+g+h)); pi=$((d+e))
  echo "uptime,cpu_busy,cpu_mhz,gpu_busy_card0,gpu_busy_card1,gpu_temp_a,gpu_temp_b,cpu_temp,apu_power_mw" > sys.csv
  while :; do sleep 1
    read -r _ a b c d e f g h _ < /proc/stat; local t=$((a+b+c+d+e+f+g+h)) i=$((d+e))
    local busy=$(( (100*((t-pt)-(i-pi)))/((t-pt)>0?(t-pt):1) )); pt=$t; pi=$i
    local mhz=$(awk '{s+=$1;n++} END{printf "%d", s/n/1000}' /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq)
    echo "$(up),$busy,$mhz,$(cat /sys/class/drm/card0/device/gpu_busy_percent 2>/dev/null),$(cat /sys/class/drm/card1/device/gpu_busy_percent 2>/dev/null),$(cat /sys/class/hwmon/hwmon1/temp1_input 2>/dev/null),$(cat /sys/class/hwmon/hwmon2/temp1_input 2>/dev/null),$(cat /sys/class/hwmon/hwmon5/temp1_input 2>/dev/null),$(cat /sys/class/hwmon/hwmon4/power1_input 2>/dev/null)" >> sys.csv
  done; }
kd() { echo "kscreen-doctor $*" >> doctor.log; kscreen-doctor "$@" >> doctor.log 2>&1; sleep 7; }
# mode id on an output by exact label, e.g. mid eDP-1 '1280x720@60.01(virtual-3D:5)'
mid() { kscreen-doctor -o 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | awk -v o="$1" '$0 ~ "Output: [0-9]+ "o" "{f=1;next} /^Output:/{f=0} f && /Modes:/{print; exit}' | tr ' ' '\n' | sed 's/[*!]//g' | grep -v '^$' | grep -E -- "^[0-9]+:$(printf '%s' "$2" | sed 's/[][().*]/\\&/g')\$" | head -1 | cut -d: -f1; }
to_out() { printf 'for (const w of workspace.windowList()) if (w.resourceClass == "mpv") { const o = workspace.screens.find(s => s.name == "%s"); if (o) workspace.sendClientToScreen(w, o); }\n' "$1" > $R/to-out.js
  local id; id=$(qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript $R/to-out.js "m-$RANDOM")
  qdbus6 org.kde.KWin /Scripting/Script$id org.kde.kwin.Script.run >/dev/null 2>&1; sleep 1; qdbus6 org.kde.KWin /Scripting/Script$id org.kde.kwin.Script.stop >/dev/null 2>&1; }
work() {  # cfg output: idle desktop, 2D film, 3D film on that output
  local cfg=$1 out=$2
  sleep 30; mark "$cfg/idle"; sleep $IDLE; mark "$cfg/idle-end"
  for w in 2dfilm:"$F2D" 3dfilm:"$F3D"; do
    local n=${w%%:*} f=${w#*:}
    mpv --no-audio --loop-file=inf --no-terminal --fs --fs-screen-name=$out --screen-name=$out --log-file=$R/$cfg-$n-mpv.log "$f" & local p=$!
    sleep 4; to_out $out; sleep $WARM; mark "$cfg/$n"; sleep $REC; mark "$cfg/$n-end"; kill $p; wait $p 2>/dev/null; sleep 8
  done
  kscreen-doctor -o 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -E '^Output|enabled|disabled|\*|replication' > $R/$cfg-outputs.txt; }
both_on() { kd output.eDP-1.enable output.HDMI-A-1.enable; kd output.HDMI-A-1.mirror.none; }
: > marks.csv; logger & L=$!
E2D=$(mid eDP-1 '1366x768@60.01'); E3D=$(mid eDP-1 '1366x768@60.01(virtual-3D:5)')
E7=$(mid eDP-1 '1280x720@60.01'); E73D=$(mid eDP-1 '1280x720@60.01(virtual-3D:5)')
T2D=$(mid HDMI-A-1 '1920x1080@30.00'); T3D=$(mid HDMI-A-1 '1920x1080@30.00(3D-FP)')
T7=$(mid HDMI-A-1 '1280x720@60.00'); T73D=$(mid HDMI-A-1 '1280x720@60.00(3D-FP)')
echo "ids E2D=$E2D E3D=$E3D E7=$E7 E73D=$E73D T2D=$T2D T3D=$T3D T7=$T7 T73D=$T73D" > ids.txt
for v in "$E2D" "$E3D" "$E7" "$E73D" "$T2D" "$T3D" "$T7" "$T73D"; do [ -n "$v" ] || { echo "missing mode id" >> ids.txt; kill $L; exit 3; }; done
grows() {  # frames logged on output $1 during $2 seconds
  local f="$B/kwin perf statistics $1.csv" a b; a=$(wc -l < "$f"); sleep $2; b=$(wc -l < "$f"); echo $((b-a)); }
inv() {  # cfg emode tmode: TV is the source, the notebook mirrors it
  local cfg=$1 em=$2 tm=$3
  both_on; kd output.eDP-1.mode.$em output.HDMI-A-1.mode.$tm; kd output.eDP-1.mirror.HDMI-A-1; mark "$cfg/setup"
  kscreen-doctor -o 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -E '^Output|replication|\*' > $R/$cfg-outputs.txt
  mpv --no-audio --loop-file=inf --no-terminal --fs --fs-screen-name=HDMI-A-1 --screen-name=HDMI-A-1 --log-file=$R/$cfg-probe-mpv.log "$F2D" & local p=$!
  sleep 4; to_out HDMI-A-1; local g; g=$(grows HDMI-A-1 60); kill $p; wait $p 2>/dev/null
  echo "$cfg probe: HDMI-A-1 frames in 60 s with a 2D film = $g" >> $R/probe.txt
  if [ "$g" -lt 10 ]; then mark "$cfg/frozen"; kd output.eDP-1.mirror.none; mark "$cfg/mirror-none"; return; fi
  work $cfg HDMI-A-1; kd output.eDP-1.mirror.none; }
: > marks.csv; logger & L=$!
E7=$(mid eDP-1 '1280x720@60.01'); E73D=$(mid eDP-1 '1280x720@60.01(virtual-3D:5)'); T7=$(mid HDMI-A-1 '1280x720@60.00'); T73D=$(mid HDMI-A-1 '1280x720@60.00(3D-FP)')
E2D=$(mid eDP-1 '1366x768@60.01'); T3D=$(mid HDMI-A-1 '1920x1080@30.00(3D-FP)')
echo "ids E7=$E7 E73D=$E73D T7=$T7 T73D=$T73D E2D=$E2D T3D=$T3D" > ids.txt
for v in "$E7" "$E73D" "$T7" "$T73D" "$E2D" "$T3D"; do [ -n "$v" ] || { echo "missing mode id" >> ids.txt; kill $L; exit 3; }; done
inv G2-copy-2d-tv-source $E7 $T7
inv H2-copy-3d-tv-source $E73D $T73D
both_on; kd output.HDMI-A-1.mode.$T3D output.eDP-1.mode.$E2D
kill $L; echo done > inverse.done
