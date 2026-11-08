#!/bin/bash
# Inside the rig image: a session start in the real order. KWin with three virtual outputs whose saved priority order differs from the
# backend's, the person's focus settings in kwinrc, then plasmashell (desktop windows and panels), then an autostart program that maps before any
# pointer motion. A KWin script records activations and the active screen from the first moment.
# Env: PRIOS="2 1 0" (priority per output index), DELAY (seconds after plasmashell is up before the autostart program), SPLASH=1 (ksplashqml first, closed after SPLASH_TAIL seconds, then a second program), KWINRC_EXTRA, NOPLASMA.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:?a folder for session.log, kwin.log and the output configuration}
APP_CMD=${APP_CMD:?the autostart program, a Wayland client, as a command line}
export XDG_RUNTIME_DIR=$HOME/xdg-$$-$RANDOM
mkdir -p "$XDG_RUNTIME_DIR" "$XDG_RUNTIME_DIR/kwin-config" "$XDG_RUNTIME_DIR/kwin-data/kwin/scripts"
chmod 700 "$XDG_RUNTIME_DIR"
unset DISPLAY WAYLAND_DISPLAY
svc=$XDG_RUNTIME_DIR/dbus-services; mkdir -p "$svc"
for f in /usr/share/dbus-1/services/*.service; do
	case $(basename "$f") in
	org.kde.kded6.service | org.kde.runners.baloo.service | org.kde.krunner.service | org.kde.KSplash.service) ;;
	*) ln -sf "$f" "$svc/" ;;
	esac
done
sed "s#<standard_session_servicedirs */>#<servicedir>$svc</servicedir>#" /usr/share/dbus-1/session.conf > "$XDG_RUNTIME_DIR/session.conf"
eval "$(dbus-launch --config-file="$XDG_RUNTIME_DIR/session.conf" --sh-syntax)"
export KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1
cp "${KWINBIN:-/usr/bin/kwin_wayland}" "$XDG_RUNTIME_DIR/kwin_wayland"
KC=$XDG_RUNTIME_DIR/kwin-config
printf '[Daemon]\nAutolock=false\nLockOnResume=false\nTimeout=0\n' > "$KC/kscreenlockerrc"
cp -r "$HERE/startlog" "$XDG_RUNTIME_DIR/kwin-data/kwin/scripts/startlog"
# the person's focus settings (memory defaults-out-of-the-box, window focus; SeparateScreenFocus from the station's kwinrc)
cat > "$KC/kwinrc" <<RC
[Windows]
FocusPolicy=FocusFollowsMouse
DelayFocusInterval=300
AutoRaise=true
AutoRaiseInterval=750
ClickRaise=true
SeparateScreenFocus=true
${KWINRC_EXTRA:-}

[Plugins]
startlogEnabled=true
RC
W=${OW:-1280}; H=${OH:-720}
startkwin() {
	env XDG_CONFIG_HOME="$KC" XDG_DATA_HOME="$XDG_RUNTIME_DIR/kwin-data" XDG_DATA_DIRS="$XDG_RUNTIME_DIR/kwin-data:/usr/local/share:/usr/share" QT_QPA_PLATFORM=offscreen \
		KWIN_VIRTUAL_STEREO_MODES=1 "$XDG_RUNTIME_DIR/kwin_wayland" --virtual --socket=wl-test --output-count ${OUTCOUNT:-3} --width $W --height $H --xwayland > "$XDG_RUNTIME_DIR/kwin-$1.log" 2>&1 &
	kwin=$!
	for _ in $(seq 300); do [ -S "$XDG_RUNTIME_DIR/wl-test" ] && break; sleep 0.2; done
	export WAYLAND_DISPLAY=wl-test
}
# phase 1 makes KWin write its output configuration, then the person's order is put into it (as Display Settings saves it)
startkwin first
for _ in $(seq 100); do wayland-info > /dev/null 2>&1 && break; sleep 0.2; done
sleep 2
kill -TERM $kwin; wait $kwin 2>/dev/null; sleep 2
python3 - "$KC/kwinoutputconfig.json" "${PRIOS:-2 1 0}" <<'PY'
import json, sys
p = sys.argv[1]; prios = [int(x) for x in sys.argv[2].split()]
d = json.load(open(p))
for sec in d:
    if sec["name"] == "setups":
        for setup in sec["data"]:
            for o in setup["outputs"]:
                o["priority"] = prios[o["outputIndex"]]
