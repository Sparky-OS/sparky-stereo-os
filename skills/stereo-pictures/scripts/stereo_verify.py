#!/usr/bin/env python3
"""Read stereo marks back with parsers that can fail (stdlib plus Pillow, run with python3 -I).

mpo FILE        every rule of the two-view MPO the layer's reader applies, then decode both JPEGs
jps FILE        the APP3 _JPSJPS_ block, descriptor fields, one marker only
pns FILE        chunk order, every CRC, the sTER mode byte, IHDR width a multiple of 16, decodes
Prints one line per check and exits 1 on the first failure.
"""
import io
import struct
import sys
import zlib

from PIL import Image


def fail(msg):
    print('FAIL', msg)
    sys.exit(1)


def ok(msg):
    print('ok  ', msg)


def jpeg_segments(data, start=0):
    """Yield (marker, offset, length-with-marker) until SOS; return end offset of the image (after EOI)."""
    assert data[start:start + 2] == b'\xff\xd8', 'no SOI at %d' % start
    pos = start + 2
    segs = []
    while True:
        assert data[pos] == 0xFF, 'marker expected at %d' % pos
        m = data[pos + 1]
        if m == 0xDA:
            segs.append((m, pos, 0))
            break
        n = struct.unpack('>H', data[pos + 2:pos + 4])[0]
        segs.append((m, pos, n + 2))
        pos += n + 2
    # scan data: find EOI (FFD9) not preceded by stuffing/RST
    pos = segs[-1][1] + 2 + struct.unpack('>H', data[segs[-1][1] + 2:segs[-1][1] + 4])[0]
    while True:
        i = data.index(b'\xff', pos)
        nxt = data[i + 1]
        if nxt == 0xD9:
            return segs, i + 2
        pos = i + 2


def u16(d, o, le):
    return struct.unpack('<H' if le else '>H', d[o:o + 2])[0]


def u32(d, o, le):
    return struct.unpack('<I' if le else '>I', d[o:o + 4])[0]


def ifd_fields(t, ifd, le):
    n = u16(t, ifd, le)
    out = {}
    for i in range(n):
        o = ifd + 2 + 12 * i
        tag, typ, cnt = u16(t, o, le), u16(t, o + 2, le), u32(t, o + 4, le)
        if tag in out:
            fail('duplicate tag %04X' % tag)
        out[tag] = (typ, cnt, u32(t, o + 8, le))
    return out, u32(t, ifd + 2 + 12 * n, le)


def mpf_of(data, seg_start_end):
    segs, _ = seg_start_end
    found = [s for s in segs if s[0] == 0xE2 and data[s[1] + 4:s[1] + 8] == b'MPF\x00']
    if len(found) != 1:
        fail('expected exactly one MPF APP2, found %d' % len(found))
    m, pos, n = found[0]
    return pos + 8, data[pos + 8:pos + n]


def verify_mpo(path):
    d = open(path, 'rb').read()
    first = jpeg_segments(d, 0)
    segs, end1 = first
    base, t = mpf_of(d, first)
    le = {b'II': True, b'MM': False}[t[:2]]
    if u16(t, 2, le) != 42:
        fail('bad TIFF magic')
    ifd = u32(t, 4, le)
    idx, nxt = ifd_fields(t, ifd, le)
    for tag, typ, cnt in ((0xB000, 7, 4), (0xB001, 4, 1), (0xB002, 7, 32)):
        if tag not in idx or idx[tag][:2] != (typ, cnt):
            fail('index IFD lacks %04X type %d count %d' % (tag, typ, cnt))
    if t[ifd + 2 + 8:ifd + 2 + 12] != b'0100':
        fail('MPFVersion not 0100')
    if idx[0xB001][2] != 2:
        fail('NumberOfImages != 2')
    ok('MPF index: version 0100, two images, byte order %s' % ('II' if le else 'MM'))
    ent = idx[0xB002][2]
    e = [(u32(t, ent + 16 * i, le), u32(t, ent + 16 * i + 4, le), u32(t, ent + 16 * i + 8, le)) for i in range(2)]
    for i, (a, s, o) in enumerate(e):
        if a & 0x07FFFFFF != 0x020002:
            fail('entry %d type code %06X is not disparity 020002' % (i, a & 0x07FFFFFF))
        if (a >> 24) & 7 != 0:
            fail('entry %d data format is not JPEG' % i)
    ok('both MP entries are type 0x020002 (Disparity, stereoscopic), JPEG data format')
    if e[0][2] != 0 or e[0][1] != end1:
        fail('first entry offset/size %d/%d, first image ends at %d' % (e[0][2], e[0][1], end1))
    start = base + e[1][2]
    if start < end1 or d[start:start + 2] != b'\xff\xd8' or e[1][1] != len(d) - start:
        fail('second entry does not point at the second image (start %d size %d file %d)' % (start, e[1][1], len(d)))
    ok('entry 0: offset 0 size %d = first image length; entry 1: offset %d (from the MPF header) size %d = rest of file' % (e[0][1], e[1][2], e[1][1]))
    # attribute IFDs
    attrs = {}
    while nxt:
        a, nxt = ifd_fields(t, nxt, le)
        attrs.update(a)
    b101a, b204a = attrs[0xB101][2], attrs[0xB204][2]
    second = jpeg_segments(d, start)
    base2, t2 = mpf_of(d, second)
    le2 = {b'II': True, b'MM': False}[t2[:2]]
    a2, n2 = ifd_fields(t2, u32(t2, 4, le2), le2)
    if 0xB001 in a2:
        fail('second image carries an index IFD')
    b101b, b204b = a2[0xB101][2], a2[0xB204][2]
    if sorted((b101a, b101b)) != [1, 2] or b204a != b204b or b204a not in (1, 2):
        fail('viewpoint numbers %s %s base %s %s' % (b101a, b101b, b204a, b204b))
    ok('MPIndividualNum (B101): first image %d, second image %d; BaseViewpointNum (B204) %d in both' % (b101a, b101b, b204a))
    with Image.open(path) as mpo:
        if mpo.format != 'MPO' or mpo.n_frames != 2:
            fail('Pillow reads %s with %s frames' % (mpo.format, getattr(mpo, 'n_frames', 1)))
        im1 = mpo.convert('RGB')
        mpo.seek(1)
        im2 = mpo.convert('RGB')
    ok("Pillow's MPO reader: 2 frames, %dx%d and %dx%d" % (im1.size + im2.size))
    return b101a == 1, im1, im2


