#!/usr/bin/env python3
"""What seeds made possible: the same tile with and without them (milestone 2).

m2seedcompare.py SCRATCH OUT.jpg CAPTIONFONT NAME:WITHOUT:WITH:TILE[:NOTE] ...
For every texture: the picture's tile, the tile's procedure without a seed (WITHOUT: the variant the fitter builds
without one, "shape" or "plain"), and with the seed, each whole and close up at 1:1, with the bytes of each procedure
and the seed it calls (the glyph, its font, what the font weighs whole and cut to the one glyph)."""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont

S, out, capfont = sys.argv[1:4]
f = ImageFont.truetype(capfont, 13)
fb = ImageFont.truetype(capfont, 15)
P, C = 300, 150
rows = []
for spec in sys.argv[4:]:
    parts = spec.split(':')
    name, without, withv, tile = parts[0], parts[1], parts[2], parts[3]
    note = parts[4] if len(parts) > 4 else ''
    pic = Image.open('%s/m2/tiles/%s/%s.ppm' % (S, name, tile)).convert('RGB')

    def get(var):
        p = '%s/m2/renders/%s/%s/%s.ppm' % (S, name, var, tile)
        im = Image.open(p).convert('RGB') if os.path.exists(p) else Image.new('RGB', pic.size, (128, 128, 128))
        lg = '%s/m2/fits/%s/%s/%s.log' % (S, name, var, tile)
        b = [l.split() for l in open(lg) if l[0].isdigit()][-1][2] if os.path.exists(lg) else '?'
        return im, b
    a_im, a_b = get(without)
    s_im, s_b = get(withv)
    seedf = '%s/m2/seeds/%s.chosen' % (S, name)
    if not os.path.exists(seedf):
        seedf = '%s/m2/seeds/%s.seed' % (S, name)
    sd = {}
    if os.path.exists(seedf):
        for l in open(seedf, encoding='utf-8'):
            k, _, v = l.rstrip('\n').partition(' ')
            if k in ('label', 'cp', 'like', 'key') and not l.startswith('#'):
                sd.setdefault(k, v)
            if k == 'drawing':
                sd.setdefault('bytes', v.split()[-1])
            if l.startswith('# weight '):
                sd['weight'] = l[9:].strip()
            if l.startswith('# the eye chose'):
                sd['eye'] = l[2:].strip()
    # the close-up: where the tile changes most
    g = pic.convert('L').resize((pic.width // 16, pic.height // 16), Image.BOX)
    px = g.load()
    best, cx, cy = -1, 0, 0
    k = C // 16
    for y in range(0, g.height - k + 1):
        for x in range(0, g.width - k + 1):
            vals = [px[x + i, y + j] for i in range(k) for j in range(k)]
            v = max(vals) - min(vals)
            if v > best:
                best, cx, cy = v, x * 16, y * 16
    box = (cx, cy, cx + C, cy + C)
    rows.append((name, tile, note, [('the picture, %s' % tile, pic), ('without a seed (%s), %s B' % (without, a_b), a_im),
                                    ('with the seed, %s B' % s_b, s_im)], box, sd))
W = 3 * (P + C + 14) + 8
H = sum(P + 112 for _ in rows) + 30
sheet = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(sheet)
d.text((8, 6), 'What seeds made possible: the same tile, its procedure without a seed and with one (whole, and 1:1 where the tile changes most)', fill='black', font=fb)
y = 30
for name, tile, note, cols, box, sd in rows:
    d.text((8, y), name + (': ' + note if note else ''), fill='black', font=fb)
    for i, (lab, im) in enumerate(cols):
        x = 8 + i * (P + C + 14)
        d.text((x, y + 20), lab, fill='black', font=f)
        sheet.paste(im.resize((P, P), Image.LANCZOS), (x, y + 38))
        sheet.paste(im.crop(box), (x + P + 6, y + 38))
    cp = sd.get('cp', '')
    if cp == '0':
        line = 'the seed: the box GlowRect draws (it lies over the motif by %s; every glyph that does as well costs more bytes): %s B, no font' % (
            sd.get('like', '?').split()[0] if sd.get('like') else '?', sd.get('bytes', '?'))
    else:
        line = 'the seed: U+%s of %s, lying over the motif by %s; in the procedure it costs its key: %s B with its Text operator' % (
            cp, sd.get('label', '?'), sd.get('like', '?').split()[0] if sd.get('like') else '?', sd.get('bytes', '?'))
    d.text((8, y + P + 42), line[:200], fill='black', font=f)
    if sd.get('weight'):
        d.text((8, y + P + 58), 'if the font had to travel: ' + sd['weight'].split(': ', 1)[-1][:180], fill='black', font=f)
    if sd.get('eye'):
        d.text((8, y + P + 74), sd['eye'][:200], fill='black', font=f)
    y += P + 112
sheet.save(out, quality=88)
print('sheet', out)
