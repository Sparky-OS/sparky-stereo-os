#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""osd.py CAPTURE.png: Dolphin's on-screen display (FPS overlay) in each eye. Looks at the band of the render window above
the test planes (background only in the scene), in each eye, at the same place: the overlay's pixels (neither the scene's
grey nor black) in each eye, and how many pixels of the band differ between the eyes. One JSON line."""
import json, re, sys
import numpy as np
from PIL import Image
path = sys.argv[1]
a = np.asarray(Image.open(path).convert("RGB")).astype(np.int32)
H, W2 = a.shape[:2]; E = W2 // 2
L, R = a[:, :E], a[:, E:]
win = None
for w_ in json.load(open(re.sub(r"-shot\d+\.png$", ".x11.log", path)))["windows"]:
    if " | " in (w_.get("name") or ""):
        ax, ay = w_["abs"]; gw, gh = w_["geom"][2], w_["geom"][3]
        if w_["props"].get("_KDE_NET_WM_STEREO_CONTENT") == [3] and w_["props"].get("_KDE_NET_WM_STEREO_CONTENT_VERSION") != [4]:
            gw //= 2
        win = [ax, ay, ax + gw, ay + gh]
out = {"file": path.split("/")[-1], "size": [W2, H], "window": win}
if win is None:
    out["error"] = "no render window in the X11 log"; print(json.dumps(out)); sys.exit(0)
x0, y0, x1, y1 = win
red = (L[..., 0] > 200) & (L[..., 1] < 110) & (L[..., 2] < 110)
rows = np.where(red[y0:y1, x0:x1].sum(axis=1) > 10)[0]
top = y0 + (int(rows.min()) - 4 if len(rows) else (y1 - y0) // 4)
bl, br = L[y0:top, x0:x1], R[y0:top, x0:x1]
def overlay(q):
    grey = (np.abs(q - 40) <= 8).all(axis=2); black = (q <= 8).all(axis=2)
    return int((~grey & ~black).sum())
out.update({"band": [x0, y0, x1, top], "overlay_px_left": overlay(bl), "overlay_px_right": overlay(br),
            "band_px_differ": int((bl != br).any(axis=2).sum()), "band_px": int(bl.shape[0] * bl.shape[1])})
print(json.dumps(out))
