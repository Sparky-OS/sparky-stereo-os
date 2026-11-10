#!/usr/bin/env python3
"""Fit a small procedure to a bitmap and measure what is left.

For each picture: three procedures (a flat colour, OpenKTG's Noise operator
with a 16-stop gradient, a sum of K cosine waves), the bytes of each, the
error of the procedure alone, and the bytes of the remainder image that
restores the picture, lossless and at a matched lossy quality.

Usage: fit.py WORKDIR OUTDIR NAME=PATH [NAME=PATH ...]
WORKDIR holds bin/ktgtool and oct/ (see run.sh); nothing is written elsewhere.
"""
import io
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFile
from scipy.stats import rankdata

# a JPEG of pure noise is larger than PIL's default encoder buffer ("broken data stream")
ImageFile.MAXBLOCK = 2048 * 2048 * 4

WORK = sys.argv[1]
OUT = sys.argv[2]
SOCK = os.environ.get("DOCKER_HOST", "")
IMAGE = os.environ["KTG_IMAGE"]  # any local image that has g++
UID = "%d:%d" % (os.getuid(), os.getgid())


def ktg(args, stdin=None):
    """Run ktgtool inside a container (no network, no core dumps)."""
    cmd = ["docker", "run", "--rm", "-i", "--network", "none", "--ulimit", "core=0",
           "--cpus", "4", "--user", UID, "-v", WORK + ":" + WORK + ":ro",
           IMAGE, WORK + "/bin/ktgtool"] + [str(a) for a in args]
    return subprocess.run(cmd, input=stdin, stdout=subprocess.PIPE, check=True).stdout


# ---------- sizes ----------

def png(a):
    """Lossless size. PNG, not lossless WebP: WebP made the wrapped remainder of an
    unrelated smooth field 5.8 % smaller than the picture alone, which no real
    saving explains, while PNG made it 1.3 % larger."""
    b = io.BytesIO()
    Image.fromarray(a).save(b, "PNG", compress_level=6)
    return len(b.getvalue())


def jpeg(a, q):
    b = io.BytesIO()
    Image.fromarray(a).save(b, "JPEG", quality=q, subsampling=0, optimize=True)
    d = np.asarray(Image.open(io.BytesIO(b.getvalue())).convert("RGB"))
    return len(b.getvalue()), d


def psnr(a, b):
    m = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return 99.0 if m == 0 else 10 * np.log10(255.0 ** 2 / m)


def lossy_remainder(img, proc, target):
    """Bytes of a JPEG of the remainder whose restored picture has target dB.

    JPEG qualities are steps, so the bytes are interpolated between the last
    quality below the target and the first one at or above it.
    """
    if psnr(img, proc) >= target:
        return 0, 0, psnr(img, proc)  # the procedure alone already reaches the target
    r = np.clip(img.astype(np.int16) - proc.astype(np.int16) + 128, 0, 255).astype(np.uint8)
    seen = {}

    def at(q):
        if q not in seen:
            n, d = jpeg(r, q)
            back = np.clip(proc.astype(np.int16) + d.astype(np.int16) - 128, 0, 255).astype(np.uint8)
            seen[q] = (n, psnr(img, back))
        return seen[q]

    lo, hi, best = 1, 100, None
    while lo <= hi:
        q = (lo + hi) // 2
        if at(q)[1] >= target:
            best = q
            hi = q - 1
        else:
            lo = q + 1
    if best is None:
        return None
    n1, p1 = at(best)
    if best == 1:
        return n1, best, p1
    n0, p0 = at(best - 1)
    f = (target - p0) / (p1 - p0) if p1 > p0 else 1.0
    return int(round(n0 + f * (n1 - n0))), best, target


# ---------- measures ----------

def bands(field):
    """Energy in 8 octave bands (1-2 ... 128-256 cycles per picture) of a 512x512 field."""
    f = np.fft.fft2(field - field.mean())
    e = (f.real ** 2 + f.imag ** 2)
    k = np.fft.fftfreq(field.shape[0]) * field.shape[0]
    r = np.sqrt(k[:, None] ** 2 + k[None, :] ** 2)
    return np.array([e[(r >= 2 ** i) & (r < 2 ** (i + 1))].sum() for i in range(8)]) + 1e-12


def uniform(field):
    return (rankdata(field, method="average").reshape(field.shape) - 0.5) / field.size


