#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""contrast.py PICTURE X,Y,W,H [--scale S] [--control]: the contrast of the sentence on the keyboard's bar (row 71, step 4).

The bar is the keyboard's top strip (55 logical pixels from its top edge, from 68 px in, where the told sentence starts
after the input method button). Its background is the strip's median colour; glyph pixels are those more than 40 apart
from it in any channel, and the glyph colour is the median of the farthest seventh of them (the cores of the strokes, not
their antialiased edges). The ratio is WCAG 2.x's: (L1 + 0.05) / (L2 + 0.05) with relative luminance from linearised sRGB.
--control: draws text in (190,3,3) on (38,36,35) (milestone 1's colours, 2.36:1 by the formula) and in white on the same,
measures both and exits 1 when the measure is off by more than 0.15.
Prints JSON: background, glyph colour, glyph pixel count, ratio, and whether it reaches 4.5:1.
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def lum(c):
    c = np.array(c, float) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])

def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

def measure(img, frame, scale=1.0):
    a = np.asarray(img.convert("RGB")).astype(int)
    x, y, w, h = [int(round(v * scale)) for v in frame]
    strip = a[y + int(4 * scale):y + int(55 * scale), x + int(68 * scale):x + w - int(10 * scale)]
    px = strip.reshape(-1, 3)
    bg = np.median(px, axis=0)
    dist = np.abs(px - bg).max(axis=1)
    glyph = px[dist > 40]
    if len(glyph) < 30:
        return {"background": [int(v) for v in bg], "glyph_px": int(len(glyph)), "ratio": None, "readable": False}
    d = np.abs(glyph - bg).max(axis=1)
    core = glyph[d >= np.quantile(d, 6 / 7)]
    fg = np.median(core, axis=0)
    r = ratio(fg, bg)
    return {"background": [int(v) for v in bg], "glyph": [int(v) for v in fg], "glyph_px": int(len(glyph)),
            "ratio": round(r, 2), "readable": r >= 4.5}

def control():
    out = {}
    font = None
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"):
        try:
            font = ImageFont.truetype(f, 16)
            break
        except OSError:
            continue
    for name, fg in (("dark-red", (190, 3, 3)), ("white", (255, 255, 255))):
        img = Image.new("RGB", (1920, 378), (38, 36, 35))
        ImageDraw.Draw(img).text((74, 16), "Fcitx 5 does not answer. Keys type as they are.", fill=fg, font=font)
        m = measure(img, (0, 0, 1920, 378))
        out[name] = {"expected": round(ratio(fg, (38, 36, 35)), 2), "measured": m}
    ok = all(v["measured"]["ratio"] is not None and abs(v["measured"]["ratio"] - v["expected"]) <= 0.15 for v in out.values())
    out["ok"] = ok
    return out, ok

if __name__ == "__main__":
    if "--control" in sys.argv:
        res, ok = control()
        print(json.dumps(res))
        sys.exit(0 if ok else 1)
    scale = float(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 1.0
    frame = [float(v) for v in sys.argv[2].split(",")]
    print(json.dumps(measure(Image.open(sys.argv[1]), frame, scale)))
