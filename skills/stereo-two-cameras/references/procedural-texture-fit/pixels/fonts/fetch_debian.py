#!/usr/bin/env python3
"""Inside a Debian forky container with network (apt checks every package against the signed index):
fetch Debian's font packages one at a time, keep their font files whose licence is on the brief's list and that the
collection does not already hold (same SHA-256), and the package's copyright file; record every file either way.

fetch_debian.py PACKAGES.txt SEEN.sha256 OUTDIR TMPDIR
PACKAGES.txt: one package name per line. SEEN.sha256: sha256 hashes already in the collection, one per line.
OUTDIR/records.tsv: package, version, path in the package, sha256, bytes, licence class, how the class was found, kept or why not.
"""
import fnmatch, hashlib, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import licence

FONT_EXT = ('.ttf', '.otf', '.ttc', '.otc', '.otb', '.pfb', '.pfa', '.t1', '.pcf', '.pcf.gz', '.bdf', '.bdf.gz', '.woff', '.woff2', '.pfr', '.fon', '.fnt', '.dfont', '.t42')
pk_file, seen_file, out, tmp = sys.argv[1:5]
pkgs = [l.strip() for l in open(pk_file) if l.strip() and not l.startswith('#')]
seen = set(l.split()[0] for l in open(seen_file) if l.strip())
os.makedirs(out, exist_ok=True)
rec = open(os.path.join(out, 'records.tsv'), 'a')
done = set()
if os.path.exists(os.path.join(out, 'done.txt')):
    done = set(l.strip() for l in open(os.path.join(out, 'done.txt')))
donef = open(os.path.join(out, 'done.txt'), 'a')


def dep5(text):
    """the Files paragraphs of a machine-readable copyright file: [(patterns, short name)] and the standalone licences"""
    if not re.search(r'^Format:\s*\S*copyright-format', text, re.M):
        return None
    paras, cur, key = [], {}, None
    for line in text.splitlines():
        if not line.strip():
            if cur:
                paras.append(cur)
            cur, key = {}, None
            continue
        if line[0] in ' \t' and key:
            cur[key] += '\n' + line.strip()
            continue
        m = re.match(r'^([A-Za-z-]+):\s*(.*)$', line)
        if m:
            key = m.group(1).lower()
            cur[key] = m.group(2)
    if cur:
        paras.append(cur)
    files = []
    for p in paras:
        if 'files' in p and 'license' in p:
            files.append((p['files'].split(), p['license'].split('\n')[0].strip()))
    return files


def classify(path, cp_text, files):
    base = os.path.basename(path)
    if files is not None:
        best = None
        for pats, short in files:
            for pat in pats:
                if pat == '*' or fnmatch.fnmatch(base, os.path.basename(pat)) or fnmatch.fnmatch(path, '*' + pat):
                    if pat.startswith('debian/'):
                        continue
                    best = (short, pat)  # the last matching paragraph wins (copyright-format 1.0, "Files")
        if best:
            return licence.from_short(best[0]), 'DEP-5 Files %s: %s' % (best[1], best[0])
        return 'unclear: no Files paragraph matches', 'DEP-5'
    c = licence.from_text(cp_text)
    return (c or 'unclear: the copyright file names no licence of the list'), 'copyright text'


for pkg in pkgs:
    if pkg in done:
        continue
    work = os.path.join(tmp, 'w')
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    r = subprocess.run(['apt-get', 'download', pkg], cwd=work, capture_output=True, text=True)
    debs = [f for f in os.listdir(work) if f.endswith('.deb')]
    if r.returncode != 0 or len(debs) != 1:
        rec.write('%s\t-\t-\t-\t0\t-\t-\tnot fetched: %s\n' % (pkg, (r.stderr.strip().splitlines() or ['?'])[-1]))
        donef.write(pkg + '\n'); donef.flush(); rec.flush()
        continue
    deb = os.path.join(work, debs[0])
    ver = debs[0].split('_')[1] if '_' in debs[0] else '?'
    ex = os.path.join(work, 'x')
    subprocess.run(['dpkg-deb', '-x', deb, ex], check=True)
    os.remove(deb)
    cp = os.path.join(ex, 'usr/share/doc', pkg, 'copyright')
    cp_text = ''
    if os.path.isfile(cp) and not os.path.islink(cp):
        cp_text = open(cp, encoding='utf-8', errors='replace').read()
    else:
        # a documentation folder that is a link to another package's (cm-super to cm-super-minimal): that package's copyright
        docdir = os.path.join(ex, 'usr/share/doc', pkg)
        if os.path.islink(docdir):
            other = os.path.basename(os.readlink(docdir))
            ocp = os.path.join(out, other, 'copyright')
            if os.path.isfile(ocp):
                cp_text = open(ocp, encoding='utf-8', errors='replace').read()
    files = dep5(cp_text) if cp_text else None
    kept_any = False
    for root, dirs, fns in os.walk(ex):
        for fn in fns:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, ex)
            if os.path.islink(full) or not fn.lower().endswith(FONT_EXT):
                continue
            data = open(full, 'rb').read()
            h = hashlib.sha256(data).hexdigest()
            cls, how = classify(rel, cp_text, files)
            if not cp_text:
                cls, how = 'unclear: no copyright file', '-'
            if h in seen:
                why = 'already in the collection'
            elif cls not in licence.USED:
                why = 'licence not on the list'
            else:
                why = 'kept'
                dst = os.path.join(out, pkg, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, 'wb') as f:
                    f.write(data)
                seen.add(h)
                kept_any = True
            rec.write('%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\n' % (pkg, ver, rel, h, len(data), cls, how.replace('\t', ' ').replace('\n', ' '), why))
    if kept_any and cp_text:
        with open(os.path.join(out, pkg, 'copyright'), 'w') as f:
            f.write(cp_text)
    shutil.rmtree(work, ignore_errors=True)
    rec.flush()
    donef.write(pkg + '\n'); donef.flush()
print('done')
