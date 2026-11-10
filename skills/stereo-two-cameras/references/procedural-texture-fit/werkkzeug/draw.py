#!/usr/bin/env python3
"""Draw a typed graph at its own size: GRAPH.png (lit), GRAPH-height.png (the operator named h)
and, when the graph has an operator named dep, GRAPH-depth.png (the height without its finest grain,
which the stereo pair uses for depth while the light keeps the grain).

A procedural texture is drawn at the size it is wanted, never resized afterwards: set the size in the
graph's generators (10 10 is 1024 x 1024).
Usage: KTG_IMAGE=image draw.py BUILD_DIR GRAPH.txt [GRAPH.txt ...]
"""
import sys

from PIL import Image

import wz
import wzlang

build = sys.argv[1]
for graph in sys.argv[2:]:
    text = open(graph).read()
    base = graph.rsplit(".", 1)[0]
    lit = Image.fromarray(wz.render(build, wzlang.compile_graph(text)[0]))
    height = Image.fromarray(wz.render(build, wzlang.compile_graph(text, out="h")[0])).convert("L")
    lit.save(base + ".png")
    height.save(base + "-height.png")
    if any(line.split()[:1] == ["dep"] for line in text.splitlines()):
        Image.fromarray(wz.render(build, wzlang.compile_graph(text, out="dep")[0])).convert("L").save(base + "-depth.png")
    print(graph, lit.size, height.size)
