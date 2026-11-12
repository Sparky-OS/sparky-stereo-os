#!/usr/bin/env python3
"""The known answers that contain Text: their scripts (with the two strings of every Text operator) and their sizes.

Usage: textset.py KKRIEGER.k OUTDIR [NAME...]     (no names: every drawable named bitmap whose graph holds a Text)
Writes OUTDIR/NAME.script and OUTDIR/names.txt (operators, bytes with the strings, Text operators, name).
A string is written as s= and its bytes as hex digits; the bytes are Windows code page 1252, as the project file holds them.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "werkkzeug"))
import kgraph

g = kgraph.Graph(sys.argv[1]); out = sys.argv[2]; want = sys.argv[3:]
os.makedirs(out, exist_ok=True)
rows = []
for n in sorted(g.named):
    o = g.named[n]
    if want and n not in want:
        continue
    if not (o["cls"] == 0x02 or o["cls"] in kgraph.NAMES):
        continue
    order, top, bad = g.collect(n)
    if not top or bad:
        if want:
            sys.exit("%s cannot be drawn: %s" % (n, bad))
        continue
    texts = [o for _, o, _ in order if kgraph.NAMES[o["cls"]] == "Text"]
    if not texts:
        if want:
            sys.exit("%s holds no Text operator" % n)
        continue
    lines, size = [], 0
    for vid, o, ins in order:
        nm = kgraph.NAMES[o["cls"]]
        line = "%s %s %s %s" % (vid, nm, ",".join(ins) if ins else "-", " ".join("%x" % w for w in o["words"]))
        size += 1 + 4 * len(o["words"])
        if nm == "Text":
            strs = (o["strings"] + ["", ""])[:2]
            for s in strs:
                b = s.encode("latin-1")
                line += " s=" + b.hex()
                size += 4 + 4 * ((len(b) + 1 + 3) // 4)
        lines.append(line)
    lines.append("out " + top)
    open(os.path.join(out, n.replace("/", "_") + ".script"), "w").write("\n".join(lines) + "\n")
    rows.append((len(order), size, len(texts), n))
with open(os.path.join(out, "names.txt"), "w") as f:
    for r in rows:
        f.write("%d %d %d %s\n" % r)
print(len(rows), "graphs with Text")
