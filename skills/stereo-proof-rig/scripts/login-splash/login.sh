#!/bin/bash
# SPDX-License-Identifier: MIT
# Inside the rig image, as the person: a real startplasma-wayland login on virtual outputs, with the loading screen captured.
# Env: CASE (folder for the results), OUTPUTS (count, default 1), MODES ("3d 2d": per output, 3d = the side by side 3D twin, 2d = the plain mode),
#      SCALE (output scale, default 1), POPPED, SUNK (the person's kwinrc [StereoDepth] limits, unset = not saved),
#      LOGIN_LANG (session locale, default C.UTF-8; must be generated in the image),
#      CONFIG_SEED (home tree to copy before setup, for a saved-choice or upgrade login),
#      KSPLASHRC (the person's own ~/.config/ksplashrc, unset = none), SHOTS ("1.5 4": seconds after the first splash window to capture),
#      W, H (output size), SETTLE (seconds after the splash ends), NOSHOT (timing run only).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
export HERE
CASE=${CASE:?}; mkdir -p "$CASE"
export HOME=$CASE/home; rm -rf "$HOME"; mkdir -p "$HOME/.config" "$HOME/.local/share/kwin/scripts"
if [ -n "${CONFIG_SEED:-}" ]; then
	cp -r "$CONFIG_SEED"/. "$HOME"/
