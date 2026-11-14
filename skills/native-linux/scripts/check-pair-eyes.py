#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""check-pair-eyes.py SHOT [--json OUT]: read a capture two outputs wide (ScreenShot2, or the scanned-out frame of a side by
side (full) output, PNG or PPM) of glx-back-both-eyes or x11-present-pair: left eye red, right eye blue, a green rectangle in
the middle of both, and for x11-present-pair a white square that must be at the same place in both eyes (the same frame).  A pair: the capture is two outputs wide, the left half holds a red window with the green
rectangle centred, the right half the same window in blue at the same place.  Exit 0 for a pair, 1 otherwise."""
import json, sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); W, H = im.size
out = {'size': [W, H]}
def kind(p):
    r, g, b = p
    if r > 200 and g < 60 and b < 60: return 'red'
    if b > 200 and r < 60 and g < 60: return 'blue'
    if g > 200 and r < 60 and b < 60: return 'green'
    if r > 240 and g > 240 and b > 240: return 'white'
    return None
def eye(x0, x1):
    px = im.load(); n = {'red': 0, 'blue': 0, 'green': 0, 'white': 0}; box = {}
    for y in range(H):
        for x in range(x0, x1):
            k = kind(px[x, y])
            if k:
                n[k] += 1; b = box.setdefault(k, [x - x0, y, x - x0, y])
                b[0] = min(b[0], x - x0); b[1] = min(b[1], y); b[2] = max(b[2], x - x0); b[3] = max(b[3], y)
    return {'count': n, 'box': box}
if W % 2 or W < 2 * H * 0.9:
    out['verdict'] = 'NOT-STEREO-CAPTURE'; out['whole'] = eye(0, W)
else:
    l, r = eye(0, W // 2), eye(W // 2, W); out['left'], out['right'] = l, r
    def centred(e, frame):
        g, f = e['box'].get('green'), e['box'].get(frame)
        if not g or not f: return False
        return abs((g[0] + g[2]) - (f[0] + f[2])) <= 4 and abs((g[1] + g[3]) - (f[1] + f[3])) <= 4
    def mark(e, frame):   # the moving white square, relative to the window: the same frame in both eyes
        f = e['box'].get(frame)
        if not f: return None
        px = im.load(); x0 = (0 if e is l else W // 2) + f[0]; xs = [x for x in range(f[2] - f[0] + 1) if kind(px[x0 + x, f[1] + 40]) == 'white']
        return [min(xs), max(xs)] if xs else None
    out['mark'] = [mark(l, 'red'), mark(r, 'blue')]
    pair = (out['mark'][0] == out['mark'][1] and l['count']['red'] > 1000 and l['count']['blue'] == 0 and r['count']['blue'] > 1000 and r['count']['red'] == 0
            and centred(l, 'red') and centred(r, 'blue') and l['box']['red'] == r['box']['blue'] and l['box']['green'] == r['box']['green'])
    out['verdict'] = 'PAIR' if pair else 'NOT-A-PAIR'
print(json.dumps(out))
if '--json' in sys.argv: open(sys.argv[sys.argv.index('--json') + 1], 'w').write(json.dumps(out, indent=1))
sys.exit(0 if out['verdict'] == 'PAIR' else 1)
