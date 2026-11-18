#!/usr/bin/env python3
"""tagshift.py OUTDIR : eye-tagged geometry. A near object tagged green and a far object tagged red; the signed shift (right eye minus left eye, px, centroid of each colour's pixels) is
predicted negative for green (nearer than the screen plane, crossed) and positive for red (farther, uncrossed). The swapped-eye reading flips both signs and must fail the prediction."""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, eyes
d = sys.argv[1]
cj = json.load(open(d + "/cap2.json"))
a = eyes.load(d + "/cap2.png"); L, R = eyes.split(a)
dom = lambda e, c: {"r": (e[..., 0] > 140) & (e[..., 1] < 70) & (e[..., 2] < 70), "g": (e[..., 1] > 140) & (e[..., 0] < 70) & (e[..., 2] < 70), "b": (e[..., 2] > 140) & (e[..., 0] < 70) & (e[..., 1] < 70)}[c]
out = {"capture_stereo": cj["stereo"], "differing_rgb_pixels": int((L != R).any(axis=2).sum())}
for name, c, sign in (("far_red", "r", +1), ("near_green", "g", -1)):
    ml, mr = dom(L, c), dom(R, c)
    s = eyes.shift(ml, mr)
    out[name] = {"px_left": int(ml.sum()), "px_right": int(mr.sum()), "shift_px": s, "predicted_sign": "+" if sign > 0 else "-",
                 "check": "PASS" if (s is not None and s * sign > 0) else "FAIL",
                 "swapped_eyes_check": "FAIL(good)" if (s is None or (-s) * sign <= 0) else "PASS(bad)"}
print(json.dumps(out))
