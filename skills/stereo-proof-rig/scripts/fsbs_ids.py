#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Eye, row and column identifiers in every sample, and the packings that place them.

Every sample of a source eye carries its own address in its 24 bits, so a picture made
from it tells for each sample which eye, column and row it came from:

    R = x & 0xff
    G = y & 0xff
    B = eye << 7 | (x >> 8 & 0xf) << 3 | (y >> 8 & 0x7)

(x below 4096, y below 2048).  Unpacking by copy keeps every address; any resampling
(a stretch, a squeeze, a filter) mixes neighbours and the addresses no longer decode
to the place they sit at.  The model is awesome-stereoscopy PR #44's verify_fieldseq.py.
"""
import numpy as np

MAX_X, MAX_Y = 4096, 2048


def eye_ids(eye, width, height):
    """The source eye: width x height samples, each its own address (H x W x 3, uint8)."""
    if width > MAX_X or height > MAX_Y:
        raise ValueError("eye too large for 24-bit addresses")
    x = np.arange(width, dtype=np.uint32)[None, :]
    y = np.arange(height, dtype=np.uint32)[:, None]
    r = (x & 0xff) + 0 * y
    g = (y & 0xff) + 0 * x
    b = (eye << 7) | ((x >> 8) & 0xf) << 3 | ((y >> 8) & 0x7)
    return np.stack([r, g, b + 0 * x], axis=-1).astype(np.uint8)


def decode(rgb):
    """Addresses of an H x W x 3 picture: (eye, x, y) arrays."""
    r = rgb[..., 0].astype(np.int32)
    g = rgb[..., 1].astype(np.int32)
    b = rgb[..., 2].astype(np.int32)
    eye = b >> 7
    x = ((b >> 3) & 0xf) << 8 | r
    y = (b & 0x7) << 8 | g
    return eye, x, y


# The packings of H.264 Table D-8 / H.265 Table D.8 (and HDMI 1.4b's 3D structures) as
# the frames that carry two eyes; each returns (frame, eye_width, eye_height): the eyes'
# own sample grids.  Full and half are the relation of the eye to the frame, not sizes.
def pack(packing, width, height, gap=0):
    """A packed frame of width x height (the frame as stored) and the size of its eyes."""
    if packing == "sbs_full":           # HDMI 3D structure 3, side by side (full)
        ew, eh = width // 2, height
    elif packing in ("sbs_half", "columns", "checkerboard", "sbs_quincunx"):
        ew, eh = width // 2, height     # Table D-8 types 3 (half), 1, 0, 3 with quincunx
    elif packing in ("tab_half", "rows"):
        ew, eh = width, height // 2     # Table D-8 types 4 (half), 2
    elif packing == "tab_full":
        ew, eh = width, height // 2
    elif packing == "frame_packing":    # HDMI 3D structure 0: two eyes and the active space
        ew, eh = width, (height - gap) // 2
    else:
        raise ValueError(packing)
    left, right = eye_ids(0, ew, eh), eye_ids(1, ew, eh)
    frame = np.zeros((height, width, 3), np.uint8)
    if packing in ("sbs_full", "sbs_half", "sbs_quincunx"):
        frame[:, :ew] = left
        frame[:, ew:2 * ew] = right
    elif packing in ("tab_half", "tab_full"):
        frame[:eh] = left
        frame[eh:2 * eh] = right
    elif packing == "frame_packing":
        frame[:eh] = left
        frame[eh + gap:2 * eh + gap] = right
    elif packing == "rows":             # even rows the first view
        frame[0::2] = left
        frame[1::2] = right
    elif packing == "columns":          # even columns the first view
        frame[:, 0::2] = left
        frame[:, 1::2] = right
    elif packing == "checkerboard":     # (x + y) even the first view
        for y in range(height):
            p = y % 2
            frame[y, p::2] = left[y]
            frame[y, 1 - p::2] = right[y]
    return frame, ew, eh


def check_full_sbs(buffer, eye_width, eye_height):
    """Whether buffer (H x W x 3) is full side by side, left eye first, each eye at its
    own resolution, every sample the source sample of its place.  Returns a report dict."""
    h, w = buffer.shape[:2]
    report = {"buffer": [w, h], "expected": [2 * eye_width, eye_height]}
    if (w, h) != (2 * eye_width, eye_height):
        report["pass"] = False
        report["why"] = "buffer is %dx%d, the eyes at their own resolution make %dx%d" % (w, h, 2 * eye_width, eye_height)
        return report
    bad = 0
    for e in (0, 1):
        part = buffer[:, e * eye_width:(e + 1) * eye_width]
        de, dx, dy = decode(part)
        xs = np.arange(eye_width)[None, :]
        ys = np.arange(eye_height)[:, None]
        wrong = (de != e) | (dx != xs) | (dy != ys)
        n = int(wrong.sum())
        report["eye%d_wrong_samples" % e] = n
        bad += n
    report["samples"] = 2 * eye_width * eye_height
    report["pass"] = bad == 0
    return report


def check_full_sbs_in_layer(buffer, eye_width, eye_height):
    """Like check_full_sbs(), for a layer that also holds the window's black around the views (a player's letterbox,
    counted in the views' own samples): each half must hold its eye at its own resolution, every sample copied, and
    nothing else but black."""
    h, w = buffer.shape[:2]
    report = {"buffer": [w, h], "eye": [eye_width, eye_height]}
    if w % 2 or w // 2 < eye_width or h < eye_height:
        report["pass"] = False
        report["why"] = "a half of %dx%d cannot hold an eye of %dx%d" % (w // 2, h, eye_width, eye_height)
        return report
    half = w // 2
    bad = 0
    for e in (0, 1):
        part = buffer[:, e * half:(e + 1) * half]
        de, dx, dy = decode(part)
        found = None
        ys, xs = np.nonzero((de == e) & (dx == 0) & (dy == 0))
        for oy, ox in zip(ys, xs):
            if ox + 1 < half and oy + 1 < h and (de[oy, ox + 1], dx[oy, ox + 1], dy[oy, ox + 1]) == (e, 1, 0) \
                    and (de[oy + 1, ox], dx[oy + 1, ox], dy[oy + 1, ox]) == (e, 0, 1):
                found = (int(ox), int(oy))
                break
        if found is None or found[0] + eye_width > half or found[1] + eye_height > h:
            report["pass"] = False
            report["why"] = "eye %d not found at its own resolution" % e
            return report
        ox, oy = found
        block = part[oy:oy + eye_height, ox:ox + eye_width]
        be, bx, by = decode(block)
        n = int(((be != e) | (bx != np.arange(eye_width)[None, :]) | (by != np.arange(eye_height)[:, None])).sum())
        rest = np.ones(part.shape[:2], bool)
        rest[oy:oy + eye_height, ox:ox + eye_width] = False
        report["eye%d_at" % e] = [ox, oy]
        report["eye%d_wrong_samples" % e] = n
        report["eye%d_non_black_outside" % e] = int((part[rest].max(-1) > 0).sum()) if rest.any() else 0
        bad += n + report["eye%d_non_black_outside" % e]
    report["pass"] = bad == 0
    return report


if __name__ == "__main__":
    import argparse, json, sys
    from PIL import Image
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make", help="write a packed frame as PNG")
    m.add_argument("packing")
    m.add_argument("width", type=int)
    m.add_argument("height", type=int)
    m.add_argument("out")
    m.add_argument("--gap", type=int, default=0)
    c = sub.add_parser("check", help="check a handed-over buffer (PNG, or raw XRGB8888 with --raw WxH:stride)")
    c.add_argument("buffer")
    c.add_argument("eye_width", type=int)
    c.add_argument("eye_height", type=int)
    c.add_argument("--raw", help="WxH:stride of a little-endian XRGB8888 dump")
    c.add_argument("--rgba-bottom-up", action="store_true", help="the dump is RGBA rows from the bottom up (an OpenGL read-back)")
    c.add_argument("--in-layer", action="store_true", help="the buffer may also hold black around each eye (a letterbox)")
    a = ap.parse_args()
    if a.cmd == "make":
        frame, ew, eh = pack(a.packing, a.width, a.height, a.gap)
        Image.fromarray(frame, "RGB").save(a.out)
        print(json.dumps({"packing": a.packing, "frame": [a.width, a.height], "eye": [ew, eh]}))
    else:
        if a.raw:
            size, stride = a.raw.split(":")
            w, h = map(int, size.split("x"))
            data = np.fromfile(a.buffer, np.uint8)[: int(stride) * h].reshape(h, int(stride))
            px = data[:, : 4 * w].reshape(h, w, 4)
            rgb = px[::-1, :, :3] if a.rgba_bottom_up else px[..., [2, 1, 0]]
        else:
            rgb = np.asarray(Image.open(a.buffer).convert("RGB"))
        r = (check_full_sbs_in_layer if a.in_layer else check_full_sbs)(rgb, a.eye_width, a.eye_height)
        print(json.dumps(r))
        sys.exit(0 if r["pass"] else 1)
