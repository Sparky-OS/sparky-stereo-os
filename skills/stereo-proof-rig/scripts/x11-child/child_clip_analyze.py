#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""analyze.py EVDIR MODE: per-eye rows of the clipping test. Exit 0 when every row passes."""
import json, re, sys
import numpy as np
from PIL import Image
ev, mode = sys.argv[1], sys.argv[2]
mode = mode[4:] if mode.startswith("egl-") else (mode[3:] if mode.startswith("vk-") else mode)
app = open(f"{ev}/app.log").read()
m = re.search(r"place=(\d+),(\d+),(\d+),(\d+) sib=(-?\d+),(-?\d+),(\d+),(\d+) stereo=(\d)", app)
cx, cy, cw, ch, sx, sy, sw, sh, stereo = map(int, m.groups())
wi = open(f"{ev}/parent-wininfo.txt").read()
px = int(re.search(r"Absolute upper-left X:\s+(-?\d+)", wi).group(1)); py = int(re.search(r"Absolute upper-left Y:\s+(-?\d+)", wi).group(1))
pw, ph = 400, 300
img = np.asarray(Image.open(f"{ev}/shot.png").convert("RGB")).astype(int)
H, W, _ = img.shape
isstereo = W == 2048
OW = W // 2 if isstereo else W
def eye(i): return img[:, i * OW:(i + 1) * OW] if isstereo else img
red = lambda a: (a[..., 0] > 150) & (a[..., 1] < 60) & (a[..., 2] < 60)
blue = lambda a: (a[..., 2] > 150) & (a[..., 0] < 60) & (a[..., 1] < 60)
green = lambda a: (a[..., 1] > 150) & (a[..., 0] < 60) & (a[..., 2] < 60)
res = {"capture": [W, H], "stereo_capture": isstereo, "parent": [px, py, pw, ph], "child_rect": [px + cx, py + cy, cw, ch]}
rows = []
def row(name, ok, detail): rows.append({"row": name, "pass": bool(ok), "detail": detail})
mono = mode == "mono-sibling"
row("capture is mono (control)" if mono else "capture is stereo (two outputs wide)", (not isstereo) if mono else isstereo, f"{W}x{H}")
yellow = lambda a: (a[..., 0] > 150) & (a[..., 1] > 150) & (a[..., 2] < 60)
for i, (nm, f) in enumerate((("only", yellow),) if mono else (("left", red), ("right", blue))):
    a = eye(i)
    mask = f(a)
    ys, xs = np.nonzero(mask)
    if not len(xs): row(f"{nm} eye shows the child's colour", False, "no pixels"); continue
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    # inside the part of the child that lies in the parent's client area, and not covered by the sibling
    x0, y0 = px + cx, py + cy
    x1, y1 = min(x0 + cw, px + pw), min(y0 + ch, py + ph)
    inside = mask[y0:y1, x0:x1]
    sibmask = np.zeros_like(inside, bool)
    if mode in ("sibling", "mono-sibling", "twosib"):
        sx0, sy0 = max(px + sx, x0) - x0, max(py + sy, y0) - y0
        sx1, sy1 = min(px + sx + sw, x1) - x0, min(py + sy + sh, y1) - y0
        sibmask[sy0:sy1, sx0:sx1] = True
    free = ~sibmask
    cover = inside[free].mean() if free.any() else 1.0
    row(f"{nm} eye: the child's colour fills its visible place", cover > 0.9, f"{cover:.3f} bbox={bbox}")
    outside = mask.copy(); outside[y0:y1, x0:x1] = False
    n_out = int(outside.sum())
    # clip: nothing of the child's colour outside the parent's client area
    pm = np.zeros_like(mask); pm[py:py + ph, px:px + pw] = True
    n_out_parent = int((mask & ~pm).sum())
    row(f"{nm} eye: no child pixel outside its window (clip to the window)", n_out_parent == 0, f"{n_out_parent} px outside the parent's {pw}x{ph}")
    if mode in ("sibling", "mono-sibling", "twosib"):
        ov = a[py + max(sy, cy):py + min(sy + sh, ch + cy), px + sx:px + min(sx + sw, cx + cw)]
        g = green(ov).mean(); c = (f(ov)).mean()
        row(f"{nm} eye: the sibling stacked over the child stays visible", g > 0.9 and c < 0.02, f"green {g:.3f}, child colour {c:.3f}")
try:
    props = json.load(open(f"{ev}/props.json"))
    byid = {w["id"]: w for w in props["windows"]}
    child_id = int(re.search(r"child=(0x[0-9a-f]+)", app).group(1), 16)
    par_id = int(re.search(r"parent=(0x[0-9a-f]+)", app).group(1), 16)
    declared = "_KDE_NET_WM_STEREO_CONTENT" in byid.get(child_id, {}).get("props", {})
    listed = child_id in byid.get(par_id, {}).get("props", {}).get("_KDE_NET_WM_STEREO_CONTENT_CHILDREN", [])
    if declared:
        row("the declared child is listed in its window's _KDE_NET_WM_STEREO_CONTENT_CHILDREN", listed, f"declared={declared} listed={listed}")
except Exception as e:
    row("declarations readable", False, repr(e))
res["rows"] = rows
res["pass"] = all(r["pass"] for r in rows)
print(json.dumps(res, indent=1))
sys.exit(0 if res["pass"] else 1)
