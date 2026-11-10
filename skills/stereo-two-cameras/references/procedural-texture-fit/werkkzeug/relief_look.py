#!/usr/bin/env python3
"""Draw a typed graph that builds a relief, and show the tile, the lit picture and the height picture.

The graph must name its height picture `h` (white is the surface, black the deepest point).
Usage: KTG_IMAGE=image relief_look.py BUILD_DIR TILE.png SHEET.jpg GRAPH.txt
Writes GRAPH.png (lit) and GRAPH-height.png beside the graph.
"""
import sys

from PIL import Image

import wz
import wzlang

build, tile, sheet, graph = sys.argv[1:5]
text = open(graph).read()
script, size, n = wzlang.compile_graph(text)
lit = Image.fromarray(wz.render(build, script))
height = Image.fromarray(wz.render(build, wzlang.compile_graph(text, out="h")[0])).convert("L")
base = graph.rsplit(".", 1)[0]
lit.save(base + ".png")
height.save(base + "-height.png")
print("%s: %d operators, %d bytes" % (graph, n, size))
S = 512
out = Image.new("RGB", (3 * (S + 6) - 6, S), "white")
for i, p in enumerate((Image.open(tile).convert("RGB"), lit, height.convert("RGB"))):
    out.paste(p.resize((S, S), Image.LANCZOS), (i * (S + 6), 0))
out.save(sheet, quality=88)
