#!/usr/bin/python3 -I
# compare.py REFERENCE.ppm FRAME.ppm [LABEL]: is FRAME the picture REFERENCE shows? REFERENCE is the frame the same screen
# shows, in the same layout, when it is the only screen connected (one display, so its eyes are laid out at its own
# size). The electrons move between frames, so a frame matches when at most 2 % of its pixels differ by more than 48 in
# a channel. Also printed: the shift of the frame's best match against the reference (the picture moved sideways), and
# for a picture whose left and right halves are both the splash, the count of wordmarks along the bottom (a raw pair
# shows two).
import sys
import numpy as np
from PIL import Image


def load(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(np.int16)


ref, img = load(sys.argv[1]), load(sys.argv[2])
label = sys.argv[3] if len(sys.argv) > 3 else sys.argv[2]
if ref.shape != img.shape:
    print('%s: size %dx%d, reference %dx%d: DIFFERENT SIZE' % (label, img.shape[1], img.shape[0], ref.shape[1], ref.shape[0]))
    sys.exit(1)
diff = (np.abs(ref - img).max(axis=2) > 48).mean()
best = (diff, 0)
h, w = ref.shape[:2]
# the shift search on a copy reduced 4 times (grey), refined to the pixel around the best
gr, gi = ref.mean(axis=2)[::4, ::4], img.mean(axis=2)[::4, ::4]
cw = gr.shape[1]
coarse = min(((np.abs(gr[:, max(0, s):cw + min(0, s)] - gi[:, max(0, -s):cw + min(0, -s)]) > 48).mean(), s)
             for s in range(-cw // 2, cw // 2))
for s in range(coarse[1] * 4 - 4, coarse[1] * 4 + 5):
    if s == 0:
        continue
    a = ref[:, max(0, s):w + min(0, s)]
    b = img[:, max(0, -s):w + min(0, -s)]
    d = (np.abs(a - b).max(axis=2) > 48).mean()
    if d < best[0]:
        best = (d, s)
# wordmarks: bright, nearly white columns in the bottom fifth of each picture of the frame (one eye's height)
eye_h = 1080 if h in (1080, 2205) else h
band = img[int(eye_h * 0.75):int(eye_h * 0.93)]
white = ((band.min(axis=2) > 200).sum(axis=0) > 3).astype(int)
runs, start, gap = [], None, 0
for x, v in enumerate(white):
    if v and start is None:
        start, gap = x, 0
    elif not v and start is not None:
        gap += 1
        if gap > 40:
            runs.append((start, x - gap))
            start = None
    elif v:
        gap = 0
if start is not None:
    runs.append((start, w - 1))
runs = [r for r in runs if r[1] - r[0] > 60]
verdict = 'MATCH' if diff <= 0.02 else 'DIFFERS'
print('%s: %s, %.1f %% of pixels differ; best shift %+d px (%.1f %%); wordmarks along the bottom: %d at x %s' % (
    label, verdict, diff * 100, best[1], best[0] * 100, len(runs), ', '.join('%d-%d' % r for r in runs)))
sys.exit(0 if verdict == 'MATCH' else 1)
