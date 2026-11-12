#!/usr/bin/env python3
"""The seed reading's candidates beside the motif they were laid over (milestone 2).

m2seedsheet.py prep SEEDDIR NAME...   writes SEEDDIR/cands/NAME-k.txt (typed graphs: a glyph drawn by werkkzeug's Text,
                                      version 2, stretched to the motif's box) and SEEDDIR/cands/render.sh
m2seedsheet.py sheet SEEDDIR OUT.jpg CAPTIONFONT NAME...   the motif's ink (from the cell) and the candidates, drawn
                                      by the engine, with the font, the character and how well each lies over the motif
Candidates are the `cand` lines of NAME.seed, the same character of several faces of one family shown once."""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

mode, sd = sys.argv[1], sys.argv[2]
cd = os.path.join(sd, 'cands')
SIDE = 256


def cands(name):
    out, seen = [], set()
    for line in open(os.path.join(sd, name + '.seed'), encoding='utf-8'):
        if not line.startswith('cand '):
            continue
        head, key, label = line.rstrip('\n').split('\t')
        p = head.split()
        rec = dict(sil=int(p[1]), cp=int(p[2][2:], 16), like=float(p[4]), drawing=p[6] == '1', bytes=int(p[8]),
                   gv=[float(x) for x in p[10:16]], box=[int(x) for x in p[17:23]], key=key, label=label)
        fam = label.split(' Version')[0].split(' -')[0].rsplit(' ', 1)[0]
        if (rec['cp'], fam) in seen:
            continue
        seen.add((rec['cp'], fam))
        out.append(rec)
    return out


if mode == 'prep':
    os.makedirs(cd, exist_ok=True)
    sh = ['#!/bin/sh', 'B=$1']
    for name in sys.argv[3:]:
        for k, c in enumerate(cands(name)[:8]):
            cw, ch, x0, y0, x1, y1 = c['box']
            asp = (x1 - x0) / max(1, y1 - y0)
            bh = 200.0 if asp <= 1 else 200.0 / asp
            bw = bh * asp
            bx0, by0 = (SIDE - bw) / 2, (SIDE - bh) / 2
            a, inkh, top, adv, lsb, avg = c['gv']
            em = bh / inkh
            sx = (bw / bh) / a
            if abs(sx - 1) < 0.01:
                sx = 1.0
            pen0 = bx0 - lsb * em * sx
            tp = by0 - top * em
            wide = 0.0 if sx == 1.0 else sx * avg * em / SIDE
            g = ('v0 Flat - 8 8 #ff000000\nv1 Text v0 %.9g %.9g %.9g %.9g #ffffffff 0 0 0 1 2 0 1 %s %s ""\n'
                 % ((pen0 - 2) / SIDE, (tp - 2) / SIDE, em / SIDE, wide, json.dumps(chr(c['cp']), ensure_ascii=False), json.dumps(c['key'], ensure_ascii=False)))
            base = os.path.join(cd, '%s-%d' % (name, k))
            open(base + '.txt', 'w', encoding='utf-8').write(g)
            # the typed graph made into a script here (the container has no Python), drawn there
            with open(base + '.script', 'w') as so:
                subprocess.run([sys.executable, '-I', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'text2script.py')],
                               input=g, text=True, stdout=so, check=True)
            sh.append('"$B" render "%s.script" "%s.ppm" 8 > "%s.out" 2>&1 || echo "failed %s"' % (base, base, base, base))
            json.dump(c, open(base + '.json', 'w'))
    open(os.path.join(cd, 'render.sh'), 'w').write('\n'.join(sh) + '\n')
    print('prepared')
else:
    out, capfont = sys.argv[3], sys.argv[4]
    f = ImageFont.truetype(capfont, 12)
    rows = []
    for name in sys.argv[5:]:
        ink = Image.open(os.path.join(sd, name + '.seed.ink.pgm')).convert('L')
        cl = cands(name)[:8]
        if not cl:
            continue
        cw, ch, x0, y0, x1, y1 = cl[0]['box']
        mot = ink.crop((x0, y0, x1, y1))
        asp = (x1 - x0) / max(1, y1 - y0)
        bh = 200 if asp <= 1 else int(200 / asp)
        mot = mot.resize((max(1, int(bh * asp)), bh), Image.NEAREST)
        tiles = [('the motif (mean cell)', mot)]
        for k, c in enumerate(cl):
            p = os.path.join(cd, '%s-%d.ppm' % (name, k))
            im = Image.open(p).convert('L') if os.path.exists(p) else Image.new('L', (SIDE, SIDE), 60)
            fam = c['label'].split(' Version')[0]
            tiles.append(('U+%04X %s %.2f%s' % (c['cp'], fam[:22], c['like'], ' D' if c['drawing'] else ''), im))
        rows.append((name, tiles))
    W = 9 * (SIDE + 6) + 6
    sheet = Image.new('RGB', (W, len(rows) * (SIDE + 40) + 10), 'white')
    d = ImageDraw.Draw(sheet)
    for r, (name, tiles) in enumerate(rows):
        y = 6 + r * (SIDE + 40)
        d.text((6, y), name + ': the motif read from the mean cell, and the glyphs that lie closest over it (likeness; D: a drawing)', fill='black', font=f)
        for i, (lab, im) in enumerate(tiles):
            x = 6 + i * (SIDE + 6)
            box = Image.new('L', (SIDE, SIDE), 0)
            box.paste(im, ((SIDE - im.width) // 2, (SIDE - im.height) // 2))
            sheet.paste(box.convert('RGB'), (x, y + 30))
            d.text((x, y + 16), lab, fill='black', font=f)
    sheet.save(out, quality=88)
    print('sheet', out)
