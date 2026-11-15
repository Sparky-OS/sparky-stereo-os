#!/bin/sh
# Starts a private session bus, PipeWire and WirePlumber inside the lane's rig container (never the desktop's).
# Usage inside the container: sh session-start.sh ; then: . $XDG_RUNTIME_DIR/env.sh
set -eu
: "${XDG_RUNTIME_DIR:?}" "${HOME:?}"
mkdir -p "$XDG_RUNTIME_DIR" "$XDG_STATE_HOME" "$XDG_CONFIG_HOME"
chmod 700 "$XDG_RUNTIME_DIR"
if [ ! -f "$XDG_RUNTIME_DIR/env.sh" ]; then
	addr=$(dbus-daemon --session --fork --print-address --address="unix:path=$XDG_RUNTIME_DIR/bus")
	echo "export DBUS_SESSION_BUS_ADDRESS=$addr" > "$XDG_RUNTIME_DIR/env.sh"
fi
. "$XDG_RUNTIME_DIR/env.sh"
nohup pipewire >"$XDG_RUNTIME_DIR/pipewire.log" 2>&1 &
sleep 1
nohup wireplumber >"$XDG_RUNTIME_DIR/wireplumber.log" 2>&1 &
sleep 3
pw-cli info 0 | head -3