def verify_jps(path):
    d = open(path, 'rb').read()
    segs, end = jpeg_segments(d, 0)
    if end != len(d):
        fail('bytes after EOI')
    jps = [s for s in segs if s[0] == 0xE3 and d[s[1] + 4:s[1] + 12] == b'_JPSJPS_']
    if len(jps) != 1:
        fail('expected one _JPSJPS_ APP3, found %d' % len(jps))
    p = d[jps[0][1] + 4:jps[0][1] + jps[0][2]]
    ln = struct.unpack('>H', p[8:10])[0]
    desc = struct.unpack('>I', p[10:14])[0]
    cl = struct.unpack('>H', p[10 + ln:12 + ln])[0]
    if ln != 4 or 12 + ln + cl != len(p):
        fail('descriptor/comment lengths inconsistent (%d, %d, payload %d)' % (ln, cl, len(p)))
    typ, layout, flags, gap = desc & 255, (desc >> 8) & 255, (desc >> 16) & 255, desc >> 24
    names = {1: 'rows', 2: 'side by side', 3: 'top and bottom', 4: 'anaglyph'}
    if typ != 1 or layout not in (2, 3) or flags & ~7:
        fail('descriptor %08X not a plain stereo side-by-side or top-bottom' % desc)
    ok('JPS descriptor 0x%08X: type %d stereo, layout %d %s, half height %d, half width %d, %s eye first, separation %d, comment %d bytes' % (
        desc, typ, layout, names[layout], flags & 1, (flags >> 1) & 1, 'left' if flags & 4 else 'right', gap, cl))
    im = Image.open(io.BytesIO(d)); im.load()
    ok('JPEG decodes: %dx%d' % im.size)
    return bool(flags & 4), im


def verify_pns(path):
    d = open(path, 'rb').read()
    if d[:8] != b'\x89PNG\r\n\x1a\n':
        fail('not a PNG')
    pos, order, mode, width = 8, [], None, None
    while pos < len(d):
        n, typ = struct.unpack('>I4s', d[pos:pos + 8])
        body, crc = d[pos + 8:pos + 8 + n], struct.unpack('>I', d[pos + 8 + n:pos + 12 + n])[0]
        if zlib.crc32(typ + body) != crc:
            fail('CRC of %r' % typ)
        order.append(typ.decode())
        if typ == b'IHDR':
            width = struct.unpack('>I', body[:4])[0]
        if typ == b'sTER':
            if n != 1:
                fail('sTER length %d' % n)
            mode = body[0]
        pos += 12 + n
    if order[0] != 'IHDR' or order[-1] != 'IEND':
        fail('chunk order %s' % order)
    if 'sTER' not in order or order.index('sTER') > order.index('IDAT'):
        fail('sTER missing or after IDAT: %s' % order)
    if order.count('sTER') != 1:
        fail('more than one sTER')
    ok('chunks %s, every CRC valid' % ' '.join(order))
    ok('sTER mode byte %d (%s), IHDR width %d, divisible by 16: %s' % (
        mode, 'diverging, left eye on the left' if mode == 1 else 'cross-fuse, right eye on the left', width, width % 16 == 0))
    if mode not in (0, 1) or width % 16:
        fail('mode or width invalid')
    im = Image.open(io.BytesIO(d)); im.load()
    ok('PNG decodes: %dx%d mode %s' % (im.size + (im.mode,)))
    return mode == 1, im


if __name__ == '__main__':
    {'mpo': verify_mpo, 'jps': verify_jps, 'pns': verify_pns}[sys.argv[1]](sys.argv[2])
