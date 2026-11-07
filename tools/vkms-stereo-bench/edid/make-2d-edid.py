#!/usr/bin/env python3
# make-2d-edid.py IN.bin OUT.bin: the same EDID with the HDMI Vendor-Specific Data Block's 3D fields removed (a 2D-only HDMI sink).
import sys
d = bytearray(open(sys.argv[1], "rb").read())
b = d[128:256]
dtd = b[2]
i = 4
out = bytearray()
while i < dtd:
    tag, n = b[i] >> 5, b[i] & 31
    blk = b[i:i+1+n]
    if tag == 3 and blk[1:4] == bytes([3, 12, 0]):
        # header, OUI, phys addr (2), flags, max tmds -> keep 8 bytes, no HDMI_Video_present, no 3D
        blk = bytearray(blk[:8]); blk[0] = (3 << 5) | 7
    out += blk
    i += 1 + n
nb = bytearray(128)
nb[0:4] = b[0:4]
nb[4:4+len(out)] = out
nb[2] = 4 + len(out)
rest = b[dtd:]
# copy detailed timings that follow
j = 0
pos = nb[2]
while j + 18 <= len(rest) and rest[j] | rest[j+1]:
    nb[pos:pos+18] = rest[j:j+18]; pos += 18; j += 18
nb[3] = b[3] & 0xf0 | 0
nb[127] = (256 - sum(nb[:127]) % 256) % 256
d[128:256] = nb
open(sys.argv[2], "wb").write(d)
