# scenario-red.sh, sourced by session.sh: upstream's DriveSync in the same session. Sign-in against the stand-in, the tray,
# closing the window, and the strings of the session's language.
post() { curl -s -X POST -H 'Content-Type: application/json' -d "$2" "http://127.0.0.1:8099$1"; }
start_app
python3 /lane/atspi.py wait drivesync button Continue 40 >> "$CASE/atspi.log" 2>&1
python3 /lane/atspi.py tree drivesync > "$CASE/atspi-start.txt" 2>&1
shot start
"$FAKEINPUT" s:500 k:57 s:700 >> "$CASE/fakeinput.log" 2>&1
python3 /lane/atspi.py press drivesync button Continue >> "$CASE/atspi.log" 2>&1
python3 /lane/atspi.py wait drivesync button "~Sign in with Google" 20 >> "$CASE/atspi.log" 2>&1
python3 /lane/atspi.py press drivesync button "~Sign in with Google" >> "$CASE/atspi.log" 2>&1
sleep 25
python3 /lane/atspi.py tree drivesync > "$CASE/atspi-after-signin.txt" 2>&1
shot after-signin
mark "token requests: $(google /log | grep -c '"/token"'), auth requests: $(google /log | grep -c '/o/oauth2/v2/auth')"
python3 /lane/secret-items.py com.rtosta.DriveSync > "$CASE/secrets-after-signin.txt" 2>&1; mark "secrets-after-signin exit $?"
gdbus introspect --session --dest org.kde.StatusNotifierWatcher --object-path /StatusNotifierWatcher --only-properties > "$CASE/tray-red.txt" 2>&1
python3 /lane/atspi.py press drivesync frame "Set up account" >> "$CASE/atspi.log" 2>&1
sleep 5
python3 /lane/atspi.py tree drivesync > "$CASE/atspi-after-close.txt" 2>&1
mark "after closing: app alive $(kill -0 "$APP" 2>/dev/null && echo yes || echo no)"
shot after-close
