#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# analyze.py CASE [EYE]: the alpha of every translucent surface a translucency probe case captured, from its captures over the black
# and the white wallpaper (alpha = 1 - (white - black) / 255) inside each window's frame as KWin gave it.
# A surface's level is the median over its drawn background: pixels where the wallpaper shows through (alpha between
# 0.03 and 0.97: icons and text are opaque and set apart, the floating gap is empty), with the profile across its
# thickness for a panel. Prints one JSON object; EYE (left/right) reads one half of a 3D capture.
import json
import os
import sys

import numpy as np
from PIL import Image

case = sys.argv[1]
eye = sys.argv[2] if len(sys.argv) > 2 else ""


def load(name):
    a = np.asarray(Image.open(os.path.join(case, name)).convert("RGB")).astype(float)
    if eye:
        half = a.shape[1] // 2
        a = a[:, :half] if eye == "left" else a[:, half:]
    return a


def level(step, w):
    b, wh = load(f"{step}-black.png"), load(f"{step}-white.png")
    x, y, ww, hh = (int(round(w[k])) for k in ("x", "y", "w", "h"))
    B, W = b[y:y + hh, x:x + ww], wh[y:y + hh, x:x + ww]
    alpha = (1 - (W - B) / 255.0).mean(axis=2)
    drawn = (alpha > 0.03) & (alpha < 0.97)
    if drawn.sum() < 50:
        return {"drawn_pixels": int(drawn.sum()), "note": "nothing translucent drawn in the frame"}
    with np.errstate(divide="ignore", invalid="ignore"):
        colour = B / np.maximum(alpha, 1e-6)[..., None]
    rows = []
    for r in range(hh):
        m = drawn[r]
        rows.append(round(float(np.median(alpha[r][m])), 4) if m.sum() >= 10 else None)
    vals = alpha[drawn]
    return {"frame": [x, y, ww, hh], "drawn_pixels": int(drawn.sum()),
            "alpha_median": round(float(np.median(vals)), 4), "alpha_mean": round(float(vals.mean()), 4),
            "alpha_8bit_median": int(round(float(np.median(vals)) * 255)),
            "alpha_p05": round(float(np.percentile(vals, 5)), 4), "alpha_p95": round(float(np.percentile(vals, 95)), 4),
            "colour_median": [int(round(float(np.median(colour[..., c][drawn])))) for c in range(3)], "rows": rows}


def frames(name):
    p = os.path.join(case, name)
    return json.load(open(p)) if os.path.exists(p) else []


out = {}
for w in frames("win-panel-shots.json"):
    if w.get("dock"):
        out[f"panel@{w['x']},{w['y']},{w['w']}x{w['h']}"] = level("panel", w)
for w in frames("win-notif.json"):
    if w.get("notification"):
        out["notification"] = level("notif", w)
for w in frames("win-launcher.json"):
    if w.get("type") == 18:
        out["launcher-popup"] = level("launcher", w)
for w in frames("win-windows.json"):
    if w.get("caption") in ("probe-inactive", "probe-active", "probe-dialog"):
        out[w["caption"]] = level("windows", w)
print(json.dumps(out))
