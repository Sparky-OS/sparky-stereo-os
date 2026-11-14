#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""check-pair-flat-split.py SHOT.png [--child grey|yellow|none] [--json OUT]: what a ScreenShot2 capture of glx-covered or x11-present-pair shows.
The window: left eye red, right eye blue, a green rectangle in the middle of both, a white square in the row 40 below the
window's top, and (with a cover) a 60x60 child 30 from the left, half way down.
  PAIR   the capture is two outputs wide; left half a whole red window, right half the same window blue at the same place,
         green centred in both, the white square at the same place in both; with --child, the child is where it belongs in
         BOTH eyes
  FLAT   one correct flat picture: the left view (red, green centred) whole, in a capture one output wide, or identical in
         both halves of a capture two outputs wide; with --child, the child where it belongs
  SPLIT  anything else that shows the window: the person sees a wrong picture
  NONE   no window found
Exit 0 for PAIR, 3 for FLAT, 1 for SPLIT, 2 for NONE."""
import json, sys
from PIL import Image, ImageChops
im = Image.open(sys.argv[1]).convert('RGB'); W, H = im.size
child = sys.argv[sys.argv.index('--child') + 1] if '--child' in sys.argv else None
out = {'size': [W, H]}
def kind(p):
    r, g, b = p
    if r > 200 and g < 60 and b < 60: return 'red'
    if b > 200 and r < 60 and g < 60: return 'blue'
    if g > 200 and r < 60 and b < 60: return 'green'
    if r > 240 and g > 240 and b > 240: return 'white'
    if abs(r - 128) < 12 and abs(g - 128) < 12 and abs(b - 128) < 12: return 'grey'
    if abs(r - 192) < 12 and abs(g - 192) < 12 and b < 30: return 'yellow'
    return None
def eye(x0, x1):
    px = im.load(); n = dict.fromkeys(('red', 'blue', 'green', 'white', 'grey', 'yellow'), 0); box = {}
    for y in range(H):
        for x in range(x0, x1):
            k = kind(px[x, y])
            if k:
                n[k] += 1; b = box.setdefault(k, [x - x0, y, x - x0, y])
                b[0] = min(b[0], x - x0); b[1] = min(b[1], y); b[2] = max(b[2], x - x0); b[3] = max(b[3], y)
    return {'count': n, 'box': box}
def whole(e, frame):
    """the window in this eye: the frame colour's box with the green rectangle centred in it and the child where it belongs"""
    f, g = e['box'].get(frame), e['box'].get('green')
    if not f or not g or e['count'][frame] < 1000: return 'no ' + frame
    if '--loose' not in sys.argv:   # --loose: an offset or another size moves the picture in the window, in both eyes alike
        if abs((g[0] + g[2]) - (f[0] + f[2])) > 4 or abs((g[1] + g[3]) - (f[1] + f[3])) > 4: return 'green not centred'
        if abs((g[2] - g[0]) * 2 - (f[2] - f[0])) > 6: return 'green not half the window'
    if child and child != 'none':
        c = e['box'].get(child)
        if not c or e['count'][child] != 3600: return 'child %s: %s pixels' % (child, e['count'][child])
        if c[0] - f[0] != 30 or c[2] - c[0] != 59 or c[3] - c[1] != 59: return 'child out of place %s' % c
    if child == 'none' and (e['count']['grey'] or e['count']['yellow']): return 'a child shows'
    return None
def mark(e, frame):
    f = e['box'].get(frame)
    if not f: return None
    px = im.load(); x0 = e['x0'] + f[0]; xs = [x for x in range(f[2] - f[0] + 1) if kind(px[x0 + x, f[1] + 40]) == 'white']
    return [min(xs), max(xs)] if xs else None
stereo = W % 2 == 0 and W >= 2 * H * 0.9
out['stereo_capture'] = stereo
if not stereo:
    e = eye(0, W); e['x0'] = 0; out['whole'] = e
    why = whole(e, 'red')
    out['verdict'] = 'NONE' if not e['count']['red'] and not e['count']['blue'] else 'FLAT' if why is None and not e['count']['blue'] else 'SPLIT'
    out['why'] = why or ('blue shows' if e['count']['blue'] else None)
else:
    l, r = eye(0, W // 2), eye(W // 2, W); l['x0'], r['x0'] = 0, W // 2
    out['left'], out['right'] = l, r
    same = ImageChops.difference(im.crop((0, 0, W // 2, H)), im.crop((W // 2, 0, W, H))).getbbox() is None
    out['halves_equal'] = same
    wl, wr = whole(l, 'red'), whole(r, 'blue')
    out['mark'] = [mark(l, 'red'), mark(r, 'blue')]
    if not any(e['count'][k] for e in (l, r) for k in ('red', 'blue')):
        out['verdict'] = 'NONE'
    elif (wl is None and wr is None and l['count']['blue'] == 0 and r['count']['red'] == 0 and l['box']['red'] == r['box']['blue']
          and l['box']['green'] == r['box']['green'] and out['mark'][0] == out['mark'][1]
          and (not child or child == 'none' or l['box'][child] == r['box'][child])):
        out['verdict'] = 'PAIR'
    elif same and wl is None and l['count']['blue'] == 0:
        out['verdict'] = 'FLAT'
    else:
        out['verdict'] = 'SPLIT'; out['why'] = [wl, wr, 'marks %s' % out['mark']]
for e in (out.get('left'), out.get('right'), out.get('whole')):
    if e: e.pop('x0', None)
print(json.dumps(out))
if '--json' in sys.argv: open(sys.argv[sys.argv.index('--json') + 1], 'w').write(json.dumps(out, indent=1))
sys.exit({'PAIR': 0, 'FLAT': 3, 'SPLIT': 1, 'NONE': 2}[out['verdict']])
