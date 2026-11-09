#!/usr/bin/env python3
# ORDER 174. Adds a prefix SEI NAL unit array to the hvcC box of an MP4 file written by
# `ffmpeg -c copy` from a raw HEVC stream (mdat before moov, so no chunk offset moves): the box
# grows, and so do the boxes that contain it. The SEI NAL unit is the first prefix SEI NAL unit
# (nal_unit_type 39) of the stream the file was made from.
#
#   add-hvcc-sei.py STREAM.hevc IN.mp4 OUT.mp4
import struct
import sys

CONTAINERS = {b'moov', b'trak', b'mdia', b'minf', b'stbl', b'stsd', b'hvc1', b'hev1'}


def first_prefix_sei(path):
    d = open(path, 'rb').read()
    pos, i = [], 0
    while True:
        i = d.find(b'\x00\x00\x01', i)
        if i < 0:
            break
        pos.append(i + 3)
        i += 3
    for k, s in enumerate(pos):
        e = pos[k + 1] - 3 if k + 1 < len(pos) else len(d)
        while e > s and d[e - 1] == 0:
            e -= 1
        if (d[s] >> 1) & 0x3f == 39:
            return d[s:e]
    raise SystemExit('no prefix SEI')


def parse(data, start, end, path, found):
    """yields (offset, size, type, path) for every box, recursing into the containers"""
    pos = start
    while pos < end:
        size, typ = struct.unpack('>I4s', data[pos:pos + 8])
        hdr = 8
        if size == 1:
            size = struct.unpack('>Q', data[pos + 8:pos + 16])[0]
            hdr = 16
        assert size >= hdr
        found.append((pos, size, typ, list(path)))
        if typ in CONTAINERS:
            skip = hdr
            if typ == b'stsd':
                skip += 8                      # version, flags, entry count
            elif typ in (b'hvc1', b'hev1'):
                skip += 78                     # the VisualSampleEntry fields
            parse(data, pos + skip, pos + size, path + [(pos, typ)], found)
        pos += size


def main():
    stream, src, dst = sys.argv[1:4]
    sei = first_prefix_sei(stream)
    data = bytearray(open(src, 'rb').read())
    boxes = []
    parse(data, 0, len(data), [], boxes)
    hvcc = [b for b in boxes if b[2] == b'hvcC'][0]
    pos, size, _, anc = hvcc
    array = struct.pack('>BHH', 39, 1, len(sei)) + sei      # array_completeness 0, NAL_unit_type 39
    # numOfArrays is the byte at offset 22 of the record, 8 bytes after the box header
    n_off = pos + 8 + 22
    data[n_off] += 1
    data[pos + size:pos + size] = array
    for off, typ in anc + [(pos, b'hvcC')]:
        (old,) = struct.unpack('>I', data[off:off + 4])
        data[off:off + 4] = struct.pack('>I', old + len(array))
    open(dst, 'wb').write(data)


main()
