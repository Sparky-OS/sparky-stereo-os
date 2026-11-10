#!/usr/bin/env python3
"""A small offline picture of a room corner, to look at textures in 2D and in stereo.

Not a renderer that ships and not DPFR: planes and one cylinder, one ray per pixel, the
relief found per eye by a search along the ray below each surface (relief mapping, Policarpo,
Oliveira and Comba 2005; parallax occlusion mapping, Tatarchuk 2006).

The scene: a floor of stone tiles, a brick wall at the back, a plaster wall on the left and a
bark post, seen from a standing person's eye height, looking down into the corner.
Stereo: two cameras with parallel axes, 65 mm apart, each with an off-axis projection so that
the plane of zero parallax lies at the nearest thing in the picture; everything is at the
screen or behind it.

Usage: scene.py TEXDIR OUTDIR
  TEXDIR holds NAME.png (lit) and NAME-height.png for tiles, brick, plaster, bark (512 x 512),
  and photo-NAME.png (the photographs, 2048 x 2048, which repeat without a seam).
"""
import sys

import numpy as np
from PIL import Image

TEX, OUT = sys.argv[1], sys.argv[2]
W, H = 1920, 1080
HFOV = np.radians(50.0)
F = (W / 2) / np.tan(HFOV / 2)
EYE = np.array([0.0, 1.5, 0.0])
PITCH = np.radians(33.0)
SEP = 0.065
# name: (size of one 512 pixel tile in metres, depth of the relief in metres, shade)
SURF = {"tiles": (0.60, 0.006, 1.00), "brick": (0.50, 0.015, 0.92), "plaster": (0.50, 0.004, 0.78), "bark": (0.30, 0.025, 1.00)}
BACK_Z, LEFT_X = 2.0, -1.0
POST = (0.50, 1.45, 0.9 / (2 * np.pi))     # x, z, radius: the circumference holds three bark tiles
LIGHT = np.array([0.6, 0.5, -0.62]) / np.linalg.norm([0.6, 0.5, -0.62])


def load(name, mode="RGB"):
    return np.asarray(Image.open(f"{TEX}/{name}.png").convert(mode)).astype(np.float32)


def sample(tex, u, v):
    """Bilinear, repeating. u, v in tiles."""
    h, w = tex.shape[:2]
    x = np.mod(u * w - 0.5, w)
    y = np.mod(v * h - 0.5, h)
    x0, y0 = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32)
    fx, fy = x - x0, y - y0
    x1, y1 = (x0 + 1) % w, (y0 + 1) % h
    if tex.ndim == 3:
        fx, fy = fx[..., None], fy[..., None]
    return (tex[y0, x0] * (1 - fx) + tex[y0, x1] * fx) * (1 - fy) + (tex[y1, x0] * (1 - fx) + tex[y1, x1] * fx) * fy


def rays(eye_offset, shift):
    """Ray origins and directions for one eye. shift: the off-axis shift of the picture in pixels."""
    px = (np.arange(W) + 0.5 - W / 2 + shift)[None, :].repeat(H, 0)
    py = (H / 2 - (np.arange(H) + 0.5))[:, None].repeat(W, 1)
    c, s = np.cos(PITCH), np.sin(PITCH)
    right = np.array([1.0, 0.0, 0.0])
    up = np.array([0.0, c, s])
    fwd = np.array([0.0, -s, c])
    d = px[..., None] * right + py[..., None] * up + F * fwd
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    o = EYE + eye_offset * right
    return o, d, fwd


def cast(o, d):
    """Nearest hit: surface id (0 none, 1 floor, 2 back wall, 3 left wall, 4 post), distance, u, v and the
    ray in the surface's own frame (along u, along v, along the normal)."""
    big = 1e9
    t = np.full(d.shape[:2], big)
    sid = np.zeros(d.shape[:2], np.int8)
    u = np.zeros(d.shape[:2]); v = np.zeros(d.shape[:2])
    vt = np.zeros(d.shape)

    def take(k, tk, uk, vk, vtk, i):
        nonlocal t, sid, u, v, vt
        t = np.where(k, tk, t); sid = np.where(k, i, sid)
        u = np.where(k, uk, u); v = np.where(k, vk, v)
        vt = np.where(k[..., None], vtk, vt)

    with np.errstate(divide="ignore", invalid="ignore"):
        # floor y = 0
        tk = -o[1] / d[..., 1]
        p = o + tk[..., None] * d
        k = (tk > 0) & (tk < t) & (p[..., 0] > LEFT_X) & (p[..., 2] < BACK_Z)
        s = SURF["tiles"][0]
        take(k, tk, p[..., 0] / s, p[..., 2] / s, np.stack([d[..., 0], d[..., 2], d[..., 1]], -1), 1)
        # back wall z = BACK_Z
        tk = (BACK_Z - o[2]) / d[..., 2]
        p = o + tk[..., None] * d
        k = (tk > 0) & (tk < t) & (p[..., 1] > 0) & (p[..., 0] > LEFT_X)
        s = SURF["brick"][0]
        take(k, tk, p[..., 0] / s, -p[..., 1] / s, np.stack([d[..., 0], -d[..., 1], -d[..., 2]], -1), 2)
        # left wall x = LEFT_X
        tk = (LEFT_X - o[0]) / d[..., 0]
        p = o + tk[..., None] * d
        k = (tk > 0) & (tk < t) & (p[..., 1] > 0) & (p[..., 2] < BACK_Z)
        s = SURF["plaster"][0]
        take(k, tk, p[..., 2] / s, -p[..., 1] / s, np.stack([d[..., 2], -d[..., 1], d[..., 0]], -1), 3)
        # post: a vertical cylinder from the floor to 1.2 m
        cx, cz, r = POST
        ox, oz = o[0] - cx, o[2] - cz
        a = d[..., 0] ** 2 + d[..., 2] ** 2
        b = 2 * (ox * d[..., 0] + oz * d[..., 2])
        cc = ox * ox + oz * oz - r * r
        disc = b * b - 4 * a * cc
        tk = (-b - np.sqrt(np.maximum(disc, 0))) / (2 * a)
        p = o + tk[..., None] * d
        k = (disc > 0) & (tk > 0) & (tk < t) & (p[..., 1] > 0) & (p[..., 1] < 1.2)
        nx, nz = (p[..., 0] - cx) / r, (p[..., 2] - cz) / r
        th = np.arctan2(nz, nx)
        s = SURF["bark"][0]
        tang = np.stack([-nz, np.zeros_like(nx), nx], -1)
        vtk = np.stack([(d * tang).sum(-1), -d[..., 1], -(d[..., 0] * nx + d[..., 2] * nz)], -1)
        take(k, tk, th * r / s, -p[..., 1] / s, vtk, 4)
        normal_light = np.where(k, nx * LIGHT[0] + nz * LIGHT[2], 0.0)
    return sid, t, u, v, vt, normal_light


