#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""halves_raw.py WLREC_DIR: for every buffer the recorder wrote (skills/stereo-proof-rig/scripts/wlrec.c), in commit
order, the pixels that differ between its left and its right half. The last line is the buffer left on the screen."""
import json, os, sys
import numpy as np
d = sys.argv[1]
for line in open(os.path.join(d, "log.jsonl")):
    j = json.loads(line)
    p = os.path.join(d, os.path.basename(j["file"]))
    if not os.path.exists(p):
        continue
    w, h, stride = j["width"], j["height"], j["stride"]
    a = np.fromfile(p, dtype=np.uint8)[:stride * h].reshape(h, stride)[:, :w * 4].reshape(h, w, 4)[..., :3].astype(int)
    half = w // 2
    n = int((np.abs(a[:, :half] - a[:, half:2 * half]).sum(axis=2) > 24).sum())
    print("%s %dx%d differing pixels between the buffer's halves: %d" % (os.path.basename(p), w, h, n))
