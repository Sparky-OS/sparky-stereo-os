#!/bin/bash
# SPDX-License-Identifier: MIT
# The X11 twin of seq-session.sh (ORDER 623): on X11 through Xwayland,
# NOGLAMOR=1 for Xwayland without glamor (no DRI3); each step's X11 declaration and window size are kept too.
# Several programs one after the other in one fresh Stereo KWin session (output in its side-by-side 3D
# mode), the person's kept problems listed after each. usage: seq-x11.sh OUTDIR
# environment: SEQ="APP|VAR=V VAR=V;APP|..." (each runs RUN seconds, default 9), ICD (the Vulkan driver for every step)
set -u
ulimit -c 0
out=$1
export XDG_RUNTIME_DIR=/tmp/rt; mkdir -p $XDG_RUNTIME_DIR; chmod 700 $XDG_RUNTIME_DIR
export HOME=/tmp/home XDG_CONFIG_HOME=/tmp/home/.config XDG_DATA_HOME=/tmp/home/.local/share XDG_CACHE_HOME=/tmp/home/.cache XDG_STATE_HOME=/tmp/home/.local/state
mkdir -p $XDG_CONFIG_HOME $XDG_DATA_HOME $XDG_CACHE_HOME $XDG_STATE_HOME
export LANG=C.UTF-8 QT_QPA_PLATFORM=wayland W=${W:-1920} H=${H:-1080}
printf '[KDE]\nCursorBlinkRate=0\nAnimationDurationFactor=0\n' > $XDG_CONFIG_HOME/kdeglobals
printf '[StereoDepth]\nSunkLimit=10\nPoppedLimit=4\nElementLimit=1\n' > $XDG_CONFIG_HOME/kwinrc
export KWIN_VIRTUAL_STEREO_MODES=1
[ "${NOGLAMOR:-0}" = 1 ] && export XWAYLAND_NO_GLAMOR=1
case ${ICD:-} in
  lvp) export VK_DRIVER_FILES=/usr/share/vulkan/icd.d/lvp_icd.json ;;
  nvidia) export VK_DRIVER_FILES=$(ls /etc/vulkan/icd.d/nvidia_icd.json /usr/share/vulkan/icd.d/nvidia_icd.json 2>/dev/null | head -1) ;;
  radeon) export VK_DRIVER_FILES=/usr/share/vulkan/icd.d/radeon_icd.json ;;
esac
cat > /tmp/seq.sh <<'S'
out=$1
KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 kwin_wayland --virtual --xwayland --socket=sub --width $W --height $H > $out/kwin.log 2>&1 &
kwin=$!
for i in $(seq 100); do [ -S $XDG_RUNTIME_DIR/sub ] && break; sleep 0.1; done
sleep 1
kd() { WAYLAND_DISPLAY=sub kscreen-doctor "$@"; }
o=$(kd -o 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | awk '/^Output:/{print $3; exit}')
m=$(kd -o 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -o '[0-9]*:[^ ]*' | grep -i -m1 '3D-SBS' | cut -d: -f1)
kd output.$o.mode.$m > /dev/null 2>&1; sleep 1
for i in $(seq 100); do ls /tmp/.X11-unix/X* >/dev/null 2>&1 && break; sleep 0.1; done
export DISPLAY=:$(ls /tmp/.X11-unix | sed -n 's/^X//p' | head -1); sleep 1
{ xdpyinfo 2>&1 | grep -E 'DRI3|Present'; xprop -root _KDE_NET_WM_STEREO_CONTENT_SUPPORTED; } > $out/xserver.txt 2>&1
n=0
IFS=';' read -r -a steps <<< "$SEQ"
for step in "${steps[@]}"; do
  app=${step%%|*}; env=${step#*|}
  IFS=' ' read -r -a E <<< "$env"
  env WAYLAND_DISPLAY=sub "${E[@]}" /bin-fx/$app > $out/step-$n.out 2> $out/step-$n.err &
  c=$!; sleep ${RUN:-9}
  python3 /scripts/capture.py $out/shot-$n.png 2>> $out/capture.err
  for w in $(xwininfo -root -tree 2>/dev/null | awk '/"vk-extent-probe"|"vk-views"/{print $1}') $(grep -o -E '(parent|child)=0x[0-9a-f]+' $out/step-$n.out | cut -d= -f2 | sort -u); do
    { echo "-- step $n window $w"; xwininfo -id $w | grep -E 'Width|Height'; xprop -id $w _KDE_NET_WM_STEREO_CONTENT _KDE_NET_WM_STEREO_CONTENT_VERSION; } >> $out/x11-props.txt 2>&1; done
  kill $c; wait $c 2>/dev/null
  { echo "== after step $n: $app $env"; sparky-stereo-problems list --json; } >> $out/problems.txt 2>&1
  [ -n "${LANGS:-}" ] && for lg in $LANGS; do { echo "-- $lg"; LANG=$lg.UTF-8 LANGUAGE=$lg LC_ALL=$lg.UTF-8 sparky-stereo-problems list; } >> $out/problems.txt 2>&1; done
  n=$((n+1))
done
kill $kwin; wait $kwin 2>/dev/null
S
exec dbus-run-session -- bash /tmp/seq.sh "$out"
