#!/usr/bin/env python3
"""The eye's choice among the seed reading's candidates where the reading found none above its threshold (milestone
2d; Daniel on the poinsettias: "so far nothing came out - come on, there must be a font that has this type of
drawing"). m2d_seedbelow.py NAME.seed K PICTURE.ppm OUT.chosen "why"
K counts the candidates of the whole motif (the `cand 0` lines), each character once. The block the fitter reads
(seed, label, cp, gv, box, repeat, colour, like, drawing, key) is written from that candidate's line, the reading's
repeat line, and the picture's two shades (Otsu's threshold, the mean colour of each side); the record says that the
reading found none above its threshold and that the eye chose this one, with the reason."""
import re, sys
import numpy as np
from PIL import Image

src, k, pic, out, why = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
lines = open(src, encoding='utf-8').read().splitlines()
m = re.search(r'repeats (\d+) by (\d+)', lines[0])
if not m:
    sys.exit('the seed file has no repeat reading on its first line')
nx, ny = int(m.group(1)), int(m.group(2))
cands, seen = [], set()
for line in lines:
    if not line.startswith('cand 0 '):
        continue
    head, key, label = line.split('\t')
    p = head.split()
    if p[2] in seen:
        continue
    seen.add(p[2])
    cands.append((p, key, label))
p, key, label = cands[k]
cw, ch, x0, y0, x1, y1 = [int(v) for v in p[17:23]]
im = np.asarray(Image.open(pic).convert('RGB')).astype(np.float64)
g = im.mean(2)
hist = np.bincount(g.astype(np.uint8).ravel(), minlength=256) / g.size
w0 = np.cumsum(hist)
mu = np.cumsum(hist * np.arange(256))
thr = int(np.argmax((mu[-1] * w0 - mu) ** 2 / np.maximum(w0 * (1 - w0), 1e-12)))
light, dark = im[g > thr].mean(0), im[g <= thr].mean(0)
ink, ground = (light, dark) if (g > thr).mean() < 0.5 else (dark, light)
word = lambda c: 'ff%02x%02x%02x' % tuple(int(round(v)) for v in c)
new = ['seed 1', 'label ' + label, 'cp ' + p[2][2:], 'gv ' + ' '.join(p[10:16]),
       'box %.6f %.6f %.6f %.6f' % ((x0 + x1) / 2 / cw, (y0 + y1) / 2 / ch, (x1 - x0) / 2 / cw, (y1 - y0) / 2 / ch),
       'repeat %d %d 0.000000 0.000000 0 0.000000' % (nx, ny), 'colour %s %s' % (word(ink), word(ground)),
       'like %s 0' % p[4], 'drawing %s bytes %s' % (p[6], p[8]), 'key ' + key,
       '# the reading found no glyph above its threshold (%s)' % next((l[4:] for l in lines if l.startswith('why ')), '?'),
       '# the eye chose U+%s of %s (like %s): %s' % (p[2][2:], label, p[4], why)]
rec = [l for l in lines if l.startswith(('cand', '#'))]
open(out, 'w', encoding='utf-8').write('\n'.join(rec + new) + '\n')
print('\n'.join(new))
