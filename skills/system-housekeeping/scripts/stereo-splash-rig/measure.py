#!/usr/bin/python3 -I
# measure.py: the checks of ORDER 715 on the frames the rig saves (RGB arrays, never RGBA bounding boxes; every shift in pixels).
#   measure.py eyes LEFT.ppm RIGHT.ppm LABEL        two eyes as two full pictures (the "left" and "right" outputs, or the
#                                                   two halves of a frame-packing frame cut by `cut-fp`): the shift of the
#                                                   wordmark and of the swirl (right minus left, in pixels, crossed < 0),
#                                                   the background's largest difference at shift 0, the wordmark count
#   measure.py anaglyph FRAME.ppm LABEL             an anaglyph frame: the red channel is the left eye, green and blue the
#                                                   right: the same shifts between the channels
#   measure.py fp FRAME.ppm LABEL [EYE_H [GAP]]     a frame-packing frame (1920x2205): the eyes are rows 0..1079 and 1125..2204
#   measure.py one REF.ppm FRAME.ppm LABEL          is FRAME one picture like REF (a one-eye or 2D reference)? the share of
#                                                   pixels that differ by more than 48, and the wordmark count
#   measure.py cmp A.ppm B.ppm LABEL                the largest and mean difference, and the pixels that differ by more than 8
# The electrons move between captures, so the shifts are measured on the static parts: the wordmark (bottom fifth) and
# the swirl's picture with its orbit lines (a clipped sum of differences, the electrons being a few small points).
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import grey_opening


def load(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(np.int16)


def foreground(img):
    """the thin bright structures of a region (the wordmark's strokes, the swirl and its orbit lines): the luminance minus its
    horizontal grey opening, so the smooth background, which is the same in both eyes, does not pull the match to shift 0"""
    lum = img.mean(axis=2)
    return lum - grey_opening(lum, size=(1, 31))


def best_shift(a, b, rng=24):
    """s such that b[:, x + s] matches a[:, x] best (the feature of b is s pixels to the right of a's): the mean absolute
    difference of the foregrounds where either of them holds a structure (over 25 levels), so the background's grain, which is
    the same in both eyes, does not weigh against the shift"""
    fa, fb = foreground(a), foreground(b)
    h, w = fa.shape
    best = None
    for s in range(-rng, rng + 1):
        xa = fa[:, max(0, -s):w - max(0, s)]
        xb = fb[:, max(0, s):w - max(0, -s)]
        on = np.maximum(xa, xb) > 25
        d = np.abs(xa - xb)[on].mean() if on.any() else 1e9
        if best is None or d < best[0]:
            best = (d, s)
    return best[1], best[0]


def regions(h, w):
    # the wordmark: bottom fifth, middle; the swirl: the upper two thirds, the middle two thirds of the width
    return {
        'wordmark': (slice(int(h * 0.78), int(h * 0.93)), slice(int(w * 0.12), int(w * 0.88))),
        'swirl': (slice(int(h * 0.05), int(h * 0.62)), slice(int(w * 0.2), int(w * 0.8))),
    }


def wordmarks(img):
    h, w = img.shape[:2]
    band = img[int(h * 0.75):int(h * 0.93)]
    white = ((band.max(axis=2) > 100).sum(axis=0) > 2).astype(int)
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
    return [r for r in runs if r[1] - r[0] > 60]


def eyes(left, right, label):
    h, w = left.shape[:2]
    out = []
    for name, (ys, xs) in regions(h, w).items():
        s, d = best_shift(left[ys, xs], right[ys, xs])
        out.append('%s %+d px (residual %.2f)' % (name, s, d))
    # the background: a strip along the left edge, below the swirl's reach, where only the background lies
    bg = (slice(int(h * 0.3), int(h * 0.7)), slice(0, int(w * 0.12)))
    bgd = np.abs(left[bg] - right[bg]).max()
    print('%s: %dx%d; right minus left: %s; background strip at shift 0: largest difference %d; wordmarks along the bottom: left %d, right %d'
          % (label, w, h, ', '.join(out), bgd, len(wordmarks(left)), len(wordmarks(right))))
    return {'w': w, 'h': h}


def main():
    mode = sys.argv[1]
    if mode == 'eyes':
        eyes(load(sys.argv[2]), load(sys.argv[3]), sys.argv[4])
    elif mode == 'anaglyph':
        img = load(sys.argv[2])
        left = np.repeat(img[:, :, 0:1], 3, axis=2)
        right = np.repeat(((img[:, :, 1] + img[:, :, 2]) // 2)[:, :, None], 3, axis=2)
        eyes(left, right, sys.argv[3] + ' (red against cyan)')
    elif mode == 'fp':
        img = load(sys.argv[2])
        eh = int(sys.argv[4]) if len(sys.argv) > 4 else 1080
        gap = int(sys.argv[5]) if len(sys.argv) > 5 else 45
        h, w = img.shape[:2]
        if h != 2 * eh + gap:
            print('%s: frame is %dx%d, not a frame-packing frame of two %d rows and a gap of %d' % (sys.argv[3], w, h, eh, gap))
            sys.exit(1)
        eyes(img[:eh], img[eh + gap:], sys.argv[3] + ' (frame packing: top against bottom)')
    elif mode == 'one':
        ref, img, label = load(sys.argv[2]), load(sys.argv[3]), sys.argv[4]
        if ref.shape != img.shape:
            print('%s: %dx%d against reference %dx%d: DIFFERENT SIZE' % (label, img.shape[1], img.shape[0], ref.shape[1], ref.shape[0]))
            sys.exit(1)
        diff = (np.abs(ref - img).max(axis=2) > 48).mean()
        print('%s: %.2f %% of pixels differ by more than 48; wordmarks along the bottom: %d' % (label, diff * 100, len(wordmarks(img))))
        sys.exit(0 if diff <= 0.02 else 1)
    elif mode == 'cmp':
        a, b, label = load(sys.argv[2]), load(sys.argv[3]), sys.argv[4]
        if a.shape != b.shape:
            print('%s: size %dx%d against %dx%d' % (label, a.shape[1], a.shape[0], b.shape[1], b.shape[0]))
            sys.exit(1)
        d = np.abs(a - b).max(axis=2)
        print('%s: largest difference %d, mean %.4f, pixels over 8: %d of %d' % (label, int(d.max()), d.mean(), int((d > 8).sum()), d.size))
    else:
        sys.exit('unknown mode')


main()
