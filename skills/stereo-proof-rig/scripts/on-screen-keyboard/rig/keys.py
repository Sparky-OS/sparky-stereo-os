#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""keys.py LAYOUT_QML CAPTURE X,Y,W,H [--bar]: where each key of an on-screen keyboard is, as JSON.

The keys of each row come from the layout's own QML (Qt Virtual Keyboard: every KeyboardRow under the KeyboardLayout is a
row of the screen, a nested KeyboardRow adds its keys in place, a FillerKey draws nothing); their places come from the
capture of the keyboard's window (X,Y,W,H in the capture's pixels): the keyboard's background is the colour of its top rows,
a row of keys is a band where most pixels are not it, and the keys of a band are its runs of other colours along the
band's middle line, split at the background's gaps. With --bar the bar above the keys (Fcitx 5 mode) is the
first band when there is one band more than the layout has rows, else the strip above the first row of keys; its runs are
reported apart, each marked as a button when one colour other than the panel's fills most of its top line.
Rows whose count of runs differs from the layout's count are reported as mismatched and get no keys.
"""
import json, re, sys
import numpy as np
from PIL import Image

def layout_rows(path):
    s = open(path, encoding="utf-8").read()
    stack, rows = [], []
    for t in re.finditer(r'(\w+)\s*\{|\}|\btext:\s*("(?:[^"\\]|\\.)*")|\bdisplayText:\s*("(?:[^"\\]|\\.)*")', s):
        if t.group(1):
            stack.append([t.group(1), None, None])
            if t.group(1) == "KeyboardRow" and sum(1 for x in stack if x[0] == "KeyboardRow") == 1:
                rows.append([])
        elif t.group(2):
            if stack:
                stack[-1][1] = json.loads(t.group(2))
        elif t.group(3):
            if stack:
                stack[-1][2] = json.loads(t.group(3))
        else:
            if not stack:
                continue
            name, text, display = stack.pop()
            if name == "Key" and rows:
                rows[-1].append({"name": "Key", "text": text, "display": display})
            elif name.endswith("Key") and name != "FillerKey" and rows:
                rows[-1].append({"name": name, "text": None, "display": None})
    return rows

def find(qml, capture, box, bar=False):
    x0, y0, w, h = box
    img = np.asarray(Image.open(capture).convert("RGB")).astype(int)[y0:y0 + h, x0:x0 + w]
    # the panel's own colour: its top rows lie above every key
    top = img[:2].reshape(-1, 3)
    colours, counts = np.unique(top, axis=0, return_counts=True)
    bg = colours[counts.argmax()]
    other = np.abs(img - bg).sum(axis=2) > 12
    rowfrac = other.mean(axis=1)
    bands, inside, start = [], False, 0
    for y, f in enumerate(rowfrac):
        if f > 0.15 and not inside:
            inside, start = True, y
        elif f <= 0.15 and inside:
            inside = False
            if y - start >= 12:
                bands.append((start, y))
    if inside and h - start >= 12:
        bands.append((start, h))
    keycolour_counts = {}
    for b0, b1 in bands:
        top = img[b0 + (b1 - b0) // 5]
        for px in top[other[b0 + (b1 - b0) // 5]]:
            keycolour_counts[tuple(px)] = keycolour_counts.get(tuple(px), 0) + 1
    keycolour = np.array(max(keycolour_counts, key=keycolour_counts.get)) if keycolour_counts else bg

    def runs(b0, b1):
        line = other[(b0 + b1) // 2]
        rs, inrun, s0 = [], False, 0
        for x, v in enumerate(line):
            if v and not inrun:
                inrun, s0 = True, x
            elif not v and inrun:
                inrun = False
                rs.append((s0, x))
        if inrun:
            rs.append((s0, len(line)))
        # glyphs of a label can leave a background gap inside a key: join runs closer than 3 px
        joined = []
        for r in rs:
            if joined and r[0] - joined[-1][1] < 3:
                joined[-1] = (joined[-1][0], r[1])
            else:
                joined.append(r)
        return [r for r in joined if r[1] - r[0] >= 8]

    result = {"background": [int(v) for v in bg], "keycolour": [int(v) for v in keycolour], "bands": bands, "rows": [], "bar": None}
    key_bands = bands
    if bar and bands:
        # the bar is what lies above the keys: its own band when its buttons fill it, else the strip above the first row
        rows_wanted = len(layout_rows(qml))
        if len(bands) > rows_wanted:
            b0, b1 = bands[0]
            key_bands = bands[1:]
        else:
            b0, b1 = 2, max(bands[0][0] - 2, 3)
        items = []
        for r0, r1 in runs(b0, b1):
            # a button: one colour other than the panel's fills most of its top line (a normal or a pressed key colour);
            # the glyphs of a preedit do not
            seg = img[b0 + (b1 - b0) // 5, r0:r1]
            cols, cnt = np.unique(seg, axis=0, return_counts=True)
            main = cols[cnt.argmax()]
            fill = float(cnt.max() / len(seg)) if np.abs(main - bg).sum() > 12 else 0.0
            items.append({"x": x0 + (r0 + r1) // 2, "y": y0 + (b0 + b1) // 2, "w": r1 - r0, "button": fill > 0.5})
        result["bar"] = items
        result["bar_band"] = [y0 + b0, y0 + b1]
    rows = layout_rows(qml)
    for i, (b0, b1) in enumerate(key_bands):
        rs = runs(b0, b1)
        entry = {"band": [y0 + b0, y0 + b1], "runs": len(rs)}
        if i < len(rows) and len(rows[i]) == len(rs):
            entry["keys"] = [dict(k, x=x0 + (r0 + r1) // 2, y=y0 + (b0 + b1) // 2) for k, (r0, r1) in zip(rows[i], rs)]
        else:
            entry["mismatch"] = {"layout": len(rows[i]) if i < len(rows) else None, "found": len(rs)}
        result["rows"].append(entry)
    return result

if __name__ == "__main__":
    box = [int(v) for v in sys.argv[3].split(",")]
    print(json.dumps(find(sys.argv[1], sys.argv[2], box, "--bar" in sys.argv), ensure_ascii=False))
