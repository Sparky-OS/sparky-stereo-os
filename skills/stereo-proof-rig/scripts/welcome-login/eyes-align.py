#!/usr/bin/python3
"""eyes-align.py CAPTURE.png REGION [--max-shift N]: is what shows in REGION a pair, or one view in both eyes?

CAPTURE is a capture of a 3D output, both eyes side by side (each half as wide). REGION is x,y,w,h in one eye's
coordinates, or window:CLASS:WINDOWS.json (the frame of the first window of that class in the rig's window log), or
screen (the whole eye). The right eye is moved by every shift from -N to +N pixels (default 24: the desktop's own layers
stand within the person's limits, 10 sunk and 4 popped on a view 1920 wide) and the shift that leaves the fewest
differing pixels (any channel more than 8 apart) is kept: one view drawn at one depth leaves almost none, a pair with
depth of its own cannot be aligned by one shift. Prints JSON: best shift, fraction differing, verdict
("pair" above 2 %, "one view" below 0.2 %, else "unclear"); exits 0 for pair or one view, 2 for unclear.
"""
import json
import os
import sys

import numpy as np
from PIL import Image


def region_of(spec, eye_w, eye_h):
    if spec == 'screen':
        return 0, 0, eye_w, eye_h
    if spec.startswith('window:'):
        _, cls, path = spec.split(':', 2)
        for w in json.load(open(path))['windows']:
            if w['cls'] == cls:
                # KWin's logical frame to this output's device pixels (MEASURE_SCALE, MEASURE_ORIGIN_X and _Y)
                s = float(os.environ.get('MEASURE_SCALE', '1'))
                ox, oy = float(os.environ.get('MEASURE_ORIGIN_X', '0')), float(os.environ.get('MEASURE_ORIGIN_Y', '0'))
                x, y, ww, hh = [int(round(v)) for v in ((w['fg'][0] - ox) * s, (w['fg'][1] - oy) * s, w['fg'][2] * s, w['fg'][3] * s)]
                return max(0, x), max(0, y), min(ww, eye_w - max(0, x)), min(hh, eye_h - max(0, y))
        raise SystemExit('no window of class %s in %s' % (cls, path))
    return tuple(int(v) for v in spec.split(','))


def main():
    args = sys.argv[1:]
    shift_max = 24
    if '--max-shift' in args:
        i = args.index('--max-shift')
        shift_max = int(args[i + 1])
        del args[i:i + 2]
    capture, spec = args
    img = np.asarray(Image.open(capture).convert('RGB')).astype(np.int16)
    eye_w = img.shape[1] // 2
    left, right = img[:, :eye_w], img[:, eye_w:]
    x, y, w, h = region_of(spec, eye_w, img.shape[0])
    # columns that stay inside the eye for every shift
    x0, x1 = max(x, shift_max), min(x + w, eye_w - shift_max)
    if x1 - x0 < 8 or h < 8:
        raise SystemExit('region too small: %r' % ((x, y, w, h),))
    a = left[y:y + h, x0:x1]
    best = None
    for s in range(-shift_max, shift_max + 1):
        b = right[y:y + h, x0 + s:x1 + s]
        differing = int((np.abs(a - b).max(axis=2) > 8).sum())
        if best is None or differing < best[1]:
            best = (s, differing)
    total = a.shape[0] * a.shape[1]
    fraction = best[1] / total
    verdict = 'pair' if fraction > 0.02 else 'one view' if fraction < 0.002 else 'unclear'
    print(json.dumps({'capture': capture, 'region': [x, y, w, h], 'best_shift': best[0], 'differing': best[1],
                      'pixels': total, 'fraction': round(fraction, 5), 'verdict': verdict}))
    return 0 if verdict != 'unclear' else 2


if __name__ == '__main__':
    sys.exit(main())
