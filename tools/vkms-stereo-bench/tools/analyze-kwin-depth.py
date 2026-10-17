#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""analyze-kwin-depth.py DIR: checks the frames of guest/phases/kwin-depth-steps.sh, Stereo KWin on a VKMS
device whose EDID declares every HDMI 1.4a 3D structure, and prints PASS/FAIL lines.

Parallax is the right eye's position minus the left eye's, in pixels of one eye (positive behind the screen).
It is measured between the eyes of side by side (full) and frame packing, where each window and the
depth client's noise patch are found in both eyes, and read from the depth picture of L + depth with the
3D metadata the kernel holds (HDMI 1.4a, Table H-4: parallax_zero, parallax_scale, dref and wref, 16 bits
each): p = (sample - parallax_zero) / parallax_scale centimetres on wref centimetres, our reading of ISO/IEC
23002-3, 6.1.2.2 and 6.2.2.2 (unverified against the standard). The checks:

listing      kscreen-doctor lists line alternative, L + depth and L + depth + graphics + graphics-depth.
sbs-full     the depth client's window at the same place in both eyes (active, at the screen), the orange
             window sunk behind, the patch 8 pixels behind; the timing property says the whole line is doubled.
l-depth      the frame (Figure H-5): the picture, then black, then the depth from line vtotal on; the depth of
             each window is the parallax measured between the eyes, the patch's within a pixel (estimated),
             the background at the screen; the metadata is parallax information.
desktop      only the desktop's depth: the patch at its window's level.
flat         every depth sample at the screen; the patch's check fails (the control: depth ignored).
250          the metadata says a viewing distance of 250 cm.
swapped      the client's views exchanged: the patch at -8; the +8 check fails (the control of the sign).
line-alt     the frame is twice as tall, the left eye on even lines, the right eye on odd lines (Figure H-3).
sbs-kept     with the blanking kept the property says so and the eyes are as before.
l-depth-gfx  the frame (Figure H-6): the popup only in the graphics, at the parallax measured in frame
             packing in the graphics' depth, and not in the picture's depth.
2d           with no depth levels, the picture of L + depth with flat depth is the 2D mode's frame."""
import os
import sys

from PIL import Image, ImageChops

BLUE, ORANGE, YELLOW, RED, GREEN = (0, 0, 255), (255, 128, 0), (255, 255, 0), (255, 0, 0), (0, 255, 0)
PATCH = (80, 40, 320, 160)
fails = 0


def check(name, ok, detail):
    global fails
    fails += not ok
    print("STEREO|check|kwin-depth/%s|%s|%s" % (name, "PASS" if ok else "FAIL", detail))


def info(d, tag):
    path = os.path.join(d, "depth-grab-%s.txt" % tag)
    ret = {"timing": None, "metadata": None}
    if not os.path.exists(path):
        return None
    for line in open(path):
        words = line.split()
        if words[:1] == ["mode"]:
            ret["mode"] = tuple(int(v) for v in words[2].split("x")) + tuple(int(v) for v in words[4].split("x"))
        elif len(words) >= 3 and words[0] == "connector" and words[2] == "sbs-full-timing":
            ret["timing"] = int(words[3])
        elif len(words) >= 3 and words[0] == "connector" and words[2] == "3d-metadata":
            ret["metadata"] = None if words[3:] == ["none"] else [int(v, 16) for v in words[3:]]
    return ret


def frame(d, tag):
    path = os.path.join(d, "depth-%s.ppm" % tag)
    return Image.open(path).convert("RGB") if os.path.exists(path) else None


def mask(im, rect, rgb):
    x, y, w, h = rect
    m = None
    for band, c in zip(im.crop((x, y, x + w, y + h)).split(), rgb):
        b = band.point(lambda v, c=c: 255 if v == c else 0)
        m = b if m is None else ImageChops.darker(m, b)
    return m


def count(m):
    return m.histogram()[255]


def shift_between(left, right, lo=-30, hi=30):
    """The horizontal shift of mask right against mask left with the most pixels in common."""
    best, score = None, -1
    for s in range(lo, hi + 1):
        n = count(ImageChops.darker(left, ImageChops.offset(right, -s, 0)))
        if n > score:
            best, score = s, n
    return best, score


def patch_rect(picture_blue_box, shrink=16):
    x0, y0 = picture_blue_box[0], picture_blue_box[1]
    return (x0 + PATCH[0] + shrink, y0 + PATCH[1] + shrink, PATCH[2] - 2 * shrink, PATCH[3] - 2 * shrink)


