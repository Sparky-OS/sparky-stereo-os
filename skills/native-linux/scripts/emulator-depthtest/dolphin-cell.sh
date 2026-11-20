#!/bin/sh
# SPDX-License-Identifier: MIT
# cell.sh NAME BACKEND: one fresh Stereo KWin session on a virtual output (W x H, default 1920x1080) and Dolphin running
# /w/depthtest.dol on BACKEND (OGL, Vulkan, Software Renderer). Settings come from the environment:
#   DOLPHIN (binary, default Debian's), STEREO (0/1), DEPTH, CONV (Dolphin's own values; empty: Dolphin's defaults),
#   SUNK, POPPED (the desktop's limits written to kwinrc; empty: KWin's defaults), MAXIMIZE=1 (KWin maximizes the
#   render window), UIMAIN=1 (render to the main window: the 3D area is a child), FPS=1 (Dolphin's FPS overlay),
#   ENVSCRIPT=1 (the session's OpenGL environment of sparky-stereo-hardware, for the program only), WAIT1 (seconds).
# Writes /o/NAME.*: kwin, app, x11 logs, dolphin.log, three captures with their JSON, ps, exit.
name=$1; backend=$2
export XDG_RUNTIME_DIR=/tmp/xdg HOME=/tmp/home
mkdir -p $XDG_RUNTIME_DIR $HOME/.config /tmp/.X11-unix; chmod 1777 /tmp/.X11-unix; chmod 700 $XDG_RUNTIME_DIR
export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
out=/o/$name
if [ -n "${SUNK:-}" ]; then printf '[StereoDepth]\nSunkLimit=%s\nPoppedLimit=%s\n' "$SUNK" "$POPPED" > $HOME/.config/kwinrc; fi
U=/tmp/dolphin-user; mkdir -p $U/Config $U/Logs
printf '[Analytics]\nEnabled = False\nPermissionAsked = True\n[Interface]\nConfirmStop = False\nUsePanicHandlers = False\n[Display]\nRenderToMain = %s\n' "$([ "${UIMAIN:-0}" = 1 ] && echo True || echo False)" > $U/Config/Dolphin.ini
{ printf '[Stereoscopy]\n'
  [ "${STEREO:-1}" = default ] || printf 'StereoMode = %s\n' "${STEREO:-1}"
  [ -n "${DEPTH:-}" ] && printf 'StereoDepth = %s\n' "$DEPTH"
  [ -n "${CONV:-}" ] && printf 'StereoConvergence = %s\n' "$CONV"
  [ "${FPS:-0}" = 1 ] && printf '[Settings]\nShowFPS = True\n'
  true; } > $U/Config/GFX.ini
printf '[Logs]\nVIDEO = True\n[Options]\nWriteToFile = True\nWriteToConsole = False\nVerbosity = 3\n' > $U/Config/Logger.ini
kwin_wayland --virtual --xwayland --socket=sub --width ${W:-1920} --height ${H:-1080} > $out.kwin.log 2>&1 &
kp=$!
i=0; while [ ! -S $XDG_RUNTIME_DIR/sub ] && [ $i -lt 100 ]; do sleep 0.3; i=$((i+1)); done
sleep 3
export DISPLAY=:0 QT_QPA_PLATFORM=xcb; unset WAYLAND_DISPLAY
(
  if [ "${ENVSCRIPT:-0}" = 1 ]; then . /w/nv-env.sh; fi
  env | grep -E '^(__EGL|__GLX|MESA_LOADER|LIBGL_KOPPER|VK_)' > $out.appenv.log
  ulimit -c 0; [ -n "${EM39_TRACE:-}" ] && export EM39_TRACE
  ${DOLPHIN:-/usr/games/dolphin-emu} -u $U -e /w/depthtest.dol -v "$backend" > $out.app.log 2>&1; echo "exit $?" > $out.exit.log
) &
ap=$!
sleep ${WAIT1:-20}
if [ "${MAXIMIZE:-0}" = 1 ]; then
  python3 /w/skill/kwin_script.py x 'for (const w of workspace.windowList()) { if (w.normalWindow && w.caption.indexOf("Dolphin") >= 0 && w.caption.indexOf("|") >= 0) { w.setMaximize(true, true); } }' > $out.kwinscript.log 2>&1
  sleep 6
fi
ps -eo pid,stat,comm,args | grep -E 'dolphin|kwin|Xwayland' | grep -v grep > $out.ps.log
python3 /w/skill/x11_props.py > $out.x11.log 2>&1
for n in 1 2 3; do python3 /w/skill/capture.py $out-shot$n.png > $out.cap$n.json 2>&1; sleep 2; done
dp=$(pgrep -x dolphin-emu | head -1); [ -n "$dp" ] && grep -oE '[^/ ]*libvulkan_[a-z_]*\.so[^ ]*|libVkLayer_[A-Za-z_]*\.so|nvidia_icd|libGLX_[a-z]*\.so[^ ]*|libgallium[^ ]*' /proc/$dp/maps | sort -u > $out.maps.log
cp $U/Logs/dolphin.log $out.dolphin.log 2>/dev/null
# Dolphin first, by SIGKILL (no crash handler, no core), then the compositor: Dolphin dies on a lost X connection
for p in $(pgrep -x dolphin-emu); do kill -9 $p; done; sleep 1; kill $ap $kp 2>/dev/null; sleep 1; kill -9 $kp 2>/dev/null; true
