# scenario-full.sh, sourced by session.sh inside the session: DriveSync against the stand-in Google service.
# PHASES (words, in order of use): signin sync conflict quota refresh metered tray places; default all of them.
PHASES=${PHASES:-signin sync conflict quota refresh metered tray places}
has() { case " $PHASES " in *" $1 "*) return 0 ;; esac; return 1; }
post() { curl -s -X POST -H 'Content-Type: application/json' -d "$2" "http://127.0.0.1:8099$1"; }
step() { mark "STEP $*"; }
atspi() { python3 /lane/atspi.py "$@" >> "$CASE/atspi.log" 2>&1; }
secrets() { python3 /lane/secret-items.py com.rtosta.DriveSync > "$CASE/secrets-$1.txt" 2>&1; mark "secrets-$1 exit $?"; }
requests_since() { google /log | python3 -I -c "import json,sys; t=float(sys.argv[1]); print(sum(1 for r in json.load(sys.stdin) if r['t']>=t and r['path'].startswith(sys.argv[2])))" "$1" "$2"; }
notified() { grep -c -F "$1" "$CASE/notifications.txt" 2>/dev/null; }
wait_notified() { local i; for i in $(seq "$2"); do [ "$(notified "$1")" -gt 0 ] && { mark "notified: $1"; return 0; }; sleep 1; done; mark "NOT notified within $2 s: $1"; return 1; }
tray() {
	{
		gdbus introspect --session --dest org.kde.StatusNotifierWatcher --object-path /StatusNotifierWatcher --only-properties
		for item in $(gdbus call --session --dest org.kde.StatusNotifierWatcher --object-path /StatusNotifierWatcher --method org.freedesktop.DBus.Properties.Get org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems | grep -o "org.kde.StatusNotifierItem-[0-9]*-[0-9]*"); do
			echo "== $item"
			for p in Id Title Status IconName OverlayIconName ToolTip Menu; do
				printf '%s: ' "$p"; gdbus call --session --dest "$item" --object-path /StatusNotifierItem --method org.freedesktop.DBus.Properties.Get org.kde.StatusNotifierItem "$p"
			done
			printf 'menu: '; gdbus call --session --dest "$item" --object-path /MenuBar --method com.canonical.dbusmenu.GetLayout 0 -1 '[]'
		done
	} > "$CASE/tray-$1.txt" 2>&1
}
item_name() { gdbus call --session --dest org.kde.StatusNotifierWatcher --object-path /StatusNotifierWatcher --method org.freedesktop.DBus.Properties.Get org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems | grep -o "org.kde.StatusNotifierItem-[0-9]*-[0-9]*" | head -1; }
app_alive() { kill -0 "$APP" 2>/dev/null; }
window_showing() { python3 /lane/atspi.py wait drivesync frame "$1" 3 >/dev/null 2>&1; }

post /ttl "{\"seconds\": ${TOKEN_TTL:-75}}" > /dev/null
REMOTE=$(post /mkdir '{"name": "Rig Sync"}' | python3 -I -c 'import json,sys; print(json.load(sys.stdin)["id"])')
post /put "{\"name\": \"from-drive.txt\", \"parent\": \"$REMOTE\", \"content\": \"written on Drive\\n\"}" > /dev/null
LOCAL=$HOME/drive-rig
mkdir -p "$LOCAL"; printf 'written on this computer\n' > "$LOCAL/from-computer.txt"
mark "remote folder $REMOTE, local folder $LOCAL"

if has signin; then
	step signin
	start_app
	atspi wait drivesync "check box" "Google Drive" 40 || atspi tree drivesync
	# the provider check box has the window's first keyboard focus; GTK gives it no AT-SPI action, so Space selects it,
	# as a person's keyboard does
	"$FAKEINPUT" s:500 k:57 s:700 >> "$CASE/fakeinput.log" 2>&1
	atspi press drivesync button Continue
	atspi wait drivesync button "~Sign in with Google" 20 || python3 /lane/atspi.py tree drivesync > "$CASE/atspi-signin-tree.txt" 2>&1
	atspi press drivesync button "~Sign in with Google"
	if atspi wait drivesync label "~Account connected" 60; then mark "account connected"; else mark "NO account connected"; python3 /lane/atspi.py tree drivesync > "$CASE/atspi-after-signin.txt" 2>&1; fi
	shot signin
	secrets after-signin
	google /issued > "$CASE/issued-after-signin.json"
	python3 /lane/atspi.py tree drivesync > "$CASE/atspi-after-signin.txt" 2>&1
	stop_app
