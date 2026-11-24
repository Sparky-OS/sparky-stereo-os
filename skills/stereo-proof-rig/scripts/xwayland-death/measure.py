#!/usr/bin/env python3
"""Each window's opacity on the captures of one session (white windows over KWin's black desktop).

Usage: measure.py OUT    writes OUT/rows.json and prints one line per capture; exit 0 always (the verdict is a field).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

# frame geometry set by session.sh (x, y, 500x320); the patch is the middle of the client area
WINDOWS = {"wl-a": (40, 40), "wl-b": (640, 40), "x11-a": (40, 420)}
SELECTED = {"0-x11-selected": "x11-a", "1-wl-a-selected": "wl-a", "2-wl-b-selected": "wl-b"}


def patch(img, x, y, half=20):
    return float(np.median(img[y - half:y + half, x - half:x + half, 0]))


def main(out):
    rows = []
    for name, selected in SELECTED.items():
        path = os.path.join(out, name + ".png")
        if not os.path.exists(path):
            rows.append({"capture": name, "error": "missing"})
            continue
        img = np.asarray(Image.open(path).convert("RGB"))
        h, w = img.shape[:2]
        row = {"capture": name, "size": [w, h], "selected": selected,
               "background": patch(img, w - 60, h - 40) / 255.0}
        for win, (x, y) in WINDOWS.items():
            row[win] = round(patch(img, x + 250, y + 180) / 255.0, 3)
        row["selected_opacity"] = row[selected]
        row["selected_opaque"] = row[selected] >= 0.99
        others = [row[k] for k in ("wl-a", "wl-b") if k != selected and row[k] > 0.05]
        row["inactive_wayland"] = others
        rows.append(row)
        print(json.dumps(row))
    with open(os.path.join(out, "rows.json"), "w") as f:
        json.dump(rows, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
