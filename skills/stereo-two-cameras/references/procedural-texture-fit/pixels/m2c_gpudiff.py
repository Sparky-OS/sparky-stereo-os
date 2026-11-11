#!/usr/bin/env python3
"""The browser's drawings against the native ones (milestone 2c): per texture and path, the largest difference in
levels of 255, the mean, and the share of pixels that differ at all and by more than 2.

m2c_gpudiff.py NATIVEDIR OUTDIR TAG [NAME ...]  -> a table on stdout (markdown)"""
import json, os, sys
import numpy as np
from PIL import Image
nat, out, tag = sys.argv[1:4]
res = json.load(open('%s/%s-result.json' % (out, tag)))
names = sys.argv[4:] or sorted(res['textures'])
print('| texture | path | largest difference | mean | pixels that differ | by more than 2 |')
print('|---|---|---|---|---|---|')
for n in names:
    a = np.asarray(Image.open('%s/%s.ppm' % (nat, n)).convert('RGB')).astype(int)
    for k in ('webgpu', 'webgpu-tiles', 'wasm'):
        p = '%s/%s-%s-%s.png' % (out, tag, n, k)
        if not os.path.exists(p):
            continue
        b = np.asarray(Image.open(p).convert('RGB')).astype(int)
        d = np.abs(a - b)
        print('| %s | %s | %d | %.4f | %.3f %% | %.4f %% |' % (n, k, d.max(), d.mean(), 100 * (d.max(2) > 0).mean(), 100 * (d.max(2) > 2).mean()))