fi
if has sync; then
	step configure
	ACCOUNT=$(python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(next(iter(d["records"])))' "$HOME/.local/share/drivesync/accounts/accounts.json")
	NAME=$(printf '%s' "$ACCOUNT" | od -An -tx1 | tr -d ' \n')
	mkdir -p "$HOME/.config/drivesync/connections"; chmod 700 "$HOME/.config/drivesync" "$HOME/.config/drivesync/connections"
	printf '[Configuration]\nversion=1\naccount-id=%s\nlocal-uri=file://%s\nremote-id=%s\nremote-path=My Drive / Rig Sync\n' "$ACCOUNT" "$LOCAL" "$REMOTE" > "$HOME/.config/drivesync/connections/$NAME.ini"
	mark "configuration written for account $ACCOUNT"
	step sync
	T0=$(date +%s.%N)
	start_app --background
	for i in $(seq 150); do [ -f "$LOCAL/from-drive.txt" ] && [ "$(requests_since "$T0" /upload/drive)" -gt 0 ] && break; sleep 1; done
	mark "after first sync: local from-drive.txt=$(cat "$LOCAL/from-drive.txt" 2>/dev/null | tr -d '\n'), upload requests=$(requests_since "$T0" /upload/drive)"
	wait_notified 'Google Drive is up to date' 120
	tray after-sync
	shot after-sync
fi
if has conflict; then
	step conflict
	printf 'changed on this computer\n' > "$LOCAL/from-drive.txt"
	post /put "{\"name\": \"from-drive.txt\", \"parent\": \"$REMOTE\", \"content\": \"changed on Drive\\n\"}" > /dev/null
	wait_notified 'A file changed on both sides' 180
	mark "after conflict: local=$(cat "$LOCAL/from-drive.txt" | tr -d '\n'); files: $(ls "$LOCAL" | tr '\n' ' ')"
	tray conflict
	shot conflict
fi
if has quota; then
	step quota
	post /fail-upload '{"name": "quota-refused.bin"}' > /dev/null
	T1=$(date +%s.%N)
	head -c 5000 /dev/urandom > "$LOCAL/quota-refused.bin"
	for i in $(seq 120); do google /log | grep -q '"status": 403' && break; sleep 1; done
	mark "403 answered: $(google /log | grep -c '"status": 403')"
	wait_notified 'Synchronization failed' 120 || wait_notified 'DriveSync needs your decision' 5
	tray quota
	shot quota
fi
if has refresh; then
	step refresh
	for i in $(seq 120); do google /issued | grep -q '"grant": "refresh_token"' && break; sleep 1; done
	google /issued > "$CASE/issued-after-refresh.json"
	secrets after-refresh
fi
if has metered; then
	step metered
	echo metered > "$XDG_RUNTIME_DIR/metered"
	TM=$(date +%s.%N)
	wait_notified 'Synchronization waits' 30
	sleep 5
	printf 'made while metered\n' > "$LOCAL/while-metered.txt"
	sleep 45
	mark "Drive requests while metered: files $(requests_since "$TM" /drive/v3/files) changes $(requests_since "$TM" /drive/v3/changes) uploads $(requests_since "$TM" /upload/)"
	tray metered
	ITEM=$(item_name)
	[ -n "$ITEM" ] && { gdbus call --session --dest "$ITEM" --object-path /MenuBar --method com.canonical.dbusmenu.Event 1 clicked '<0>' 0 >> "$CASE/tray-event.txt" 2>&1; sleep 3; }
	python3 /lane/atspi.py tree drivesync > "$CASE/atspi-metered.txt" 2>&1
	mark "metered banner showing: $(grep -c "label | 'Synchronization waits because the connection is metered.' .* showing" "$CASE/atspi-metered.txt")"
	shot metered
	python3 /lane/atspi.py press drivesync frame DriveSync >> "$CASE/atspi.log" 2>&1; sleep 2
	echo unmetered > "$XDG_RUNTIME_DIR/metered"
	TU=$(date +%s.%N)
	for i in $(seq 150); do [ "$(requests_since "$TU" /upload/)" -gt 0 ] && break; sleep 1; done
	mark "after unmetered: uploads $(requests_since "$TU" /upload/)"
	tray unmetered
fi
if has tray; then
	step tray
	ITEM=$(item_name); mark "tray item: ${ITEM:-none}"
	tray menu
	tray_open() { [ -n "$ITEM" ] && gdbus call --session --dest "$ITEM" --object-path /MenuBar --method com.canonical.dbusmenu.Event 1 clicked '<0>' 0 >> "$CASE/tray-event.txt" 2>&1; sleep 3; }
	tray_open
	mark "after Open from the tray: window showing $(window_showing DriveSync && echo yes || echo no)"
	shot opened-from-tray
	atspi press drivesync frame DriveSync
	sleep 3
	mark "after closing the window: app alive $(app_alive && echo yes || echo no), window showing $(window_showing DriveSync && echo yes || echo no)"
	python3 /lane/atspi.py tree drivesync > "$CASE/atspi-after-close.txt" 2>&1
	shot closed-to-tray
	tray_open
	mark "after Open from the tray again: window showing $(window_showing DriveSync && echo yes || echo no)"
	shot reopened
fi
if has places; then
	step places
	WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland setsid dolphin "$HOME" >> "$CASE/dolphin.log" 2>&1 & D=$!
	sleep 10; kill -TERM "$D" 2>/dev/null; sleep 2
	mark "user-places.xbel before: $([ -f "$HOME/.local/share/user-places.xbel" ] && echo present || echo absent)"
	stop_app; start_app; sleep 12
	atspi press drivesync "toggle button" "Account actions" || atspi press drivesync button "Account actions" || python3 /lane/atspi.py tree drivesync > "$CASE/atspi-places-tree.txt" 2>&1
	sleep 1
	# GTK 4's popover menu items reach AT-SPI without names: the account menu's items in order are Configure folders,
	# Open local folder, Open Google Drive folder, Add local folder to Places, Sign Out (the capture shows the menu)
	shot account-menu
	python3 /lane/atspi.py tree drivesync > "$CASE/atspi-places-menu.txt" 2>&1
	ITEMS=$(grep -c "menu item | '' | \['click'\] | showing" "$CASE/atspi-places-menu.txt")
	mark "account menu items: $ITEMS"
	if [ "$ITEMS" = 5 ]; then atspi press drivesync "menu item" "" 4; else mark "no Places entry in this build's account menu"; fi
	sleep 2
	cp "$HOME/.local/share/user-places.xbel" "$CASE/user-places.xbel" 2>/dev/null
	mark "places entry: $(grep -c "file://$LOCAL" "$HOME/.local/share/user-places.xbel" 2>/dev/null)"
	WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland setsid dolphin "$LOCAL" >> "$CASE/dolphin.log" 2>&1 & D=$!
	sleep 10; shot dolphin-places; kill -TERM "$D" 2>/dev/null
fi
