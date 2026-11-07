#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""analyze-fsphase.py RUN: the eye stream a frame sequential twin scans out from its first frame after the mode set.
Reads RUN/planelog-<fs-left|fs-right>-<disable|enable>-<n>.txt (drm-planelog: ms, framebuffer, its width, SRC_X, SRC_W).
The packed frame holds the left view in its left half with the swap off and the right view with the swap on (checked by the
grab of the first repetition); SRC_X 0 shows the left half, SRC_X 1920 the right half."""
import glob, os, re, sys
run = sys.argv[1]
summary = {}
for path in sorted(glob.glob(os.path.join(run, "planelog-*.txt"))):
    tag = os.path.basename(path)[len("planelog-"):-4]
    twin, swap, rep = tag.rsplit("-", 2)
    rows = [tuple(int(v) for v in m.groups()) for m in re.finditer(r"^(\d+) fb (\d+) width (-?\d+) src_x (-?\d+) src_w (-?\d+)", open(path).read(), re.M)]
    stream = [(t, x) for t, fb, w, x, sw in rows if w == 3840]
    eyes = []
    for t, x in stream:
        half = "L" if x == 0 else "R"
        eye = {"disable": {"L": "L", "R": "R"}, "enable": {"L": "R", "R": "L"}}[swap][half]
        if not eyes or eyes[-1][1] != eye:
            eyes.append((t, eye))
    seq = "".join(e for _, e in eyes)
    summary.setdefault((twin, swap), []).append(seq)
    print("%-26s first eye %s, %d eye changes, sequence %s" % (tag, seq[:1], len(seq) - 1, seq[:24]))
print()
for (twin, swap), seqs in sorted(summary.items()):
    first = {s[:1] for s in seqs}
    alt = all(all(a != b for a, b in zip(s, s[1:])) for s in seqs)
    print("STEREO|info|fsphase/%s swap %s|first eye %s in %d of %d runs, strictly alternating run list %s"
          % (twin, swap, "/".join(sorted(first)), sum(s[:1] == sorted(first)[0] for s in seqs), len(seqs), alt))
