#!/usr/bin/env python3
"""What a seed's font weighs if it had to travel with the procedure (milestone 2).

m2fontweight.py CANDIDATES.tsv KEY CODEPOINT-HEX
Prints the font file's size, and the size of the font cut down to the one glyph the seed calls (fontTools' subsetter:
the glyph, its cmap entry and the tables a renderer needs; no hinting, no layout tables, no names but the required),
as a plain OpenType file and as WOFF2 when the Brotli module is present. The font file is only read."""
import io, os, sys
from fontTools import subset
from fontTools.ttLib import TTFont

ix, key, cp = sys.argv[1], sys.argv[2], int(sys.argv[3], 16)
path = face = None
for line in open(ix, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if p[0] == key:
        path, face = p[1], int(p[2])
        break
if path is None:
    sys.exit('no font with the key %r in the index' % key)
size = os.path.getsize(path)
opts = subset.Options()
opts.layout_features = []
opts.hinting = False
opts.name_IDs = []
opts.notdef_outline = False
opts.drop_tables += ['DSIG', 'GSUB', 'GPOS', 'GDEF', 'kern', 'COLR', 'CPAL', 'SVG ', 'CBDT', 'CBLC', 'sbix', 'EBDT', 'EBLC', 'vhea', 'vmtx']
font = TTFont(path, fontNumber=face, lazy=False)
sub = subset.Subsetter(opts)
sub.populate(unicodes=[cp])
sub.subset(font)
b = io.BytesIO()
font.save(b)
one = b.tell()
w2 = None
try:
    import brotli  # noqa: F401
    font.flavor = 'woff2'
    b2 = io.BytesIO()
    font.save(b2)
    w2 = b2.tell()
except ImportError:
    pass
print('%s U+%04X: font file %d bytes (%s); cut to the one glyph %d bytes%s' % (key, cp, size, os.path.basename(path), one,
      ', as WOFF2 %d bytes' % w2 if w2 else ' (no Brotli module here for WOFF2)'))
