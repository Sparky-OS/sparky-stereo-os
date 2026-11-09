#!/bin/bash
# SPDX-License-Identifier: MIT
# Inside the rig container: inner.sh MODE EVDIR
# MODE: plain | overflow | sibling | mono-sibling | late-sibling | shaped-sibling | raised | pointer | gls (glx client), egl-MODE (EGL two-view client), vk-MODE (Vulkan stereo layer client).
# One fresh Stereo KWin session per case; writes shot.png, props.json (the declarations), app.log, parent-wininfo.txt into EVDIR.
# Environment: CLIENT_SW=1 (llvmpipe for the client), CLIENT_ENV="VAR=value ..." (words put before the client), GLXV (GLX vendor, default mesa).
mode=$1 ev=$2; mkdir -p "$ev"
HERE=$(cd "$(dirname "$0")" && pwd); SCRIPTS=${SCRIPTS:-$HERE/..}
export HOME=$ev/home XDG_RUNTIME_DIR=$(mktemp -d /tmp/rt.XXXXXX) LANG=C.UTF-8
mkdir -p $HOME; chmod 700 $XDG_RUNTIME_DIR
export XDG_CONFIG_HOME=$XDG_RUNTIME_DIR/config; mkdir -p $XDG_CONFIG_HOME
export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
case "$mode" in
vk-*) src=x11vk.c; libs="-lvulkan -lxcb"; cmode=${mode#vk-};;
egl-*) src=x11egl.c; libs="-lX11 -lEGL -lGL"; cmode=${mode#egl-};;
*) src=x11child.c; libs="-lX11 -lXext -lGL"; cmode=$mode;;
esac
cc -O1 -o $ev/x11child $HERE/$src $libs 2>$ev/cc.log || { cat $ev/cc.log; exit 4; }
export HERE SCRIPTS ev mode cmode
dbus-run-session -- bash -c '
kwin_wayland --virtual --xwayland --socket=w --width 1024 --height 640 > $ev/kwin.log 2>&1 & kp=$!
for i in $(seq 1 120); do test -S $XDG_RUNTIME_DIR/w && ls /tmp/.X11-unix/X* >/dev/null 2>&1 && break; sleep .25; done; sleep 1
export DISPLAY=$(ls /tmp/.X11-unix | sed -n "s/^X/:/p" | head -1)
xprop -root _KDE_NET_WM_STEREO_CONTENT_SUPPORTED > $ev/root.txt 2>&1
env -u WAYLAND_DISPLAY ${CLIENT_SW:+LIBGL_ALWAYS_SOFTWARE=1} $CLIENT_ENV __GLX_VENDOR_LIBRARY_NAME=${GLXV:-mesa} X11VK_MODE=$cmode $ev/x11child $cmode > $ev/app.log 2> $ev/app.err & ap=$!
sleep 5
WAYLAND_DISPLAY=w /usr/bin/python3 -W ignore $SCRIPTS/capture.py $ev/shot.png > $ev/capture.json 2>$ev/capture.err
/usr/bin/python3 $SCRIPTS/x11_props.py > $ev/props.json 2>&1
if [ "$mode" = pointer ]; then
  xwininfo -id $(sed -n "s/.*parent=\(0x[0-9a-f]*\).*/\1/p" $ev/app.log | head -1) > $ev/parent-wininfo.txt 2>&1
  px=$(sed -n "s/.*Absolute upper-left X: *\(-\?[0-9]*\).*/\1/p" $ev/parent-wininfo.txt); py=$(sed -n "s/.*Absolute upper-left Y: *\(-\?[0-9]*\).*/\1/p" $ev/parent-wininfo.txt)
  steps=""
  for pt in 30,30 150,200 260,100 260,70 150,100; do
    x=${pt%,*}; y=${pt#*,}
    steps="$steps m:$((px+x-8)),$((py+y-8)) s:250 m:$((px+x)),$((py+y)) s:250 m:$((px+x+1)),$((py+y+1)) s:250"
  done
  WAYLAND_DISPLAY=w ${FAKEINPUT:?pointer: set FAKEINPUT to the fakeinput binary (stereo-proof-rig/scripts/build-fakeinput.sh)} $steps > $ev/fakeinput.log 2>&1
  sleep 1
fi
p=$(sed -n "s/.*parent=\(0x[0-9a-f]*\).*/\1/p" $ev/app.log | head -1)
xwininfo -id $p > $ev/parent-wininfo.txt 2>&1
kill $ap $kp; wait $ap $kp 2>/dev/null' _
rm -rf "$XDG_RUNTIME_DIR"
