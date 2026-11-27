#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""measure_sidebar.py START_DIR [TITLE...]: on System Monitor's capture, the rendered width of each sidebar entry's
text against its full width in the session's font (Noto Sans 10 pt, Noto Sans CJK for CJK text, 96 dpi: 13.333 px).
Sidebar entries come from AT-SPI (list items; their boxes are relative to the window's surface: START_DIR/
window-offset.txt, "DX DY", gives the surface's place on the capture, as KWin reports it; without it the window is taken
as maximised and the title bar's height, the screen's height minus the frame's, is added). An entry is cut when it ends
in Qt's ellipsis (calibrated on entries known cut and whole); an entry where no text is found is "not measured"
(cut: null), never whole. Prints JSON lines; exits 1 when a TITLE given is cut, not measured or not found."""
import json
import sys

from PIL import Image, ImageFont

START = sys.argv[1]
WANT = sys.argv[2:]
LAT = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 13.333)
CJK = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 13.333, index=0)


def full_width(text):
    cjk = any(ord(c) > 0x2E80 for c in text)
    return (CJK if cjk else LAT).getlength(text)


objs = json.load(open(START + "/atspi.json"))["objects"]
im = Image.open(START + "/screen.png").convert("RGB")
frame = next(o for o in objs if o.get("role") == "frame")
try:
    dx, dy = (int(round(float(v))) for v in open(START + "/window-offset.txt").read().split()[:2])
except OSError:
    dx, dy = 0, im.size[1] - frame["box"][3]
items = [o for o in objs if o.get("role") == "list item" and o.get("showing") and o.get("name")
         and o["box"] and o["box"][0] < 400]
rows, failed = [], False
for o in items:
    x, y, w, h = o["box"]
    x += dx
    y += dy
    if x < 0 or y < 0 or x + w > im.size[0] or y + h > im.size[1]:
        rows.append({"title": o["name"], "rendered": 0, "full": round(full_width(o["name"]), 1), "cut": None})
        continue
    # inside the selected entry's highlight too: the background is sampled and the text searched clear of the margins
    bg = im.getpixel((x + w - 10, y + h // 2))
    ink = [(px, py) for px in range(x + 8, x + w - 8) for py in range(y + h // 4, y + h - h // 4)
           if sum(abs(a - b) for a, b in zip(im.getpixel((px, py)), bg)) > 90]
    # the entry's icon, where the theme draws one, is ink too: split the columns at gaps over 8 px (letters and words
    # are closer) and leave out a first group of an icon's size at the entry's left
    xs = sorted({px for px, _ in ink})
    groups = []
    for px in xs:
        if groups and px - groups[-1][-1] <= 8:
            groups[-1].append(px)
        else:
            groups.append([px])
    if len(groups) > 1 and groups[0][-1] - groups[0][0] <= 26 and groups[0][0] <= x + 32:
        ink = [(px, py) for px, py in ink if px > groups[0][-1]]
    cols = [px for px, _ in ink]
    rendered = (max(cols) - min(cols) + 1) if cols else 0
    expected = full_width(o["name"])
    # Qt elides with "…": then the text's last 6 px hold ink at most 3 px high in its lower half (the dots), where a
    # title of letters ends with a glyph taller than that
    cut = None  # no text found: not measured
    if ink:
        top, bottom = min(py for _, py in ink), max(py for _, py in ink)
        tail = [py for px, py in ink if px > max(cols) - 6]
        cut = max(tail) - min(tail) <= 3 and min(tail) > (top + bottom) / 2
    rows.append({"title": o["name"], "rendered": rendered, "full": round(expected, 1), "cut": cut})
for r in rows:
    print(json.dumps(r, ensure_ascii=False))
for t in WANT:
    match = [r for r in rows if r["title"] == t]
    if not match or match[0]["cut"] is not False:
        failed = True
        print(json.dumps({"want": t, "found": bool(match), "cut": match[0]["cut"] if match else None}, ensure_ascii=False))
sys.exit(1 if failed else 0)
