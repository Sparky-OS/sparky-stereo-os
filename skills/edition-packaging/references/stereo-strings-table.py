#!/usr/bin/python3 -I
"""stereo-strings-table.py LANG --pool POOL [--stage STAGE ...] [--tree TRANSLATIONS_DIR] [--work DIR]

For every source package whose debian/patches carries *.po.patch files, takes the newest version found in the pool (and in
the stage folders, which win when newer), reads the msgids those patches add (any language, any hunk), and asks the built
binaries' LANG catalogue (usr/share/locale/LANG/LC_MESSAGES/DOMAIN.mo) whether it answers each one. Prints one row per
source: msgids, how many LANG lacks, how many of those a patch in TRANSLATIONS_DIR already writes for LANG ("in tree": a
rebuild is all it needs) and how many nobody wrote.
The catalogue's answer is what counts: a grep of the build tree misses patches that only the published source carries.
A .po.patch may be in git-diff form ("diff --git a/po/xx/dom.po"), in plain form ("+++ b/po/xx/dom.po") or in
"Index:" form ("+++ name/po/xx/dom.po"); all three are read."""
import argparse, collections, gettext, glob, os, re, shutil, subprocess, sys, tarfile

HEAD = re.compile(r'^(?:diff --git a/po/([^/]+)/(\S+)\.po |\+\+\+ [^/\s]+/po/([^/]+)/(\S+?)\.po(?:\s|$))')

def unesc(s):
    return re.sub(r'\\(n|t|"|\\)', lambda m: {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}[m.group(1)], s)

def entries(lines):
    out, e, field = [], None, None
    for l in lines + ['']:
        if not l.strip():
            if e and 'id' in e: out.append(e)
            e, field = None, None
            continue
        m = re.match(r'^(msgctxt|msgid_plural|msgid|msgstr(?:\[\d\])?) "(.*)"$', l)
        if m:
            e = e if e is not None else {}
            k = m.group(1)
            field = {'msgctxt': 'ctxt', 'msgid': 'id', 'msgid_plural': 'idpl'}.get(k, 'str')
            if field != 'str': e[field] = m.group(2)
            elif 'str' not in e: e['str'] = m.group(2)
            continue
        m = re.match(r'^"(.*)"$', l)
        if m and e is not None and field in e:
            e[field] += m.group(1)
    return out

def parse(text):
    """{(lang, domain): [entry]} from the added lines of a .po.patch"""
    res, cur, lines = {}, None, []
    for l in text.split('\n'):
        m = HEAD.match(l)
        if m:
            if cur: res[cur] = entries(lines)
            cur, lines = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4)), []
        elif cur and l.startswith('+') and not l.startswith('+++'):
            lines.append(l[1:])
    if cur: res[cur] = entries(lines)
    return res

def newest(cands):
    best = cands[0]
    for c in cands[1:]:
        if subprocess.run(['dpkg', '--compare-versions', c[0], 'gt', best[0]]).returncode == 0: best = c
    return best

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('lang'); ap.add_argument('--pool', required=True)
    ap.add_argument('--stage', action='append', default=[]); ap.add_argument('--tree'); ap.add_argument('--work', default='/var/tmp/stereo-strings')
    a = ap.parse_args()
    cands = collections.defaultdict(list)
    for root in [a.pool] + a.stage:
        for r, ds, fs in os.walk(root, followlinks=False):
            for f in fs:
                m = re.match(r'(.+?)_(.+)\.debian\.tar\.xz$', f)
                if m: cands[m.group(1)].append((m.group(2), os.path.join(r, f), root))
    written = set()
    if a.tree:
        for f in glob.glob(a.tree + '/*.po.patch'):
            for (lg, dom), es in parse(open(f, encoding='utf8', errors='replace').read()).items():
                if lg == a.lang: written |= {(dom, unesc(e.get('ctxt', '')) or None, unesc(e['id'])) for e in es}
    print('%-20s %-28s %6s %6s %7s %6s' % ('source', 'version', 'msgids', 'lacks', 'in tree', 'nobody'))
    for src, lst in sorted(cands.items()):
        ver, path, base = newest([(v, p) for v, p, _ in lst]) + (None,)
        base = [b for v, p, b in lst if p == path][0]
        tf = tarfile.open(path)
        ents = {}
        for m in tf.getmembers():
            if m.name.endswith('.po.patch'):
                for (lg, dom), es in parse(tf.extractfile(m).read().decode('utf8', 'replace')).items():
                    for e in es: ents.setdefault((dom, unesc(e.get('ctxt', '')) or None, unesc(e['id'])), e)
        ents = {k: v for k, v in ents.items() if k[2]}
        if not ents: continue
        tmp = os.path.join(a.work, src); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
        d = os.path.dirname(path)
        for r, ds, fs in os.walk(d if base == a.pool else base, followlinks=False):
            for f in fs:
                if f.endswith('.deb') and '_' + ver.replace(':', '') + '_' in f and 'dbgsym' not in f and '-lc-hr' not in f:
                    p1 = subprocess.Popen(['dpkg-deb', '--fsys-tarfile', os.path.join(r, f)], stdout=subprocess.PIPE)
                    subprocess.run(['tar', '-x', '-C', tmp, '--wildcards', '*/locale/%s/LC_MESSAGES/*.mo' % a.lang], stdin=p1.stdout, stderr=subprocess.DEVNULL)
                    p1.wait()
        lacks = []
        for (dom, ctxt, mid), e in ents.items():
            mo = '%s/usr/share/locale/%s/LC_MESSAGES/%s.mo' % (tmp, a.lang, dom)
            cat = gettext.GNUTranslations(open(mo, 'rb'))._catalog if os.path.exists(mo) else {}
            k = (ctxt + '\x04' + mid) if ctxt else mid
            v = cat.get((k, 0)) if 'idpl' in e else cat.get(k)
            if not v: lacks.append((dom, ctxt, mid))
        print('%-20s %-28s %6d %6d %7d %6d' % (src, ver, len(ents), len(lacks), sum(1 for x in lacks if x in written), sum(1 for x in lacks if x not in written)))

main()
