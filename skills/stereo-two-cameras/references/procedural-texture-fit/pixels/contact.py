#!/usr/bin/env python3
"""A contact sheet: contact.py OUT.jpg TILE COLUMNS "CAPTION" FILE=LABEL...   (pictures reduced to TILE pixels, the label above each)"""
import sys
from PIL import Image, ImageDraw
out, g, cols, cap = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
items = [a.split("=", 1) for a in sys.argv[5:]]
rows = (len(items) + cols - 1) // cols
caplines = [l for l in cap.split("\n") if l]
sheet = Image.new("RGB", (cols * (g + 6) + 6, rows * (g + 20) + 6 + 14 * len(caplines)), "white"); d = ImageDraw.Draw(sheet)
for i, (f, lab) in enumerate(items):
    x = 6 + (i % cols) * (g + 6); y = 4 + (i // cols) * (g + 20)
    d.text((x, y), lab[: g // 6], fill="black")
    im = Image.open(f).convert("RGB")
    sheet.paste(im if im.size == (g, g) else im.resize((g, g), Image.LANCZOS), (x, y + 14))
for k, l in enumerate(caplines):
    d.text((6, rows * (g + 20) + 6 + 14 * k), l, fill="black")
sheet.save(out, quality=88)
