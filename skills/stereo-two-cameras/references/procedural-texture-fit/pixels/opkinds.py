"""The packing of every operator the fitter writes (i whole number, f decimal, c colour): werkkzeug3's from p2p.zig's
table, the modern family (milestone 2b) from each ops/*.zig file's parameter table. Ramp's table is made by a loop
over its eight stops, so it is spelled out here; `p2p kinds` prints the same table from inside the program, and
test_opkinds compares the two."""
import glob, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = HERE + "/p2p.zig" if os.path.exists(HERE + "/p2p.zig") else os.path.dirname(HERE) + "/src/p2p.zig"


def kinds():
    k = {}
    for m in re.finditer(r'\.name = "(\w+)", \.kinds = "(\w*)"', open(SRC).read()):
        k[m.group(1)] = m.group(2)
    ops = os.path.join(os.path.dirname(SRC), "ops")
    for f in sorted(glob.glob(ops + "/*.zig")):
        t = open(f).read()
        m = re.search(r'pub const name = "(\w+)";', t)
        if not m:
            continue
        name = m.group(1)
        if name == "Ramp":
            k[name] = "ii" + "fc" * 8
            continue
        k[name] = "".join({"int": "i", "cycle": "i", "float": "f", "rgba": "c"}[x] for x in re.findall(r'\.kind = \.(\w+)', t))
    return k
