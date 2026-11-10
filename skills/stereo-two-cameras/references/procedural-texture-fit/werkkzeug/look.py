#!/usr/bin/env python3
"""Draw one or more typed graphs and put them beside the tile they are meant to match.

Usage: KTG_IMAGE=image look.py BUILD_DIR TILE.png SHEET.jpg GRAPH.txt [GRAPH.txt ...]
The sheet shows the tile first, then each graph's picture, all at the same size, left to right.
"""
import sys

from PIL import Image

import wz
import wzlang

build, tile, sheet, graphs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
pics = [Image.open(tile).convert("RGB")]
for g in graphs:
    script, size, n = wzlang.compile_graph(open(g).read())
    a = wz.render(build, script)
    pics.append(Image.fromarray(a))
    Image.fromarray(a).save(g.rsplit(".", 1)[0] + ".png")
    print("%s: %d operators, %d bytes" % (g, n, size))
S = 512
out = Image.new("RGB", (len(pics) * (S + 6) - 6, S), "white")
for i, p in enumerate(pics):
    out.paste(p.resize((S, S), Image.LANCZOS), (i * (S + 6), 0))
out.save(sheet, quality=90)
