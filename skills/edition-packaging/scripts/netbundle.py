#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""List the files of a .NET single-file bundle and print one of them (deflate-decompressed when needed).
Usage: netbundle.py BUNDLE [PATH_TO_PRINT]   (format: dotnet/runtime src/installer/managed/Microsoft.NET.HostModel/Bundle)"""
import struct
import sys
import zlib

SIG = bytes.fromhex('8b1202b96a612038727b930214d7a03213f5b9e6efae3318ee3b2dce24b36aae')
data = open(sys.argv[1], 'rb').read()
i = data.find(SIG)
assert i > 8, 'no bundle signature'
(hdr,) = struct.unpack_from('<q', data, i - 8)
p = hdr


def string(p):
    n = shift = 0
    while True:
        b = data[p]
        p += 1
        n |= (b & 0x7f) << shift
        shift += 7
        if not b & 0x80:
            break
    return data[p:p + n].decode('utf-8'), p + n


major, minor, count = struct.unpack_from('<IIi', data, p)
p += 12
bundle_id, p = string(p)
if major >= 2:
    p += 8 * 4 + 8  # deps.json and runtimeconfig.json locations, flags
entries = []
for _ in range(count):
    off, size = struct.unpack_from('<qq', data, p)
    p += 16
    csize = 0
    if major >= 6:
        (csize,) = struct.unpack_from('<q', data, p)
        p += 8
    kind = data[p]
    p += 1
    path, p = string(p)
    entries.append((path, off, size, csize, kind))
want = sys.argv[2] if len(sys.argv) > 2 else None
for path, off, size, csize, kind in entries:
    if want is None:
        print(f'{size:>10} {csize:>10} {kind} {path}')
    elif path == want:
        raw = data[off:off + (csize or size)]
        sys.stdout.buffer.write(zlib.decompress(raw, -15) if csize else raw)
if want is None:
    print(f'# bundle {major}.{minor}, {count} files, id {bundle_id}', file=sys.stderr)
