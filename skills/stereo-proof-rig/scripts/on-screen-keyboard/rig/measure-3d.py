#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""measure-3d.py CASE: the on-screen keyboard over a stereo window on a 3D output (step6-3d.sh), measured from KWin's
window list and the captures of both eyes (ScreenShot2 on a 3D output: left eye, right eye, side by side).

Prints JSON:
- keyboard: KWin's frame, and in that frame the right eye moved by every shift from -12 to +12 pixels against the left
  eye; the shift that leaves the fewest differing pixels (any channel more than 8 apart) is the keyboard's disparity,
  and the pixels still differing there say whether both eyes show the same keys (0 when they do);
- keyboard_drawn: how much of the keyboard's frame changed from the capture before it opened (a keyboard is there);
- behind: the stereo window's pixels outside the keyboard and Kate, after against before, per eye (0 when the window
  behind is as it was);
- pair: the stereo window above the keyboard: mean colour of each eye there (the left view red, the right view blue).
"""
import json, os, sys
import numpy as np
from PIL import Image

case = sys.argv[1]
def windows(name):
    return json.load(open(os.path.join(case, name)))["windows"] or []
def first(ws, pred):
    return next((w for w in ws if pred(w) and not w.get("deleted") and not w.get("hidden")), None)
before = np.asarray(Image.open(os.path.join(case, "before.png")).convert("RGB")).astype(int)
after = np.asarray(Image.open(os.path.join(case, "after2.png")).convert("RGB")).astype(int)
H, W2, _ = after.shape
E = W2 // 2
ws = windows("windows-after.json")
kb = first(ws, lambda w: w.get("inputMethod") or "plasma.keyboard" in (w.get("cls") or "") or "plasma-keyboard" in (w.get("cls") or ""))
gw = first(ws, lambda w: w.get("cls") == "org.kde.gwenview")
kt = first(ws, lambda w: w.get("cls") == "org.kde.kate")
out = {"capture": [W2, H], "eye_width": E, "keyboard_window": kb, "gwenview": gw and gw["fg"], "kate": kt and kt["fg"]}
if kb is None:
    out["keyboard"] = None
    print(json.dumps(out)); sys.exit(0)
x, y, w, h = [int(round(v)) for v in kb["fg"]]
m = 12
L = after[y + m:y + h - m, x + m:x + w - m]
best = None
for s in range(-12, 13):
    xs0, xs1 = x + m + s, x + w - m + s
    if xs0 < 0 or xs1 > E:
        continue
    R = after[y + m:y + h - m, E + xs0:E + xs1]
    diff = int((np.abs(L - R).max(axis=2) > 8).sum())
    if best is None or diff < best[1]:
        best = (s, diff)
    if s == 0:
        at_zero = diff
out["keyboard"] = {"frame": [x, y, w, h], "disparity_px": best[0], "differing_at_disparity": best[1], "differing_at_zero": at_zero,
                   "pixels": int(L.shape[0] * L.shape[1])}
changed = (np.abs(after[y:y + h, x:x + w] - before[y:y + h, x:x + w]).max(axis=2) > 8).mean()
out["keyboard_drawn"] = round(float(changed), 4)
if gw:
    mask = np.zeros((H, E), bool)
    gx, gy, gww, ghh = [int(round(v)) for v in gw["fg"]]
    mask[max(gy, 0):gy + ghh, max(gx, 0):gx + gww] = True
    mask[y:y + h, x:x + w] = False
    if kt:
        kx, ky, kw_, kh = [int(round(v)) for v in kt["fg"]]
        mask[max(ky - 2, 0):ky + kh + 2, max(kx - 2, 0):kx + kw_ + 2] = False
    res = {}
    for eye, off in (("left", 0), ("right", E)):
        d = np.abs(after[:, off:off + E] - before[:, off:off + E]).max(axis=2) > 8
        res[eye] = {"differing": int((d & mask).sum()), "compared": int(mask.sum())}
    out["behind"] = res
    # the stereo picture: where the left eye is red before the keyboard opens; probed between Kate and the keyboard
    red = (before[:, :E, 0] > 150) & (before[:, :E, 1] < 100) & (before[:, :E, 2] < 100)
    ys, xs = np.nonzero(red)
    if len(xs):
        top = max(int(ys.min()), (int(kt["fg"][1] + kt["fg"][3]) + 10) if kt else 0)
        rows, cols = slice(top, min(int(ys.max()), y - 10)), slice(int(xs.min()) + 5, int(xs.max()) - 5)
        out["pair"] = {"probe": [cols.start, rows.start, cols.stop - cols.start, rows.stop - rows.start],
                       "left_mean_rgb": [round(float(v), 1) for v in after[rows, cols].reshape(-1, 3).mean(axis=0)],
                       "right_mean_rgb": [round(float(v), 1) for v in after[rows, E + cols.start:E + cols.stop].reshape(-1, 3).mean(axis=0)]}
print(json.dumps(out))