def shade(sid, u, v, vt, nl, textures, relief):
    """relief: 0 none, 1 sunk below each surface, -1 the wrong case, standing in front of it."""
    img = np.zeros(sid.shape + (3,), np.float32)
    img[...] = np.array([52, 56, 64], np.float32)                     # nothing hit
    for i, name in ((1, "tiles"), (2, "brick"), (3, "plaster"), (4, "bark")):
        k = sid == i
        if not k.any():
            continue
        size, depth, sh = SURF[name]
        col, hgt, scale = textures[name]
        uu, vv, t3 = u[k] * scale, v[k] * scale, vt[k]
        if relief and hgt is not None:
            into = np.maximum(-t3[:, 2], 0.2)                           # how steeply the ray enters
            du = t3[:, 0] / into * depth / size * scale
            dv = t3[:, 1] / into * depth / size * scale
            if relief < 0:                                               # start where the ray meets the top of a relief in front
                uu, vv = uu - du, vv - dv
            steps = 40
            hit = np.zeros(uu.shape, bool)
            th = np.ones(uu.shape, np.float32)
            prev = None
            for j in range(steps + 1):
                tt = j / steps
                gap = (1 - sample(hgt, uu + du * tt, vv + dv * tt) / 255.0) - tt
                new = (~hit) & (gap <= 0)
                if prev is not None:
                    th = np.where(new, (j - 1 + prev / np.maximum(prev - gap, 1e-6)) / steps, th)
                else:
                    th = np.where(new, 0.0, th)
                hit |= new
                prev = gap
            uu, vv = uu + du * th, vv + dv * th
        c = sample(col, uu, vv) * sh
        if i == 4:
            c = c * np.clip(0.55 + 0.6 * nl[k], 0.3, 1.15)[:, None]
        img[k] = c
    return np.clip(img, 0, 255)


def textures(kind):
    out = {}
    for name in SURF:
        if kind == "photo":
            out[name] = (load("photo-" + name), None, 0.25)             # the 2048 picture spans four tiles
        else:
            out[name] = (load(name), load(name + "-height", "L"), 1.0)
    return out


def main():
    # the plane of zero parallax: at the nearest thing the middle camera sees
    o, d, fwd = rays(0.0, 0.0)
    sid, t, u, v, vt, nl = cast(o, d)
    z = (t * (d @ fwd))[sid > 0]
    z0 = float(z.min())
    shift = F * SEP / (2 * z0)
    far = float(np.percentile(z, 99))
    info = dict(zero_parallax_distance_m=round(z0, 3), eye_separation_m=SEP, horizontal_field_degrees=50.0,
                eye_height_m=float(EYE[1]), pitch_down_degrees=33.0, off_axis_shift_px=round(float(shift), 2),
                largest_parallax_px=round(float(F * SEP * (1 / z0 - 1 / far)), 1), farthest_m=round(far, 2),
                relief_depth_m={k: v[1] for k, v in SURF.items()}, tile_size_m={k: v[0] for k, v in SURF.items()})
    import json
    json.dump(info, open(f"{OUT}/scene-setup.json", "w"), indent=1)
    print(info)
    proc, photo = textures("procedural"), textures("photo")
    save = lambda a, name: Image.fromarray(np.rint(a).astype(np.uint8)).save(f"{OUT}/{name}.png")
    save(shade(sid, u, v, vt, nl, proc, 0), "scene-2D-procedural-lit-textures")
    save(shade(sid, u, v, vt, nl, photo, 0), "scene-2D-photographs")
    for label, tex, relief in (("scene-3D-procedural-stereo-textures-relief-sunk", proc, 1),
                               ("scene-3D-photographs-plain-textures-no-relief", photo, 0),
                               ("scene-3D-procedural-relief-POPPED-control", proc, -1)):
        eyes = []
        for side in (-1, +1):
            o, d, _ = rays(side * SEP / 2, -side * shift)
            s2, t2, u2, v2, vt2, nl2 = cast(o, d)
            eyes.append(shade(s2, u2, v2, vt2, nl2, tex, relief))
        L, R = eyes
        save(np.concatenate([L, R], 1), label + "-sbs-3840x1080")
        save(np.stack([L[..., 0], R[..., 1], R[..., 2]], -1), label + "-anaglyph")


if __name__ == "__main__":
    main()
