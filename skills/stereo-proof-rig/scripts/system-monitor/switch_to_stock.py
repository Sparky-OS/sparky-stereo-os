#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""switch_to_stock.py OUT_DIR [STOCK_TITLE [EDIT_PAGES_TEXT]]: press System Monitor's "Edit or Remove pages…" menu item
through AT-SPI (GObject bindings) once the sidebar toolbar's overflow menu is open (switch.sh opens it by fake input).
Prints the step; exits 1 when the item is not there. System Monitor must run with QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1.
The Edit Pages dialog itself is a popup AT-SPI does not show, so switch.sh drives it by pointer."""
import json
import sys
import time

import gi
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi  # noqa: E402

OUT = sys.argv[1]
EDIT_PAGES = sys.argv[3] if len(sys.argv) > 3 else "Edit or Remove pages…"


def nodes(root):
    out = []

    def walk(n):
        try:
            out.append(n)
            for i in range(n.get_child_count()):
                c = n.get_child_at_index(i)
                if c is not None:
                    walk(c)
        except Exception:
            pass
    walk(root)
    return out


def find(predicate, wait=8.0):
    end = time.time() + wait
    while time.time() < end:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is not None and app.get_name() == "plasma-systemmonitor":
                for n in nodes(app):
                    try:
                        if predicate(n):
                            return n
                    except Exception:
                        pass
        time.sleep(0.3)
    return None


item = find(lambda n: n.get_role_name() == "menu item" and n.get_name() == EDIT_PAGES
            and n.get_state_set().contains(Atspi.StateType.SHOWING))
done = None
if item is not None:
    names = [Atspi.Action.get_action_name(item, i) for i in range(Atspi.Action.get_n_actions(item))]
    index = names.index("Press") if "Press" in names else 0
    Atspi.Action.do_action(item, index)
    done = names[index] if names else None
step = {"step": "edit pages action", "found": item is not None, "name": EDIT_PAGES, "action": done}
print(json.dumps(step, ensure_ascii=False))
time.sleep(1)
json.dump([step], open(OUT + "/switch-steps.json", "w"), ensure_ascii=False, indent=1)
sys.exit(0 if item is not None else 1)
