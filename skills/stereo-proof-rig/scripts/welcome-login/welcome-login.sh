#!/bin/bash
# welcome-login.sh: inside the rig image, as the person, a new account's first login and second login in one home,
# with what opens by itself, captures of each output (both eyes on a 3D output), and the Welcome's pages driven by
# fake input. Adapted from skills/stereo-proof-rig/scripts/login-splash/login.sh (ORDER 571).
# Env: CASE (results folder), MODE (3d or 2d: the output's side by side 3D twin or its plain mode), POPPED, SUNK (the
#      person's kwinrc [StereoDepth] limits, unset = not saved), WAIT (seconds to wait for a first-run window, 45),
#      DRIVE (1: go to the second page, capture it, click its button), BUTTON_AT (x,y of the second page's button,
#      relative to the Welcome window's frame), LOGINS (1 or 2), W, H (output size), RIG (the rig scripts folder).
set -uo pipefail
CASE=${CASE:?}; RIG=${RIG:?}; mkdir -p "$CASE"
# RIG_HOME: the person's home where the image has it, mounted from the case folder by run-case.sh; else a folder of the case
if [ -n "${RIG_HOME:-}" ]; then export HOME=$RIG_HOME; find "$HOME" -mindepth 1 -delete; else export HOME=$CASE/home; rm -rf "$HOME"; fi
mkdir -p "$HOME/.config" "$HOME/.local/share/kwin/scripts"
# SEED_HOME: an account made earlier (a mounted copy of its home), put in place before anything of this run
[ -n "${SEED_HOME:-}" ] && cp -a "$SEED_HOME"/. "$HOME"/
export XDG_RUNTIME_DIR=/tmp/r$$; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LANG=${LOGIN_LANG:-C.UTF-8}
W=${W:-1920}; H=${H:-1080}; MODE=${MODE:-3d}
# 1. the person's saved screen, made the way Display Settings makes it
dbus-run-session -- bash -c '
KWIN_VIRTUAL_STEREO_MODES=1 kwin_wayland --virtual --socket=setup --output-count '"${OUTPUTS:-1}"' --width '"$W"' --height '"$H"' > "$XDG_RUNTIME_DIR/setup.log" 2>&1 & k=$!
for i in $(seq 100); do [ -S "$XDG_RUNTIME_DIR/setup" ] && break; sleep 0.1; done; sleep 1.5
args=($(WAYLAND_DISPLAY=setup kscreen-doctor -j 2>/dev/null | python3 -c "
import json, sys
kind = sys.argv[1]
d = json.load(sys.stdin)
for o in d[\"outputs\"]:
    if kind == \"3d\":
        m = [m for m in o[\"modes\"] if m.get(\"stereo3D\") == 1]
        mode = m[0][\"id\"] if m else None
    else:
        mode = [m for m in o[\"modes\"] if not m.get(\"stereo3D\")][0][\"id\"]
    print(\"output.%s.mode.%s\" % (o[\"name\"], mode))
    if sys.argv[2]:
        print(\"output.%s.scale.%s\" % (o[\"name\"], sys.argv[2]))
" "'"$MODE"'" "'"${SCALE:-}"'"))
echo "${args[@]}" > "'"$CASE"'/setup-args.txt"
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
# 2. the person's own settings, as System Settings writes them; the rig's window logger
[ -n "${POPPED:-}" ] && kwriteconfig6 --file kwinrc --group StereoDepth --key PoppedLimit "$POPPED"
[ -n "${SUNK:-}" ] && kwriteconfig6 --file kwinrc --group StereoDepth --key SunkLimit "$SUNK"
# QUIET_FIRST_RUN=1: an account that has seen both first-run windows (KDE's own record, Sparky Welcome's own mark)
if [ "${QUIET_FIRST_RUN:-0}" = 1 ]; then
	kwriteconfig6 --file plasma-welcomerc --group General --key LastSeenVersion 6.7.4
	mkdir -p "$HOME/.config/autostart"; printf '[Desktop Entry]\nExec=\n' > "$HOME/.config/autostart/sparky-welcome.desktop"
fi
# USER_SETUP: a mounted script run here, as the person, before the first login (an account made earlier, a setting)
[ -n "${USER_SETUP:-}" ] && bash "$USER_SETUP" > "$CASE/user-setup.log" 2>&1
kwriteconfig6 --file kwinrc --group Plugins --key splashlogEnabled true
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Timeout 0
cp -r "$RIG/login-splash/splashlog" "$HOME/.local/share/kwin/scripts/"
cp "$HOME/.config/kwinoutputconfig.json" "$CASE/kwinoutputconfig.json"
# 3. KWin on the virtual output: kwin_wayland_wrapper starts kwin_wayland from PATH and adds its own arguments
mkdir -p "$XDG_RUNTIME_DIR/shim"
cat > "$XDG_RUNTIME_DIR/shim/kwin_wayland" <<SH
#!/bin/sh
# KWin on the card the container was given (NVIDIA through CDI); the session's programs keep Mesa's software renderer
exec env -u LIBGL_ALWAYS_SOFTWARE -u __EGL_VENDOR_LIBRARY_FILENAMES /usr/bin/kwin_wayland "\$@" --virtual --output-count ${OUTPUTS:-1} --width $W --height $H
SH
chmod +x "$XDG_RUNTIME_DIR/shim/kwin_wayland"
# STANDIN_PKEXEC=1: pkexec, which needs polkit and a person's password, is a stand-in that writes what it was asked to run
if [ "${STANDIN_PKEXEC:-0}" = 1 ]; then
	printf '#!/bin/sh\nprintf "%%s\\n" "$*" >> %s/pkexec.txt\n' "$CASE" > "$XDG_RUNTIME_DIR/shim/pkexec"; chmod +x "$XDG_RUNTIME_DIR/shim/pkexec"
fi
export PATH=$XDG_RUNTIME_DIR/shim:$PATH KWIN_VIRTUAL_STEREO_MODES=1 KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
export QT_LOGGING_RULES="org.sparky.stereo*=true;welcome*=true;kf.kio*=false"
cat > "$XDG_RUNTIME_DIR/inner.sh" <<'IN'
set -u
n=$1; L=$CASE/login$n; mkdir -p "$L"
echo "login $(date +%s.%N)" > "$L/marks.txt"
setsid startplasma-wayland > "$L/session.log" 2>&1 & sp=$!
found=""
for i in $(seq $((WAIT * 4))); do
	if grep -q -E 'SPLASHLOG.*ADDED (org.kde.plasma-welcome|plasma-welcome|yad) ' "$L/session.log" 2>/dev/null; then
		found=$(grep -m1 -E -o 'SPLASHLOG.*ADDED (org.kde.plasma-welcome|plasma-welcome|yad) ' "$L/session.log"); echo "first-run-window $(date +%s.%N) $found" >> "$L/marks.txt"; break
	fi
	sleep 0.25
done
# the rest of the WAIT window: a second first-run window may follow the first (both before the change)
sleep "${AFTER:-8}"
python3 "$RIG/kwin_windows.py" "$L/session.log" > "$L/windows-at-login.json" 2>"$L/windows.err"
for o in $OUTS; do python3 "$RIG/login-splash/shot.py" $o "$L/at-login-$o.png" >> "$L/shots.jsonl" 2>>"$L/shot-errors.txt"; done
cp "$L/windows-at-login.json" "$L/windows.json"
if [ -n "${APP_CMD:-}" ] && [ "$n" = 1 ]; then
	# APP_CMD: a program started in the session (its own process group), then the windows and both eyes; APP_STEPS: fake input
	# steps after that, then the windows and the eyes again
	echo "app-start $(date +%s.%N)" >> "$L/marks.txt"
	WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true KDE_SESSION_VERSION=6 \
		setsid bash -c "$APP_CMD" > "$L/app.log" 2>&1 &
	app=$!
	sleep "${APP_WAIT:-12}"
	python3 "$RIG/kwin_windows.py" "$L/session.log" > "$L/windows-app.json" 2>>"$L/windows.err"
	python3 "$RIG/login-splash/shot.py" Virtual-0 "$L/app-Virtual-0.png" >> "$L/shots.jsonl" 2>>"$L/shot-errors.txt"
	if [ -n "${APP_STEPS:-}" ]; then
		"$FAKEINPUT" $APP_STEPS > "$L/fakeinput-app.txt" 2>&1
		python3 "$RIG/kwin_windows.py" "$L/session.log" > "$L/windows-app2.json" 2>>"$L/windows.err"
		python3 "$RIG/login-splash/shot.py" Virtual-0 "$L/app2-Virtual-0.png" >> "$L/shots.jsonl" 2>>"$L/shot-errors.txt"
	fi
	kill -KILL -- -"$app" 2>/dev/null
fi
if [ "${DRIVE:-0}" = 1 ] && [ "$n" = 1 ]; then
	geo=$(python3 -c "
import json, sys
for w in json.load(open('$L/windows-at-login.json'))['windows']:
    if w['cls'] in ('org.kde.plasma-welcome', 'plasma-welcome'):
        print('%d %d %d %d' % tuple(w['fg'])); break
")
	echo "welcome-frame $geo" >> "$L/marks.txt"
	if [ -n "$geo" ]; then
		set -- $geo; cx=$(( $1 + $3 / 2 )); cy=$(( $2 + $4 * 3 / 4 ))
		# a point of the Welcome window that no window above it covers (KWin's stacking order, bottom first)
		free=$(python3 -c "
import json
ws = json.load(open('$L/windows-at-login.json'))['windows']
i = [k for k, w in enumerate(ws) if w['cls'] in ('org.kde.plasma-welcome', 'plasma-welcome')][0]
x, y, w, h = ws[i]['fg']
above = [v['fg'] for v in ws[i + 1:] if v['normal'] and not v['hidden']]
def covered(px, py):
    return any(a <= px < a + c and b <= py < b + d for a, b, c, d in above)
pts = [(x + w // 2 + dx, y + h - 1 - dy) for dy in range(4, h, 4) for dx in (0, -w // 4, w // 4)]
pts += [(x + 2 + dx, y + h // 2) for dx in range(0, w, 4)]
print('%d %d' % next(p for p in pts if not covered(*p)))
")
		echo "pointer-rest $free" >> "$L/marks.txt"
		# the pointer rests there: with focus follows the mouse the Welcome window gets the keys and comes to the front
		# (DelayFocusInterval 300 ms, AutoRaiseInterval 750 ms); then it rests inside the page for the captures
		"$FAKEINPUT" m:$(( ${free% *} - 20 )),${free#* } s:300 m:${free% *},${free#* } s:2000 m:$cx,$cy s:1500 > "$L/fakeinput-rest.txt" 2>&1
		python3 "$RIG/kwin_windows.py" "$L/session.log" > "$L/windows.json" 2>>"$L/windows.err"
		for o in $OUTS; do python3 "$RIG/login-splash/shot.py" $o "$L/page1-$o.png" >> "$L/shots.jsonl" 2>>"$L/shot-errors.txt"; done
		# the mouse's forward button: the next page
		"$FAKEINPUT" m:$cx,$cy s:600 b:276 s:2500 > "$L/fakeinput-next.txt" 2>&1
		python3 "$RIG/kwin_windows.py" "$L/session.log" > "$L/windows-page2.json" 2>>"$L/windows.err"
		for o in $OUTS; do python3 "$RIG/login-splash/shot.py" $o "$L/page2-$o.png" >> "$L/shots.jsonl" 2>>"$L/shot-errors.txt"; done
		if [ -n "${BUTTON_AT:-}" ]; then
			bx=$(( $1 + ${BUTTON_AT%,*} )); by=$(( $2 + ${BUTTON_AT#*,} ))
			echo "button-click $bx,$by $(date +%s.%N)" >> "$L/marks.txt"
			"$FAKEINPUT" m:$bx,$by s:600 b:272 s:6000 > "$L/fakeinput-button.txt" 2>&1
			python3 "$RIG/kwin_windows.py" "$L/session.log" > "$L/windows-after-click.json" 2>>"$L/windows.err"
			for o in $OUTS; do python3 "$RIG/login-splash/shot.py" $o "$L/after-click-$o.png" >> "$L/shots.jsonl" 2>>"$L/shot-errors.txt"; done
		fi
	fi
fi
if [ -n "${MOCK_PAGES:-}" ] && [ "$n" = 1 ]; then
	# the mockups: KDE's Welcome Center showing the named pages (from extra-pages, mounted over the image's folder)
	for p in $(pgrep -x plasma-welcome); do kill -KILL "$p" 2>/dev/null; done; sleep 1
	WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true KDE_SESSION_VERSION=6 \
		plasma-welcome --pages "$MOCK_PAGES" > "$L/mock-welcome.log" 2>&1 &
	sleep 8
	python3 "$RIG/kwin_windows.py" "$L/session.log" > "$L/windows-mock.json" 2>>"$L/windows.err"
	k=1
	for page in $(echo "$MOCK_PAGES" | tr ',' ' '); do
		python3 "$RIG/login-splash/shot.py" Virtual-0 "$L/mock-$k-$page-Virtual-0.png" >> "$L/shots.jsonl" 2>>"$L/shot-errors.txt"
		geo=$(python3 -c "
import json
for w in json.load(open('$L/windows-mock.json'))['windows']:
    if w['cls'] in ('org.kde.plasma-welcome', 'plasma-welcome'):
        print('%d %d' % (w['fg'][0] + w['fg'][2] // 2, w['fg'][1] + w['fg'][3] // 2)); break
")
		[ -n "$geo" ] && "$FAKEINPUT" m:${geo% *},${geo#* } s:600 b:276 s:2500 >> "$L/fakeinput-mock.txt" 2>&1
		k=$((k + 1))
	done
fi
# the catalogues the Welcome Center has open (glibc maps each .mo it reads)
for p in $(pgrep -x plasma-welcome); do grep -o '/usr/share/locale/[^ ]*\.mo' /proc/$p/maps; done 2>/dev/null | sort -u > "$L/catalogue.txt"
cp "$HOME/.config/plasma-welcomerc" "$L/plasma-welcomerc.after" 2>/dev/null || echo "none" > "$L/plasma-welcomerc.after"
ps -eo pid,comm,args > "$L/processes.txt"
# the programs first, then the session: an X11 program left to die with Xwayland would crash (ORDER 39)
for p in $(pgrep -x plasma-welcome) $(pgrep -x yad) $(pgrep -x systemsettings) $(pgrep -x kcmshell6); do kill -KILL "$p" 2>/dev/null; done
kill -TERM $sp; sleep 3
IN
OUTS=$(seq 0 $(( ${OUTPUTS:-1} - 1 )) | sed "s/^/Virtual-/" | tr "\n" " ")
export OUTS CASE WAIT=${WAIT:-45} DRIVE=${DRIVE:-0} BUTTON_AT=${BUTTON_AT:-} RIG FAKEINPUT=${FAKEINPUT:-/tools/fakeinput} APP_CMD=${APP_CMD:-} APP_WAIT=${APP_WAIT:-12} APP_STEPS=${APP_STEPS:-}
status=0
for n in $(seq 1 "${LOGINS:-2}"); do
	dbus-run-session -- bash "$XDG_RUNTIME_DIR/inner.sh" "$n" || status=$?
	sleep 2
done
cp "$HOME/.config/kwinrc" "$CASE/kwinrc" 2>/dev/null
cp -r "$HOME/.config/autostart" "$CASE/autostart-after" 2>/dev/null
rm -rf "$XDG_RUNTIME_DIR"
exit "$status"
