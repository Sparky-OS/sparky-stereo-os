#!/usr/bin/env python3
"""Does a tile hold one known operator? If so, return it and its parameters.

For a picture cut into 256 pixel tiles, each tile is tried as a flat colour, as
OpenKTG's Cells, as a GlowRect over a flat colour, and as Noise with a two-colour
gradient; the answer is drawn again by the real operator and compared pixel by pixel.

Usage: KTG_IMAGE=image recognise.py WORKDIR OUTDIR NAME=PATH [...]
With --gate only the first tile is tried as Noise and the best seed correlation is
reported (a quick way to say that a picture is not such a procedure).
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

WORK, OUT = sys.argv[1], sys.argv[2]
GATE = "--gate" in sys.argv
SPECS = [a for a in sys.argv[3:] if "=" in a]
IMAGE = os.environ["KTG_IMAGE"]  # any local image that has g++
UID = "%d:%d" % (os.getuid(), os.getgid())
T, L = 256, 8
_run = [0]


def ktg(args, stdin=None):
    _run[0] += 1
    cmd = ["docker", "run", "--rm", "-i", "--name", "x3d-473w-rec-%d-%d" % (os.getpid(), _run[0]),
           "--network", "none", "--ulimit", "core=0", "--cpus", "1", "--user", UID,
           "-v", WORK + ":" + WORK + ":ro", IMAGE, WORK + "/bin/ktgtool"] + [str(a) for a in args]
    return subprocess.run(cmd, input=stdin, stdout=subprocess.PIPE, check=True).stdout


def render(lines):
    raw = ktg(["tiles", L], stdin=("\n".join(lines) + "\n").encode())
    return np.frombuffer(raw, dtype=np.uint8).reshape(len(lines), T, T, 3).copy()


def fields(freq, oct_, fade, typ, seeds):
    raw = ktg(["fields", L, freq, oct_, fade, typ], stdin=(" ".join(str(int(s)) for s in seeds) + "\n").encode())
    return np.frombuffer(raw, dtype=np.float32).reshape(len(seeds), T * T)


def psnr(a, b):
    m = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    return 99.0 if m == 0 else 10 * np.log10(255.0 ** 2 / m)


def kind_of(t):
    flat = t.reshape(-1, 3)
    colours = np.unique(flat, axis=0)
    if len(colours) == 1:
        return "F"
    if len(colours) <= 16:
        return "C"
    corners = np.stack([t[0, 0], t[0, -1], t[-1, 0], t[-1, -1]])
    if (corners == corners[0]).all() and (flat == corners[0]).all(1).mean() >= 0.3:
        return "G"
    return "N"


# ---------- Cells ----------

def voronoi(sites):
    g = (np.arange(T) + 0.5) / T
    best = np.full((T, T), np.inf)
    lab = np.zeros((T, T), int)
    for j, (x, y) in enumerate(sites):
        dy = np.abs(g - y); dy = np.minimum(dy, 1 - dy)
        dx = np.abs(g - x); dx = np.minimum(dx, 1 - dx)
        d = (dy ** 2)[:, None] + (dx ** 2)[None, :]
        k = d < best
        best[k] = d[k]
        lab[k] = j
    return lab


def fit_cells(t):
    colours, lab = np.unique(t.reshape(-1, 3), axis=0, return_inverse=True)
    lab = lab.reshape(T, T)
    k = len(colours)
    ang = (np.arange(T) + 0.5) / T * 2 * np.pi
    sites = []
    for j in range(k):
        m = lab == j
        ys, xs = np.nonzero(m)
        # a region may wrap around the tile: take the mean on the circle
        x = np.arctan2(np.sin(ang[xs]).mean(), np.cos(ang[xs]).mean()) / (2 * np.pi) % 1
        y = np.arctan2(np.sin(ang[ys]).mean(), np.cos(ang[ys]).mean()) / (2 * np.pi) % 1
        sites.append([x, y])
    grid = lambda v: (np.floor(np.asarray(v) * 64) % 64 + 0.5) / 64
    sites = [list(grid(s)) for s in sites]
    wrong = lambda s: int((voronoi(s) != lab).sum())
    cur = wrong(sites)
    # every site in turn tries all 64 x 64 grid positions against a quarter-size copy of the labels
    sub = lab[2::4, 2::4].reshape(-1)
    g4 = (np.arange(2, T, 4) + 0.5) / T
    cand = (np.arange(64) + 0.5) / 64
    wrap = lambda d: np.minimum(d, 1 - d)
    d1 = wrap(np.abs(g4[None, :] - cand[:, None])) ** 2            # (candidate coordinate, pixel coordinate)
    dc = (d1[:, None, :, None] + d1[None, :, None, :]).reshape(64 * 64, -1)   # candidate (y, x) against pixel (y, x)
    for _ in range(16):
        before = [list(x) for x in sites]
        for j in range(k):
            others = [i for i in range(k) if i != j]
            do = np.stack([(wrap(np.abs(g4 - sites[i][1])) ** 2)[:, None] + (wrap(np.abs(g4 - sites[i][0])) ** 2)[None, :]
                           for i in others]).reshape(len(others), -1)
            dmin, lo = do.min(0), np.asarray(others)[do.argmin(0)]
            mine = dc < dmin[None, :]
            bad = (mine != (sub == j)[None, :]) | (~mine & (lo != sub)[None, :])
            c = int(bad.sum(1).argmin())
            sites[j] = [cand[c % 64], cand[c // 64]]
        if before == sites:
            break
    # two sites moved together, up to two grid steps each: one site alone can sit in a dead end
    def wrong_sub(st):
        d = np.stack([(wrap(np.abs(g4 - y)) ** 2)[:, None] + (wrap(np.abs(g4 - x)) ** 2)[None, :] for x, y in st])
        return int((d.reshape(len(st), -1).argmin(0) != sub).sum())
    moves = [(a, b) for a in range(-2, 3) for b in range(-2, 3)]
    cur = wrong_sub(sites)
    for _ in range(6):
        improved = False
        for i in range(k):
            for j in range(i + 1, k):
                for ax, ay in moves:
                    for bx, by in moves:
                        trial = [list(x) for x in sites]
                        trial[i] = [(trial[i][0] + ax / 64) % 1, (trial[i][1] + ay / 64) % 1]
                        trial[j] = [(trial[j][0] + bx / 64) % 1, (trial[j][1] + by / 64) % 1]
                        w = wrong_sub(trial)
                        if w < cur:
                            sites, cur, improved = trial, w, True
        if not improved:
            break
    cur = wrong(sites)
    for _ in range(10):                       # then single grid steps against every pixel
        improved = False
        for j in range(k):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                trial = [list(s) for s in sites]
                trial[j] = [(trial[j][0] + dx / 64) % 1, (trial[j][1] + dy / 64) % 1]
                w = wrong(trial)
                if w < cur:
                    sites, cur, improved = trial, w, True
        if not improved or cur == 0:
            break
    line = "C %d " % k + " ".join("%.6f %.6f %d %d %d" % (s[0], s[1], *c) for s, c in zip(sites, colours))
    return line, 1 + 5 * k


# ---------- GlowRect ----------

def fit_glow(t):
    bg = t[0, 0]
    mask = (t != bg).any(-1)
    ys, xs = np.nonzero(mask)
    inner_colours, counts = np.unique(t[mask], axis=0, return_counts=True)
    inner = inner_colours[counts.argmax()]
    plateau = (t == inner).all(-1)
    pys, pxs = np.nonzero(plateau)
    snap = lambda v: int(round(v * 64))
    ox, oy = snap((xs.min() + xs.max() + 1) / 2 / T), snap((ys.min() + ys.max() + 1) / 2 / T)
    hx, hy = (xs.max() - xs.min() + 1) / 2 / T, (ys.max() - ys.min() + 1) / 2 / T
    px, py = (pxs.max() - pxs.min() + 1) / 2 / T, (pys.max() - pys.min() + 1) / 2 / T
    lines = []
    for ux in (snap(hx), snap(hx) + 1, snap(hx) + 2):
        for vy in (snap(hy), snap(hy) + 1, snap(hy) + 2):
            ru = min((0.25, 0.5, 0.75), key=lambda r: abs(r - px / (ux / 64)))
            rv = min((0.25, 0.5, 0.75), key=lambda r: abs(r - py / (vy / 64)))
            lines.append("G %d %d %d %.6f %.6f %.6f %.6f %.2f %.2f %d %d %d" % (*bg, ox / 64, oy / 64, ux / 64, vy / 64, ru, rv, *inner))
    out = render(lines)
    err = [float(np.mean((o.astype(float) - t) ** 2)) for o in out]
    return lines[int(np.argmin(err))], 3 + 6 + 3


# ---------- Noise ----------

def find_material(t):
    """Kind, frequency, octaves, fadeoff and the first tile's seed, from a 32 x 32 copy and then the pixels."""
    flat = t.reshape(-1, 3).astype(np.float64)
    w, v = np.linalg.eigh(np.cov((flat - flat.mean(0)).T))
    proj = ((flat - flat.mean(0)) @ v[:, -1]).reshape(T, T)
    small = proj.reshape(32, 8, 32, 8).mean(axis=(1, 3)).astype(np.float32).tobytes()
    best = None
    for typ in (0, 1):
        for freq in (0, 1, 2, 3):
            for oct_ in (2, 4):
                for fade in (0.5, 0.8):
                    seed, corr, second = ktg(["seedscan", 5, freq, oct_, fade, typ, 0], stdin=small).split()
                    corr = abs(float(corr))
                    if best is None or corr > best[0]:
                        best = (corr, typ, freq, int(seed))
    corr, typ, freq, seed = best
    if corr < 0.5:
        return None, corr
    # the small copy settles the kind and the frequency; the seed is scanned again on the pixels,
    # because the small copy's best seed can be a wrong one
    line = fit_noise(t[None], (typ, freq, min(4, L - freq), 0.5))[0][0]
    seed = int(line.split()[4])
    found = None
    for oct_ in range(1, L - freq + 1):
        for fade in [round(0.3 + 0.05 * i, 2) for i in range(19) if abs(0.3 + 0.05 * i - 1) > 1e-6]:
            f = fields(freq, oct_, fade, typ, [seed])[0].astype(np.float64)
            A = np.stack([np.ones_like(f), f], 1)
            res = np.linalg.lstsq(A, flat, rcond=None)[1].sum()
            if found is None or res < found[0]:
                found = (res, oct_, fade)
    return (typ, freq, found[1], found[2]), corr


