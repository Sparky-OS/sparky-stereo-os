#!/usr/bin/env python3
"""Bytes and time of the found procedures beside the artists' own graphs.

Usage: table.py FITDIR NAMES.txt NAME...     (NAMES.txt is prior.py's: operators, bytes, name)
"""
import re, sys
fit, names = sys.argv[1], sys.argv[2]
orig = {}
for line in open(names):
    n, b, name = line.split(None, 2)
    orig[name.strip()] = (int(n), int(b))
print("| texture | artist's graph | found | found / artist's bytes | time |")
print("|---|---|---|---|---|")
for name in sys.argv[3:]:
    last = open("%s/%s.out" % (fit, name)).read().strip().splitlines()[-1]
    m = re.match(r"done: (\d+) operators, (\d+) bytes, ([\d.]+) s", last)
    if not m:
        print("| %s | | no result: %s | | |" % (name, last)); continue
    o = orig[name]
    print("| %s | %d operators, %d B | %s operators, %s B | %.0f %% | %.0f s |" % (name, o[0], o[1], m.group(1), m.group(2), 100.0 * int(m.group(2)) / o[1], float(m.group(3))))
