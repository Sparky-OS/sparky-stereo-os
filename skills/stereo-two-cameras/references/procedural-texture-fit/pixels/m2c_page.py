#!/usr/bin/env python3
"""Put the WebGPU page together (milestone 2c): the page, its scripts, the WGSL twins, the final procedures, the
WebAssembly module and the one font a seed needs, cut to its glyph.

m2c_page.py FITDIR WASM OUTDIR
Writes OUTDIR/index.html, app.js, wasi.js, ops/*.wgsl, data/list.txt, data/NAME.script, data/p2p.wasm,
data/files.txt (the module's in-memory files: path TAB address), data/fonts/candidates.tsv and the cut font."""
import os, shutil, sys
from fontTools import subset
from fontTools.ttLib import TTFont

W = '/K3D/partners/queue/procedures-from-pixels-508'
S = '/var/tmp/procedures-from-pixels-508'
fit, wasm, out = sys.argv[1:4]
os.makedirs(out + '/ops', exist_ok=True)
os.makedirs(out + '/data/fonts', exist_ok=True)
for f in ('index.html', 'app.js', 'wasi.js'):
    shutil.copy(W + '/src/web/' + f, out + '/' + f)
for f in sorted(os.listdir(W + '/src/ops')):
    if f.endswith('.wgsl'):
        shutil.copy(W + '/src/ops/' + f, out + '/ops/' + f)
names = sorted(f[:-13] for f in os.listdir(fit) if f.endswith('.whole.script'))
for n in names:
    shutil.copy('%s/%s.script' % (fit, n), '%s/data/%s.script' % (out, n))
open(out + '/data/list.txt', 'w').write('\n'.join(names) + '\n')
shutil.copy(wasm, out + '/data/p2p.wasm')
# the fonts the procedures' Text operators name, from the font index, each cut to the characters they draw
index = {}
lines = open(S + '/m1e/ix/candidates.tsv', encoding='utf-8').read().split('\n')
for l in lines[1:]:
    c = l.split('\t')
    if len(c) > 2:
        index.setdefault(c[0], l)
need = {}
for n in names:
    for l in open('%s/data/%s.script' % (out, n)):
        t = l.split()
        if len(t) > 2 and t[1] == 'Text':
            s = [bytes.fromhex(x[2:]).decode('utf-8') for x in t[3:] if x.startswith('s=')]
            need.setdefault(s[1], set()).update(s[0])
rows = [lines[0]]
files = []
for key, chars in sorted(need.items()):
    row = index[key].split('\t')
    src = row[1]
    cut = '%s/data/fonts/%s' % (out, key.replace('/', '-') + '.ttf')
    o = subset.Options()
    o.layout_features = ['*']
    f = TTFont(src, fontNumber=int(row[2]))
    sub = subset.Subsetter(o)
    # the space and a to z stay: werkkzeug3's Text works out a font's average character width from their advances
    # (the older weighted rule), and a font cut to one glyph would stretch it otherwise (found on the snowflakes)
    sub.populate(unicodes=sorted(set(ord(c) for c in chars) | set(ord(c) for c in ' abcdefghijklmnopqrstuvwxyz')))
    sub.subset(f)
    f.save(cut)
    row[1] = '/data/fonts/' + os.path.basename(cut)
    row[2] = '0'
    rows.append('\t'.join(row))
    files.append((row[1], 'data/fonts/' + os.path.basename(cut)))
    print('font %s cut to %d character(s) and a to z: %d bytes' % (key, len(chars), os.path.getsize(cut)))
open(out + '/data/fonts/candidates.tsv', 'w', encoding='utf-8').write('\n'.join(rows) + '\n')
files.append(('/data/fonts/candidates.tsv', 'data/fonts/candidates.tsv'))
open(out + '/data/files.txt', 'w').write('\n'.join('%s\t%s' % f for f in files) + '\n')
print('%d procedures, page in %s' % (len(names), out))
