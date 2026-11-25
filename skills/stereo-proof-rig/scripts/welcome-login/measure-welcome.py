#!/usr/bin/env python3
# measure-welcome.py KIND CAPTURE WINDOWS.json [SOURCE.pns | PLAIN.png] > rows.json
# Measures one capture of the Welcome window against the prediction written before the run (ORDER 63/720).
# KIND page1: CAPTURE is a 3D output's capture (both eyes side by side, each 1920x1080); SOURCE is the first page's
#   stereo picture. Prediction: inside the Welcome window the eyes differ only inside one box, the picture (the words
#   and the button at the screen, 0 differing pixels outside it); in that box each eye is its own view of the source
#   (the left eye nearer to the source's left view than to its right view, and the right eye the other way).
# KIND page2: CAPTURE as above, then SUNK and the same page's capture on a 2D output. Prediction at the person's sunk
#   limit S and a 1920-wide view: the drawing's window behind at depth -0.2, parallax round(-0.2 * S) = -2 at S=10: its
#   inner bars 1 px left in the left eye and 1 px right in the right eye of their 2D place (disparity, left minus right,
#   -2; its outline is cut to its 2D rectangle), the window under the pointer and everything else at 0.
# KIND flat2d: CAPTURE is a 2D output's capture of the first page (1920x1080), then SOURCE and the page1 rows of the
#   3D output. Prediction: one picture, and the source's left view where the 3D output showed the pair.
import json
import os
import sys

import numpy as np
from PIL import Image


# the least PSNR of an eye against its own view: 30 dB where the output shows the views at their own pixels; at a
# fractional scale the compositor resamples them and MEASURE_MIN_DB lowers it (each eye stays 5 dB nearer its own view)
MIN_DB = float(os.environ.get("MEASURE_MIN_DB", "30"))


def welcome_frame(windows):
    # KWin gives the frame in the desktop's logical pixels; a capture is one output in device pixels: MEASURE_SCALE (the
    # output's scale) and MEASURE_ORIGIN_X, MEASURE_ORIGIN_Y (the output's place on the desktop) map one to the other
    s = float(os.environ.get("MEASURE_SCALE", "1"))
    ox, oy = float(os.environ.get("MEASURE_ORIGIN_X", "0")), float(os.environ.get("MEASURE_ORIGIN_Y", "0"))
    data = json.load(open(windows))
    for w in (data["windows"] if isinstance(data, dict) else data):
        if w["cls"] in ("org.kde.plasma-welcome", "plasma-welcome"):
            x, y, ww, hh = w["fg"]
            return [int(round((x - ox) * s)), int(round((y - oy) * s)), int(round(ww * s)), int(round(hh * s))]
    raise SystemExit("no Welcome window in " + windows)


