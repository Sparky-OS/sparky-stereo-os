#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""ORDER 573: read vk-views captures. Each capture holds both eyes side by side. In each eye the pixels of the four
pure colours are counted, and the halves of their bounding box say which colour leads. The verdict per capture:
PAIR (left eye red, right eye blue), FLAT (each eye: left half green, right half yellow; the one picture whole),
HALVES (left eye green only, right eye yellow only: one picture shown as a pair), OTHER.
usage: views.py CASEDIR [CASEDIR...]"""
import sys, os, glob, json
import numpy as np
from PIL import Image

COLS = {'red': (255, 0, 0), 'blue': (0, 0, 255), 'green': (0, 255, 0), 'yellow': (255, 255, 0)}

def masks(eye):
    e = eye.astype(int)
    out = {}
    for n, (r, g, b) in COLS.items():
        out[n] = (abs(e[..., 0] - r) < 40) & (abs(e[..., 1] - g) < 40) & (abs(e[..., 2] - b) < 40)
    return out

def eye_read(eye):
    m = masks(eye)
    any_ = np.zeros(eye.shape[:2], bool)
    for v in m.values():
        any_ |= v
    if not any_.any():
        return {'count': 0}
    ys, xs = np.nonzero(any_)
    x0, x1 = xs.min(), xs.max() + 1
    mid = (x0 + x1) // 2
    r = {'box': [int(x0), int(ys.min()), int(x1), int(ys.max()) + 1], 'count': int(any_.sum())}
    for half, sl in (('lefthalf', slice(x0, mid)), ('righthalf', slice(mid, x1))):
        counts = {n: int(v[:, sl].sum()) for n, v in m.items()}
        r[half] = max(counts, key=counts.get)
        r[half + '_counts'] = counts
    r['counts'] = {n: int(v.sum()) for n, v in m.items()}
    return r

def verdict(L, R):
    if L.get('count', 0) == 0 or R.get('count', 0) == 0:
        return 'NONE'
    lc, rc = L['counts'], R['counts']
    if lc['red'] > 0.95 * L['count'] and rc['blue'] > 0.95 * R['count']:
        return 'PAIR'
    if (L['lefthalf'], L['righthalf'], R['lefthalf'], R['righthalf']) == ('green', 'yellow', 'green', 'yellow') \
            and lc['yellow'] > 0.3 * L['count'] and rc['green'] > 0.3 * R['count']:
        return 'FLAT'
    if lc['green'] > 0.95 * L['count'] and rc['yellow'] > 0.95 * R['count']:
        return 'HALVES'
    return 'OTHER'

for d in sys.argv[1:]:
    shots = {}
    for line in open(os.path.join(d, 'shots.txt')) if os.path.exists(os.path.join(d, 'shots.txt')) else []:
        n, _, t = line.split()
        shots[n] = t
    res = []
    for p in sorted(glob.glob(os.path.join(d, 'shot-*.png'))):
        a = np.asarray(Image.open(p).convert('RGB'))
        w = a.shape[1] // 2
        L, R = eye_read(a[:, :w]), eye_read(a[:, w:])
        name = os.path.basename(p)[:-4]
        res.append({'shot': name, 'at': shots.get(name), 'verdict': verdict(L, R), 'left': L, 'right': R,
                    'eyes_differ_px': int((a[:, :w] != a[:, w:]).any(axis=2).sum())})
    json.dump(res, open(os.path.join(d, 'views.json'), 'w'), indent=1)
    print(os.path.basename(d.rstrip('/')), ' '.join('%s@%s:%s' % (r['shot'][5:], r['at'], r['verdict']) for r in res))
