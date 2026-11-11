#!/usr/bin/env python3
"""Sort the font index into the reading's candidates: classify.py INDEX.tsv GOOGLE_DIR DEBIAN_DIR OUTDIR

For every face of the index (p2p fontindex) the licence class is read from the font's own name table (licence
description, name ID 13) and from its source's record (Google Fonts: the licence folder and the family's METADATA.pb;
Debian: the package's machine-readable copyright, as fetch_debian.py recorded it). The machine's own fonts are
candidates whatever their licence (Daniel, 2026-11-11: the person's installed fonts, the core fonts included, are read
and credited, never copied). Of the collection only the classes on the brief's list are candidates. A family, style and version
already given by an earlier source (machine, then Google Fonts, then Debian) is listed and left out of the candidates.

Writes OUTDIR/index-classified.tsv (every face, with class, class_from, use, why), OUTDIR/candidates.tsv (the faces
used, the same columns as the index so the renderer reads it as WZ_FONTINDEX) and OUTDIR/summary.txt.
"""
import collections, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import licence

index, gdir, ddir, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
rows = [l.rstrip('\n').split('\t') for l in open(index, encoding='utf-8')]
head, rows = rows[0], rows[1:]
col = {n: i for i, n in enumerate(head)}

# Debian: what fetch_debian.py recorded for each kept file
deb = {}
rec = os.path.join(ddir, 'records.tsv')
if os.path.exists(rec):
    for l in open(rec, encoding='utf-8'):
        p = l.rstrip('\n').split('\t')
        if len(p) >= 8 and p[7] == 'kept':
            deb[os.path.join(ddir, p[0], p[2])] = (p[0], p[1], p[5], p[6])

# Google Fonts: the licence folder and METADATA.pb's licence and designer lines
meta_cache = {}
def google_record(path):
    rel = os.path.relpath(path, gdir)
    parts = rel.split(os.sep)
    folder = {'ofl': 'OFL', 'apache': 'Apache-2.0', 'ufl': 'UFL'}.get(parts[0])
    fam_dir = os.path.join(gdir, parts[0], parts[1]) if len(parts) > 1 else None
    md = meta_cache.get(fam_dir)
    if md is None and fam_dir:
        md = {}
        mp = os.path.join(fam_dir, 'METADATA.pb')
        if os.path.exists(mp):
            t = open(mp, encoding='utf-8', errors='replace').read()
            m = re.search(r'^license:\s*"([^"]+)"', t, re.M)
            md['license'] = m.group(1) if m else ''
            md['designer'] = ', '.join(re.findall(r'^designer:\s*"([^"]+)"', t, re.M))
        meta_cache[fam_dir] = md
    return folder, (md or {})

out_rows = []
seen_fs = {}
count = collections.Counter()
for r in rows:
    path, source = r[col['file']], r[col['source']]
    lic_text = r[col['licence']] + ' ' + r[col['licence_url']]
    own = licence.from_text(lic_text) if r[col['licence']] != '-' else None
    cls, how, use, why = None, '', 'no', ''
    if source == 'machine':
        cls = own or 'installed on this machine (licence not stated in the font)'
        how = 'name table' if own else '-'
        use, why = 'yes', "the machine's own font"
    elif source == 'google':
        folder, md = google_record(path)
        src_cls = licence.from_short(md.get('license') or folder or '')
        cls = src_cls
        how = 'Google Fonts %s folder, METADATA.pb license "%s"' % (folder, md.get('license', ''))
        if own and own != src_cls:
            how += '; the name table says %s' % own
        use = 'yes' if cls in licence.USED else 'no'
        why = 'on the list' if use == 'yes' else 'licence not on the list'
    elif source == 'debian':
        d = deb.get(path)
        if d:
            cls, how = d[2], 'Debian %s %s copyright: %s' % (d[0], d[1], d[3])
            if own and own != cls:
                how += '; the name table says %s' % own
        else:
            cls, how = 'unclear: no record', '-'
        use = 'yes' if cls in licence.USED else 'no'
        why = 'on the list' if use == 'yes' else 'licence not on the list'
    fs = (r[col['family']].strip().lower(), r[col['style']].strip().lower(), r[col['version']].strip().lower())
    if use == 'yes':
        if fs in seen_fs and seen_fs[fs] != source:
            use, why = 'no', 'the same family, style and version is already given by the %s copy' % seen_fs[fs]
        elif fs in seen_fs:
            pass  # a second face of the same family and style in the same source: kept (another version or build)
        else:
            seen_fs[fs] = source
    count[(source, use, why if use == 'no' else 'used')] += 1
    out_rows.append(r + [cls or '-', how or '-', use, why])

with open(os.path.join(out, 'index-classified.tsv'), 'w', encoding='utf-8') as f:
    f.write('\t'.join(head + ['class', 'class_from', 'use', 'why']) + '\n')
    for r in out_rows:
        f.write('\t'.join(x.replace('\t', ' ') for x in r) + '\n')
with open(os.path.join(out, 'candidates.tsv'), 'w', encoding='utf-8') as f:
    f.write('\t'.join(head + ['class', 'class_from']) + '\n')
    for r in out_rows:
        if r[-2] == 'yes':
            f.write('\t'.join(x.replace('\t', ' ') for x in r[:-2]) + '\n')
with open(os.path.join(out, 'summary.txt'), 'w', encoding='utf-8') as f:
    for k, v in sorted(count.items()):
        f.write('%6d  %s  %s  %s\n' % (v, k[0], k[1], k[2]))
    cls_count = collections.Counter((r[col['source']], r[-4]) for r in out_rows if r[-2] == 'yes')
    f.write('\nused, by source and licence class:\n')
    for k, v in sorted(cls_count.items()):
        f.write('%6d  %s  %s\n' % (v, k[0], k[1]))
print(open(os.path.join(out, 'summary.txt')).read())
