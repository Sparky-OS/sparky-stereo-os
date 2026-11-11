#!/usr/bin/env python3
"""Each procedure's 16 tiles of 512, drawn through their windows, put together against its whole at 2048
(milestone 2e): m2e_tilecheck.py NATIVEDIR NAME...   (NAME.ppm and NAME-t-R-C.ppm)"""
import sys
import numpy as np
from PIL import Image
d = sys.argv[1]
for n in sys.argv[2:]:
    w = np.asarray(Image.open('%s/%s.ppm' % (d, n)).convert('RGB')).astype(int)
    t = np.zeros_like(w)
    for r in range(4):
        for c in range(4):
            t[r * 512:(r + 1) * 512, c * 512:(c + 1) * 512] = np.asarray(Image.open('%s/%s-t-%d-%d.ppm' % (d, n, r, c)).convert('RGB')).astype(int)
    df = np.abs(w - t)
    print('%s: the 16 tiles put together against the whole: largest difference %d, pixels that differ %d' % (n, df.max(), int((df.max(axis=2) > 0).sum())))