def down(a, n):
    """Box average to n x n."""
    s = a.shape[0] // n
    return a.reshape(n, s, n, s, -1).mean(axis=(1, 3))


def spectrum_gap_db(img, proc, axis):
    a = bands(down(img.astype(np.float64), 512) @ axis)
    b = bands(down(proc.astype(np.float64), 512) @ axis)
    return float(np.sqrt(np.mean((10 * np.log10(b / a)) ** 2)))


def histogram_gap(img, proc):
    return float(np.mean([np.mean(np.abs(np.sort(img[..., c].ravel()[::16]).astype(float)
                                         - np.sort(proc[..., c].ravel()[::16]).astype(float)))
                          for c in range(3)]))


def mip_psnr(img, proc):
    out = []
    n = img.shape[0]
    while n >= 8:
        out.append(round(psnr(down(img.astype(np.float64), n), down(proc.astype(np.float64), n)), 2))
        n //= 2
    return out


# ---------- procedure 1: OpenKTG Noise + gradient ----------

def octave(t, F, seed=None):
    if seed is None:
        return np.fromfile(f"{WORK}/oct/o_{t}_{F}.f32", dtype=np.float32).reshape(512, 512).astype(np.float64)
    return np.frombuffer(ktg(["octave", 9, F, t, seed]), dtype=np.float32).reshape(512, 512).astype(np.float64)


def n01(octs, fade, absmode):
    oct_ = len(octs)
    # GenTexture::Noise computes (fadeoff - 1) / (fadeoff^oct - 1): 0/0 at fadeoff 1
    assert abs(fade - 1) > 1e-6, "fadeoff 1 is undefined in OpenKTG's normalised Noise"
    scal = (fade - 1) / (fade ** oct_ - 1)
    s, acc = 1.0, 0.0
    for o in octs:
        acc = acc + s * (np.abs(o) if absmode else o)
        s *= fade
    return scal * acc if absmode else 0.5 + 0.5 * scal * acc


def gradient_lookup(v, stops):
    p = np.clip(v, 0, 1) * (len(stops) - 1)
    i = np.minimum(p.astype(int), len(stops) - 2)
    f = (p - i)[..., None]
    return stops[i] * (1 - f) + stops[i + 1] * f


