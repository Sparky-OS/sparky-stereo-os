#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""state.py: print the player's own state as JSON from its MPRIS name on the session bus: PlaybackStatus and Fullscreen.
state.py wait: wait up to 30 s for a name org.mpris.MediaPlayer2.vlc*, then print."""
import json, sys, time
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
def names():
    r = bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "ListNames", None, None, Gio.DBusCallFlags.NONE, 5000, None)
    return [n for n in r.unpack()[0] if n.startswith("org.mpris.MediaPlayer2.vlc")]
def get(dest, iface, prop):
    r = bus.call_sync(dest, "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties", "Get", GLib.Variant("(ss)", (iface, prop)), None, Gio.DBusCallFlags.NONE, 5000, None)
    return r.unpack()[0]
for _ in range(120):
    n = names()
    if n:
        break
    time.sleep(0.25)
else:
    print(json.dumps({"error": "no MPRIS name"})); sys.exit(1)
d = n[0]
if len(sys.argv) > 2 and sys.argv[1] == "set-fs":
    bus.call_sync(d, "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties", "Set", GLib.Variant("(ssv)", ("org.mpris.MediaPlayer2", "Fullscreen", GLib.Variant("b", sys.argv[2] == "1"))), None, Gio.DBusCallFlags.NONE, 5000, None)
    time.sleep(1.5)
print(json.dumps({"name": d, "status": get(d, "org.mpris.MediaPlayer2.Player", "PlaybackStatus"), "fullscreen": get(d, "org.mpris.MediaPlayer2", "Fullscreen")}))
