#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Is the picture on screen each eye resized once, by the compositor?

    one_resize.py CAPTURE.png LEFT.png RIGHT.png X Y W H [--flags bilinear] [--out DIR]

CAPTURE is Stereo KWin's capture of a stereo screen (both eyes side by side, each at the
output's size).  LEFT and RIGHT are the eyes as the program handed them over, each at its
own resolution.  For each eye the region X, Y, W x H of its half of the capture is compared
with FFmpeg's own resize of that eye to W x H (one resize, swscale with FLAGS), as PSNR in
dB over RGB; the rest of the half must be the window's black.  A second reference, the eye
first stretched to the shape of its display (as a program that "restores" half views would)
and then resized, is reported for comparison when --twice WxH is given.
"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image


def ffmpeg_scale(src, w, h, flags):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "o.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
                        "scale=%d:%d:flags=%s,format=rgb24" % (w, h, flags), "-frames:v", "1", out], check=True)
        return np.asarray(Image.open(out).convert("RGB")).astype(np.float64)


def locate(eye, ref):
    """Top-left of the ref-sized region of eye that matches ref best: coarse, then exact."""
    f = 8
    h, w = ref.shape[:2]
    small_eye = eye[: eye.shape[0] // f * f, : eye.shape[1] // f * f].reshape(eye.shape[0] // f, f, eye.shape[1] // f, f, 3).mean((1, 3))
    small_ref = ref[: h // f * f, : w // f * f].reshape(h // f, f, w // f, f, 3).mean((1, 3))
    best = None
    for y in range(small_eye.shape[0] - small_ref.shape[0] + 1):
        for x in range(small_eye.shape[1] - small_ref.shape[1] + 1):
            d = np.mean((small_eye[y:y + small_ref.shape[0], x:x + small_ref.shape[1]] - small_ref) ** 2)
            if best is None or d < best[0]:
                best = (d, x * f, y * f)
    _, bx, by = best
    best = None
    for y in range(max(0, by - f), min(eye.shape[0] - h, by + f) + 1):
        for x in range(max(0, bx - f), min(eye.shape[1] - w, bx + f) + 1):
            d = np.mean((eye[y:y + h, x:x + w] - ref) ** 2)
            if best is None or d < best[0]:
                best = (d, x, y)
    return best[1], best[2]


def psnr(a, b):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return float("inf") if mse == 0 else 10 * np.log10(255.0 ** 2 / mse)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("left")
    ap.add_argument("right")
    ap.add_argument("x", type=int)
    ap.add_argument("y", type=int)
    ap.add_argument("w", type=int)
    ap.add_argument("h", type=int)
    ap.add_argument("--flags", default="bilinear")
    ap.add_argument("--twice", help="WxH the eye is first stretched to, for the two-resize reference")
    ap.add_argument("--out")
    ap.add_argument("--ignore-outside", action="store_true", help="the window's own 2D parts surround the region")
    ap.add_argument("--find", action="store_true", help="X Y are unknown: find the region where the left eye's reference fits best")
    a = ap.parse_args()
    cap = np.asarray(Image.open(a.capture).convert("RGB"))
    half = cap.shape[1] // 2
    if a.find:
        a.x, a.y = locate(cap[:, :half].astype(np.float64), ffmpeg_scale(a.left, a.w, a.h, a.flags))
    report = {"capture": [cap.shape[1], cap.shape[0]], "rect": [a.x, a.y, a.w, a.h], "flags": a.flags}
    ok = True
    for name, eye_png, offset in (("left", a.left, 0), ("right", a.right, half)):
        eye = cap[:, offset:offset + half]
        region = eye[a.y:a.y + a.h, a.x:a.x + a.w]
        ref = ffmpeg_scale(eye_png, a.w, a.h, a.flags)
        r = {"eye_size": list(Image.open(eye_png).size), "psnr_one_resize": round(psnr(region, ref), 2)}
        other = a.right if name == "left" else a.left
        r["psnr_against_other_eye"] = round(psnr(region, ffmpeg_scale(other, a.w, a.h, a.flags)), 2)
        if a.twice:
            tw, th = map(int, a.twice.split("x"))
            with tempfile.TemporaryDirectory() as d:
                mid = os.path.join(d, "m.png")
                Image.fromarray(ffmpeg_scale(eye_png, tw, th, "bilinear").astype(np.uint8)).save(mid)
                r["psnr_two_resizes"] = round(psnr(region, ffmpeg_scale(mid, a.w, a.h, a.flags)), 2)
        mask = np.ones(eye.shape[:2], bool)
        mask[a.y:a.y + a.h, a.x:a.x + a.w] = False
        r["outside_max"] = int(eye[mask].max()) if mask.any() else 0
        if a.find or a.ignore_outside:
            r["outside_max"] = 0  # the window's own 2D parts surround the region
        r["pass"] = bool(r["psnr_one_resize"] >= 35 and r["outside_max"] <= 2 and r["psnr_one_resize"] > r["psnr_against_other_eye"] + 3
                         and r["psnr_one_resize"] > r.get("psnr_two_resizes", -1))
        ok &= r["pass"]
        report[name] = r
        if a.out:
            os.makedirs(a.out, exist_ok=True)
            Image.fromarray(region).save(os.path.join(a.out, name + "-region.png"))
            Image.fromarray(ref.astype(np.uint8)).save(os.path.join(a.out, name + "-ffmpeg.png"))
    report["pass"] = bool(ok)
    print(json.dumps(report))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
