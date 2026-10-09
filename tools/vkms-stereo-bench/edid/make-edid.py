#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""make-edid.py [--sbs-full] OUT.bin [C-ARRAY-NAME]: writes the stereo test EDID (base block + CTA-861
extension with an HDMI 1.4b Vendor-Specific Data Block declaring 3D) and prints it as a C array.
--sbs-full adds a side-by-side (full) entry for VIC 16, a layout mainline DRM does not list.

HDMI VSDB layout (HDMI 1.4b, 8.3.2): OUI 00-0C-03, physical address, flags, Max_TMDS_Clock,
HDMI_Video_present; then 3D_present / 3D_Multi_present, HDMI_VIC_LEN / HDMI_3D_LEN,
3D_Structure_ALL_15..0 (applies to the first 16 VICs when 3D_Multi_present = 01) and
2D_VIC_order_X / 3D_Structure_X entries. Structure codes: 0 frame packing, 3 side-by-side (full),
6 top-and-bottom, 8 side-by-side (half) (bit 8 of 3D_Structure_ALL)."""
import sys

def checksum(block):
    block[127] = (256 - sum(block[:127]) % 256) % 256

def base_block():
    b = bytearray(128)
    b[0:8] = bytes([0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00])
    b[8:10] = bytes([0x31, 0xd8])          # "LNX", as the DRM KUnit EDIDs
    b[10:12] = bytes([0x3d, 0x00])         # product code 61
    b[17] = 0x21                           # made in 2023
    b[18:20] = bytes([0x01, 0x03])         # EDID 1.3
    b[20] = 0x81                           # digital, DFP 1.x
    b[21:23] = bytes([0xa0, 0x5a])         # 160 cm x 90 cm
    b[23] = 0x78                           # gamma 2.2
    b[24] = 0x0a                           # RGB colour, first detailed timing is preferred
    b[35] = 0x20                           # established 640x480@60
    b[38:54] = bytes([0x01, 0x01] * 8)     # no standard timings
    # DTD 1: 1920x1080@60 (CTA VIC 16), 148.5 MHz
    b[54:72] = bytes([0x02, 0x3a, 0x80, 0x18, 0x71, 0x38, 0x2d, 0x40, 0x58, 0x2c,
                      0x45, 0x00, 0x40, 0x84, 0x63, 0x00, 0x00, 0x1e])
    b[72:90] = bytes([0x00, 0x00, 0x00, 0xfc, 0x00]) + b"Stereo EDID\n "
    # range limits: 23-76 Hz V, 15-140 kHz H, 300 MHz, default GTF
    b[90:108] = bytes([0x00, 0x00, 0x00, 0xfd, 0x00, 0x17, 0x4c, 0x0f, 0x8c, 0x1e,
                       0x00, 0x0a, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20])
    b[108:126] = bytes([0x00, 0x00, 0x00, 0x10] + [0x00] * 14)
    b[126] = 1
    checksum(b)
    return b

def cta_block(sbs_full):
    vics = [16, 4, 32, 19, 31, 34]          # 1080p60 720p60 1080p24 720p50 1080p50 1080p30
    vdb = bytes([(2 << 5) | len(vics)] + vics)
    structure_all = 1 << 8                  # side-by-side (half) for every VIC
    x_entries = [(0 << 4) | 6,              # VIC 16: top-and-bottom
                 (5 << 4) | 0]              # VIC 34: frame packing
    if sbs_full:
        x_entries.append((0 << 4) | 3)      # VIC 16: side-by-side (full)
    payload = bytes([0x03, 0x0c, 0x00,      # IEEE OUI 00-0C-03, LSB first
                     0x10, 0x00,            # physical address 1.0.0.0
                     0x00,                  # no deep colour
                     300 // 5,              # Max_TMDS_Clock 300 MHz
                     0x20,                  # HDMI_Video_present, no latency fields
                     0x80 | (1 << 5),       # 3D_present, 3D_Multi_present = 01
                     (0 << 5) | (2 + len(x_entries)),   # HDMI_VIC_LEN 0, HDMI_3D_LEN
                     structure_all >> 8, structure_all & 0xff] + x_entries)
    vsdb = bytes([(3 << 5) | len(payload)]) + payload
    vcdb = bytes([(7 << 5) | 2, 0x00, 0x4a])   # Video Capability Data Block: RGB range selectable
    blocks = vdb + vsdb + vcdb
    c = bytearray(128)
    c[0:4] = bytes([0x02, 0x03, 4 + len(blocks), 0x81])   # CTA rev 3, underscan, 1 native DTD
    c[4:4 + len(blocks)] = blocks
    checksum(c)
    return c

args = sys.argv[1:]
sbs_full = "--sbs-full" in args
args = [a for a in args if a != "--sbs-full"]
edid = base_block() + cta_block(sbs_full)
open(args[0], "wb").write(edid)
name = args[1] if len(args) > 1 else "edid"
print("static const u8 %s[] = {" % name)
for i in range(0, len(edid), 12):
    print("\t" + ", ".join("0x%02x" % x for x in edid[i:i + 12]) + ",")
print("};")
