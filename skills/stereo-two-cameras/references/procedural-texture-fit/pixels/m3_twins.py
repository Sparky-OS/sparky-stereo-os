#!/usr/bin/env python3
"""Compare the tester's WebGPU player (twins.js: whole at 2048 and sixteen 512 tiles put together) with p2p's native
drawings of the same procedures (the final program's p2p render, m3/native). m3_twins.py DIR TAG
Prints per texture: the largest difference in levels of 255 and the share of pixels that differ, whole and tiles."""
import json, sys
import numpy as np
d, tag = sys.argv[1], sys.argv[2]
S = '/var/tmp/procedures-from-pixels-508'
# p2p render of each scene procedure by the final program of milestone 2e (8e613345): m3/native/NAME.ppm
native = {n: 'm3/native/%s.ppm' % n for n in ('red_brick_03', 'floor_tiles_06', 'metal_plate', 'patterned_terracotta_tiling', 'rock_05', 'bark_brown_02', 'rusty_metal_02')}


def ppm(path):
    b = open(path, 'rb').read()
    f, p = [], 0
    while len(f) < 4:
        while b[p:p + 1].isspace():
            p += 1
        q = p
        while not b[q:q + 1].isspace():
            q += 1
        f.append(b[p:q]); p = q
    w, h = int(f[1]), int(f[2])
    return np.frombuffer(b[p + 1:p + 1 + w * h * 3], np.uint8).reshape(h, w, 3)


info = json.load(open('%s/%s-twins.json' % (d, tag)))
print('adapter', info['adapter'])
for name, rel in native.items():
    n = ppm('%s/%s' % (S, rel)).astype(int)
    for kind in ('whole', 'tiles'):
        g = np.frombuffer(open('%s/%s-%s-%s.rgb' % (d, tag, name, kind), 'rb').read(), np.uint8).reshape(2048, 2048, 3).astype(int)
        diff = np.abs(g - n).max(axis=2)
        print('%-28s %-5s max %3d levels, %.3f %% of pixels differ' % (name, kind, diff.max(), 100 * (diff > 0).mean()))
    t = info['textures'][name]
    print('%-28s whole: %d submissions, longest %.1f ms, sum %.1f ms; tiles: %d submissions, longest %.1f ms' % (
        name, t['submissionsWhole'], t['longestWholeMs'], t['sumWholeMs'], t['submissionsTiles'], t['longestTileMs']))
