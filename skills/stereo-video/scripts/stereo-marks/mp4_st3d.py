#!/usr/bin/env python3
"""Insert a Spherical Video V2 'st3d' box into the first video sample entry of an MP4 (stdlib only).

st3d (Spherical Video V2 RFC, section 'Stereoscopic 3D Video Box'): FullBox, version 0, flags 0,
one byte stereo_mode: 0 mono, 1 top-bottom (left eye on top), 2 left-right (left eye on the left),
3 stereo-custom, 4 right-left.  The box goes after the entry's codec configuration box and before the optional
clap and pasp boxes, as the RFC (google/spatial-media, docs/spherical-video-v2-rfc.md, st3d) asks.  Usage: mp4_st3d.py IN.mp4 OUT.mp4 MODE
The parents' sizes grow by the box size; when moov comes before mdat every stco/co64 entry is
shifted by the same amount.  `verify` mode parses a file with a second walker and prints the mark.
"""
import struct
import sys

CONTAINERS = {b'moov', b'trak', b'mdia', b'minf', b'stbl', b'edts', b'dinf'}


def boxes(buf, start, end):
    pos = start
    while pos + 8 <= end:
        size, typ = struct.unpack('>I4s', buf[pos:pos + 8])
        hdr = 8
        if size == 1:
            size = struct.unpack('>Q', buf[pos + 8:pos + 16])[0]
            hdr = 16
        elif size == 0:
            size = end - pos
        if size < hdr or pos + size > end:
            raise ValueError('bad box %r at %d size %d' % (typ, pos, size))
        yield pos, size, hdr, typ
        pos += size


def find_video_entry(buf):
    """Return (path of (pos,size,hdr) from moov down to the video sample entry, entry type)."""
    for p, s, h, t in boxes(buf, 0, len(buf)):
        if t != b'moov':
            continue
        for tp, ts, th, tt in boxes(buf, p + h, p + s):
            if tt != b'trak':
                continue
            for mp, ms, mh, mt in boxes(buf, tp + th, tp + ts):
                if mt != b'mdia':
                    continue
                kind = None
                for xp, xs, xh, xt in boxes(buf, mp + mh, mp + ms):
                    if xt == b'hdlr':
                        kind = buf[xp + xh + 8:xp + xh + 12]
                    if xt == b'minf' and kind == b'vide':
                        for bp, bs, bh, bt in boxes(buf, xp + xh, xp + xs):
                            if bt != b'stbl':
                                continue
                            for sp, ss, sh, st in boxes(buf, bp + bh, bp + bs):
                                if st != b'stsd':
                                    continue
                                ep = sp + sh + 8
                                esz, etyp = struct.unpack('>I4s', buf[ep:ep + 8])
                                return [(p, s, h), (tp, ts, th), (mp, ms, mh), (xp, xs, xh),
                                        (bp, bs, bh), (sp, ss, sh), (ep, esz, 8)], etyp
    raise ValueError('no video sample entry')


def entry_children_start(buf, ep, etyp):
    # VisualSampleEntry: 8 box header + 6 reserved + 2 dref + 70 bytes of fields = 86
    return ep + 86


def insert(inp, out, mode):
    buf = bytearray(open(inp, 'rb').read())
    path, etyp = find_video_entry(buf)
    ep, esz, eh = path[-1]
    for c in boxes(buf, entry_children_start(buf, ep, etyp), ep + esz):
        if c[3] == b'st3d':
            raise ValueError('st3d already present')
    box = struct.pack('>I4sIB', 13, b'st3d', 0, mode)
    moov_pos = path[0][0]
    mdat_pos = next(p for p, s, h, t in boxes(buf, 0, len(buf)) if t == b'mdat')
    insert_at = ep + esz
    for c in boxes(buf, entry_children_start(buf, ep, etyp), ep + esz):
        if c[3] in (b'clap', b'pasp'):
            insert_at = c[0]
            break
    buf[insert_at:insert_at] = box
    for pos, size, hdr in path:
        struct.pack_into('>I', buf, pos, size + len(box))
    if moov_pos < mdat_pos:
        moov_size = path[0][1] + len(box)
        shift_offsets(buf, moov_pos + 8, moov_pos + moov_size, len(box))
    open(out, 'wb').write(buf)


def shift_offsets(buf, start, end, delta):
    for p, s, h, t in boxes(buf, start, end):
        if t in CONTAINERS:
            shift_offsets(buf, p + h, p + s, delta)
        elif t == b'stco':
            n = struct.unpack('>I', buf[p + h + 4:p + h + 8])[0]
            for i in range(n):
                o = p + h + 8 + 4 * i
                struct.pack_into('>I', buf, o, struct.unpack('>I', buf[o:o + 4])[0] + delta)
        elif t == b'co64':
            n = struct.unpack('>I', buf[p + h + 4:p + h + 8])[0]
            for i in range(n):
                o = p + h + 8 + 8 * i
                struct.pack_into('>Q', buf, o, struct.unpack('>Q', buf[o:o + 8])[0] + delta)


def verify(path):
    buf = open(path, 'rb').read()
    p, etyp = find_video_entry(buf)
    ep, esz, _ = p[-1]
    found = []
    for c in boxes(buf, entry_children_start(buf, ep, etyp), ep + esz):
        if c[3] == b'st3d':
            ver_flags, mode = struct.unpack('>IB', buf[c[0] + 8:c[0] + 13])
            found.append((c[1], ver_flags, mode))
    order = [c[3].decode() for c in boxes(buf, entry_children_start(buf, ep, etyp), ep + esz)]
    return etyp, found, order


if __name__ == '__main__':
    if sys.argv[1] == 'verify':
        print(verify(sys.argv[2]))
    else:
        insert(sys.argv[1], sys.argv[2], int(sys.argv[3]))
