#!/usr/bin/env python3
# Created by Daniel Ramos (Capitain Jack) 2026/11/26. Copyright 2026 under the GNU GPL3 License.
"""edid-extract.py SOURCE_TEXT OUT_BIN: the EDID a public record quotes, as the kernel reads it.

The record is an edid-decode output ("edid-decode (hex):" then rows of hex), an xrandr --props block, or a plain hex
dump. The base block says how many extension blocks follow (byte 126, VESA E-EDID Release A2, 3.10.2 Table 3.1 and 3.11);
the kernel reads that many and no more (drivers/gpu/drm/drm_edid.c, _drm_do_get_edid), so trailing blocks a probe tool
dumped beyond them are dropped and said. Every kept block must pass its checksum (E-EDID 3.11: the 128 bytes sum to 0
modulo 256). Prints one line: the identity (PnP ID, product code, name) and every detailed timing of the kept blocks.
"""
import re
import sys


def blocks_from(text):
    if 'edid-decode (hex):' in text:
        text = text.split('edid-decode (hex):', 1)[1].split('----------------', 1)[0]
    hexes = re.findall(r'\b[0-9a-fA-F]{2}\b', text)
    data = bytes(int(h, 16) for h in hexes)
    if len(data) < 128 or len(data) % 128:
        raise SystemExit(f'not whole 128-byte blocks: {len(data)} bytes')
    return data


def identity(b):
    word = (b[8] << 8) | b[9]
    pnp = ''.join(chr(0x40 + ((word >> s) & 0x1F)) for s in (10, 5, 0))
    product = b[10] | (b[11] << 8)
    name = None
    timings = []
    for block in range(0, len(b), 128):
        if block == 0:
            offsets = range(54, 126, 18)
        elif b[block] == 0x02:
            d = b[block + 2]
            offsets = range(block + d, block + 127 - 17, 18) if d >= 4 else ()
        else:
            offsets = ()
        for off in offsets:
            d = b[off:off + 18]
            clock = d[0] | (d[1] << 8)
            if clock:
                ha = d[2] | ((d[4] >> 4) << 8)
                hb = d[3] | ((d[4] & 0x0F) << 8)
                va = d[5] | ((d[7] >> 4) << 8)
                vb = d[6] | ((d[7] & 0x0F) << 8)
                timings.append(f'{ha}x{va}@{clock * 10000 / ((ha + hb) * (va + vb)):.3f}')
            elif block == 0 and d[3] == 0xFC:
                name = d[5:18].split(b'\n')[0].decode('ascii', 'replace').strip()
    return pnp, product, name, timings


def main():
    src, out = sys.argv[1], sys.argv[2]
    data = blocks_from(open(src, encoding='utf-8', errors='replace').read())
    count = 1 + data[126]
    kept = data[:128 * count]
    note = ''
    if len(kept) < 128 * count:
        raise SystemExit(f'the base block names {count - 1} extensions, the record has {len(data) // 128 - 1}')
    if len(data) > len(kept):
        note = f' (record had {len(data) // 128} blocks, the base block declares {count}: the rest dropped)'
    for i in range(0, len(kept), 128):
        if sum(kept[i:i + 128]) % 256:
            raise SystemExit(f'block {i // 128} fails its checksum')
    open(out, 'wb').write(kept)
    pnp, product, name, timings = identity(kept)
    print(f'{out}\t{pnp}\t0x{product:04x}\t{name!r}\t{len(kept)} bytes\t{" ".join(timings)}{note}')


if __name__ == '__main__':
    main()
