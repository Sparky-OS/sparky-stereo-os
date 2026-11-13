#!/usr/bin/env python3
"""rust-census.py TOOLKIT METADATA.json OUT.json [FILELIST]: count, over the Rust files of every package in a
`cargo metadata` graph (or only the files named in FILELIST, one path per line: the files a build's dep-info says the
compiler read), what the Lean Code Rust adapter removes and each kind of comment or position use that is data.
TOOLKIT is the build tree's sparky-os folder (lean/lang_rust.py)."""
import collections, json, os, re, sys
from multiprocessing import Pool
sys.path.insert(0, sys.argv[1])
from lean import lang_rust, project, core

FENCE = re.compile(r'```')
DIRECTIVES = {'safety': re.compile(r'^//\s*SAFETY\b', re.I), 'compiletest //@': re.compile(r'^//@'), 'ui annotation //~': re.compile(r'^//~'),
              'todo/fixme': re.compile(r'^//\s*(TODO|FIXME)\b', re.I), 'rustfmt/clippy/tidy': re.compile(r'^//\s*(rustfmt|clippy|tidy|ignore-tidy)', re.I)}
CODE = {'line!/column!': re.compile(r'\b(?:line|column)\s*!\s*[(\[{]'), 'file!': re.compile(r'\bfile\s*!\s*[(\[{]'),
        'Location::caller': re.compile(r'\bLocation\s*::\s*caller\s*\('), '#[track_caller]': re.compile(r'#\s*\[\s*track_caller\s*\]'),
        'include_str!/include_bytes!': re.compile(r'\binclude_(?:str|bytes)\s*!\s*[(\[{]'), 'include!': re.compile(r'\binclude\s*!\s*[(\[{]'),
        '#[doc = ...] written out': re.compile(r'#\s*!?\s*\[\s*doc\s*='), 'deny/forbid(missing_docs)': re.compile(r'(?:deny|forbid)\s*\([^)]*missing_docs'),
        'panic sites (panic!, unwrap, expect, assert*, unreachable!, todo!, unimplemented!)': re.compile(r'\b(?:panic|assert|assert_eq|assert_ne|debug_assert|debug_assert_eq|debug_assert_ne|unreachable|todo|unimplemented)\s*!|\.\s*(?:unwrap|expect)\s*\('),
        'log/tracing macros': re.compile(r'\b(?:trace|debug|info|warn|error)\s*!\s*\('), 'dbg!': re.compile(r'\bdbg\s*!')}


def one(path):
    c = collections.Counter()
    try:
        raw = open(path, 'rb').read()
    except OSError:
        return path, {'unreadable': 1}, []
    c['files'] = 1; c['bytes'] = len(raw); c['lines'] = raw.count(b'\n')
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        c['left: not UTF-8'] = 1; return path, dict(c), []
    if '\r' in text:
        c['left: CRLF'] = 1; return path, dict(c), []
    why = lang_rust.refuse(text)
    if why:
        c['left: ' + why] = 1; return path, dict(c), []
    try:
        spans = lang_rust.lex(text)
        lean, rendered, _ = project.render_text(text, 'rust', None, None, None, pointer=False)
    except Exception as e:
        c['left: lexer: ' + str(e)] = 1; return path, dict(c), []
    for sp in spans:
        t = text[sp.start:sp.end]
        if sp.kind == core.COMMENT:
            c['comments removed'] += 1; c['comment bytes'] += len(t.encode())
            for k, rx in DIRECTIVES.items():
                if rx.match(t): c['removed comment that is a tool directive: ' + k] += 1
        elif sp.kind == core.KEEP:
            kind = 'doc' if 'doc' in sp.why else 'notice' if 'notice' in sp.why else 'interpreter line' if 'interpreter' in sp.why else 'pointer'
            c[f'kept {kind} comments'] += 1; c[f'kept {kind} bytes'] += len(t.encode())
            if kind == 'doc':
                c['doc lines'] += t.count('\n') + 1; c['doc code fences'] += len(FENCE.findall(t))
    out = lean.encode()
    c['lean bytes'] = len(out); c['lean lines'] = out.count(b'\n')
    c['files that change'] = 1 if rendered.removed else 0
    code = lang_rust.code_text(text)
    for k, rx in CODE.items():
        n = len(rx.findall(code))
        if n: c[k] += n; c['files with ' + k] += 1
    emb = [(t, w) for t, w in lang_rust.embedded(path, text)]
    return path, dict(c), emb


