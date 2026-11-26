#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""check_output.py READBACK_DIR PATCHES.txt [--eyes two|one] [--tol T] [--min-levels N]

Reads the frame an output got, as the virtual backend of the rig's private KWin wrote it (OUTPUT.rgba: a text line
"WIDTH HEIGHT TYPE FOURCC", then four samples a pixel, the top row first), and checks the area of glarea-stereo-test
in it: the buffer's format and sample type, the eye tag of each eye (with --eyes two the output is in a 3D mode and the
backend wrote the right eye's buffer too, OUTPUT-right.rgba: a virtual output packs nothing, each eye is a whole
picture), each patch against the
values PATCHES.txt expects in the output's own encoding (within --tol, default 0.004, about four codes of 10 bits), and
the number of different values the ramp holds in each eye (--min-levels, default 2: more than 8 bits would give).
Prints one line per check and exits 1 if any fails.
"""
import sys
from pathlib import Path

import numpy as np

FRAME = 4


def main():
    args = sys.argv[1:]
    folder, patches_file = Path(args[0]), args[1]
    eyes_mode = args[args.index("--eyes") + 1] if "--eyes" in args else "one"
    tol = float(args[args.index("--tol") + 1]) if "--tol" in args else 0.004
    min_levels = int(args[args.index("--min-levels") + 1]) if "--min-levels" in args else 2
    ok = True

    def row(passed, text):
        nonlocal ok
        ok = ok and passed
        print(("PASS " if passed else "FAIL ") + text)

    def frame(path):
        raw = path.read_bytes()
        header, data = raw.split(b"\n", 1)
        w, h, kind, fourcc = header.decode().split()
        w, h = int(w), int(h)
        # the first row is the top of the picture: KWin draws an output's buffer in the buffer's own row order
        a = np.frombuffer(data, np.float32 if kind == "float32" else np.uint8).reshape(h, w, 4).astype(np.float64)
        if kind != "float32":
            a = a / 255.0
        row(True, "%s: a frame of %dx%d, buffer format %s, read as %s" % (path.stem, w, h, fourcc, kind))
        # a small picture of the frame beside the check, to look at (the values as they are, cut to 8 bits: not evidence of depth)
        try:
            from PIL import Image
            Image.fromarray((np.clip(a[:, :, :3], 0, 1) * 255 + 0.5).astype(np.uint8)).save(folder / (path.stem + "-as-written-8bit.png"))
        except Exception:
            pass
        return a

    left = sorted(p for p in folder.glob("*.rgba") if not p.stem.endswith("-right"))
    right = sorted(folder.glob("*-right.rgba"))
    if not left:
        row(False, "the output's frame was written")
        sys.exit(1)
    halves = [("left" if eyes_mode == "two" else "one", frame(left[0]))]
    if eyes_mode == "two":
        if not right:
            row(False, "the right eye's frame was written")
        else:
            halves.append(("right", frame(right[0])))
    patches = []
    for line in open(patches_file):
        name, _, want = line.split()
        patches.append((name, [float(v) for v in want.split(",")]))
    for eye, img in halves:
        r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        frame = (g > r + 0.15) & (g > b + 0.15)
        if not frame.any():
            row(False, "%s: the area's frame is found" % eye)
            continue
        ys, xs = np.nonzero(frame)
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        aw, ah = x1 - x0, y1 - y0
        tag = ah // 6
        t = img[y1 - 1 - (FRAME + tag // 2), x0 + FRAME + tag // 2, :3]
        seen = "red" if t[0] > t[2] + 0.1 else "blue" if t[2] > t[0] + 0.1 else "white"
        want = {"left": "red", "right": "blue", "one": "red"}[eye]
        row(seen == want, "%s eye: area %dx%d at %d,%d, eye tag %s (%s wanted, sample %s)" % (eye, aw, ah, x0, y0, seen, want, np.round(t, 4).tolist()))
        n = len(patches)
        for i, (name, wanted) in enumerate(patches):
            px0 = FRAME + tag + i * (aw - 2 * FRAME - tag) // n
            px1 = FRAME + tag + (i + 1) * (aw - 2 * FRAME - tag) // n
            got = img[y0 + 3 * ah // 4, x0 + (px0 + px1) // 2, :3]
            d = float(np.abs(got - np.array(wanted)).max())
            row(d <= tol, "%s eye: patch %s holds %s, expected %s (off by %.4f)" % (eye, name, np.round(got, 5).tolist(), wanted, d))
        # the ramp's own columns: 256 steps of (area width - frame) // 256 pixels each
        step = max((aw - 2 * FRAME) // 256, 1)
        ramp = img[y0 + ah // 4, x0 + FRAME: x0 + FRAME + 256 * step, 0]
        levels = len(np.unique(ramp))
        row(levels >= min_levels, "%s eye: the ramp holds %d different values in the output's buffer (%.6f to %.6f)" % (eye, levels, ramp.min(), ramp.max()))
    sys.exit(0 if ok else 1)


main()
