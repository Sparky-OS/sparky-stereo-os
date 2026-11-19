#!/bin/bash
# Runs in the rig container as root: prepares the devices' folder and a systemctl for the private session, then runs the command
# given as the unprivileged user "rig" in the session.
set -u
ulimit -c 0
mkdir -p /run/sa631 && chmod 777 /run/sa631
cat >/usr/local/bin/systemctl <<'SC'
#!/bin/bash
if [ "$1" = "--user" ] && [ "$2" = "restart" ]; then
  n=$(ls /tmp/pw-*.log 2>/dev/null | wc -l); cp /tmp/pipewire.log /tmp/pw-$n.log 2>/dev/null
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
mkdir -p /run/user/1001 /home/rig/.config
[ -d /ev/pre ] && cp -r /ev/pre/. /home/rig/.config/
chown -R rig:rig /run/user/1001 /home/rig && chmod 700 /run/user/1001
[ -d /build/dest/usr ] && cp -a /build/dest/usr/. /usr/ && ldconfig
if [ -n "${SP_HIDE_MODULE:-}" ]; then chmod 000 /usr/lib/x86_64-linux-gnu/pipewire-0.3/libpipewire-module-filter-chain.so; touch /tmp/module-hidden; fi
if [ -n "${SP_POLKIT:-}" ]; then
  # the system bus, polkit and its rule: SP_POLKIT=yes lets the page's every-account action through, no refuses it
  mkdir -p /run/dbus /etc/polkit-1/rules.d
  rm -f /run/dbus/pid; dbus-daemon --system --fork
  RES=YES; [ "$SP_POLKIT" = no ] && RES=NO
  printf 'polkit.addRule(function(action, subject) { if (action.id.indexOf("org.kde.plasma.pa.speakers") == 0) return polkit.Result.%s; });\n' $RES >/etc/polkit-1/rules.d/49-sp23.rules
  /usr/lib/polkit-1/polkitd --no-debug >/tmp/polkitd.log 2>&1 &
  sleep 2
fi
export PATH=/usr/local/bin:$PATH
exec setpriv --reuid 1001 --regid 1001 --clear-groups env HOME=/home/rig XDG_RUNTIME_DIR=/run/user/1001 PATH=$PATH QML_XHR_ALLOW_FILE_READ=1 XDG_DATA_DIRS=/usr/local/share:/usr/share QT_QPA_PLATFORM=offscreen bash /src/session.sh "$@"
