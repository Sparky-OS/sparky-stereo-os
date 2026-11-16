#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""make_pns.py IN.png OUT.pns [--crop X0,Y0,X1,Y1 (applied to each eye)] | --check FILE.pns
Writes a full side by side stereo capture (left eye first, twice the output's width) as a PNG with the sTER chunk
(PNG Extensions 1.4.0, 3.6: one byte, 1 = divergent layout, left eye on the left) placed before IDAT, and reads it back."""
import struct, sys, zlib, io
from PIL import Image

def chunks(data):
    i = 8
    while i < len(data):
        n, = struct.unpack(">I", data[i:i + 4]); t = data[i + 4:i + 8]
        yield t, data[i + 8:i + 8 + n]
        i += 12 + n

def check(path):
    d = open(path, "rb").read()
    assert d[:8] == b"\x89PNG\r\n\x1a\n"
    names = [t for t, _ in chunks(d)]
    ster = dict(chunks(d)).get(b"sTER")
    ok = ster == b"\x01" and names.index(b"sTER") < names.index(b"IDAT")
    w, h = Image.open(path).size
    print(path, "sTER" if ster is not None else "NO sTER", "mode", ster[0] if ster else None, "before IDAT" if ok else "BAD ORDER/MODE", f"{w}x{h}", "width%16", w % 16)
    return ok and w % 16 == 0

if sys.argv[1] == "--check":
    sys.exit(0 if all(check(p) for p in sys.argv[2:]) else 1)
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
W, H = im.size
assert W % 2 == 0
if "--crop" in sys.argv:
    x0, y0, x1, y1 = map(int, sys.argv[sys.argv.index("--crop") + 1].split(","))
    h = W // 2
    left = im.crop((x0, y0, x1, y1)); right = im.crop((h + x0, y0, h + x1, y1))
    out = Image.new("RGB", (2 * (x1 - x0), y1 - y0)); out.paste(left, (0, 0)); out.paste(right, (x1 - x0, 0)); im = out
buf = io.BytesIO(); im.save(buf, "PNG"); data = buf.getvalue()
res = bytearray(data[:8])
for t, c in chunks(data):
    if t == b"IDAT" and b"sTER" not in res:
        body = b"sTER" + b"\x01"; res += struct.pack(">I", 1) + body + struct.pack(">I", zlib.crc32(body))
    body = t + c; res += struct.pack(">I", len(c)) + body + struct.pack(">I", zlib.crc32(body))
open(dst, "wb").write(res)
sys.exit(0 if check(dst) else 1)
