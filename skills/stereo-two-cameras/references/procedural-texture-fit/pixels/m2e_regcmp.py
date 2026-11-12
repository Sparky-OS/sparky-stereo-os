#!/usr/bin/env python3
"""Compare the final program's redraws with the earlier milestones' own (milestone 2e): m2e_regcmp.py NEWDIR OLDDIR
Every .ppm and .pgm of NEWDIR against the file of the same name in OLDDIR, byte for byte; prints same, different and
missing counts and the names that differ."""
import filecmp, os, sys
new, old = sys.argv[1], sys.argv[2]
same = diff = miss = 0
bad = []
for f in sorted(os.listdir(new)):
    if not f.endswith(('.ppm', '.pgm')):
        continue
    o = os.path.join(old, f)
    if not os.path.exists(o):
        miss += 1
        continue
    if filecmp.cmp(os.path.join(new, f), o, shallow=False):
        same += 1
    else:
        diff += 1
        bad.append(f)
print('%s against %s: same bytes %d, different %d, without an earlier file %d' % (new, old, same, diff, miss))
for b in bad[:20]:
    print('  different:', b)
