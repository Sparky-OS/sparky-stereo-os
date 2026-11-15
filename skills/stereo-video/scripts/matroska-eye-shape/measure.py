#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Measure the shapes in one eye of the ORDER 577 fixtures.

An eye holds a white circle (left part) and a white square (right part) on a red (left eye) or blue (right eye)
background. shapes(eye, sx) returns the circle's and the square's width over height, with the eye's columns counted
sx times wider (sx = the sample aspect ratio the reader applies, 1 for a picture already at display shape), and the
eye's colour. A round circle reads 1.0; a 32:9 strip of a 16:9 eye reads 2.0; a squeezed half reads 0.5.
"""
import numpy as np


def _extent(mask):
    cols = np.where(mask.any(axis=0))[0]
    rows = np.where(mask.any(axis=1))[0]
    if len(cols) == 0 or len(rows) == 0:
        return None
    return cols[0], cols[-1] + 1, rows[0], rows[-1] + 1


def _blob(mask):
    """The connected shape grown from the middle of the longest white run: a player's overlay (a play bar, a time) is
    not part of it."""
    if not mask.any():
        return mask
    runs = np.zeros(mask.shape[0], int)
    best = (0, 0, 0)
    for y in range(mask.shape[0]):
        row = mask[y]
        if not row.any():
            continue
        d = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
        starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
        k = int(np.argmax(ends - starts))
        if ends[k] - starts[k] > best[0]:
            best = (ends[k] - starts[k], y, (starts[k] + ends[k]) // 2)
    grown = np.zeros_like(mask)
    grown[best[1], best[2]] = True
    while True:
        nxt = grown.copy()
        nxt[1:] |= grown[:-1]; nxt[:-1] |= grown[1:]; nxt[:, 1:] |= grown[:, :-1]; nxt[:, :-1] |= grown[:, 1:]
        nxt &= mask
        if (nxt == grown).all():
            return grown
        grown = nxt


def shapes(eye, sx=1.0, sy=1.0):
    """eye: HxWx3 uint8 array. Returns dict(circle, square, colour, found)."""
    a = eye.astype(np.int32)
    white = (a[..., 0] > 170) & (a[..., 1] > 170) & (a[..., 2] > 170)
    h, w = white.shape
    split = int(round(0.58 * w))
    out = {"circle": None, "square": None}
    for name, part, x0 in (("circle", _blob(white[:, :split]), 0), ("square", _blob(white[:, split:]), split)):
        e = _extent(part)
        if e:
            cw = (e[1] - e[0]) * sx
            ch = (e[3] - e[2]) * sy
            out[name] = round(cw / ch, 4) if ch else None
    bg = ~white
    if bg.any():
        r, g, b = (a[..., c][bg].mean() for c in range(3))
        out["colour"] = "red" if r > 2 * b and r > 30 else "blue" if b > 2 * r and b > 30 else "green" if g > 30 else "dark"
    else:
        out["colour"] = "none"
    return out


def eyes_from_frame(frame, packing, order):
    """Split a decoded frame (HxWx3, the coded samples) into (left, right) eyes at their coded size."""
    h, w = frame.shape[:2]
    if packing == "sbs":
        a, b = frame[:, : w // 2], frame[:, w // 2 :]
    elif packing == "tab":
        a, b = frame[: h // 2], frame[h // 2 :]
    elif packing == "cols":
        a, b = frame[:, 0::2], frame[:, 1::2]
    elif packing == "rows":
        a, b = frame[0::2], frame[1::2]
    elif packing == "checker":
        even = (np.add.outer(np.arange(h), np.arange(w)) % 2) == 0
        a = np.where(even[..., None], frame, 0).astype(np.uint8)
        b = np.where(~even[..., None], frame, 0).astype(np.uint8)
        # each eye's samples sit on alternate positions of the whole frame: fill the holes from the row's neighbour
        a = np.maximum(a, np.roll(a, 1, axis=1)); b = np.maximum(b, np.roll(b, 1, axis=1))
    else:
        return frame, frame
    return (a, b) if order != "rl" else (b, a)
