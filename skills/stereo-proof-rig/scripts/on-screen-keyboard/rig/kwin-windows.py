#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""kwin-windows.py KWINLOG: KWin's own list of windows as one JSON line, with the on-screen keyboard's flags.

From skills/stereo-proof-rig/scripts/kwin_windows.py (ORDER 249), with what row 71 reads: KWin's inputMethod flag (an
input panel of KWin's input method), the window type, its pid and its output. Run inside the rig's D-Bus session.
"""
import json, os, sys, time
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

log = sys.argv[1]
tag = "KBWIN%d" % int(time.monotonic() * 1000)
js = os.path.join(os.environ["XDG_RUNTIME_DIR"], tag + ".js")
with open(js, "w") as f:
    f.write("""
var out = [];
var ws = workspace.stackingOrder;
for (var i = 0; i < ws.length; i++) {
  var w = ws[i];
  out.push({caption: w.caption, cls: String(w.resourceClass), fg: [w.frameGeometry.x, w.frameGeometry.y, w.frameGeometry.width, w.frameGeometry.height],
            cg: [w.clientGeometry.x, w.clientGeometry.y, w.clientGeometry.width, w.clientGeometry.height],
            active: w.active, normal: w.normalWindow, dock: w.dock, inputMethod: w.inputMethod, type: w.windowType, pid: w.pid,
            output: w.output ? w.output.name : null, hidden: w.hidden, deleted: w.deleted, minimized: w.minimized,
            opacity: w.opacity, keepAbove: w.keepAbove});
}
print("%s " + JSON.stringify(out));
""" % tag)
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
start = os.path.getsize(log) if os.path.exists(log) else 0
sid = bus.call_sync("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "loadScript",
                    GLib.Variant("(ss)", (js, tag)), GLib.VariantType("(i)"), Gio.DBusCallFlags.NONE, 5000, None).unpack()[0]
for path in ("/Scripting/Script%d" % sid, "/%d" % sid):
    try:
        bus.call_sync("org.kde.KWin", path, "org.kde.kwin.Script", "run", None, None, Gio.DBusCallFlags.NONE, 5000, None)
        break
    except GLib.Error:
        continue
line = None
for _ in range(60):
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
