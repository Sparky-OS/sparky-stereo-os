#!/usr/bin/env python3
"""Overview of milestone 2: per texture the picture, one procedure for the whole picture and the tiled procedures,
three textures to a row, with the bytes.

m2overview.py SCRATCH EVDIR OUT.jpg CAPTIONFONT NAME[:VARIANTLABEL] ...   (EVDIR/NAME-tiled.jpg and NAME.json from m2compose)"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

S, ev, out, capfont = sys.argv[1:5]
f = ImageFont.truetype(capfont, 12)
P = 200
items = sys.argv[5:]
per = 3
cw = 3 * (P + 4) + 14
rows = (len(items) + per - 1) // per
sheet = Image.new('RGB', (per * cw + 6, rows * (P + 52) + 6), 'white')
d = ImageDraw.Draw(sheet)
for i, it in enumerate(items):
    name, _, lab = it.partition(':')
    rec = json.load(open(os.path.join(ev, name + '.json')))
    x0 = 6 + (i % per) * cw
    y0 = 6 + (i // per) * (P + 52)
    pic = Image.open('%s/m2/tex/%s.png' % (S, name)).convert('RGB')
    pic = pic.crop((0, 0, pic.width, pic.width)).resize((P, P), Image.LANCZOS)
    l0p = '%s/m2/renders/%s/%s/L0-0-0.ppm' % (S, name, rec.get('l0_variant', 'plain'))
    l0 = Image.open(l0p).convert('RGB').resize((P, P), Image.LANCZOS) if os.path.exists(l0p) else Image.new('RGB', (P, P), 'grey')
    tl = Image.open(os.path.join(ev, name + '-tiled.jpg')).convert('RGB').resize((P, P), Image.LANCZOS)
    for k, im in enumerate((pic, l0, tl)):
        sheet.paste(im, (x0 + k * (P + 4), y0 + 16))
    d.text((x0, y0), '%s%s' % (name, (' (' + lab + ')') if lab else ''), fill='black', font=f)
    b = rec['baseline']
    d.text((x0, y0 + P + 20), 'picture | one procedure %s B | %d tiles %s B' % (format(rec['l0_bytes'], ','), len(rec['took']), format(rec['rung_bytes'][-1], ',')), fill='black', font=f)
    d.text((x0, y0 + P + 34), 'JPEG %s B, its copies %s B' % (format(b.get('jpeg', 0), ','), format(b.get('chain', 0), ',')), fill='black', font=f)
sheet.save(out, quality=88)
print('overview', out)
