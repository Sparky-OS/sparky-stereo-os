#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""mpris_vol.py: print VLC Stereo's own volume and playback state through MPRIS as one JSON line."""
import json, time
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
d = "org.mpris.MediaPlayer2.vlc-stereo"
def get(prop):
    r = bus.call_sync(d, "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties", "Get", GLib.Variant("(ss)", ("org.mpris.MediaPlayer2.Player", prop)), None, Gio.DBusCallFlags.NONE, 5000, None)
    return r.unpack()[0]
print(json.dumps({"t": time.time(), "volume": get("Volume"), "status": get("PlaybackStatus")}))
