#!/usr/bin/env python3
"""Bytes of one procedure and of four procedures per picture against the fair baseline (milestone 2d).

m2d_table.py S EVIDENCE_2C_TABLE > table.md
The bytes of a script are counted as p2p's Graph.bytes counts them (werkkzeug3's storage: one class byte and four bytes
per word of every operator, a Text's strings as a length word and the bytes to whole words). The picture's JPEG and its
lower-resolution copies are milestone 2c's columns (the same pictures, chain_sizes.py of skill stereo-two-cameras)."""
import os, re, sys

S, t2c = sys.argv[1], sys.argv[2]


def script_bytes(path):
    b, n = 0, 0
    for line in open(path):
        t = line.split()
        if not t or t[0] == 'out':
            continue
        words = [w for w in t[3:] if not w.startswith('s=')]
        strs = [w[2:] for w in t[3:] if w.startswith('s=')]
        b += 1 + 4 * len(words)
        for sx in strs:
            ln = len(bytes.fromhex(sx))
            b += 4 + 4 * ((ln + 1 + 3) // 4)
        n += 1
    return n, b


base = {}
for line in open(t2c):
    c = [x.strip() for x in line.split('|')]
    if len(c) > 8 and c[1] and not c[1].startswith(('texture', '---')):
        pic = int(c[6].replace(',', '').split()[0])
        cop = int(c[7].replace(',', '').split()[0])
        base[c[1]] = (pic, cop)
print('# Bytes: one procedure, four procedures per picture, against the fair baseline (milestone 2d)')
print()
print('The fair baseline is the picture as JPEG quality 90 with its lower-resolution copies to 1 pixel (milestone 2c\'s columns, the same pictures). Bytes are p2p\'s count (one class byte and four bytes per word of every operator, a Text\'s strings to whole words). "Four" is a Quad of the four quarters\' procedures (simple: each quarter\'s whole-picture procedure without its close-up layers; close: with them), seam smooth, band 0.03.')
print()
print('| texture | one procedure (2d) | four, simple | four, close-up layers | the picture as JPEG q90 | its copies | one + picture against picture + copies | four simple + picture against picture + copies |')
print('|---|---|---|---|---|---|---|---|')
for nm in sorted(base):
    one = os.path.join(S, 'm2d/fitF/%s.whole.script' % nm)
    if not os.path.exists(one):
        continue
    n1, b1 = script_bytes(one)
    q = os.path.join(S, 'm2d/quadF/%s-simple.script' % nm)
    qc = os.path.join(S, 'm2d/quadF/%s-close.script' % nm)
    g = os.path.join(S, 'm2d/fitG/%s.whole.script' % nm)
    four = '%d operators, %d B' % script_bytes(q) if os.path.exists(q) else 'not drawn (a motif repeating three times across: a quarter holds one and a half)'
    fourc = '%d operators, %d B' % script_bytes(qc) if os.path.exists(qc) else ''
    pic, cop = base[nm]
    g1 = 100.0 * ((b1 + pic) / (pic + cop) - 1)
    g4 = '%+.1f %%' % (100.0 * ((script_bytes(q)[1] + pic) / (pic + cop) - 1)) if os.path.exists(q) else ''
    extra = ''
    if os.path.exists(g):
        extra = '; with the glyph the eye picked: %d operators, %d B' % script_bytes(g)
    print('| %s | %d operators, %d B%s | %s | %s | %s B | %s B | %+.1f %% | %s |' % (nm, n1, b1, extra, four, fourc, format(pic, ','), format(cop, ','), g1, g4))
