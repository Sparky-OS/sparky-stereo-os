#!/usr/bin/env python3
"""Pack real left and right pictures into the stereo photo formats, stdlib plus Pillow.

mpo   LEFT.jpg RIGHT.jpg OUT.mpo   two JPEGs and a CIPA DC-007 index (disparity pair, left eye first)
jps   SBS.jpg OUT.jps              side-by-side JPEG, left eye first, VRex 1997 descriptor in APP3
pns   LEFT RIGHT OUT.pns           PNG, left eye first, the registered sTER chunk (mode 1, diverging)

Layouts follow the reader in stereo-layer (src/policy/stereo-jpeg.c): the two-view writer's MPF
index (II, B000/B001/B002 then B000/B101/B204) and the JPS descriptor 0x00040201 (type 1 stereo,
layout 2 side by side, flag bit 18 left eye first).
"""
import struct
import sys
import zlib


def le16(v):
    return struct.pack('<H', v)


def le32(v):
    return struct.pack('<I', v)


def field(tag, typ, count, value):
    return le16(tag) + le16(typ) + le32(count) + le32(value)


def mpf_tiff(entries):
    """entries None: secondary (viewpoint 2) attribute IFD; else index plus attributes (viewpoint 1)."""
    if entries is None:
        t = b'II' + le16(42) + le32(8)
        t += le16(3) + field(0xB000, 7, 4, 0x30303130) + field(0xB101, 4, 1, 2) + field(0xB204, 4, 1, 1) + le32(0)
        return t
    t = b'II' + le16(42) + le32(8)
    t += le16(3) + field(0xB000, 7, 4, 0x30303130) + field(0xB001, 4, 1, 2) + field(0xB002, 7, 32, 92) + le32(50)
    t += le16(3) + field(0xB000, 7, 4, 0x30303130) + field(0xB101, 4, 1, 1) + field(0xB204, 4, 1, 1) + le32(0)
    assert len(t) == 92, len(t)
    for attributes, size, offset in entries:
        t += le32(attributes) + le32(size) + le32(offset) + le16(0) + le16(0)
    return t


def app2(tiff):
    body = b'MPF\x00' + tiff
    return b'\xff\xe2' + struct.pack('>H', len(body) + 2) + body


def split_segments(jpeg):
    """Return (index after the APPn run, whether it is a JFIF/Exif JPEG)."""
    assert jpeg[:2] == b'\xff\xd8'
    pos = 2
    while jpeg[pos] == 0xFF and 0xE0 <= jpeg[pos + 1] <= 0xEF:
        pos += 2 + struct.unpack('>H', jpeg[pos + 2:pos + 4])[0]
    return pos


def jpeg_end(jpeg):
    assert jpeg[-2:] == b'\xff\xd9', 'JPEG must end with EOI and carry no trailer'
    return len(jpeg)


def make_mpo(left, right):
    # app segment sizes do not depend on the entries' values, so build twice
    attr = 0x20020002, 0x00020002
    secondary = app2(mpf_tiff(None))
    ins1 = split_segments(left)
    ins2 = split_segments(right)
    second = right[:ins2] + secondary + right[ins2:]
    first_len = len(left) + len(app2(mpf_tiff([(0, 0, 0)] * 2)))
    # TIFF header sits 4 (marker+length) + 4 ('MPF\0') bytes after the segment start
    seg_start = ins1
    base = seg_start + 4 + 4
    entries = [(attr[0], first_len, 0), (attr[1], len(second), first_len - base)]
    first = left[:ins1] + app2(mpf_tiff(entries)) + left[ins1:]
    assert len(first) == first_len
    return first + second


def make_jps(jpeg, comment=b''):
    descriptor = 0x00040201
    payload = b'_JPSJPS_' + struct.pack('>HI', 4, descriptor) + struct.pack('>H', len(comment)) + comment
    seg = b'\xff\xe3' + struct.pack('>H', len(payload) + 2) + payload
    at = split_segments(jpeg)
    return jpeg[:at] + seg + jpeg[at:]


def png_chunks(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos = 8
    while pos < len(data):
        n, typ = struct.unpack('>I4s', data[pos:pos + 8])
        yield typ, data[pos + 8:pos + 8 + n], data[pos + 8 + n:pos + 12 + n]
        pos += 12 + n


def make_pns(png_bytes, mode=1):
    out = [b'\x89PNG\r\n\x1a\n']
    for typ, body, crc in png_chunks(png_bytes):
        out.append(struct.pack('>I', len(body)) + typ + body + crc)
        if typ == b'IHDR':
            chunk = b'sTER' + bytes([mode])
            out.append(struct.pack('>I', 1) + chunk + struct.pack('>I', zlib.crc32(chunk)))
    return b''.join(out)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'mpo':
        open(sys.argv[4], 'wb').write(make_mpo(open(sys.argv[2], 'rb').read(), open(sys.argv[3], 'rb').read()))
    elif cmd == 'jps':
        open(sys.argv[3], 'wb').write(make_jps(open(sys.argv[2], 'rb').read()))
    elif cmd == 'pns':
        open(sys.argv[3], 'wb').write(make_pns(open(sys.argv[2], 'rb').read()))
    else:
        sys.exit('mpo | jps | pns')
