#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""analyze-eyeorder.py RUN: checks the frames of an eyeorder matrix run (guest/eyeorder/steps.sh).

The reference (ref.ppm) is the 2D mode with the eye swap off: the blue 2D window and the left view (red) of the
declared subsurface. L is that frame, R the same frame with the subsurface's pixels green (the right view).
For every 3D mode, with the output's swap off and on, the scanned-out frame is compared with the packing's model
built from (L, R) or, with the swap on, from (R, L); the other swap's model is the negative control and must fail
on every pixel where the eyes differ. Right-first twins must equal the left-first twin with the swap flipped.
Models (the mesa-stereo lane's, vkms-bench/scripts/analyze-kscreen.py): anaglyph = encode(Ml*decode(L)+Mr*decode(R)) with
KWin's Dubois sets and gamma 2.2; rows, columns, checkerboard by the parity of the scanout line, column or both,
left eye on the even ones for left first; side by side half and top and bottom: each eye halved, left or top first;
side by side full and frame sequential: left eye in the left half of the packed frame (right eye first starts on the right half instead, so its packed frame is the same); frame packing: eyes at lines 0 and 1125 of 2205."""
import json, os, re, sys
import numpy as np
from PIL import Image

RUN = sys.argv[1]
TOL = 2
RED, GREEN, BLUE = np.array([255, 0, 0]), np.array([0, 255, 0]), np.array([0, 0, 255])
MODERN = (np.array([[0.4154, 0.4710, 0.1669], [-0.0458, -0.0484, -0.0257], [-0.0547, -0.0615, 0.0128]]),
          np.array([[-0.0109, -0.0364, -0.0060], [0.3756, 0.7333, 0.0111], [-0.0651, -0.1287, 1.2971]]))
CRT = (np.array([[0.456, 0.500, 0.176], [-0.040, -0.038, -0.016], [-0.015, -0.021, -0.005]]),
       np.array([[-0.043, -0.088, -0.002], [0.378, 0.734, -0.018], [-0.072, -0.113, 1.226]]))
results, fails = {}, 0


def check(name, ok, detail):
    global fails
    fails += not ok
    print("STEREO|check|eyeorder/%s|%s|%s" % (name, "PASS" if ok else "FAIL", detail))
    results[name] = {"pass": bool(ok), "detail": detail}


def load(tag):
    for ext in (".ppm", ".png"):
        p = os.path.join(RUN, tag + ext)
        if os.path.exists(p):
            return np.asarray(Image.open(p).convert("RGB")).astype(np.int32)
    return None


def decode(c8):
    return (c8 / 255.0) ** 2.2


def encode(v):
    return np.floor(np.rint(np.clip(v, 0, 1) ** (1 / 2.2) * 65535) / 256).astype(np.int32)


def anaglyph(L, R, m):
    return encode(np.maximum(decode(L) @ m[0].T + decode(R) @ m[1].T, 0.0))


def pattern(L, R, kind, right_first=0):
    h, w, _ = L.shape
    y, x = np.mgrid[0:h, 0:w]
    parity = {"rows": y, "columns": x, "checkerboard": x + y}[kind]
    return np.where((((parity + right_first) % 2) == 1)[..., None], R, L)


def squeeze(L, R, axis):
    def half(e):
        return (e[:, 0::2] + e[:, 1::2]) / 2 if axis == 1 else (e[0::2] + e[1::2]) / 2
    return np.concatenate([half(L), half(R)], axis=axis)


def packed_fp(L, R):
    out = np.zeros((2205, L.shape[1], 3), dtype=np.int32)
    out[0:1080] = L
    out[1125:2205] = R
    return out


ref = load("ref")
if ref is None:
    check("ref", False, "no reference frame")
    sys.exit(1)
area = np.all(ref == RED, axis=2)
check("ref", ref.shape == (1080, 1920, 3) and area.sum() > 0 and not np.all(ref == GREEN, axis=2).any(),
      "%dx%d, the left view (red) fills %d pixels" % (ref.shape[1], ref.shape[0], area.sum()))
L = ref
R = np.where(area[..., None], GREEN, ref)

# tag -> model(a, b) where a is the first eye of the packing and b the second
MODELS = {
    "anaglyph-modern": lambda a, b: anaglyph(a, b, MODERN),
    "anaglyph-crt": lambda a, b: anaglyph(a, b, CRT),
    "twin-sbs-half": lambda a, b: squeeze(a, b, 1),
    "twin-tab": lambda a, b: squeeze(a, b, 0),
    "rows-left": lambda a, b: pattern(a, b, "rows", 0),
    "rows-right": lambda a, b: pattern(a, b, "rows", 1),
    "columns-left": lambda a, b: pattern(a, b, "columns", 0),
    "columns-right": lambda a, b: pattern(a, b, "columns", 1),
    "checkerboard-left": lambda a, b: pattern(a, b, "checkerboard", 0),
    "checkerboard-right": lambda a, b: pattern(a, b, "checkerboard", 1),
    "fs-left": lambda a, b: np.concatenate([a, b], axis=1),
    "fs-right": lambda a, b: np.concatenate([a, b], axis=1),
    "hdmi-sbs-half": lambda a, b: squeeze(a, b, 1),
    "hdmi-tab": lambda a, b: squeeze(a, b, 0),
    "hdmi-sbs-full": lambda a, b: np.concatenate([a, b], axis=1),
    "hdmi-fp": packed_fp,
}
frames = {}
for tag, model in MODELS.items():
    for sw in (0, 1):
        A = load("%s-s%d" % (tag, sw))
        frames[(tag, sw)] = A
        if A is None:
            check("%s swap %s" % (tag, "on" if sw else "off"), False, "no frame")
            continue
        want = np.rint(model(R, L) if sw else model(L, R)).astype(np.int32)
        other = np.rint(model(L, R) if sw else model(R, L)).astype(np.int32)
        if A.shape != want.shape:
            check("%s swap %s" % (tag, "on" if sw else "off"), False, "frame %s, expected %s" % (A.shape, want.shape))
            continue
        diff = np.abs(A - want).max(axis=2)
        differ = np.any(want != other, axis=2)
        ctl = np.abs(A - other).max(axis=2)
        ok = bool((diff <= TOL).all())
        ctl_match = int(((ctl <= TOL) & differ).sum())
        check("%s swap %s" % (tag, "on" if sw else "off"), ok and differ.sum() > 0 and ctl_match == 0,
              "%dx%d: %d of %d pixels within %d of the model (max %d, %d exact); negative control (the other swap's model): %d of the %d pixels where the eyes differ match it"
              % (A.shape[1], A.shape[0], int((diff <= TOL).sum()), diff.size, TOL, int(diff.max()), int((diff == 0).sum()),
                 ctl_match, int(differ.sum())))
# the 2D output shows the left eye, its swap the right eye
for sw, eye, name in ((0, L, "left"), (1, R, "right")):
    A = load("plain-s%d" % sw)
    if A is not None and A.shape == eye.shape:
        n = int(np.any(A != eye, axis=2).sum())
        check("plain 2D swap %s shows the %s view" % ("on" if sw else "off", name), n == 0, "%d pixels differ" % n)
# a right-first twin equals the left-first twin with the swap flipped
for kind in ("rows", "columns", "checkerboard"):
    for sw in (0, 1):
        a, b = frames.get((kind + "-right", sw)), frames.get((kind + "-left", 1 - sw))
        if a is None or b is None or a.shape != b.shape:
            check("%s right-first swap %d equals left-first swap %d" % (kind, sw, 1 - sw), False, "frames missing")
            continue
        n = int(np.any(a != b, axis=2).sum())
        check("%s right-first swap %s equals left-first swap %s" % (kind, "on" if sw else "off", "off" if sw else "on"),
              n == 0, "%d of %d pixels differ" % (n, a.size // 3))
# frame sequential: which half the plane shows on each refresh
for tag in ("fs-left", "fs-right"):
    for sw in (0, 1):
        p = os.path.join(RUN, "flips-%s-s%d.txt" % (tag, sw))
        if os.path.exists(p):
            xs = [int(m.group(1)) for m in re.finditer(r"src_x (-?\d+)", open(p).read())]
            ch = sum(1 for a, b in zip(xs, xs[1:]) if a != b)
            half_eye = "R" if sw else "L"
            print("STEREO|info|eyeorder/%s swap %d flips|%d samples, SRC_X values %s (the left half of the packed frame holds the %s view), %d changes"
                  % (tag, sw, len(xs), sorted(set(xs)), "right" if sw else "left", ch))
            results["%s swap %d flips" % (tag, sw)] = {"samples": len(xs), "values": sorted(set(xs)), "changes": ch}
A = load("back-2d")
if A is not None:
    n = int(np.any(A != ref, axis=2).sum()) if A.shape == ref.shape else -1
    check("back to 2D equals the reference", n == 0, "%d pixels differ" % n)
print("STEREO|summary|eyeorder|%d failed" % fails)
json.dump({"tolerance": TOL, "failed": fails, "checks": results}, open(os.path.join(RUN, "analysis.json"), "w"), indent=1)
sys.exit(1 if fails else 0)
