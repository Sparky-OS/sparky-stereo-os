#!/bin/sh
# Rygel's MPRIS plugin makes every MPRIS2 player on the session bus a UPnP AV MediaRenderer.
# The player here is VLC (or mpv) headless: it stands in for the edition's MPRIS2 stereo players
# (VLC Stereo, Haruna, Dragon), which declare the pair to KWin themselves.
set -eu
: "${RENDERER_INTERFACE:=eth0}"
: "${RENDERER_TITLE:=PC (stereo player)}"
export HOME=/tmp/pc XDG_RUNTIME_DIR=/tmp/pc/run XDG_CONFIG_HOME=/tmp/pc/config
mkdir -p "$HOME" "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME"
chmod 700 "$XDG_RUNTIME_DIR"
cat > "$XDG_CONFIG_HOME/rygel.conf" <<CONF
[general]
upnp-enabled=true
interface=$RENDERER_INTERFACE
log-level=*:4
[MPRIS]
enabled=true
title=$RENDERER_TITLE
[MediaExport]
enabled=false
[External]
enabled=false
[Tracker3]
enabled=false
[LMS]
enabled=false
CONF
# PLAYER=vlc (default) or mpv. mpv-mpris advertises only application/ogg and audio/mpeg as supported MIME types,
# and Rygel refuses a pushed item whose type is not in that list (UPnP error 714), so mpv plays no film here.
: "${PLAYER:=vlc}"
cat > /tmp/pc/session.sh <<SESSION
#!/bin/sh
if [ "$PLAYER" = mpv ]; then
  mpv --idle=yes --force-window=no --vo=null --ao=null --input-ipc-server=/records/mpv.sock --msg-level=all=info > /records/player.log 2>&1 &
else
  cvlc -I dummy --control dbus --vout dummy --aout dummy --no-xlib --verbose 1 > /records/player.log 2>&1 &
fi
sleep 3
exec rygel > /records/rygel.log 2>&1
SESSION
chmod +x /tmp/pc/session.sh
exec dbus-run-session -- /tmp/pc/session.sh
