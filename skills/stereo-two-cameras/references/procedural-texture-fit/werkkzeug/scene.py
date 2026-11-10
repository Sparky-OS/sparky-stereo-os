#!/usr/bin/env python3
"""A small offline picture of a room corner, to look at textures in 2D and in stereo.

Not a renderer that ships and not DPFR: planes and one cylinder, one ray per pixel, the
relief found per eye by a search along the ray through a thin shell around each surface (relief
mapping, Policarpo, Oliveira and Comba 2005; parallax occlusion mapping, Tatarchuk 2006).
On the post the search runs in the cylinder's own shell (radius and angle), not in a flat sheet.

The scene: a floor of stone tiles, a brick wall at the back, a plaster wall on the left and a
bark post, seen from a standing person's eye height, looking down into the corner.
Stereo: two cameras with parallel axes, 65 mm apart, each with an off-axis projection so that
the plane of zero parallax lies at the nearest thing in the picture.

Usage: scene.py TEXDIR OUTDIR
  TEXDIR holds NAME.png (lit) and NAME-depth.png for tiles, brick, plaster, bark, drawn at their own size.
Writes scene-2D.png and two marked stereo pictures (pns.py): the relief sunk only, and mostly sunk
with a little of it in front of each surface.
"""
import json
import sys

import numpy as np
from PIL import Image

import pns

TEX, OUT = sys.argv[1], sys.argv[2]
W, H = 1920, 1080
HFOV = np.radians(50.0)
F = (W / 2) / np.tan(HFOV / 2)
EYE = np.array([0.0, 1.5, 0.0])
PITCH = np.radians(33.0)
SEP = 0.065
# name: size of one tile in metres, relief behind the surface and in front of it in metres, shade,
# and the three levels of the depth picture: black (deepest), the surface, white (highest)
SURF = {"tiles": (0.60, 0.006, 0.001, 1.00, (0, 226, 234)), "brick": (0.50, 0.015, 0.003, 0.92, (13, 200, 216)),
        "plaster": (0.50, 0.004, 0.001, 0.78, (126, 207, 221)), "bark": (0.30, 0.025, 0.006, 1.00, (25, 128, 165))}
BACK_Z, LEFT_X = 2.0, -1.0
POST = (0.50, 1.45, 0.9 / (2 * np.pi))     # x, z, radius: the circumference holds three bark tiles
LIGHT = np.array([0.6, 0.5, -0.62]) / np.linalg.norm([0.6, 0.5, -0.62])
STEPS = 64


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


def cast(o, d, post_radius=None):
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
        if post_radius is None:
            return sid, t, u, v, vt, np.zeros(d.shape[:2]), None
        cx, cz, r = POST[0], POST[1], post_radius
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
        take(k, tk, th * POST[2] / s, -p[..., 1] / s, vtk, 4)
        normal_light = np.where(k, nx * LIGHT[0] + nz * LIGHT[2], 0.0)
        leave = (-b + np.sqrt(np.maximum(disc, 0))) / (2 * a)
    return sid, t, u, v, vt, normal_light, leave


def below(name, tex, uu, vv, pop):
    """How far the relief lies below the outer bound of its shell, as a fraction of the shell: 0 at the
    bound, 1 at the deepest. pop False: the whole relief at the surface or behind it."""
    size, sunk, front, sh, (black, surface, white) = SURF[name]
    hv = sample(tex, uu, vv)
    if not pop:
        return np.clip((white - hv) / (white - black), 0, 1), sunk, 0.0
    down = np.clip((surface - hv) / (surface - black), 0, 1) * sunk
    up = np.clip((hv - surface) / (white - surface), 0, 1) * front
    return (front + down - up) / (sunk + front), sunk, front


def shade(sid, u, v, vt, nl, face, textures, relief):
    """relief: 0 none, 1 sunk only, 2 mostly sunk with a little in front. sid 5: the post, already searched."""
    img = np.zeros(sid.shape + (3,), np.float32)
    img[...] = np.array([52, 56, 64], np.float32)                     # nothing hit
    for i, name in ((1, "tiles"), (2, "brick"), (3, "plaster"), (4, "bark"), (5, "bark")):
        k = sid == i
        if not k.any():
            continue
        size, sunk, front, sh, _ = SURF[name]
        col, hgt = textures[name]
        uu, vv, t3 = u[k], v[k], vt[k]
        if relief and i < 4:
            _, sunk, front = below(name, hgt, uu, vv, relief == 2)
            thick = sunk + front
            into = np.maximum(-t3[:, 2], 0.2)                           # how steeply the ray enters
            du = t3[:, 0] / into * thick / size
            dv = t3[:, 1] / into * thick / size
            uu, vv = uu - du * front / thick, vv - dv * front / thick   # start on the shell's outer bound
            hit = np.zeros(uu.shape, bool)
            th = np.ones(uu.shape, np.float32)
            prev = None
            for j in range(STEPS + 1):
                tt = j / STEPS
                gap = below(name, hgt, uu + du * tt, vv + dv * tt, relief == 2)[0] - tt
                new = (~hit) & (gap <= 0)
                if prev is not None:
                    th = np.where(new, (j - 1 + prev / np.maximum(prev - gap, 1e-6)) / STEPS, th)
                else:
                    th = np.where(new, 0.0, th)
                hit |= new
                prev = gap
            uu, vv = uu + du * th, vv + dv * th
        c = sample(col, uu, vv) * sh
        if i >= 4:
            # towards the post's rim one pixel covers many of the bark's: take the softened bark there
            w = np.clip(1 - face[k] / 0.45, 0, 1)[:, None]
            c = (c * (1 - w) + sample(textures["bark-soft"], uu, vv) * sh * w) * np.clip(0.55 + 0.6 * nl[k], 0.3, 1.15)[:, None]
        img[k] = c
    return np.clip(img, 0, 255)


