# Variant "blank": the same comment spans from the edition's C/C++ lexer, each removed comment replaced
# by one space, or by the newlines it held, so every line keeps its number without any #line directive.
# Kept comments (notices, fall-through) stay. A multi-line comment inside a directive is left as written.
import sys, os, json, collections
sys.path.insert(0, os.environ.get('SPARKY_LEAN', 'sparky-os'))  # the build repo's sparky-os folder
from lean import project, consumers, core
mod = consumers.HANDLERS['c']
src, dst = sys.argv[1], sys.argv[2]
st = collections.Counter(); bi = bo = 0
for root, dirs, files in os.walk(src):
    for f in files:
        p = os.path.join(root, f); q = os.path.join(dst, os.path.relpath(p, src))
        os.makedirs(os.path.dirname(q), exist_ok=True)
        data = open(p, 'rb').read(); out = data
        try:
            text = data.decode('utf-8')
            spans = project._lex('c', mod, text, 'c++')
            buf, i, n = [], 0, 0
            for sp in spans:
                if sp.kind != core.COMMENT: continue
                ls = text.rfind('\n', 0, sp.start) + 1
                k = text.count('\n', sp.start, sp.end)
                if k and text[ls:sp.start].lstrip().startswith('#'): continue
                buf.append(text[i:sp.start]); buf.append('\n' * k if k else ' '); i = sp.end; n += 1
            buf.append(text[i:])
            if n: out = ''.join(buf).encode('utf-8'); st['comments blanked'] += 1
            else: st['no removable comments'] += 1
        except Exception as e:
            st[f'not read: {type(e).__name__}'] += 1
        open(q, 'wb').write(out); bi += len(data); bo += len(out)
print(json.dumps({'tree': src, 'files': dict(st), 'bytes_in': bi, 'bytes_out': bo}))
