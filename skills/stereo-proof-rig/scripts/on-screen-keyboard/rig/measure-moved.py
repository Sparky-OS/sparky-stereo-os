#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""measure-moved.py CASE: a declared stereo window with a text field, before and after the on-screen keyboard opened for
its field (step3-3d-moved.sh), from KWin's window list and the captures of both eyes (ScreenShot2 on a 3D output: the
left eye's picture, then the right eye's, side by side).

Prints JSON:
- window_before, window_after: the window's frame; moved: whether KWin moved or resized it; keyboard: the keyboard's
  frame (KWin's input panel or the layer-shell keyboard); clear_of_keyboard: the window ends where the keys begin;
- picture_before, picture_after: the stereo picture inside the window, found in each eye by its colour (left view red,
  right view blue): its box in each eye, the mean colour of each eye there, and the disparity of its white stripes (the
  shift of the right eye's stripe profile against the left eye's that matches best; the picture was drawn 12 px apart
  before it was scaled into the window);
- pair_kept: after the move the picture is still a pair: red in the left eye, blue in the right, the same size as before,
  where the window now is, and the same disparity (within 1 px). Both captures are of the active window: the edition's
  depth rules draw an inactive window a step behind the screen, which shifts the pair by 2 px (found in calibration);
- window_active_before, window_active_after: KWin's active flag of the window at each capture.
"""
import json, os, sys
import numpy as np
from PIL import Image

case = sys.argv[1]
def windows(name):
    try:
        return json.load(open(os.path.join(case, name)))["windows"] or []
    except Exception:
        return []
def live(ws, pred):
    return next((w for w in ws if pred(w) and not w.get("deleted") and not w.get("hidden")), None)
is_win = lambda w: "Row71 stereo field" in (w.get("caption") or "")
is_kb = lambda w: w.get("inputMethod") or "plasma-keyboard" in (w.get("cls") or "") or "plasma.keyboard" in (w.get("cls") or "")

def picture(img, frame):
    """The stereo picture inside FRAME (the window's client area), per eye: its box is where the left view is red
    (a declared 3D area is drawn in the same rectangle in each eye); the mean colour of each eye there, and the
    disparity of its white stripes."""
    H, W2, _ = img.shape
    E = W2 // 2
    x, y, w, h = [int(round(v)) for v in frame]
    y0, y1, x0, x1 = max(y, 0), min(y + h, H), max(x, 0), min(x + w, E)
    a = img[y0:y1, x0:x1]
    red = (a[..., 0] > 150) & (a[..., 1] < 110) & (a[..., 2] < 110)
    ys, xs = np.nonzero(red)
    out = {}
    if len(xs) < 500:
        return {"left": None, "right": None}
    bx0, bx1, by0, by1 = int(xs.min()) + x0, int(xs.max()) + x0, int(ys.min()) + y0, int(ys.max()) + y0
    for eye, off in (("left", 0), ("right", E)):
        region = img[by0:by1 + 1, off + bx0:off + bx1 + 1].reshape(-1, 3)
        out[eye] = {"box": [bx0, by0, bx1 - bx0 + 1, by1 - by0 + 1], "mean_rgb": [round(float(v), 1) for v in region.mean(axis=0)]}
    # the stripes: columns white over most of a band in the middle of the picture, per eye; the right eye's profile is
    # shifted against the left eye's until they match best
    band = slice(by0 + (by1 - by0) // 3, by0 + 2 * (by1 - by0) // 3)
    prof = {}
    for eye, off in (("left", 0), ("right", E)):
        b = img[band, off + bx0 - 20:off + bx1 + 21]
        prof[eye] = ((b.min(axis=2) > 200).mean(axis=0) > 0.5).astype(int)
    L = prof["left"][20:-20]
    best = None
    for s_ in range(-20, 21):
        R = prof["right"][20 + s_:len(prof["right"]) - 20 + s_]
        if len(R) != len(L):
            continue
        d = int(np.abs(L - R).sum())
        if best is None or d < best[1]:
            best = (s_, d)
    out["disparity_px"] = best[0] if best else None
    out["mismatch_at_disparity"] = best[1] if best else None
    out["stripes_left"] = int(np.diff(np.concatenate([[0], L])).clip(0).sum())
    return out

before = np.asarray(Image.open(os.path.join(case, "before.png")).convert("RGB")).astype(int)
after = np.asarray(Image.open(os.path.join(case, "after2.png")).convert("RGB")).astype(int)
wb = live(windows("windows-before.json"), is_win)
wsa = windows("windows-after.json")
wa = live(wsa, is_win)
kb = live(wsa, is_kb)
res = {"capture": list(after.shape[1::-1]), "window_before": wb and wb["fg"], "window_after": wa and wa["fg"],
       "keyboard": kb and kb["fg"], "keyboard_kind": kb and ("input-panel" if kb.get("inputMethod") else "layer")}
try:
    res["qml_log"] = [l.strip() for l in open(os.path.join(case, "qml.log"), errors="replace") if "stereoActive" in l][:4]
except FileNotFoundError:
    res["qml_log"] = None
if wb and wa:
    res["moved"] = [round(v) for v in wb["fg"]] != [round(v) for v in wa["fg"]]
    res["window_active_before"], res["window_active_after"] = wb.get("active"), wa.get("active")
    if kb:
        res["clear_of_keyboard"] = wa["fg"][1] + wa["fg"][3] <= kb["fg"][1] + 1
    pb = picture(before, wb["cg"])
    # after: the part of the window above the keyboard (the keyboard may cover the window that was not moved)
    fa = list(wa["cg"])
    if kb and fa[1] + fa[3] > kb["fg"][1]:
        fa[3] = max(0, kb["fg"][1] - fa[1])
    pa = picture(after, fa)
    res["picture_before"], res["picture_after"] = pb, pa
    ok = all(pa.get(e) for e in ("left", "right")) and all(pb.get(e) for e in ("left", "right"))
    if ok:
        lb, la = pb["left"]["box"], pa["left"]["box"]
        same_size = abs(lb[2] - la[2]) <= 2 and abs(lb[3] - la[3]) <= 2
        followed = abs((la[1] - lb[1]) - (wa["fg"][1] - wb["fg"][1])) <= 2 and abs((la[0] - lb[0]) - (wa["fg"][0] - wb["fg"][0])) <= 2
        colours = all(p["left"]["mean_rgb"][0] > 120 and p["right"]["mean_rgb"][2] > 120 for p in (pb, pa))
        # the stripes are found in both captures (12 drawn per eye, a few cut by the box's edges) and shifted the same
        found = pb.get("stripes_left", 0) >= 8 and pa.get("stripes_left", 0) >= 8
        disp = found and pb.get("disparity_px") is not None and pa.get("disparity_px") is not None and abs(pb["disparity_px"] - pa["disparity_px"]) <= 1
        res["pair_checks"] = {"same_size": same_size, "followed_the_window": followed, "colours": colours, "same_disparity": disp}
        res["pair_kept"] = same_size and followed and colours and disp
    else:
        res["pair_kept"] = False
print(json.dumps(res))
