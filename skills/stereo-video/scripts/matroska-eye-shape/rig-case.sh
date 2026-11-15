#!/bin/bash
# One rig case of the shape of an eye in a Matroska pair, inside a throwaway container: a fresh Stereo KWin on a virtual output (software rendering),
# one player showing one fixture, ScreenShot2's picture of both eyes, the player's Wayland declarations.
# Usage: rig-case.sh PLAYER FIXTURE.mkv OUTDIR [WAIT_SECONDS]
set -u
PLAYER=$1 FILE=$2 OUT=$3 WAIT=${4:-8}
export OUT WAIT
mkdir -p "$OUT"
export XDG_RUNTIME_DIR=/tmp/xdg-$(id -u); mkdir -p -m 700 "$XDG_RUNTIME_DIR"
# a fresh home for every case: players remember their last file and window
export HOME=$OUT/home XDG_CONFIG_HOME=$OUT/home/.config XDG_DATA_HOME=$OUT/home/.local/share XDG_CACHE_HOME=$OUT/home/.cache
mkdir -p "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_CACHE_HOME"
export LIBGL_ALWAYS_SOFTWARE=1 QT_QUICK_BACKEND= QT_QPA_PLATFORM=wayland
ulimit -c 0
case $PLAYER in
	mpv)    CMD=(mpv --fs --no-osc --osd-level=0 --no-terminal --hwdec=no --gpu-sw --pause "$FILE") ;;
	vlc)    CMD=(vlc-stereo -I qt --fullscreen --no-video-title-show --no-osd --no-qt-privacy-ask --no-qt-video-autoresize "$FILE") ;;
	dragon) CMD=(dragon "$FILE") ;;
	plank)  CMD=(plank-player "$FILE") ;;
	sview)  CMD=(sView --fullscreen --in=video --toShowMenu=off --toShowTopbar=off "$FILE") ;;
	bino)   CMD=(bino "$FILE") ;;
	haruna) CMD=(haruna "$FILE") ;;
	*) echo "unknown player $PLAYER" >&2; exit 2 ;;
esac
dbus-run-session -- bash -c '
	set -u
	KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 kwin_wayland --virtual --xwayland \
		--socket=wrig --width 1920 --height 1080 > "$OUT/kwin.log" 2>&1 &
	kw=$!
	for i in $(seq 100); do [ -S "$XDG_RUNTIME_DIR/wrig" ] && break; sleep 0.1; done
	[ -S "$XDG_RUNTIME_DIR/wrig" ] || { echo "no compositor socket" > "$OUT/error"; kill $kw; exit 1; }
	sleep 1
	DISPLAY=:0 WAYLAND_DISPLAY=wrig WAYLAND_DEBUG=client "$@" > "$OUT/player.log" 2> "$OUT/player.wl" &
	pl=$!
	sleep "$WAIT"
	python3 "${CAPTURE:-/scripts/capture.py}" "$OUT/capture.png" > "$OUT/capture.json" 2> "$OUT/capture.err"
	kill $pl 2>/dev/null; sleep 0.5; kill -9 $pl 2>/dev/null
	kill $kw 2>/dev/null; wait 2>/dev/null
	grep -c "kde_stereo_content.*set_content\|set_content(" "$OUT/player.wl" > "$OUT/declarations" 2>/dev/null || echo 0 > "$OUT/declarations"
	exit 0
' rig-case "${CMD[@]}"
# keep the logs small
for f in player.wl kwin.log player.log; do [ -f "$OUT/$f" ] && tail -c 200000 "$OUT/$f" > "$OUT/$f.t" && mv "$OUT/$f.t" "$OUT/$f"; done
grep -E 'set_content|kde_stereo|wp_viewport.*set_destination|error' "$OUT/player.wl" 2>/dev/null | head -40 > "$OUT/declarations.txt"
grep -v -E '^\[[0-9:. ]+\]' "$OUT/player.wl" 2>/dev/null | tail -60 > "$OUT/player.err"
rm -f "$OUT/player.wl"
rm -rf "$OUT/home"
exit 0
