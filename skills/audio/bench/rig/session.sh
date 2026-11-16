#!/bin/bash
# Starts a private PipeWire + WirePlumber session (no PulseAudio server unless asked) and runs the command given.
# Run as the unprivileged user "rig": session.sh COMMAND [ARG...]
set -u
export XDG_RUNTIME_DIR=/run/user/1001 HOME=/home/rig
mkdir -p "$XDG_RUNTIME_DIR"
cd "$HOME"
cat >/tmp/sa631-inner.sh <<'IN'
set -u
pipewire >/tmp/pipewire.log 2>&1 &
PW=$!
for i in $(seq 50); do [ -S "$XDG_RUNTIME_DIR/pipewire-0" ] && break; sleep 0.2; done
wireplumber >/tmp/wireplumber.log 2>&1 &
WP=$!
if [ -n "${SA631_PULSE:-}" ]; then pipewire-pulse >/tmp/pipewire-pulse.log 2>&1 & PP=$!; fi
for i in $(seq 50); do pw-cli ls Node 2>/dev/null | grep -q alsa_output.rig_dac && break; sleep 0.2; done
sleep 1.5
"$@"
rc=$?
kill $WP $PW ${PP:-} 2>/dev/null; wait 2>/dev/null
exit $rc
IN
exec dbus-run-session -- bash /tmp/sa631-inner.sh "$@"
