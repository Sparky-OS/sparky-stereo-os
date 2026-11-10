#!/usr/bin/env python3
"""A ladder of tiled procedures fitted to a high-resolution picture.

Each rung cuts the picture into smaller tiles (512, 256, ... 8 pixels) and adds,
per tile, terms fitted to what the rungs below left over:
  a gradient  one colour per tile corner, shared by the four tiles that meet there
  cells       four Voronoi sites with a colour each (OpenKTG's Cells), kept only
              where they remove 15 % or more of the tile's remaining error
  noise       OpenKTG's noise for the tile, the seed chosen among all 4,096 by how
              well its field follows the tile's own pixels, one amplitude per channel
A device evaluates the rungs it can afford; a finer rung refines the coarser ones.

Usage: KTG_IMAGE=image tiled.py WORKDIR OUTDIR [--window] NAME=PATH [...]
--window fades every cells and noise term to zero at its tile's border with
GlowRect's own falloff, so that no seam can exist.
"""
import io
import json
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageFile
from scipy.ndimage import gaussian_filter, convolve

ImageFile.MAXBLOCK = 2048 * 2048 * 4
WORK, OUT = sys.argv[1], sys.argv[2]
ARGS = sys.argv[3:]
WINDOW = "--window" in ARGS
SPECS = [a for a in ARGS if "=" in a]
IMAGE = os.environ["KTG_IMAGE"]  # any local image that has g++
UID = "%d:%d" % (os.getuid(), os.getgid())
RUNGS = [int(t) for t in os.environ.get("RUNGS", "512,256,128,64,32,16,8").split(",")]
NOISE_TERMS = int(os.environ.get("NOISE_TERMS", "1"))  # noise terms per tile and rung, each fitted to what the last left
N = 2048
SEEDS = 4096
_run = [0]


def ktg(args, stdin=None):
    _run[0] += 1
    cmd = ["docker", "run", "--rm", "-i", "--name", "x3d-473w-%d-%d" % (os.getpid(), _run[0]),
           "--network", "none", "--ulimit", "core=0", "--cpus", "1", "--user", UID,
           "-v", WORK + ":" + WORK + ":ro", IMAGE, WORK + "/bin/ktgtool"] + [str(a) for a in args]
    return subprocess.run(cmd, input=stdin, stdout=subprocess.PIPE, check=True).stdout


def fields(T, freq, oct_, fade, typ, seeds):
    """The octave sums OpenKTG's Noise forms for these seeds, one T x T field each."""
    L = T.bit_length() - 1
    raw = ktg(["fields", L, freq, oct_, fade, typ], stdin=(" ".join(str(int(s)) for s in seeds) + "\n").encode())
    return np.frombuffer(raw, dtype=np.float32).reshape(len(seeds), T * T)


def material(T):
    L = T.bit_length() - 1
    return 1, max(1, L - 1)  # freq, octaves: cells from half the tile down to 2 pixels


def window(T):
    """GlowRect's falloff: 1 inside three quarters of the tile, a ramp to 0 at its border."""
    u = np.abs((np.arange(T) + 0.5) / T * 2 - 1)
    d = np.maximum(u - 0.75, 0) / 0.25
    return np.clip(1 - np.sqrt(d[:, None] ** 2 + d[None, :] ** 2), 0, 1).astype(np.float32)


def tiles_of(a, T):
    n = N // T
    return a.reshape(n, T, n, T, 3).transpose(0, 2, 1, 3, 4).reshape(n * n, T, T, 3)


def untile(t, T):
    n = N // T
    return t.reshape(n, n, T, T, 3).transpose(0, 2, 1, 3, 4).reshape(N, N, 3)


# ---------- the three terms ----------

