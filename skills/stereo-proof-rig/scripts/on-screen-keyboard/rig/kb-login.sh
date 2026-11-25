#!/bin/bash
# kb-login.sh: inside the rig image, as the person: one login of a new account on a computer with a touch screen of its own
# (row 71), the session's language, tablet mode as the case sets it, then the typing driver (type-case.py) or another step.
# Adapted from skills/stereo-proof-rig/scripts/welcome-login/welcome-login.sh (ORDER 63/720).
# Env: CASE (results), RIG (the skill's stereo-proof-rig/scripts), LANE (this folder), LOGIN_LANG (xx_YY.UTF-8), LANG_CASE,
#      MODE (2d or 3d: the output's plain mode or its side by side 3D twin), TOUCH_SCREEN (1: the computer has a touch screen
#      and a built-in panel, read by the hardware layer from a sysfs fixture; 0: a desktop without one), TABLET (on or auto:
#      kwinrc [Input] TabletMode as General Behavior writes it), STEP (type, or a script under LANE run in the session),
#      USER_SETUP (a script run as the person before the login), W, H.
set -uo pipefail
CASE=${CASE:?}; RIG=${RIG:?}; LANE=${LANE:?}; mkdir -p "$CASE"
export HOME=${RIG_HOME:-/home/person}; find "$HOME" -mindepth 1 -delete
mkdir -p "$HOME/.config" "$HOME/.local/share/kwin/scripts" "$HOME/.local/share/applications"
export XDG_RUNTIME_DIR=/tmp/r$$; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LANG=${LOGIN_LANG:-C.UTF-8}
W=${W:-1920}; H=${H:-1080}; MODE=${MODE:-2d}
# 1. the person's saved screen, made the way Display Settings makes it
dbus-run-session -- bash -c '
KWIN_VIRTUAL_STEREO_MODES=1 kwin_wayland --virtual --socket=setup --width '"$W"' --height '"$H"' > "$XDG_RUNTIME_DIR/setup.log" 2>&1 & k=$!
for i in $(seq 100); do [ -S "$XDG_RUNTIME_DIR/setup" ] && break; sleep 0.1; done; sleep 1.5
args=($(WAYLAND_DISPLAY=setup kscreen-doctor -j 2>/dev/null | python3 -c "
import json, sys
kind = sys.argv[1]
for o in json.load(sys.stdin)[\"outputs\"]:
    if kind == \"3d\":
        m = [m for m in o[\"modes\"] if m.get(\"stereo3D\") == 1]
        mode = m[0][\"id\"] if m else None
    else:
        mode = [m for m in o[\"modes\"] if not m.get(\"stereo3D\")][0][\"id\"]
    print(\"output.%s.mode.%s\" % (o[\"name\"], mode))
" "'"$MODE"'"))
WAYLAND_DISPLAY=setup kscreen-doctor "${args[@]}" > "$XDG_RUNTIME_DIR/kd.log" 2>&1; sleep 1.5
WAYLAND_DISPLAY=setup kscreen-doctor -o 2>/dev/null | sed "s/\x1b\[[0-9;]*m//g" | grep -E "Output:|Modes|Scale" > "'"$CASE"'/outputs.txt"
kill -TERM $k; wait $k 2>/dev/null'
rm -f "$XDG_RUNTIME_DIR"/setup*
python3 - "$HOME/.config/kwinoutputconfig.json" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p))
for sec in d:
    if sec["name"] == "outputs":
        for o in sec["data"]:
            if o.get("mode", {}).get("flags", 0) & 0x20000:
                o["otherStereoFormats"] = True
json.dump(d, open(p, "w"), indent=1)
PY
# 2. the person's own settings, as System Settings writes them; Kate saves its document every 2 seconds
kwriteconfig6 --file kwinrc --group Input --key TabletMode "${TABLET:-on}"
kwriteconfig6 --file kwinrc --group Plugins --key splashlogEnabled true
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Timeout 0
kwriteconfig6 --file katerc --group "KTextEditor Document" --key "Auto Save" true
kwriteconfig6 --file katerc --group "KTextEditor Document" --key "Auto Save Interval" 2
kwriteconfig6 --file katerc --group General --key "Show welcome view for new window" false
[ -n "${USER_SETUP:-}" ] && bash "$USER_SETUP" > "$CASE/user-setup.log" 2>&1
cp -r "$RIG/login-splash/splashlog" "$HOME/.local/share/kwin/scripts/"
# the rig's own fake input client, granted by KWin as any program is: its desktop entry names the protocol
printf '[Desktop Entry]\nType=Application\nName=rig fake input\nExec=%s\nNoDisplay=true\nX-KDE-Wayland-Interfaces=org_kde_kwin_fake_input\n' "${FAKEINPUT:-/tools/fakeinput}" > "$HOME/.local/share/applications/rig-fakeinput.desktop"
cp "$HOME/.config/kwinoutputconfig.json" "$CASE/kwinoutputconfig.json"
# 3. the computer: a touch screen and a built-in panel (sysfs as the kernel shows them, read by the hardware layer)
SYSFS=$XDG_RUNTIME_DIR/sysfs
input() { d=$SYSFS/class/input/input$1; mkdir -p "$d/capabilities"; echo "$2" > "$d/properties"; echo "$3" > "$d/capabilities/abs"; echo "$4" > "$d/capabilities/key"; echo "$5" > "$d/capabilities/sw"; }
mkdir -p "$SYSFS/class/dmi/id" "$SYSFS/class/drm"; echo 10 > "$SYSFS/class/dmi/id/chassis_type"
input 0 0 0 '402000000 3803078f800d001 feffffdfffefffff fffffffffffffffe' 0
input 1 5 '260800000000003' 'e520 10000 0 0 0 0' 0
if [ "${TOUCH_SCREEN:-1}" = 1 ]; then
	input 2 2 '260800000000003' '400 0 0 0 0 0' 0
	mkdir -p "$SYSFS/class/drm/card0-eDP-1"; echo connected > "$SYSFS/class/drm/card0-eDP-1/status"
else
	mkdir -p "$SYSFS/class/drm/card0-DP-1"; echo connected > "$SYSFS/class/drm/card0-DP-1/status"
fi
SPARKY_STEREO_SYSFS=$SYSFS /usr/lib/sparky-stereo-hardware/has-tablet-mode --why > "$CASE/has-tablet-mode.txt" 2>&1; echo "exit $?" >> "$CASE/has-tablet-mode.txt"
export SPARKY_STEREO_SYSFS=$SYSFS
# 4. KWin on the virtual output, on the card the container was given; a built-in touch screen of its own
mkdir -p "$XDG_RUNTIME_DIR/shim"
cat > "$XDG_RUNTIME_DIR/shim/kwin_wayland" <<SH
#!/bin/sh
exec env -u LIBGL_ALWAYS_SOFTWARE -u __EGL_VENDOR_LIBRARY_FILENAMES /usr/bin/kwin_wayland "\$@" --virtual --width $W --height $H
SH
chmod +x "$XDG_RUNTIME_DIR/shim/kwin_wayland"
[ -n "${SHIM_DIR:-}" ] && cp -a "$SHIM_DIR"/. "$XDG_RUNTIME_DIR/shim/"
export PATH=$XDG_RUNTIME_DIR/shim:$PATH KWIN_VIRTUAL_STEREO_MODES=1 KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1
[ "${TOUCH_SCREEN:-1}" = 1 ] && export KWIN_VIRTUAL_TOUCH_SCREEN=1
export QT_LOGGING_RULES="org.kde.plasma.keyboard*=true;kwin_virtualkeyboard*=true;kf.kio*=false"
cat > "$XDG_RUNTIME_DIR/inner.sh" <<'IN'
set -u
L=$CASE; export SESSION_LOG=$L/session.log
echo "login $(date +%s.%N)" > "$L/marks.txt"
setsid startplasma-wayland > "$SESSION_LOG" 2>&1 & sp=$!
for i in $(seq 240); do
	grep -q -E 'SPLASHLOG.*ADDED plasmashell .*desktop=true' "$SESSION_LOG" 2>/dev/null && break
	sleep 0.25
done
echo "desktop $(date +%s.%N)" >> "$L/marks.txt"
sleep "${SETTLE:-8}"
export WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true KDE_SESSION_VERSION=6
# what the session runs with: plasmashell's environment, KWin's input method setting through that configuration path
ps_pid=$(pgrep -x plasmashell | head -1)
tr '\0' '\n' < /proc/$ps_pid/environ | grep -E '^(XDG_CONFIG_DIRS|LANG|LC_ALL)=' > "$L/session-env.txt" 2>/dev/null
XDG_CONFIG_DIRS=$(sed -n 's/^XDG_CONFIG_DIRS=//p' "$L/session-env.txt") kreadconfig6 --file kwinrc --group Wayland --key InputMethod > "$L/inputmethod.txt" 2>&1
XDG_CONFIG_DIRS=$(sed -n 's/^XDG_CONFIG_DIRS=//p' "$L/session-env.txt") kreadconfig6 --file plasmakeyboardrc --group General --key showWithFcitx --default unset > "$L/showwithfcitx.txt" 2>&1
case "${STEP:-type}" in
type) timeout 240 python3 "$LANE/type-case.py" > "$L/type-case.log" 2>&1 ;;
*) timeout 240 bash "$LANE/$STEP" > "$L/step.log" 2>&1 ;;
esac
ps -eo pid,comm,args > "$L/processes.txt"
for p in $(pgrep -x kate) $(pgrep -x plasma-keyboard); do kill -TERM "$p" 2>/dev/null; done
kill -TERM $sp; sleep 3
IN
export CASE RIG LANE LANG_CASE FAKEINPUT=${FAKEINPUT:-/tools/fakeinput} STEP=${STEP:-type} SETTLE=${SETTLE:-8} TOUCH_KATE=${TOUCH_KATE:-1}
status=0
dbus-run-session -- bash "$XDG_RUNTIME_DIR/inner.sh" || status=$?
cp "$HOME/.config/kwinrc" "$CASE/kwinrc" 2>/dev/null
cp -r "$HOME/.config/fcitx5" "$CASE/fcitx5-config" 2>/dev/null
rm -rf "$XDG_RUNTIME_DIR"
exit "$status"