def post_search(o, d, enter, leave, k, hgt, pop):
    """The bark's relief in the post's own shell. For the rays in k: walk from where the ray enters the
    shell's outer cylinder to where it leaves it, and stop where the ray's radius falls below the
    relief's. Returns hit, u, v and the light on the round post at that point."""
    size, sunk, front, sh, _ = SURF["bark"]
    cx, cz, r0 = POST
    if not pop:
        front = 0.0
    outer = r0 + front
    dk, t0, t1 = d[k], enter[k], leave[k]
    hit = np.zeros(t0.shape, bool)
    at = np.zeros(t0.shape)
    prev = None

    def place(t):
        p = o + t[:, None] * dk
        x, z = p[:, 0] - cx, p[:, 2] - cz
        rad = np.hypot(x, z)
        return rad, np.arctan2(z, x) * r0 / size, -p[:, 1] / size, p[:, 1], x / rad, z / rad

    for j in range(STEPS + 1):
        t = t0 + (t1 - t0) * j / STEPS
        rad, uu, vv, y, nx, nz = place(t)
        frac = below("bark", hgt, uu, vv, pop)[0]
        gap = rad - (outer - frac * (sunk + front))            # positive while the ray is still outside the relief
        new = (~hit) & (gap <= 0) & (y > 0) & (y < 1.2)
        if prev is None:
            at = np.where(new, t, at)
        else:
            at = np.where(new, t - (t1 - t0) / STEPS * gap / np.minimum(gap - prev, -1e-9), at)
        hit |= new
        prev = gap
    rad, uu, vv, y, nx, nz = place(at)
    return hit, uu, vv, nx * LIGHT[0] + nz * LIGHT[2], -(dk[:, 0] * nx + dk[:, 2] * nz)


def render(side, shift, textures, relief):
    o, d, _ = rays(side * SEP / 2, -side * shift)
    front = SURF["bark"][2] if relief == 2 else 0.0
    sid, t, u, v, vt, nl, leave = cast(o, d, POST[2] + front)
    face = np.abs(vt[..., 2])
    if relief:
        k = sid == 4
        hit, uu, vv, light, facing = post_search(o, d, t, leave, k, textures["bark"][1], relief == 2)
        s0, t0, u0, v0, vt0, nl0, _ = cast(o, d)                 # the room without the post, for rays that pass through a furrow at its rim
        idx = np.flatnonzero(k)
        miss = idx[~hit]
        for a, b in ((sid, s0), (u, u0), (v, v0), (nl, nl0)):
            a.flat[miss] = b.flat[miss]
        vt.reshape(-1, 3)[miss] = vt0.reshape(-1, 3)[miss]
        good = idx[hit]
        sid.flat[good] = 5
        u.flat[good], v.flat[good], nl.flat[good], face.flat[good] = uu[hit], vv[hit], light[hit], facing[hit]
    return shade(sid, u, v, vt, nl, face, textures, relief)


def main():
    o, d, fwd = rays(0.0, 0.0)
    sid, t, u, v, vt, nl, _ = cast(o, d, POST[2] + SURF["bark"][2])
    z = (t * (d @ fwd))[sid > 0]
    z0 = float(z.min())                                          # zero parallax at the nearest thing the middle camera sees
    shift = F * SEP / (2 * z0)
    far = float(np.percentile(z, 99))
    info = dict(zero_parallax_distance_m=round(z0, 3), eye_separation_m=SEP, horizontal_field_degrees=50.0,
                eye_height_m=float(EYE[1]), pitch_down_degrees=33.0, off_axis_shift_px=round(float(shift), 2),
                largest_parallax_px=round(float(F * SEP * (1 / z0 - 1 / far)), 1), farthest_m=round(far, 2),
                relief_behind_m={k: s[1] for k, s in SURF.items()}, relief_in_front_m={k: s[2] for k, s in SURF.items()},
                tile_size_m={k: s[0] for k, s in SURF.items()})
    json.dump(info, open(f"{OUT}/scene-setup.json", "w"), indent=1)
    print(info)
    tex = {n: (load(n), load(n + "-depth", "L")) for n in SURF}
    from PIL import ImageFilter
    soft = Image.open(f"{TEX}/bark.png").convert("RGB")
    soft = Image.merge("RGB", [Image.fromarray(np.roll(np.asarray(c.filter(ImageFilter.GaussianBlur(8))), 0)) for c in soft.split()])
    tex["bark-soft"] = np.asarray(soft).astype(np.float32)
    as8 = lambda a: np.rint(a).astype(np.uint8)
    Image.fromarray(as8(render(0, 0.0, tex, 0))).save(f"{OUT}/scene-2D.png")
    for label, relief in (("scene-3D-relief-sunk", 1), ("scene-3D-relief-mostly-sunk-a-little-popped", 2)):
        L, R = (as8(render(side, shift, tex, relief)) for side in (-1, +1))
        print(label, pns.write(f"{OUT}/{label}.pns", L, R))


if __name__ == "__main__":
    main()
