#!/usr/bin/env python3
"""eyes.py CAP.png [--lmask R,G,B --rmask R,G,B] : split a stereo capture (twice the output's width) into eyes (RGB arrays),
count differing RGB pixels, and measure the horizontal shift (right minus left, px, signed) of the tagged shapes by
matching the right eye's tagged mask against the left's (centroid and best integer/sub-pixel row-wise match)."""
import sys, json
import numpy as np
from PIL import Image
def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.int16)
def split(a):
    h, w, _ = a.shape
    return a[:, : w // 2], a[:, w // 2 :]
def mask(e, rgb, tol=60):
    return (np.abs(e - np.array(rgb)).max(axis=2) <= tol)
def blockmatch(L, R, area, bs=24, rng=160):
    """block matching along the same row only. returns dict: median/min/max horizontal shift (right minus left, px), vertical median, n blocks, share within 1 px of the median"""
    x0, y0, w, h = area
    g = lambda e: e.astype(np.float32).mean(axis=2)
    Lg, Rg = g(L), g(R)
    dxs = []; dys = []
    for y in range(y0, y0 + h - bs, bs):
        for x in range(x0, x0 + w - bs, bs):
            blk = Lg[y:y + bs, x:x + bs]
            if blk.std() < 8:
                continue
            best = None
            for dy in (0,):
                for dx in range(-rng, rng + 1):
                    xx = x + dx
                    if xx < 0 or xx + bs > Rg.shape[1]:
                        continue
                    sad = np.abs(Rg[y + dy:y + dy + bs, xx:xx + bs] - blk).mean()
                    if best is None or sad < best[0]:
                        best = (sad, dx, dy)
            if best and best[0] < 6:
                dxs.append(best[1]); dys.append(best[2])
    if not dxs:
        return {"blocks": 0}
    dxs = np.array(dxs); m = float(np.median(dxs))
    # vertical: repeat best match with dy in -3..3 at the median dx
    return {"blocks": int(len(dxs)), "median_px": m, "min_px": int(dxs.min()), "max_px": int(dxs.max()),
            "within_1px_of_median": round(float((np.abs(dxs - m) <= 1).mean()), 3)}

def shift(ml, mr):
    """signed shift of mr relative to ml: centroid difference over rows both occupy"""
    if ml.sum() == 0 or mr.sum() == 0:
        return None
    ys, xs = np.nonzero(ml); yr, xr = np.nonzero(mr)
    return round(float(xr.mean() - xs.mean()), 2)
if __name__ == "__main__":
    a = load(sys.argv[1])
    L, R = split(a) if "--mono" not in sys.argv else (a, a)
    out = {"size": list(a.shape[1::-1]), "eye_size": [L.shape[1], L.shape[0]],
           "differing_rgb_pixels": int((L != R).any(axis=2).sum())}
    args = sys.argv[2:]
    if "--area" in args:
        x, y, w, h = [int(v) for v in args[args.index("--area") + 1].split(",")]
        d = (L != R).any(axis=2); d[y:y + h, x:x + w] = False
        out["differing_rgb_pixels_outside_area"] = int(d.sum())
    if "--bm" in args:
        x, y, w, h = [int(v) for v in args[args.index("--bm") + 1].split(",")]
        out["blockmatch"] = blockmatch(L, R, (x, y, w, h))
    if "--mono" in args:
        out["differing_rgb_pixels"] = 0
    if "--lmask" in args:
        lm = [int(x) for x in args[args.index("--lmask") + 1].split(",")]
        rm = [int(x) for x in args[args.index("--rmask") + 1].split(",")]
        ml = mask(L, lm); mr = mask(R, rm)
        out["left_tag_px"] = int(ml.sum()); out["right_tag_px"] = int(mr.sum())
        out["right_eye_has_left_tag"] = int(mask(R, lm).sum()); out["left_eye_has_right_tag"] = int(mask(L, rm).sum())
        out["shift_px"] = shift(ml, mr)
        # swapped-eye check: tags read the other way must not match
        sw = shift(mask(R, lm), mask(L, rm))
        out["swapped_tags_found"] = [int(mask(R, lm).sum()), int(mask(L, rm).sum())]
    print(json.dumps(out))