def eyes(capture):
    a = np.asarray(Image.open(capture).convert("RGB")).astype(np.int32)
    h, w, _ = a.shape
    if w != 2 * h * 16 // 9 and w != 3840:
        raise SystemExit("not a pair of 1920x1080 eyes: %dx%d" % (w, h))
    return a[:, : w // 2], a[:, w // 2:]


def box_of(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def psnr(a, b):
    mse = float(((a.astype(np.float64) - b.astype(np.float64)) ** 2).mean())
    return 99.0 if mse == 0 else 10 * np.log10(255 * 255 / mse)


def page1(capture, windows, source):
    x, y, w, h = welcome_frame(windows)
    left, right = eyes(capture)
    L, R = left[y:y + h, x:x + w], right[y:y + h, x:x + w]
    diff = (np.abs(L - R).sum(axis=2) > 24)
    box = box_of(diff)
    out = {"kind": "page1", "frame": [x, y, w, h], "differing_pixels": int(diff.sum()), "diff_box": box}
    if box is None:
        out["verdict"] = "FLAT: the eyes do not differ inside the window"
        return out
    bx0, by0, bx1, by1 = box
    # the picture's box: the left eye's pixels that are not the window's own background, around the differing box
    cy = (by0 + by1) // 2
    bg = np.median(L[cy, 4:12], axis=0)
    ys0, ys1 = max(0, by0 - 80), min(h, by1 + 80)
    mask = np.zeros(diff.shape, bool)
    mask[ys0:ys1, 6:w - 6] = np.abs(L[ys0:ys1, 6:w - 6] - bg).sum(axis=2) > 18
    cols = np.nonzero(mask[ys0:ys1].sum(axis=0) > 0.5 * (by1 - by0))[0]
    lines = np.nonzero(mask[:, bx0:bx1].sum(axis=1) > 0.5 * (bx1 - bx0))[0]
    x0, x1, y0 = int(cols.min()), int(cols.max()) + 1, int(lines.min())
    src = Image.open(source).convert("RGB")
    sw, sh = src.size
    y1 = y0 + round((x1 - x0) * sh / (sw // 2))
    out["picture_box"] = [x0, y0, x1 - x0, y1 - y0]
    out["window_background"] = [int(v) for v in bg]
    outside = diff.copy()
    outside[y0:y1, x0:x1] = False
    out["differing_outside_picture"] = int(outside.sum())
    sl, sr = src.crop((0, 0, sw // 2, sh)), src.crop((sw // 2, 0, sw, sh))
    ww, hh = x1 - x0, y1 - y0
    el, er = L[y0:y1, x0:x1], R[y0:y1, x0:x1]
    vl = np.asarray(sl.resize((ww, hh), Image.Resampling.BOX)).astype(np.int32)
    vr = np.asarray(sr.resize((ww, hh), Image.Resampling.BOX)).astype(np.int32)
    out["left_eye_vs_left_view_db"] = round(psnr(el, vl), 2)
    out["left_eye_vs_right_view_db"] = round(psnr(el, vr), 2)
    out["right_eye_vs_right_view_db"] = round(psnr(er, vr), 2)
    out["right_eye_vs_left_view_db"] = round(psnr(er, vl), 2)
    ok = (out["differing_outside_picture"] == 0
          and out["left_eye_vs_left_view_db"] > out["left_eye_vs_right_view_db"]
          and out["right_eye_vs_right_view_db"] > out["right_eye_vs_left_view_db"]
          and out["left_eye_vs_left_view_db"] >= MIN_DB and out["right_eye_vs_right_view_db"] >= MIN_DB
          and out["left_eye_vs_left_view_db"] - out["left_eye_vs_right_view_db"] >= 5
          and out["right_eye_vs_right_view_db"] - out["right_eye_vs_left_view_db"] >= 5)
    out["min_db"] = MIN_DB
    out["verdict"] = "PASS" if ok else "FAIL"
    return out


def first_x(eye, rows_range, colour, tol=6):
    c = np.array(colour)
    xs = []
    for yy in rows_range:
        m = np.nonzero((np.abs(eye[yy] - c).max(axis=1) <= tol))[0]
        if len(m):
            xs.append(int(m.min()))
    return xs


def colour_span(img, row, colour, tol=3, least=10):
    # the bars are long spans: a lone pixel of the colour on an edge resampled at a fractional scale is not one
    m = np.nonzero(np.abs(img[row] - np.array(colour)).max(axis=1) <= tol)[0]
    return (int(m.min()), int(m.max())) if len(m) >= least else None


def page2(capture, windows, sunk, plain=None):
    # The drawing's window behind at depth -0.2: parallax round(-0.2 * sunk) at a 1920-wide view, split as the edition's
    # Qt Quick splits it (the right eye -trunc(p/2), the left the rest). Its outline is cut to its 2D rectangle, so the
    # shift is read on its inner bars (#77818d), away from its edges. The window under the pointer (title #3a6fa8) and
    # every other pixel of the page stay at the screen.
    x, y, w, h = welcome_frame(windows)
    left, right = eyes(capture)
    L, R = left[y:y + h, x:x + w], right[y:y + h, x:x + w]
    p = int(round(-0.2 * sunk))
    right_shift = -int(p / 2)
    left_shift = p + right_shift
    out = {"kind": "page2", "frame": [x, y, w, h], "predicted_parallax": p,
           "predicted_left_shift": left_shift, "predicted_right_shift": right_shift}
    P = None
    if plain:
        b = np.asarray(Image.open(plain).convert("RGB")).astype(np.int32)
        P = b[y:y + h, x:x + w]
    bars = []
    front = []
    for row in range(h):
        sl, sr = colour_span(L, row, (0x77, 0x81, 0x8d)), colour_span(R, row, (0x77, 0x81, 0x8d))
        if sl and sr:
            bars.append((row, sl[0], sr[0], colour_span(P, row, (0x77, 0x81, 0x8d))[0] if P is not None and colour_span(P, row, (0x77, 0x81, 0x8d)) else None))
        fl, fr = colour_span(L, row, (0x3a, 0x6f, 0xa8)), colour_span(R, row, (0x3a, 0x6f, 0xa8))
        if fl and fr:
            front.append((row, fl, fr, colour_span(P, row, (0x3a, 0x6f, 0xa8)) if P is not None else None))
    out["bar_rows"] = len(bars)
    out["front_title_rows"] = len(front)
    if bars:
        d = [a - b for _, a, b, _ in bars]
        out["back_disparity_left_minus_right"] = int(np.median(d))
        out["back_disparity_spread"] = [int(min(d)), int(max(d))]
        if P is not None:
            ls = [a - c for _, a, _, c in bars if c is not None]
            rs = [b - c for _, _, b, c in bars if c is not None]
            out["back_left_shift_vs_2d"] = int(np.median(ls)) if ls else None
            out["back_right_shift_vs_2d"] = int(np.median(rs)) if rs else None
    if front:
        out["front_disparity_left_minus_right"] = int(np.median([fl[0] - fr[0] for _, fl, fr, _ in front]))
        if P is not None:
            out["front_shift_vs_2d"] = int(np.median([fl[0] - f2[0] for _, fl, _, f2 in front if f2]))
    diff = (np.abs(L - R).sum(axis=2) > 24)
    out["differing_pixels"] = int(diff.sum())
    out["diff_box"] = box_of(diff)
    ok = (bars and front and out["back_disparity_left_minus_right"] == p and out["back_disparity_spread"] == [p, p]
          and out["front_disparity_left_minus_right"] == 0)
    if P is not None:
        ok = ok and out.get("back_left_shift_vs_2d") == left_shift and out.get("back_right_shift_vs_2d") == right_shift \
            and out.get("front_shift_vs_2d") == 0
    out["verdict"] = "PASS" if ok else "FAIL"
    return out


def flat2d(capture, windows, source, page1_rows):
    # A 2D output: one picture (no pair), and the first page's picture shows the source's left view where the 3D output
    # showed the pair (the box the page1 measure found).
    a = np.asarray(Image.open(capture).convert("RGB")).astype(np.int32)
    x, y, w, h = welcome_frame(windows)
    out = {"kind": "flat2d", "size": [int(a.shape[1]), int(a.shape[0])], "frame": [x, y, w, h]}
    bx, by, bw, bh = json.load(open(page1_rows))["picture_box"]
    P = a[y + by:y + by + bh, x + bx:x + bx + bw]
    src = Image.open(source).convert("RGB")
    sw, sh = src.size
    vl = np.asarray(src.crop((0, 0, sw // 2, sh)).resize((bw, bh), Image.Resampling.BOX)).astype(np.int32)
    vr = np.asarray(src.crop((sw // 2, 0, sw, sh)).resize((bw, bh), Image.Resampling.BOX)).astype(np.int32)
    out["picture_vs_left_view_db"] = round(psnr(P, vl), 2)
    out["picture_vs_right_view_db"] = round(psnr(P, vr), 2)
    ok = a.shape[1] == 1920 and out["picture_vs_left_view_db"] >= 30 and out["picture_vs_left_view_db"] > out["picture_vs_right_view_db"]
    out["verdict"] = "PASS" if ok else "FAIL"
    return out


if __name__ == "__main__":
    kind = sys.argv[1]
    if kind == "page1":
        out = page1(sys.argv[2], sys.argv[3], sys.argv[4])
    elif kind == "page2":
        out = page2(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 10.0,
                    sys.argv[5] if len(sys.argv) > 5 else None)
    elif kind == "flat2d":
        out = flat2d(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        raise SystemExit("kind: page1, page2 or flat2d")
    print(json.dumps(out))
