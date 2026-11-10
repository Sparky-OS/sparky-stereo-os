#!/usr/bin/env python3
"""The tiled controls must come back, and the real pictures must not be mistaken for procedures.

Usage: check_tiled.py WORKDIR RECOGNISE_DIR LADDER_DIR      (exit 1 when any check fails)
"""
import glob
import json
import sys

work, rec, lad = sys.argv[1:4]
truth = json.load(open(work + "/tex2/tiled-controls-truth.json"))
fails = []


def check(label, ok, detail):
    print(("PASS " if ok else "FAIL ") + label + ": " + detail)
    if not ok:
        fails.append(label)


def same(a, b):
    """Two operator lines agree when every number agrees (the fit may print 0.6 for 0.60)."""
    x, y = a.split(), b.split()
    return len(x) == len(y) and x[0] == y[0] and all(abs(float(p) - float(q)) < 1e-6 for p, q in zip(x[1:], y[1:]))


k = json.load(open(rec + "/control-tiled-ktg-recognise.json"))
check("tiled noise control: all 64 tiles come back pixel for pixel", k.get("exact_tiles") == 64, "%s of 64" % k.get("exact_tiles"))
head = lambda line: [float(v) for v in line.split()[1:6]]
tail = lambda line: [int(v) for v in line.split()[6:12]]
n = sum(head(t["line"]) == head(w) for t, w in zip(k["tiles"], truth["control-tiled-ktg"]))
check("tiled noise control: every tile's frequency, octaves, fadeoff, seed and mode are the ones it was made with", n == 64, "%d of 64" % n)
off = [max(abs(a - b) for a, b in zip(tail(t["line"]), tail(w))) for t, w in zip(k["tiles"], truth["control-tiled-ktg"])]
check("tiled noise control: every colour is the one it was made with, or one level away with the same pixels", max(off) <= 1,
      "%d tiles with the same colours, %d with a colour one level away" % (off.count(0), off.count(1)))

m = json.load(open(rec + "/control-tiled-mixed-recognise.json"))
kinds = sum(t["kind"] == w[0] for t, w in zip(m["tiles"], truth["control-tiled-mixed"]))
check("mixed control: the operator of every tile is named", kinds == 64, "%d of 64" % kinds)
for kind, word in (("N", "Noise"), ("G", "GlowRect"), ("F", "flat colour")):
    got = [t for t in m["tiles"] if t["kind"] == kind]
    check("mixed control: every %s tile comes back pixel for pixel" % word, all(t["exact"] for t in got),
          "%d of %d" % (sum(t["exact"] for t in got), len(got)))
cells = [t for t in m["tiles"] if t["kind"] == "C"]
print("NOTE mixed control: Cells tiles pixel for pixel: %d of %d; the others at %s dB"
      % (sum(t["exact"] for t in cells), len(cells), sorted(t["psnr"] for t in cells if not t["exact"])))

for f in sorted(glob.glob(rec + "/*-recognise.json")):
    r = json.load(open(f))
    if r["name"].startswith("control-tiled"):
        continue
    check("real picture %s is not taken for a tiled procedure" % r["name"], not r["recognised"],
          "best seed correlation %.3f" % r.get("first_noise_tile_seed_correlation", 0))

for f in sorted(glob.glob(lad + "/*-hard.json")) + sorted(glob.glob(lad + "/*-window.json")):
    r = json.load(open(f))
    p = [x["psnr"] for x in r["rungs"]]
    check("ladder %s (%s): no rung is further from the picture than the one below" % (r["name"], "window" if r["window"] else "hard"),
          all(b >= a - 0.005 for a, b in zip(p, p[1:])), " ".join("%.2f" % v for v in p))
sys.exit(1 if fails else 0)
