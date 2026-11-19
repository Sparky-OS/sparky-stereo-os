#!/bin/bash
# Runs in a rig container as root: prepares the fake devices and the engine's choices, then runs the command
# given as the unprivileged user "rig" inside a private PipeWire, WirePlumber and pipewire-pulse session.
# usage: page-run.sh [--proto] [--no-engine] COMMAND...
set -u
ulimit -c 0
PROTO=0 ENGINE=1
while [ $# -gt 0 ]; do case $1 in --proto) PROTO=1; shift;; --no-engine) ENGINE=0; shift;; *) break;; esac; done
mkdir -p /run/sa631 && chmod 777 /run/sa631
mkdir -p /opt/sa631 && cp -r /src/proc-asound /opt/sa631/ 2>/dev/null
export SPARKY_STEREO_AUDIO_PROC=/opt/sa631/proc-asound
if [ $ENGINE = 1 ]; then
  SPARKY_STEREO_AUDIO_CPU_COST=10 sparky-stereo-audio detect --write >/tmp/engine-detect.txt 2>&1
fi
# a systemctl that restarts this private session the way systemd would restart the user's units
cat >/usr/local/bin/systemctl <<'SC'
#!/bin/bash
if [ "$1" = "--user" ] && [ "$2" = "restart" ]; then
  for p in wireplumber pipewire-pulse pipewire; do pkill -x $p 2>/dev/null; done
  sleep 0.5
  export XDG_RUNTIME_DIR=/run/user/1001 HOME=/home/rig
  setsid pipewire >/tmp/pipewire.log 2>&1 </dev/null &
  for i in $(seq 50); do [ -S $XDG_RUNTIME_DIR/pipewire-0 ] && break; sleep 0.1; done
  setsid wireplumber >/tmp/wireplumber.log 2>&1 </dev/null &
  setsid pipewire-pulse >/tmp/pipewire-pulse.log 2>&1 </dev/null &
  exit 0
fi
exit 1
SC
chmod +x /usr/local/bin/systemctl
mkdir -p /run/user/1001 /home/rig/.config && chown -R rig:rig /run/user/1001 /home/rig && chmod 700 /run/user/1001
if [ $PROTO = 1 ]; then
  cp -a /build/dest/usr/. /usr/
fi
# the system bus, polkit and its rule (PG_POLKIT=yes lets the Sound page's action through, no refuses it)
if [ -n "${PG_POLKIT:-}" ]; then
  mkdir -p /run/dbus /etc/polkit-1/rules.d
  rm -f /run/dbus/pid; dbus-daemon --system --fork
  RES=YES; [ "$PG_POLKIT" = no ] && RES=NO
  printf 'polkit.addRule(function(action, subject) { if (action.id.indexOf("org.kde.plasma.pa.soundformats") == 0) return polkit.Result.%s; });\n' $RES >/etc/polkit-1/rules.d/49-page-rig.rules
  /usr/lib/polkit-1/polkitd --no-debug >/tmp/polkitd.log 2>&1 &
  sleep 2
fi
export PATH=/usr/local/bin:$PATH
exec setpriv --reuid 1001 --regid 1001 --clear-groups env HOME=/home/rig XDG_RUNTIME_DIR=/run/user/1001 SA631_PULSE=1 PATH=$PATH SPARKY_STEREO_AUDIO_PROC=$SPARKY_STEREO_AUDIO_PROC QT_PLUGIN_PATH="${QT_PLUGIN_PATH:-}" QML_IMPORT_PATH="${QML_IMPORT_PATH:-}" LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}" XDG_DATA_DIRS="${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" QML_XHR_ALLOW_FILE_READ=1 QT_QPA_PLATFORM=offscreen bash /src/session.sh "$@"