def fit_noise(tiles, mat):
    typ, freq, oct_, fade = mat
    M = len(tiles)
    R = tiles.reshape(M, T * T, 3).astype(np.float32)
    R = R - R.mean(1, keepdims=True)
    best = np.zeros(M, np.float32)
    seed = np.zeros(M, int)
    for s0 in range(0, 4096, 256):
        s = np.arange(s0, s0 + 256)
        F = fields(freq, oct_, fade, typ, s).copy()
        F -= F.mean(1, keepdims=True)
        nu = (F ** 2).sum(1)
        gain = sum((R[:, :, c] @ F.T) ** 2 for c in range(3)) / nu[None, :]
        j = gain.argmax(1)
        g = gain[np.arange(M), j]
        k = g > best
        best[k], seed[k] = g[k], s[j[k]]
    F = fields(freq, oct_, fade, typ, np.unique(seed))
    F = {int(s): f for s, f in zip(np.unique(seed), F)}
    scal = (fade - 1) / (fade ** oct_ - 1)
    lines = []
    for m in range(M):
        n01 = 0.5 + 0.5 * scal * F[int(seed[m])].astype(np.float64)
        A = np.stack([1 - n01, n01], 1)
        s = np.linalg.lstsq(A, tiles[m].reshape(-1, 3).astype(np.float64), rcond=None)[0]
        s = np.clip(np.rint(s), 0, 255).astype(int)
        lines.append("N %d %d %s %d %d %s" % (freq, oct_, fade, seed[m], 2 | (4 if typ else 0), " ".join(map(str, s.ravel()))))
    return lines, 8


