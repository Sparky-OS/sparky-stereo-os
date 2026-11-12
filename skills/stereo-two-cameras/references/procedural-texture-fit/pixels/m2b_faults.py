#!/usr/bin/env python3
"""Milestone 2b, the three faults of milestone 2's tiles, before and after (one sheet).

m2b_faults.py SCRATCH OUT.jpg CAPTIONFONT NAME...
Per picture, three columns at a glance (the 16 tiles of 512 put side by side, hard borders, reduced to 512): the
picture, milestone 2's tiles (the whole picture's procedure retuned per tile, its kind kept), the same with the three
faults fixed (a tile's noise at the picture's frequencies, the light at the picture's place, colours retuned by
brightness and saturation only); then the corner where four tiles meet at 1:1 (256 pixels around it) for the three."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

S, out, capfont = sys.argv[1:4]
names = sys.argv[4:]
f = ImageFont.truetype(capfont, 14)


def ppm(p):
    return np.asarray(Image.open(p).convert('RGB'))


def stitch(folder):
    rows = []
    for r in range(4):
        rows.append(np.concatenate([ppm('%s/L2-%d-%d.ppm' % (folder, r, c)) for c in range(4)], axis=1))
    return np.concatenate(rows, axis=0)


G = 300
C = 256
W = 3 * (G + 6) + 3 * (C + 6) + 20
H = len(names) * (max(G, C) + 30) + 10
sheet = Image.new('RGB', (W, H), (255, 255, 255))
d = ImageDraw.Draw(sheet)
for k, n in enumerate(names):
    pic = np.asarray(Image.open('%s/m2/tex/%s.png' % (S, n)).convert('RGB'))[:2048, :2048]
    a = stitch('%s/m2/fits/%s/kc3' % (S, n))
    b = stitch('%s/m2b/fits/%s/kc3fix' % (S, n))
    y = 10 + k * (max(G, C) + 30)
    d.text((10, y), '%s: picture | milestone 2 tiles | faults fixed   (whole, 16 tiles of 512)   ...   the corner of four tiles at 1:1' % n, fill=(0, 0, 0), font=f)
    y += 20
    x = 10
    for im in (pic, a, b):
        sheet.paste(Image.fromarray(im).resize((G, G), Image.LANCZOS), (x, y))
        x += G + 6
    x += 8
    for im in (pic, a, b):
        sheet.paste(Image.fromarray(im[1024 - C // 2:1024 + C // 2, 1024 - C // 2:1024 + C // 2]), (x, y))
        x += C + 6
sheet.save(out, quality=88)
print(out, sheet.size)
