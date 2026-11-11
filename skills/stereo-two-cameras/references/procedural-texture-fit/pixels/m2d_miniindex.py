#!/usr/bin/env python3
"""A small glyph index of the characters the eye picked from the search's sheet (milestone 2d), so the seed reading
(p2p seed) lays them over the motif and writes their drawing's words: m2d_miniindex.py INDEXDIR OUTDIR "KEY|U+XXXX" ...
Writes OUTDIR/glyphs.bin (the picked entries, their font renumbered) and OUTDIR/candidates.tsv (the header and their
fonts' rows, in the same order). Every key must be in the index: a key or a character not found stops with a sentence."""
import os, sys
import numpy as np

ixdir, out = sys.argv[1], sys.argv[2]
picks = []
for a in sys.argv[3:]:
    key, cp = a.rsplit('|', 1)
    picks.append((key, int(cp[2:], 16)))
rows = open(os.path.join(ixdir, 'candidates.tsv'), encoding='utf-8').read().rstrip('\n').split('\n')
head, rows = rows[0], rows[1:]
keys = [r.split('\t', 1)[0] for r in rows]
dt = np.dtype([('font', '<u4'), ('cp', '<u4'), ('aspect', '<f4'), ('form', 'u1'), ('parts', 'u1'), ('pad', 'u1', 2), ('bits', 'u1', 32)])
ix = np.memmap(os.path.join(ixdir, 'glyphs.bin'), dtype=dt, mode='r')
os.makedirs(out, exist_ok=True)
sel, frows = [], []
for key, cp in picks:
    if key not in keys:
        sys.exit('font %s is not in the index' % key)
    fi = keys.index(key)
    hit = np.nonzero((ix['font'] == fi) & (ix['cp'] == cp))[0]
    if len(hit) == 0:
        sys.exit('U+%04X of %s is not in the index' % (cp, key))
    e = np.zeros(1, dtype=dt)[0]
    for f in dt.names:
        e[f] = ix[hit[0]][f]
    if rows[fi] not in frows:
        frows.append(rows[fi])
    e['font'] = frows.index(rows[fi])
    sel.append(e.copy())
np.array(sel, dtype=dt).tofile(os.path.join(out, 'glyphs.bin'))
open(os.path.join(out, 'candidates.tsv'), 'w', encoding='utf-8').write(head + '\n' + '\n'.join(frows) + '\n')
print('%d glyphs of %d fonts' % (len(sel), len(frows)))
