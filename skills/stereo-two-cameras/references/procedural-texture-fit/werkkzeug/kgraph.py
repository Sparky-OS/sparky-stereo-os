#!/usr/bin/env python3
"""Take one named texture out of a werkkzeug3 project: its operator graph as a script for
wzrender, and the same graph in plain words.

Usage: kgraph.py FILE.k                       lists the named bitmaps (stores) with their operator counts
       kgraph.py FILE.k NAME [--max-size N]   prints the script; writes nothing
       import kgraph; g = kgraph.Graph(path); g.script(name), g.describe(name)
"""
import struct
import sys

import kdoc

NAMES = {0x21: "Flat", 0x22: "Perlin", 0x23: "Color", 0x24: "Merge", 0x25: "Format", 0x27: "GlowRectOld", 0x28: "Dots",
         0x29: "Blur", 0x2a: "Mask", 0x2b: "HSCB", 0x2c: "Transform", 0x2d: "Distort", 0x2e: "Normals", 0x2f: "Light",
         0x30: "Bump", 0x31: "Text", 0x32: "Cell", 0x34: "Gradient", 0x35: "Range", 0x36: "TransformMul", 0x37: "Twirl",
         0x38: "Sharpen", 0x39: "GlowRect", 0x3b: "ColorBalance", 0x3c: "Unwrap", 0x3d: "Bricks", 0x3e: "Bulge", 0x43: "Paste"}
PASS = {0x02: "Store", 0x03: "Nop", 0x41: "Export"}
LOAD = 0x01
# parameter labels, word index and kind, from the Edit_Bitmap_* functions of werkkzeug3's werkops.cpp
P = {
    "Flat": [("size", 0, "size"), ("colour", 2, "c")],
    "Perlin": [("size", 0, "size"), ("frequency", 2, "i"), ("octaves", 3, "i"), ("fadeoff", 4, "f"), ("seed", 5, "i"),
               ("mode", 6, "norm|abs|sin|abs+sin"), ("amplify", 7, "f"), ("gamma", 8, "f"), ("colour 0", 9, "c"), ("colour 1", 10, "c")],
    "Color": [("mode", 0, "mul|add|sub|gray|invert|scale"), ("colour", 1, "c")],
    "Range": [("flags", 0, "i"), ("colour 0", 1, "c"), ("colour 1", 2, "c")],
    "Merge": [("mode", 0, "add|sub|mul|diff|alpha|brightness|hardlight|over|addsmooth|min|max")],
    "Format": [],
    "GlowRect": [("centre", 0, "ff"), ("radius", 2, "ff"), ("size", 4, "ff"), ("colour", 6, "c"), ("blend", 7, "f"),
                 ("power", 8, "f"), ("wrap", 9, "off|on"), ("flags", 10, "i")],
    "Dots": [("colour 0", 0, "c"), ("colour 1", 1, "c"), ("count", 2, "i"), ("seed", 3, "i")],
    "Blur": [("passes", 0, "i"), ("blur", 1, "ff"), ("amplify", 3, "f")],
    "Mask": [("mode", 0, "mix|add|sub|mul")],
    "HSCB": [("hue", 0, "f"), ("saturation", 1, "f"), ("contrast", 2, "f"), ("brightness", 3, "f")],
    "Transform": [("angle", 0, "f"), ("scale", 1, "ff"), ("offset", 3, "ff"), ("border and filter", 5, "i"), ("new size", 6, "ii")],
    "TransformMul": [("angle", 0, "f"), ("scale", 1, "ff"), ("offset", 3, "ff"), ("border", 5, "i"), ("pre-adjust", 6, "c"),
                     ("mode", 7, "i"), ("count", 8, "i"), ("fade", 9, "c")],
    "Twirl": [("strength", 0, "f"), ("gamma", 1, "f"), ("radius", 2, "ff"), ("centre", 4, "ff"), ("border", 6, "i")],
    "Distort": [("strength", 0, "f"), ("border", 1, "i")],
    "Normals": [("strength", 0, "f"), ("mode", 1, "i")],
    "Light": [("mode", 0, "spot|point|directional"), ("position", 1, "fff"), ("direction", 4, "ff"), ("diffuse", 6, "c"),
              ("ambient", 7, "c"), ("outer", 8, "f"), ("falloff", 9, "f"), ("amplify", 10, "f")],
    "Bump": [("mode", 0, "spot|point|directional"), ("position", 1, "fff"), ("direction", 4, "ff"), ("diffuse", 6, "c"),
             ("ambient", 7, "c"), ("outer", 8, "f"), ("falloff", 9, "f"), ("amplify", 10, "f"), ("specular", 11, "c"),
             ("specular power", 12, "f"), ("specular amplify", 13, "f")],
    "Text": [],
    "Cell": [("size", 0, "size"), ("colour 0", 2, "c"), ("colour 1", 3, "c"), ("colour 2", 4, "c"), ("max", 5, "i"), ("seed", 6, "i"),
             ("amplify", 7, "f"), ("gamma", 8, "f"), ("flags", 9, "i"), ("min distance", 10, "f"), ("percentage", 11, "i"), ("aspect", 12, "f")],
    "Bricks": [("size", 0, "size"), ("colour 0", 2, "c"), ("colour 1", 3, "c"), ("joints colour", 4, "c"), ("joints size", 5, "ff"),
               ("count", 7, "ii"), ("seed", 9, "i"), ("single width stones", 10, "i"), ("flags", 11, "i"), ("side", 12, "f"), ("colour balance", 13, "f")],
    "Gradient": [("size", 0, "size"), ("colour 0", 2, "c"), ("colour 1", 3, "c"), ("position", 4, "f"), ("angle", 5, "f"),
                 ("width", 6, "f"), ("mode", 7, "linear|gaussian|sine")],
    "Sharpen": [("order", 0, "i"), ("radius", 1, "ff"), ("amplify", 3, "f")],
    "ColorBalance": [("shadows", 0, "fff"), ("midtones", 3, "fff"), ("highlights", 6, "fff")],
    "Unwrap": [("mode", 0, "i")],
    "Bulge": [("warp", 0, "f")],
    "Paste": [("pre-scale", 0, "ff"), ("position", 2, "ff"), ("size", 4, "ff"), ("angle", 6, "f"), ("mode", 7, "i")],
}
P["GlowRectOld"] = P["GlowRect"]
GENERATORS = {"Flat", "Perlin", "Cell", "Gradient", "Bricks"}


