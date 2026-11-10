#!/usr/bin/env python3
"""A graph an artist can type, turned into the parameter words wzrender takes.

One operator per line:   NAME OPERATOR INPUTS VALUES...
  INPUTS   "-" or names joined by commas
  VALUES   in the order of werkkzeug3's own parameter words for that operator: whole numbers,
           decimals, and colours as #aarrggbb. Sizes are powers of two (9 is 512 pixels).
Lines starting with # are notes. The last operator is the result.

Usage: wzlang.py GRAPH.txt            prints the wzrender script and the graph's size
"""
import struct
import sys

# i = whole number, f = decimal, c = colour; from the packing strings of werkkzeug3's operator table
PACK = {"Flat": "iic", "Perlin": "iiiififffcc", "Color": "ic", "Merge": "i", "GlowRect": "ffffffcffii", "GlowRectOld": "ffffffcffii",
        "Dots": "ccii", "Blur": "ifff", "Mask": "i", "HSCB": "ffff", "Transform": "fffffiii", "Distort": "fi", "Normals": "fi",
        "Light": "iffffffccfff", "Bump": "ifffffccfffcff", "Cell": "iiccciiffifif", "Gradient": "iiccfffi", "Range": "icc",
        "TransformMul": "ffffficiic", "Twirl": "ffffffi", "Sharpen": "ifff", "ColorBalance": "fffffffff", "Unwrap": "i",
        "Bricks": "iicccffiiiiiff", "Bulge": "f", "Paste": "fffffffi"}
# Light and Bump take position x, y, z and direction a, b after the mode
PACK["Light"] = "ifffffccfff"
PACK["Bump"] = "ifffffccfffcff"


def compile_graph(text):
    lines, names = [], []
    for raw in text.splitlines():
        t = raw.split("#!")[0].strip()
        if not t or t.startswith("#"):
            continue
        p = t.split()
        name, op, ins, vals = p[0], p[1], p[2], p[3:]
        if op not in PACK:
            raise ValueError("%s: no operator %s" % (name, op))
        kinds = PACK[op]
        if len(vals) != len(kinds):
            raise ValueError("%s %s: %d values, the operator takes %d" % (name, op, len(vals), len(kinds)))
        words = []
        for v, k in zip(vals, kinds):
            if k == "c":
                words.append(int(v.lstrip("#"), 16))
            elif k == "f":
                words.append(struct.unpack("<I", struct.pack("<f", float(v)))[0])
            else:
                words.append(int(v) & 0xFFFFFFFF)
        for i in ([] if ins == "-" else ins.split(",")):
            if i not in names:
                raise ValueError("%s: input %s is not defined above it" % (name, i))
        names.append(name)
        lines.append("%s %s %s %s" % (name, op, ins, " ".join("%x" % w for w in words)))
    lines.append("out " + names[-1])
    size = sum(1 + 4 * len(PACK[l.split()[1]]) for l in lines[:-1])
    return "\n".join(lines) + "\n", size, len(names)


if __name__ == "__main__":
    s, size, n = compile_graph(open(sys.argv[1]).read())
    sys.stdout.write(s)
    sys.stderr.write("%d operators, %d bytes\n" % (n, size))
