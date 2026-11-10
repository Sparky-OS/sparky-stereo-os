#!/usr/bin/env python3
"""One gaze point on a still: the tiled procedural ladder against a tiled bitmap pyramid.

Both schemes serve the same rings around the gaze. The level a ring needs follows the
linear acuity model of Guenter, Finch, Drucker, Tan and Snyder (Foveated 3D Graphics,
2012): the smallest resolvable angle is w = m e + w0, with w0 = 1/48 degree and m between
1.32 and 1.65 arc minutes per degree of eccentricity e; this script takes the conservative
1.32. The picture is assumed to span the display at 48 pixels per degree, so a pixel at the
gaze is at the acuity limit. Nothing is rendered: the pictures are composed from the ladder's
saved rungs and from JPEG pages.

The bitmap scheme is the one of sparse virtual texturing (Barrett 2008; van Waveren,
Software Virtual Textures, 2012: 128 x 128 pages of every mip level, fetched by need) and
of Vulkan's sparse residency (levels smaller than a block form the mip tail, always bound).

Usage: foveate.py LADDER_DIR BENCH.json NAME=PATH [...]   writes LADDER_DIR/NAME-foveated.json
"""
import io
import json
import sys
import time

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

LAD, BENCH = sys.argv[1], json.load(open(sys.argv[2]))
N, PAGE = 2048, 128
PX_PER_DEG, W0, SLOPE = 48.0, 1 / 48.0, 1.32 / 60.0
RUNG_OF_LEVEL = [8, 16, 32, 64, 128]          # the finest tile size a ring of that level evaluates
ALL_RUNGS = [512, 256, 128, 64, 32, 16, 8]


def jpeg(a):
    b = io.BytesIO()
    Image.fromarray(a).save(b, "JPEG", quality=90)   # the same settings as chain_sizes.py
    return b.getvalue()


def down(a, n):
    s = a.shape[0] // n
    return a.reshape(n, s, n, s, -1).mean(axis=(1, 3))


def to8(a):
    return np.clip(np.rint(a), 0, 255).astype(np.uint8)


def up(a8):
    return np.asarray(Image.fromarray(a8).resize((N, N), Image.BILINEAR)).astype(np.float64)


