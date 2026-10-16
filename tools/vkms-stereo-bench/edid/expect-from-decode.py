#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""expect-from-decode.py DECODE.txt: the stereo formats a KMS connector should list for an EDID,
from edid-decode's text (not from the kernel's parser), as "WxH@R layout" lines.

- 3D present: the HDMI 1.4b mandatory 3D formats of the 2D formats the EDID lists
  (1080p24 frame packing and top-and-bottom, 720p50/60 frame packing and top-and-bottom,
  1080i50/60 side by side (half)).
- 3D_Structure_ALL ("3D: ..." lines) for the VICs it applies to ("All advertised VICs" means the
  first 16, or the "3D VIC indices that support these capabilities" list).
- "3D VIC indices with specific capabilities" entries.
Kept: progressive formats (the connector does not allow interlace) in the layouts DRM's EDID parser
lists: frame packing, top-and-bottom, side by side (half, horizontal), side by side (full), line
alternative, L + depth and L + depth + graphics + graphics-depth (HDMI 1.4a, Table H-2); the last
three on progressive formats only (Figures H-3, H-5, H-6)."""
import re, sys

names = {"frame packing": "fp", "frame-packing": "fp", "top-and-bottom": "tab",
         "side-by-side (half, horizontal)": "sbs-half", "side-by-side (full)": "sbs-full",
         "line alternative": "line-alt", "line-alternative": "line-alt",
         "field alternative": "field-alt", "field-alternative": "field-alt",
         "l + depth": "l-depth", "l + depth + gfx + gfx-depth": "l-depth-gfx"}
vic_re = re.compile(r"VIC\s+(\d+):\s+(\d+)x(\d+)(i?)\s+([\d.]+) Hz")
mandatory = {(32, "fp"), (32, "tab"), (19, "fp"), (19, "tab"), (4, "fp"), (4, "tab"),
             (20, "sbs-half"), (5, "sbs-half")}

text = open(sys.argv[1]).read().splitlines()
vics, fmt = [], {}
section = None
all_structs, mask_vics, specific, present, all_vics = [], [], [], False, False
for line in text:
    s = line.strip()
    if s.startswith("Video Data Block"):
        section = "vdb"; continue
    if s.startswith("Vendor-Specific Data Block (HDMI)"):
        section = "hdmi"; continue
    if section == "vdb":
        m = vic_re.search(s)
        if not m or not s.startswith("VIC"):
            section = None
        else:
            v = int(m.group(1)); vics.append(v)
            fmt[v] = (int(m.group(2)), int(m.group(3)), m.group(4) == "i", round(float(m.group(5))))
            continue
    if section == "hdmi":
        if s == "3D present":
            present = True
        elif s.startswith("All advertised VICs are 3D-capable"):
            all_vics = True
        elif s.startswith("3D: "):
            all_structs.append(s[4:].lower())
        elif s.startswith("3D VIC indices that support"):
            section = "mask"
        elif s.startswith("3D VIC indices with specific"):
            section = "specific"
        elif not line.startswith("    "):
            section = None
        continue
    if section in ("mask", "specific"):
        m = vic_re.search(s)
        if not m:
            section = "hdmi" if line.startswith("      ") else None
            if section == "hdmi" and s.startswith("3D VIC indices with specific"):
                section = "specific"
            continue
        v = int(m.group(1))
        if section == "mask":
            mask_vics.append(v)
        else:
            rest = s[s.index("MHz") + 3:].strip()
            specific.append((v, rest[1:-1].lower() if rest.startswith("(") else ""))
        continue

out = set()
def add(v, layout):
    w, h, inter, r = fmt[v]
    if not inter and layout in names.values():
        out.add("%dx%d@%d %s" % (w, h, r, layout))
if present:
    for v in vics:
        for mv, layout in mandatory:
            if mv == v:
                add(v, layout)
targets = vics[:16] if all_vics else mask_vics
for st in all_structs:
    if st in names:
        for v in targets:
            add(v, names[st])
for v, st in specific:
    if st in names:
        add(v, names[st])
for f in sorted(out):
    print(f)
