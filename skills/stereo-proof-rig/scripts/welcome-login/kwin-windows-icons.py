#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""kwin-windows-icons.py KWINLOG: the rig's kwin_windows.py (ORDER 249) with each window's minimized state and its iconGeometry,
the rectangle of its button in the task manager as the task manager hands it to KWin (ORDER 63/720, the touch rows).

Loads a small KWin script through org.kde.kwin.Scripting that prints every window of workspace.stackingOrder
(caption, class, frame and client geometry, full screen, popup, transient, active, opacity), reads its line back
from KWin's log, and unloads it. Run inside the rig's D-Bus session.
"""
import json, os, sys, time
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

log = sys.argv[1]
tag = "FSWIN%d" % int(time.monotonic() * 1000)
js = os.path.join(os.environ["XDG_RUNTIME_DIR"], tag + ".js")
with open(js, "w") as f:
    f.write("""
var out = [];
var ws = workspace.stackingOrder;
for (var i = 0; i < ws.length; i++) {
  var w = ws[i];
  out.push({caption: w.caption, cls: String(w.resourceClass), fg: [w.frameGeometry.x, w.frameGeometry.y, w.frameGeometry.width, w.frameGeometry.height],
            cg: [w.clientGeometry.x, w.clientGeometry.y, w.clientGeometry.width, w.clientGeometry.height],
            fs: w.fullScreen, popup: w.popupWindow, transient: w.transient, active: w.active, normal: w.normalWindow,
            utility: w.utility, tooltip: w.tooltip, x11: w.x11Client !== undefined ? w.x11Client : null, opacity: w.opacity,
            hidden: w.hidden, deleted: w.deleted, minimized: w.minimized,
            icon: [w.iconGeometry.x, w.iconGeometry.y, w.iconGeometry.width, w.iconGeometry.height]});
}
print("%s " + JSON.stringify(out));
""" % tag)
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
start = os.path.getsize(log) if os.path.exists(log) else 0
sid = bus.call_sync("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "loadScript",
                    GLib.Variant("(ss)", (js, tag)), GLib.VariantType("(i)"), Gio.DBusCallFlags.NONE, 5000, None).unpack()[0]
path = "/Scripting/Script%d" % sid
try:
    bus.call_sync("org.kde.KWin", path, "org.kde.kwin.Script", "run", None, None, Gio.DBusCallFlags.NONE, 5000, None)
except GLib.Error:
    path = "/%d" % sid
    bus.call_sync("org.kde.KWin", path, "org.kde.kwin.Script", "run", None, None, Gio.DBusCallFlags.NONE, 5000, None)
line = None
for _ in range(40):
    time.sleep(0.05)
    with open(log, errors="replace") as f:
        f.seek(start)
        for l in f:
            if tag + " " in l:
                line = l.split(tag + " ", 1)[1].strip()
    if line:
        break
bus.call_sync("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "unloadScript",
              GLib.Variant("(s)", (tag,)), GLib.VariantType("(b)"), Gio.DBusCallFlags.NONE, 5000, None)
os.unlink(js)
print(json.dumps({"t_monotonic_ms": int(time.monotonic() * 1000), "windows": json.loads(line) if line else None}))
