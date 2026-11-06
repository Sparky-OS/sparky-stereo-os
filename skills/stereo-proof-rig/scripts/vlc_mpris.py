#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""mpris.py open FILE | stop | status: drives VLC Stereo through its MPRIS name on the session bus."""
import sys
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
dest, path = "org.mpris.MediaPlayer2.vlc-stereo", "/org/mpris/MediaPlayer2"
def call(method, args=None, sig=None):
    return bus.call_sync(dest, path, "org.mpris.MediaPlayer2.Player", method, GLib.Variant(sig, args) if sig else None, None, Gio.DBusCallFlags.NONE, 10000, None)
if sys.argv[1] == "open":
    call("OpenUri", ("file://" + sys.argv[2],), "(s)")
elif sys.argv[1] == "stop":
    call("Stop")
elif sys.argv[1] == "status":
    r = bus.call_sync(dest, path, "org.freedesktop.DBus.Properties", "Get", GLib.Variant("(ss)", ("org.mpris.MediaPlayer2.Player", "PlaybackStatus")), None, Gio.DBusCallFlags.NONE, 10000, None)
    print(r.unpack()[0])
