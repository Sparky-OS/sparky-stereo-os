#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""scanout_eyes.py FRAME.ppm sbs|anaglyph|2d

Names what the frame Stereo KWin scans out (drm-grab) shows in the video area of a full-screen test client whose
left view is red and right view blue, the area being x 200..1700, y 100..800 of a 1920x1080 eye.

sbs (a 1920x1080 side by side (half) 3D mode: the left eye squeezed into the left half, the right eye into the
right half):
  STEREO   left eye red, right eye blue
  LEFT     the left view in both eyes (the scene drawn once, not once per eye)
  PACKED   both views side by side in each eye, the same in both (the area shown as 2D)
  OTHER    anything else
anaglyph (the anaglyph (modern) twin): the same four names, read from the filter's colours.
2d (a plain mode, one picture): LEFT (the left view), PACKED or OTHER.
Prints the verdict and the shares; exit 0 for STEREO (sbs) or LEFT (2d).
"""
import sys

import numpy as np
from PIL import Image


def shares(px):
    r, g, b = px[..., 0].astype(int), px[..., 1].astype(int), px[..., 2].astype(int)
    n = max(1, px.shape[0] * px.shape[1])
    return ((r > 150) & (g < 80) & (b < 80)).sum() / n, ((b > 150) & (r < 80) & (g < 80)).sum() / n


def name(area):
    """the colours of one eye's area: (red, blue, red share of its left half, blue share of its right half)"""
    r, b = shares(area)
    w = area.shape[1]
    r1, _ = shares(area[:, :w // 2])
    _, b2 = shares(area[:, w // 2:])
    return r, b, r1, b2


def main():
    img = np.asarray(Image.open(sys.argv[1]).convert("RGB"))
    mode = sys.argv[2]
    H, W, _ = img.shape
    if mode == "sbs":
        half = W // 2
        y0, y1 = 100 * H // 1080, 800 * H // 1080
        x0, x1 = 200 * half // 1920, 1700 * half // 1920
        left = name(img[y0:y1, x0:x1])
        right = name(img[y0:y1, half + x0:half + x1])
        if left[0] > 0.9 and right[1] > 0.9:
            verdict = "STEREO"
        elif left[0] > 0.9 and right[0] > 0.9:
            verdict = "LEFT"
        elif left[2] > 0.9 and left[3] > 0.9 and right[2] > 0.9 and right[3] > 0.9:
            verdict = "PACKED"
        else:
            verdict = "OTHER"
        print(f"{verdict} frame {W}x{H} left eye red {left[0]:.3f} blue {left[1]:.3f} halves {left[2]:.2f}/{left[3]:.2f} "
              f"right eye red {right[0]:.3f} blue {right[1]:.3f} halves {right[2]:.2f}/{right[3]:.2f}")
        return 0 if verdict == "STEREO" else 1
    y0, y1 = 100 * H // 1080, 800 * H // 1080
    x0, x1 = 200 * W // 1920, 1700 * W // 1920
    if mode == "anaglyph":
        # KWin's anaglyph (modern) filter of the two eyes, measured on this rig (8-bit grab of the scanout):
        # left eye red and right eye blue give (170, 0, 255); red in both eyes (169, 154, 0); blue in both
        # (111, 0, 255), the colours of the undeclared control's two halves
        area = img[y0:y1, x0:x1].astype(float)
        w = area.shape[1]
        a = area[:, :w * 7 // 15].reshape(-1, 3).mean(0)
        b = area[:, w * 8 // 15:].reshape(-1, 3).mean(0)
        near = lambda c, ref: max(abs(c - np.array(ref))) < 25
        if near(a, (170, 0, 255)) and near(b, (170, 0, 255)):
            verdict = "STEREO"
        elif near(a, (169, 154, 0)) and near(b, (169, 154, 0)):
            verdict = "LEFT"
        elif near(a, (169, 154, 0)) and near(b, (111, 0, 255)):
            verdict = "PACKED"
        else:
            verdict = "OTHER"
        print(f"{verdict} frame {W}x{H} anaglyph, mean of the area's left part {a.round(1).tolist()} right part {b.round(1).tolist()}")
        return 0 if verdict == "STEREO" else 1
    one = name(img[y0:y1, x0:x1])
    if one[0] > 0.9:
        verdict = "LEFT"
    elif one[2] > 0.9 and one[3] > 0.9:
        verdict = "PACKED"
    else:
        verdict = "OTHER"
    print(f"{verdict} frame {W}x{H} red {one[0]:.3f} blue {one[1]:.3f} halves {one[2]:.2f}/{one[3]:.2f}")
    return 0 if verdict == "LEFT" else 1


if __name__ == "__main__":
    sys.exit(main())
