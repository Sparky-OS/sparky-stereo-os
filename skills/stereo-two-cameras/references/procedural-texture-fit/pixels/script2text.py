#!/usr/bin/env python3
"""A found procedure (the fitter's script of hex words) as the typed text an artist reads and
lane 503's playback module takes: NAME OPERATOR INPUTS VALUES, one operator per line.

Usage: script2text.py FOUND.script [SIZE-EXPONENT] > FOUND.txt      (default size 9: 512 pixels)
"""
import json, os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "farbrausch"))
from wzlang import PACK
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from opkinds import kinds as _kinds
PACK = dict(PACK)
for _k, _v in _kinds().items():
    PACK.setdefault(_k, _v)   # the modern operators of milestone 2b
size = int(sys.argv[2]) if len(sys.argv) > 2 else 9
out = None
for line in open(sys.argv[1]):
    p = line.split()
    if not p:
        continue
    if p[0] == "out":
        out = p[1]; continue
    name, op, ins, words = p[0], p[1], p[2], [int(x, 16) for x in p[3:] if not x.startswith("s=")]
    kinds = PACK[op]
    v2 = op == "Text" and len(words) >= 10 and words[9] == 2
    if v2:
        kinds = kinds + "iii"
    elif len(words) < len(kinds) and op not in ("Text",):
        # a modern operator of an earlier version stores fewer words (Tiles version 1 has 17 of version 2's 24)
        kinds = kinds[:len(words)]
    strs = [bytes.fromhex(x[2:]).decode("utf-8") if v2 else bytes.fromhex(x[2:]).decode("latin-1") for x in p[3:] if x.startswith("s=")]
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
            vals.append("%.9g" % struct.unpack("<f", struct.pack("<I", w))[0])
        else:
            vals.append(str(struct.unpack("<i", struct.pack("<I", w))[0]))
    # a Text operator's two strings (the text, the font's name; an empty name is werkkzeug3's "arial") as quoted strings
    print(name, op, ins, " ".join(vals + [json.dumps(x, ensure_ascii=False) for x in strs]))
if out is None:
    sys.exit("no out line")
