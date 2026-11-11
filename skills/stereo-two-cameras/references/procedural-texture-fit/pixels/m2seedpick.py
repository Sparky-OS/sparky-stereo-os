#!/usr/bin/env python3
"""The eye's choice among the seed candidates (milestone 2): the program offers the glyphs that lie closest over the
motif; the person or the model looking at the candidates sheet (m2seedsheet.py) chooses one, as the visual check of
milestone 1c chooses a structure.

m2seedpick.py NAME.seed K OUT.seed "why"
K is the candidate's place on the sheet (0 is the first glyph after the motif). OUT.seed is NAME.seed with the chosen
glyph in place of the program's, and two record lines: the program's choice and the eye's, with the reason."""
import sys

src, k, out, why = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
lines = open(src, encoding='utf-8').read().splitlines()
cands, seen = [], set()
for line in lines:
    if not line.startswith('cand 0 '):
        continue
    head, key, label = line.split('\t')
    p = head.split()
    fam = label.split(' Version')[0].split(' -')[0].rsplit(' ', 1)[0]
    if (p[2], fam) in seen:
        continue
    seen.add((p[2], fam))
    cands.append((p, key, label))
p, key, label = cands[k]
cw, ch, x0, y0, x1, y1 = [int(v) for v in p[17:23]]
block = {l.split(' ', 1)[0]: l for l in lines if not l.startswith(('cand', '#'))}
if block.get('seed') != 'seed 1':
    sys.exit('the seed file holds no seed to replace (the program found none): nothing is chosen behind its back')
prog = '# the program chose %s of %s (%s)' % (block['cp'].split()[1], block['label'][6:], block['like'])
new = ['seed 1', 'label ' + label, 'cp ' + p[2][2:], 'gv ' + ' '.join(p[10:16]),
       'box %.6f %.6f %.6f %.6f' % ((x0 + x1) / 2 / cw, (y0 + y1) / 2 / ch, (x1 - x0) / 2 / cw, (y1 - y0) / 2 / ch),
       block['repeat'], block['colour'], 'like %s %s' % (p[4], block['like'].split()[2]), 'drawing %s bytes %s' % (p[6], p[8]),
       'key ' + key, prog, '# the eye chose U+%s of %s: %s' % (p[2][2:], label, why)]
rec = [l for l in lines if l.startswith(('cand', '#'))]
open(out, 'w', encoding='utf-8').write('\n'.join(rec + new) + '\n')
print('\n'.join(new))