json.dump(d, open(p, "w"), indent=1)
PY
rm -f "$XDG_RUNTIME_DIR/wl-test" "$XDG_RUNTIME_DIR/wl-test.lock"
# phase 2: the login. KWin first, then plasmashell, then the autostart program
startkwin run
T0=$(date +%s.%N)
for _ in $(seq 100); do wayland-info > /dev/null 2>&1 && break; sleep 0.2; done
echo "SESSION $(date +%s.%N) kwin up (socket)" >> "$OUT/session.log"
if [ -n "${SPLASH:-}" ]; then
	env XDG_CONFIG_HOME="$KC" QT_QPA_PLATFORM=wayland XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true ksplashqml "${SPLASH_THEME:-org.kde.breeze.desktop}" > "$XDG_RUNTIME_DIR/ksplash.log" 2>&1 &
	splash=$!
	echo "SESSION $(date +%s.%N) ksplashqml started" >> "$OUT/session.log"
	sleep "${SPLASH_HEAD:-2}"
fi
if [ -z "${NOPLASMA:-}" ]; then
	PCONF=$XDG_RUNTIME_DIR/plasma-config; PDATA=$XDG_RUNTIME_DIR/plasma-data
	mkdir -p "$PCONF" "$PDATA" "$XDG_RUNTIME_DIR/plasma-cache"
	cp "$KC/kscreenlockerrc" "$PCONF/"
	env XDG_CONFIG_HOME="$PCONF" XDG_DATA_HOME="$PDATA" XDG_CACHE_HOME="$XDG_RUNTIME_DIR/plasma-cache" QT_QPA_PLATFORM=wayland \
		/usr/lib/x86_64-linux-gnu/libexec/kactivitymanagerd > "$XDG_RUNTIME_DIR/kactivities.log" 2>&1 &
	sleep 1
	env XDG_CONFIG_HOME="$PCONF" XDG_DATA_HOME="$PDATA" XDG_CACHE_HOME="$XDG_RUNTIME_DIR/plasma-cache" QT_QPA_PLATFORM=wayland \
		XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true KDE_SESSION_VERSION=6 XDG_SESSION_TYPE=wayland \
		plasmashell > "$XDG_RUNTIME_DIR/plasmashell.log" 2>&1 &
	plasma=$!
	echo "SESSION $(date +%s.%N) plasmashell started" >> "$OUT/session.log"
	for _ in $(seq 300); do dbus-send --session --dest=org.freedesktop.DBus --print-reply /org/freedesktop/DBus org.freedesktop.DBus.NameHasOwner string:org.kde.plasmashell 2>/dev/null | grep -q true && break; sleep 0.2; done
	echo "SESSION $(date +%s.%N) plasmashell on the bus" >> "$OUT/session.log"
fi
sleep "${DELAY:-1}"
echo "SESSION $(date +%s.%N) autostart program starts" >> "$OUT/session.log"
QT_QPA_PLATFORM=${APPPLAT:-wayland} $APP_CMD > "$XDG_RUNTIME_DIR/app1.log" 2>&1 &
if [ -n "${SPLASH:-}" ]; then
	sleep "${SPLASH_TAIL:-3}"
	kill ${splash:-} 2>/dev/null; echo "SESSION $(date +%s.%N) ksplashqml closed" >> "$OUT/session.log"
	sleep 2
	QT_QPA_PLATFORM=${APPPLAT:-wayland} $APP_CMD > "$XDG_RUNTIME_DIR/app2.log" 2>&1 &
	echo "SESSION $(date +%s.%N) second program starts" >> "$OUT/session.log"
fi
sleep "${SETTLE:-8}"
cat > "$XDG_RUNTIME_DIR/d.js" <<'JS'
var out = [];
workspace.windowList().forEach(function (w) { out.push((w.resourceClass||"?") + "|" + w.caption + "|normal=" + w.normalWindow + "|desktop=" + w.desktopWindow + "|dock=" + w.dock + "|out=" + (w.output ? w.output.name : "")); });
print("DUMP " + JSON.stringify({windows: out, outputs: workspace.screens.map(function (o) { return o.name + "@" + o.geometry.x + " prio " + o.priority; }), active: workspace.activeScreen.name, cursor: [workspace.cursorPos.x, workspace.cursorPos.y]}));
JS
r=$(dbus-send --session --print-reply --dest=org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript string:"$XDG_RUNTIME_DIR/d.js" string:dump); sid=${r##* }
dbus-send --session --print-reply --dest=org.kde.KWin /Scripting/Script$sid org.kde.kwin.Script.run > /dev/null
sleep 2
kill ${plasma:-} 2>/dev/null; kill $kwin 2>/dev/null; sleep 1; kill "$DBUS_SESSION_BUS_PID" 2>/dev/null
cp "$XDG_RUNTIME_DIR"/kwin-run.log "$OUT/kwin.log"; cp "$XDG_RUNTIME_DIR/plasmashell.log" "$OUT/" 2>/dev/null; cp "$KC/kwinoutputconfig.json" "$OUT/" 2>/dev/null
rm -rf "$XDG_RUNTIME_DIR"
