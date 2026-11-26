#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# contrast_over_wallpaper.py COLORS WALLPAPER SURFACE_RGB LEVELS_JSON: every Foreground* of a Plasma style's Window, View, Button,
# Header and Tooltip groups against every translucent surface it can sit on, as seen over the wallpaper
# (alpha * surface + (1 - alpha) * wallpaper, the surface's region of the screen); prints the worst (1st percentile)
# contrast per colour and surface, and the surface that is worst for each colour. LEVELS_JSON maps surface -> alpha8.
import configparser
import json
import sys

import numpy as np
from PIL import Image

colors_path, wall_path, surface_rgb, levels = sys.argv[1], sys.argv[2], json.loads(sys.argv[3]), json.loads(sys.argv[4])


def lum(rgb):
    c = np.asarray(rgb, float) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


if wall_path in ("black", "white"):
    w = np.full((1080, 1920, 3), 0 if wall_path == "black" else 255, float)
else:
    w = np.asarray(Image.open(wall_path).convert("RGB").resize((1920, 1080), Image.BILINEAR), float)
regions = {"panel": w[-56:].reshape(-1, 3), "top": w[:26].reshape(-1, 3)}
anywhere = w[::4, ::4].reshape(-1, 3)
cp = configparser.ConfigParser(interpolation=None)
cp.optionxform = str
cp.read(colors_path)
groups = {"Window": ["panel", "top", "dialog", "widget", "translucent"], "View": ["dialog", "widget", "translucent"],
          "Button": ["panel", "top", "dialog"], "Header": ["dialog"], "Tooltip": ["tooltip"]}
out = []
for g, surfaces in groups.items():
    sec = f"Colors:{g}"
    if sec not in cp:
        continue
    for key, val in cp[sec].items():
        if not key.startswith("Foreground"):
            continue
        rgb = [int(x) for x in val.split(",")[:3]]
        lt = float(lum(rgb))
        worst = None
        for s in surfaces:
            if s not in levels:
                continue
            a = levels[s] / 255
            bg = a * np.asarray(surface_rgb[s], float) + (1 - a) * regions.get(s, anywhere)
            lb = lum(bg)
            c = (np.maximum(lb, lt) + 0.05) / (np.minimum(lb, lt) + 0.05)
            v = float(np.percentile(c, 1))
            if worst is None or v < worst[0]:
                worst = (v, s)
        out.append({"group": g, "key": key, "rgb": rgb, "worst": round(worst[0], 2), "surface": worst[1]})
print(json.dumps(out))
