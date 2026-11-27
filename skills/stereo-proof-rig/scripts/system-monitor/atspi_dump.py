#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""atspi_dump.py APP OUT.json: every accessible object of APP's windows (role, name, text, screen box, showing,
checked), read through AT-SPI's own GObject bindings (gir1.2-atspi-2.0, no pyatspi needed), so a page is read by its
widgets' own text rather than by recognising characters on a capture. The program must run with
QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 on the same session bus as the AT-SPI bus launcher."""
import json
import sys

import gi
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi  # noqa: E402


def walk(node, depth, out):
    try:
        text = ""
        if node.get_text_iface() is not None:
            text = Atspi.Text.get_text(node, 0, Atspi.Text.get_character_count(node))
        box = None
        if node.get_component_iface() is not None:
            e = Atspi.Component.get_extents(node, Atspi.CoordType.SCREEN)
            box = [e.x, e.y, e.width, e.height]
        states = node.get_state_set()
        out.append({"depth": depth, "role": node.get_role_name(), "name": node.get_name() or "", "text": text,
                    "box": box, "showing": states.contains(Atspi.StateType.SHOWING),
                    "checked": states.contains(Atspi.StateType.CHECKED)})
        for i in range(node.get_child_count()):
            child = node.get_child_at_index(i)
            if child is not None:
                walk(child, depth + 1, out)
    except Exception as error:  # an object that went away while it was read
        out.append({"depth": depth, "error": str(error)})


def main():
    app_name, target = sys.argv[1], sys.argv[2]
    desktop = Atspi.get_desktop(0)
    out, names = [], []
    for i in range(desktop.get_child_count()):
        app = desktop.get_child_at_index(i)
        if app is None:
            continue
        names.append(app.get_name())
        if app.get_name() == app_name:
            walk(app, 0, out)
    json.dump({"applications": names, "objects": out}, open(target, "w"), ensure_ascii=False, indent=0)
    print("%d objects of %s (applications: %s)" % (len(out), app_name, names))
    return 0 if out else 1


if __name__ == "__main__":
    sys.exit(main())
