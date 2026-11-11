#!/usr/bin/env python3
"""Search the glyph index for a motif and for parts of it (milestone 2d; Daniel on the poinsettias: "come on, there
must be a font that has this type of drawing"; on the snowflakes: "the more operations are missing the final tip
pattern, the inner losangles are nice, the lines crossing not nice").

m2d_glyphsearch.py PICTURE.ppm INDEXDIR OUT.tsv [rotations=N] [part=whole|ring|centre] [inner=R] [top=K] [drawings=1] [tolerant=1]

The motif: the picture's ink (the lighter of the two shades, Otsu's threshold) split into pieces along the rows and
columns that hold no ink; the first piece is the motif. Its ink is cut to its box and laid on 16 by 16 cells by
majority, as the index lays every glyph (wzfontindex.c: the outline's ink at 64 by 64 stretched to its box, then 16
by 16 by majority), with its width over its height. part=ring compares only the cells outside a disc of radius
inner (in parts of the box's half side) around the box's centre (a motif's tips), part=centre only the cells inside
it (its middle). The score is the cells both hold over the cells either holds, among the compared cells, less a
tenth of how far the widths over heights differ (in doublings); tolerant=1 counts as held a cell within one cell of
held ink on the other side too (thin lines drawn a cell apart still meet), averaged with the strict score;
drawings=1 keeps only characters that are drawings (Unicode's So and Sm, and private use, where icon fonts put their
pictures: Daniel, "when fonts are pure drawing, it's even better"); rotations=N also turns the motif N times around its
centre (a flower's leaves stand at any angle) and keeps each glyph's best turn. Every glyph of the index is read
(17,166,578 entries of 48 bytes: font, character, width over height, form, pieces, 32 bytes of cells).
The index is data: nothing in it is run."""
import os, sys, unicodedata
import numpy as np
from PIL import Image

pic_path, ixdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
opts = dict(a.split('=', 1) for a in sys.argv[4:])
rot_n = int(opts.get('rotations', '1'))
part = opts.get('part', 'whole')
inner = float(opts.get('inner', '0.45'))
top = int(opts.get('top', '40'))
drawings = opts.get('drawings', '0') == '1'
tolerant = opts.get('tolerant', '0') == '1'
ROWM_L = np.uint64(0xFFFEFFFEFFFEFFFE)  # a cell moved one to the right stays in its row (bit x of a row is column x)
ROWM_R = np.uint64(0x7FFF7FFF7FFF7FFF)


def dilate(b):
    """b: (N, 4) words of 4 rows each (16 bits a row); the cells within one cell of a held cell"""
    h = b | ((b << np.uint64(1)) & ROWM_L) | ((b >> np.uint64(1)) & ROWM_R)
    up = h >> np.uint64(16)
    up[:, :3] |= h[:, 1:] << np.uint64(48)
    dn = h << np.uint64(16)
    dn[:, 1:] |= h[:, :3] >> np.uint64(48)
    return h | up | dn

im = np.asarray(Image.open(pic_path).convert('L')).astype(np.float64)
# Otsu's threshold on the grey
hist = np.bincount(im.astype(np.uint8).ravel(), minlength=256).astype(np.float64)
p = hist / hist.sum()
w0 = np.cumsum(p)
mu = np.cumsum(p * np.arange(256))
var = (mu[-1] * w0 - mu) ** 2 / np.maximum(w0 * (1 - w0), 1e-12)
thr = int(np.argmax(var))
ink = im > thr if (im > thr).mean() < 0.5 else im <= thr


def runs(v):
    r, s = [], None
    for i, x in enumerate(v):
        if x and s is None:
            s = i
        if not x and s is not None:
            r.append((s, i))
            s = None
    if s is not None:
        r.append((s, len(v)))
    return r


cols = runs(ink.any(0))
x0, x1 = max(cols, key=lambda r: r[1] - r[0])
rows = runs(ink[:, x0:x1].any(1))
y0, y1 = max(rows, key=lambda r: r[1] - r[0])
motif = ink[y0:y1, x0:x1].astype(np.float64)
aspect = (x1 - x0) / (y1 - y0)
print('motif: %d by %d pixels at %d,%d (width over height %.3f), threshold %d' % (x1 - x0, y1 - y0, x0, y0, aspect, thr))


def cells16(m):
    a = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((64, 64), Image.BOX)).astype(np.float64) / 255
    return a.reshape(16, 4, 16, 4).mean(axis=(1, 3)) > 0.5


