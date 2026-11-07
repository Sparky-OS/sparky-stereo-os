#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""propagation.py: does a pointer click on the video reach the video window of the interface? Finds the window that carries
_KDE_NET_WM_STEREO_CONTENT, selects ButtonPress and MotionNotify on its parent, clicks in the middle of the child with xdotool and
prints, as one JSON line, the events the parent received (X propagates an event that the child did not select to its parent).
Run it when no other client changes the window (the player is playing)."""
import json, subprocess, time
from Xlib import X, display
d = display.Display(); root = d.screen().root
atom = d.intern_atom("_KDE_NET_WM_STEREO_CONTENT", True)
def walk(w, parent=None):
    if w.get_full_property(atom, X.AnyPropertyType) is not None:
        return w, parent
    for c in w.query_tree().children:
        r = walk(c, w)
        if r: return r
child, parent = walk(root)
parent.change_attributes(event_mask=X.ButtonPressMask | X.ButtonReleaseMask | X.PointerMotionMask)
d.sync()
t = root.translate_coords(parent, 0, 0)
g = parent.get_geometry()
cx, cy = t.x + g.width // 2, t.y + g.height // 2
subprocess.run(["xdotool", "mousemove", str(cx - 20), str(cy), "mousemove", str(cx), str(cy), "click", "1"], check=False)
time.sleep(0.5)
got = []
while d.pending_events():
    e = d.next_event()
    got.append({"type": int(e.type), "event_window_is_parent": e.window.id == parent.id,
                "child_is_subwindow": getattr(e, "child", None) == child.id if hasattr(e, "child") else None})
print(json.dumps({"parent": parent.id, "child": child.id, "events": got}))
