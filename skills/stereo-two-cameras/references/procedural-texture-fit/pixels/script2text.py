#!/usr/bin/env python3
"""A found procedure (the fitter's script of hex words) as the typed text an artist reads and
lane 503's playback module takes: NAME OPERATOR INPUTS VALUES, one operator per line.

Usage: script2text.py FOUND.script [SIZE-EXPONENT] > FOUND.txt      (default size 9: 512 pixels)
"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "werkkzeug"))
from wzlang import PACK
size = int(sys.argv[2]) if len(sys.argv) > 2 else 9
out = None
for line in open(sys.argv[1]):
    p = line.split()
    if not p:
        continue
    if p[0] == "out":
        out = p[1]; continue
    name, op, ins, words = p[0], p[1], p[2], [int(x, 16) for x in p[3:]]
    kinds = PACK[op]
    vals = []
    for i, k in enumerate(kinds):
        w = words[i] if i < len(words) else 0
        if op in ("Flat", "Perlin", "Cell", "Gradient", "Bricks") and i < 2:
            vals.append(str(size))
        elif op == "Transform" and i >= 6:
            vals.append("0")
        elif k == "c":
            vals.append("#%08x" % w)
        elif k == "f":
            vals.append("%.6g" % struct.unpack("<f", struct.pack("<I", w))[0])
        else:
            vals.append(str(struct.unpack("<i", struct.pack("<I", w))[0]))
    print(name, op, ins, " ".join(vals))
if out is None:
    sys.exit("no out line")
