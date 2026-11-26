#!/bin/bash
# SPDX-License-Identifier: MIT
# DESKTOP_PROBE for login-splash/login.sh: inside the person's session, after the desktop is up, capture every translucent
# surface over a black and a white wallpaper (and any other wallpaper named), so analyze.py can read each surface's alpha.
# Env: STEPS ("panel notif launcher windows"), PROBE_PANEL ("floating=true;opacity=translucent;height=36", Plasma's
# scripting properties of every panel; empty = as the look made it), WALLS ("NAME=PATH ...", default the rig's black and
# white, made here), EXTRA_WALLS (more wallpapers for the panel step only), CASE. A capture's name says the step and the
# wallpaper (panel-black.png); KWin's frames are saved beside them (win-*.json). Every wait polls what it reads.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
P="python3 $HERE/probe.py"
log() { echo "$(date -u +%H:%M:%S.%N) $*" >> "$CASE/probe.log"; }
fail() { log "FAIL $*"; echo "FAIL $*" >> "$CASE/probe-fail.txt"; }
mkdir -p "$CASE/walls"
python3 -c "
from PIL import Image
for n, c in (('black', 0), ('white', 255)):
    Image.new('RGB', (1920, 1080), (c, c, c)).save('$CASE/walls/' + n + '.png')"
WALLS=${WALLS:-"black=$CASE/walls/black.png white=$CASE/walls/white.png"}
$P waitwin dock dock > "$CASE/win-start.json" 2>>"$CASE/probe.log" || fail "no panel"
$P panels > "$CASE/panels-as-made.json" 2>>"$CASE/probe.log"
if [ -n "${PROBE_PANEL:-}" ]; then
	$P panel "$PROBE_PANEL" > "$CASE/panels-set.json" 2>>"$CASE/probe.log" || fail "panel $PROBE_PANEL"
	$P waitwin dockset dock > "$CASE/win-panel.json" 2>>"$CASE/probe.log" || fail "panel did not settle"
fi
walls() { # walls STEP [MORE]: every wallpaper (and the MORE ones), one capture each
	for nw in $WALLS ${2:-}; do
		n=${nw%%=*}; w=${nw#*=}
		$P wall "$w" >> "$CASE/probe.log" 2>&1 || { fail "wall $n"; continue; }
		$P shot "$1-$n" 2>>"$CASE/probe.log" || fail "shot $1-$n"
		log "shot $1-$n"
	done
}
for step in ${STEPS:-panel notif launcher windows}; do
	case $step in
	panel)
		$P windows panel > "$CASE/win-panel-shots.json" 2>>"$CASE/probe.log"
		walls panel "${EXTRA_WALLS:-}" ;;
	notif)
		id=$($P notify 2>>"$CASE/probe.log") || fail notify
		$P waitwin notif notification > "$CASE/win-notif.json" 2>>"$CASE/probe.log" || fail "no notification window"
		walls notif
		[ -n "${id:-}" ] && $P unnotify "$id" 2>>"$CASE/probe.log" ;;
	launcher)
		# the panel's launcher opens as KWin's window type 18, an applet's pop-up (not a "popupWindow")
		$P launcher 2>>"$CASE/probe.log" || fail launcher
		$P waitwin launch type:18 > "$CASE/win-launcher.json" 2>>"$CASE/probe.log" || fail "no launcher pop-up"
		walls launcher
		$P launcher 2>>"$CASE/probe.log" ;;
	windows)
		# the probe's shell has no Wayland display of its own: name the session's
		QT_QPA_PLATFORM=wayland WAYLAND_DISPLAY=wayland-0 python3 "$HERE/windows.py" > "$CASE/windows.log" 2>&1 & wp=$!
		$P waitwin windows normal 2 > /dev/null 2>>"$CASE/probe.log" || fail "test windows"
		$P place probe-inactive 120 300 420 260; $P place probe-active 700 300 420 260; $P place probe-dialog 1300 340 300 180
		$P activate probe-active
		$P waitwin windowsplaced normal 2 > "$CASE/win-windows.json" 2>>"$CASE/probe.log" || fail "test windows placed"
		walls windows
		kill "$wp" 2>/dev/null; wait "$wp" 2>/dev/null ;;
	esac
done
log "probe done"
