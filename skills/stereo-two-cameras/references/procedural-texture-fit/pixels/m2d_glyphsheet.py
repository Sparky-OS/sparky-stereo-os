#!/usr/bin/env python3
"""The glyph search's nearest candidates beside the motif, drawn by the engine (milestone 2d).

m2d_glyphsheet.py prep RESULT.tsv OUTDIR N JOBS.txt BINARY   typed graphs (Flat and Text version 2: the candidate's
                                                    character of its font, large on a 512 canvas), made into scripts
                                                    here (the container has no Python), and render jobs for m2d_run.py
m2d_glyphsheet.py sheet OUT.jpg TITLE CAPFONT PICTURE.ppm RESULT.tsv:OUTDIR:N ...   one row per search: the motif (its
                                                    ink box from the result's first line), then each candidate's ink
                                                    cut to its box and turned by the turn the search found, with the
                                                    character, the font and the score
Candidates repeat one character in several faces of one family: each character is shown once, in its best font."""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))


def rows(tsv, n):
    out, seen = [], set()
    for line in open(tsv, encoding='utf-8'):
        if line.startswith('#') or line.startswith('score'):
            continue
        sc, cp, key, f, face, turn, form, lic = line.rstrip('\n').split('\t')
        if cp in seen:
            continue
        seen.add(cp)
        out.append(dict(score=float(sc), cp=int(cp[2:], 16), key=key, file=f, turn=float(turn), licence=lic))
        if len(out) >= n:
            break
    return out


mode = sys.argv[1]
if mode == 'prep':
    tsv, od, n, jobs, binary = sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6]
    os.makedirs(od, exist_ok=True)
    with open(jobs, 'a') as jf:
        for k, r in enumerate(rows(tsv, n)):
            g = ('v0 Flat - 9 9 #ff000000\nv1 Text v0 0.2 0.12 0.6 0 #ffffffff 0 0 0 1 2 0 1 %s %s ""\n'
                 % (json.dumps(chr(r['cp']), ensure_ascii=False), json.dumps(r['key'], ensure_ascii=False)))
            base = os.path.join(od, 'c%02d' % k)
            open(base + '.txt', 'w', encoding='utf-8').write(g)
            with open(base + '.script', 'w') as so:
                subprocess.run([sys.executable, '-I', os.path.join(HERE, 'text2script.py')], input=g, text=True, stdout=so, check=True)
            json.dump(r, open(base + '.json', 'w'))
            jf.write('%s.ppm render %s.script %s.ppm\n' % (base, base, base))
    sys.exit(0)

out, title, capfont, picture = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
specs = sys.argv[6:]
C = 200
f = ImageFont.truetype(capfont, 12)
pic = Image.open(picture).convert('RGB')
lines = []
for sp in specs:
    tsv, od, n = sp.split(':')
    first = open(tsv, encoding='utf-8').readline().split()
    w, h = [int(v) for v in first[2:5:2]]
    x0, y0 = [int(v) for v in first[6].split(',')]
    lines.append((tsv, od, int(n), (x0, y0, x0 + w, y0 + h), ' '.join(first[9:])))
ncol = 1 + max(l[2] for l in lines)
sheet = Image.new('RGB', (8 + ncol * (C + 8), 30 + len(lines) * (C + 50)), 'white')
d = ImageDraw.Draw(sheet)
d.text((8, 6), title, fill='black', font=f)
for ri, (tsv, od, n, box, what) in enumerate(lines):
    Y = 30 + ri * (C + 50)
    m = pic.crop(box)
    m.thumbnail((C, C))
    sheet.paste(m, (8 + (C - m.width) // 2, Y + (C - m.height) // 2))
    d.text((8, Y + C + 4), 'the motif; search: ' + what[:28], fill='black', font=f)
    for k in range(n):
        base = os.path.join(od, 'c%02d' % k)
        if not os.path.exists(base + '.ppm'):
            continue
        r = json.load(open(base + '.json'))
        g = Image.open(base + '.ppm').convert('L')
        bb = g.point(lambda v: 255 if v > 128 else 0).getbbox()
        if not bb:
            continue
        g = g.crop(bb)
        if r['turn']:
            g = g.rotate(-r['turn'], expand=True, resample=Image.BILINEAR)
        g.thumbnail((C, C))
        X = 8 + (k + 1) * (C + 8)
        tile = Image.new('RGB', (C, C), (60, 60, 60))
        tile.paste(Image.new('RGB', g.size, 'white'), ((C - g.width) // 2, (C - g.height) // 2), g)
        sheet.paste(tile, (X, Y))
        d.text((X, Y + C + 4), 'U+%04X %.3f%s' % (r['cp'], r['score'], ' turned %.0f' % r['turn'] if r['turn'] else ''), fill='black', font=f)
        d.text((X, Y + C + 20), r['key'][:30], fill='black', font=f)
sheet.save(out, quality=90)
print(out, sheet.size)
