#!/usr/bin/env python3
"""The render jobs of milestone 2c for one or more textures (for m2c_run.py): the final procedure whole at 2048 with
its 16-bit relief, its 16 tiles of 512 each through its own window, and every rung whole at 512 and at 1:1 around the
corner of four tiles (512 pixels, the window 0.375, 0.375, 0.25).

m2c_renderset.py FITDIR OUTDIR NAME... > JOBS.txt"""
import glob, os, sys

fit, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
for name in sys.argv[3:]:
    f = '%s/%s.script' % (fit, name)
    o = '%s/%s.ppm' % (out, name)
    print(o, 'render', f, o, '11', 'height=%s/%s-h.pgm' % (out, name))
    for r in range(4):
        for c in range(4):
            o = '%s/%s-t-%d-%d.ppm' % (out, name, r, c)
            print(o, 'render', f, o, '9', 'window=%g,%g,0.25' % (c / 4, r / 4))
    for rs in sorted(glob.glob('%s/%s.r[0-9][0-9].script' % (fit, name))):
        b = os.path.basename(rs)[:-7]
        o = '%s/%s-w.ppm' % (out, b)
        print(o, 'render', rs, o, '9')
        o = '%s/%s-c.ppm' % (out, b)
        print(o, 'render', rs, o, '9', 'window=0.375,0.375,0.25')
    o = '%s/%s-c.ppm' % (out, name)
    print(o, 'render', f, o, '9', 'window=0.375,0.375,0.25')
