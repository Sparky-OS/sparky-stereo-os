#!/usr/bin/env python3
"""Put a real stereo photograph beside a procedural stereo texture, both left eye first, at the same size.

Usage: real_pair.py REAL.jpg cross|parallel PROCEDURAL-sbs-tile.png OUT_PREFIX
  cross     the photograph is a cross-eyed pair: its left half is the right eye's view, so the halves are swapped
  parallel  its left half is the left eye's view
Writes OUT_PREFIX-real-sbs-3840x1080.png (the photograph alone, left eye first),
OUT_PREFIX-real-beside-procedural-sbs-3840x1080.png and the two red-cyan versions.
"""
import sys

import numpy as np
from PIL import Image

real, kind, proc, prefix = sys.argv[1:5]
W, H, S = 1920, 1080, 900
im = Image.open(real).convert("RGB")
a, b = im.crop((0, 0, im.width // 2, im.height)), im.crop((im.width // 2, 0, im.width, im.height))
left, right = (b, a) if kind == "cross" else (a, b)
p = Image.open(proc).convert("RGB")
pl, pr = p.crop((0, 0, p.width // 2, p.height)), p.crop((p.width // 2, 0, p.width, p.height))


def fit(i, box_w, box_h):
    s = min(box_w / i.width, box_h / i.height)
    return i.resize((max(1, round(i.width * s)), max(1, round(i.height * s))), Image.LANCZOS)


def frame(items):
    f = Image.new("RGB", (W, H), (96, 96, 96))
    slot = W // len(items)
    for k, i in enumerate(items):
        i = fit(i, slot - 40, S)
        f.paste(i, (k * slot + (slot - i.width) // 2, (H - i.height) // 2))
    return np.asarray(f)


def write(L, R, name):
    Image.fromarray(np.concatenate([L, R], 1)).save(f"{prefix}-{name}-sbs-3840x1080.png")
    Image.fromarray(np.stack([L[..., 0], R[..., 1], R[..., 2]], -1)).save(f"{prefix}-{name}-anaglyph.png")


write(frame([left]), frame([right]), "real")
write(frame([left, pl]), frame([right, pr]), "real-beside-procedural")
