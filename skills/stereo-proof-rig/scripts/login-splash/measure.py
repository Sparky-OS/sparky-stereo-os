#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# measure.py: checks on a ScreenShot2 capture of one output (both eyes side by side on a 3D output, one picture on a 2D one).
#   measure.py gear CAPTURE GEAR.png         where KDE's gear is in each eye, and how well it matches (normalised correlation)
#   measure.py eyes CAPTURE                  pixels that differ between the eyes, and the shift of the whole right eye that fits the left best
#   measure.py levels CAPTURE REF2D LAYOUT.json   each level's disparity: its shift against the plain picture in each eye, left minus right
import json, sys
import numpy as np
from PIL import Image

def load(p):
    return np.asarray(Image.open(p).convert("RGB"), np.float32)

def eyes(px):
    h, w, _ = px.shape
    return (px[:, : w // 2], px[:, w // 2 :]) if w >= 2 * h else (px, None)

def gray(a):
    return a @ np.array([0.299, 0.587, 0.114], np.float32)

def ncc_search(img, tpl, mask):
    # brute force on a 4x smaller picture, then refined at full size around the best place
    best = (-2, 0, 0)
    f = 4
    small = gray(img)[::f, ::f]; t = gray(tpl)[::f, ::f]; m = mask[::f, ::f] > 0.5
    th, tw = t.shape
    tv = t[m] - t[m].mean(); tn = np.sqrt((tv * tv).sum()) + 1e-6
    for y in range(0, small.shape[0] - th):
        for x in range(0, small.shape[1] - tw):
            v = small[y : y + th, x : x + tw][m]; v = v - v.mean()
            s = float((v * tv).sum() / (np.sqrt((v * v).sum()) * tn + 1e-6))
            if s > best[0]:
                best = (s, x * f, y * f)
    return best

def cmd_gear(cap, gear):
    g = Image.open(gear).convert("RGBA"); tpl = np.asarray(g, np.float32)
    out = {}
    for name, e in zip(("left", "right"), eyes(load(cap))):
        if e is None:
            continue
        s, x, y = ncc_search(e, tpl[..., :3], tpl[..., 3] / 255.0)
        out[name] = {"score": round(s, 3), "x": x, "y": y}
    print(json.dumps({"gear": out}))

def best_shift(a, b, rng=24):
    # the shift s that makes b moved right by s match a: a[:, x] ~ b[:, x - s]
    res = []
    for s in range(-rng, rng + 1):
        if s >= 0:
            d = np.abs(a[:, s:] - b[:, : b.shape[1] - s])
        else:
            d = np.abs(a[:, :s] - b[:, -s:])
        res.append((float(d.mean()), s))
    res.sort()
    return res[0][1], res[0][0], res[1][0]

def cmd_eyes(cap):
    l, r = eyes(load(cap))
    if r is None:
        print(json.dumps({"stereo": False})); return
    diff = int((np.abs(l - r).max(axis=2) > 0).sum())
    s, err, second = best_shift(l, r)
    print(json.dumps({"stereo": True, "differing_pixels": diff, "whole_shift": s, "error": round(err, 3), "next_error": round(second, 3)}))

def cmd_levels(cap, ref, layout):
    # each part's pixels are the bright ones of the plain picture inside the part's box (the swirl's ring and lines, the logo's
    # letters; the background under them is darker), so the match follows the part, not the background it lies on
    L = json.load(open(layout))
    l, r = eyes(load(cap)); flat = load(ref)
    out = {}
    for item in L["items"]:
        x0, y0, x1, y1 = item["box"]
        g = gray(flat[y0:y1, x0:x1])
        mask = g > np.percentile(g, 85)
        res = {"pixels": int(mask.sum())}
        for name, e in (("left", l), ("right", r)):
            if e is None:
                continue
            best = []
            for s in range(-16, 17):
                a = e[y0:y1, x0 + s : x1 + s]; b = flat[y0:y1, x0:x1]
                best.append((float(np.abs(a - b).max(axis=2)[mask].mean()), s))
            best.sort()
            res[name] = {"shift": best[0][1], "error": round(best[0][0], 2), "next_error": round(best[1][0], 2)}
        if "right" in res:
            res["disparity"] = res["left"]["shift"] - res["right"]["shift"]
        res["predicted"] = item.get("predicted")
        out[item["name"]] = res
    print(json.dumps(out))

if __name__ == "__main__":
    {"gear": cmd_gear, "eyes": cmd_eyes, "levels": cmd_levels}[sys.argv[1]](*sys.argv[2:])
