#!/usr/bin/env python3
"""The visual check: the finished drawing of every structure the readings allowed, beside the original.

Usage: choices.py REFDIR FITDIR OUT.jpg NAME TAG...
Top row: whole pictures at half size. Bottom row: the same 256 x 256 cut, pixel for pixel.
The caption of each drawing is its tag, bytes and the inner measure; the lowest measure is the program's choice (marked P).
The person or model looking chooses by eye; the sheet only shows.
"""
import re, sys
from PIL import Image, ImageDraw
ref, fit, out, name = sys.argv[1:5]; tags = sys.argv[5:]
a = Image.open("%s/%s.ppm" % (ref, name)).convert("RGB")
g = 256; c0 = (a.width - g) // 2
cols = [("original", a, "")]
best = None
for t in tags:
    try:
        im = Image.open("%s/%s/%s.ppm" % (fit, t, name)).convert("RGB")
        log = open("%s/%s/%s.out" % (fit, t, name)).read()
    except OSError:
        cols.append((t + ": no drawing", None, "")); continue
    m = re.findall(r"cleaned and tuned at \d+ px: (\d+) operators, (\d+) bytes, measure ([0-9.]+)", log)[-1]
    cols.append((t, im, "%s ops, %s B, measure %s" % m))
    if best is None or float(m[2]) < best[0]:
        best = (float(m[2]), t)
sheet = Image.new("RGB", (len(cols) * (g + 6) + 6, 2 * g + 50), "white"); d = ImageDraw.Draw(sheet)
for i, (lab, im, cap) in enumerate(cols):
    x = 6 + i * (g + 6)
    d.text((x, 2), name + ": " + lab + (" (P)" if best and lab == best[1] else ""), fill="black")
    if im is not None:
        sheet.paste(im.resize((g, g), Image.LANCZOS), (x, 16)); sheet.paste(im.crop((c0, c0, c0 + g, c0 + g)), (x, 16 + g + 4))
    d.text((x, 2 * g + 24), cap, fill="black")
sheet.save(out, quality=88)
print(name, "program's choice:", best[1] if best else "none")
