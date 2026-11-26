#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Prints the 3D part of Celluloid's menu bar as the program exports it on the session bus (org.gtk.Menus):
one line per entry with its label, its action and target, and its hidden-when attribute.

The menu is read with the interface's own calls (Start on the groups, then on every group a section or a submenu
names), not through GDBusMenuModel, whose items only arrive while a main loop runs."""
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

BUS = "io.github.celluloid_player.Celluloid"
PATH = "/io/github/celluloid_player/Celluloid/menus/menubar"


def main():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    menus = {}          # (group, menu) -> list of item dicts
    asked, todo = set(), [0]
    while todo:
        groups = [g for g in todo if g not in asked]
        todo = []
        if not groups:
            break
        asked.update(groups)
        reply = bus.call_sync(BUS, PATH, "org.gtk.Menus", "Start", GLib.Variant("(au)", (groups,)),
                              GLib.VariantType("(a(uuaa{sv}))"), Gio.DBusCallFlags.NONE, 10000, None)
        for group, menu, items in reply.unpack()[0]:
            menus[(group, menu)] = items
            for item in items:
                for link in (":section", ":submenu"):
                    if link in item and item[link][0] not in asked:
                        todo.append(item[link][0])

    def walk(key, depth, inside):
        for item in menus.get(key, []):
            text = item.get("label", "")
            here = inside or text.replace("_", "") == "3D"
            if here:
                target = item.get("target")
                print("%s%s | action=%s | target=%s | hidden-when=%s" % (
                    "  " * depth, text or "(section)", item.get("action", ""),
                    "" if target is None else repr(target), item.get("hidden-when", "")))
            for link in (":section", ":submenu"):
                if link in item:
                    walk(tuple(item[link]), depth + 1 if here else depth, here)

    walk((0, 0), 0, False)


main()
