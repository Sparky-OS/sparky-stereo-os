#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Fixtures for ORDER 577: Matroska stereo tracks whose eyes hold a circle and a square.

Each eye is drawn at the shape it is meant to be shown at (the circle round, the square square), then resized to the
eye's coded size, packed side by side or top and bottom (either eye first), encoded losslessly (FFV1) by FFmpeg and
muxed by mkvmerge with the StereoMode and display size of the case.  A reader that shows an eye at the right shape
shows a round circle: measure.py reads the circle's width over its height.

Usage: fixtures.py OUTDIR [CASE...]   (no CASE: every case)
Writes OUTDIR/NAME.mkv, OUTDIR/cases.json (what each case is meant to show) and OUTDIR/SHA256SUMS.
"""
import hashlib, json, os, subprocess, sys, tempfile
from fractions import Fraction
import numpy as np
from PIL import Image, ImageDraw

LEFT_BG, RIGHT_BG, MONO_BG = (96, 0, 0), (0, 0, 96), (0, 72, 0)
FRAMES, RATE = 30, 1

# name: packing, coded frame, one eye's intended display shape (w:h), declaration
#   decl: ("dims", W, H) mkvmerge --display-dimensions in pixels; ("none",) the elements removed (RFC 9559 default);
#         ("unit", U, W, H) DisplayUnit U with DisplayWidth W and DisplayHeight H
CASES = {
    # side by side, the films of the ORDER and their kinds
    "sbs-full-2560x720":        ("sbs", 2560, 720, Fraction(16, 9), ("dims", 2560, 720)),
    "sbs-half-1920x1080":       ("sbs", 1920, 1080, Fraction(16, 9), ("dims", 1920, 1080)),
    "sbs-declared-854x480":     ("sbs", 854, 480, Fraction(1707, 960), ("dims", 1707, 480)),
    "sbs-full-1920x540":        ("sbs", 1920, 540, Fraction(960, 544), ("dims", 1920, 544)),
    # top and bottom twins
    "tab-full-1280x1440":       ("tab", 1280, 1440, Fraction(16, 9), ("dims", 1280, 1440)),
    "tab-half-1920x1080":       ("tab", 1920, 1080, Fraction(16, 9), ("dims", 1920, 1080)),
    "tab-declared-854x480":     ("tab", 854, 480, Fraction(854, 480), ("dims", 854, 960)),
    "tab-full-960x1080":        ("tab", 960, 1080, Fraction(960, 544), ("dims", 960, 1088)),
    # the other ways a writer declares the same pictures
    "sbs-full-plane-1280x720":  ("sbs", 2560, 720, Fraction(16, 9), ("dims", 1280, 720)),   # RFC 9559 18.10: one plane
    "sbs-half-default":         ("sbs", 1920, 1080, Fraction(16, 9), ("none",)),
    "sbs-full-default":         ("sbs", 2560, 720, Fraction(16, 9), ("none",)),
    "sbs-full-dar":             ("sbs", 2560, 720, Fraction(16, 9), ("unit", 3, 32, 9)),
    "sbs-half-unknown-unit":    ("sbs", 1920, 1080, Fraction(16, 9), ("unit", 4, 1920, 1080)),
    "tab-full-plane-1280x720":  ("tab", 1280, 1440, Fraction(16, 9), ("dims", 1280, 720)),
    "tab-half-default":         ("tab", 1920, 1080, Fraction(16, 9), ("none",)),
    "tab-full-default":         ("tab", 1280, 1440, Fraction(16, 9), ("none",)),
    # interleaved packings share the axis of side by side (columns) and top and bottom (rows)
    "cols-full-2560x720":       ("cols", 2560, 720, Fraction(16, 9), ("dims", 2560, 720)),
    "cols-half-1920x1080":      ("cols", 1920, 1080, Fraction(16, 9), ("dims", 1920, 1080)),
    "rows-full-1280x1440":      ("rows", 1280, 1440, Fraction(16, 9), ("dims", 1280, 1440)),
    "rows-half-1920x1080":      ("rows", 1920, 1080, Fraction(16, 9), ("dims", 1920, 1080)),
    # a checkerboard eye keeps the frame's shape: no multiplier, before or after
    "checker-1920x1080":        ("checker", 1920, 1080, Fraction(16, 9), ("dims", 1920, 1080)),
    # the 2D control
    "mono-1280x720":            ("mono", 1280, 720, Fraction(16, 9), ("dims", 1280, 720)),
}
# StereoMode for each packing and order (RFC 9559 5.1.4.1.28.3, Table 5)
MODES = {("sbs", "lr"): 1, ("sbs", "rl"): 11, ("tab", "lr"): 3, ("tab", "rl"): 2,
         ("cols", "lr"): 9, ("cols", "rl"): 8, ("rows", "lr"): 7, ("rows", "rl"): 6,
         ("checker", "lr"): 5, ("checker", "rl"): 4}


def eye_coded(packing, w, h):
    if packing in ("sbs", "cols"):
        return w // 2, h
    if packing in ("tab", "rows"):
        return w, h // 2
    return w, h  # checkerboard: each eye has half the samples over the whole frame; mono


def draw_eye(shape, cw, ch, bg, frame):
    """The eye at its display shape (height 4 x coded), resized to cw x ch."""
    H = 4 * ch
    W = round(H * shape)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    r = 0.30 * H
    cx = 0.30 * W + (frame % 4) * 0.002 * W  # a small movement, so a player has frames to show
    d.ellipse((cx - r, 0.5 * H - r, cx + r, 0.5 * H + r), fill=(255, 255, 255))
    s = 0.15 * H
    sx = 0.78 * W
    d.rectangle((sx - s, 0.5 * H - s, sx + s, 0.5 * H + s), fill=(255, 255, 255))
    return img.resize((cw, ch), Image.LANCZOS)


def pack(packing, w, h, left, right):
    out = Image.new("RGB", (w, h))
    if packing == "sbs":
        out.paste(left, (0, 0)); out.paste(right, (w // 2, 0))
    elif packing == "tab":
        out.paste(left, (0, 0)); out.paste(right, (0, h // 2))
    elif packing in ("cols", "rows", "checker"):
        a, b = np.asarray(left), np.asarray(right)
        o = np.zeros((h, w, 3), np.uint8)
        if packing == "cols":
            o[:, 0::2], o[:, 1::2] = a, b
        elif packing == "rows":
            o[0::2], o[1::2] = a, b
        else:
            even = (np.add.outer(np.arange(h), np.arange(w)) % 2) == 0
            o[even], o[~even] = a[even], b[~even]
        out = Image.fromarray(o)
    else:
        out.paste(left, (0, 0))
    return out


def make(outdir, name, order):
    packing, w, h, shape, decl = CASES[name]
    cw, ch = eye_coded(packing, w, h)
    if packing == "checker":
        cw, ch = w, h
    tmp = tempfile.mkdtemp(dir=outdir)
    for f in range(FRAMES):
        if packing == "mono":
            frame = draw_eye(shape, w, h, MONO_BG, f)
        else:
            first = draw_eye(shape, cw, ch, LEFT_BG, f)
            second = draw_eye(shape, cw, ch, RIGHT_BG, f)
            if order == "rl":
                first, second = second, first
            frame = pack(packing, w, h, first, second)
        frame.save(os.path.join(tmp, "f%03d.png" % f))
    raw = os.path.join(tmp, "raw.mkv")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(RATE), "-i", os.path.join(tmp, "f%03d.png"),
                    "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-g", "1", "-fflags", "+bitexact",
                    "-map_metadata", "-1", raw], check=True)
    fname = name if packing == "mono" else "%s-%s" % (name, order)
    out = os.path.join(outdir, fname + ".mkv")
    cmd = ["mkvmerge", "-q", "--no-date", "-o", out]
    if packing != "mono":
        cmd += ["--stereo-mode", "0:%d" % MODES[(packing, order)]]
    if decl[0] == "dims":
        cmd += ["--display-dimensions", "0:%dx%d" % (decl[1], decl[2])]
    cmd += [raw]
    subprocess.run(cmd, check=True, env=dict(os.environ, LC_ALL="C.UTF-8"))
    if decl[0] == "none":
        subprocess.run(["mkvpropedit", "-q", out, "--edit", "track:v1", "--delete", "display-width",
                        "--delete", "display-height", "--delete", "display-unit"], check=True)
    elif decl[0] == "unit":
        subprocess.run(["mkvpropedit", "-q", out, "--edit", "track:v1", "--set", "display-unit=%d" % decl[1],
                        "--set", "display-width=%d" % decl[2], "--set", "display-height=%d" % decl[3]], check=True)
    for f in os.listdir(tmp):
        os.unlink(os.path.join(tmp, f))
    os.rmdir(tmp)
    return fname, {"packing": packing, "order": order if packing != "mono" else None,
                   "stereo_mode": MODES.get((packing, order)) if packing != "mono" else None,
                   "coded": [w, h], "eye_coded": [cw, ch], "eye_shape": [shape.numerator, shape.denominator],
                   "declaration": list(decl)}


def main():
    outdir = os.path.abspath(sys.argv[1])
    names = sys.argv[2:] or list(CASES)
    os.makedirs(outdir, exist_ok=True)
    cases = {}
    for name in names:
        orders = [None] if CASES[name][0] == "mono" else ["lr", "rl"]
        for order in orders:
            fname, info = make(outdir, name, order)
            cases[fname] = info
            print(fname, flush=True)
    with open(os.path.join(outdir, "cases.json"), "w") as f:
        json.dump(cases, f, indent=1, sort_keys=True)
    with open(os.path.join(outdir, "SHA256SUMS"), "w") as f:
        for fname in sorted(cases):
            data = open(os.path.join(outdir, fname + ".mkv"), "rb").read()
            f.write("%s  %s.mkv\n" % (hashlib.sha256(data).hexdigest(), fname))


if __name__ == "__main__":
    main()
