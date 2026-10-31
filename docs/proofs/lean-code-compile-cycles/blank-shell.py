# Blank the comments of a shell script with the edition's Lean Code shell lexer, keeping every line in place
# (each comment becomes the line breaks it held), for scripts the projector leaves because they use LINENO or caller.
#   SPARKY_LEAN=<build repo>/sparky-os python3 blank-shell.py IN OUT
import os, sys
sys.path.insert(0, os.environ.get('SPARKY_LEAN', 'sparky-os'))
from lean import project, consumers, core
mod = consumers.HANDLERS['shell']
text = open(sys.argv[1], encoding='utf-8').read()
buf, i, n = [], 0, 0
for sp in project._lex('shell', mod, text, 'bash'):
    if sp.kind != core.COMMENT:
        continue
    buf.append(text[i:sp.start]); buf.append('\n' * text.count('\n', sp.start, sp.end)); i = sp.end; n += 1
buf.append(text[i:])
out = ''.join(buf)
open(sys.argv[2], 'w', encoding='utf-8').write(out)
print('comments blanked', n, '| bytes', len(text.encode()), '->', len(out.encode()), '| lines', text.count('\n'), '->', out.count('\n'))
