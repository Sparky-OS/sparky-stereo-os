#!/usr/bin/env python3
"""A quick sheet to look at (milestone 2c, while tuning): per texture, the picture, milestone 2b and the new fit, each
whole (reduced) and at 1:1 around the corner of four tiles. Writes the render jobs, runs them, composes.

m2c_look.py FITDIR OUT.jpg [NAME ...]"""
import os, subprocess, sys
from PIL import Image, ImageDraw
S = '/var/tmp/procedures-from-pixels-508'
W = '/K3D/partners/queue/procedures-from-pixels-508'
fit, out = sys.argv[1], sys.argv[2]
names = sys.argv[3:] or sorted(f[:-7] for f in os.listdir(fit) if f.endswith('.script') and '.r' not in f[-11:] and not f.endswith('.whole.script'))
look = os.path.join(os.path.dirname(os.path.abspath(out)), 'look-' + os.path.basename(os.path.abspath(fit)))
fit = os.path.abspath(fit)
os.makedirs(look, exist_ok=True)
jobs = []
for n in names:
    for tag, sc in (('2b', '%s/m2b/fit5/%s.script' % (S, n)), ('2c', '%s/%s.script' % (fit, n))):
        for kind, args in (('w', ['9']), ('c', ['9', 'window=0.375,0.375,0.25'])):
            o = '%s/%s-%s-%s.ppm' % (look, n, tag, kind)
            if tag == '2c' and os.path.exists(o):
                os.remove(o)
            jobs.append(' '.join([o, 'render', sc, o] + args))
jf = look + '/jobs.txt'
open(jf, 'w').write('\n'.join(jobs) + '\n')
binary = os.environ.get('P2P', S + '/build-2c/p2p')
subprocess.run(['python3', W + '/scripts/m2c_run.py', binary, jf, '7'], check=True, stdout=subprocess.DEVNULL)
T = 360
sheet = Image.new('RGB', (6 * T + 70, len(names) * (T + 22) + 10), 'white')
d = ImageDraw.Draw(sheet)
for r, n in enumerate(names):
    full = Image.open('%s/m2b/full/%s.ppm' % (S, n))
    y = 5 + r * (T + 22)
    d.text((5, y), n + ': picture | 2b | 2c (whole) | picture | 2b | 2c (1:1 at the corner of four tiles)', fill='black')
    ims = [full.resize((T, T), Image.LANCZOS)]
    for tag in ('2b', '2c'):
        ims.append(Image.open('%s/%s-%s-w.ppm' % (look, n, tag)).resize((T, T), Image.LANCZOS))
    ims.append(full.crop((768, 768, 1280, 1280)).resize((T, T), Image.LANCZOS))
    for tag in ('2b', '2c'):
        ims.append(Image.open('%s/%s-%s-c.ppm' % (look, n, tag)).resize((T, T), Image.LANCZOS))
    for k, im in enumerate(ims):
        sheet.paste(im, (5 + k * (T + 10) + (20 if k >= 3 else 0), y + 16))
sheet.save(out, quality=88)
print(out)
