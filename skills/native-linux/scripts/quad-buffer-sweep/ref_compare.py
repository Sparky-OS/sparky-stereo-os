#!/usr/bin/env python3
"""ref_compare.py QUADDIR LEFTDIR RIGHTDIR : compare the two eyes of a quad-buffer capture against the program's own single-eye renderings
(left-only and right-only, same window place). Prints differing RGB pixel counts for the right pairing and for the swapped pairing."""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, eyes
q, l, r = sys.argv[1:4]
props = json.load(open(q + "/props.json")); w = [x for x in props["windows"] if any(k.startswith("_KDE_NET_WM_STEREO_CONTENT") and k != "_KDE_NET_WM_STEREO_CONTENT_VERSION" for k in x["props"])][0]
x, y = w["abs"]; gw, gh = w["geom"][2], w["geom"][3]
QL, QR = eyes.split(eyes.load(q + "/cap2.png"))
ML = eyes.load(l + "/cap2.png"); MR = eyes.load(r + "/cap2.png")
crop = lambda a: a[y:y + gh, x:x + gw]
cnt = lambda a, b: int((crop(a) != crop(b)).any(axis=2).sum())
out = {"area": [x, y, gw, gh], "left_eye_vs_left_only": cnt(QL, ML), "right_eye_vs_right_only": cnt(QR, MR),
       "SWAPPED_left_eye_vs_right_only": cnt(QL, MR), "SWAPPED_right_eye_vs_left_only": cnt(QR, ML),
       "eyes_differ_px": cnt(QL, QR)}
# the shift of the right eye against the left, from block matching, signed
bm = eyes.blockmatch(QL, QR, (x, y, gw, gh), rng=min(200, gw // 2)); out["blockmatch"] = bm
out["eyes_match_own_reference"] = out["left_eye_vs_left_only"] == 0 and out["right_eye_vs_right_only"] == 0
out["swapped_eyes_fail"] = out["SWAPPED_left_eye_vs_right_only"] > 0 and out["SWAPPED_right_eye_vs_left_only"] > 0
print(json.dumps(out))
