#!/usr/bin/env python3
"""Narrow a glyph search's results by the glyph's own name in its font (milestone 2e): icon and dingbat fonts name
their pictures (snowflake, flower, holly) where Unicode gives a private-use character no name. The ranking stays the
pixels': the rows keep the search's order and scores. m2e_glyphnames.py RESULT.tsv REGEX OUT.tsv [TOP]
The fonts are data, read with fontTools (WOFF2 through brotli); nothing in them is run."""
import re, sys
from fontTools.ttLib import TTFont

src, rx, out = sys.argv[1], re.compile(sys.argv[2], re.I), sys.argv[3]
top = int(sys.argv[4]) if len(sys.argv) > 4 else 40
cache = {}


def name_of(path, face, cp):
    key = (path, face)
    if key not in cache:
        try:
            f = TTFont(path, fontNumber=face, lazy=True)
            cache[key] = f.getBestCmap() or {}
        except Exception as e:
            cache[key] = {}
    return cache[key].get(cp, '')


kept = []
head = []
for line in open(src, encoding='utf-8'):
    if line.startswith('#') or line.startswith('score'):
        head.append(line)
        continue
    p = line.rstrip('\n').split('\t')
    cp = int(p[1][2:], 16)
    nm = name_of(p[3], int(p[4]), cp)
    if nm and rx.search(nm):
        kept.append(line.rstrip('\n') + '\t' + nm + '\n')
        if len(kept) >= top:
            break
with open(out, 'w', encoding='utf-8') as fo:
    fo.writelines(head)
    fo.writelines(kept)
print('%d rows whose glyph name matches %s' % (len(kept), sys.argv[2]))
for l in kept[:15]:
    print(l.rstrip()[:160])
