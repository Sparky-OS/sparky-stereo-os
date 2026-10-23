#!/bin/bash
# Daniel's full matrix (2026-10-23): every display setup x {idle desktop, 2D film, 3D film}; plus DPMS-off idle floors.
# KWin logs every frame of every output (drop-in); a 1 Hz sysfs logger runs throughout; marks give each window.
set -u
B=~/kwin-measure-2026-10-23; R=$B/matrix2; mkdir -p $R; cd $R
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus WAYLAND_DISPLAY=wayland-0
V=~/Videos; F2D="$V/Tudo.em.Todo.Lugar.ao.Mesmo.Tempo.2022.mkv"; F3D="$V/[3D].Life.of.Pi.mkv"
WARM=60; REC=180; IDLE=120
up() { cut -d' ' -f1 /proc/uptime; }
say() { notify-send -a "KWin measurement" -t 8000 "$1" "${2:-}" >/dev/null 2>&1 || true; }
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
kd() { say "Changing screens" "$*"; echo "kscreen-doctor $*" >> doctor.log; kscreen-doctor "$@" >> doctor.log 2>&1; sleep 7; }
# mode id on an output by exact label, e.g. mid eDP-1 '1280x720@60.01(virtual-3D:5)'
mid() { kscreen-doctor -o 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | awk -v o="$1" '$0 ~ "Output: [0-9]+ "o" "{f=1;next} /^Output:/{f=0} f && /Modes:/{print; exit}' | tr ' ' '\n' | sed 's/[*!]//g' | grep -v '^$' | grep -E -- "^[0-9]+:$(printf '%s' "$2" | sed 's/[][().*]/\\&/g')\$" | head -1 | cut -d: -f1; }
to_out() { printf 'for (const w of workspace.windowList()) if (w.resourceClass == "mpv") { const o = workspace.screens.find(s => s.name == "%s"); if (o) workspace.sendClientToScreen(w, o); }\n' "$1" > $R/to-out.js
  local id; id=$(qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript $R/to-out.js "m-$RANDOM")
  qdbus6 org.kde.KWin /Scripting/Script$id org.kde.kwin.Script.run >/dev/null 2>&1; sleep 1; qdbus6 org.kde.KWin /Scripting/Script$id org.kde.kwin.Script.stop >/dev/null 2>&1; }
