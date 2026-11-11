#!/usr/bin/env python3
"""The bytes of milestone 2 against the fair baseline, one row per texture, from m2compose.py's records.

m2table.py EVDIR NAME... > table.md"""
import json, os, sys

ev = sys.argv[1]
print('| texture | tiles took | rungs of the tiled texture (bytes, all 16 tiles) | one procedure for the whole picture | the picture as JPEG q90 | its lower-resolution copies (the fair baseline) | procedures + picture against picture + copies |')
print('|---|---|---|---|---|---|---|')
for name in sys.argv[2:]:
    r = json.load(open(os.path.join(ev, name + '.json')))
    b = r['baseline']
    kinds = {}
    for v in r['took'].values():
        kinds[v] = kinds.get(v, 0) + 1
    last = r['rung_bytes'][-1]
    gain = 100.0 * ((b['jpeg'] + last) / (b['jpeg'] + b['chain']) - 1)
    print('| %s | %s | %s | %s B (%s) | %s B | %s B (+%.1f %%) | %+.1f %% |' % (
        name, ', '.join('%s %d' % kv for kv in sorted(kinds.items())), ' / '.join(format(x, ',') for x in r['rung_bytes']),
        format(r['l0_bytes'], ','), r.get('l0_variant', 'plain'), format(b['jpeg'], ','), format(b['chain'], ','),
        100.0 * b['chain'] / b['jpeg'], gain))
