#!/usr/bin/env python3
"""A look sheet for the lane's eye (milestone 2d): rows of named pictures, whole (reduced) and 1:1 crops.
m2d_look.py OUT.jpg TITLE SIDE CROP "label=path[@x,y]" ...   (CROP 0: whole reduced to SIDE; else a CROP-pixel crop at
x,y, default the centre, shown at SIDE; path@x,y,size crops that item alone). A row break is the word NEXT."""
import sys
from PIL import Image, ImageDraw, ImageFont

out, title, side, crop = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
items = sys.argv[5:]
rows, row = [], []
for it in items:
    if it == 'NEXT':
        rows.append(row); row = []
        continue
    lab, p = it.split('=', 1)
    xy = None
    if '@' in p:
        p, q = p.rsplit('@', 1)
        xy = tuple(int(v) for v in q.split(','))
    row.append((lab, p, xy))
if row:
    rows.append(row)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
except OSError:
    font = ImageFont.load_default()
ncol = max(len(r) for r in rows)
W = 8 + ncol * (side + 8)
H = 30 + len(rows) * (side + 30)
sheet = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(sheet)
d.text((8, 6), title, fill='black', font=font)
for ri, r in enumerate(rows):
    for ci, (lab, p, xy) in enumerate(r):
        im = Image.open(p).convert('RGB')
        cs = xy[2] if xy and len(xy) > 2 else crop
        if cs:
            w, h = im.size
            x, y = xy[:2] if xy else ((w - cs) // 2, (h - cs) // 2)
            im = im.crop((x, y, x + cs, y + cs))
        im = im.resize((side, side), Image.BOX if im.size[0] > side else Image.NEAREST)
        X = 8 + ci * (side + 8)
        Y = 30 + ri * (side + 30)
        sheet.paste(im, (X, Y))
        d.text((X, Y + side + 4), lab, fill='black', font=font)
sheet.save(out, quality=90)
print(out, sheet.size)
