#!/usr/bin/env python3
"""Which half of a side-by-side picture is the left eye?  (numpy and Pillow, run with python3 -I)

eye_order.py IMAGE AX AY AW AH BX BY BW BH NEAR_X NEAR_Y FAR_X FAR_Y [BLOCK]
A and B are the two views as boxes (x y width height) of IMAGE, A the one on the left of the file.
NEAR and FAR are two points in view A's own coordinates, a near object and a far one.
For each point the block around it is matched along the row in view B; d = x_A - x_B.
An object nearer than another has a larger d when A is the LEFT eye (the left eye sees it further right).
Prints both d and the verdict.  The rule: near minus far, never the absolute sign, because the zero-parallax
plane of a pair is wherever its maker put it.
"""
import sys

import numpy as np
from PIL import Image


def match(a, b, x, y, block, rng):
    blk = a[y:y + block, x:x + block]
    best = None
    for d in range(-rng, rng + 1):
        xs = x - d
        if xs < 0 or xs + block > b.shape[1]:
            continue
        cand = b[y:y + block, xs:xs + block]
        c = np.corrcoef(blk.ravel(), cand.ravel())[0, 1]
        if best is None or c > best[0]:
            best = (c, d)
    return best[1], best[0]


if __name__ == '__main__':
    path = sys.argv[1]
    ax, ay, aw, ah, bx, by, bw, bh, nx, ny, fx, fy = map(int, sys.argv[2:14])
    block = int(sys.argv[14]) if len(sys.argv) > 14 else 200
    g = np.asarray(Image.open(path).convert('L'), float)
    a = g[ay:ay + ah, ax:ax + aw]
    b = g[by:by + bh, bx:bx + bw]
    dn, cn = match(a, b, nx, ny, block, 80)
    df, cf = match(a, b, fx, fy, block, 80)
    print('near d=%d (corr %.2f), far d=%d (corr %.2f), near minus far = %d' % (dn, cn, df, cf, dn - df))
    print('A is the LEFT eye' if dn - df > 0 else 'A is the RIGHT eye (cross-eyed order)' if dn - df < 0 else 'no depth difference measured')
