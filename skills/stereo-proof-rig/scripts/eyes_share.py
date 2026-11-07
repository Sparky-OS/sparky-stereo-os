#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""analyze.py PNG: the shares of the clip's two colours (left view red 200,0,0, right view blue 0,0,200) in the whole
picture, its left half and its right half, and the picture size, as one JSON line. A stereo capture is both eyes side
by side, left eye first (twice the output's width)."""
import json, sys
import numpy as np
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
h, w, _ = a.shape
def shares(p):
    r = (p[..., 0] > 150) & (p[..., 1] < 60) & (p[..., 2] < 60)
    b = (p[..., 2] > 150) & (p[..., 0] < 60) & (p[..., 1] < 60)
    n = p.shape[0] * p.shape[1]
    return round(float(r.sum()) / n, 4), round(float(b.sum()) / n, 4)
half = w // 2
res = {"size": [w, h], "whole": shares(a), "left_half": shares(a[:, :half]), "right_half": shares(a[:, half:])}
# the eyes differ where the video differs
res["halves_equal"] = bool((a[:, :half] == a[:, half:2 * half]).all()) if w % 2 == 0 else None
print(json.dumps(res))
