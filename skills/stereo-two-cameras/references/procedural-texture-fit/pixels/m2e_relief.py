#!/usr/bin/env python3
"""The relief (the material's height, a 16-bit PGM from p2p render height=) as an 8-bit picture for a sheet
(milestone 2e): m2e_relief.py IN.pgm OUT.ppm [lit]   grey: black low, white high; lit: the height lit from the top
left (a hillshade), so the order of the layers in the relief can be seen."""
import sys
import numpy as np
from PIL import Image
h = np.asarray(Image.open(sys.argv[1])).astype(np.float64) / 65535.0
if len(sys.argv) > 3 and sys.argv[3] == 'lit':
    gy, gx = np.gradient(h * 40.0)
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    L = np.array([-1.0, -1.0, 1.4]); L /= np.linalg.norm(L)
    v = np.clip(n @ L, 0, 1)
else:
    v = h
Image.fromarray((v * 255 + 0.5).astype(np.uint8)).convert('RGB').save(sys.argv[2])
