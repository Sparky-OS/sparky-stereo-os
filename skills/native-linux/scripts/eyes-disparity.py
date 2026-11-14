#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""eyes-disparity.py SHOT.png [--win X Y W H] [--json OUT]: block-match the two eyes of a stereo capture along the same row.
Disparity = x in the right eye minus x in the left eye, in pixels (negative: in front of the screen).
Only blocks with horizontal texture are used; the vertical check is separate (the best row shift must be 0)."""
import sys, json
import numpy as np
from PIL import Image
a = sys.argv[1:]; shot = a[0]
win = (460, 240, 1000, 600)
if '--win' in a: i = a.index('--win'); win = tuple(int(v) for v in a[i+1:i+5])
out = a[a.index('--json')+1] if '--json' in a else None
roi = (250, 20, 950, 580)          # inside the window: away from the program's 2D parts on the left
if '--roi' in a: i = a.index('--roi'); roi = tuple(int(v) for v in a[i+1:i+5])
im = Image.open(shot).convert('L'); W, H = im.size
if W != 3840: print('NOT-STEREO %dx%d' % (W, H)); sys.exit(2)
g = np.asarray(im, dtype=np.float32)
x0, y0, w, h = win
Lw = g[y0:y0+h, x0:x0+w]; Rw = g[y0:y0+h, 1920+x0:1920+x0+w]
B = 17; R = int(a[a.index('--range')+1]) if '--range' in a else 140
res = []
for by in range(roi[1], roi[3]-B, 12):
    for bx in range(roi[0], roi[2]-B, 12):
        blk = Lw[by:by+B, bx:bx+B]
        if np.abs(np.diff(blk, axis=1)).sum() < 600: continue      # no horizontal texture
        best = None; sads = []
        for d in range(-R, R+1):
            xs = bx + d
            if xs < 0 or xs + B > w: sads.append(1e12); continue
            s = float(np.abs(Rw[by:by+B, xs:xs+B] - blk).sum()); sads.append(s)
        k = int(np.argmin(sads)); s0 = sads[k]
        srt = sorted(sads)
        if s0 > 0.06 * 255 * B * B: continue                       # no good match
        if srt[1] < 1e11 and len([v for v in sads if v < s0 * 1.05 + 20]) > 4: continue   # ambiguous (flat or repeating)
        d = k - R
        if 0 < k < 2*R and sads[k-1] < 1e11 and sads[k+1] < 1e11:
            den = sads[k-1] - 2*s0 + sads[k+1]
            if den > 0: d += 0.5 * (sads[k-1] - sads[k+1]) / den
        res.append((bx, by, d))
if not res: print('NO-BLOCKS'); sys.exit(3)
D = np.array([r[2] for r in res])
# vertical: shift the right eye up and down by whole rows, the best overall match must be 0
best = []
for dy in (-2, -1, 0, 1, 2):
    tot = 0.0
    for bx, by, d in res[::3]:
        xs = int(round(bx + d)); ys = by + dy
        if ys < 0 or ys + B > h or xs < 0 or xs + B > w: tot += 1e6; continue
        tot += float(np.abs(Rw[ys:ys+B, xs:xs+B] - Lw[by:by+B, bx:bx+B]).sum())
    best.append(tot)
vert = (-2, -1, 0, 1, 2)[int(np.argmin(best))]
s = dict(blocks=len(res), min=float(D.min()), p10=float(np.percentile(D, 10)), median=float(np.median(D)), p90=float(np.percentile(D, 90)), max=float(D.max()), vertical=vert)
print(json.dumps(s))
if out: json.dump(dict(summary=s, blocks=res), open(out, 'w'))
