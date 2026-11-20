#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""measure.py CAPTURE.png [DEPTH CONV [DEPTH_PCT CONV_PCT]]: the three planes of depthtest (red w=40, green w=80, blue
w=160) in a Stereo KWin capture (left eye = left half, right eye = right half), against Dolphin's own formula.

Dolphin 2609b: stereo_depth = Depth * DepthPercentage * 0.00001 and stereo_convergence = Convergence *
ConvergencePercentage * 0.01 (Source/Core/VideoCommon/VideoConfig.cpp:171-174); the left eye gets -stereo_depth and
the right eye +stereo_depth (GeometryShaderManager.cpp:55-57); every vertex moves by
pos.x += hoffset * (pos.w - stereo_convergence) (GeometryShaderGen.cpp:238-239). After the division by w, the two
eyes differ by 2 * stereo_depth * (1 - stereo_convergence / w) in normalized device coordinates, which span 2, so a
plane at distance w shifts by  stereo_depth * (1 - stereo_convergence / w) * D  pixels between the eyes (right minus
left, positive behind the screen), D being the width the picture is drawn at on the screen.

The shift of a plane is found by cross-correlating its colour signal between the eyes along rows (sub-pixel by a
parabola through the peak), the vertical shift by the same on its row profile. Prints one JSON line."""
import json, sys
import numpy as np
from PIL import Image

path = sys.argv[1]
depth = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
conv = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
dpct = float(sys.argv[4]) if len(sys.argv) > 4 else 100.0
cpct = float(sys.argv[5]) if len(sys.argv) > 5 else 100.0
a = np.asarray(Image.open(path).convert("RGB")).astype(np.int32)
H, W2 = a.shape[:2]
E = W2 // 2
L, R = a[:, :E], a[:, E:]
out = {"file": path.split("/")[-1], "size": [W2, H]}

def masks(q):
    r, g, b = q[..., 0], q[..., 1], q[..., 2]
    return {40: (r > 200) & (g < 110) & (b < 110), 80: (g > 200) & (r < 110) & (b < 110),
            160: (b > 200) & (r < 140) & (g < 140)}

def signal(q, w):
    r, g, b = q[..., 0].astype(float), q[..., 1].astype(float), q[..., 2].astype(float)
    if w == 40:
        return np.clip(r - np.maximum(g, b), 0, None)
    if w == 80:
        return np.clip(g - np.maximum(r, b), 0, None)
    return np.clip(b - np.maximum(r, g), 0, None)

def peak(c):
    i = int(np.argmax(c))
    if 0 < i < len(c) - 1:
        y0, y1, y2 = c[i - 1], c[i], c[i + 1]
        den = y0 - 2 * y1 + y2
        return i + (0.5 * (y0 - y2) / den if den != 0 else 0.0)
    return float(i)

ml = masks(L)
# The render window's place, from the X11 log beside the capture (the window whose name has " | "): one view wide
win = None
try:
    import os, re
    x11 = re.sub(r"-shot\d+\.png$", ".x11.log", path)
    for w_ in json.load(open(x11))["windows"]:
        if " | " in (w_.get("name") or ""):
            ax, ay = w_["abs"]; gw, gh = w_["geom"][2], w_["geom"][3]
            if w_["props"].get("_KDE_NET_WM_STEREO_CONTENT") == [3] and w_["props"].get("_KDE_NET_WM_STEREO_CONTENT_VERSION") != [4]:
                gw //= 2      # declared by the program: Stereo KWin made the X window two views wide
            win = [ax, ay, ax + gw, ay + gh]
except Exception:
    win = None
out["window"] = win
bg = (np.abs(L - 40) <= 6).all(axis=2)
pic = bg | ml[40] | ml[80] | ml[160]
if win:
    clip = np.zeros_like(pic); clip[win[1]:win[3], win[0]:win[2]] = True; pic &= clip
ys, xs = np.where(pic)
if len(xs) == 0:
    out["error"] = "no picture found in the left eye"
    print(json.dumps(out)); sys.exit(0)
x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
D = x1 - x0
out.update({"picture": [x0, y0, x1, y1], "D": D})
diff = (L[y0:y1, x0:x1] != R[y0:y1, x0:x1]).any(axis=2)
out["eyes_differ_share"] = round(float(diff.mean()), 4)
s_eff = depth * dpct * 0.00001
c_eff = conv * cpct * 0.01
planes = {}
M = 200
for w in (40, 80, 160):
    rows = np.where(ml[w].sum(axis=1) > 10)[0]
    if len(rows) < 10:
        planes[w] = {"error": "plane not found"}; continue
    lo, hi = rows[len(rows) // 5], rows[-len(rows) // 5]
    sl, sr = signal(L, w), signal(R, w)
    shifts = []
    for y in range(lo, hi, 3):
        l, r = sl[y], sr[y]
        if l.sum() == 0 or r.sum() == 0:
            continue
        lz, rz = l - l.mean(), r - r.mean()
        c = np.array([np.dot(lz[max(0, -s):E - max(0, s)], rz[max(0, s):E - max(0, -s)]) for s in range(-M, M + 1)])
        shifts.append(peak(c) - M)
    # vertical: the plane's row profile in each eye
    pl, pr = sl.sum(axis=1), sr.sum(axis=1)
    plz, prz = pl - pl.mean(), pr - pr.mean()
    cv = np.array([np.dot(plz[max(0, -s):H - max(0, s)], prz[max(0, s):H - max(0, -s)]) for s in range(-20, 21)])
    pred = s_eff * (1.0 - c_eff / w) * D
    sh = np.array(shifts)
    planes[w] = {"shift_px": round(float(np.median(sh)), 3), "rows": len(sh), "spread_px": round(float(sh.max() - sh.min()), 3),
                 "vertical_px": round(float(peak(cv) - 20), 3), "predicted_px": round(pred, 3),
                 "error_px": round(float(np.median(sh)) - pred, 3)}
out["planes"] = planes
out["formula"] = {"stereo_depth": s_eff, "stereo_convergence": c_eff}
print(json.dumps(out))