def main():
    meta = json.load(open(sys.argv[2])); only = None
    if len(sys.argv) > 4:
        only = {os.path.realpath(l.strip()) for l in open(sys.argv[4]) if l.strip()}
    ws = set(meta['workspace_members']); crates = []
    for p in meta['packages']:
        d = os.path.dirname(p['manifest_path']); src = p['source'] or ''
        kind = 'workspace' if p['id'] in ws else 'registry' if src.startswith('registry') else 'git' if src.startswith('git') else 'path'
        files = []
        for r, ds, fs in os.walk(d):
            ds[:] = [x for x in ds if x not in ('target', '.git')]
            files += [os.path.join(r, f) for f in fs if f.endswith('.rs')]
        if only is not None:
            files = [f for f in files if os.path.realpath(f) in only]
        pm = any(t.get('kind') == ['proc-macro'] for t in p['targets'])
        bs = [t['src_path'] for t in p['targets'] if t.get('kind') == ['custom-build']]
        crates.append({'name': p['name'], 'version': p['version'], 'kind': kind, 'dir': d, 'files': sorted(files), 'proc_macro': pm, 'build_script': bs})
    allfiles = sorted({f for c in crates for f in c['files']})
    with Pool(3) as pool:
        res = pool.map(one, allfiles, chunksize=64)
    per = {p: c for p, c, _ in res}; emb = {p: e for p, _, e in res if e}
    tot = {}
    for c in crates:
        t = tot.setdefault(c['kind'], collections.Counter())
        for f in c['files']:
            t.update(per[f])
        t['crates'] += 1; t['procedural-macro crates'] += c['proc_macro']; t['crates with a build script'] += bool(c['build_script'])
        readers = []
        for b in c['build_script']:
            try: why = lang_rust.source_reader(os.path.relpath(b, c['dir']), open(b, errors='replace').read())
            except OSError: why = None
            if why: readers.append(why)
        if readers:
            t['crates whose build script reads Rust source text (left authored whole)'] += 1
            t['files left: build script reads source'] += len(c['files']); c['reader'] = readers
        if c['proc_macro']:
            for f in c['files']:
                why = lang_rust.source_reader(os.path.relpath(f, c['dir']), open(f, errors='replace').read(), macro=True)
                if why:
                    t['procedural-macro crates that ask for source text (stop until reviewed)'] += 1; c['macro_reader'] = why; break
    targets = collections.Counter(); rs_targets = []
    fileset = set(allfiles)
    for p, es in emb.items():
        for target, why in es:
            if target.endswith('/'): targets['computed path'] += 1
            else:
                ext = os.path.splitext(target)[1].lower() or '(none)'; targets[ext] += 1
                if os.path.realpath(target) in fileset or ext == '.rs': rs_targets.append((p, target))
    out = {'totals': {k: dict(v) for k, v in tot.items()}, 'include_str targets by extension': dict(targets), 'include_str targets that are Rust files': rs_targets,
           'build-script readers': [(c['name'], c['version'], c['kind'], c['reader']) for c in crates if c.get('reader')],
           'macro readers': [(c['name'], c['version'], c['kind'], c['macro_reader']) for c in crates if c.get('macro_reader')],
           'crates': len(crates), 'files': len(allfiles)}
    json.dump(out, open(sys.argv[3], 'w'), indent=1, sort_keys=True)
    print('done', len(crates), 'crates', len(allfiles), 'files')


main()
