#!/usr/bin/env python3
"""The blend strips (ORDER 508, milestone 3): read the frames strip.js posted (TAG-VIEW-MODE-KK.png, KK = blend time
in tenths), measure each frame and lay out the sheet.
m3_strip.py DIR TAG LABEL OUT.jpg OUT.md
Measures (luminance, 0 to 255): detail contrast = the standard deviation of the frame minus its 9 by 9 box mean (how
much fine structure is visible); coarse error = the mean absolute difference of 32 by 32 block means against the last
frame (the picture): how far the large patches are from the picture's; step = the mean absolute change from the frame
before (a pop is one large step); and how much of the frame's detail is the procedure's and how much the picture's
(least squares of the frame's detail on the two endpoints' details)."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

d, tag, label, out_jpg, out_md = sys.argv[1:6]


def load(view, mode, k):
    return np.asarray(Image.open('%s/%s-%s-%s-%02d.png' % (d, tag, view, mode, k)).convert('RGB'), dtype=np.float64)


def lum(a):
    return a @ np.array([0.2126, 0.7152, 0.0722])


def box(a, r=4):
    k = 2 * r + 1
    p = np.pad(a, r, mode='edge')
    c = p.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def blocks(a, b=32):
    h, w = a.shape
    return a[:h - h % b, :w - w % b].reshape(h // b, b, w // b, b).mean(axis=(1, 3))


rows = []
md = ['# Blend strips: %s' % label, '', 'Each row: blend time 0 (the procedure) to 1 (the picture), the tester\'s own shader read back. Measures in luminance levels of 255.', '']
for view in ('crop', 'whole'):
    md += ['## %s' % ('1:1, the centre 512 pixels' if view == 'crop' else 'the whole texture at 512 pixels'), '',
           '| blend | t | detail contrast | coarse error | step | detail from procedure | detail from picture |', '|---|---|---|---|---|---|---|']
    P, I = lum(load(view, 'cross', 0)), lum(load(view, 'cross', 10))
    dP, dI = P - box(P), I - box(I)
    for mode in ('cross', 'coarse'):
        prev = None
        frames = []
        for k in range(11):
            a = load(view, mode, k)
            frames.append(a)
            L = lum(a)
            det = L - box(L)
            A = np.stack([dP.ravel(), dI.ravel()], 1)
            cf = np.linalg.lstsq(A, det.ravel(), rcond=None)[0]
            ce = np.abs(blocks(L) - blocks(I)).mean()
            st = np.abs(L - prev).mean() if prev is not None else 0.0
            prev = L
            md.append('| %s | %.1f | %.2f | %.2f | %.2f | %.2f | %.2f |' % (mode, k / 10, det.std(), ce, st, cf[0], cf[1]))
        rows.append((view, mode, frames))
    md.append('')
# the sheet: four rows (crop cross, crop coarse, whole cross, whole coarse), seven times each
ks = [0, 2, 4, 5, 6, 8, 10]
cell, pad, top, left = 256, 6, 40, 150
W = left + len(ks) * (cell + pad)
H = top + len(rows) * (cell + pad) + 10
sheet = Image.new('RGB', (W, H), (24, 24, 28))
dr = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
except OSError:
    font = ImageFont.load_default()
dr.text((10, 8), label + ': procedure (t 0) to picture (t 1); 1:1 rows show the centre at full size', fill=(230, 230, 230), font=font)
for j, k in enumerate(ks):
    dr.text((left + j * (cell + pad) + 100, top - 18), 't %.1f' % (k / 10), fill=(200, 200, 200), font=font)
for i, (view, mode, frames) in enumerate(rows):
    y = top + i * (cell + pad)
    dr.text((8, y + 110), ('1:1 ' if view == 'crop' else 'whole ') + ('cross-fade' if mode == 'cross' else 'coarse first'), fill=(230, 230, 230), font=font)
    for j, k in enumerate(ks):
        a = frames[k].astype(np.uint8)
        im = Image.fromarray(a[128:384, 128:384]) if view == 'crop' else Image.fromarray(a).resize((cell, cell), Image.LANCZOS)
        sheet.paste(im, (left + j * (cell + pad), y))
sheet.save(out_jpg, quality=90)
open(out_md, 'w').write('\n'.join(md) + '\n')
print('\n'.join(md))
