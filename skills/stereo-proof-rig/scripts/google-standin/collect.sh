#!/bin/bash
# collect.sh CASE_DIR EVIDENCE_DIR [SHOT...]: a case's small evidence into the lane folder.
set -u
C=$1; E=$2; shift 2; mkdir -p "$E"
for f in marks.txt secrets-after-signin.txt secrets-after-refresh.txt issued-after-signin.json issued-after-refresh.json tray-after-sync.txt tray-conflict.txt tray-quota.txt tray-metered.txt tray-menu.txt tray-red.txt user-places.xbel browser.log; do
	[ -f "$C/$f" ] && cp "$C/$f" "$E/"
done
[ -f "$C/notifications.txt" ] && python3 -I "$(dirname "$0")/notifications.py" "$C/notifications.txt" > "$E/notifications.jsonl"
[ -f "$C/google/requests.json" ] && python3 -I -c '
import json, sys
log = json.load(open(sys.argv[1]))
for r in log:
	print("%.3f %s %s %s%s" % (r["t"], r["status"], r["method"], r["host"], r["path"]))
' "$C/google/requests.json" > "$E/requests.txt"
for f in atspi-after-signin.txt atspi-metered.txt atspi-after-close.txt atspi-start.txt; do [ -f "$C/$f" ] && grep -E "label|button|frame|menu" "$C/$f" | grep -v "''" | sed "s/ | \[.*\] | / | /" > "$E/$f"; done
for s in "$@"; do [ -f "$C/shots/$s.png" ] && cp "$C/shots/$s.png" "$E/"; done
grep -h -i "error\|warning\|panicked" "$C/app.log" 2>/dev/null | sort | uniq -c | sort -rn | head -20 > "$E/app-messages.txt"
du -sh "$E" | cut -f1
