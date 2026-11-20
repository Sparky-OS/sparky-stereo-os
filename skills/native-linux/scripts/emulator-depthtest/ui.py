#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""ui.py CAPTURE.png: with the render widget inside Dolphin's main window (its 3D area is a declared child window), the
main window's 2D part (menus, toolbar, status bar: the window minus the child) in both eyes. One JSON line."""
import json, re, sys
import numpy as np
from PIL import Image
path = sys.argv[1]
a = np.asarray(Image.open(path).convert("RGB")).astype(np.int32)
H, W2 = a.shape[:2]; E = W2 // 2
L, R = a[:, :E], a[:, E:]
wins = json.load(open(re.sub(r"-shot\d+\.png$", ".x11.log", path)))["windows"]
child = next((w for w in wins if w["props"].get("_KDE_NET_WM_STEREO_CONTENT") == [3] and w["props"].get("WM_STATE") is None), None)
top = next((w for w in wins if w["props"].get("_KDE_NET_WM_STEREO_CONTENT_CHILDREN")), None)
out = {"file": path.split("/")[-1], "size": [W2, H], "child": child and child["abs"] + child["geom"][2:], "top": top and top["abs"] + top["geom"][2:]}
if not (child and top):
    out["error"] = "no declared child or no top-level listing it"; print(json.dumps(out)); sys.exit(0)
tx, ty = top["abs"]; tw, th = top["geom"][2], top["geom"][3]
cx, cy = child["abs"]; cw, ch = child["geom"][2], child["geom"][3]
if child["props"].get("_KDE_NET_WM_STEREO_CONTENT_VERSION") != [4] and cw > tw:
    cw //= 2
mask = np.zeros((H, E), bool); mask[ty:ty + th, tx:tx + tw] = True; mask[cy:cy + ch, cx:cx + cw] = False
d = (L != R).any(axis=2)
out.update({"ui_px": int(mask.sum()), "ui_px_differ": int((d & mask).sum()),
            "area_px_differ_share": round(float(d[cy:cy + ch, cx:cx + cw].mean()), 4)})
print(json.dumps(out))
