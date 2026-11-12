#!/usr/bin/env python3
"""A sheet to judge a Text picture by eye: the original and the found procedure's drawing, whole and close up,
and under them the font sentences (which font stood in for which name) and the two graphs as typed text.

Usage: sheet2.py ORIGINAL.ppm FOUND.ppm OUT.jpg CAPTION-FILE [X Y]
CAPTION-FILE holds the lines to print under the pictures. X Y: the top left of the 256 pixel close-up (default: where the ink is densest).
"""
import sys
from PIL import Image, ImageDraw, ImageChops
a = Image.open(sys.argv[1]).convert("RGB"); b = Image.open(sys.argv[2]).convert("RGB")
if a.size != b.size:
    sys.exit("the two pictures differ in size: %s and %s" % (a.size, b.size))
lines = [l.rstrip("\n") for l in open(sys.argv[4], encoding="utf-8", errors="replace")]
w = a.width; g = 256
if len(sys.argv) > 6:
    cx, cy = int(sys.argv[5]), int(sys.argv[6])
else:
    # the close-up goes where the original differs most from its own most common colour
    small = a.convert("L").resize((w // 16, w // 16), Image.BOX)
    bg = max(set(small.getdata()), key=list(small.getdata()).count)
    best, cx, cy = -1, (w - g) // 2, (w - g) // 2
    px = small.load(); k = g // 16; m = w // 16
    for y in range(0, m - k + 1, 2):
        for x in range(0, m - k + 1, 2):
            v = sum(abs(px[x + i, y + j] - bg) for i in range(k) for j in range(k))
            if v > best:
                best, cx, cy = v, x * 16, y * 16
tiles = [("original, whole", a.resize((g, g), Image.LANCZOS)), ("found, whole", b.resize((g, g), Image.LANCZOS)),
         ("original, close up 1:1 at %d, %d" % (cx, cy), a.crop((cx, cy, cx + g, cy + g))), ("found, close up 1:1", b.crop((cx, cy, cx + g, cy + g)))]
sheet = Image.new("RGB", (4 * g + 5 * 6, g + 24 + 13 * len(lines) + 8), "white"); d = ImageDraw.Draw(sheet)
for i, (lab, im) in enumerate(tiles):
    x = 6 + i * (g + 6); sheet.paste(im, (x, 16)); d.text((x, 2), lab, fill="black")
for k, l in enumerate(lines):
    d.text((6, g + 22 + 13 * k), l[:170], fill="black")
sheet.save(sys.argv[3], quality=90)
