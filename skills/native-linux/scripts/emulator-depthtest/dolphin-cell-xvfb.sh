#!/bin/sh
# SPDX-License-Identifier: MIT
# cell-x.sh NAME BACKEND: a desktop without Stereo KWin: a plain X server (Xvfb 1920x1080, no window manager, no
# _KDE_NET_WM_STEREO_CONTENT_SUPPORTED), Dolphin running /w/depthtest.dol. STEREO: 1 (the person turned 3D on in
# GFX.ini), 0 (off), default (nothing written: Dolphin's default). Writes /o/NAME.* : the root picture, the window list.
name=$1; backend=$2
export HOME=/tmp/home XDG_RUNTIME_DIR=/tmp/xdg; mkdir -p $HOME $XDG_RUNTIME_DIR /tmp/.X11-unix; chmod 700 $XDG_RUNTIME_DIR
out=/o/$name
U=/tmp/dolphin-user; mkdir -p $U/Config $U/Logs
printf '[Analytics]\nEnabled = False\nPermissionAsked = True\n[Interface]\nConfirmStop = False\nUsePanicHandlers = False\n[Display]\nRenderToMain = False\n' > $U/Config/Dolphin.ini
case "${STEREO:-default}" in default) : > $U/Config/GFX.ini ;; *) printf '[Stereoscopy]\nStereoMode = %s\n' "$STEREO" > $U/Config/GFX.ini ;; esac
printf '[Logs]\nVIDEO = True\n[Options]\nWriteToFile = True\nWriteToConsole = False\nVerbosity = 3\n' > $U/Config/Logger.ini
Xvfb :0 -screen 0 1920x1080x24 -nolisten tcp > $out.xvfb.log 2>&1 &
xp=$!; sleep 2
export DISPLAY=:0 QT_QPA_PLATFORM=xcb; unset WAYLAND_DISPLAY
( ulimit -c 0; ${DOLPHIN:-/usr/games/dolphin-emu} -u $U -e /w/depthtest.dol -v "$backend" > $out.app.log 2>&1; echo "exit $?" > $out.exit.log ) &
ap=$!
sleep ${WAIT1:-20}
python3 /w/skill/x11_props.py > $out.x11.log 2>&1
xwininfo -root -tree > $out.tree.log 2>&1
python3 - "$out-root.png" <<'PY'
import sys
from Xlib import display, X
from PIL import Image
d = display.Display(); r = d.screen().root; g = r.get_geometry()
raw = r.get_image(0, 0, g.width, g.height, X.ZPixmap, 0xffffffff)
Image.frombytes("RGB", (g.width, g.height), raw.data, "raw", "BGRX").save(sys.argv[1])
print(g.width, g.height)
PY
cp $U/Logs/dolphin.log $out.dolphin.log 2>/dev/null
for p in $(pgrep -x dolphin-emu); do kill -9 $p; done; sleep 1; kill $ap $xp 2>/dev/null; sleep 1; true
