#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# svg_render.py STYLE_DIR [STYLE_DIR ...]: render every frame centre a Plasma style draws its surfaces with, the way
# KSvg does (QSvgRenderer.render(painter, elementId, bounds)), onto a transparent image, and print the alpha it gives:
# mean, minimum, maximum and the alpha by row (the panel's profile across its thickness), and the mean colour where
# drawn (unpremultiplied). KSvg falls back from translucent/, solid/ and opaque/ to the plain file when a style has
# no such file, so each request is resolved the same way and the file actually read is named.
import json
import os
import sys

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QGuiApplication, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer

FILES = ["widgets/panel-background", "dialogs/background", "widgets/tooltip", "widgets/background",
         "widgets/translucentbackground"]
FOLDERS = ["", "translucent/", "solid/", "opaque/"]
PREFIXES = {"widgets/panel-background": ["south", "north", "east", "west", ""]}


def resolve(style, folder, name):
    for f in ([folder] if folder else []) + [""]:
        for ext in (".svg", ".svgz"):
            p = os.path.join(style, f + name + ext)
            if os.path.exists(p):
                return p
    return None


def measure(renderer, ident, w, h):
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    renderer.render(p, ident, QRectF(0, 0, w, h))
    p.end()
    img = img.convertToFormat(QImage.Format.Format_ARGB32)
    rows = []
    total_a = 0
    rgb = [0, 0, 0]
    amin, amax = 255, 0
    for y in range(h):
        ra = 0
        for x in range(w):
            c = img.pixelColor(x, y)
            a = c.alpha()
            ra += a
            total_a += a
            amin, amax = min(amin, a), max(amax, a)
            rgb[0] += c.red() * a
            rgb[1] += c.green() * a
            rgb[2] += c.blue() * a
        rows.append(round(ra / w / 255, 4))
    n = w * h
    colour = [round(v / total_a) for v in rgb] if total_a else None
    return {"alpha_mean": round(total_a / n / 255, 4), "alpha_min": round(amin / 255, 4),
            "alpha_max": round(amax / 255, 4), "rows": rows, "colour": colour}


def main():
    app = QGuiApplication(sys.argv[:1])
    for style in sys.argv[1:]:
        for folder in FOLDERS:
            for name in FILES:
                path = resolve(style, folder, name)
                if path is None:
                    continue
                r = QSvgRenderer(path)
                for prefix in PREFIXES.get(name, [""]):
                    ident = f"{prefix}-center" if prefix else "center"
                    if not r.elementExists(ident):
                        continue
                    b = r.boundsOnElement(ident)
                    # the panel's thickness in the rig (44 logical px, the default bottom panel) across, the length along;
                    # other surfaces at a square of 64
                    if name == "widgets/panel-background" and prefix in ("south", "north", ""):
                        w, h = 64, 44
                    elif name == "widgets/panel-background":
                        w, h = 44, 64
                    else:
                        w, h = 64, 64
                    m = measure(r, ident, w, h)
                    print(json.dumps({"style": os.path.basename(style.rstrip("/")), "request": folder + name,
                                      "file": os.path.relpath(path, style), "id": ident,
                                      "bounds": [round(b.x(), 2), round(b.y(), 2), round(b.width(), 2), round(b.height(), 2)],
                                      "size": [w, h], **m}))
    del app


main()
