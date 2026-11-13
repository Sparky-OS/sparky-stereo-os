#!/usr/bin/env python3
"""Check relative links and anchors of the files given; compare a translation with its source.

usage: check-front-page-links.py REPO FILE... [--pair SOURCE TRANSLATION]...
           [--placeholder NAME]... [--allow URL]... [--control]

FILE: every relative link must reach a file, and every fragment an anchor of that file
(GitHub's heading slugs and explicit <a id> or <a name>).
--pair: the translation must keep the source's external links, explicit ids, heading
levels, pictures, and every anchor the source's headings make (the page title excepted).
--placeholder: a link target that stands for a page that does not exist yet; counted, not resolved.
--allow: an external link that may differ between a source and its translation
(the vendor's page in the translation's language, the sign-up thread of each language).
--control: also run a case that must fail, so a green run means something.
Exit 1 on any problem.
"""
import os, re, sys, unicodedata

PLACEHOLDERS = set()

def strip_code(text):
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    # inline code goes, except where it is a link's own text: [`name`](target)
    return re.sub(r'(?<!\[)`[^`\n]*`(?!\])', '', text)

def slug(heading):
    h = re.sub(r'<[^>]+>', '', heading)
    h = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', h)
    h = h.replace('`', '').replace('*', '').strip().lower()
    out = []
    for c in h:
        cat = unicodedata.category(c)
        if c in '-_' or cat[0] in 'LN' or cat in ('Mn', 'Mc'):
            out.append(c)
        elif c == ' ':
            out.append('-')
    return ''.join(out)

def anchors(path):
    text = open(path, encoding='utf-8').read()
    ids = set(re.findall(r'<a\s+(?:id|name)="([^"]+)"', text))
    seen = {}
    for m in re.finditer(r'^(#{1,6})\s+(.*?)\s*#*\s*$', strip_code(text), flags=re.M):
        s = slug(m.group(2))
        n = seen.get(s, 0)
        seen[s] = n + 1
        ids.add(s if n == 0 else '%s-%d' % (s, n))
    return ids

def links(path):
    text = strip_code(open(path, encoding='utf-8').read())
    found = re.findall(r'\]\(([^)\s]+)(?:\s+"[^"]*")?\)', text)
    found += re.findall(r'(?:href|src)="([^"]+)"', text)
    return found

def check(repo, rel):
    path = os.path.join(repo, rel)
    bad, n_rel, n_frag, n_ext, n_ph = [], 0, 0, 0, 0
    for target in links(path):
        if target in PLACEHOLDERS:
            n_ph += 1
            continue
        if re.match(r'[a-z][a-z0-9+.-]*:', target):
            n_ext += 1
            continue
        file_part, _, frag = target.partition('#')
        dest = path if not file_part else os.path.normpath(os.path.join(os.path.dirname(path), file_part))
        n_rel += 1
        if not os.path.exists(dest):
            bad.append('%s: missing file: %s' % (rel, target))
            continue
        if frag:
            n_frag += 1
            if dest.endswith('.md') and frag not in anchors(dest):
                bad.append('%s: missing anchor: %s' % (rel, target))
    print('%-40s relative %3d (with anchor %3d)  external %3d  placeholder %d  broken %d'
          % (rel, n_rel, n_frag, n_ext, n_ph, len(bad)))
    return bad

def pair(repo, src, tr, allowed):
    """Translation against source: external URLs, explicit ids, heading levels, picture sources."""
    def parts(rel):
        p = os.path.join(repo, rel)
        text = open(p, encoding='utf-8').read()
        ext = sorted(t for t in links(p) if re.match(r'https?:', t))
        ids = set(re.findall(r'<a\s+id="([^"]+)"', text))
        levels = [len(m) for m in re.findall(r'^(#{1,6})\s', strip_code(text), flags=re.M)]
        src_ = sorted(re.findall(r'src="([^"]+)"', text) + re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text))
        return ext, ids, levels, src_, anchors(p)
    a, b = parts(src), parts(tr)
    problems = []
    only_src = [u for u in a[0] if u not in b[0] and u not in allowed]
    only_tr = [u for u in b[0] if u not in a[0] and u not in allowed]
    if only_src: problems.append('external links only in %s: %s' % (src, only_src))
    if only_tr: problems.append('external links only in %s: %s' % (tr, only_tr))
    if a[1] - b[1]: problems.append('explicit ids missing in %s: %s' % (tr, sorted(a[1] - b[1])))
    if a[2] != b[2]: problems.append('heading levels differ: %s against %s' % (a[2], b[2]))
    if a[3] != b[3]: problems.append('pictures differ: %s against %s' % (a[3], b[3]))
    h1 = {slug(m) for m in re.findall(r'^#\s+(.*)$', strip_code(open(os.path.join(repo, src), encoding='utf-8').read()), flags=re.M)}
    lost = a[4] - b[4] - h1  # the page title's anchor is the page itself
    if lost: problems.append('anchors of %s that do not resolve in %s: %s' % (src, tr, sorted(lost)))
    print('pair %s -> %s: external %d/%d, explicit ids %d/%d, headings %d/%d, pictures %d/%d, source anchors lost %d'
          % (src, tr, len(a[0]), len(b[0]), len(a[1]), len(b[1]), len(a[2]), len(b[2]), len(a[3]), len(b[3]), len(lost)))
    return problems

def main():
    args = sys.argv[1:]
    repo = args.pop(0)
    files, pairs, control, allowed = [], [], False, set()
    while args:
        x = args.pop(0)
        if x == '--pair':
            pairs.append((args.pop(0), args.pop(0)))
        elif x == '--placeholder':
            PLACEHOLDERS.add(args.pop(0))
        elif x == '--allow':
            allowed.add(args.pop(0))
        elif x == '--control':
            control = True
        else:
            files.append(x)
    bad = []
    for f in files:
        bad += check(repo, f)
    for s, t in pairs:
        bad += pair(repo, s, t, allowed)
    if control:
        import tempfile, shutil
        d = tempfile.mkdtemp()
        try:
            open(os.path.join(d, 'a.md'), 'w').write('# One\n[x](a.md#one) [y](a.md#onee) [z](missing.md)\n')
            got = check(d, 'a.md')
            ok = len(got) == 2
            print('control (one wrong anchor, one missing file must be reported): %s' % ('PASS' if ok else 'FAIL'))
            if not ok: bad.append('control failed')
        finally:
            shutil.rmtree(d)
    for b in bad:
        print('BROKEN', b)
    print('RESULT: %s' % ('FAIL, %d problem(s)' % len(bad) if bad else 'PASS, 0 broken'))
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
