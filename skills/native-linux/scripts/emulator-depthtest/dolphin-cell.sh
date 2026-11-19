#!/bin/sh
# cell.sh NAME BACKEND [dolphin options...]: one fresh Stereo KWin session on a virtual output, depthtest.dol in Dolphin.
# Writes /o/NAME.{kwin,app,wl}.log, /o/NAME-shot1..3.png; DOLPHIN selects the binary.
name=$1; backend=$2; shift 2
export XDG_RUNTIME_DIR=/tmp/xdg HOME=/tmp/home
mkdir -p $XDG_RUNTIME_DIR $HOME /tmp/.X11-unix; chmod 1777 /tmp/.X11-unix; chmod 700 $XDG_RUNTIME_DIR
export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
[ -f /etc/xdg/plasma-workspace/env/sparky-stereo-opengl.sh ] && [ "${ENVSCRIPT:-0}" = 1 ] && . /etc/xdg/plasma-workspace/env/sparky-stereo-opengl.sh
out=/o/$name
if [ -n "$SUNK" ]; then mkdir -p $HOME/.config; printf '[StereoDepth]\nSunkLimit=%s\nPoppedLimit=%s\n' "$SUNK" "$POPPED" > $HOME/.config/kwinrc; fi
mkdir -p /tmp/dolphin-user && cp -r /w/userdir/. /tmp/dolphin-user/
[ -n "$UIMAIN" ] && printf '[Analytics]\nEnabled = False\nPermissionAsked = True\n[Interface]\nConfirmStop = False\nUsePanicHandlers = False\n[Display]\nRenderToMain = True\n' > /tmp/dolphin-user/Config/Dolphin.ini
[ -n "$GFXINI" ] && printf '%b' "$GFXINI" > /tmp/dolphin-user/Config/GFX.ini
kwin_wayland --virtual --xwayland --socket=sub --width ${W:-1280} --height ${H:-800} > $out.kwin.log 2>&1 &
kp=$!
i=0; while [ ! -S $XDG_RUNTIME_DIR/sub ] && [ $i -lt 100 ]; do sleep 0.3; i=$((i+1)); done
sleep 3
export DISPLAY=:0 QT_QPA_PLATFORM=xcb; unset WAYLAND_DISPLAY
( ${DOLPHIN:-/usr/games/dolphin-emu} -u /tmp/dolphin-user -e /w/depthtest.dol -v "$backend" "$@" > $out.app.log 2> $out.wl.log; echo "exit $?" > $out.exit.log ) &
ap=$!
sleep ${WAIT1:-25}
ps -eo pid,stat,comm,args | grep -E 'dolphin|kwin|Xwayland' | grep -v grep > $out.ps.log
DISPLAY=:0 sh /w/skill/x11props.sh > $out.x11.log 2>&1
DISPLAY=:0 xprop -root _KDE_NET_WM_STEREO_CONTENT_SUPPORTED >> $out.x11.log 2>&1
for n in 1 2 3; do python3 /w/skill/capture.py $out-shot$n.png > $out.cap$n.json 2>&1; sleep 2; done
kill $ap $kp 2>/dev/null; sleep 1