def f32(w):
    return struct.unpack("<f", struct.pack("<I", w & 0xFFFFFFFF))[0]


def words_text(name, words):
    out = []
    w = list(words) + [0] * 32
    for label, i, kind in P.get(name, []):
        if kind == "size":
            v = "%d x %d" % (1 << w[i], 1 << w[i + 1])
        elif kind == "c":
            v = "#%08x" % w[i]
        elif kind == "i":
            v = str(struct.unpack("<i", struct.pack("<I", w[i]))[0])
        elif kind == "ii":
            v = "%d, %d" % (w[i], w[i + 1])
        elif set(kind) == {"f"}:
            v = ", ".join("%.4g" % f32(w[i + k]) for k in range(len(kind)))
        else:
            opts = kind.split("|")
            v = opts[w[i]] if w[i] < len(opts) else str(w[i])
        out.append("%s %s" % (label, v))
    return "; ".join(out)


class Graph:
    def __init__(self, path):
        self.pages, self.ops, _ = kdoc.load(path)
        self.named = {}
        for o in self.ops:
            if o["name"]:
                self.named.setdefault(o["name"], o)
        by_page = {}
        for o in self.ops:
            if not o["hide"]:
                by_page.setdefault(o["page"], []).append(o)
        self.inputs = {}
        for page_ops in by_page.values():
            rows = {}
            for o in page_ops:
                rows.setdefault(o["y"], []).append(o)
            for o in page_ops:
                above = [p for p in rows.get(o["y"] - 1, []) if p["x"] + p["w"] > o["x"] and p["x"] < o["x"] + o["w"]]
                self.inputs[o["i"]] = sorted(above, key=lambda p: p["x"])

    def resolve(self, o, depth=0):
        """Follow stores, nops, loads and bypassed operators down to the operator that draws."""
        while depth < 200:
            depth += 1
            if o["cls"] == LOAD:
                t = self.named.get(o["links"][0]) if o["links"] else None
                if t is None:
                    return None
                o = t
            elif o["cls"] in PASS or o["bypass"]:
                ins = self.inputs.get(o["i"], [])
                if not ins:
                    return None
                o = ins[0]
            else:
                return o
        return None

    def collect(self, name):
        root = self.resolve(self.named[name])
        order, seen, bad = [], {}, []

        def walk(o):
            if o is None:
                bad.append("a missing input")
                return None
            if o["i"] in seen:
                return seen[o["i"]]
            if o["cls"] not in NAMES:
                bad.append("operator class 0x%x" % o["cls"])
                return None
            ins = [walk(self.resolve(p)) for p in self.inputs.get(o["i"], [])]
            if NAMES[o["cls"]] in GENERATORS:
                ins = []
            seen[o["i"]] = "v%d" % len(order)
            order.append((seen[o["i"]], o, ins))
            return seen[o["i"]]

        sys.setrecursionlimit(10000)
        top = walk(root) if root else None
        return order, top, bad

    def script(self, name):
        order, top, bad = self.collect(name)
        if bad or top is None:
            return None, bad or ["no drawing operator"]
        lines = []
        for vid, o, ins in order:
            lines.append("%s %s %s %s" % (vid, NAMES[o["cls"]], ",".join(ins) if ins else "-", " ".join("%x" % w for w in o["words"])))
        lines.append("out " + top)
        return "\n".join(lines) + "\n", []

    def describe(self, name):
        order, top, bad = self.collect(name)
        out = []
        for vid, o, ins in order:
            n = NAMES[o["cls"]]
            stored = " (stored as %s)" % o["name"] if o["name"] else ""
            out.append("%s = %s%s%s: %s" % (vid, n, "(" + ", ".join(ins) + ")" if ins else "", stored, words_text(n, o["words"])))
        return out

    def size_bytes(self, name):
        """The graph as werkkzeug3 keeps it: one class byte and the parameter words of every operator."""
        order, top, bad = self.collect(name)
        return sum(1 + 4 * len(o["words"]) for _, o, _ in order), len(order)


if __name__ == "__main__":
    g = Graph(sys.argv[1])
    if len(sys.argv) == 2:
        for n in sorted(g.named):
            o = g.named[n]
            if o["cls"] in (0x02,) or o["cls"] in NAMES:
                order, top, bad = g.collect(n)
                if top and not bad:
                    print(len(order), n, g.pages[o["page"]]["name"])
    else:
        s, bad = g.script(sys.argv[2])
        print(s if s else "cannot draw: " + ", ".join(sorted(set(bad))))
