# Copy a C++ header tree through the edition's Lean Code C/C++ renderer and its GCC check.
# Measurement only: the compiler is the sole consumer here, so the refusal for Doxygen comments
# (another consumer: documentation generators) is not applied; notices stay, #line keeps line numbers.
import sys, os, json, collections
sys.path.insert(0, os.environ.get('SPARKY_LEAN', 'sparky-os'))  # the build repo's sparky-os folder
from lean import project, consumers
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
            lean, rendered, spans = project.render_text(text, 'c', 'c++', 'libstdc++-16-dev', p, pointer=False)
            if rendered.removed:
                ok, detail = project._verify('c', mod, text, lean, 'c++')
                if ok: out = lean.encode('utf-8'); st['projected, check passed'] += 1
                else: st['check failed, kept'] += 1
            else: st['no removable comments'] += 1
        except Exception as e:
            st[f'not read: {type(e).__name__}'] += 1
        open(q, 'wb').write(out); bi += len(data); bo += len(out)
print(json.dumps({'tree': src, 'files': dict(st), 'bytes_in': bi, 'bytes_out': bo}))
