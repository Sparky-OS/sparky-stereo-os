#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# readable_colours.py COLORS WALLPAPER SURFACES_JSON LEVELS_JSON REPORT.json [--write]: bring every Foreground* of a Plasma
# style's Window, View, Button, Header and Tooltip groups to 4.5:1 or more (WCAG 2.2, target 4.55 for 8-bit rounding)
# on every translucent surface it can sit on, as seen over the look's own wallpaper (the 1st percentile of the pixels
# behind the surface). A failing colour moves in CIE L* only, a* and b* kept as far as sRGB allows, by the smallest step
# that reaches the target (Daniel, 2026-11-25: "yes, fix them. bring them to a readable level"; hues kept).
# Reports each change and the CIEDE2000 distance of the meaningful pairs (normal vision) before and after.
import configparser
import json
import math
import re
import sys

import numpy as np
from PIL import Image

colors_path, wall_path, surfaces, levels, report = sys.argv[1], sys.argv[2], json.loads(sys.argv[3]), json.loads(sys.argv[4]), sys.argv[5]
write = "--write" in sys.argv
TARGET = 4.55
GROUPS = {"Window": ["panel", "top", "dialog", "widget", "translucent"], "View": ["dialog", "widget", "translucent"],
          "Button": ["panel", "top", "dialog"], "Header": ["dialog"], "Tooltip": ["tooltip"]}
PAIRS = [("ForegroundNegative", "ForegroundPositive"), ("ForegroundNegative", "ForegroundNeutral"),
         ("ForegroundPositive", "ForegroundNeutral"), ("ForegroundLink", "ForegroundVisited"),
         ("ForegroundNegative", "ForegroundNormal"), ("ForegroundPositive", "ForegroundNormal"),
         ("ForegroundInactive", "ForegroundNormal")]


def srgb_lin(c):
    c = np.asarray(c, float) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lum(rgb):
    l = srgb_lin(rgb)
    return 0.2126 * l[..., 0] + 0.7152 * l[..., 1] + 0.0722 * l[..., 2]


M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
WHITE = np.array([0.95047, 1.0, 1.08883])


def to_lab(rgb):
    xyz = M @ srgb_lin(rgb) / WHITE
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def in_gamut(lab):
    L, a, b = lab
    fy = (L + 16) / 116
    f = np.array([fy + a / 500, fy, fy - b / 200])
    xyz = np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27)) * WHITE
    lin = np.linalg.solve(M, xyz)
    return bool(np.all(lin >= -1e-6) and np.all(lin <= 1 + 1e-6))


def at_lightness(lab, L):
    """The colour at lightness L with the hue kept: a* and b* as given, scaled down only as far as sRGB requires."""
    for k in np.linspace(1, 0, 101):
        cand = [L, lab[1] * k, lab[2] * k]
        if in_gamut(cand):
            return from_lab(cand)
    return from_lab([L, 0, 0])


def from_lab(lab):
    L, a, b = lab
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    f = np.array([fx, fy, fz])
    xyz = np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27)) * WHITE
    lin = np.linalg.solve(M, xyz)
    lin = np.clip(lin, 0, 1)
    c = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    return [int(round(v)) for v in np.clip(c * 255, 0, 255)]


def ciede2000(c1, c2):
    L1, a1, b1 = to_lab(c1)
    L2, a2, b2 = to_lab(c2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p, h2p = math.degrees(math.atan2(b1, a1p)) % 360, math.degrees(math.atan2(b2, a2p)) % 360
    dL, dC = L2 - L1, C2p - C1p
    dh = 0 if C1p * C2p == 0 else (h2p - h1p if abs(h2p - h1p) <= 180 else h2p - h1p - 360 if h2p > h1p else h2p - h1p + 360)
    dH = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lb, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    hb = h1p + h2p if C1p * C2p == 0 else ((h1p + h2p) / 2 if abs(h1p - h2p) <= 180 else (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2)
    T = 1 - 0.17 * math.cos(math.radians(hb - 30)) + 0.24 * math.cos(math.radians(2 * hb)) + 0.32 * math.cos(math.radians(3 * hb + 6)) - 0.20 * math.cos(math.radians(4 * hb - 63))
    SL = 1 + 0.015 * (Lb - 50) ** 2 / math.sqrt(20 + (Lb - 50) ** 2)
    SC, SH = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    RT = -2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) * math.sin(math.radians(60 * math.exp(-(((hb - 275) / 25) ** 2))))
    return math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH))


if wall_path in ("black", "white"):
    w = np.full((1080, 1920, 3), 0 if wall_path == "black" else 255, float)
else:
    w = np.asarray(Image.open(wall_path).convert("RGB").resize((1920, 1080), Image.BILINEAR), float)
regions = {"panel": w[-56:].reshape(-1, 3), "top": w[:26].reshape(-1, 3)}
anywhere = w[::4, ::4].reshape(-1, 3)
bglum = {}
for s, a8 in levels.items():
    a = a8 / 255
    bglum[s] = lum(a * np.asarray(surfaces[s], float) + (1 - a) * regions.get(s, anywhere))


