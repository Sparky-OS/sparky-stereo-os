#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""check_colour.py CAPTURE.png OUTPUT_WIDTH PATCHES.txt [--expect stereo|mono] [--tol N] [--raw]

Reads a ScreenShot2 capture of glarea-stereo-test drawn with --patch: finds the area by its frame in each eye, reads the
middle of each patch and compares it with the sRGB value PATCHES.txt expects (the third column of colour_values.py),
within --tol levels (default 3). A stereo capture is twice the output's width: the left half must carry the red eye tag,
the right half the blue one, and the patches must be equal in both. --raw expects the written values themselves times
255 instead (the model in which the compositor ignores the colour state: a correct run must fail it).
Prints one line per check and exits 1 if any fails.
"""
import sys

import numpy as np
from PIL import Image

FRAME = 4


def find_area(a):
    r, g, b = (a[:, :, i].astype(np.int32) for i in range(3))
    frame = (g > r + 60) & (g > b + 60) & (g > 120)
    if not frame.any():
        return None
    ys, xs = np.nonzero(frame)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def main():
    args = sys.argv[1:]
    path, width, patches_file = args[0], int(args[1]), args[2]
    expect = args[args.index("--expect") + 1] if "--expect" in args else "mono"
    tol = int(args[args.index("--tol") + 1]) if "--tol" in args else 3
    raw = "--raw" in args
    patches = []
    for line in open(patches_file):
        name, written, shown = line.split()
        patches.append((name, [float(v) for v in written.split(",")], [int(v) for v in shown.split(",")]))
    a = np.asarray(Image.open(path).convert("RGB"))
    h, w = a.shape[:2]
    ok = True

    def row(passed, text):
        nonlocal ok
        ok = ok and passed
        print(("PASS " if passed else "FAIL ") + text)

    stereo = w == 2 * width
    row(stereo == (expect == "stereo"), "the capture is %s (width %d for an output of %d)" % ("both eyes" if stereo else "one picture", w, width))
    eyes = [("left", a[:, :width]), ("right", a[:, width:])] if stereo else [("one", a[:, :width])]
    read = {}
    for eye, img in eyes:
        box = find_area(img)
        if box is None:
            row(False, "%s: the area's frame is found" % eye)
            continue
        x0, y0, x1, y1 = box
        aw, ah = x1 - x0, y1 - y0
        tag = ah // 6
        t = img[y1 - FRAME - tag // 2, x0 + FRAME + tag // 2].astype(int)
        want = {"left": "red", "right": "blue", "one": "white"}[eye]
        seen = "red" if t[0] > 150 and t[2] < 100 else "blue" if t[2] > 150 and t[0] < 100 else "white" if min(t) > 150 else "other"
        row(seen == want, "%s: area %dx%d at %d,%d, eye tag %s (%s wanted, sample %s)" % (eye, aw, ah, x0, y0, seen, want, t.tolist()))
        n = len(patches)
        for i, (name, written, shown) in enumerate(patches):
            px0 = FRAME + tag + i * (aw - 2 * FRAME - tag) // n
            px1 = FRAME + tag + (i + 1) * (aw - 2 * FRAME - tag) // n
            got = img[y0 + 3 * ah // 4, x0 + (px0 + px1) // 2].astype(int)
            read[(eye, name)] = got
            target = [round(255 * min(max(v, 0), 1)) for v in written] if raw else shown
            d = int(np.abs(got - np.array(target)).max())
            row(d <= tol, "%s: patch %s shows %s, %s %s (off by %d)" % (eye, name, got.tolist(), "the written values would be" if raw else "expected", target, d))
    if stereo:
        same = all((read.get(("left", n)) == read.get(("right", n))).all() for n, _, _ in patches if ("left", n) in read and ("right", n) in read)
        row(same, "the patches are equal in both eyes")
    sys.exit(0 if ok else 1)


main()
