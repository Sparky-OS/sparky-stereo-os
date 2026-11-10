#!/usr/bin/env python3
"""Turn a real side-by-side stereo photograph into a marked .pns at its own size, left eye first.

Usage: real_pns.py REAL.jpg cross|parallel OUT.pns
  cross     a cross-eyed pair: its left half is the right eye's view, so the halves change places
  parallel  its left half is the left eye's view
No pixel is resampled: the halves are copied, and the PNG specification's padding goes between them.
"""
import sys

import numpy as np
from PIL import Image

import pns

real, kind, out = sys.argv[1:4]
a = np.asarray(Image.open(real).convert("RGB"))
w = a.shape[1] // 2
first, second = a[:, :w], a[:, a.shape[1] - w:]
left, right = (second, first) if kind == "cross" else (first, second)
print(out, pns.write(out, np.ascontiguousarray(left), np.ascontiguousarray(right)))
