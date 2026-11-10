#!/usr/bin/env python3
"""Write and check a stereo PNG: full side by side, left eye first, marked with the sTER chunk.

PNG extensions 1.4.0, section 3.6: sTER holds one byte, 1 for the left eye's picture on the left;
it stands before the first IDAT; the right picture starts on a column divisible by eight, so the
left one is followed by padding = 7 - ((width - 1) mod 8) columns.
Pillow drops the chunk, so it is inserted into the finished file and the file is read back.

Usage: pns.py FILE.pns [FILE.pns ...]   checks each file and prints what it found; exit 1 on any fault
"""
import io
import struct
import sys
import zlib

import numpy as np
from PIL import Image


def write(path, left, right):
    """left, right: uint8 arrays (H, W, 3) of the same shape."""
    assert left.shape == right.shape and left.dtype == np.uint8
    h, w = left.shape[:2]
    pad = 7 - ((w - 1) % 8)
    both = np.concatenate([left, np.zeros((h, pad, 3), np.uint8), right], 1)
    raw = io.BytesIO()
    Image.fromarray(both).save(raw, "PNG")
    d = raw.getvalue()
    assert d[12:16] == b"IHDR"
    chunk = b"sTER" + b"\x01"
    ster = struct.pack(">I", 1) + chunk + struct.pack(">I", zlib.crc32(chunk))
    open(path, "wb").write(d[:33] + ster + d[33:])
    found = check(path)
    assert found["eye"] == (w, h), found
    return found


def check(path):
    d = open(path, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(path + ": not a PNG")
    i, names, mode = 8, [], None
    while i < len(d):
        n, t = struct.unpack(">I4s", d[i:i + 8])
        body = d[i + 8:i + 8 + n]
        if struct.unpack(">I", d[i + 8 + n:i + 12 + n])[0] != zlib.crc32(t + body):
            raise ValueError("%s: bad CRC in %s" % (path, t.decode()))
        if t == b"sTER":
            if n != 1 or b"IDAT" in names:
                raise ValueError(path + ": sTER has the wrong length or stands after IDAT")
            mode = body[0]
        names.append(t)
        i += 12 + n
    if names[0] != b"IHDR" or names[-1] != b"IEND" or mode is None:
        raise ValueError(path + ": chunk order or missing sTER: " + " ".join(x.decode() for x in names[:4]))
    if mode != 1:
        raise ValueError(path + ": sTER mode %d, not 1 (left eye on the left)" % mode)
    im = Image.open(path)
    im.load()
    W, H = im.size
    pad = 15 - ((W - 1) % 16)
    if pad > 7 or (W - pad) % 2:
        raise ValueError("%s: width %d does not hold two views with the specified padding" % (path, W))
    return {"eye": ((W - pad) // 2, H), "padding": pad, "mode": mode}


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        try:
            print(p, check(p))
        except Exception as e:
            print("FAULT", e)
            bad = 1
    sys.exit(bad)
