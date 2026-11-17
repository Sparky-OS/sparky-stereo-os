#!/usr/bin/python3 -I
# check-eye.py EYE.ppm FRAME.ppm LABEL: is FRAME one eye, EYE, centred, and only background beside it? EYE is the main
# screen's left eye as the splash lays it out (the main screen alone, or the left eye of its frame-packing frame:
# rows 0 to 1079 of a 1920x2205 frame). FRAME is a screen that is not converted: larger than EYE, it must hold EYE at its
# middle and plain background around it (each row of the border one colour, the gradient); smaller, it must equal the
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
        # the border: every row one colour (the background gradient runs from top to bottom)
        rows = [img[r][mask[r]] for r in range(h) if mask[r].any()]
        spread = max(int((r.max(axis=0) - r.min(axis=0)).max()) for r in rows)
        notes.append('border rows vary by at most %d' % spread)
        ok &= spread <= 3
else:
    x0, y0 = (ew - w) // 2, (eh - h) // 2
    part = eye[y0:y0 + h, x0:x0 + w]
    d = (np.abs(img - part).max(axis=2) > 48).mean()
    notes.append('the eye\'s middle %dx%d: %.2f %% differ' % (w, h, d * 100))
    ok &= d <= 0.02
print('%s: %s, %s' % (label, 'ONE EYE' if ok else 'NOT ONE EYE', '; '.join(notes)))
sys.exit(0 if ok else 1)
