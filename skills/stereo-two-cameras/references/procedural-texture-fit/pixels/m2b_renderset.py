#!/usr/bin/env python3
"""Write the shell script that draws one texture's final procedure in one place (run inside the lane's container):
the whole at 2048 (and its height as 16 bits), the 16 tiles of 512 each through its window, every rung at 512.

m2b_renderset.py FITDIR NAME OUTDIR native|wasm BINARY > SCRIPT
For wasm, BINARY is the precompiled module (wasmtime compile) and the runtime is /wasmtime in the container."""
import glob, os, sys

fit, name, out, kind, binary = sys.argv[1:6]
S = os.environ['P2P_SCRATCH']  # the scratch folder: fits, pictures, the font index under m1e/ix
if kind == 'native':
    run = binary
else:
    run = ('/wasmtime run --allow-precompiled --dir %s::%s --dir /usr/share/fonts::/usr/share/fonts '
           '--dir /usr/local/share/fonts::/usr/local/share/fonts --dir /usr/share/texmf::/usr/share/texmf '
           '--env WZ_FONTMAP= --env WZ_FONTINDEX=%s/m1e/ix/candidates.tsv --env WZ_GLYPHINDEX= %s') % (S, S, S, binary)
print('set -e')
print('mkdir -p %s' % out)
f = '%s/%s.script' % (fit, name)
print('%s render %s %s/%s.ppm 11 height=%s/%s-h.pgm > %s/%s.render.out 2>&1' % (run, f, out, name, out, name, out, name))
for r in range(4):
    for c in range(4):
        print('%s render %s %s/%s-t-%d-%d.ppm 9 window=%g,%g,0.25 > /dev/null 2>&1' % (run, f, out, name, r, c, c / 4, r / 4))
for rs in sorted(glob.glob('%s/%s.r[0-9][0-9].script' % (fit, name))):
    b = os.path.basename(rs)[:-7]
    print('%s render %s %s/%s.ppm 9 > /dev/null 2>&1' % (run, rs, out, b))
print('echo done %s' % name)
