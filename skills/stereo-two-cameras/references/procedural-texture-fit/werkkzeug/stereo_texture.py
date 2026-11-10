#!/usr/bin/env python3
"""A stereo pair of a flat textured surface with its relief: mostly sunk, a few pixels popped at most.

The picture is the surface. The height picture gives every point a place in depth through three
levels, as an artist sets them: the height that lies at the surface (no parallax), the black level
(the deepest point, SUNK pixels of parallax behind) and the white level (the highest point, POP
pixels in front; 0 keeps everything at the surface or behind it).
Each eye sees, along its own ray, the first point of the relief the ray meets (relief mapping,
Policarpo, Oliveira and Comba 2005; parallax occlusion mapping, Tatarchuk 2006), once per eye.
The lit colour is the same for both eyes.

Nothing is resized: the eyes have the texture's own size. The texture repeats, so each eye is
drawn over the tile plus the edge columns, and then the edge rule cuts the same columns from the
left and the right of both eyes: half the largest parallax per side, rounded up. No strip is left.

Usage: stereo_texture.py LIT.png HEIGHT.png OUT.pns --sunk N --pop M --black B --surface S --white W
  levels are height values 0..255; parallax in pixels of the picture itself
Writes OUT.pns: full side by side, left eye first, marked with sTER (see pns.py).
"""
import argparse
import math

import numpy as np
from PIL import Image

import pns

STEPS = 96


def parallax(h, a):
    """Height 0..255 to parallax in pixels: positive behind the surface, negative in front."""
    below = a.sunk * (a.surface - h) / max(a.surface - a.black, 1e-6)
    above = -a.pop * (h - a.surface) / max(a.white - a.surface, 1e-6)
    return np.clip(np.where(h <= a.surface, below, above), -a.pop, a.sunk).astype(np.float32)


def eye(colour, par, sign, a):
    """colour (H, W, 3), par (H, W) parallax. sign -1 for the left eye, +1 for the right."""
    h, w = par.shape
    cut = math.ceil(max(a.sunk, a.pop) / 2)
    xs = (np.arange(w + 2 * cut, dtype=np.float32) - cut)[None, :].repeat(h, 0)   # the tile plus the edge columns
    rows = np.arange(h)[:, None]

    def sample(t, x):
        x = np.mod(x, w)
        fl = np.floor(x)
        f = x - fl
        x0 = fl.astype(np.int32) % w
        x1 = (x0 + 1) % w
        if t.ndim == 3:
            f = f[..., None]
        return t[rows, x0] * (1 - f) + t[rows, x1] * f

    span = a.sunk + a.pop
    hit = np.zeros(xs.shape, bool)
    at = np.full(xs.shape, float(a.sunk), np.float32)
    prev = None
    for j in range(STEPS + 1):
        p = -a.pop + span * j / STEPS                     # the ray's depth at this step
        gap = sample(par, xs - sign * p / 2) - p          # the relief is still behind the ray while positive
        new = (~hit) & (gap <= 0)
        if prev is None:
            at = np.where(new, p, at)
        else:
            at = np.where(new, p - span / STEPS * gap / np.minimum(gap - prev, -1e-6), at)
        hit |= new
        prev = gap
    out = sample(colour, xs - sign * at / 2)
    return out[:, cut:cut + w]                             # the edge rule: the same columns cut from both eyes


def pair(colour, height, a):
    par = parallax(height, a)
    L, R = eye(colour, par, -1, a), eye(colour, par, +1, a)
    return [np.clip(np.rint(x), 0, 255).astype(np.uint8) for x in (L, R)]


def selftest():
    """A mark on a wide flat floor at each level must come out with that level's parallax."""
    a = argparse.Namespace(sunk=10.0, pop=3.0, black=0.0, surface=128.0, white=255.0)
    for level, want in ((0, 10.0), (128, 0.0), (255, -3.0)):
        hgt = np.full((4, 512), float(level), np.float32)
        col = np.zeros((4, 512, 3), np.float32)
        col[:, 250:262] = 255
        L, R = pair(col, hgt, a)
        centre = lambda e: float((e[0, :, 0].astype(np.float64) * np.arange(512)).sum() / e[0, :, 0].sum())
        got = centre(R) - centre(L)
        assert abs(got - want) < 0.05, (level, want, got)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("lit"); ap.add_argument("height"); ap.add_argument("out")
    for n, d in (("sunk", 10.0), ("pop", 0.0), ("black", 0.0), ("surface", 255.0), ("white", 255.0)):
        ap.add_argument("--" + n, type=float, default=d)
    a = ap.parse_args()
    selftest()
    colour = np.asarray(Image.open(a.lit).convert("RGB")).astype(np.float32)
    height = np.asarray(Image.open(a.height).convert("L")).astype(np.float32)
    assert colour.shape[:2] == height.shape
    L, R = pair(colour, height, a)
    print(a.out, pns.write(a.out, L, R), "cut per side before delivery:", math.ceil(max(a.sunk, a.pop) / 2))
