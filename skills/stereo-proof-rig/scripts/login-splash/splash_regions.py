#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# splash_regions.py PLAIN.png PAIR.png VARIANT POPPED OUT.json: the Kubabbar Glass loading screen's parts found in the plain
# (2D) capture, as regions for measure-regions.py, each with its predicted right-minus-left disparity (the window, or the
# menu bar look's middle, at the person's popped limit: -round(POPPED) device pixels on a view 1920 wide), and the check
# that the background is at the screen: outside the popped part (and its shift), the two eyes are the same picture.
import json
import sys

import numpy as np
from PIL import Image

plain_p, pair_p, variant, popped, out = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]
plain = np.asarray(Image.open(plain_p).convert("RGB")).astype(float)
pair = np.asarray(Image.open(pair_p).convert("RGB")).astype(float)
H, W = plain.shape[:2]
pred = -int(np.floor(popped * W / 1920 + 0.5))
g = plain.mean(axis=2)
if variant == "window":
    # the light glass window: its pixels are far lighter than the dark background around the middle of the screen
    m = g[:, :] > 150
    m[: H // 6] = False
    ys, xs = np.nonzero(m)
else:
    # the menu bar look's middle: the white logo, the light texts and the track, below the strip
    m = g > 150
    m[: int(H * 0.06)] = False
    ys, xs = np.nonzero(m)
x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
regions = []
if variant == "window":
    regions.append({"name": "window", "method": "boundary", "predicted": pred,
                    "x_edge": [x0 - 20, (y0 + y1) // 2 - 40, x0 + 20, (y0 + y1) // 2 + 40],
                    "y_edge": [(x0 + x1) // 2 - 60, y0 - 20, (x0 + x1) // 2 + 60, y0 + 20]})
    cy = y0 + 28 + 10  # below the title bar: the logo and the name, matched on their own edges
    regions.append({"name": "logo-and-name", "box": [x0 + 40, cy, x1 - 40, cy + 170], "predicted": pred})
else:
    regions.append({"name": "middle", "box": [x0 - 10, y0 - 10, x1 + 10, y1 + 10], "predicted": pred})
    regions.append({"name": "strip", "box": [400, 4, W - 400, int(H * 0.04)], "predicted": 0, "normalize_mean": True})
json.dump(regions, open(out, "w"), indent=1)
# the background at the screen: compare the eyes outside the popped box widened by the shift
L, R = pair[:, :W], pair[:, W:]
mask = np.ones((H, W), bool)
pad = abs(pred) + 12
mask[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad] = False
diff = np.abs(L - R).max(axis=2)[mask]
print(json.dumps({"box": [x0, y0, x1, y1], "predicted": pred, "outside_pixels": int(mask.sum()),
                  "outside_differing": int((diff > 2).sum()), "outside_max_diff": float(diff.max())}))