def fit_ktg_noise(img):
    small = down(img.astype(np.float64), 512)
    flat = small.reshape(-1, 3)
    mean = flat.mean(0)
    w, v = np.linalg.eigh(np.cov((flat - mean).T))
    axis = v[:, -1] if v[:, -1].sum() >= 0 else -v[:, -1]
    t = (small - mean) @ axis
    tu = uniform(t)
    tb = np.log10(bands(tu))
    best = None
    cache = {(ty, F): octave(ty, F) for ty in (0, 1) for F in range(10)}
    for ty in (0, 1):
        for ab in (0, 1):
            for freq in range(0, 7):
                for oc in range(1, 11 - freq):
                    octs = [cache[(ty, freq + i)] for i in range(oc)]
                    for fade in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99, 1.1, 1.2):
                        n = n01(octs, fade, ab)
                        if n.std() == 0:
                            continue
                        loss = float(np.sum((np.log10(bands(uniform(n))) - tb) ** 2))
                        if best is None or loss < best[0]:
                            best = (loss, ty, ab, freq, oc, fade)
    loss, ty, ab, freq, oc, fade = best
    # the seed: 4096 exist; scan them all at 128x128 against the rank picture
    tgt = uniform(down(small, 128) @ axis).astype(np.float32).tobytes()
    seed, corr, second = ktg(["seedscan", 7, freq, oc, fade, ty, ab], stdin=tgt).split()
    seed, corr, second = int(seed), float(corr), float(second)
    locked = corr > 0.5
    if locked:
        # the picture follows this very noise field: settle octaves, fadeoff and
        # the gradient stops against the pixels themselves, at the full size
        rng = np.random.default_rng(1)
        pick = rng.choice(2048 * 2048, 300000, replace=False)
        full = img.reshape(-1, 3)[pick].astype(np.float64)
        octs = [np.frombuffer(ktg(["octave", 11, freq + i, ty, seed]), dtype=np.float32)[pick].astype(np.float64)
                for i in range(12 - freq)]

        def stops_for(fd, oc_):
            n = n01(octs[:oc_], fd, ab)
            p = np.clip(n, 0, 1) * 15
            i = np.minimum(p.astype(int), 14)
            f = p - i
            A = np.zeros((n.size, 16))
            A[np.arange(n.size), i] = 1 - f
            A[np.arange(n.size), i + 1] += f
            used = A.sum(0) > 0
            s = np.zeros((16, 3))
            s[used] = np.linalg.lstsq(A[:, used], full, rcond=None)[0]
            idx = np.where(used)[0]
            for k in range(16):
                if not used[k]:
                    s[k] = s[idx[np.argmin(np.abs(idx - k))]]
            s = np.clip(np.rint(s), 0, 255)
            return float(np.mean((A @ s - full) ** 2)), s

        g = (np.sqrt(5) - 1) / 2
        found = None
        for oc_ in range(1, 12 - freq + 1):
            lo, hi = max(0.05, fade - 0.15), fade + 0.15
            for _ in range(30):
                a, b = hi - g * (hi - lo), lo + g * (hi - lo)
                if stops_for(a, oc_)[0] < stops_for(b, oc_)[0]:
                    hi = b
                else:
                    lo = a
            fd = (lo + hi) / 2
            # prefer a value a person would have typed when it fits as well
            for cand in (round(fd, 2), round(fd, 3), round(fd, 4)):
                if abs(cand - 1) < 1e-6:
                    continue
                e = stops_for(cand, oc_)[0]
                if found is None or e < found[0] - 1e-9:
                    found = (e, oc_, cand)
        _, oc, fade = found
        stops = stops_for(fade, oc)[1]
    else:
        # only the statistics match: give each stop the colour the picture has at
        # the same rank (histogram matching along the main colour axis)
        octs = [octave(ty, freq + i, seed) for i in range(oc)]
        n = n01(octs, fade, ab)
        order = np.argsort(tu.ravel())
        sorted_n = np.sort(n.ravel())
        stops = np.zeros((16, 3))
        for k in range(16):
            q = np.searchsorted(sorted_n, k / 15.0) / n.size
            q = min(max(q, 1 / 64), 1 - 1 / 64)
            a, b = int((q - 1 / 64) * n.size), int((q + 1 / 64) * n.size)
            stops[k] = flat[order[a:b]].mean(0)
    stops8 = np.clip(np.rint(stops), 0, 255).astype(int)
    mode = 2 | ab | (4 if ty else 0)
    grad_args = [int(x) for x in stops8.ravel()]
    small_op = np.frombuffer(ktg(["noise", 9, freq, min(oc, 10 - freq), fade, seed, mode] + grad_args),
                             dtype=np.uint8).reshape(512, 512, 3).astype(np.float64)
    model = gradient_lookup(n01([octave(ty, freq + i, seed) for i in range(min(oc, 10 - freq))], fade, ab),
                            stops8.astype(np.float64))
    gap = float(np.abs(small_op - model).max())
    assert gap <= 1.0, "the real operator and the fit's model differ by %.2f levels" % gap
    raw = ktg(["noise", 11, freq, oc, fade, seed, mode] + grad_args)
    proc = np.frombuffer(raw, dtype=np.uint8).reshape(2048, 2048, 3)
    params = dict(freq=freq, oct=oc, fadeoff=fade, seed=seed, mode=mode,
                  noise="value (Noise2)" if ty else "gradient (GNoise2)", abs=bool(ab),
                  gradient=stops8.tolist(), band_loss=round(loss, 4),
                  operator_against_model_levels=round(gap, 3), seed_correlation=corr, second_best_seed_correlation=second, seed_locked=locked)
    nbytes = 1 + 1 + 4 + 2 + 1 + 16 * 3  # freq, oct, fadeoff f32, seed u16, mode, 16 RGB stops
    return proc, nbytes, params, axis


# ---------- procedure 2: K cosine waves ----------

