#!/bin/bash
# session.sh: inside the row 299 rig image, as the person: one fresh Plasma login (startplasma-wayland on a virtual
# output, KWin on the card the container was given), the stand-in Google service, the stand-in NetworkManager on a
# private system bus, the Secret Service owner the case asks for, a notification monitor, DriveSync, then SCENARIO.
# Env: CASE (results), LANE (this folder, mounted), SKILL (the proof rig's scripts folder), BIN (the DriveSync to run),
#      SECRETS (kwallet | gnome | blocked), SCENARIO (a file of this folder, sourced in the session), W, H.
set -uo pipefail
: "${CASE:?}" "${LANE:?}" "${SKILL:?}" "${BIN:?}" "${SCENARIO:?}"
export HOME=/home/person
find "$HOME" -mindepth 1 -delete 2>/dev/null
mkdir -p "$HOME/.config" "$HOME/.local/share/kwin/scripts" "$CASE/shots"
export XDG_RUNTIME_DIR=/tmp/r$$; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LANG=${LOGIN_LANG:-C.UTF-8}
W=${W:-1600}; H=${H:-900}
# the person's settings: no lock screen in the run, the rig's window logger
kwriteconfig6 --file kwinrc --group Plugins --key splashlogEnabled true
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Timeout 0
cp -r "$SKILL/login-splash/splashlog" "$HOME/.local/share/kwin/scripts/"
# the stand-in Google service (Google's four host names point here through /etc/hosts)
mkdir -p "$CASE/google"
python3 -I /lane/fakegoogle.py /rig/server.crt /rig/server.key "$CASE/google" 443 8099 > "$CASE/google/server.log" 2>&1 &
GOOGLE=$!
# the stand-in NetworkManager on a private system bus
echo "${METERED_AT_START:-unmetered}" > "$XDG_RUNTIME_DIR/metered"
dbus-daemon --config-file=/usr/share/dbus-1/session.conf --address="unix:path=$XDG_RUNTIME_DIR/system_bus" --fork --print-pid > "$XDG_RUNTIME_DIR/system_bus.pid"
export DBUS_SYSTEM_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/system_bus"
python3 -I /lane/fake-nm.py "$XDG_RUNTIME_DIR/metered" > "$CASE/fake-nm.log" 2>&1 &
NM=$!
# KWin on the card the container was given (NVIDIA through CDI); the session's programs keep Mesa's software renderer
mkdir -p "$XDG_RUNTIME_DIR/shim"
cat > "$XDG_RUNTIME_DIR/shim/kwin_wayland" <<SH
#!/bin/sh
exec env -u LIBGL_ALWAYS_SOFTWARE -u __EGL_VENDOR_LIBRARY_FILENAMES /usr/bin/kwin_wayland "\$@" --virtual --output-count 1 --width $W --height $H
SH
chmod +x "$XDG_RUNTIME_DIR/shim/kwin_wayland"
# SECRETS=blocked: no Secret Service at all (the person's own activation file shadows the system's and fails)
if [ "${SECRETS:-}" = blocked ]; then
	mkdir -p "$HOME/.local/share/dbus-1/services"
	printf '[D-BUS Service]\nName=org.freedesktop.secrets\nExec=/bin/false\n' > "$HOME/.local/share/dbus-1/services/org.freedesktop.secrets.service"
fi
export PATH=$XDG_RUNTIME_DIR/shim:$PATH KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
cat > "$XDG_RUNTIME_DIR/inner.sh" <<'IN'
set -u
mark() { echo "$(date +%s.%N) $*" >> "$CASE/marks.txt"; }
owner() { gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus --method org.freedesktop.DBus.GetNameOwner "$1" 2>/dev/null | tr -d "(',)"; }
exe_of() { local pid; pid=$(gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus --method org.freedesktop.DBus.GetConnectionUnixProcessID "$1" 2>/dev/null | sed -n 's/^(uint32 \([0-9]*\),)$/\1/p'); [ -n "$pid" ] && readlink /proc/$pid/exe; }
shot() { python3 "$SKILL/login-splash/shot.py" Virtual-0 "$CASE/shots/$1.png" >> "$CASE/shots.jsonl" 2>>"$CASE/shot-errors.txt"; }
google() { curl -s "http://127.0.0.1:8099$1" "${@:2}"; }
wait_for() { local i; for i in $(seq "$2"); do eval "$1" && return 0; sleep 1; done; return 1; }
# the login's own keyring step comes before the session, as PAM runs it at a display manager's login (pam_kwallet5 or
# pam_gnome_keyring); started later, KDE Wallet's ksecretd, activated by the session, already holds the name
case "${SECRETS:-}" in
	kwallet) python3 -I /lane/kwallet-login.py "$CASE/ksecretd.log" > "$CASE/ksecretd.pid"; wait_for '[ -n "$(owner org.freedesktop.secrets)" ]' 20 ;;
	gnome) printf 'rig' | gnome-keyring-daemon --unlock --components=secrets > "$CASE/gnome-keyring.env" 2>&1; wait_for '[ -n "$(owner org.freedesktop.secrets)" ]' 20 ;;
esac
mark "secrets owner at login: $(owner org.freedesktop.secrets) $(exe_of "$(owner org.freedesktop.secrets)")"
mark login
setsid startplasma-wayland > "$CASE/session.log" 2>&1 & SP=$!
wait_for '[ -n "$(owner org.kde.StatusNotifierWatcher)" ] && [ -n "$(owner org.kde.plasmashell)" ]' 90 && mark "plasma up" || mark "plasma NOT up"
sleep 4
dbus-monitor --session "type='method_call',interface='org.freedesktop.Notifications',member='Notify'" > "$CASE/notifications.txt" 2>&1 & MON=$!
mark "secrets owner before DriveSync: $(owner org.freedesktop.secrets) $(exe_of "$(owner org.freedesktop.secrets)")"
start_app() {
	mark "start $BIN"
	local oauth=(); [ "${OAUTH_ENV:-1}" = 1 ] && oauth=(DRIVESYNC_GOOGLE_OAUTH_FILE=/case/oauth.json)
	env WAYLAND_DISPLAY=wayland-0 GDK_BACKEND=wayland GSK_RENDERER=cairo XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true \
		KDE_SESSION_VERSION=6 RIG_BROWSER_LOG=/case/browser.log "${oauth[@]}" \
		setsid "$BIN" "$@" >> "$CASE/app.log" 2>&1 &
	APP=$!
}
stop_app() { kill -TERM "$APP" 2>/dev/null; for i in $(seq 20); do kill -0 "$APP" 2>/dev/null || break; sleep 0.5; done; kill -KILL "$APP" 2>/dev/null; mark "stopped app"; }
. "$LANE/$SCENARIO"
mark "secrets owner at end: $(owner org.freedesktop.secrets) $(exe_of "$(owner org.freedesktop.secrets)")"
google /log > "$CASE/google/requests.json"
google /tree > "$CASE/google/tree.json"
kill "$MON" 2>/dev/null
stop_app
kill -TERM "$SP"; sleep 3
IN
export CASE LANE SKILL BIN SECRETS OAUTH_ENV
status=0
dbus-run-session -- bash "$XDG_RUNTIME_DIR/inner.sh" || status=$?
kill "$GOOGLE" "$NM" 2>/dev/null
kill "$(cat "$XDG_RUNTIME_DIR/system_bus.pid" | head -1)" 2>/dev/null
rm -rf "$XDG_RUNTIME_DIR"
exit "$status"
