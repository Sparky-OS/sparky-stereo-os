#!/usr/bin/env python3
"""Cut each picture at full size into its four quarters (milestone 2d): OUT/NAME/qR-C.full.ppm at full size (1024 of a
2048 picture), beside milestone 2's box-averaged quarter at 512 (m2/tiles/NAME/L1-R-C.ppm), which the fitter reads as
the quarter's whole picture. m2d_quarters.py FULLDIR OUT NAME..."""
import os, sys
from PIL import Image

full, out = sys.argv[1], sys.argv[2]
for name in sys.argv[3:]:
    im = Image.open(os.path.join(full, name + '.ppm')).convert('RGB')
    w, h = im.size
    if w != h or w % 2:
        sys.exit('%s: the picture must be square and even (%dx%d)' % (name, w, h))
    s = w // 2
    os.makedirs(os.path.join(out, name), exist_ok=True)
    for r in range(2):
        for c in range(2):
            im.crop((c * s, r * s, (c + 1) * s, (r + 1) * s)).save(os.path.join(out, name, 'q%d-%d.full.ppm' % (r, c)))
    print(name, 'quarters of', s)
