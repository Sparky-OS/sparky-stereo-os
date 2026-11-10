#!/usr/bin/env python3
"""A desktop panel with a stereo wood texture: the wood's relief sunk below the panel's own plane.

The panel is a flat element drawn once per eye. Its plane has zero parallax; the wood's grooves and
the joint between planks lie behind it, each eye's texture shifted by that depth; the icons and the
clock's text sit on the panel's plane and are the same in both eyes. No 3D scene.

Usage: panel.py WOOD_LIT.png WOOD_HEIGHT.png OUT_PREFIX [--popped]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import stereo_tile

W, H, BAR = 1920, 1080, 48
stereo_tile.SUNK_PX = 4.0          # the deepest groove: 4 pixels between the eyes at 1920 wide (the lane's choice)


def strip(path, mode):
    t = Image.open(path).convert(mode).resize((192, 192), Image.LANCZOS)
    a = np.asarray(t).astype(np.float32)
    a = np.concatenate([a] * 10, 1)[60:60 + BAR, :W]
    return a


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
    popped = "--popped" in sys.argv
    stereo_tile.selftest()
    c, h = strip(lit, "RGB"), strip(height, "L") / 255.0
    d = 1 - h
    left = stereo_tile.march(c, d, -1, popped)
    right = stereo_tile.march(c, d, +1, popped)
    L, R = desktop(left), desktop(right)
    Image.fromarray(desktop(c)).save(prefix + "-2D.png")
    Image.fromarray(np.concatenate([L, R], 1)).save(prefix + "-sbs-3840x1080.png")
    a = np.stack([L[..., 0], R[..., 1], R[..., 2]], -1)
    Image.fromarray(a).save(prefix + "-anaglyph.png")
    # the panel alone, three times enlarged, for a close look
    z = Image.fromarray(a[H - BAR - 8:, :640]).resize((1920, (BAR + 8) * 3), Image.NEAREST)
    z.save(prefix + "-anaglyph-panel-enlarged.png")


if __name__ == "__main__":
    main()
