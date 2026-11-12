#!/usr/bin/env python3
"""What a blend from the procedure into its picture would have to cross (milestone 2c, "against the final form"):
per texture, the difference between the procedure's drawing and the picture at full size, as a person would see it
change if the picture replaced the drawing at once: the mean difference of the colours averaged over blocks of 256,
64 and 16 pixels (the coarse look) and per pixel (the detail), in levels of 255; and the share of 64-pixel blocks whose
mean colour moves by more than 6 levels (a step the eye notices on a flat surface, the order of a just noticeable
difference in sRGB at mid grey).

m2c_blend.py RENDERDIR NAME... > table.md"""
import sys
import numpy as np
from PIL import Image
S = '/var/tmp/procedures-from-pixels-508'
ren = sys.argv[1]
print('| texture | 256 px blocks | 64 px blocks | 16 px blocks | per pixel | 64 px blocks moving more than 6 levels |')
print('|---|---|---|---|---|---|')
for n in sys.argv[2:]:
    a = np.asarray(Image.open('%s/m2b/full/%s.ppm' % (S, n)).convert('RGB')).astype(float)
    b = np.asarray(Image.open('%s/%s.ppm' % (ren, n)).convert('RGB')).astype(float)
    row = [n]
    for k in (256, 64, 16):
        h = a.shape[0] // k
        am = a.reshape(h, k, h, k, 3).mean((1, 3))
        bm = b.reshape(h, k, h, k, 3).mean((1, 3))
        row.append('%.1f' % np.abs(am - bm).mean())
        if k == 64:
            big = (np.abs(am - bm).max(2) > 6).mean()
    row.append('%.1f' % np.abs(a - b).mean())
    row.append('%.0f %%' % (100 * big))
    print('| ' + ' | '.join(row) + ' |')

# The same, when the picture arrives coarse first (a small copy first, as a mip chain streamed from its smallest level):
# the drawing's coarse look taken from the picture's copy of side 2048/k, the procedure's own detail kept above it.
# What still changes when the full picture replaces that: per pixel, and over 4 pixel blocks (the coarser blocks match
# by construction once the copy is finer than them).
print()
print('| texture | coarse look from the picture\'s 32 px copy: per pixel, 4 px blocks | from its 128 px copy | from its 512 px copy |')
print('|---|---|---|---|')
for n in sys.argv[2:]:
    a = np.asarray(Image.open('%s/m2b/full/%s.ppm' % (S, n)).convert('RGB')).astype(float)
    b = np.asarray(Image.open('%s/%s.ppm' % (ren, n)).convert('RGB')).astype(float)
    row = [n]
    for k in (64, 16, 4):
        s = a.shape[0] // k
        def low(x):
            m = x.reshape(s, k, s, k, 3).mean((1, 3))
            return np.repeat(np.repeat(m, k, 0), k, 1)
        comp = np.clip(low(a) + (b - low(b)), 0, 255)
        d = np.abs(a - comp)
        h = a.shape[0] // 4
        d16 = np.abs(a.reshape(h, 4, h, 4, 3).mean((1, 3)) - comp.reshape(h, 4, h, 4, 3).mean((1, 3))).mean()
        row.append('%.1f, %.1f' % (d.mean(), d16))
    print('| ' + ' | '.join(row) + ' |')