def fit_cosines(img, K):
    a = img.astype(np.float64)
    mean = a.reshape(-1, 3).mean(0)
    F = np.stack([np.fft.rfft2(a[..., c] - mean[c]) for c in range(3)], -1)
    e = (np.abs(F) ** 2).sum(-1)
    e[0, 0] = 0
    # the half plane rfft2 keeps holds each wave once, except column 0 and the
    # Nyquist column, where rows above the middle mirror rows below it
    n = a.shape[0]
    e[n // 2 + 1:, 0] = 0
    e[n // 2 + 1:, -1] = 0
    idx = np.argsort(e.ravel())[::-1][:K]
    ky, kx = np.unravel_index(idx, e.shape)
    G = np.zeros_like(F)
    scale = n * n
    for y, x in zip(ky, kx):
        c = F[y, x] / scale
        amp = np.float16(np.abs(c)).astype(np.float64)          # 2 bytes per channel
        ph = np.rint(np.angle(c) / (2 * np.pi) * 256) % 256      # 1 byte per channel
        q = amp * np.exp(2j * np.pi * ph / 256) * scale
        G[y, x] = q
        if x == 0 or x == e.shape[1] - 1:
            G[(-y) % n, x] = np.conj(q)
    proc = np.stack([np.fft.irfft2(G[..., c], s=a.shape[:2]) + np.rint(mean[c]) for c in range(3)], -1)
    proc = np.clip(np.rint(proc), 0, 255).astype(np.uint8)
    nbytes = 3 + K * (2 + 2 + 3 * 3)  # mean colour; per wave kx, ky as int16 and 3 x (amplitude f16, phase u8)
    waves = [[int(x), int(y if y <= n // 2 else y - n)] for y, x in zip(ky[:12], kx[:12])]
    return proc, nbytes, dict(K=K, strongest_waves_kx_ky=waves)


# ---------- one picture ----------

def measure(name, img):
    res = dict(name=name, size=list(img.shape[:2]))
    res["direct_png"] = png(img)
    nj, dj = jpeg(img, 90)
    target = psnr(img, dj)
    res["direct_jpeg_q90"] = dict(bytes=nj, psnr=round(target, 2))
    flat = np.broadcast_to(np.rint(img.reshape(-1, 3).mean(0)).astype(np.uint8), img.shape).copy()
    ktgp, ktgb, ktgparams, axis = fit_ktg_noise(img)
    procs = [("flat colour", flat, 3, {}), ("OpenKTG Noise + gradient", ktgp, ktgb, ktgparams)]
    for K in (16, 64, 256, 1024):
        p, b, par = fit_cosines(img, K)
        procs.append((f"{K} cosine waves", p, b, par))
    for n in (16, 32, 64):
        b = io.BytesIO()
        Image.fromarray(img).resize((n, n), Image.BOX).save(b, "JPEG", quality=90, subsampling=0, optimize=True)
        up = np.asarray(Image.open(io.BytesIO(b.getvalue())).convert("RGB").resize((2048, 2048), Image.BICUBIC))
        procs.append((f"{n}x{n} picture, enlarged (not a procedure)", up, len(b.getvalue()), {}))
    res["procedures"] = []
    for label, p, b, par in procs:
        rem = ((img.astype(np.int16) - p.astype(np.int16)) % 256).astype(np.uint8)
        back = ((p.astype(np.int16) + rem.astype(np.int16)) % 256).astype(np.uint8)
        assert np.array_equal(back, img), "lossless remainder does not restore the picture"
        lr = lossy_remainder(img, p, target)
        res["procedures"].append(dict(
            procedure=label, procedure_bytes=b, params=par,
            psnr_alone=round(psnr(img, p), 2),
            spectrum_gap_db=round(spectrum_gap_db(img, p, axis), 2),
            histogram_gap_levels=round(histogram_gap(img, p), 2),
            psnr_per_level=mip_psnr(img, p),
            remainder_png=png(rem),
            remainder_jpeg=dict(bytes=lr[0], quality=lr[1], psnr=round(lr[2], 2)) if lr else None,
        ))
        if label.startswith("OpenKTG") or label.startswith("64 "):
            tag = "ktg" if label.startswith("OpenKTG") else "cos64"
            Image.fromarray(p).resize((512, 512), Image.BOX).save(f"{OUT}/{name}-{tag}.png")
    Image.fromarray(img).resize((512, 512), Image.BOX).save(f"{OUT}/{name}-picture.png")
    return res


def main():
    os.makedirs(OUT, exist_ok=True)
    for spec in sys.argv[3:]:
        name, path = spec.split("=", 1)
        img = np.asarray(Image.open(path).convert("RGB"))
        assert img.shape == (2048, 2048, 3), img.shape
        r = measure(name, img)
        with open(f"{OUT}/{name}.json", "w") as f:
            json.dump(r, f, indent=1)
        print(name, "done", flush=True)


if __name__ == "__main__":
    main()
