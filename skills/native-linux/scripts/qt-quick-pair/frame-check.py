#!/usr/bin/python3
"""Check Qt's own frame around a window drawn as a pair. The capture holds both eyes side by side, the
left eye first; the window's content is the neutral grey (128, 128, 128) of qdiscs. Prints the content rectangle
(the grey's bounding box in the left eye), the pixels that differ between the eyes inside it and outside it (the
frame and the desktop must be the same in both eyes), and with a reference capture (the same window drawn by the
installed libraries) the pixels of each eye that differ from it outside the content rectangle (the frame unchanged).
usage: frame-check.py CAPTURE.png [REFERENCE.png]"""
import json, sys
import numpy as np
from PIL import Image


def eyes(path):
    px = np.asarray(Image.open(path).convert('RGB')).astype(int)
    w = px.shape[1] // 2
    return px[:, :w], px[:, w:]


left, right = eyes(sys.argv[1])
grey = (np.abs(left - 128).max(axis=2) <= 1)
# the content is a solid grey block with the discs in it: rows and columns that are grey for most of its length
# (the frame has grey pixels too, but no long runs of them)
cols = np.nonzero(grey.sum(axis=0) >= 0.5 * grey.sum(axis=0).max())[0]
rows = np.nonzero(grey.sum(axis=1) >= 0.5 * grey.sum(axis=1).max())[0]
y0, y1, x0, x1 = int(rows.min()), int(rows.max()) + 1, int(cols.min()), int(cols.max()) + 1
inside = np.zeros(grey.shape, bool)
inside[y0:y1, x0:x1] = True
differ = np.abs(left - right).max(axis=2) > 0
out = {'content': [x0, y0, x1 - x0, y1 - y0],
       'eyes_differ_inside': int((differ & inside).sum()),
       'eyes_differ_outside': int((differ & ~inside).sum())}
if len(sys.argv) > 2:
    rl, rr = eyes(sys.argv[2])
    out['left_vs_reference_outside'] = int(((np.abs(left - rl).max(axis=2) > 0) & ~inside).sum())
    out['right_vs_reference_outside'] = int(((np.abs(right - rr).max(axis=2) > 0) & ~inside).sum())
print(json.dumps(out))
