#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read one rig capture of ORDER 577: Stereo KWin's ScreenShot2 picture, both eyes side by side when a stereo surface
is on screen (each eye the output's size), one picture otherwise.

In each eye the video is found by its background colour (the left eye's view red, the right eye's blue, a 2D picture
green), cut to that area, and its circle and square measured (measure.shapes): 1.0 is the right shape.
Usage: analyze-capture.py CAPTURE.png OUTPUT_WIDTH  -> one JSON line
"""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure import shapes


def area(eye):
    a = eye.astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    found = {}
    for name, m in (("red", (r > 50) & (g < 40) & (b < 40)), ("blue", (b > 50) & (r < 40) & (g < 40)),
                    ("green", (g > 40) & (r < 40) & (b < 40))):
        if m.sum() > 2000:
            # the video's own rows and columns are mostly its background; a stray pixel of the colour elsewhere
            # (a window icon, a menu) is not
            rows, cols = m.sum(axis=1), m.sum(axis=0)
            ys = np.where(rows >= 0.3 * rows.max())[0]
            xs = np.where(cols >= 0.3 * cols.max())[0]
            found[name] = (int(m.sum()), xs.min(), xs.max() + 1, ys.min(), ys.max() + 1)
    if not found:
        # interleaved views in 4:2:0 share each chroma sample, so their colours mix: take any lit, non-white area
        m = (a.max(axis=2) > 30) & ~((r > 170) & (g > 170) & (b > 170))
        if m.sum() > 2000:
            rows, cols = m.sum(axis=1), m.sum(axis=0)
            ys = np.where(rows >= 0.3 * rows.max())[0]
            xs = np.where(cols >= 0.3 * cols.max())[0]
            found["mixed"] = (int(m.sum()), xs.min(), xs.max() + 1, ys.min(), ys.max() + 1)
    if not found:
        return None, None
    name = max(found, key=lambda k: found[k][0])
    _, x0, x1, y0, y1 = found[name]
    return name, eye[y0:y1, x0:x1]


def main():
    path, ow = sys.argv[1], int(sys.argv[2])
    px = np.asarray(Image.open(path).convert("RGB"))
    h, w = px.shape[:2]
    eyes = [px[:, :ow], px[:, ow:2 * ow]] if w >= 2 * ow else [px]
    rec = {"capture": os.path.basename(os.path.dirname(path)), "width": w, "height": h, "stereo_capture": w >= 2 * ow}
    for i, eye in enumerate(eyes):
        colour, video = area(eye)
        key = "left" if i == 0 else "right"
        if video is None:
            rec[key] = {"colour": None}
            continue
        m = shapes(video)
        rec[key] = {"colour": colour, "video_size": [int(video.shape[1]), int(video.shape[0])],
                    "circle": m["circle"], "square": m["square"]}
    print(json.dumps(rec))


if __name__ == "__main__":
    main()