def luma(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def ssim_map(a, b):
    x, y = luma(a), luma(b)
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    f = lambda v: gaussian_filter(v, 1.5, truncate=3.5, mode="wrap")
    mx, my = f(x), f(y)
    vx, vy, cxy = f(x * x) - mx * mx, f(y * y) - my * my, f(x * y) - mx * my
    return ((2 * mx * my + c1) * (2 * cxy + c2)) / ((mx * mx + my * my + c1) * (vx + vy + c2))


def psnr_mask(a, b, m):
    e = float(((a - b) ** 2)[m].mean())
    return 99.0 if e == 0 else round(10 * np.log10(255.0 ** 2 / e), 2)


def closeness(pic, ref_level, out, rings):
    s = ssim_map(pic, out)
    return {name: dict(psnr_against_picture=psnr_mask(pic, out, m), ssim_against_picture=round(float(s[m].mean()), 4),
                       psnr_against_the_level_the_ring_resolves=psnr_mask(ref_level, out, m))
            for name, m in rings.items()}


def main():
    yy, xx = np.mgrid[0:N, 0:N] + 0.5
    ecc = np.hypot(yy - N / 2, xx - N / 2) / PX_PER_DEG
    level = np.clip(np.floor(np.log2((SLOPE * ecc + W0) / W0)), 0, 4).astype(int)
    rings = {"fovea (levels 0 and 1)": level <= 1, "near periphery (levels 2 and 3)": (level >= 2) & (level <= 3),
             "far periphery (level 4)": level >= 4}
    c_noise = [BENCH["noise_gradient_ns_per_pixel_octave"], BENCH["noise_value_ns_per_pixel_octave"]]
    c_cells, c_grad = BENCH["cells_4_ns_per_pixel"], BENCH["bilinear_ns_per_pixel"]
    for spec in sys.argv[3:]:
        name, path = spec.split("=", 1)
        pic8 = np.asarray(Image.open(path).convert("RGB"))
        pic = pic8.astype(np.float64)
        lad = json.load(open(f"{LAD}/{name}-hard.json"))
        rung = {r["tile"]: r for r in lad["rungs"]}
        res = dict(name=name, model=dict(pixels_per_degree=PX_PER_DEG, w0_degrees=W0, slope_degrees_per_degree=SLOPE,
                                         gaze=[N // 2, N // 2], page=PAGE),
                   ring_share_of_pixels={k: round(float(m.mean()), 4) for k, m in rings.items()})
        # what each ring can resolve: the picture at its level, enlarged
        ref = np.zeros_like(pic)
        for l in range(5):
            ref[level == l] = (pic if l == 0 else up(to8(down(pic, N >> l))))[level == l]

        # ---- the procedural ladder, foveated ----
        out = np.zeros_like(pic)
        wire, tiles_needed, ns = 3, {}, 0.0
        for l in range(5):
            p = np.load(f"{LAD}/{name}-hard-rung-{RUNG_OF_LEVEL[l]}.npy")
            out[level == l] = (p.astype(np.float64) if l == 0 else up(to8(down(p.astype(np.float64), N >> l))))[level == l]
        for T in ALL_RUNGS:
            lr = {8: 0, 16: 1, 32: 2, 64: 3, 128: 4}.get(T, 5)
            n = N // T
            need = (level.reshape(n, T, n, T).min(axis=(1, 3)) <= lr).reshape(-1)
            keep = np.load(f"{LAD}/{name}-hard-cells-{T}.npy")
            tiles_needed[str(T)] = int(need.sum())
            wire += int(need.sum()) * 11 + int((need & keep).sum()) * 20 + (int(need.sum()) + 7) // 8 + 4
            typ = 1 if rung[T]["noise"][0]["kind"].startswith("value") else 0
            octs = rung[T]["noise"][0]["octaves"]
            frac = rung[T]["cells_tiles"] / rung[T]["tiles"]
            for l in range(5):
                if lr >= l:                      # a ring evaluates every rung up to its own
                    samples = float((level == l).sum()) / 4 ** l
                    ns += samples * (c_grad + frac * c_cells + c_noise[typ] * max(1, octs - l))
        samples_total = sum(float((level == l).sum()) / 4 ** l for l in range(5))
        res["procedural_foveated"] = dict(
            wire_bytes=wire, tiles_needed=tiles_needed, evaluation_ms_reference_cpu_one_thread=round(ns / 1e6, 1),
            samples=int(samples_total), resident_bytes_if_tiles_are_cached_rgba8=int(samples_total) * 4,
            resident_bytes_if_evaluated_every_frame=wire, closeness=closeness(pic, ref, out, rings))
        Image.fromarray(to8(out)).save(f"{LAD}/{name}-foveated-procedural.jpg", quality=92)

        # ---- the whole ladder at its finest rung everywhere ----
        full = np.load(f"{LAD}/{name}-hard-rung-8.npy").astype(np.float64)
        ns_full = 0.0
        for T in ALL_RUNGS:
            typ = 1 if rung[T]["noise"][0]["kind"].startswith("value") else 0
            ns_full += N * N * (c_grad + rung[T]["cells_tiles"] / rung[T]["tiles"] * c_cells + c_noise[typ] * rung[T]["noise"][0]["octaves"])
        res["procedural_uniform_finest"] = dict(wire_bytes=rung[8]["bytes_so_far"], evaluation_ms_reference_cpu_one_thread=round(ns_full / 1e6, 1),
                                                samples=N * N, closeness=closeness(pic, ref, full, rings))

        # ---- the bitmap pyramid, foveated ----
        out = np.zeros_like(pic)
        wire, pages_needed, decode_s, all_pages = 0, {}, 0.0, 0
        for l in range(5):
            n = N >> l
            lv = to8(down(pic, n))
            k = n // PAGE
            foot = PAGE << l
            need = (level.reshape(k, foot, k, foot) == l).any(axis=(1, 3))
            dec = np.zeros_like(lv)
            for i in range(k):
                for j in range(k):
                    data = jpeg(lv[i * PAGE:(i + 1) * PAGE, j * PAGE:(j + 1) * PAGE])
                    all_pages += len(data)
                    t0 = time.perf_counter()
                    page = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))
                    dt = time.perf_counter() - t0
                    dec[i * PAGE:(i + 1) * PAGE, j * PAGE:(j + 1) * PAGE] = page
                    if need[i, j]:
                        wire += len(data)
                        decode_s += dt
            pages_needed[str(l)] = int(need.sum())
            out[level == l] = (dec.astype(np.float64) if l == 0 else up(dec))[level == l]
        tail = sum(len(jpeg(to8(down(pic, n)))) for n in (64, 32, 16, 8, 4, 2, 1))
        npages = sum(pages_needed.values())
        res["bitmap_pyramid_foveated"] = dict(
            wire_bytes=wire + tail, mip_tail_bytes=tail, pages_needed=pages_needed, decode_ms_pillow_one_thread=round(decode_s * 1e3, 1),
            resident_bytes_rgba8=npages * PAGE * PAGE * 4 + sum(n * n * 4 for n in (64, 32, 16, 8, 4, 2, 1)),
            resident_bytes_at_4_bits_per_texel=npages * PAGE * PAGE // 2, upload_bytes_rgba8=npages * PAGE * PAGE * 4,
            closeness=closeness(pic, ref, out, rings))
        Image.fromarray(to8(out)).save(f"{LAD}/{name}-foveated-bitmap.jpg", quality=92)

        # ---- everything, once the last layer has arrived ----
        picture = len(jpeg(pic8))
        chain = sum(len(jpeg(to8(down(pic, n)))) for n in (1024, 512, 256, 128, 64, 32, 16, 8, 4, 2, 1))
        res["totals"] = dict(picture_jpeg_q90=picture, lower_resolution_copies=chain, picture_plus_copies=picture + chain,
                             tiled_pyramid_all_pages_and_tail=all_pages + tail,
                             ladder_bytes={str(T): rung[T]["bytes_so_far"] for T in ALL_RUNGS},
                             picture_plus_ladder={str(T): picture + rung[T]["bytes_so_far"] for T in ALL_RUNGS})
        json.dump(res, open(f"{LAD}/{name}-foveated.json", "w"), indent=1)
        print(name, "done", flush=True)


if __name__ == "__main__":
    main()