def patch_parallax(im, left, right, box):
    """The shift of the noise patch from the left eye to the right eye, by exact pixel matches."""
    x, y, w, h = patch_rect(box, 24)
    a = im.crop((left[0] + x, left[1] + y, left[0] + x + w, left[1] + y + h))
    best, score = None, -1
    for s in range(-20, 21):
        b = im.crop((right[0] + x + s, right[1] + y, right[0] + x + s + w, right[1] + y + h))
        same = ImageChops.difference(a, b).convert("L").histogram()[0]
        if same > score:
            best, score = s, same
    return best, score / (w * h)


def decoder(meta, eye_width):
    if not meta or len(meta) < 10 or meta[0] != 0 or meta[1] != 8:
        return None
    zero, scale, wref = meta[2] << 8 | meta[3], meta[4] << 8 | meta[5], meta[8] << 8 | meta[9]
    return lambda sample: (sample - zero) / scale * eye_width / wref


def samples(im, rect):
    x, y, w, h = rect
    return list(im.crop((x, y, x + w, y + h)).split()[0].tobytes())


def median(values):
    s = sorted(values)
    return s[len(s) // 2] if s else None


def eroded_bbox_region(m, offset, erode=4):
    box = m.getbbox()
    if not box:
        return None
    return (offset[0] + box[0] + erode, offset[1] + box[1] + erode, box[2] - box[0] - 2 * erode, box[3] - box[1] - 2 * erode)


def region_values(depth_img, region_mask, origin):
    """Depth samples where region_mask (in picture coordinates) is set."""
    m = region_mask
    data = list(depth_img.split()[0].tobytes())
    w = depth_img.width
    ret = []
    md = list(m.tobytes())
    for i, v in enumerate(md):
        if v:
            ret.append(data[i])
    return ret


def erode(m, n=3):
    from PIL import ImageFilter
    return m.filter(ImageFilter.MinFilter(2 * n + 1))


d = sys.argv[1]
listing = ""
for name in ("kscreen-depth-a.txt",):
    p = os.path.join(d, name)
    listing = open(p).read() if os.path.exists(p) else ""
for label in ("(3D-line-alt)", "(3D-L+depth)", "(3D-L+depth+gfx)"):
    check("listing " + label, label in listing, "listed by kscreen-doctor" if label in listing else "not listed")

# side by side (full): each window's parallax between the eyes
measured = {}
im, nf = frame(d, "a-sbsfull"), info(d, "a-sbsfull")
if im is None or nf is None:
    check("sbs-full", False, "no frame")
else:
    w, h = im.size
    eye = w // 2
    lb, rb = mask(im, (0, 0, eye, h), BLUE), mask(im, (eye, 0, eye, h), BLUE)
    lo, ro = mask(im, (0, 0, eye, h), ORANGE), mask(im, (eye, 0, eye, h), ORANGE)
    blue_box = lb.getbbox()
    measured["blue"] = shift_between(lb, rb)[0]
    measured["orange"] = shift_between(lo, ro)[0] if count(lo) else None
    if blue_box:
        measured["patch"] = patch_parallax(im, (0, 0), (eye, 0), blue_box)
    check("sbs-full eyes", blue_box is not None and measured["blue"] == 0 and measured.get("orange") is not None and measured["orange"] > 0
          and measured.get("patch", (None, 0))[0] == 8 + measured["blue"],
          "window %s px, orange window %s px, patch %s px (%.0f%% of its pixels exact)"
          % (measured["blue"], measured.get("orange"), measured.get("patch", (None,))[0], 100 * measured.get("patch", (0, 0))[1]))
    check("sbs-full timing property", nf["timing"] == 0, "side by side full timing = %s (0 = whole line doubled)" % nf["timing"])


def depth_frame(tag):
    im, nf = frame(d, tag), info(d, tag)
    if im is None or nf is None or "mode" not in nf:
        return None
    hd, vd, ht, vt = nf["mode"]
    return im, nf, hd, vd, ht, vt


def content_check(tag, want, tolerance=1.0):
    """Whether the patch's depth, inside it, decodes to want pixels; returns (ok, detail)."""
    got = depth_frame(tag)
    if not got:
        return False, "no frame"
    im, nf, hd, vd, ht, vt = got
    picture = im.crop((0, 0, hd, vd))
    depth = im.crop((0, vt, hd, vt + vd))
    box = mask(picture, (0, 0, hd, vd), BLUE).getbbox()
    dec = decoder(nf["metadata"], hd)
    if not box or not dec:
        return False, "window %s, metadata %s" % (box, nf["metadata"])
    values = [dec(v) for v in samples(depth, patch_rect(box))]
    med = median(values)
    near = sum(abs(v - want) <= tolerance + 0.5 for v in values) / len(values)
    return abs(med - want) <= tolerance and near >= 0.9, "patch %.2f px (median), %.0f%% within %.1f px of %s" % (med, 100 * near, tolerance + 0.5, want)


got = depth_frame("a-ldepth")
if not got:
    check("l-depth", False, "no frame")
else:
    im, nf, hd, vd, ht, vt = got
    check("l-depth frame", im.size == (hd, vt + vd), "%dx%d for %dx%d, vtotal %d (Figure H-5: vtotal + vdisplay)" % (im.size + (hd, vd, vt)))
    gap = mask(im, (0, vd, hd, vt - vd), (0, 0, 0))
    check("l-depth gap", count(gap) == hd * (vt - vd), "%d of %d pixels black between the pictures" % (count(gap), hd * (vt - vd)))
    meta = nf["metadata"]
    check("l-depth metadata", bool(meta) and meta[:4] == [0, 8, 0, 128],
          "3D_Metadata_type, length and parallax_zero: %s; parallax_scale %s, dref %s, wref %s"
          % (meta[:4] if meta else None, meta and meta[4] << 8 | meta[5], meta and meta[6] << 8 | meta[7], meta and meta[8] << 8 | meta[9]))
    dec = decoder(meta, hd)
    picture = im.crop((0, 0, hd, vd))
    depth = im.crop((0, vt, hd, vt + vd))
    if dec and "blue" in measured:
        ok, detail = content_check("a-ldepth", measured["patch"][0])
        check("l-depth patch (estimated)", ok, detail + "; measured between the eyes: %s px" % measured["patch"][0])
        omask = erode(mask(picture, (0, 0, hd, vd), ORANGE))
        ovals = [dec(v) for v in region_values(depth, omask, (0, 0))]
        if ovals and measured.get("orange") is not None:
            off = max(abs(v - measured["orange"]) for v in ovals)
            check("l-depth orange window", off <= 0.6, "%d samples, all within %.2f px of %s px measured between the eyes" % (len(ovals), off, measured["orange"]))
        else:
            check("l-depth orange window", False, "orange window not found")
        bmask = erode(mask(picture, (0, 0, hd, vd), BLUE))
        bvals = [dec(v) for v in region_values(depth, bmask, (0, 0))]
        near = sum(abs(v - measured["blue"]) <= 1.0 for v in bvals) / max(len(bvals), 1)
        check("l-depth window around the patch", near >= 0.95, "%.0f%% of its plain part within 1 px of %s px" % (100 * near, measured["blue"]))
        black = erode(mask(picture, (0, 0, hd, vd), (0, 0, 0)), 8)
        kvals = region_values(depth, black, (0, 0))
        zero = sum(v == 128 for v in kvals)
        check("l-depth background", kvals and zero == len(kvals), "%d of %d samples at the screen (128)" % (zero, len(kvals)))

ok, detail = content_check("a-ldepth-desktop", measured.get("blue", 0), 0.6)
check("desktop source", ok, detail + " (the window's level, the content's depth not estimated)")

got = depth_frame("a-ldepth-flat")
if got:
    im, nf, hd, vd, ht, vt = got
    vals = samples(im.crop((0, vt, hd, vt + vd)), (0, 0, hd, vd))
    flat = sum(v == 128 for v in vals)
    check("flat source", flat == len(vals), "%d of %d depth samples at the screen" % (flat, len(vals)))
    ok, detail = content_check("a-ldepth-flat", measured.get("patch", (8,))[0])
    check("control: depth ignored", not ok, "the patch check %s: %s" % ("fails as it must" if not ok else "PASSES, which it must not", detail))
else:
    check("flat source", False, "no frame")

nf = info(d, "a-ldepth-250")
meta = nf and nf["metadata"]
check("viewing distance", bool(meta) and (meta[6] << 8 | meta[7]) == 250, "dref %s cm" % (meta and meta[6] << 8 | meta[7]))

ok, detail = content_check("a-ldepth-swapped", -8)
check("swapped views", ok, detail)
ok, detail = content_check("a-ldepth-swapped", 8)
check("control: eyes swapped", not ok, "the +8 check %s: %s" % ("fails as it must" if not ok else "PASSES, which it must not", detail))

im = frame(d, "a-linealt")
nf = info(d, "a-linealt")
if im is None or nf is None:
    check("line-alt", False, "no frame")
else:
    hd, vd, ht, vt = nf["mode"]
    w, h = im.size
    red, green = mask(im, (0, 0, w, h), RED), mask(im, (0, 0, w, h), GREEN)
    rows_red = {y for y in range(h) if red.crop((0, y, w, y + 1)).getbbox()}
    rows_green = {y for y in range(h) if green.crop((0, y, w, y + 1)).getbbox()}
    paired = all((y + 1) in rows_green and red.crop((0, y, w, y + 1)).getbbox()[0::2] == green.crop((0, y + 1, w, y + 2)).getbbox()[0::2] for y in rows_red)
    check("line-alt", (w, h) == (hd, 2 * vd) and rows_red and all(y % 2 == 0 for y in rows_red) and all(y % 2 == 1 for y in rows_green) and paired,
          "%dx%d; the left view on %d even lines, the right view on %d odd lines, each pair at the same place: %s"
          % (w, h, len(rows_red), len(rows_green), paired))

im, nf = frame(d, "a-sbsfull-kept"), info(d, "a-sbsfull-kept")
if im is None or nf is None:
    check("sbs-kept", False, "no frame")
else:
    w, h = im.size
    eye = w // 2
    lb, rb = mask(im, (0, 0, eye, h), BLUE), mask(im, (eye, 0, eye, h), BLUE)
    box = lb.getbbox()
    pp = patch_parallax(im, (0, 0), (eye, 0), box) if box else (None, 0)
    check("sbs-kept", nf["timing"] == 1 and box is not None and shift_between(lb, rb)[0] == 0 and pp[0] == 8,
          "side by side full timing = %s (1 = blanking kept); the window at the same place, the patch %s px" % (nf["timing"], pp[0]))

popup = None
im, nf = frame(d, "a-fp720"), info(d, "a-fp720")
if im is not None and nf is not None:
    hd, vd, ht, vt = nf["mode"]
    ly, ry = mask(im, (0, 0, hd, vd), YELLOW), mask(im, (0, vt, hd, vd), YELLOW)
    if count(ly):
        popup = shift_between(ly, ry)[0]
    check("fp 720p popup", popup is not None, "the popup %s px between the eyes" % popup)
got = depth_frame("a-ldgg")
if not got:
    check("l-depth-gfx", False, "no frame")
else:
    im, nf, hd, vd, ht, vt = got
    check("l-depth-gfx frame", im.size == (hd, 3 * vt + vd), "%dx%d for %dx%d, vtotal %d (Figure H-6: 3 vtotal + vdisplay)" % (im.size + (hd, vd, vt)))
    picture, depth = im.crop((0, 0, hd, vd)), im.crop((0, vt, hd, vt + vd))
    graphics, gdepth = im.crop((0, 2 * vt, hd, 2 * vt + vd)), im.crop((0, 3 * vt, hd, 3 * vt + vd))
    py, gy = mask(picture, (0, 0, hd, vd), YELLOW), mask(graphics, (0, 0, hd, vd), YELLOW)
    check("l-depth-gfx popup in the graphics only", count(py) == 0 and count(gy) > 0 and count(mask(graphics, (0, 0, hd, vd), BLUE)) == 0,
          "%d popup pixels in the picture, %d in the graphics, %d window pixels in the graphics" % (count(py), count(gy), count(mask(graphics, (0, 0, hd, vd), BLUE))))
    dec = decoder(nf["metadata"], hd)
    if dec and popup is not None:
        gvals = [dec(v) for v in region_values(gdepth, erode(gy), (0, 0))]
        off = max(abs(v - popup) for v in gvals) if gvals else None
        check("l-depth-gfx popup depth", gvals and off <= 0.6, "%d samples within %s px of the popup's %s px" % (len(gvals), off, popup))
        dvals = [dec(v) for v in region_values(depth, erode(gy), (0, 0))]
        popped = sum(abs(v - popup) <= 0.6 for v in dvals) / max(len(dvals), 1)
        check("l-depth-gfx picture depth without the popup", popup == 0 or popped < 0.05, "%.0f%% of the picture's depth under the popup at its parallax" % (100 * popped))
        box = mask(picture, (0, 0, hd, vd), BLUE).getbbox()
        vals = [dec(v) for v in samples(depth, patch_rect(box))] if box else []
        med = median(vals)
        check("l-depth-gfx patch", med is not None and abs(med - 8) <= 1, "patch %s px (median)" % med)
    else:
        check("l-depth-gfx popup depth", False, "metadata %s, popup %s" % (nf["metadata"], popup))

got, two = depth_frame("b-ldepth-flat"), frame(d, "b-2d")
if not got or two is None:
    check("2d", False, "no frame")
else:
    im, nf, hd, vd, ht, vt = got
    diff = ImageChops.difference(im.crop((0, 0, hd, vd)), two.crop((0, 0, hd, vd))).convert("L")
    differ = hd * vd - diff.histogram()[0]
    check("2d picture unchanged", two.size == (hd, vd) and differ == 0, "the picture of L + depth and the 2D frame differ in %d pixels" % differ)

print("STEREO|summary|kwin-depth|%d failed" % fails)
sys.exit(1 if fails else 0)