def pack(b):
    by = np.packbits(b.astype(np.uint8).ravel(), bitorder='little')  # cell (y, x): byte (16y + x) // 8, bit x % 8 (wzfontindex.c)
    return by.view('<u8')


yy, xx = np.mgrid[0:16, 0:16]
rr = np.hypot((xx + 0.5) / 8 - 1, (yy + 0.5) / 8 - 1)
if part == 'ring':
    sel = rr > inner
elif part == 'centre':
    sel = rr <= inner
else:
    sel = np.ones((16, 16), bool)
selw = pack(sel)

queries = []
for k in range(rot_n):
    ang = 360.0 * k / rot_n
    m = motif
    if ang:
        side = int(np.ceil(np.hypot(*m.shape))) + 2
        big = np.zeros((side, side))
        oy, ox = (side - m.shape[0]) // 2, (side - m.shape[1]) // 2
        big[oy:oy + m.shape[0], ox:ox + m.shape[1]] = m
        r = np.asarray(Image.fromarray((big * 255).astype(np.uint8)).rotate(ang, resample=Image.BILINEAR)).astype(np.float64) / 255 > 0.5
        ys, xs = np.nonzero(r)
        m = r[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float64)
    b = cells16(m)
    qw = pack(b & sel)
    queries.append((ang, qw, m.shape[1] / m.shape[0], b, dilate(qw.reshape(1, 4))[0] & selw))

dt = np.dtype([('font', '<u4'), ('cp', '<u4'), ('aspect', '<f4'), ('form', 'u1'), ('parts', 'u1'), ('pad', 'u1', 2), ('bits', 'u1', 32)])
ix = np.memmap(os.path.join(ixdir, 'glyphs.bin'), dtype=dt, mode='r')
fonts = [l.rstrip('\n').split('\t') for l in open(os.path.join(ixdir, 'candidates.tsv'), encoding='utf-8')]
head, fonts = fonts[0], fonts[1:]
print('index: %d glyphs, %d fonts' % (len(ix), len(fonts)))
best = np.full(len(ix), -9.0, np.float32)
bang = np.zeros(len(ix), np.float32)
CH = 2_000_000
for s in range(0, len(ix), CH):
    blk = ix[s:s + CH]
    bits = np.ascontiguousarray(blk['bits']).view('<u8').reshape(-1, 4) & selw
    la = np.log2(np.maximum(blk['aspect'], 1e-3))
    keep = None
    if drawings:
        cps = blk['cp']
        keep = np.array([(0xE000 <= c <= 0xF8FF) or c >= 0xF0000 or unicodedata.category(chr(c)) in ('So', 'Sm') for c in cps.tolist()])
    if tolerant:
        dbits = dilate(bits) & selw
    for ang, q, qa, _, qd in queries:
        inter = np.bitwise_count(bits & q).sum(1)
        uni = np.bitwise_count(bits | q).sum(1)
        sc = inter / np.maximum(uni, 1)
        if tolerant:
            na = np.bitwise_count(bits).sum(1)
            nq = int(np.bitwise_count(q).sum())
            met = (np.bitwise_count(bits & qd).sum(1) + np.bitwise_count(dbits & q).sum(1)) / np.maximum(na + nq, 1)
            sc = 0.5 * (sc + met)
        sc = sc - 0.1 * np.abs(la - np.log2(qa))
        if keep is not None:
            sc = np.where(keep, sc, -9.0)
        upd = sc > best[s:s + CH]
        best[s:s + CH][upd] = sc[upd]
        bang[s:s + CH][upd] = ang
order = np.argsort(-best)
seen = set()
rows = []
for i in order:
    e = ix[i]
    f = fonts[e['font']]
    fam = f[head.index('family')]
    key = (int(e['cp']), fam)
    if key in seen:
        continue
    seen.add(key)
    rows.append((float(best[i]), int(e['cp']), f[0], f[1], int(f[2]) if f[2].isdigit() else 0, float(bang[i]), int(e['form']), f[head.index('licence')] if 'licence' in head else ''))
    if len(rows) >= top:
        break
with open(out, 'w', encoding='utf-8') as fo:
    fo.write('# motif %d by %d at %d,%d of %s; part %s (inner %.2f); %d turns\n' % (x1 - x0, y1 - y0, x0, y0, os.path.basename(pic_path), part, inner, rot_n))
    fo.write('score\tcp\tfont key\tfile\tface\tturn\tform\tlicence\n')
    for r in rows:
        fo.write('%.4f\tU+%04X\t%s\t%s\t%d\t%.1f\t%d\t%s\n' % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
np.save(out + '.query.npy', queries[0][3])
print('wrote', out, 'best', rows[0][:3])