def worst(rgb, group):
    lt = float(lum(np.asarray(rgb, float)))
    v = []
    for s in GROUPS[group]:
        if s in bglum:
            lb = bglum[s]
            v.append((float(np.percentile((np.maximum(lb, lt) + 0.05) / (np.minimum(lb, lt) + 0.05), 1)), s))
    return min(v)


text = open(colors_path).read()
cp = configparser.ConfigParser(interpolation=None)
cp.optionxform = str
cp.read_string(text)
changes, pairs = [], []
new_values = {}
for g in GROUPS:
    sec = f"Colors:{g}"
    if sec not in cp:
        continue
    for key, val in cp[sec].items():
        if not key.startswith("Foreground"):
            continue
        rgb = [int(x) for x in val.split(",")[:3]]
        w0 = worst(rgb, g)
        if w0[0] >= 4.5:
            continue
        lab = to_lab(rgb)
        # lighter texts move up, darker texts down, judged against the median background they sit on
        med = float(np.median(np.concatenate([bglum[s].ravel() for s in GROUPS[g] if s in bglum])))
        step = 0.25 if float(lum(np.asarray(rgb, float))) > med else -0.25
        new = rgb
        L = lab[0]
        for _ in range(400):
            L = min(100, max(0, L + step))
            new = at_lightness(lab, L)
            if worst(new, g)[0] >= TARGET or L in (0, 100):
                break
        w1 = worst(new, g)
        new_values[(sec, key)] = new
        changes.append({"group": g, "key": key, "before": rgb, "after": new, "worst_before": round(w0[0], 2),
                        "surface": w0[1], "worst_after": round(w1[0], 2), "deltaE2000": round(ciede2000(rgb, new), 1)})
# a meaningful pair that came closer than 5 (CIEDE2000) and closer than it was: its second colour moves further the
# way it moved (more contrast, never less) until the pair is 5 apart again or the colour reaches the end of its range
for g in GROUPS:
    sec = f"Colors:{g}"
    if sec not in cp:
        continue
    cur = {k: [int(x) for x in v.split(",")[:3]] for k, v in cp[sec].items() if k.startswith("Foreground")}
    for p, q in PAIRS:
        if p not in cur or q not in cur or (sec, q) not in new_values:
            continue
        a_p, a_q = new_values.get((sec, p), cur[p]), new_values[(sec, q)]
        before = ciede2000(cur[p], cur[q])
        if ciede2000(a_p, a_q) >= min(5, before):
            continue
        lab = to_lab(cur[q])
        L = to_lab(a_q)[0]
        step = 0.25 if L > lab[0] else -0.25
        while ciede2000(a_p, a_q) < min(5, before) and 0 < L < 100:
            L = min(100, max(0, L + step))
            a_q = at_lightness(lab, L)
        new_values[(sec, q)] = a_q
        for c in changes:
            if c["group"] == g and c["key"] == q:
                c["after"], c["worst_after"], c["deltaE2000"] = a_q, round(worst(a_q, g)[0], 2), round(ciede2000(cur[q], a_q), 1)
                c["moved_for_pair"] = f"{p[10:]}/{q[10:]}"
for g in GROUPS:
    sec = f"Colors:{g}"
    if sec not in cp:
        continue
    cur = {k: [int(x) for x in v.split(",")[:3]] for k, v in cp[sec].items() if k.startswith("Foreground")}
    aft = {k: new_values.get((sec, k), v) for k, v in cur.items()}
    for p, q in PAIRS:
        if p in cur and q in cur:
            pairs.append({"group": g, "pair": f"{p[10:]}/{q[10:]}", "before": round(ciede2000(cur[p], cur[q]), 1),
                          "after": round(ciede2000(aft[p], aft[q]), 1)})
json.dump({"colors": colors_path, "wallpaper": wall_path, "levels": levels, "changes": changes, "pairs": pairs},
          open(report, "w"), indent=1)
if write:
    for (sec, key), rgb in new_values.items():
        section = re.search(r"(?m)^\[" + re.escape(sec) + r"\]\n(?:(?!\[).*\n?)*", text)
        body = section.group(0)
        body2 = re.sub(r"(?m)^" + re.escape(key) + r"=.*$", f"{key}={rgb[0]},{rgb[1]},{rgb[2]}", body, count=1)
        text = text[:section.start()] + body2 + text[section.end():]
    open(colors_path, "w").write(text)
for c in changes:
    print(f"{c['group']:8} {c['key']:20} {c['before']} -> {c['after']}  worst {c['worst_before']} -> {c['worst_after']} ({c['surface']})  dE {c['deltaE2000']}")
for p in pairs:
    if p["after"] < 5 or p["before"] < 5:
        print(f"pair {p['group']:8} {p['pair']:22} dE2000 {p['before']} -> {p['after']}")