work() {  # cfg output: idle desktop, 2D film, 3D film on that output
  local cfg=$1 out=$2
  say "Case $cfg" "Idle desktop: 2 minutes recorded after 30 s"; sleep 30; mark "$cfg/idle"; sleep $IDLE; mark "$cfg/idle-end"
  for w in 2dfilm:"$F2D" 3dfilm:"$F3D"; do
    local n=${w%%:*} f=${w#*:}
    say "Case $cfg: $n" "1 min warm-up, then 3 min recorded"
    mpv --no-audio --loop-file=inf --no-terminal --fs --fs-screen-name=$out --screen-name=$out --log-file=$R/$cfg-$n-mpv.log "$f" & local p=$!
    sleep 4; to_out $out; sleep $WARM; mark "$cfg/$n"; sleep $REC; mark "$cfg/$n-end"; kill $p; wait $p 2>/dev/null; sleep 8
  done
  kscreen-doctor -o 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -E '^Output|enabled|disabled|\*|replication' > $R/$cfg-outputs.txt; }
workp() {  # cfg output file prime(0|1): one film, the same windows, with or without render offload to the discrete GPU
  local cfg=$1 out=$2 f=$3 pr=$4
  if [ "$pr" = 1 ]; then export DRI_PRIME=1; else unset DRI_PRIME; fi
  mpv --no-audio --loop-file=inf --no-terminal --fs --fs-screen-name=$out --screen-name=$out -v --log-file=$R/$cfg-mpv.log "$f" & local p=$!
  unset DRI_PRIME
  say "Case $cfg" "1 min warm-up, then 3 min recorded"
  sleep 4; to_out $out; sleep $WARM; mark "$cfg"; sleep $REC; mark "$cfg-end"; kill $p; wait $p 2>/dev/null; sleep 8; }
both_on() { kd output.eDP-1.enable output.HDMI-A-1.enable; kd output.HDMI-A-1.mirror.none; }
: > marks.csv; logger & L=$!
E2D=$(mid eDP-1 '1366x768@60.01'); E3D=$(mid eDP-1 '1366x768@60.01(virtual-3D:5)')
E7=$(mid eDP-1 '1280x720@60.01'); E73D=$(mid eDP-1 '1280x720@60.01(virtual-3D:5)')
T2D=$(mid HDMI-A-1 '1920x1080@30.00'); T3D=$(mid HDMI-A-1 '1920x1080@30.00(3D-FP)')
T7=$(mid HDMI-A-1 '1280x720@60.00'); T73D=$(mid HDMI-A-1 '1280x720@60.00(3D-FP)')
echo "ids E2D=$E2D E3D=$E3D E7=$E7 E73D=$E73D T2D=$T2D T3D=$T3D T7=$T7 T73D=$T73D" > ids.txt
say "Measurement matrix" "Starting: about 90 minutes, no need to watch"
for v in "$E2D" "$E3D" "$E7" "$E73D" "$T2D" "$T3D" "$T7" "$T73D"; do [ -n "$v" ] || { echo "missing mode id" >> ids.txt; say "Measurement stopped" "A display mode was not found"; kill $L; exit 3; }; done
# L, K: extended, both 2D; notebook 3D with TV 2D
both_on; kd output.eDP-1.mode.$E2D output.HDMI-A-1.mode.$T2D; work L-ext-both-2d eDP-1
kd output.eDP-1.mode.$E3D; work K-ext-edp3d-tv2d eDP-1
# P: render offload (PRIME) to the discrete R5 M430, extended with both screens in 3D, default then offload, back to back
both_on; kd output.eDP-1.mode.$E3D output.HDMI-A-1.mode.$T3D
F48="$V/[3D].Coyote Falls.mkv"
workp P-lifeofpi-default eDP-1 "$F3D" 0
workp P-lifeofpi-prime eDP-1 "$F3D" 1
workp P-coyote-default eDP-1 "$F48" 0
workp P-coyote-prime eDP-1 "$F48" 1
# C, D: notebook alone
kd output.HDMI-A-1.disable; kd output.eDP-1.mode.$E2D; work C-edp-alone-2d eDP-1
kd output.eDP-1.mode.$E3D; work D-edp-alone-3d eDP-1
# E, F: TV alone
kd output.HDMI-A-1.enable; kd output.HDMI-A-1.mode.$T2D; kd output.eDP-1.disable; work E-tv-alone-2d HDMI-A-1
kd output.HDMI-A-1.mode.$T3D; work F-tv-alone-3d HDMI-A-1
# A, B: idle floor, both screens on in 2D then 3D, DPMS off
kd output.eDP-1.enable; kd output.eDP-1.mode.$E2D output.HDMI-A-1.mode.$T2D; sleep 20; kscreen-doctor --dpms off >> doctor.log 2>&1; sleep 30; mark "A-dpms-off-2d/idle"; sleep 180; mark "A-dpms-off-2d/idle-end"; kscreen-doctor --dpms on >> doctor.log 2>&1; sleep 15
kd output.eDP-1.mode.$E3D output.HDMI-A-1.mode.$T3D; sleep 20; kscreen-doctor --dpms off >> doctor.log 2>&1; sleep 30; mark "B-dpms-off-3d/idle"; sleep 180; mark "B-dpms-off-3d/idle-end"; kscreen-doctor --dpms on >> doctor.log 2>&1; sleep 15
# back to Daniel's setup of this morning: TV 1080p30 frame packing, notebook 1366x768 2D, extended
kd output.HDMI-A-1.mode.$T3D output.eDP-1.mode.$E2D
kscreen-doctor -o 2>&1 | sed 's/\x1b\[[0-9;]*m//g' > outputs-final.txt
say "Measurement matrix done" "Screens back to the morning setup"; kill $L; echo done > matrix.done