def gradient_term(res, T):
    n = N // T
    r = np.roll(res, (T // 2, T // 2), axis=(0, 1))
    node = r.reshape(n, T, n, T, 3).mean(axis=(1, 3))          # node (i, j) sits at pixel (i T, j T)
    node = np.clip(np.rint(node), -127, 127).astype(np.float32)  # one signed byte per channel
    t = (np.arange(N) + 0.5) / T
    i0 = np.floor(t).astype(int)
    f = (t - i0).astype(np.float32)
    a, b = i0 % n, (i0 + 1) % n
    rows = node[a] * (1 - f)[:, None, None] + node[b] * f[:, None, None]
    return rows[:, a] * (1 - f)[None, :, None] + rows[:, b] * f[None, :, None]


def cells_term(rt, T, w):
    """Four sites per tile; rt is (M, T, T, 3). Returns the term and which tiles keep it."""
    M = rt.shape[0]
    s = max(1, T // 32)
    sub = rt[:, s // 2::s, s // 2::s]
    m = sub.shape[1]
    yy, xx = np.meshgrid((np.arange(m) * s + s // 2 + 0.5) / T, (np.arange(m) * s + s // 2 + 0.5) / T, indexing="ij")
    pos = np.stack([yy, xx], -1).reshape(1, m * m, 2).astype(np.float32)
    col = sub.reshape(M, m * m, 3)
    sp = np.tile(np.array([[0.25, 0.25], [0.25, 0.75], [0.75, 0.25], [0.75, 0.75]], np.float32), (M, 1, 1))
    sc = np.stack([col[:, np.abs(pos[0] - sp[0, j]).sum(-1).argmin()] for j in range(4)], 1).copy()
    lam = (col.var(axis=(1, 2)) * 3 + 1e-3)[:, None, None] / 0.25 ** 2
    for _ in range(6):
        d = ((col[:, :, None, :] - sc[:, None, :, :]) ** 2).sum(-1) + lam * ((pos[:, :, None, :] - sp[:, None, :, :]) ** 2).sum(-1)
        lab = d.argmin(-1)
        for j in range(4):
            k = (lab == j)
            c = k.sum(1)
            ok = c > 0
            sc[ok, j] = (col * k[:, :, None]).sum(1)[ok] / c[ok, None]
            sp[ok, j] = (pos * k[:, :, None]).sum(1)[ok] / c[ok, None]
    sp = (np.clip(np.floor(sp * 256), 0, 255) + 0.5) / 256      # one byte per coordinate
    g = (np.arange(T) + 0.5) / T
    best = np.full((M, T, T), np.inf, np.float32)
    lab = np.zeros((M, T, T), np.int8)
    for j in range(4):
        dy = np.abs(g[None, :] - sp[:, j, 0:1]); dy = np.minimum(dy, 1 - dy)   # the operator wraps distances
        dx = np.abs(g[None, :] - sp[:, j, 1:2]); dx = np.minimum(dx, 1 - dx)
        d = (dy ** 2)[:, :, None] + (dx ** 2)[:, None, :]
        k = d < best
        best[k] = d[k]
        lab[k] = j
    term = np.zeros_like(rt)
    w3 = w[None, :, :, None]
    for j in range(4):
        k = (lab == j)[..., None]
        den = (k * w3 * w3).sum(axis=(1, 2))
        c = (rt * k * w3).sum(axis=(1, 2)) / np.maximum(den, 1e-6)
        c = np.clip(np.rint(c), -127, 127).astype(np.float32)
        term += k * w3 * c[:, None, None, :]
    before = (rt ** 2).sum(axis=(1, 2, 3))
    after = ((rt - term) ** 2).sum(axis=(1, 2, 3))
    keep = (before - after) >= 0.15 * before
    term[~keep] = 0
    return term, keep


def noise_scan(res_tiles, T, w):
    """For every picture's tiles: the best seed and amplitudes, for each candidate material.

    res_tiles: list of (M, T*T, 3) arrays. Returns the candidates and, per candidate and
    picture, (gain per tile, seed per tile, amplitude per tile and channel)."""
    freq, oct_ = material(T)
    cands = [(typ, fade) for typ in (0, 1) for fade in (0.6, 0.9)]
    wf = w.reshape(-1)
    out = []
    chunk = max(16, min(SEEDS, (96 << 20) // (T * T * 4)))
    for typ, fade in cands:
        best = [(np.zeros(r.shape[0], np.float32), np.zeros(r.shape[0], np.int32), np.zeros((r.shape[0], 3), np.float32))
                for r in res_tiles]
        for s0 in range(0, SEEDS, chunk):
            seeds = np.arange(s0, min(SEEDS, s0 + chunk))
            F = fields(T, freq, oct_, fade, typ, seeds).copy()
            F -= F.mean(1, keepdims=True)
            F *= wf[None, :]
            nu = (F ** 2).sum(1)
            for p, r in enumerate(res_tiles):
                step = max(1, (64 << 20) // (len(seeds) * 4))
                for m0 in range(0, r.shape[0], step):
                    rr = r[m0:m0 + step]
                    C = np.stack([rr[:, :, c] @ F.T for c in range(3)], -1)      # (m, S, 3)
                    gain = (C ** 2).sum(-1) / nu[None, :]
                    j = gain.argmax(1)
                    g = gain[np.arange(len(j)), j]
                    bg, bs, ba = best[p]
                    k = g > bg[m0:m0 + step]
                    idx = np.arange(m0, m0 + len(j))[k]
                    bg[idx] = g[k]
                    bs[idx] = seeds[j[k]]
                    ba[idx] = C[np.arange(len(j)), j][k] / nu[j[k], None]
        out.append(best)
    return cands, out


def noise_term(T, typ, fade, seeds, amps, w, octaves=None):
    freq, oct_ = material(T)
    uniq, inv = np.unique(seeds, return_inverse=True)
    F = fields(T, freq, octaves or oct_, fade, typ, uniq).copy()
    F -= F.mean(1, keepdims=True)
    F *= w.reshape(1, -1)
    a = amps.astype(np.float16).astype(np.float32)               # two bytes per channel
    return (F[inv][:, :, None] * a[:, None, :]).reshape(len(seeds), T, T, 3)


# ---------- measures ----------

def psnr(a, b):
    m = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    return 99.0 if m == 0 else 10 * np.log10(255.0 ** 2 / m)


def luma(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def ssim(a, b):
    """Wang, Bovik, Sheikh and Simoncelli 2004: Gaussian window (sigma 1.5), K1 0.01, K2 0.03, on luma."""
    x, y = luma(a.astype(np.float64)), luma(b.astype(np.float64))
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    f = lambda v: gaussian_filter(v, 1.5, truncate=3.5, mode="wrap")
    mx, my = f(x), f(y)
    vx, vy, cxy = f(x * x) - mx * mx, f(y * y) - my * my, f(x * y) - mx * my
    return float((((2 * mx * my + c1) * (2 * cxy + c2)) / ((mx * mx + my * my + c1) * (vx + vy + c2))).mean())


def gmsd(a, b):
    """Xue, Zhang, Mou and Bovik 2014: deviation of the gradient magnitude similarity
    (Prewitt, constant 170 on a 0..255 scale, after averaging 2 x 2). 0 is identical."""
    def gm(v):
        v = v.reshape(v.shape[0] // 2, 2, v.shape[1] // 2, 2).mean(axis=(1, 3))
        kx = np.array([[1, 0, -1]] * 3, np.float64) / 3
        return np.sqrt(convolve(v, kx, mode="wrap") ** 2 + convolve(v, kx.T, mode="wrap") ** 2)
    ga, gb = gm(luma(a.astype(np.float64))), gm(luma(b.astype(np.float64)))
    return float(((2 * ga * gb + 170) / (ga * ga + gb * gb + 170)).std())


def down(a, n):
    s = a.shape[0] // n
    return a.reshape(n, s, n, s, -1).mean(axis=(1, 3))


def bands(field):
    f = np.fft.fft2(field - field.mean())
    e = f.real ** 2 + f.imag ** 2
    k = np.fft.fftfreq(field.shape[0]) * field.shape[0]
    r = np.sqrt(k[:, None] ** 2 + k[None, :] ** 2)
    return np.array([e[(r >= 2 ** i) & (r < 2 ** (i + 1))].sum() for i in range(9)]) + 1e-12


def spectrum_gap(img, p):
    a, b = bands(luma(down(img, 1024))), bands(luma(down(p, 1024)))
    return float(np.sqrt(np.mean((10 * np.log10(b / a)) ** 2)))


def seam_ratio(img, p, T):
    """Jump across tile borders against the jump elsewhere, the picture's own ratio divided out."""
    def ratio(v):
        d = np.abs(np.diff(luma(v.astype(np.float64)), axis=1))
        border = np.zeros(N - 1, bool)
        border[T - 1::T] = True
        return d[:, border].mean() / max(d[:, ~border].mean(), 1e-9)
    return float(ratio(p) / ratio(img))


def jpeg_bytes(a, q=90):
    b = io.BytesIO()
    Image.fromarray(a).save(b, "JPEG", quality=q, subsampling=0, optimize=True)
    return b.getvalue()


def to8(a):
    return np.clip(np.rint(a), 0, 255).astype(np.uint8)


def same_bytes_picture(img8, budget):
    """The closest enlarged lower-resolution JPEG of the picture within the byte budget."""
    best = None
    for n in (8, 16, 32, 64, 128, 256, 512, 1024):
        small = to8(down(img8.astype(np.float64), n))
        for q in (30, 50, 70, 90):
            data = jpeg_bytes(small, q)
            if len(data) > budget:
                continue
            up = np.asarray(Image.open(io.BytesIO(data)).convert("RGB").resize((N, N), Image.BICUBIC))
            v = psnr(img8, up)
            if best is None or v > best[0]:
                best = (v, n, q, len(data), up)
    return best


def levels(img, p):
    out = {}
    n = N
    while n >= 64:
        a, b = (img, p) if n == N else (down(img, n), down(p, n))
        out[str(n)] = [round(psnr(a, b), 2), round(ssim(a, b), 4)]
        n //= 2
    return out


# ---------- the ladder ----------

def main():
    os.makedirs(OUT, exist_ok=True)
    names = [s.split("=", 1)[0] for s in SPECS]
    imgs = [np.asarray(Image.open(s.split("=", 1)[1]).convert("RGB")).astype(np.float32) for s in SPECS]
    for i in imgs:
        assert i.shape == (N, N, 3)
    mean = [np.rint(i.reshape(-1, 3).mean(0)).astype(np.float32) for i in imgs]
    P = [np.broadcast_to(m, (N, N, 3)).copy() for m in mean]       # every rung at its full octaves
    Q = [p.copy() for p in P]                                        # the same rungs with two octaves at most
    total = [3] * len(imgs)
    results = [dict(name=n, window=WINDOW, rungs=[]) for n in names]
    tag = "window" if WINDOW else "hard"
    for T in RUNGS:
        t0 = time.time()
        w = window(T) if WINDOW else np.ones((T, T), np.float32)
        M = (N // T) ** 2
        rec = []
        for p in range(len(imgs)):
            g = gradient_term(imgs[p] - P[p], T)
            P[p] += g
            Q[p] += g
            rt = tiles_of(imgs[p] - P[p], T)
            ct = np.zeros_like(rt)
            keep = np.zeros(M, bool)
            step = max(1, (256 << 20) // (T * T * 3 * 4 * 6))
            for m0 in range(0, M, step):
                ct[m0:m0 + step], keep[m0:m0 + step] = cells_term(rt[m0:m0 + step], T, w)
            c = untile(ct, T)
            P[p] += c
            Q[p] += c
            rec.append(dict(tile=T, tiles=M, mse_before=round(float(np.mean((imgs[p] - P[p] + c + g) ** 2)), 2),
                            mse_after_gradient=round(float(np.mean((imgs[p] - P[p] + c) ** 2)), 2),
                            gradient_bytes=3 * M, cells_tiles=int(keep.sum()),
                            cells_bytes=int(keep.sum()) * 20 + (M + 7) // 8))
            np.save(f"{OUT}/{names[p]}-{tag}-cells-{T}.npy", keep)
        freq, oct_ = material(T)
        for p in range(len(imgs)):
            rec[p]["mse_after_gradient_cells"] = round(float(np.mean((imgs[p] - P[p]) ** 2)), 2)
        for term in range(NOISE_TERMS):
            res_tiles = [tiles_of(imgs[p] - P[p], T).reshape(M, T * T, 3) for p in range(len(imgs))]
            cands, scan = noise_scan(res_tiles, T, w)
            del res_tiles
            for p in range(len(imgs)):
                gains = [float(scan[c][p][0].sum()) for c in range(len(cands))]
                c = int(np.argmax(gains))
                typ, fade = cands[c]
                _, seeds, amps = scan[c][p]
                P[p] += untile(noise_term(T, typ, fade, seeds, amps, w), T)
                Q[p] += untile(noise_term(T, typ, fade, seeds, amps, w, octaves=min(2, oct_)), T)
                rec[p].setdefault("noise", []).append(dict(kind="value (Noise2)" if typ else "gradient (GNoise2)",
                                                           freq=freq, octaves=oct_, fadeoff=fade))
        for p in range(len(imgs)):
            r = rec[p]
            r["mse_after_noise"] = round(float(np.mean((imgs[p] - P[p]) ** 2)), 2)
            r["noise_bytes"] = NOISE_TERMS * (8 * M + 4)
            total[p] += r["gradient_bytes"] + r["cells_bytes"] + r["noise_bytes"]
            r["bytes_so_far"] = total[p]
            img8, p8, q8 = to8(imgs[p]), to8(P[p]), to8(Q[p])
            r["psnr"], r["ssim"], r["gmsd"] = round(psnr(img8, p8), 2), round(ssim(img8, p8), 4), round(gmsd(img8, p8), 4)
            r["spectrum_gap_db"] = round(spectrum_gap(imgs[p], P[p]), 2)
            r["levels"] = levels(imgs[p], np.clip(P[p], 0, 255))
            r["seam_ratio"] = round(seam_ratio(img8, p8, T), 3)
            r["two_octaves"] = dict(psnr=round(psnr(img8, q8), 2), ssim=round(ssim(img8, q8), 4), gmsd=round(gmsd(img8, q8), 4))
            sb = same_bytes_picture(img8, total[p])
            if sb:
                r["same_bytes_picture"] = dict(size=sb[1], quality=sb[2], bytes=sb[3], psnr=round(sb[0], 2),
                                               ssim=round(ssim(img8, sb[4]), 4), gmsd=round(gmsd(img8, sb[4]), 4))
            results[p]["rungs"].append(r)
            np.save(f"{OUT}/{names[p]}-{tag}-rung-{T}.npy", p8)
            if T in (128, 32, 8):
                Image.fromarray(p8[:512, :512]).save(f"{OUT}/{names[p]}-{tag}-rung-{T}-crop.png")
            json.dump(results[p], open(f"{OUT}/{names[p]}-{tag}.json", "w"), indent=1)
        print("rung", T, "done in %.0f s" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
