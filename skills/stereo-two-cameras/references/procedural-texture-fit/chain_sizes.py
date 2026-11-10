#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# The fair baseline for DPFR (Daniel, 2026-11-10): what a traditional asset ships besides the picture.
# Usage: chain_sizes.py PICTURE.png [...]  prints, per picture, the JPEG q90 bytes of the picture, of its
# lower-resolution copies (box-averaged levels down to 1 pixel, as a mip chain), and of two device copies
# (half and quarter size), plus the same chain as PNG.
import io, sys
import numpy as np
from PIL import Image

def size(a, fmt):
    b = io.BytesIO()
    Image.fromarray(a).save(b, fmt, **({"quality": 90} if fmt == "JPEG" else {"optimize": True}))
    return b.tell()

for path in sys.argv[1:]:
    lv = [np.asarray(Image.open(path).convert("RGB")).astype(np.float64)]
    while min(lv[-1].shape[:2]) > 1:
        x = lv[-1]
        lv.append((x[0::2, 0::2] + x[1::2, 0::2] + x[0::2, 1::2] + x[1::2, 1::2]) / 4)
    lv = [np.clip(np.rint(x), 0, 255).astype(np.uint8) for x in lv]
    full, chain, dev = size(lv[0], "JPEG"), sum(size(x, "JPEG") for x in lv[1:]), sum(size(x, "JPEG") for x in lv[1:3])
    pfull, pchain = size(lv[0], "PNG"), sum(size(x, "PNG") for x in lv[1:])
    print(f"{path}: JPEG picture {full}, chain {chain} (+{100 * chain / full:.1f} %), "
          f"two device copies {dev} (+{100 * dev / full:.1f} %); PNG picture {pfull}, chain {pchain} (+{100 * pchain / pfull:.1f} %)")
