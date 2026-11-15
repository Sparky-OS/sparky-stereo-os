#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# layout.py ART_DIR OUTDIR W H [POPPED SUNK]: the loading screen's static parts where Splash.qml places them on an output of W x H device
# pixels (the same sums), each part's mask from its picture's alpha, and the parallax predicted from the person's limits (pixels of
# a view 1920 wide; KWin's defaults 4 and 10 on the rig's virtual output, which reports no size, so the display factor is 1)
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter
art, out, W, H = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
P = float(sys.argv[5]) if len(sys.argv) > 5 else 4.0
S = float(sys.argv[6]) if len(sys.argv) > 6 else 10.0
os.makedirs(out, exist_ok=True)
def place(name, img, x, y, w, h, depth):
    a = img.split()[3].resize((round(w), round(h)), Image.LANCZOS)
    top = a.getextrema()[1] * 0.6  # the wordmark is drawn with alpha 101 at most
    a = a.point(lambda v: 255 if v > top else 0).filter(ImageFilter.MinFilter(5))
    m = Image.new("L", (W, H)); m.paste(a, (round(x), round(y)))
    arr = np.asarray(m); ys, xs = np.nonzero(arr)
    box = [int(max(xs.min() - 4, 20)), int(max(ys.min() - 4, 0)), int(min(xs.max() + 5, W - 20)), int(min(ys.max() + 5, H))]
    path = os.path.join(out, name + "-mask.png"); m.save(path)
    lim = P if depth >= 0 else S
    pred = math.copysign(math.floor(abs(depth * lim * W / 1920) + 0.5), depth) if depth else 0
    return {"name": name, "box": box, "mask": path, "predicted": int(pred), "pixels": int((arr > 0).sum())}
logo = Image.open(os.path.join(art, "logo.png")).convert("RGBA")
lh = min(W, H) * 0.7; lw = logo.width * lh / logo.height
lx = W / 2 - lw / 2 + lw * 0.092
wm = Image.open(os.path.join(art, "wordmark.png")).convert("RGBA")
fit = min(1, lw / wm.width * 0.7); ww, wh = wm.width * fit, wm.height * fit
items = [place("swirl", logo, lx, 0, lw, lh, 0.5), place("wordmark", wm, (W - ww) / 2, H - H * 0.092 - wh, ww, wh, 1.0)]
json.dump({"W": W, "H": H, "popped": P, "sunk": S, "items": items}, open(os.path.join(out, "layout.json"), "w"), indent=1)
print(json.dumps([(i["name"], i["box"], i["predicted"], i["pixels"]) for i in items]))
