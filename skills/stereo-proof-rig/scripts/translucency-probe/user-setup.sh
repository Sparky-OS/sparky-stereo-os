#!/bin/bash
# USER_SETUP for login.sh: the account as the ISO makes it (lookandfeeltool -a moves the look's values into
# ~/.config/kdedefaults, sparky-os/vm/prepack.sh), then the case's own settings. Env: LOOK (look-and-feel id),
# EXTRA_KWINRC ("group:key=value;..."), PROBE_PANEL (kept for probe.sh).
set -u
if [ -n "${LOOK:-}" ]; then
	rt=$(mktemp -d); chmod 700 "$rt"
	XDG_RUNTIME_DIR=$rt QT_QPA_PLATFORM=offscreen dbus-run-session -- plasma-apply-lookandfeel -a "$LOOK" > "$CASE/apply-look.txt" 2>&1
	echo "apply-look exit $?" >> "$CASE/apply-look.txt"
	rm -rf "$rt"
fi
IFS=';' read -r -a items <<< "${EXTRA_KWINRC:-}"
for it in "${items[@]}"; do
	[ -n "$it" ] || continue
	g=${it%%:*}; kv=${it#*:}; kwriteconfig6 --file kwinrc --group "$g" --key "${kv%%=*}" "${kv#*=}"
done
# blur noise differs per session (skill stereo-pictures, animated-stereo-icons): none, so two sessions compare
kwriteconfig6 --file kwinrc --group Effect-blur --key NoiseStrength 0
mkdir -p "$CASE/config-before"; cp -r "$HOME/.config/kdedefaults" "$CASE/config-before/" 2>/dev/null || true
cp "$HOME/.config/kdeglobals" "$CASE/config-before/" 2>/dev/null || true
