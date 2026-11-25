#!/bin/bash
# page-clicks.sh: inside a rig session (welcome-login.sh's APP_CMD), real clicks on the buttons and links of the Welcome
# Center's new pages, each page opened with plasma-welcome --pages, and after each click KWin's windows, the addresses
# the stand-in browser was given ($CASE/urls.txt, m2-setup.sh) and the commands the stand-in pkexec was asked to run
# ($CASE/pkexec.txt, STANDIN_PKEXEC=1). CLICKS names the clicks: "PAGE:NAME:X,Y ..." with X,Y relative to the Welcome
# window's frame; a calibrate run (CLICKS unset) captures each page for reading them.
# Env: CASE, RIG, FAKEINPUT, PAGES (comma list), CLICKS.
set -u
LOG=$CASE/login1/session.log; OUT=$CASE/clicks; mkdir -p "$OUT"
win() { python3 /lane/kwin-windows-icons.py "$LOG" > "$OUT/$1.json" 2>>"$OUT/errors.txt"; }
shot() { python3 "$RIG/login-splash/shot.py" Virtual-0 "$OUT/$1.png" >> "$OUT/shots.jsonl" 2>>"$OUT/errors.txt"; }
frame() { python3 -c "
import json
for w in json.load(open('$OUT/$1.json'))['windows'] or []:
    if w['cls'] == 'org.kde.plasma-welcome':
        print(*[int(v) for v in w['fg']]); break
"; }
clip() { python3 -c "
import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib
try:
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    r = bus.call_sync('org.kde.klipper', '/klipper', 'org.kde.klipper.klipper', 'getClipboardContents', None, GLib.VariantType('(s)'), Gio.DBusCallFlags.NONE, 3000, None)
    print(r.unpack()[0].replace(chr(10), ' / ')[:160])
except Exception as e:
    print('unreadable: %s' % e)
"; }
closeall() { for n in plasma-welcome yad systemsettings kcmshell6; do for p in $(pgrep -x $n); do kill -TERM "$p"; done; done; sleep 2; }
for page in $(echo "$PAGES" | tr ',' ' '); do
	closeall
	plasma-welcome --pages "$page" > "$OUT/welcome-$page.log" 2>&1 &
	sleep 7; win "$page-open"; shot "$page-open"
	set -- $(frame "$page-open"); fx=${1:-0}; fy=${2:-0}
	echo "$page frame $*" >> "$OUT/marks.txt"
	for c in ${CLICKS:-}; do
		p=${c%%:*}; rest=${c#*:}; name=${rest%%:*}; at=${rest#*:}
		[ "$p" = "$page" ] || continue
		x=$(( fx + ${at%,*} )); y=$(( fy + ${at#*,} ))
		before=$(cat "$CASE/urls.txt" 2>/dev/null | wc -l); pbefore=$(cat "$CASE/pkexec.txt" 2>/dev/null | wc -l)
		echo "click $page $name $x,$y $(date +%s.%N)" >> "$OUT/marks.txt"
		"$FAKEINPUT" m:$x,$y s:500 b:272 s:4500 >> "$OUT/fakeinput.txt" 2>&1
		win "$page-$name"; shot "$page-$name"
		url=$(tail -n +$((before + 1)) "$CASE/urls.txt" 2>/dev/null | head -1)
		cmd=$(tail -n +$((pbefore + 1)) "$CASE/pkexec.txt" 2>/dev/null | head -1)
		new=$(python3 -c "
import json
before = {(w['cls'], w['caption']) for w in json.load(open('$OUT/$page-open.json'))['windows'] or []}
after = json.load(open('$OUT/$page-$name.json'))['windows'] or []
print('; '.join('%s|%s' % (w['cls'], w['caption']) for w in after if (w['cls'], w['caption']) not in before and w['normal']))
")
		printf '%s\t%s\turl=%s\tpkexec=%s\twindows=%s\tclipboard=%s\n' "$page" "$name" "$url" "$cmd" "$new" "$(clip)" >> "$OUT/results.tsv"
		# close what the click opened, keep the Welcome window
		# and spsudo with the Upgrade helper (comm sparky-stereo-w), which would ask for the password again
		for n in yad systemsettings kcmshell6 spsudo sparky-stereo-w; do for q in $(pgrep -x $n); do kill -TERM "$q"; done; done; sleep 1.5
	done
done
closeall
