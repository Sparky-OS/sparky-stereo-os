#!/bin/sh
# KWin on a virtual output inside the rig container, with the rig's own session bus, PipeWire and WirePlumber.
# Usage: kwin-session.sh [WIDTH HEIGHT]   (then WAYLAND_DISPLAY=sub). Needs session-start.sh run first, --cap-add SYS_NICE and a render node.
set -eu
. "$XDG_RUNTIME_DIR/env.sh"
unset LD_PRELOAD
export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 LIBGL_ALWAYS_SOFTWARE=1 QT_QPA_PLATFORM=wayland
W=${1:-1280}; H=${2:-900}
nohup kwin_wayland --virtual --socket=sub --width "$W" --height "$H" >"$XDG_RUNTIME_DIR/kwin.log" 2>&1 &
i=0; while [ ! -S "$XDG_RUNTIME_DIR/sub" ] && [ $i -lt 40 ]; do sleep 0.5; i=$((i+1)); done
[ -S "$XDG_RUNTIME_DIR/sub" ] && echo "kwin up" || { tail -5 "$XDG_RUNTIME_DIR/kwin.log"; exit 1; }
