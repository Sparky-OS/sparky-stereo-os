#!/usr/bin/env python3
"""Read DocType, track codecs, PixelWidth/Height, DisplayWidth/Height and StereoMode from a Matroska or WebM file.

Walks the EBML tree with the element IDs of RFC 8794 and RFC 9559 (stdlib only, run with python3 -I).
StereoMode is Video\\StereoMode (0x53B8): 0 mono, 1 side by side left first, 2 top bottom right first,
3 top bottom left first, ...; WebM allows 0 to 3.
"""
import sys

MASTER = {0x18538067: 'Segment', 0x1654AE6B: 'Tracks', 0xAE: 'TrackEntry', 0xE0: 'Video', 0x1A45DFA3: 'EBML'}
IDS = {0x4282: 'DocType', 0x4287: 'DocTypeVersion', 0x86: 'CodecID', 0xD7: 'TrackNumber', 0x83: 'TrackType',
       0xB0: 'PixelWidth', 0xBA: 'PixelHeight', 0x54B0: 'DisplayWidth', 0x54BA: 'DisplayHeight',
       0x53B8: 'StereoMode', 0x54B2: 'DisplayUnit', 0x9A: 'FlagInterlaced'}


def vint(buf, pos, keep_marker):
    first = buf[pos]
    n = 1
    while n <= 8 and not first & (0x80 >> (n - 1)):
        n += 1
    val = first if keep_marker else first & (0xFF >> n)
    for b in buf[pos + 1:pos + n]:
        val = val << 8 | b
    return val, n


def walk(buf, pos, end, out, path=''):
    while pos < end:
        eid, n1 = vint(buf, pos, True)
        size, n2 = vint(buf, pos + n1, False)
        body = pos + n1 + n2
        if size == (1 << (7 * n2)) - 1:
            size = end - body
        if eid in MASTER:
            walk(buf, body, min(body + size, end), out, path + '/' + MASTER[eid])
        elif eid in IDS:
            raw = bytes(buf[body:body + size])
            out.append((path, IDS[eid], raw.decode() if IDS[eid] in ('DocType', 'CodecID') else int.from_bytes(raw, 'big')))
        elif eid == 0x1F43B675:   # Cluster: stop, tracks are before it
            return
        pos = body + size


if __name__ == '__main__':
    data = open(sys.argv[1], 'rb').read(1 << 20)
    rows = []
    walk(data, 0, len(data), rows)
    for p, k, v in rows:
        print('%-32s %-14s %s' % (p, k, v))
