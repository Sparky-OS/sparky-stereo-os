#!/usr/bin/env python3
"""Band energies of a picture and a drawing, region by region (milestone 2e): does a quarter's (or a tile's) fit
lose the scale above its own canvas? m2e_bands.py PICTURE DRAWING COLS ROWS [SIDE]
Both are read at SIDE (default 1024), luminance; each region (a tile of COLS x ROWS) is cut and its Laplacian pyramid
band energies (standard deviation of each band, box filters of 2^k pixels) printed for the picture and the drawing,
with their ratio; the coarse bands are those of 1/8 of the region and larger."""
import sys
import numpy as np
from PIL import Image

def lum(p, side):
    im = Image.open(p).convert('RGB').resize((side, side), Image.BOX)
    a = np.asarray(im, dtype=np.float64) / 255.0
    return a @ np.array([0.299, 0.587, 0.114])

def boxdown(a):
    h, w = a.shape
    return a[:h - h % 2, :w - w % 2].reshape(h // 2, 2, w // 2, 2).mean(axis=(1, 3))

def bands(a):
    out = []
    cur = a
    while min(cur.shape) >= 4:
        d = boxdown(cur)
        up = np.kron(d, np.ones((2, 2)))[:cur.shape[0], :cur.shape[1]]
        out.append(float((cur - up).std()))
        cur = d
    out.append(float(cur.std()))
    return out

pic, drw, cols, rows = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
side = int(sys.argv[5]) if len(sys.argv) > 5 else 1024
A, B = lum(pic, side), lum(drw, side)
th, tw = side // rows, side // cols
tot = None
for r in range(rows):
    for c in range(cols):
        a = A[r * th:(r + 1) * th, c * tw:(c + 1) * tw]
        b = B[r * th:(r + 1) * th, c * tw:(c + 1) * tw]
        ba, bb = bands(a), bands(b)
        ratio = [y / x if x > 1e-9 else 0 for x, y in zip(ba, bb)]
        tot = ratio if tot is None else [t + q for t, q in zip(tot, ratio)]
        print('tile %d-%d mean %.3f/%.3f  ' % (r, c, a.mean(), b.mean()) + ' '.join('%d:%.3f/%.3f' % (2 ** k, x, y) for k, (x, y) in enumerate(zip(ba, bb))))
n = cols * rows
print('drawing/picture per band (pixels of the band at side %d, region %dx%d): ' % (side, tw, th) + ' '.join('%d:%.2f' % (2 ** k, t / n) for k, t in enumerate(tot)))
