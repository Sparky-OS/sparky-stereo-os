#!/bin/sh
# What the MPRIS2 player says, read on the session bus Rygel talks to: one "key=value" per line.
pid=$(pgrep -x rygel | head -1)
export DBUS_SESSION_BUS_ADDRESS=$(tr '\0' '\n' < /proc/$pid/environ | grep '^DBUS_SESSION_BUS_ADDRESS=' | cut -d= -f2-)
name=$(gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus --method org.freedesktop.DBus.ListNames | grep -o 'org\.mpris\.MediaPlayer2\.[A-Za-z0-9._-]*' | head -1)
get() { gdbus call --session --dest "$name" --object-path /org/mpris/MediaPlayer2 --method org.freedesktop.DBus.Properties.Get "$1" "$2" 2>&1 | tr -d '\n'; echo; }
echo "player=$name"
echo "mime=$(get org.mpris.MediaPlayer2 SupportedMimeTypes | cut -c1-600)"
echo "status=$(get org.mpris.MediaPlayer2.Player PlaybackStatus)"
echo "position=$(get org.mpris.MediaPlayer2.Player Position)"
echo "metadata=$(get org.mpris.MediaPlayer2.Player Metadata | cut -c1-900)"
