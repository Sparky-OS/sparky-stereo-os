#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""pairs.py FRAME.ppm [...]: for a side by side (full) frame showing pairstress windows, the disparity of each
window's near square against its reference square: (near - reference) in the left half minus the same in the right
half, in pixels. A window drawn as a pair reads 8.0, one picture in both eyes reads 0.0, a window not on the screen
reads "absent"."""
import sys
import numpy as np
from PIL import Image
WINDOWS = {"A": ((0, 0, 255), (255, 0, 0)), "B": ((0, 255, 0), (255, 0, 255))}
def centre(half, colour):
    m = (np.abs(half - np.array(colour)).sum(axis=2) < 60)
    n = int(m.sum())
    if n < 400:
        return None, n
    return float(np.nonzero(m)[1].mean()), n
for path in sys.argv[1:]:
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    w = a.shape[1] // 2
    out = []
    for name, (reference, near) in WINDOWS.items():
        v = [centre(h, c) for h in (a[:, :w], a[:, w:2 * w]) for c in (reference, near)]
        if any(x[0] is None for x in v):
            out.append("%s absent" % name)
            continue
        (rl, _), (nl, npx), (rr, _), (nr, _) = v
        out.append("%s disparity %.1f (near square %d px)" % (name, (nl - rl) - (nr - rr), npx))
    print(path.split("/")[-1], "; ".join(out))
