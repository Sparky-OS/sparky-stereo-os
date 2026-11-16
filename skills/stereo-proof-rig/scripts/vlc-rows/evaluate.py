#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""evaluate.py ROWDIR [KIND]: reads the captures of a row and says, per capture, whether the notice is on the picture.
KIND is 3d (default: left eye red, right eye blue, the capture 3840 wide) or 2d (a green picture, the capture 1920 wide).
The picture is a plain colour with a moving white box lower down, so any pixel of the top band of the picture that is not
the colour is text: the count is printed per capture, with the bounding box of the picture and of the text."""
import json, sys, glob, os
import numpy as np
from PIL import Image

row = sys.argv[1]; kind = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "3d"
colour = np.array([255, 0, 0] if kind == "3d" else [0, 128, 0])
res = {}
for f in sorted(glob.glob(os.path.join(row, "cap-*.png")), key=lambda p: float(os.path.basename(p)[4:-4])):
    im = np.asarray(Image.open(f).convert("RGB")).astype(int)
    H, W, _ = im.shape
    eye = im[:, : W // 2] if W >= 3000 else im
    near = (np.abs(eye - colour).sum(axis=2) < 60)
    ys, xs = np.where(near)
    if len(ys) < 1000:
        res[os.path.basename(f)] = {"picture": None}; continue
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    band_h = max(12, int((y1 - y0) * 0.14))
    band = eye[y0:y0 + band_h, x0:x0 + (x1 - x0) // 2]
    other = np.abs(band - colour).sum(axis=2) >= 60
    cnt = int(other.sum())
    box = None
    if cnt:
        oy, ox = np.where(other); box = [int(ox.min() + x0), int(oy.min() + y0), int(ox.max() + x0), int(oy.max() + y0)]
    res[os.path.basename(f)] = {"picture": [int(x0), int(y0), int(x1), int(y1)], "text_pixels": cnt, "text_box": box, "capture": [W, H]}
if "--summary" in sys.argv:
    ts = lambda k: float(k[4:-4])
    pics = [k for k, v in res.items() if v.get("picture")]
    txt = [k for k, v in res.items() if v.get("text_pixels")]
    print(json.dumps({"captures": len(res), "with_picture": len(pics), "with_notice": len(txt),
                      "notice_first_s": min(map(ts, txt)) if txt else None, "notice_last_s": max(map(ts, txt)) if txt else None,
                      "max_text_pixels": max([res[k]["text_pixels"] for k in txt], default=0)}))
else:
    print(json.dumps(res, indent=1))
