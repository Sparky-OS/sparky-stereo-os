#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""halves.py FRAME.ppm [...]: for a side by side (full) scanout, the pixels that differ between its two halves,
where they are, and the mean colour of each half inside that area. 0 differing pixels means one eye twice."""
import sys
import numpy as np
from PIL import Image
for path in sys.argv[1:]:
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    w = a.shape[1] // 2
    l, r = a[:, :w], a[:, w:2 * w]
    d = np.abs(l - r).sum(axis=2) > 24
    n = int(d.sum())
    line = "%s %dx%d differing pixels between the halves: %d" % (path.split("/")[-1], a.shape[1], a.shape[0], n)
    if n:
        ys, xs = np.nonzero(d)
        line += " in x %d..%d y %d..%d; left mean %s right mean %s" % (
            xs.min(), xs.max(), ys.min(), ys.max(), l[d].mean(axis=0).round().astype(int).tolist(), r[d].mean(axis=0).round().astype(int).tolist())
    print(line)