fi
export XDG_RUNTIME_DIR=/tmp/r$$; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LANG=${LOGIN_LANG:-C.UTF-8}
N=${OUTPUTS:-1}; W=${W:-1920}; H=${H:-1080}
read -r -a MODEA <<< "${MODES:-3d}"
# 1. the person's saved screens, made the way Display Settings makes them
dbus-run-session -- bash -c '
KWIN_VIRTUAL_STEREO_MODES=1 kwin_wayland --virtual --socket=setup --output-count '"$N"' --width '"$W"' --height '"$H"' > "$XDG_RUNTIME_DIR/setup.log" 2>&1 & k=$!
for i in $(seq 100); do [ -S "$XDG_RUNTIME_DIR/setup" ] && break; sleep 0.1; done; sleep 1.5
args=($(WAYLAND_DISPLAY=setup kscreen-doctor -j 2>/dev/null | python3 -c "
import json, sys
want = sys.argv[1].split(); scale = sys.argv[2]
d = json.load(sys.stdin)
for o in sorted(d[\"outputs\"], key=lambda o: o[\"name\"]):
    i = int(o[\"name\"].split(\"-\")[1]); kind = want[i] if i < len(want) else \"2d\"
    if kind == \"3d\":
        m = [m for m in o[\"modes\"] if m.get(\"stereo3D\") == 1]
        mode = m[0][\"id\"] if m else None
    else:
        mode = [m for m in o[\"modes\"] if not m.get(\"stereo3D\")][0][\"id\"]
    print(\"output.%s.mode.%s\" % (o[\"name\"], mode))
    if scale != \"1\": print(\"output.%s.scale.%s\" % (o[\"name\"], scale))
" "'"${MODEA[*]}"'" "'"${SCALE:-1}"'"))
echo "${args[@]}" > "'"$CASE"'/setup-args.txt"
WAYLAND_DISPLAY=setup kscreen-doctor "${args[@]}" > "$XDG_RUNTIME_DIR/kd.log" 2>&1; sleep 1.5
WAYLAND_DISPLAY=setup kscreen-doctor -o 2>/dev/null | sed "s/\x1b\[[0-9;]*m//g" | grep -E "Output:|Modes|Scale" > "'"$CASE"'/outputs.txt"
kill -TERM $k; wait $k 2>/dev/null' 
rm -f "$XDG_RUNTIME_DIR"/setup*
# Display Settings saves a hand-switched 3D twin with the output's "Other stereo formats" switch on; KWin restores the twin
# only then (outputconfigurationstore.cpp, canRestoreVirtualMode). kscreen-doctor sets the mode but not the switch.
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
# 2. the person's own settings
[ -n "${POPPED:-}" ] && kwriteconfig6 --file kwinrc --group StereoDepth --key PoppedLimit "$POPPED"
[ -n "${SUNK:-}" ] && kwriteconfig6 --file kwinrc --group StereoDepth --key SunkLimit "$SUNK"
kwriteconfig6 --file kwinrc --group Plugins --key splashlogEnabled true
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
[ -n "${KSPLASHRC+x}" ] && printf '%b' "$KSPLASHRC" > "$HOME/.config/ksplashrc"
cp -r "$HERE/splashlog" "$HOME/.local/share/kwin/scripts/"
# capture cases only: the desktop comes HOLD seconds later, so the loading screen stays up to be captured (the person's
# autostart folder overrides the system's entry of the same name); timing cases run without it
if [ -n "${HOLD:-}" ]; then
	mkdir -p "$HOME/.config/autostart"
	sed "s#^Exec=.*#Exec=sh -c 'sleep $HOLD; exec /usr/bin/plasmashell'#" /etc/xdg/autostart/org.kde.plasmashell.desktop > "$HOME/.config/autostart/org.kde.plasmashell.desktop"
fi
# 3. KWin on the virtual outputs: kwin_wayland_wrapper starts kwin_wayland from PATH and adds its own arguments
mkdir -p "$XDG_RUNTIME_DIR/shim"
cat > "$XDG_RUNTIME_DIR/shim/kwin_wayland" <<SH
#!/bin/sh
exec /usr/bin/kwin_wayland "\$@" --virtual --output-count $N --width $W --height $H
SH
chmod +x "$XDG_RUNTIME_DIR/shim/kwin_wayland"
export PATH=$XDG_RUNTIME_DIR/shim:$PATH KWIN_VIRTUAL_STEREO_MODES=1 KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
export QT_LOGGING_RULES="org.kde.plasma.ksplashqml.debug=true;org.sparky.stereo*=true"
# 4. the login
cat > "$XDG_RUNTIME_DIR/inner.sh" <<'IN'
set -u
T0=$(date +%s.%N); echo "login $T0" > "$CASE/marks.txt"
startplasma-wayland > "$CASE/session.log" 2>&1 & sp=$!
first=""
if [ "${EXPECT_NO_SPLASH:-0}" = 1 ]; then
    sleep 4
    if grep -q 'SPLASHLOG.*ADDED ksplashqml' "$CASE/session.log"; then
        echo "FAIL: splash mapped with None selected" > "$CASE/no-splash.txt"
        kill -TERM $sp
        exit 1
    fi
    echo "PASS: no splash mapped with None selected" > "$CASE/no-splash.txt"
else
for i in $(seq 600); do
	if [ -z "$first" ] && grep -q 'SPLASHLOG.*ADDED ksplashqml' "$CASE/session.log" 2>/dev/null; then first=$(date +%s.%N); echo "splash-mapped $first" >> "$CASE/marks.txt"; break; fi
	sleep 0.05
done
fi
kp=$(pgrep kwin_wayland | tail -1); [ -n "$kp" ] && tr '\0' '\n' < /proc/$kp/environ | grep -E '^KWIN_' > "$CASE/kwin-env.txt"
WAYLAND_DISPLAY=wayland-0 kscreen-doctor -o 2>/dev/null | sed "s/\x1b\[[0-9;]*m//g" | grep -E "Output:|Modes|Scale" > "$CASE/outputs-login.txt"
if [ -n "$first" ] && [ -z "${NOSHOT:-}" ]; then
	for s in ${SHOTS:-1.5 4}; do
		sleep_for=$(python3 -c "import time;print(max(0, $first + $s - time.time()))"); sleep "$sleep_for"
		for o in $(seq 0 $((N - 1))); do python3 "$HERE/shot.py" Virtual-$o "$CASE/shot-${s}s-Virtual-$o.png" >> "$CASE/shots.jsonl" 2>>"$CASE/shot-errors.txt"; done
	done
fi
if [ "${EXPECT_NO_SPLASH:-0}" != 1 ]; then
for i in $(seq 1200); do grep -q 'SPLASHLOG.*REMOVED ksplashqml' "$CASE/session.log" && break; sleep 0.05; done
fi
echo "splash-gone $(date +%s.%N)" >> "$CASE/marks.txt"
sleep "${SETTLE:-3}"
for o in $(seq 0 $((N - 1))); do [ -z "${NOSHOT:-}" ] && python3 "$HERE/shot.py" Virtual-$o "$CASE/desktop-Virtual-$o.png" >> "$CASE/shots.jsonl" 2>>"$CASE/shot-errors.txt"; done
if [ -n "${DESKTOP_PROBE:-}" ]; then
    bash "$DESKTOP_PROBE"
    probe_status=$?
    if [ "$probe_status" != 0 ]; then
        kill -TERM $sp
        exit "$probe_status"
    fi
fi
kill -TERM $sp; sleep 2
IN
export HOLD="${HOLD:-}" CASE N SHOTS="${SHOTS:-1.5 4}" SETTLE="${SETTLE:-3}" NOSHOT="${NOSHOT:-}"
login_status=0
dbus-run-session -- bash "$XDG_RUNTIME_DIR/inner.sh" || login_status=$?
grep -E 'SPLASHLOG|ksplashqml|org.sparky.stereo|stereo' "$CASE/session.log" | grep -v '^$' > "$CASE/splash-lines.txt" || true
cp "$HOME/.config/kwinoutputconfig.json" "$CASE/" 2>/dev/null
rm -rf "$XDG_RUNTIME_DIR"
exit "$login_status"
