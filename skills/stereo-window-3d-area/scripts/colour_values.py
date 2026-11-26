#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""The numbers of the colour test. For colours given in linear sRGB (Rec. 709 primaries, 1.0 = reference white) it
prints the values an area writes when its colour state is STATE, and what is expected of them:

  colour_values.py STATE [MODEL [PEAK]]   ->  one line per patch: name, the --patch argument, the expected triple

MODEL says who turns the area's values into the output's:
  gtk       GTK itself (a plain area, drawn into the window): 8-bit sRGB values, IEC 61966-2-1's own curve.
  kwin      KWin, from the description it received for the area's own surface (a stereo area), on an SDR output:
            8-bit values with KWin's gamma 2.2 for sRGB. PQ content comes with no luminances (GDK has none to send),
            so KWin takes PQ's defaults (reference white 203, peak 10000 cd/m2) and its perceptual intent compresses
            that range into the output's with its tone curve (src/core/colorpipeline.cpp, ColorTonemapper), which at
            most halves the reference white.
  kwin-hdr  KWin on an HDR output (Rec. 2020, PQ, reference white 203 cd/m2, peak PEAK cd/m2): the PQ values the
            output's buffer holds, as floats, after the same tone curve from 10000 to PEAK.

Rec. ITU-R BT.2100-3 table 4 (PQ EOTF and its inverse) and table 7 (ICtCp), Rec. ITU-R BT.2020-2 table 3 with BT.709-6
items 1.3 and 1.4 (the primaries, hence the matrix), IEC 61966-2-1 (the sRGB transfer function); reference white of PQ
content at 203 cd/m2 (Report ITU-R BT.2408-8, 2.1).
"""
import sys

PATCHES = [("white", (1.0, 1.0, 1.0)), ("half", (0.5, 0.5, 0.5)), ("orange", (0.5, 0.25, 0.125)),
           ("red", (0.6, 0.05, 0.05)), ("blue", (0.05, 0.1, 0.6)), ("dark", (0.05, 0.05, 0.05))]
# linear Rec. 709 to linear Rec. 2020 (from the two sets of primaries with D65)
M = [(0.6274039, 0.3292830, 0.0433131), (0.0690973, 0.9195404, 0.0113623), (0.0163914, 0.0880133, 0.8955953)]
# BT.2100 table 7: linear Rec. 2020 to LMS, and L'M'S' to ICtCp
LMS = [(1688 / 4096, 2146 / 4096, 262 / 4096), (683 / 4096, 2951 / 4096, 462 / 4096), (99 / 4096, 309 / 4096, 3688 / 4096)]
ICTCP = [(0.5, 0.5, 0.0), (6610 / 4096, -13613 / 4096, 7003 / 4096), (17933 / 4096, -17390 / 4096, -543 / 4096)]
REFERENCE_WHITE = 203.0
M1, M2, C1, C2, C3 = 2610 / 16384, 2523 / 4096 * 128, 3424 / 4096, 2413 / 4096 * 32, 2392 / 4096 * 32


def mul(m, v):
    return [sum(m[i][j] * v[j] for j in range(3)) for i in range(3)]


def inverse(m):
    (a, b, c), (d, e, f), (g, h, i) = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    return [((e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det),
            ((f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det),
            ((d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det)]


def pq_inverse_eotf(nits):
    y = max(nits, 0.0) / 10000.0
    return ((C1 + C2 * y ** M1) / (1 + C3 * y ** M1)) ** M2


def pq_eotf(code):
    p = max(code, 0.0) ** (1 / M2)
    return 10000.0 * (max(p - C1, 0.0) / (C2 - C3 * p)) ** (1 / M1)


def srgb_oetf(v):
    v = min(max(v, 0.0), 1.0)
    return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055


def gamma22(v):
    return min(max(v, 0.0), 1.0) ** (1 / 2.2)


def tone_map(wide_nits, reference, peak_in, peak_out):
    """KWin's ColorTonemapper on the intensity of ICtCp: x(1 + xv)/(1 + x) on the luminance relative to the reference"""
    in_range, out_range = peak_in / reference, peak_out / reference
    v = (out_range * (1 + in_range) - in_range) / in_range ** 2
    ictcp = mul(ICTCP, [pq_inverse_eotf(c) for c in mul(LMS, wide_nits)])
    x = max(pq_eotf(ictcp[0]) / reference, 0.0)
    ictcp[0] = pq_inverse_eotf(x * (1 + x * v) / (1 + x) * reference)
    lms = [pq_eotf(c) for c in mul(inverse(ICTCP), ictcp)]
    return mul(inverse(LMS), lms)


