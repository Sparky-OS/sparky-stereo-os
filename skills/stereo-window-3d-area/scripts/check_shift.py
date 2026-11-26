#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""check_shift.py CAPTURE.png OUTPUT_WIDTH [--expect stereo|mono] [--min N]

For a program that draws one scene with a camera for each eye (gtk3-demo's OpenGL Area): a stereo capture is twice the
output's width; the two eyes are equal except in one region (the scene), and there the right eye's picture is the left
one moved sideways. Prints the region, the horizontal shift that best moves the left eye's region onto the right
one's and the share of samples that still differ after it, and checks: two eyes, a region that differs, a shift of at
least --min samples (default 4) that leaves under 5 % of the region's samples more than 24 levels apart. --expect mono:
one picture. Exits 1 when a check fails.
"""
import sys

import numpy as np
from PIL import Image


def main():
    a = sys.argv[1:]
    path, width = a[0], int(a[1])
    expect = a[a.index("--expect") + 1] if "--expect" in a else "stereo"
    minimum = int(a[a.index("--min") + 1]) if "--min" in a else 4
    img = np.asarray(Image.open(path).convert("RGB")).astype(np.int32)
    ok = True

    def row(passed, text):
        nonlocal ok
        ok = ok and passed
        print(("PASS " if passed else "FAIL ") + text)

    stereo = img.shape[1] == 2 * width
    row(stereo == (expect == "stereo"), "the capture is %s (width %d, output %d)" % ("both eyes" if stereo else "one picture", img.shape[1], width))
    if not stereo or expect != "stereo":
        sys.exit(0 if ok else 1)
    left, right = img[:, :width], img[:, width:]
    diff = np.abs(left - right).max(axis=2) > 24
    row(diff.any(), "the eyes differ somewhere (%d samples)" % int(diff.sum()))
    if not diff.any():
        sys.exit(1)
    ys, xs = np.nonzero(diff)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    best = None
    for s in range(-80, 81):
        lx0, lx1 = max(x0, x0 - s), min(x1, x1 - s)
        if lx1 - lx0 < 8:
            continue
        lw = left[y0:y1, lx0:lx1]
        rw = right[y0:y1, lx0 + s:lx1 + s]
        bad = (np.abs(lw - rw).max(axis=2) > 24).mean()
        if best is None or bad < best[1]:
            best = (s, bad)
    print("region %d,%d to %d,%d; best shift %+d samples, %.2f %% of the region still differs" % (x0, y0, x1, y1, best[0], 100 * best[1]))
    row(abs(best[0]) >= minimum, "the right eye's scene is the left one moved sideways by at least %d samples (%+d)" % (minimum, best[0]))
    row(best[1] < 0.05, "after that shift the eyes agree (%.2f %% differ)" % (100 * best[1]))
    outside = diff.copy()
    outside[y0:y1, x0:x1] = False
    row(not outside.any(), "outside the scene the eyes are identical")
    sys.exit(0 if ok else 1)


main()
