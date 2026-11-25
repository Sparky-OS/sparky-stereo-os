#!/bin/bash
# step-fcitx-activated.sh: inside a rig session whose input method is KWin's own (a Latin language, Plasma Keyboard as
# KWin's input method): Fcitx 5 is started behind KWin's back by D-Bus activation (a program asking it something, as an
# input method configuration tool does), then Kate is touched and typed into as in every typing case (row 71, the filter
# of input-method protocols, KWin merge request 9601). Writes activation.txt (Fcitx 5's processes after the activation)
# and panel-owner.txt (the program of the keyboard window KWin shows). Env: CASE, LANE, RIG, FAKEINPUT, SESSION_LOG.
set -u
python3 - > "$CASE/activation.txt" 2>&1 <<'PY'
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
try:
    # no NO_AUTO_START flag: the bus starts Fcitx 5 from its service file, as for any program that asks it
    v = bus.call_sync("org.fcitx.Fcitx5", "/controller", "org.fcitx.Fcitx.Controller1", "CurrentInputMethod", None,
                      GLib.VariantType("(s)"), Gio.DBusCallFlags.NONE, 20000, None)
    print("activated, current input method", v.unpack()[0])
except Exception as e:
    print("activation failed:", e)
PY
sleep 6
pgrep -a fcitx5 >> "$CASE/activation.txt"
grep -i -E 'input.?method|input.?panel' "$SESSION_LOG" | grep -i fcitx | tail -5 >> "$CASE/activation.txt"
timeout 200 python3 "$LANE/type-case.py" > "$CASE/type-case.log" 2>&1
python3 - "$CASE" > "$CASE/panel-owner.txt" 2>&1 <<'PY'
import json, os, sys
try:
    r = json.load(open(os.path.join(sys.argv[1], "result.json")))
    w = (r.get("keyboard") or {}).get("window") or {}
    pid = w.get("pid")
    comm = open("/proc/%d/comm" % pid).read().strip() if pid else None
    print(json.dumps({"kind": (r.get("keyboard") or {}).get("kind"), "pid": pid, "program": comm, "typed": r.get("typed"), "ok": r.get("ok")},
                     ensure_ascii=False))
except Exception as e:
    print(json.dumps({"error": str(e)}))
PY
