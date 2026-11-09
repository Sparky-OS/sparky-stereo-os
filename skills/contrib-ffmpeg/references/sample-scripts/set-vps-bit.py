#!/usr/bin/env python3
# ORDER 174. Sets one bit of the RBSP of every VPS NAL unit of an Annex B HEVC stream (the bit counted
# from the first bit after the two byte NAL unit header, emulation prevention bytes removed) and writes
# the stream again with the bytes escaped.
#
#   set-vps-bit.py IN.hevc OUT.hevc BIT VALUE
import sys


def split(data):
    pos, out, i = [], [], 0
    while True:
        i = data.find(b'\x00\x00\x01', i)
        if i < 0:
            break
        pos.append(i + 3)
        i += 3
    for k, s in enumerate(pos):
        e = pos[k + 1] - 3 if k + 1 < len(pos) else len(data)
        while e > s and data[e - 1] == 0:
            e -= 1
        out.append(data[s:e])
    return out


def unescape(nal):
    out, zeros = bytearray(), 0
    for c in nal:
        if zeros >= 2 and c == 3:
            zeros = 0
            continue
        out.append(c)
        zeros = zeros + 1 if c == 0 else 0
    return bytearray(out)


def escape(rbsp):
    out, zeros = bytearray(), 0
    for c in rbsp:
        if zeros >= 2 and c <= 3:
            out.append(3)
            zeros = 0
        out.append(c)
        zeros = zeros + 1 if c == 0 else 0
    return bytes(out)


def main():
    src, dst, bit, value = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    out, n = bytearray(), 0
    for nal in split(open(src, 'rb').read()):
        if (nal[0] >> 1) & 0x3f == 32:
            rbsp = unescape(nal[2:])
            mask = 0x80 >> (bit % 8)
            rbsp[bit // 8] = (rbsp[bit // 8] & ~mask & 0xff) | (mask if value else 0)
            nal = nal[:2] + escape(rbsp)
            n += 1
        out += b'\x00\x00\x00\x01' + nal
    open(dst, 'wb').write(out)
    print('%s: bit %d of %d VPS set to %d' % (dst, bit, n, value))


main()
