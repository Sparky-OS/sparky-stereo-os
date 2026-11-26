#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""check_lit.py CAPTURE.png OUTPUT_WIDTH MIN_FRACTION

Whether the window's own widgets are on the output: the share of the left eye (or of the one picture) that is not
black must be at least MIN_FRACTION. A test window of 640x460 with its area is about 0.29 of a 1280x800 output; the
area alone is 0.127. Exits 1 below it.
"""
import sys

import numpy as np
from PIL import Image

img = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(np.int32)
width, minimum = int(sys.argv[2]), float(sys.argv[3])
eye = img[:, :width]
lit = float((eye.sum(axis=2) > 60).mean())
print(("PASS" if lit >= minimum else "FAIL") + " lit share of the picture %.3f (at least %.3f wanted)" % (lit, minimum))
sys.exit(0 if lit >= minimum else 1)
