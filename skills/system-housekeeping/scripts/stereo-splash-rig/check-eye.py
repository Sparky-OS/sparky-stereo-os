#!/usr/bin/python3 -I
# check-eye.py EYE.ppm FRAME.ppm LABEL: is FRAME one eye, EYE, centred, and only background beside it? EYE is the main
# screen's left eye as the splash lays it out (the main screen alone, or the left eye of its frame-packing frame:
# rows 0 to 1079 of a 1920x2205 frame). FRAME is a screen that is not converted: larger than EYE, it must hold EYE at its
# middle and, around it, the eye's own edge continued (each border pixel equal to the nearest pixel of the eye in the
# same capture: no frame of another colour); smaller, it must equal the
# middle of EYE. The electrons move between frames: at most 2 % of the compared pixels may differ by more than 48.
import sys
import numpy as np
from PIL import Image

eye = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.int16)
img = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(np.int16)
label = sys.argv[3]
if eye.shape[0] == 2205:
    eye = eye[:1080]
eh, ew = eye.shape[:2]
h, w = img.shape[:2]
ok = True
notes = []
if w >= ew and h >= eh:
    x0, y0 = (w - ew) // 2, (h - eh) // 2
    inner = img[y0:y0 + eh, x0:x0 + ew]
    d = (np.abs(inner - eye).max(axis=2) > 48).mean()
    notes.append('middle %dx%d against the eye: %.2f %% differ' % (ew, eh, d * 100))
    ok &= d <= 0.02
    mask = np.ones((h, w), bool)
    mask[y0:y0 + eh, x0:x0 + ew] = False
    if mask.any():
        # the border must continue the eye's own edge: each border pixel equal to the nearest pixel of the eye as it
        # is in this capture (no frame of another colour, nothing of the other eye)
        ys = np.clip(np.arange(h), y0, y0 + eh - 1)
        xs = np.clip(np.arange(w), x0, x0 + ew - 1)
        edge = img[ys][:, xs]
        d = np.abs(img - edge).max(axis=2)[mask]
        notes.append('border against the eye\'s edge continued: largest difference %d, %.2f %% of border pixels off by more than 3'
                     % (int(d.max()), (d > 3).mean() * 100))
        ok &= int(d.max()) <= 3
else:
    x0, y0 = (ew - w) // 2, (eh - h) // 2
    part = eye[y0:y0 + h, x0:x0 + w]
    d = (np.abs(img - part).max(axis=2) > 48).mean()
    notes.append('the eye\'s middle %dx%d: %.2f %% differ' % (w, h, d * 100))
    ok &= d <= 0.02
print('%s: %s, %s' % (label, 'ONE EYE' if ok else 'NOT ONE EYE', '; '.join(notes)))
sys.exit(0 if ok else 1)
