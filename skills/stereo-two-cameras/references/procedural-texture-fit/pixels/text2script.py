#!/usr/bin/env python3
"""The typed form of a graph (script2text.py's output) back into the fitter's script: text2script.py < TYPED > SCRIPT
Used for small test graphs that check what an operator does (which way a move goes, which input is subtracted)."""
import json, re, struct, sys
kinds = {}
import os
here = os.path.dirname(os.path.abspath(__file__))
src = here + "/p2p.zig" if os.path.exists(here + "/p2p.zig") else os.path.dirname(here) + "/src/p2p.zig"
for m in re.finditer(r'\.name = "(\w+)", \.kinds = "(\w*)"', open(src).read()):
    kinds[m.group(1)] = m.group(2)
sys.path.insert(0, here)
from opkinds import kinds as _kinds
for _k, _v in _kinds().items():
    kinds.setdefault(_k, _v)   # the modern operators of milestone 2b
last = None
for line in sys.stdin:
    # quoted strings (a Text operator's text and font name) are taken out first: they may hold spaces
    strs = [json.loads(m) for m in re.findall(r'"(?:[^"\\]|\\.)*"', line)]
    t = re.sub(r'"(?:[^"\\]|\\.)*"', "", line).split()
    if not t or t[0].startswith("#"):
        continue
    name, op, ins, vals = t[0], t[1], t[2], t[3:]
    k = kinds[op]
    # Text version 2 (our extension): three more whole numbers (the version, 2; the palette; the form) and a third
    # string (the axis values); its strings are UTF-8, werkkzeug3's own are 8-bit
    v2 = op == "Text" and len(vals) == len(k) + 3
    if v2:
        k = k + "iii"
    if op == "Ramp" and len(vals) < len(k) and len(vals) >= 6 and len(vals) % 2 == 0:
        # a Ramp typed with fewer than eight stops: the stored operator holds eight, the unused ones repeat the last
        while len(vals) < len(k):
            vals += ["1", vals[-1]]
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
    if v2 and len(strs) == 2:
        strs.append("")
    print(name, op, ins, " ".join(out + ["s=" + x.encode("utf-8" if v2 else "latin-1").hex() for x in strs]))
    last = name
print("out", last)
