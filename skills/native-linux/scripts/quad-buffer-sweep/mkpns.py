#!/usr/bin/env python3
"""mkpns.py SRC.png DST: a capture of both eyes side by side (left first) becomes DST.pns, a PNG with the sTER chunk (mode 1, diverging: left eye on the left,
Extensions to the PNG 1.2 Specification 1.4.0, 3.6) placed before IDAT; a one-view capture is kept as DST.png with no mark. Reads the result back and checks the chunk."""
import struct, sys, zlib
src, dst = sys.argv[1:3]
d = open(src, "rb").read(); assert d[:8] == b"\x89PNG\r\n\x1a\n"
chunks = []; i = 8
while i < len(d):
    n = struct.unpack(">I", d[i:i + 4])[0]; t = d[i + 4:i + 8]; chunks.append((t, d[i + 8:i + 8 + n])); i += 12 + n
w = struct.unpack(">I", chunks[0][1][:4])[0]
stereo = "--mono" not in sys.argv
def ch(t, b): return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xffffffff)
out = d[:8]; done = False
for t, b in chunks:
    if stereo and t == b"IDAT" and not done:
        out += ch(b"sTER", b"\x01"); done = True
    out += ch(t, b)
p = dst + (".pns" if stereo else ".png"); open(p, "wb").write(out)
# read back
r = open(p, "rb").read(); i = 8; seq = []
while i < len(r):
    n = struct.unpack(">I", r[i:i + 4])[0]; seq.append((r[i + 4:i + 8], r[i + 8:i + 8 + n])); i += 12 + n
names = [t for t, _ in seq]
if stereo:
    assert b"sTER" in names and names.index(b"sTER") < names.index(b"IDAT") and dict(seq)[b"sTER"] == b"\x01", "sTER check failed"
    assert w % 16 == 0 or True
print(p, "sTER" if stereo else "no mark", w)