def main():
    os.makedirs(OUT, exist_ok=True)
    for spec in SPECS:
        name, path = spec.split("=", 1)
        img = np.asarray(Image.open(path).convert("RGB"))
        tiles = img.reshape(8, T, 8, T, 3).transpose(0, 2, 1, 3, 4).reshape(64, T, T, 3)
        kinds = [kind_of(t) for t in tiles]
        res = dict(name=name, tile=T)
        ni = [i for i, k in enumerate(kinds) if k == "N"]
        mat = None
        if ni:
            mat, corr = find_material(tiles[ni[0]])
            res["first_noise_tile_seed_correlation"] = round(corr, 4)
        if GATE or (ni and mat is None):
            res["recognised"] = False
            json.dump(res, open(f"{OUT}/{name}-recognise.json", "w"), indent=1)
            print(name, "not a tiled procedure: best seed correlation", res.get("first_noise_tile_seed_correlation"), flush=True)
            continue
        lines, nbytes = [None] * 64, [0] * 64
        if ni:
            got, per = fit_noise(tiles[ni], mat)
            for i, line in zip(ni, got):
                lines[i], nbytes[i] = line, per
        for i, k in enumerate(kinds):
            if k == "F":
                lines[i], nbytes[i] = "F %d %d %d" % tuple(tiles[i][0, 0]), 3
            elif k == "C":
                lines[i], nbytes[i] = fit_cells(tiles[i])
            elif k == "G":
                lines[i], nbytes[i] = fit_glow(tiles[i])
        back = render(lines)
        # a rounded colour can be one level off: try the neighbours of a Noise tile that is not yet exact
        for i in ni:
            for _ in range(4):                # walk one level at a time until nothing improves
                if (back[i] == tiles[i]).all():
                    break
                v = lines[i].split()
                base = [int(x) for x in v[6:12]]
                cand = []
                for c in range(3 ** 6):
                    d = [(c // 3 ** j) % 3 - 1 for j in range(6)]
                    cand.append(" ".join(v[:6] + [str(min(255, max(0, b + e))) for b, e in zip(base, d)]))
                out = render(cand)
                err = ((out.astype(np.int32) - tiles[i][None]) ** 2).reshape(len(cand), -1).sum(1)
                if cand[int(err.argmin())] == lines[i]:
                    break
                lines[i] = cand[int(err.argmin())]
                back[i] = out[int(err.argmin())]
        res["recognised"] = bool(sum((t == o).all() for t, o in zip(tiles, back)) >= 32)
        res["tiles"] = [dict(kind=k, line=line, bytes=b, psnr=round(psnr(t, o), 2), exact=bool((t == o).all()))
                        for k, line, b, t, o in zip(kinds, lines, nbytes, tiles, back)]
        res["bytes"] = int(sum(nbytes)) + 64 // 4 + 5            # two bits of kind per tile, the shared noise material
        res["exact_tiles"] = int(sum(x["exact"] for x in res["tiles"]))
        res["picture_psnr"] = round(psnr(tiles, back), 2)
        json.dump(res, open(f"{OUT}/{name}-recognise.json", "w"), indent=1)
        print(name, "exact tiles", res["exact_tiles"], "of 64; bytes", res["bytes"], "; PSNR", res["picture_psnr"], flush=True)


if __name__ == "__main__":
    main()
