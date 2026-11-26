#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""check_two.py CAPTURE.png OUTPUT_WIDTH

Two stereo areas in one window (glarea-stereo-test3 --two: 480x270 and 240x135 under it): the capture holds both eyes;
in the left eye two red fields and no blue, in the right eye two blue fields at the same places and no red; outside
the fields the eyes are identical. Exits 1 when a check fails.
"""
import sys

import numpy as np
from PIL import Image


def fields(eye, colour):
    r, g, b = (eye[:, :, i] for i in range(3))
    m = (r > 200) & (g < 60) & (b < 60) if colour == "red" else (b > 200) & (r < 60) & (g < 60)
    rows = np.nonzero(m.any(axis=1))[0]
    out = []
    if rows.size == 0:
        return out
    start = prev = rows[0]
    for y in list(rows[1:]) + [None]:
        if y is None or y != prev + 1:
            cols = np.nonzero(m[start:prev + 1].any(axis=0))[0]
            out.append((int(cols.min()), int(start), int(cols.max()) + 1, int(prev) + 1))
            if y is not None:
                start = y
        if y is not None:
            prev = y
    return out


def main():
    img = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(np.int32)
    width = int(sys.argv[2])
    ok = True

    def row(passed, text):
        nonlocal ok
        ok = ok and passed
        print(("PASS " if passed else "FAIL ") + text)

    row(img.shape[1] == 2 * width, "the capture is both eyes (width %d, output %d)" % (img.shape[1], width))
    left, right = img[:, :width], img[:, width:2 * width]
    lr, lb, rb, rr = fields(left, "red"), fields(left, "blue"), fields(right, "blue"), fields(right, "red")
    size = lambda f: (f[2] - f[0], f[3] - f[1])
    row(len(lr) == 2 and not lb, "left eye: two red fields %s, no blue" % [size(f) for f in lr])
    row(len(rb) == 2 and not rr, "right eye: two blue fields %s, no red" % [size(f) for f in rb])
    row(lr == rb, "the fields are at the same places in both eyes %s %s" % (lr, rb))
    diff = np.abs(left - right).max(axis=2) > 0
    for x0, y0, x1, y1 in lr:
        diff[y0 - 1:y1 + 1, x0 - 1:x1 + 1] = False
    row(not diff.any(), "outside the fields the eyes are identical (%d samples differ)" % int(diff.sum()))
    sys.exit(0 if ok else 1)


main()
