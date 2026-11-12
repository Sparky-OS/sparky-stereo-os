#!/usr/bin/env python3
"""Fetch npm packages for the scene checks (the Khronos glTF-Validator; three.js as a viewer that ignores the
extension), over HTTPS, each into its own new folder: fetchnpm.py OUTDIR NAME@VERSION...   (lane 508's script)
The registry's record for that version, the tarball checked against the record's sha512 integrity, its SHA-256
written down, every regular file extracted with tarfile's data filter (no links, nothing outside the folder).
The files are data here: nothing is run on this machine; they are mounted read-only into the containers.
Writes OUTDIR/fetched.tsv (package, version, licence field, tarball, sha256)."""
import base64, hashlib, io, json, os, sys, tarfile, urllib.request

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for spec in sys.argv[2:]:
    name, ver = spec.rsplit('@', 1)
    rec = json.load(urllib.request.urlopen('https://registry.npmjs.org/%s/%s' % (name, ver), timeout=60))
    url = rec['dist']['tarball']
    if not url.startswith('https://'):
        sys.exit('%s: the tarball is not on https' % spec)
    data = urllib.request.urlopen(url, timeout=300).read()
    algo, want = rec['dist']['integrity'].split('-', 1)
    if algo != 'sha512' or base64.b64encode(hashlib.sha512(data).digest()).decode() != want:
        sys.exit('%s: the tarball does not match the registry integrity' % spec)
    sha = hashlib.sha256(data).hexdigest()
    d = os.path.join(out, name.replace('@', '').replace('/', '_'))
    if os.path.exists(d):
        sys.exit('%s exists: give an empty folder' % d)
    os.makedirs(d)
    tf = tarfile.open(fileobj=io.BytesIO(data), mode='r:gz')
    n = 0
    for m in tf.getmembers():
        if m.isfile():
            tf.extract(m, d, filter='data')
            n += 1
    with open(os.path.join(out, 'fetched.tsv'), 'a') as f:
        f.write('\t'.join([rec['name'], rec['version'], str(rec.get('license')), url, sha]) + '\n')
    print('%s %s %s: %d files, sha256 %s' % (rec['name'], rec['version'], rec.get('license'), n, sha[:16]))
