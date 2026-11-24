#!/bin/bash
# One session: Stereo KWin on a virtual output with Xwayland, Xwayland's Wayland connection traced
# (WAYLAND_DEBUG=client is inherited by the Xwayland KWin starts), then one X11 client command.
# Usage: traced-xwayland-session.sh OUT SECONDS CMD [ARGS...]
#   to run another Xwayland binary, bind-mount it over /usr/bin/Xwayland (KWin starts "Xwayland" from PATH); its hash is recorded.
set -uo pipefail
OUT=$1
SECS=$2
shift 2
mkdir -p "$OUT"
export XDG_RUNTIME_DIR=$(mktemp -d /tmp/rt.XXXXXX) HOME=/home/rig
chmod 700 "$XDG_RUNTIME_DIR"
step() { printf '%s %s\n' "$(date -u +%T.%3N)" "$*" >> "$OUT/steps.txt"; }
export XW_REAL=/usr/bin/Xwayland
"$XW_REAL" -version > "$OUT/xwayland-version.txt" 2>&1
sha256sum "$XW_REAL" >> "$OUT/xwayland-version.txt"
echo "XWAYLAND_TEST_IMPLICIT_SYNC=${XWAYLAND_TEST_IMPLICIT_SYNC:-unset}" >> "$OUT/xwayland-version.txt"
WAYLAND_DEBUG=client KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 \
    kwin_wayland --virtual --xwayland --socket=sub --width 1280 --height 800 > "$OUT/kwin.log" 2>&1 &
KWIN=$!
for _ in $(seq 100); do [ -S "$XDG_RUNTIME_DIR/sub" ] && break; sleep 0.1; done
for _ in $(seq 100); do ls /tmp/.X11-unix/X* >/dev/null 2>&1 && break; sleep 0.1; done
DISP=:$(ls /tmp/.X11-unix/ | sed -n 's/^X//p' | sort -n | head -1)
sleep 1
XWPID=$(pidof Xwayland)
step "kwin $KWIN x11 $DISP xwayland $XWPID case $*"
DISPLAY=$DISP WAYLAND_DISPLAY= timeout "$SECS" "$@" > "$OUT/client.txt" 2>&1
echo "client exit $?" >> "$OUT/client.txt"
sleep 1
step "xwayland after: $(pidof Xwayland || echo none) (was $XWPID)"
grep -E 'acquire point|Protocol error|X11 connection broke|XWAYLAND|error 4|glamor|EGL' "$OUT/kwin.log" | grep -v -E 'set_(acquire|release)_point\(|^\[' | head -40 > "$OUT/errors.txt"
grep -c -E 'wp_linux_drm_syncobj_surface_v1#[0-9]+\.set_acquire_point' "$OUT/kwin.log" > "$OUT/acquire-count.txt"
grep -n -E 'wp_linux_drm_syncobj_manager_v1#[0-9]+\.get_surface|wl_surface#[0-9]+\.(attach|commit)\(|set_(acquire|release)_point|wp_linux_drm_syncobj_surface_v1#[0-9]+\.destroy|error 4|delete_id' "$OUT/kwin.log" | tail -80 > "$OUT/sync-trace.txt"
kill "$KWIN" 2>/dev/null
wait "$KWIN" 2>/dev/null
step end
exit 0
