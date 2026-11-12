#!/usr/bin/env python3
"""Fetch the font files of github.com/google/fonts (ofl, apache, ufl) at one commit, file by file, and
check each against the git blob hash the repository's own tree states: fetch_gf.py TREE.json COMMIT OUTDIR.
Also fetches each family folder's METADATA.pb and licence file (the source's own record of designer and licence)."""
import hashlib, json, os, sys, urllib.request, concurrent.futures as cf

tree_json, commit, out = sys.argv[1], sys.argv[2], sys.argv[3]
tree = json.load(open(tree_json))
assert not tree.get('truncated')
want = []
for e in tree['tree']:
    if e['type'] != 'blob':
        continue
    p = e['path']
    top = p.split('/')[0]
    if top not in ('ofl', 'apache', 'ufl'):
        continue
    base = p.rsplit('/', 1)[-1]
    ext = base.rsplit('.', 1)[-1].lower()
    if ext in ('ttf', 'otf', 'ttc', 'otc', 'woff', 'woff2') or base in ('METADATA.pb', 'OFL.txt', 'LICENSE.txt', 'UFL.txt', 'LICENCE.txt'):
        want.append(e)

def blob_sha(data):
    h = hashlib.sha1(b'blob %d\0' % len(data))
    h.update(data)
    return h.hexdigest()

def one(e):
    dst = os.path.join(out, e['path'])
    if os.path.exists(dst):
        with open(dst, 'rb') as f:
            if blob_sha(f.read()) == e['sha']:
                return 'have'
    url = 'https://raw.githubusercontent.com/google/fonts/%s/%s' % (commit, urllib.request.quote(e['path']))
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                data = r.read()
            break
        except Exception as ex:
            err = ex
    else:
        return 'FAIL %s %s' % (e['path'], err)
    if blob_sha(data) != e['sha'] or len(data) != e['size']:
        return 'MISMATCH %s' % e['path']
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + '.part'
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, dst)
    return 'ok'

total = sum(e['size'] for e in want)
print('files %d, %.2f GB' % (len(want), total / 1e9), flush=True)
counts = {}
with cf.ThreadPoolExecutor(8) as ex:
    for i, r in enumerate(ex.map(one, want)):
        k = r.split(' ')[0]
        counts[k] = counts.get(k, 0) + 1
        if k not in ('ok', 'have'):
            print(r, flush=True)
        if i % 500 == 0:
            print(i, counts, flush=True)
print('done', counts, flush=True)
sys.exit(0 if set(counts) <= {'ok', 'have'} else 1)
