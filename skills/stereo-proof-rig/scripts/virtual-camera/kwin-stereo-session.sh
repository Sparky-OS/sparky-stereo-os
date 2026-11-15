#!/bin/sh
# Restart KWin on a virtual output that lists its 3D twins and put it in the side-by-side (half) twin. Usage: kwin-stereo-session.sh [SCALE]
set -eu
. "$XDG_RUNTIME_DIR/env.sh"
unset LD_PRELOAD
kill $(pidof kwin_wayland) 2>/dev/null || true; sleep 1; rm -f "$XDG_RUNTIME_DIR/sub" "$XDG_RUNTIME_DIR/sub.lock"
export KWIN_VIRTUAL_STEREO_MODES=1 KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 LIBGL_ALWAYS_SOFTWARE=1 QT_QPA_PLATFORM=wayland
nohup kwin_wayland --virtual --socket=sub --width 1280 --height 900 >"$XDG_RUNTIME_DIR/kwin.log" 2>&1 &
i=0; while [ ! -S "$XDG_RUNTIME_DIR/sub" ] && [ $i -lt 40 ]; do sleep 0.5; i=$((i+1)); done
export WAYLAND_DISPLAY=sub
kscreen-doctor -o 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | head -30
