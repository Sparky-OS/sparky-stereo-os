#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""columns.py CAPTURE.png EYE X0 Y0 [--output-width N] [--search N]: read the column code of make-barcode-fixtures.sh from the part of a
capture that shows one eye (EYE left or right; a stereo capture is both eyes side by side, each output-width wide), with the view's
top-left corner at X0 Y0 in the eye's picture, and report how many of the 960 columns carry their own number and the eye marker.
The corner is searched within +-N pixels (default 3). One JSON line."""
import json, sys
import numpy as np
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert("L")).astype(int)
eye, x0, y0 = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
ow = 1920
search = 3
for i, t in enumerate(sys.argv):
    if t == "--output-width": ow = int(sys.argv[i + 1])
    if t == "--search": search = int(sys.argv[i + 1])
W, H = 960, 540
base = x0 + (ow if eye == "right" else 0)
def decode(bx, by):
    if bx < 0 or by < 0 or bx + W > a.shape[1] or by + H > a.shape[0]:
        return None
    ok = 0; bad = []
    marker = a[by + 410:by + 430, bx:bx + W].mean(axis=0) > 127
    eye_ok = bool(marker.all() if eye == "right" else (~marker).all())
    for x in range(W):
        n = 0
        for k in range(10):
            n |= int(a[by + 40 * k + 10:by + 40 * k + 30, bx + x].mean() > 127) << k
        if n == x: ok += 1
        elif len(bad) < 5: bad.append([x, n])
    return ok, bad, eye_ok
best = None
for dy in range(-search, search + 1):
    for dx in range(-search, search + 1):
        r = decode(base + dx, y0 + dy)
        if r and (best is None or r[0] > best[0][0]):
            best = (r, dx, dy)
if best is None:
    print(json.dumps({"error": "the view is outside the capture"})); sys.exit(1)
(r, dx, dy) = best
print(json.dumps({"eye": eye, "columns_ok": r[0], "columns": W, "eye_marker_ok": r[2], "offset": [dx, dy], "first_bad": r[1]}))
