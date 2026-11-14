#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""Measure a stereo capture of a window of coloured discs on neutral grey (qdiscs, or any window drawn that way).
usage: disc-parallax.py CAPTURE.png [--compare OTHER.png] [--predict P1,P2,...] [--json OUT]
The capture holds both eyes side by side, the left eye first. For each coloured disc the coverage-weighted
centroid is taken in each eye; the parallax is the left centroid minus the right one, in device pixels,
positive when nearer. --compare counts the pixels that differ from another capture."""
import json, sys
import numpy as np
from PIL import Image

DISCS = [('red', (255, 0, 0)), ('green', (0, 255, 0)), ('blue', (0, 0, 255)),
         ('yellow', (255, 255, 0)), ('cyan', (0, 255, 255)), ('magenta', (255, 0, 255))]
GREY = np.array([128, 128, 128], float)

def centroid(eye, colour):
    c = np.array(colour, float)
    d = c - GREY
    cov = ((eye.astype(float) - GREY) @ d) / (d @ d)          # 0 on the grey, 1 on the disc
    near = np.abs(eye.astype(float) - (GREY + np.clip(cov, 0, 1)[..., None] * d)).sum(axis=2) < 12
    cov = np.where(near, np.clip(cov, 0, 1), 0)
    solid = cov > 0.99
    if solid.sum() < 500:
        return None
    ys, xs = np.nonzero(solid)
    y0, y1, x0, x1 = ys.min() - 6, ys.max() + 7, xs.min() - 6, xs.max() + 7
    box = cov[y0:y1, x0:x1]
    w = box.sum()
    gx = (box.sum(axis=0) * np.arange(x0, x1)).sum() / w
    gy = (box.sum(axis=1) * np.arange(y0, y1)).sum() / w
    return gx, gy, w

def main():
    args = sys.argv[1:]
    img = np.asarray(Image.open(args[0]).convert('RGB'))
    h, w2, _ = img.shape
    w = w2 // 2
    left, right = img[:, :w], img[:, w:]
    predict = None
    if '--predict' in args:
        predict = [float(x) for x in args[args.index('--predict') + 1].split(',')]
    res = {'capture': args[0], 'eye_size': [w, h], 'eyes_differ_pixels': int((left != right).any(axis=2).sum()), 'discs': []}
    for i, (name, colour) in enumerate(DISCS):
        l, r = centroid(left, colour), centroid(right, colour)
        if not l or not r:
            res['discs'].append({'disc': name, 'found': False}); continue
        d = {'disc': name, 'left_x': round(l[0], 3), 'right_x': round(r[0], 3), 'disparity': round(l[0] - r[0], 3),
             'vertical': round(l[1] - r[1], 3), 'area_left': round(l[2], 1), 'area_right': round(r[2], 1)}
        if predict and i < len(predict):
            d['predicted'] = predict[i]; d['error'] = round(d['disparity'] - predict[i], 3)
        res['discs'].append(d)
    if '--compare' in args:
        other = np.asarray(Image.open(args[args.index('--compare') + 1]).convert('RGB'))
        if other.shape != img.shape:
            res['compare'] = {'other': args[args.index('--compare') + 1], 'same_size': False}
        else:
            diff = np.abs(img.astype(int) - other.astype(int)).max(axis=2)
            res['compare'] = {'other': args[args.index('--compare') + 1], 'same_size': True,
                              'differing_pixels': int((diff > 0).sum()), 'differing_over_8': int((diff > 8).sum()),
                              'max_difference': int(diff.max()), 'pixels': int(diff.size)}
            if (diff > 0).any():
                ys, xs = np.nonzero(diff > 0)
                res['compare']['bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    if '--json' in args:
        json.dump(res, open(args[args.index('--json') + 1], 'w'), indent=1)
    print(json.dumps(res, indent=1))

main()
