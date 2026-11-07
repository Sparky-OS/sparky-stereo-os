#!/bin/bash
# SPDX-License-Identifier: MIT
# Inside the rig container: remap-inner.sh STEREO(0|1) EVDIR. The raw GLX unmap/remap reproducer (glx-remap-metrics.c):
# the logical (GLX) and native widths must be the same before and after the remap. CTRL_SUPPORT=3 forces the root's
# _KDE_NET_WM_STEREO_CONTENT_SUPPORTED to 3, the old doubling route: the negative control, the widths grow (640/1280 to 1280/2560).
st=$1 ev=$2; mkdir -p "$ev"
HERE=$(cd "$(dirname "$0")" && pwd)
export HOME=$ev/home XDG_RUNTIME_DIR=$(mktemp -d /tmp/rt.XXXXXX) LANG=C.UTF-8; mkdir -p $HOME; chmod 700 $XDG_RUNTIME_DIR
export XDG_CONFIG_HOME=$XDG_RUNTIME_DIR/config; mkdir -p $XDG_CONFIG_HOME
cc -O1 -o $ev/glx-remap-metrics $HERE/glx-remap-metrics.c -lX11 -lGL 2>$ev/cc.log || { cat $ev/cc.log; exit 4; }
export HERE ev st CTRL_SUPPORT
dbus-run-session -- bash -c '
kwin_wayland --virtual --xwayland --socket=w --width 1600 --height 900 > $ev/kwin.log 2>&1 & kp=$!
for i in $(seq 1 120); do test -S $XDG_RUNTIME_DIR/w && ls /tmp/.X11-unix/X* >/dev/null 2>&1 && break; sleep .25; done; sleep 1
export DISPLAY=$(ls /tmp/.X11-unix | sed -n "s/^X/:/p" | head -1)
[ -n "$CTRL_SUPPORT" ] && xprop -root -f _KDE_NET_WM_STEREO_CONTENT_SUPPORTED 32c -set _KDE_NET_WM_STEREO_CONTENT_SUPPORTED $CTRL_SUPPORT
xprop -root _KDE_NET_WM_STEREO_CONTENT_SUPPORTED > $ev/root.txt
env -u WAYLAND_DISPLAY LIBGL_ALWAYS_SOFTWARE=1 __GLX_VENDOR_LIBRARY_NAME=mesa timeout 12 $ev/glx-remap-metrics $st > $ev/app.log 2> $ev/app.err
kill $kp; wait $kp 2>/dev/null' _
rm -rf "$XDG_RUNTIME_DIR"
python3 - "$ev" <<'PY'
import re, sys
ev = sys.argv[1]
rows = [(int(m.group(1)), int(m.group(2)), int(m.group(3))) for m in re.finditer(r"frame=(\d+) glx_width=(\d+) physical_width=(\d+)", open(f"{ev}/app.err").read())]
print(open(f"{ev}/app.log").read().strip())
before = [r for r in rows if r[0] < 10]; after = [r for r in rows if r[0] >= 15]
print("before remap (glx, native):", sorted({(r[1], r[2]) for r in before}))
print("after remap  (glx, native):", sorted({(r[1], r[2]) for r in after}))
ok = bool(before) and bool(after) and {r[1] for r in before} == {r[1] for r in after} and {r[2] for r in before} == {r[2] for r in after}
print("PASS" if ok else "FAIL", "the logical and native widths stay across unmap/remap")
sys.exit(0 if ok else 1)
PY
