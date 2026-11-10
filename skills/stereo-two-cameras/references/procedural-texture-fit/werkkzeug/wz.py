#!/usr/bin/env python3
"""Draw wzrender scripts in a container and return pictures.

Usage as a program: KTG_IMAGE=image wz.py BUILD_DIR SCRIPT.txt OUT.png
"""
import os
import struct
import subprocess
import sys

import numpy as np
from PIL import Image

_n = [0]


def render(build, script):
    """script: the text for wzrender. Returns an RGB uint8 array, or raises with wzrender's message."""
    _n[0] += 1
    cmd = ["docker", "run", "--rm", "-i", "--name", "x3d-473x-%d-%d" % (os.getpid(), _n[0]), "--network", "none",
           "--ulimit", "core=0", "--cpus", "1", "--user", "%d:%d" % (os.getuid(), os.getgid()),
           "-v", build + ":" + build + ":ro", os.environ["KTG_IMAGE"], build + "/wzrender"]
    r = subprocess.run(cmd, input=script.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError("wzrender: " + r.stderr.decode(errors="replace").strip()[:300])
    w, h = struct.unpack("<ii", r.stdout[:8])
    return np.frombuffer(r.stdout[8:], dtype=np.uint8).reshape(h, w, 3)


if __name__ == "__main__":
    Image.fromarray(render(sys.argv[1], open(sys.argv[2]).read())).save(sys.argv[3])
