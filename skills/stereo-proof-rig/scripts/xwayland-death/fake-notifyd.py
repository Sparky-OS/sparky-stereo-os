#!/usr/bin/env python3
"""A stand-in notification server on the session bus (org.freedesktop.Notifications, Desktop Notifications 1.2):
every Notify call is written to OUT as one JSON line. For the rig's private session bus only.

Usage: fake-notifyd.py OUT
"""
import json
import sys
import time

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

XML = """
<node>
 <interface name="org.freedesktop.Notifications">
  <method name="Notify">
   <arg type="s" direction="in"/><arg type="u" direction="in"/><arg type="s" direction="in"/>
   <arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="as" direction="in"/>
   <arg type="a{sv}" direction="in"/><arg type="i" direction="in"/><arg type="u" direction="out"/>
  </method>
  <method name="CloseNotification"><arg type="u" direction="in"/></method>
  <method name="GetCapabilities"><arg type="as" direction="out"/></method>
  <method name="GetServerInformation">
   <arg type="s" direction="out"/><arg type="s" direction="out"/><arg type="s" direction="out"/><arg type="s" direction="out"/>
  </method>
  <signal name="NotificationClosed"><arg type="u"/><arg type="u"/></signal>
  <signal name="ActionInvoked"><arg type="u"/><arg type="s"/></signal>
 </interface>
</node>
"""

out = open(sys.argv[1], "a", buffering=1)
counter = [0]


def call(conn, sender, path, iface, method, params, invocation):
    if method == "Notify":
        app, replaces, icon, summary, body, actions, hints, timeout = params.unpack()
        counter[0] += 1
        out.write(json.dumps({"time": time.strftime("%H:%M:%S", time.gmtime()), "app": app, "summary": summary,
                              "body": body, "icon": icon, "actions": actions,
                              "hints": sorted(hints.keys()), "sender": sender}) + "\n")
        invocation.return_value(GLib.Variant("(u)", (counter[0],)))
    elif method == "GetCapabilities":
        invocation.return_value(GLib.Variant("(as)", (["body", "actions", "persistence"],)))
    elif method == "GetServerInformation":
        invocation.return_value(GLib.Variant("(ssss)", ("rig-fake-notifyd", "sparky-stereo", "1", "1.2")))
    else:
        invocation.return_value(None)


def acquired(conn, name):
    node = Gio.DBusNodeInfo.new_for_xml(XML)
    conn.register_object("/org/freedesktop/Notifications", node.interfaces[0], call, None, None)
    out.write(json.dumps({"ready": True}) + "\n")


Gio.bus_own_name(Gio.BusType.SESSION, "org.freedesktop.Notifications", Gio.BusNameOwnerFlags.NONE,
                 acquired, None, lambda *a: out.write(json.dumps({"lost": True}) + "\n"))
GLib.MainLoop().run()
