#!/usr/bin/env python3
"""Two tiled control pictures drawn by OpenKTG's own operators, 8 x 8 tiles of 256 pixels.

Usage: KTG_IMAGE=image make_tiled_controls.py WORKDIR
  control-tiled-ktg    every tile is Noise with its own seed and its own two colours
  control-tiled-mixed  tiles take turns: Noise, Cells, GlowRect over a flat colour, a flat colour
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

WORK = sys.argv[1]
IMAGE = os.environ["KTG_IMAGE"]  # any local image that has g++
rng = np.random.default_rng(473)


def render(lines):
    cmd = ["docker", "run", "--rm", "-i", "--name", "x3d-473w-controls-%d" % os.getpid(), "--network", "none",
           "--ulimit", "core=0", "--cpus", "1", "--user", "%d:%d" % (os.getuid(), os.getgid()),
           "-v", WORK + ":" + WORK + ":ro", IMAGE, WORK + "/bin/ktgtool", "tiles", "8"]
    raw = subprocess.run(cmd, input=("\n".join(lines) + "\n").encode(), stdout=subprocess.PIPE, check=True).stdout
    t = np.frombuffer(raw, dtype=np.uint8).reshape(8, 8, 256, 256, 3)
    return t.transpose(0, 2, 1, 3, 4).reshape(2048, 2048, 3)


def noise():
    c = rng.integers(0, 256, 6)
    return "N 2 6 0.6 %d 2 %s" % (rng.integers(0, 4096), " ".join(map(str, c)))


def cells():
    out = ["C 5"]
    for _ in range(5):
        x, y = (rng.integers(0, 64, 2) + 0.5) / 64
        out.append("%.6f %.6f %d %d %d" % (x, y, *rng.integers(0, 256, 3)))
    return " ".join(out)


def glow():
    bg, col = rng.integers(0, 256, 3), rng.integers(0, 256, 3)
    ox, oy = rng.integers(24, 41, 2) / 64
    ux, vy = rng.integers(6, 15, 2) / 64
    ru, rv = rng.choice([0.25, 0.5, 0.75], 2)
    return "G %d %d %d %.6f %.6f %.6f %.6f %.2f %.2f %d %d %d" % (*bg, ox, oy, ux, vy, ru, rv, *col)


def flat():
    return "F %d %d %d" % tuple(rng.integers(0, 256, 3))


a = [noise() for _ in range(64)]
b = [[noise, cells, glow, flat][(i // 8 + i % 8) % 4]() for i in range(64)]
os.makedirs(WORK + "/tex2", exist_ok=True)
Image.fromarray(render(a)).save(WORK + "/tex2/control-tiled-ktg.png")
Image.fromarray(render(b)).save(WORK + "/tex2/control-tiled-mixed.png")
json.dump({"control-tiled-ktg": a, "control-tiled-mixed": b}, open(WORK + "/tex2/tiled-controls-truth.json", "w"), indent=1)
