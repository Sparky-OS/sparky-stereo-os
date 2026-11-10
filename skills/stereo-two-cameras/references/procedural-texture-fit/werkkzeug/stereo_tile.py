#!/usr/bin/env python3
"""A stereo pair of a textured flat surface whose relief is sunk below it.

The surface lies in the screen plane (zero parallax). The height picture gives every point a
depth behind it: white is the surface, black the deepest point. Each eye looks through the
surface along its own ray and sees the first point of the relief the ray meets, as in relief
mapping (Policarpo, Oliveira and Comba 2005: a linear search along the ray, then a refinement)
and parallax occlusion mapping (Tatarchuk 2006), done once per eye. The lit colour is the same
for both eyes: the light is baked, only the position differs.

Usage: stereo_tile.py LIT.png HEIGHT.png OUT_PREFIX [--popped] [--flat]
  --popped  the wrong case as a control: the same relief standing in front of the surface
  --flat    no relief: both eyes see the same picture (the tile as a plain texture)
Writes OUT_PREFIX-sbs-3840x1080.png (full side by side, left eye first, 1920 x 1080 per eye),
OUT_PREFIX-sbs-tile.png (the tile only, 1024 x 1024 per eye) and OUT_PREFIX-anaglyph.png (red-cyan).
"""
import sys

import numpy as np
from PIL import Image

EYE_W, EYE_H, TILE = 1920, 1080, 1024
SUNK_PX = 10.0          # the deepest point's parallax between the eyes, in pixels of the 1920 wide frame
# the viewing setup the numbers are stated for
SCREEN_M, DISTANCE_M, EYES_M = 1.21, 2.5, 0.065


def march(colour, depth, sign, popped):
    """colour (H, W, 3), depth (H, W) in 0..1. sign -1 for the left eye, +1 for the right."""
    h, w = depth.shape
    k = SUNK_PX / 2.0
    xs = np.arange(w, dtype=np.float32)[None, :].repeat(h, 0)
    rows = np.arange(h)[:, None]

    def sample(a, x):
        x = np.mod(x, w)
        x0 = np.floor(x).astype(np.int32)
        f = (x - x0)[..., None] if a.ndim == 3 else (x - x0)
        x1 = (x0 + 1) % w
        return a[rows, x0] * (1 - f) + a[rows, x1] * f

    steps = 64
    hit = np.zeros((h, w), bool)
    t_hit = np.ones((h, w), np.float32)
    prev_gap = None
    for i in range(steps + 1):
        t = i / steps
        if popped:
            # the ray comes down from the top of the relief (in front of the screen) to the surface
            tt = 1 - t
            x = xs + sign * k * tt
            gap = tt - (1 - sample(depth, x))        # above the relief while positive
        else:
            x = xs - sign * k * t
            gap = sample(depth, x) - t                # above the relief while positive
        new = (~hit) & (gap <= 0)
        if prev_gap is not None:
            frac = np.where(new, prev_gap / np.maximum(prev_gap - gap, 1e-6), 0)
            t_hit = np.where(new, (i - 1 + frac) / steps, t_hit)
        else:
            t_hit = np.where(new, 0.0, t_hit)
        hit |= new
        prev_gap = gap
    if popped:
        x = xs + sign * k * (1 - t_hit)
    else:
        x = xs - sign * k * t_hit
    return sample(colour, x)


def frame(tile_img):
    """The tile in a 1920 x 1080 frame: a quiet grey surround at the screen plane and a dark outline."""
    rng = np.random.default_rng(7)
    bg = 96 + rng.integers(-6, 7, (EYE_H // 4, EYE_W // 4, 1)).repeat(4, 0).repeat(4, 1).repeat(3, 2)
    out = bg.astype(np.float32)
    y0, x0 = (EYE_H - TILE) // 2, (EYE_W - TILE) // 2
    out[y0 - 4:y0 + TILE + 4, x0 - 4:x0 + TILE + 4] = 24
    out[y0:y0 + TILE, x0:x0 + TILE] = tile_img
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def pair(lit, height, popped=False, flat=False):
    colour = np.asarray(Image.open(lit).convert("RGB").resize((TILE, TILE), Image.BICUBIC)).astype(np.float32)
    hgt = np.asarray(Image.open(height).convert("L").resize((TILE, TILE), Image.BICUBIC)).astype(np.float32) / 255.0
    depth = np.zeros_like(hgt) if flat else 1.0 - hgt
    return march(colour, depth, -1, popped), march(colour, depth, +1, popped)


def write(left, right, prefix):
    L, R = frame(left), frame(right)
    Image.fromarray(np.concatenate([L, R], 1)).save(prefix + "-sbs-3840x1080.png")
    Image.fromarray(np.concatenate([np.clip(np.rint(left), 0, 255).astype(np.uint8),
                                    np.clip(np.rint(right), 0, 255).astype(np.uint8)], 1)).save(prefix + "-sbs-tile.png")
    y0, x0 = (EYE_H - TILE) // 2 - 28, (EYE_W - TILE) // 2 - 28
    a = np.stack([L[..., 0], R[..., 1], R[..., 2]], -1)[y0:y0 + TILE + 56, x0:x0 + TILE + 56]
    Image.fromarray(a).save(prefix + "-anaglyph.png")


def setup_text():
    px = SCREEN_M / EYE_W
    p = SUNK_PX * px
    z = DISTANCE_M * p / (EYES_M - p)
    return ("a 1920 pixel wide picture on a screen %.2f m wide, seen from %.1f m with eyes %.0f mm apart: "
            "the deepest point has %g pixels of parallax between the eyes (%.1f mm on the screen) and is seen about %.2f m "
            "behind the screen; the surface itself has none" % (SCREEN_M, DISTANCE_M, EYES_M * 1000, SUNK_PX, p * 1000, z))


def selftest():
    """A mark on the floor of a wide pit must sit further left in the left eye than in the right, by
    the full parallax; with the same relief popped, a mark on its top must sit the other way round."""
    c = np.zeros((64, 256, 3), np.float32)
    c[:, 120:130] = 255
    d = np.zeros((64, 256), np.float32)
    d[:, 40:220] = 1
    centre = lambda img: float((img[32, :, 0] > 127).nonzero()[0].mean())
    l, r = march(c, d, -1, False), march(c, d, +1, False)
    assert centre(l) < centre(r), "sunk relief must have uncrossed parallax"
    assert abs((centre(r) - centre(l)) - SUNK_PX) < 1.0, (centre(l), centre(r))
    l, r = march(c, 1 - d, -1, True), march(c, 1 - d, +1, True)     # the same band, now a plateau in front
    assert centre(l) > centre(r), "popped relief must have crossed parallax"
    flat = np.zeros_like(d)
    assert np.array_equal(march(c, flat, -1, False), march(c, flat, +1, False)), "a flat surface has no parallax"
    return True


if __name__ == "__main__":
    if sys.argv[1] == "--setup":
        print(setup_text())
        sys.exit(0)
    selftest()
    lit, height, prefix = sys.argv[1:4]
    l, r = pair(lit, height, popped="--popped" in sys.argv, flat="--flat" in sys.argv)
    write(l, r, prefix)
