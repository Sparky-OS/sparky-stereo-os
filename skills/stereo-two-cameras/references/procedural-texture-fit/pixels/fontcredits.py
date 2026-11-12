#!/usr/bin/env python3
"""The credit of every font an evidence sheet draws with, read from the font's own name table (as the font index holds
it): fontcredits.py INDEX-CLASSIFIED.tsv SCRIPT... > fonts-credits.md

A script's Text operators of version 2 name their font by the index key; werkkzeug3's own names (an empty name, "times
new roman", "verdana") are the machine's Arial, Times New Roman and Verdana, read in place and never copied."""
import sys
index = sys.argv[1]
rows = [l.rstrip('\n').split('\t') for l in open(index, encoding='utf-8')]
col = {n: i for i, n in enumerate(rows[0])}
by_key = {r[0]: r for r in rows[1:]}
by_family = {}
for r in rows[1:]:
    if r[col['source']] == 'machine' and r[col['style']] == 'Regular':
        by_family.setdefault(r[col['family']].lower(), r)
used = {}
for path in sys.argv[2:]:
    for line in open(path, encoding='utf-8', errors='replace'):
        p = line.split()
        if len(p) < 3 or p[1] != 'Text':
            continue
        strs = [bytes.fromhex(x[2:]) for x in p[3:] if x.startswith('s=')]
        words = [int(x, 16) for x in p[3:] if not x.startswith('s=')]
        if len(strs) < 2:
            continue
        if len(words) >= 10 and words[9] == 2:
            key = strs[1].decode('utf-8')
            r = by_key.get(key)
        else:
            name = strs[1].decode('latin-1') or 'arial'
            r = by_family.get(name)
            key = r[0] if r else name
        used.setdefault(key, (r, set()))[1].add(path.rsplit('/', 1)[-1])
print('| font | version | source | designer (name ID 9) | copyright (name ID 0) | licence class | drawn in |')
print('|---|---|---|---|---|---|---|')
for key in sorted(used):
    r, where = used[key]
    if r is None:
        print('| %s | - | not in the index | - | - | - | %s |' % (key, ', '.join(sorted(where))))
        continue
    lic = r[col['class']] if 'class' in col else '-'
    print('| %s %s | %s | %s | %s | %s | %s | %s |' % (r[col['family']], r[col['style']], r[col['version']].split(';')[0], r[col['source']],
          r[col['designer']], r[col['copyright']].replace('|', '/')[:160], lic, ', '.join(sorted(where))[:120]))
