#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""analyze-kwin.py DIR: checks the frames Stereo KWin scanned out on the VKMS stereo device (drm-grab PPMs
from guest/phases/kwin-steps.sh) against each layout's packing (HDMI 1.4b), prints PASS/FAIL lines.
A layout whose mode kscreen-doctor did not list is skipped (side by side (full) needs the DRM core's support).

desktop:  the left and right eye regions are identical (the desktop drawn into both eyes) and the
          frame packing active space is black. The headless session has no wallpaper (black).
fullscreen: a fullscreen 2D client with a gradient: identical in both eyes, more than 1000 colours,
          frame packing active space black.
client:   the test window's blue 2D part sits at the same place in both eyes; its 3D area is red
          (left view) in the left eye only and green (right view) in the right eye only, at the
          same place.
client2d: the same window as a plain 2D client: red in both eyes, no green.
Colours are matched exactly (blue 0000ff, red ff0000, green 00ff00); "same place" means the same
bounding box and the same pixel count in both eyes."""
import os, sys
from PIL import Image, ImageChops

def eyes(layout, w, h):
    if layout == "fp":
        v = 1080; vt = 1125
        return (0, 0, w, v), (0, vt, w, v), (0, v, w, vt - v)
    if layout == "sbs-full":
        return (0, 0, w // 2, h), (w // 2, 0, w // 2, h), None
    if layout == "tab":
        return (0, 0, w, h // 2), (0, h // 2, w, h // 2), None
    if layout == "sbs-half":
        return (0, 0, w // 2, h), (w // 2, 0, w // 2, h), None
    return (0, 0, w, h), None, None

def mask(im, rect, rgb):
    """A mode L image of rect: 255 where the pixel is exactly rgb, 0 elsewhere."""
    x0, y0, w, h = rect
    bands = im.crop((x0, y0, x0 + w, y0 + h)).split()
    m = None
    for band, c in zip(bands, rgb):
        b = band.point(lambda v, c=c: 255 if v == c else 0)
        m = b if m is None else ImageChops.darker(m, b)
    return m

def bbox(im, rect, rgb):
    m = mask(im, rect, rgb)
    box = m.getbbox()
    if not box:
        return None
    return box + (m.histogram()[255],)

def same(im, a, b):
    ca = im.crop((a[0], a[1], a[0] + a[2], a[1] + a[3]))
    cb = im.crop((b[0], b[1], b[0] + b[2], b[1] + b[3]))
    m = None
    for band in ImageChops.difference(ca, cb).split():
        nz = band.point(lambda v: 255 if v else 0)
        m = nz if m is None else ImageChops.lighter(m, nz)
    return m.histogram()[255]

fails = 0
def check(name, ok, detail):
    global fails
    fails += not ok
    print("STEREO|check|kwin/%s|%s|%s" % (name, "PASS" if ok else "FAIL", detail))

d = sys.argv[1]
BLUE, RED, GREEN = (0, 0, 255), (255, 0, 0), (0, 255, 0)
labels = {"fp": "(3D-FP)", "sbs-full": "(3D-SBS-full)", "tab": "(3D-TaB)", "sbs-half": "(3D-SBS)", "2d": ""}
listed = open(os.path.join(d, "kscreen-outputs.txt")).read() if os.path.exists(os.path.join(d, "kscreen-outputs.txt")) else ""
for layout in ("fp", "sbs-full", "tab", "sbs-half", "2d"):
    if labels[layout] and labels[layout] not in listed:
        print("STEREO|skip|kwin/%s|mode not listed by kscreen-doctor" % layout)
        continue
    for kind in ("desktop", "fullscreen", "client", "client2d"):
        path = os.path.join(d, "kwin-%s-%s.ppm" % (layout, kind))
        if not os.path.exists(path):
            check("%s-%s" % (layout, kind), False, "no frame")
            continue
        im = Image.open(path).convert("RGB")
        w, h = im.size
        left, right, gap = eyes(layout, w, h)
        tag = "%s-%s %dx%d" % (layout, kind, w, h)
        if kind == "fullscreen":
            colours = len(im.crop((0, 0, left[2], left[3])).getcolors(left[2] * left[3]))
            if right:
                diff = same(im, left, right)
                check(tag, diff == 0 and colours > 1000,
                      "left and right eye differ in %d pixels, %d colours in the left eye" % (diff, colours))
            else:
                check(tag, colours > 1000, "%d colours" % colours)
            if gap:
                g = bbox(im, gap, (0, 0, 0))
                n = g[4] if g else 0
                check(tag + " active space", n == gap[2] * gap[3], "%d of %d pixels black" % (n, gap[2] * gap[3]))
            continue
        if kind == "desktop":
            if right:
                diff = same(im, left, right)
                check(tag, diff == 0, "left and right eye differ in %d pixels" % diff)
            if gap:
                g = bbox(im, gap, (0, 0, 0))
                n = g[4] if g else 0
                check(tag + " active space", n == gap[2] * gap[3], "%d of %d pixels black" % (n, gap[2] * gap[3]))
            if not right:
                check(tag, True, "2D frame %dx%d" % (w, h))
            continue
        if not right:
            b, r, g = bbox(im, left, BLUE), bbox(im, left, RED), bbox(im, left, GREEN)
            want = (r is not None and g is None) if kind == "client" else (r is not None and g is None)
            check(tag, b is not None and want, "blue %s red %s green %s" % (b, r, g))
            continue
        bl, br = bbox(im, left, BLUE), bbox(im, right, BLUE)
        rl, rr = bbox(im, left, RED), bbox(im, right, RED)
        gl, gr = bbox(im, left, GREEN), bbox(im, right, GREEN)
        place = bl is not None and br is not None and bl == br
        if kind == "client":
            ok = place and rl is not None and rr is None and gr is not None and gl is None and rl == gr
        else:
            ok = place and rl is not None and rr is not None and rl == rr and gl is None and gr is None
        check(tag, ok, "blue L %s R %s; red L %s R %s; green L %s R %s" % (bl, br, rl, rr, gl, gr))
print("STEREO|summary|kwin|%d failed" % fails)
sys.exit(1 if fails else 0)
