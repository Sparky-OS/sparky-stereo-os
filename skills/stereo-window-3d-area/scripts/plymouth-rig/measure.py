#!/usr/bin/python3 -I
# The parallax of the splash's levels in a frame-packing capture (left eye at line 0, right eye at line 1125, 1920x1080
# each): the wordmark is the logo level, the swirl the base level. The right eye's region is matched against the left
# eye's (shifts -30..30 px, mean absolute difference); a thing popped by d px sits d px to the right in the left eye
# and d px to the left in the right eye, so the match is -d. usage: measure.py PNG [PNG...]
import sys
import numpy as np
from PIL import Image
REGIONS = {'wordmark (logo level)': (865, 975, 730, 1190), 'swirl (base level)': (275, 395, 975, 1135)}
for path in sys.argv[1:]:
    im = np.asarray(Image.open(path).convert('L')).astype(float)
    if im.shape[0] < 2205:
        print('%s: %dx%d, not a frame-packing capture' % (path, im.shape[1], im.shape[0])); continue
    L, R = im[:1080], im[1125:2205]
    row = [path.split('/')[-1]]
    for name, (y0, y1, x0, x1) in REGIONS.items():
        best = min(((np.abs(L[y0:y1, x0:x1] - R[y0:y1, x0 + s:x1 + s]).mean(), s) for s in range(-30, 31)))
        row.append('%s: popped %d px (match error %.2f)' % (name, -best[1], best[0]))
    print('  '.join(row))
