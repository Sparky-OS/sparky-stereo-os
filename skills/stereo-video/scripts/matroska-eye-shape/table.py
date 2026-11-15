#!/usr/bin/env python3
# One line per rig case: player, fixture, declarations, two eyes captured, each eye's colour and circle
import json, sys
for l in open(sys.argv[1]):
    p = l.rstrip("\n").split(" ", 3)
    if len(p) < 4:
        continue
    try:
        r = json.loads(p[3])
    except ValueError:
        print("%-7s %-28s unreadable" % (p[0], p[1])); continue
    L = r.get("left") or {}; R = r.get("right") or {}
    print("%-7s %-28s decl=%-2s pair=%-5s L=%-5s %-7s R=%-5s %-7s" % (p[0], p[1], p[2], r.get("stereo_capture"), L.get("colour"), L.get("circle"), R.get("colour"), R.get("circle")))
