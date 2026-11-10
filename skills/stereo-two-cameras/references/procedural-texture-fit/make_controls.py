#!/usr/bin/env python3
"""Three control pictures whose right answer is known before the fit runs.

Usage: make_controls.py WORKDIR
  control-ktg      made by OpenKTG's own Noise operator with known parameters
  control-white    independent uniform random bytes: nothing to find
  control-lattice  a mean colour plus 12 known cosine waves
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

WORK = sys.argv[1]
IMAGE = os.environ["KTG_IMAGE"]  # any local image that has g++
os.makedirs(WORK + "/tex", exist_ok=True)

truth = dict(freq=2, oct=7, fadeoff=0.55, seed=1234, mode=2)
stops = [[20 + 12 * k, 30 + 9 * k, 70 + 5 * k] for k in range(16)]
cmd = ["docker", "run", "--rm", "--network", "none", "--ulimit", "core=0", "--cpus", "4",
       "--user", "%d:%d" % (os.getuid(), os.getgid()), "-v", WORK + ":" + WORK + ":ro", IMAGE,
       WORK + "/bin/ktgtool", "noise", "11", "2", "7", "0.55", "1234", "2"] + [str(v) for s in stops for v in s]
raw = subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout
Image.fromarray(np.frombuffer(raw, dtype=np.uint8).reshape(2048, 2048, 3)).save(WORK + "/tex/control-ktg.png")

rng = np.random.default_rng(473)
Image.fromarray(rng.integers(0, 256, (2048, 2048, 3), dtype=np.uint8)).save(WORK + "/tex/control-white.png")

waves = [(4, 0), (0, 8), (4, 8), (8, 0), (12, 0), (0, 16), (4, -8), (8, 16), (16, 0), (20, 0), (0, 24), (12, 8)]
y, x = np.mgrid[0:2048, 0:2048] / 2048.0
img = np.zeros((2048, 2048, 3)) + np.array([120.0, 100.0, 90.0])
for i, (kx, ky) in enumerate(waves):
    amp = np.array([14.0, 11.0, 9.0]) / (1 + i * 0.25)
    for c in range(3):
        img[..., c] += amp[c] * np.cos(2 * np.pi * (kx * x + ky * y) + 0.7 * i + 0.3 * c)
Image.fromarray(np.clip(np.rint(img), 0, 255).astype(np.uint8)).save(WORK + "/tex/control-lattice.png")
json.dump(dict(ktg=dict(truth, gradient=stops), lattice=[list(w) for w in waves]),
          open(WORK + "/tex/controls-truth.json", "w"), indent=1)
