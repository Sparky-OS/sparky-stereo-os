#!/usr/bin/env python3
"""Two views as one full side by side PNG, left eye first, marked with the PNG sTER chunk (mode 1, the diverging
layout: the left eye's picture on the left; PNG Extensions 1.4.0, 3.6), named .pns, then read back and checked.
m3_pns.py LEFT.png RIGHT.png OUT.pns"""
import struct, sys, zlib
from PIL import Image
l, r, out = sys.argv[1:4]
a, b = Image.open(l).convert('RGB'), Image.open(r).convert('RGB')
assert a.size == b.size, 'the two views differ in size'
w, h = a.size
s = Image.new('RGB', (2 * w, h)); s.paste(a, (0, 0)); s.paste(b, (w, 0))
s.save(out, 'PNG')
data = open(out, 'rb').read()
chunk = b'sTER' + bytes([1])
ster = struct.pack('>I', 1) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
i = data.index(b'IDAT') - 4          # sTER goes before the first IDAT
data = data[:i] + ster + data[i:]
open(out, 'wb').write(data)
# read back: walk the chunks, check sTER's place, value and CRC
p, seen = 8, []
while p < len(data):
    n = struct.unpack('>I', data[p:p + 4])[0]
    typ = data[p + 4:p + 8]
    body = data[p + 8:p + 8 + n]
    crc = struct.unpack('>I', data[p + 8 + n:p + 12 + n])[0]
    assert crc == zlib.crc32(typ + body) & 0xffffffff, 'bad CRC in %s' % typ
    seen.append((typ.decode(), body))
    p += 12 + n
names = [t for t, _ in seen]
assert 'sTER' in names and names.index('sTER') < names.index('IDAT') and dict(seen)['sTER'] == bytes([1]), names
w2, h2 = struct.unpack('>II', dict(seen)['IHDR'][:8])
print('%s: %dx%d, sTER mode 1 before IDAT, every CRC right' % (out, w2, h2))