def values(state, rgb):
    wide = mul(M, rgb)
    if state == "rec2100-pq":
        return [pq_inverse_eotf(REFERENCE_WHITE * c) for c in wide]
    if state == "rec2100-linear":
        return wide
    if state == "rec2100-hlg":
        # BT.2100-3 table 5: display light back to scene light through the inverse OOTF (system gamma 1.2 for a
        # display of 1000 cd/m2, the reference white at 203), then the HLG OETF; the form GDK's own conversion has
        import math
        a, b, c = 0.17883277, 0.28466892, 0.55991073
        yd = 0.2627 * wide[0] + 0.6780 * wide[1] + 0.0593 * wide[2]
        scale = (REFERENCE_WHITE / 1000.0) ** (1 / 1.2) * yd ** (1 / 1.2 - 1) if yd > 0 else 0.0
        scene = [max(x * scale, 0.0) for x in wide]
        return [math.sqrt(3 * e) if e <= 1 / 12 else a * math.log(12 * e - b) + c for e in scene]
    if state == "srgb-linear":
        return list(rgb)
    if state == "srgb":
        return [srgb_oetf(c) for c in rgb]
    raise SystemExit("unknown colour state " + state)


def expected(state, model, rgb, peak):
    if model == "gtk":
        return [round(255 * srgb_oetf(c)) for c in rgb]
    if model == "kwin":
        if state == "srgb":
            # described as gamma 2.2 and shown on a gamma 2.2 output: the written values themselves
            return [round(255 * srgb_oetf(c)) for c in rgb]
        if state == "rec2100-hlg":
            raise SystemExit("KWin lists no hybrid log-gamma transfer function: a stereo area in it is not shown per eye")
        if state == "rec2100-pq":
            # KWin scales the reference white of the content to the output's and tone maps in the output's primaries:
            # the same numbers as doing it at 203 cd/m2 in Rec. 2020, which is done here
            mapped = tone_map([REFERENCE_WHITE * c for c in mul(M, rgb)], REFERENCE_WHITE, 10000.0, REFERENCE_WHITE)
            narrow = mul(inverse(M), mapped)
            return [round(255 * gamma22(c / REFERENCE_WHITE)) for c in narrow]
        return [round(255 * gamma22(c)) for c in rgb]
    if model == "kwin-hdr":
        if state == "srgb":
            # KWin reads the written sRGB values with gamma 2.2 and puts their white at the output's reference white
            rgb = [srgb_oetf(c) ** 2.2 for c in rgb]
        nits = [REFERENCE_WHITE * c for c in mul(M, rgb)]
        if state == "rec2100-pq" and peak < 10000.0:
            nits = tone_map(nits, REFERENCE_WHITE, 10000.0, peak)
        return [pq_inverse_eotf(c) for c in nits]
    raise SystemExit("unknown model " + model)


def main():
    state = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "gtk"
    peak = float(sys.argv[3]) if len(sys.argv) > 3 else 1000.0
    for name, rgb in PATCHES:
        v = values(state, rgb)
        e = expected(state, model, rgb, peak)
        fmt = "%.5f,%.5f,%.5f" if model == "kwin-hdr" else "%d,%d,%d"
        print(("%s %.6f,%.6f,%.6f " + fmt) % (name, v[0], v[1], v[2], e[0], e[1], e[2]))


if __name__ == "__main__":
    main()
