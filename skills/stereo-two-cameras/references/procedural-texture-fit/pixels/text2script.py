#!/usr/bin/env python3
"""The typed form of a graph (script2text.py's output) back into the fitter's script: text2script.py < TYPED > SCRIPT
Used for small test graphs that check what an operator does (which way a move goes, which input is subtracted)."""
import re, struct, sys
kinds = {}
import os
here = os.path.dirname(os.path.abspath(__file__))
src = here + "/p2p.zig" if os.path.exists(here + "/p2p.zig") else os.path.dirname(here) + "/src/p2p.zig"
for m in re.finditer(r'\.name = "(\w+)", \.kinds = "(\w*)"', open(src).read()):
    kinds[m.group(1)] = m.group(2)
last = None
for line in sys.stdin:
    t = line.split()
    if not t or t[0].startswith("#"):
        continue
    name, op, ins, vals = t[0], t[1], t[2], t[3:]
    k = kinds[op]
    if len(vals) != len(k):
        sys.exit("%s: %s takes %d values, %d given" % (name, op, len(k), len(vals)))
    out = []
    for kd, v in zip(k, vals):
        if kd == "i":
            out.append("%x" % (int(v) & 0xffffffff))
        elif kd == "f":
            out.append("%x" % struct.unpack("<I", struct.pack("<f", float(v)))[0])
        else:
            out.append(v.lstrip("#"))
    print(name, op, ins, " ".join(out))
    last = name
print("out", last)
