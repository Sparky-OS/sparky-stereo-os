#!/bin/bash
# session.sh: inside the rig image, as the person: a virtual Stereo KWin, the session's ksystemstats (on the station's
# own sysfs, or on a recorded machine through umockdev), the login hook of sparky-stereo-systemmonitor, then System
# Monitor; captures the screen, reads every label through AT-SPI, lists ksystemstats' sensors and keeps the pages and
# the person's systemmonitorrc. Queue row 182.
# Env: CASE (results folder), MACHINE (live, or a umockdev-record file), LOGIN_LANG (en_US.UTF-8, pt_BR.UTF-8 ...),
#      HOOK (1: run the login hook before System Monitor; 0: published state, no hook), STARTS (System Monitor starts,
#      1 or 2), BETWEEN (a script run as the person between two starts), SEED (a script run before the hook), WAIT.
set -uo pipefail
CASE=${CASE:?}; mkdir -p "$CASE"
# RIG_HOME: a fresh account's own home (the bench); else a new home inside the case
if [ -n "${RIG_HOME:-}" ]; then export HOME=$RIG_HOME; else export HOME=$CASE/home; rm -rf "$HOME"; fi; mkdir -p "$HOME/.config"
export RIG_DIR=${RIG_DIR:-/rig} RIGS_DIR=${RIGS_DIR:-/rigs} FAKEINPUT=${FAKEINPUT:-/rig/bin/fakeinput}
[ -n "${SEED_HOME:-}" ] && cp -a "$SEED_HOME"/. "$HOME"/
export XDG_RUNTIME_DIR=/tmp/r$$; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LANG=${LOGIN_LANG:-en_US.UTF-8} LANGUAGE= LC_ALL=
export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
# INSTALLED=1: the installed package, its hook being the autostart entry's own Exec line; else the source at /pkg
if [ "${INSTALLED:-0}" = 1 ]; then
	export HOOK_CMD=$(sed -n 's/^Exec=//p' /etc/xdg/autostart/sparky-stereo-systemmonitor-pages.desktop)
	export EXPLAIN_CMD="/usr/libexec/sparky-stereo-systemmonitor/overview-pages --explain"
else
	export SPARKY_STEREO_SYSTEMMONITOR_DATA=/pkg
	export HOOK_CMD="python3 -I /pkg/bin/overview-pages --login" EXPLAIN_CMD="python3 -I /pkg/bin/overview-pages --explain"
fi
ulimit -c 1 2>/dev/null
cat > "$XDG_RUNTIME_DIR/inner.sh" <<'IN'
set -u
under() { if [ "$MACHINE" = live ]; then "$@"; else umockdev-run --device "$MACHINE" -- "$@"; fi; }
echo "start $(date +%s.%N)" > "$CASE/marks.txt"
kwin_wayland --virtual --socket=sm --width 1920 --height 1200 > "$CASE/kwin.log" 2>&1 & kw=$!
for i in $(seq 100); do [ -S "$XDG_RUNTIME_DIR/sm" ] && break; sleep 0.1; done
/usr/libexec/at-spi-bus-launcher --launch-immediately > "$CASE/atspi.log" 2>&1 & ab=$!
# --remain: ksystemstats quits when its last client disconnects (src/main.cpp), and D-Bus would then start a plain one
under ksystemstats --remain > "$CASE/ksystemstats.log" 2>&1 & ks=$!
for i in $(seq 100); do gdbus call --session -d org.freedesktop.DBus -o /org/freedesktop/DBus -m org.freedesktop.DBus.NameHasOwner org.kde.ksystemstats1 2>/dev/null | grep -q true && break; sleep 0.1; done
sleep 2
kstatsviewer --list 2>/dev/null | grep -E '^(gpu|memory|cpu/(all|cpu[0-9]+)/usage)' > "$CASE/sensors.txt"
ids=$(grep -o -E '^gpu/gpu[0-9]+/(name|usage|usedVram|totalVram|temperature|power1?)\b' "$CASE/sensors.txt" | sort -u)
[ -n "$ids" ] && timeout 8 kstatsviewer --details $ids > "$CASE/sensor-values.txt" 2>/dev/null
[ -n "${SEED:-}" ] && bash "$SEED" > "$CASE/seed.log" 2>&1
if [ "${HOOK:-1}" = 1 ]; then
	echo "hook: $HOOK_CMD" > "$CASE/hook.txt"
	under $EXPLAIN_CMD > "$CASE/explain.txt" 2>&1
	under $HOOK_CMD >> "$CASE/hook.txt" 2>&1; echo "hook exit $?" >> "$CASE/hook.txt"
fi
for n in $(seq "${STARTS:-1}"); do
	S=$CASE/start$n; mkdir -p "$S"
	WAYLAND_DISPLAY=sm QT_QPA_PLATFORM=wayland XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true KDE_SESSION_VERSION=6 \
		QT_QUICK_CONTROLS_STYLE=org.kde.desktop QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 LIBGL_ALWAYS_SOFTWARE=1 \
		setsid plasma-systemmonitor ${APP_ARGS:-} > "$S/app.log" 2>&1 & app=$!
	sleep 6
	python3 "$RIGS_DIR/kwin_script.py" x 'for (const w of workspace.windowList()) { if (w.resourceClass.indexOf("systemmonitor") >= 0) { w.setMaximize(true, true); } }' 2>> "$S/errors.txt"
	sleep "${WAIT:-14}"
	python3 "$RIGS_DIR/capture.py" "$S/screen.png" > "$S/capture.json" 2>> "$S/errors.txt"
	python3 "$RIG_DIR/atspi_dump.py" plasma-systemmonitor "$S/atspi.json" > "$S/atspi.txt" 2>> "$S/errors.txt"
	# which ksystemstats served the page: every process, whether umockdev is preloaded in it, gpu0's name now
	for p in $(ps -eo pid,comm | awk '$2=="ksystemstats" {print $1}'); do echo "pid $p ppid $(ps -o ppid= -p $p) umockdev $(tr '\0' '\n' < /proc/$p/environ 2>/dev/null | grep -c umockdev)"; done > "$S/ksystemstats-ps.txt"
	timeout 4 kstatsviewer gpu/gpu0/name >> "$S/ksystemstats-ps.txt" 2>/dev/null
	[ -n "${ACT:-}" ] && [ "$n" = 1 ] && { case "$ACT" in *.sh) bash "$ACT" "$S" ;; *) python3 "$ACT" "$S" ;; esac > "$S/act.txt" 2>&1; sleep 2; }
	kill -TERM "$app" 2>/dev/null; wait "$app" 2>/dev/null
	cp "$HOME/.config/systemmonitorrc" "$S/systemmonitorrc" 2>/dev/null
	[ -n "${BETWEEN:-}" ] && [ "$n" = 1 ] && bash "$BETWEEN" > "$S/between.log" 2>&1
done
mkdir -p "$CASE/pages"; cp "$HOME"/.local/share/plasma-systemmonitor/*.page "$CASE/pages/" 2>/dev/null
cp "$HOME/.config/systemmonitorrc" "$CASE/systemmonitorrc.end" 2>/dev/null
cp -r "$HOME/.local/state/sparky-stereo-systemmonitor" "$CASE/state" 2>/dev/null
kill -TERM $ks $ab $kw 2>/dev/null; wait 2>/dev/null
IN
dbus-run-session -- bash "$XDG_RUNTIME_DIR/inner.sh"
rm -rf "$XDG_RUNTIME_DIR"
