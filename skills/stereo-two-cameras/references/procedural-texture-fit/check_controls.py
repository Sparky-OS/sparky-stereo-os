#!/usr/bin/env python3
"""The fit must find what the controls hold, and must find nothing in white noise.

Usage: check_controls.py WORKDIR RESULTS_DIR      (exit 1 when any check fails)
"""
import json
import sys

work, out = sys.argv[1], sys.argv[2]
truth = json.load(open(work + "/tex/controls-truth.json"))
fails = []


def check(label, ok, detail):
    print(("PASS " if ok else "FAIL ") + label + ": " + detail)
    if not ok:
        fails.append(label)


def proc(r, label):
    return next(p for p in r["procedures"] if p["procedure"].startswith(label))


k = json.load(open(out + "/control-ktg.json"))
p = proc(k, "OpenKTG")
t = truth["ktg"]
par = p["params"]
check("ktg control: frequency, octaves, seed and mode recovered",
      [par["freq"], par["oct"], par["seed"], par["mode"]] == [t["freq"], t["oct"], t["seed"], t["mode"]],
      "found %s, made with %s" % ([par["freq"], par["oct"], par["seed"], par["mode"]],
                                 [t["freq"], t["oct"], t["seed"], t["mode"]]))
check("ktg control: fadeoff within 0.005", abs(par["fadeoff"] - t["fadeoff"]) < 0.005,
      "found %.4f, made with %.2f" % (par["fadeoff"], t["fadeoff"]))
check("ktg control: the procedure alone is the picture (40 dB or more)", p["psnr_alone"] >= 40,
      "%.2f dB" % p["psnr_alone"])
check("ktg control: remainder under 5 percent of the picture's own lossless size",
      p["remainder_png"] < 0.05 * k["direct_png"],
      "%d against %d bytes" % (p["remainder_png"], k["direct_png"]))

w = json.load(open(out + "/control-white.json"))
for q in w["procedures"]:
    check("white noise: no saving with " + q["procedure"],
          q["remainder_png"] + q["procedure_bytes"] >= 0.999 * w["direct_png"],
          "%d + %d against %d bytes" % (q["remainder_png"], q["procedure_bytes"], w["direct_png"]))
check("white noise: the seed scan does not lock", not proc(w, "OpenKTG")["params"]["seed_locked"],
      "best correlation %.4f" % proc(w, "OpenKTG")["params"]["seed_correlation"])

l = json.load(open(out + "/control-lattice.json"))
p = proc(l, "16 cosine")
found = {tuple(v) for v in p["params"]["strongest_waves_kx_ky"]}
want = set()
for kx, ky in truth["lattice"]:
    want.add((kx, ky) if kx > 0 or (kx == 0 and ky > 0) else (-kx, -ky))
check("lattice control: the 12 waves are the 12 strongest found", want <= found,
      "missing %s" % sorted(want - found))
check("lattice control: 16 waves alone are the picture (45 dB or more)", p["psnr_alone"] >= 45,
      "%.2f dB" % p["psnr_alone"])
sys.exit(1 if fails else 0)
