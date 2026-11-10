#!/usr/bin/env python3
"""A desktop panel with a stereo wood texture: the wood's relief sunk below the panel's own plane.

The panel is a flat element drawn once per eye. Its plane has zero parallax; the wood's grooves and
the joint between planks lie behind it, each eye's texture shifted by that depth; the icons and the
clock's text sit on the panel's plane and are the same in both eyes. No 3D scene.
The wood is used at the size it was drawn (a 256 pixel tile, 48 of its rows), never resized, and
it repeats along the bar, so the shift uncovers nothing at the screen's edges and no column is lost.

Usage: panel.py WOOD_LIT.png WOOD_HEIGHT.png OUT_PREFIX [SUNK_PIXELS]
Writes OUT_PREFIX-2D.png and OUT_PREFIX-3D.pns (full side by side, left eye first, marked).
"""
import argparse
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import pns
import stereo_texture

W, H, BAR, ROW = 1920, 1080, 48, 60


def desktop(bar):
    y = np.linspace(0, 1, H)[:, None, None]
    bg = (np.array([38, 62, 92]) * (1 - y) + np.array([92, 120, 150]) * y) * np.ones((H, W, 1))
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))
    img.paste(Image.fromarray(np.clip(np.rint(bar), 0, 255).astype(np.uint8)), (0, H - BAR))
    d = ImageDraw.Draw(img)
    d.line([(0, H - BAR), (W, H - BAR)], fill=(20, 12, 8), width=1)
    cols = [(240, 240, 240), (86, 156, 214), (240, 180, 60), (120, 200, 120), (220, 90, 90)]
    for i, c in enumerate(cols):                       # flat icons on the panel's plane
        x = 14 + i * 52
        d.rounded_rectangle([x, H - BAR + 8, x + 32, H - 8], radius=6, fill=c)
        d.ellipse([x + 9, H - BAR + 17, x + 23, H - 17], fill=(30, 30, 30))
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    d.text((W - 86, H - BAR + 12), "21:10", font=font, fill=(250, 244, 230))
    return np.asarray(img)


def main():
    lit, height, prefix = sys.argv[1:4]
    sunk = float(sys.argv[4]) if len(sys.argv) > 4 else 4.0   # the deepest groove, in pixels between the eyes
    stereo_texture.selftest()
    c = np.asarray(Image.open(lit).convert("RGB")).astype(np.float32)[ROW:ROW + BAR]
    h = np.asarray(Image.open(height).convert("L")).astype(np.float32)[ROW:ROW + BAR]
    a = argparse.Namespace(sunk=sunk, pop=0.0, black=0.0, surface=255.0, white=255.0)
    along = lambda s: np.concatenate([s] * (W // s.shape[1] + 1), 1)[:, :W]
    left, right = (along(e) for e in stereo_texture.pair(c, h, a))
    Image.fromarray(desktop(along(c))).save(prefix + "-2D.png")
    print(prefix, pns.write(prefix + "-3D.pns", desktop(left), desktop(right)))


if __name__ == "__main__":
    main()
