#!/usr/bin/env python3
"""The prior: what .kkrieger's artists really built, read from kkrieger.k.

Usage: prior.py KKRIEGER.k OUTDIR HELD_OUT_NAME...
Writes OUTDIR/scripts/NAME.script (every drawable named bitmap, wzrender's form),
OUTDIR/prior.txt (operator instances and generator chains with their consumer; the graphs of the
held-out names and every operator they contain are left out, so a known answer never meets its own values),
OUTDIR/names.txt (operators, bytes, name).
prior.txt lines:
  I OP WORDS...                      one real instance of an operator (hex words)
  C SLOT CONSUMER WORDS | OP WORDS ; OP WORDS ...   a generator and the one-input operators above it, and the
                                     several-input operator that takes the chain as input number SLOT
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "werkkzeug"))
import kgraph

g = kgraph.Graph(sys.argv[1]); out = sys.argv[2]; held = set(sys.argv[3:])
os.makedirs(out + "/scripts", exist_ok=True)
names = []
for n in sorted(g.named):
    o = g.named[n]
    if o["cls"] in (0x02,) or o["cls"] in kgraph.NAMES:
        order, top, bad = g.collect(n)
        if top and not bad and not any(kgraph.NAMES[o["cls"]] == "Text" for _, o, _ in order):
            names.append((n, order, top))
heldops = set()
for n, order, top in names:
    if n in held:
        heldops |= {o["i"] for _, o, _ in order}
missing = held - {n for n, _, _ in names}
if missing:
    sys.exit("held-out names not drawable: %s" % sorted(missing))
inst, chains = set(), set()
with open(out + "/names.txt", "w") as f:
    for n, order, top in names:
        s, _ = g.script(n)
        open(out + "/scripts/" + n.replace("/", "_") + ".script", "w").write(s)
        f.write("%d %d %s\n" % (len(order), sum(1 + 4 * len(o["words"]) for _, o, _ in order), n))
        if n in held:
            continue
        cons = {}
        for vid, o, ins in order:
            for k, i in enumerate(ins):
                cons.setdefault(i, []).append((vid, k))
        byid = {vid: (o, ins) for vid, o, ins in order}
        hexw = lambda o: " ".join("%x" % w for w in o["words"])
        for vid, o, ins in order:
            nm = kgraph.NAMES[o["cls"]]
            if nm in ("Format",) or o["i"] in heldops:
                continue
            inst.add("I %s %s" % (nm, hexw(o)))
            if nm in kgraph.GENERATORS:
                chain, cur = ["%s %s" % (nm, hexw(o))], vid
                while len(cons.get(cur, [])) == 1:
                    nv, slot = cons[cur][0]
                    no, nins = byid[nv]
                    nn = kgraph.NAMES[no["cls"]]
                    if no["i"] in heldops:
                        break
                    if len(nins) == 1 and nn != "Format" and len(chain) < 5:
                        chain.append("%s %s" % (nn, hexw(no))); cur = nv
                    else:
                        if len(nins) in (2, 3) and nn in ("Merge", "Mask", "Distort", "Bump", "Paste"):
                            chains.add("C %d %s %s | %s" % (slot, nn, hexw(no), " ; ".join(chain)))
                        break
with open(out + "/prior.txt", "w") as f:
    f.write("\n".join(sorted(inst)) + "\n" + "\n".join(sorted(chains)) + "\n")
print(len(names), "graphs,", len(inst), "instances,", len(chains), "chains; held out", len(held), "graphs,", len(heldops), "operators")
