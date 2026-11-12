#!/usr/bin/env python3
"""A sheet to judge by eye: the original and the found procedure's drawing, at a glance and close up.

Usage: sheet.py ORIGINAL.ppm FOUND.ppm OUT.jpg "CAPTION"
At a glance: both whole pictures at half size. Close up: the same 256 x 256 cut of both, pixel for pixel.
"""
import sys
from PIL import Image, ImageDraw
a = Image.open(sys.argv[1]).convert("RGB"); b = Image.open(sys.argv[2]).convert("RGB")
if a.size != b.size:
    sys.exit("the two pictures differ in size: %s and %s" % (a.size, b.size))
w = a.width; g = 256; c0 = (w - g) // 2
tiles = [("original, whole", a.resize((g, g), Image.LANCZOS)), ("found, whole", b.resize((g, g), Image.LANCZOS)),
         ("original, close up 1:1", a.crop((c0, c0, c0 + g, c0 + g))), ("found, close up 1:1", b.crop((c0, c0, c0 + g, c0 + g)))]
sheet = Image.new("RGB", (4 * g + 5 * 6, g + 44), "white"); d = ImageDraw.Draw(sheet)
for i, (lab, im) in enumerate(tiles):
    x = 6 + i * (g + 6); sheet.paste(im, (x, 16)); d.text((x, 2), lab, fill="black")
d.text((6, g + 22), sys.argv[4], fill="black")
sheet.save(sys.argv[3], quality=90)
