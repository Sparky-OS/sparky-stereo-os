#!/usr/bin/env python3
"""analyze.py CAPTURE.png SUNK POPPED [--view-width W]: the three planes' mean right-minus-left shifts (px) against the
prediction of the fit rule (edges are paired by polarity, so a shift is unambiguous below half the stripe period, 10.7 px) for the test scene (planes at w=40, 80, 160, background at the far plane w=300) and the share
of differing pixels between the eyes inside the render window. The limits are pixels of a view 1920 wide; the view is
W px wide (default 640, the window's one-view width)."""
import sys, numpy as np
from PIL import Image
path, S, P = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
W = 640
if "--view-width" in sys.argv: W = int(sys.argv[sys.argv.index("--view-width") + 1])
a = np.asarray(Image.open(path).convert("RGB")).astype(int)
E = a.shape[1] // 2
L, R = a[:, :E], a[:, E:]
ys, xs = np.where(L.sum(axis=2) > 0)
x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
diff = (L[y0:y1, x0:x1] != R[y0:y1, x0:x1]).any(axis=2).mean()
# prediction
u = {w: 1.0 / w for w in (40, 80, 160, 300)}
umax, umin = u[40], u[300]
s, p = S / 1920.0, P / 1920.0
if s + p > 0:
    b = (p + s) / (umax - umin); a_ = s + b * umin
else:
    b = a_ = 0.0
pred = {w: (a_ - b * uu) * W for w, uu in u.items()}
masks = {40: lambda q: (q[..., 0] > 200) & (q[..., 1] < 90) & (q[..., 2] < 90),
         80: lambda q: (q[..., 1] > 200) & (q[..., 0] < 90) & (q[..., 2] < 90),
         160: lambda q: (q[..., 2] > 200) & (q[..., 0] < 120) & (q[..., 1] < 120)}
def edges(row, rising):
    d = np.diff(row.astype(int))
    return np.where(d == (1 if rising else -1))[0] + 1
y = (y0 + y1) // 2
print("%s limits %g/%g, view %d px: eyes differ in %.4f of the window's pixels; render area x %d..%d y %d..%d" % (path.split("/")[-1], S, P, W, diff, x0, x1, y0, y1))
for w, m in masks.items():
    d = []
    for rising in (True, False):
        el, er = edges(m(L[y]), rising), edges(m(R[y]), rising)
        d += [er[np.argmin(np.abs(er - e))] - e for e in el[2:-2] if len(er) and np.abs(er - e).min() <= 15]
    d = np.array(d, dtype=float)
    if not len(d):
        print("  plane w=%-3d no edges in one eye" % w); continue
    print("  plane w=%-3d measured mean %+.2f px (n=%d, min %+d max %+d), predicted %+.2f px, error %+.2f" % (w, d.mean(), len(d), d.min(), d.max(), pred[w], d.mean() - pred[w]))
print("  background (w=300) predicted %+.2f px, nearest pixel (w=40) predicted %+.2f px" % (pred[300], pred[40]))
