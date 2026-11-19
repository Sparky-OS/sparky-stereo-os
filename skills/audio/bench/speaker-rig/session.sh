#!/bin/bash
# Starts a private PipeWire, WirePlumber and pipewire-pulse session as the user "rig" and runs the command given.
# session.sh COMMAND [ARG...]  (root inside the rig container prepares /run/user/1001 and calls it through setpriv)
set -u
export XDG_RUNTIME_DIR=/run/user/1001 HOME=/home/rig
mkdir -p "$XDG_RUNTIME_DIR"
cd "$HOME"
cat >/tmp/sp23-inner.sh <<'IN'
set -u
pipewire >/tmp/pipewire.log 2>&1 &
PW=$!
for i in $(seq 50); do [ -S "$XDG_RUNTIME_DIR/pipewire-0" ] && break; sleep 0.2; done
wireplumber >/tmp/wireplumber.log 2>&1 &
WP=$!
pipewire-pulse >/tmp/pipewire-pulse.log 2>&1 &
PP=$!
for i in $(seq 50); do pw-cli ls Node 2>/dev/null | grep -q alsa_output.rig_71 && break; sleep 0.2; done
sleep 1.5
"$@"
rc=$?
kill $WP $PW $PP 2>/dev/null; wait 2>/dev/null
exit $rc
IN
exec dbus-run-session -- bash /tmp/sp23-inner.sh "$@"
