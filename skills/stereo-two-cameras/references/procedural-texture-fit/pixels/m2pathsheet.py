#!/usr/bin/env python3
"""Two paths for the tiles of a photograph, side by side (milestone 2): a procedure found on each tile on its own, and
the whole picture's procedure retuned on each tile's pixels. The first row of tiles of every picture, with hard
borders, so the change from tile to tile is not hidden by the seam band.

m2pathsheet.py SCRATCH OUT.jpg CAPTIONFONT NAME..."""
import os, sys
from PIL import Image, ImageDraw, ImageFont

S, out, capfont = sys.argv[1:4]
f = ImageFont.truetype(capfont, 13)
names = sys.argv[4:]
VARS = os.environ.get('PATH_VARS', 'plain coh3 kc3').split()
H = 180
W = 4 * H
sheet = Image.new('RGB', ((1 + len(VARS)) * (W + 8) + 8, len(names) * (H + 22) + 30), 'white')
d = ImageDraw.Draw(sheet)
LAB = {'plain': 'a procedure found on each tile on its own', 'coh3': 'the whole\'s procedure, every value retuned per tile', 'kc3': 'the whole\'s procedure, its kind kept, retuned per tile'}
d.text((8, 6), 'the first row of four tiles (512 pixels each, shown at %d): the picture | ' % H + ' | '.join(LAB.get(v, v) for v in VARS), fill='black', font=f)
for i, n in enumerate(names):
    y = 30 + i * (H + 22)
    pic = Image.open('%s/m2/tex/%s.png' % (S, n)).convert('RGB').crop((0, 0, 2048, 512)).resize((W, H), Image.LANCZOS)
    strips = [pic]
    for var in VARS:
        st = Image.new('RGB', (2048, 512), (128, 128, 128))
        for c in range(4):
            p = '%s/m2/renders/%s/%s/L2-0-%d.ppm' % (S, n, var, c)
            if os.path.exists(p):
                st.paste(Image.open(p).convert('RGB'), (c * 512, 0))
        strips.append(st.resize((W, H), Image.LANCZOS))
    d.text((8, y), n, fill='black', font=f)
    for k, im in enumerate(strips):
        sheet.paste(im, (8 + k * (W + 8), y + 16))
sheet.save(out, quality=86)
print('sheet', out)
