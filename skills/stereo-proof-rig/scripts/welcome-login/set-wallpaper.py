#!/usr/bin/python3
"""set-wallpaper.py PLUGIN IMAGE_URL: inside a rig session, every desktop's wallpaper becomes PLUGIN showing IMAGE_URL, through
plasmashell's own scripting (org.kde.PlasmaShell.evaluateScript), as Desktop and Wallpaper settings would set it."""
import sys
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib
plugin, url = sys.argv[1:3]
js = ('desktops().forEach(function (d) { d.wallpaperPlugin = "%s"; d.currentConfigGroup = ["Wallpaper", "%s", "General"];'
      ' d.writeConfig("Image", "%s"); d.reloadConfig(); });' % (plugin, plugin, url))
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
bus.call_sync("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell", "evaluateScript", GLib.Variant("(s)", (js,)),
              None, Gio.DBusCallFlags.NONE, 10000, None)
print("set", plugin, url)
