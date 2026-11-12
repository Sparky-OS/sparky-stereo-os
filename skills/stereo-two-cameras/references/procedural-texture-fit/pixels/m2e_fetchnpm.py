#!/usr/bin/env python3
"""Fetch icon and symbol fonts published on the npm registry (milestone 2e: Daniel, "find christmass themed fonts and
download them if needed - same for the snowflake"), over HTTPS, each package into its own new folder:
m2e_fetchnpm.py OUTDIR NAME...
For each package: the registry's latest record, the tarball, its sha512 checked against the record's integrity, the
SHA-256 written down; from the tarball only the font files (ttf, otf, woff, woff2) and the licence and readme files are
taken out (tarfile's data filter: no links, no paths outside the folder). The files are data: nothing in them is run.
Writes OUTDIR/fetched.tsv (package, version, licence field, tarball, sha256, files kept)."""
import base64, hashlib, io, json, os, sys, tarfile, urllib.request

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
rows = []
KEEP = ('.ttf', '.otf', '.woff', '.woff2')
for name in sys.argv[2:]:
    rec = json.load(urllib.request.urlopen('https://registry.npmjs.org/%s/latest' % name, timeout=60))
    url = rec['dist']['tarball']
    if not url.startswith('https://'):
        sys.exit('%s: the tarball is not on https: %s' % (name, url))
    data = urllib.request.urlopen(url, timeout=300).read()
    algo, want = rec['dist']['integrity'].split('-', 1)
    if algo != 'sha512' or base64.b64encode(hashlib.sha512(data).digest()).decode() != want:
        sys.exit('%s: the tarball does not match the registry integrity' % name)
    sha = hashlib.sha256(data).hexdigest()
    d = os.path.join(out, name.replace('@', '').replace('/', '_'))
    if os.path.exists(d):
        sys.exit('%s exists: give an empty folder' % d)
    os.makedirs(d)
    tf = tarfile.open(fileobj=io.BytesIO(data), mode='r:gz')
    kept = []
    for m in tf.getmembers():
        if not m.isfile():
            continue
        low = m.name.lower()
        base = os.path.basename(low)
        if low.endswith(KEEP) or base.startswith(('license', 'licence', 'copying', 'readme', 'ofl')):
            tf.extract(m, d, filter='data')
            kept.append(m.name)
    rows.append((rec['name'], rec['version'], str(rec.get('license')), url, sha, str(len(kept))))
    print('%s %s %s: %d files kept, sha256 %s' % (rec['name'], rec['version'], rec.get('license'), len(kept), sha[:16]), flush=True)
with open(os.path.join(out, 'fetched.tsv'), 'a') as f:
    for r in rows:
        f.write('\t'.join(r) + '\n')
