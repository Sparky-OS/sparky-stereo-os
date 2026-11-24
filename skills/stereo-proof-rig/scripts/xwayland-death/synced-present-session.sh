#!/bin/bash
# One session: KWin on a virtual output with Xwayland, Xwayland's Wayland connection traced
# (WAYLAND_DEBUG=client is inherited by the Xwayland KWin starts), then one X11 client case.
# Usage: synced-present-session.sh OUT CASE   CASE: an AFTER of x11-synced-present, with -stereo or -child for its modes,
#   or vkcube-resize (vkcube on the X11 swapchain, resized twice)
set -uo pipefail
OUT=$1
AFTER=$2
mkdir -p "$OUT"
export XDG_RUNTIME_DIR=$(mktemp -d /tmp/rt.XXXXXX) HOME=/home/rig
chmod 700 "$XDG_RUNTIME_DIR"
step() { printf '%s %s\n' "$(date -u +%T.%3N)" "$*" >> "$OUT/steps.txt"; }
Xwayland -version > "$OUT/xwayland-version.txt" 2>&1
sha256sum /usr/bin/Xwayland >> "$OUT/xwayland-version.txt"
WAYLAND_DEBUG=client KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 \
    kwin_wayland --virtual --xwayland --socket=sub --width 1280 --height 800 > "$OUT/kwin.log" 2>&1 &
KWIN=$!
for _ in $(seq 100); do [ -S "$XDG_RUNTIME_DIR/sub" ] && break; sleep 0.1; done
for _ in $(seq 100); do ls /tmp/.X11-unix/X* >/dev/null 2>&1 && break; sleep 0.1; done
DISP=:$(ls /tmp/.X11-unix/ | sed -n 's/^X//p' | sort -n | head -1)
step "kwin $KWIN x11 $DISP case $AFTER"
if [ "$AFTER" = vkcube-resize ]; then
    # a Vulkan swapchain with explicit sync, recreated by two resizes (upstream !2399's trigger)
    DISPLAY=$DISP timeout 12 vkcube --wsi xcb --c 400 > "$OUT/client.txt" 2>&1 &
    VK=$!
    sleep 3
    DISPLAY=$DISP xwininfo -root -tree > "$OUT/xtree.txt" 2>&1
    W=$(awk '/"Vkcube X11"/ {print $1; exit}' "$OUT/xtree.txt")
    echo "window $W" >> "$OUT/client.txt"
    DISPLAY=$DISP xdotool windowsize "$W" 640 480 >> "$OUT/client.txt" 2>&1; sleep 2
    DISPLAY=$DISP xdotool windowsize "$W" 300 200 >> "$OUT/client.txt" 2>&1; sleep 2
    wait $VK; echo "vkcube exit $?" >> "$OUT/client.txt"
elif [ "$AFTER" = vkcube ]; then
    DISPLAY=$DISP timeout 8 vkcube --wsi xcb --c 300 > "$OUT/client.txt" 2>&1
    echo "vkcube exit $?" >> "$OUT/client.txt"
else
    case "$AFTER" in *-stereo|*-child) A=${AFTER%-*} ;; *) A=$AFTER ;; esac
    DISPLAY=$DISP timeout 20 "${RIG_BIN:?the folder with x11-synced-present}/x11-synced-present" 400 300 6 "$A" $(case "$AFTER" in *-stereo) echo stereo ;; *-child) echo child ;; esac) > "$OUT/client.txt" 2>&1
    echo "client exit $?" >> "$OUT/client.txt"
fi
sleep 1
step "xwayland after: $(pidof Xwayland || echo none)"
grep -E 'acquire point|wp_linux_drm_syncobj|Protocol error|X11 connection broke|XWAYLAND|error 4' "$OUT/kwin.log" | grep -v -E 'set_(acquire|release)_point\(' | head -40 > "$OUT/errors.txt"
grep -c -E 'wp_linux_drm_syncobj_surface_v1#[0-9]+\.set_acquire_point' "$OUT/kwin.log" > "$OUT/acquire-count.txt"
grep -n -E 'wp_linux_drm_syncobj_manager_v1#[0-9]+\.get_surface|wl_surface#[0-9]+\.(attach|commit)\(|set_(acquire|release)_point|wp_linux_drm_syncobj_surface_v1#[0-9]+\.destroy' "$OUT/kwin.log" | tail -60 > "$OUT/sync-trace.txt"
kill $KWIN 2>/dev/null
wait $KWIN 2>/dev/null
step end
exit 0
