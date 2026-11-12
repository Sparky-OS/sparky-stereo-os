#!/usr/bin/env python3
"""The per-view drawing against the prediction (ORDER 508, milestone 3): m3_views.py DIR TAG
xrtest.js drew the scene into a left and a right view with parallel axes 64 mm apart and both frustums meeting at
D = 3 m. For points of the scene (the wall's centre, the crate's top, the barrel's top, the floor in front) the
prediction is: the same row in both views (no vertical disparity), and a horizontal disparity, right view minus left,
of (n / r) * ipd * (1/D - 1/Z) in normalised units (Z the point's depth along the camera's axis), times W/2 pixels.
Measured: the left view's 31 by 31 patch around the predicted place, found in the right view by normalised
cross-correlation within 60 pixels across and 6 down."""
import json, math, sys
import numpy as np
from PIL import Image
d, tag = sys.argv[1], sys.argv[2]
v = json.load(open('%s/%s-views.json' % (d, tag)))
L = np.asarray(Image.open('%s/%s-left.png' % (d, tag)).convert('L'), float)
R = np.asarray(Image.open('%s/%s-right.png' % (d, tag)).convert('L'), float)
W, H, D, ipd = v['W'], v['H'], v['D'], v['ipd']
cam = np.array(v['camera']).reshape(4, 4).T          # column-major in the file
inv = np.linalg.inv(cam)
t = math.tan(math.radians(v['yfovDeg']) / 2)
aspect = W / H
pts = {'wall centre': (0, 1.2, -2), 'wall left end': (-1.6, 1.6, -2), 'crate top': (-1.25, 0.8, -0.35), 'barrel front': (1.3, 0.45, 0.85),
       'plinth front': (1.0, 0.35, -0.85), 'floor front': (0.3, 0, 1.8)}
print('| point | depth Z | predicted disparity | measured | vertical |')
print('|---|---|---|---|---|')
worst = 0
for name, p in pts.items():
    e = inv @ np.array([*p, 1.0])
    Z = -e[2]
    # the left eye sits at -ipd/2 on the camera's x; its view of the point
    xl = (e[0] + ipd / 2) / (Z * t * aspect) - (ipd / 2) / (D * t * aspect)
    yl = e[1] / (Z * t)
    px, py = (xl + 1) / 2 * W, (1 - yl) / 2 * H
    pred = (1 / (t * aspect)) * ipd * (1 / D - 1 / Z) * W / 2
    x0, y0 = int(round(px)), int(round(py))
    a = L[y0 - 15:y0 + 16, x0 - 15:x0 + 16]
    a = (a - a.mean()) / (a.std() + 1e-9)
    best = (-2, 0, 0)
    for dy in range(-6, 7):
        for dx in range(-60, 61):
            b = R[y0 + dy - 15:y0 + dy + 16, x0 + dx - 15:x0 + dx + 16]
            if b.shape != a.shape:
                continue
            b = (b - b.mean()) / (b.std() + 1e-9)
            c = (a * b).mean()
            if c > best[0]:
                best = (c, dx, dy)
    worst = max(worst, abs(best[1] - pred))
    print('| %s | %.2f m | %+.1f px | %+d px (correlation %.2f) | %+d px |' % (name, Z, pred, best[1], best[0], best[2]))
print('\nlargest difference from the prediction: %.1f px (whole pixels measured)' % worst)
