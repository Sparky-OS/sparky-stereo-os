#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""The geometry of vk-x11-covered's pair (TOPLEVEL=1 UNCOVERED=1) in ScreenShot2 captures, against a prediction.
The client draws an 800x600 window: left view red, right view blue, a 400x300 green rectangle in the middle of both,
a 40x40 white square 20 px below the top that moves 16 px a frame, the same place in both views.
Prediction for a pair shown by Stereo KWin (each eye one half of the capture):
  - left eye: a red box of W x H (one view, not two and not half), right eye: a blue box of W x H at the same place;
    no blue in the left eye, no red in the right eye;
  - green: W/2 x H/2, centred in the box, the same place in both eyes;
  - white: 40 x 40, 20 px below the box's top, the same place in both eyes (disparity 0, vertical 0);
  - over several captures the white square moves (the right eye is not a frame behind).
usage: pair_geometry.py [--size WxH] SHOT.png [SHOT.png ...]   exit 0 when every capture matches"""
import json
import sys
import numpy as np
from PIL import Image

args = sys.argv[1:]
W, H = 800, 600
if args[:1] == ['--size']:
    W, H = map(int, args[1].split('x'))
    args = args[2:]


def box(mask):
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def eye(a):
    r, g, b = (a[..., i].astype(int) for i in range(3))
    red = (r > 200) & (g < 60) & (b < 60)
    blue = (b > 200) & (r < 60) & (g < 60)
    green = (g > 200) & (r < 60) & (b < 60)
    white = (r > 240) & (g > 240) & (b > 240)
    return {'red': box(red), 'blue': box(blue), 'green': box(green), 'white': box(white),
            'n': {'red': int(red.sum()), 'blue': int(blue.sum()), 'green': int(green.sum()), 'white': int(white.sum())}}


ok_all = True
marks = []
for path in args:
    a = np.asarray(Image.open(path).convert('RGB'))
    half = a.shape[1] // 2
    left, right = eye(a[:, :half]), eye(a[:, half:])
    why = []
    fl, fr = left['red'], right['blue']
    if not fl or not fr:
        why.append('no red window in the left eye or no blue window in the right eye')
    else:
        for name, f in (('left', fl), ('right', fr)):
            if (f[2] - f[0], f[3] - f[1]) != (W, H):
                why.append(f'{name} window {f[2]-f[0]}x{f[3]-f[1]}, predicted {W}x{H}')
        if fl != fr:
            why.append(f'windows at different places {fl} {fr}')
        if left['n']['blue'] or right['n']['red']:
            why.append(f"the other view's colour in an eye: blue {left['n']['blue']} left, red {right['n']['red']} right")
        want_green = [fl[0] + W // 4, fl[1] + H // 4, fl[0] + 3 * W // 4, fl[1] + 3 * H // 4]
        for name, e in (('left', left), ('right', right)):
            if e['green'] != want_green:
                why.append(f"{name} green {e['green']}, predicted {want_green}")
        wl, wr = left['white'], right['white']
        if not wl or not wr or (wl[2] - wl[0], wl[3] - wl[1]) != (40, 40) or wl[1] != fl[1] + 20:
            why.append(f'white square {wl} {wr}, predicted 40x40 at y {fl[1] + 20}')
        elif wl != wr:
            why.append(f'white square at different places: {wl} {wr} (disparity {wl[0]-wr[0]}, vertical {wl[1]-wr[1]})')
        else:
            marks.append(wl[0] - fl[0])
    ok = not why
    ok_all &= ok
    print(json.dumps({'shot': path, 'verdict': 'PAIR' if ok else 'WRONG', 'why': why,
                      'left': {k: left[k] for k in ('red', 'green', 'white')},
                      'right': {k: right[k] for k in ('blue', 'green', 'white')}}))
if len(args) > 1:
    moved = len(set(marks)) == len(marks) == len(args)
    print(json.dumps({'white_x_per_capture': marks, 'moves': moved}))
    ok_all &= moved
sys.exit(0 if ok_all else 1)
