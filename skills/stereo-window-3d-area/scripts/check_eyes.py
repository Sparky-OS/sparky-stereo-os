#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""check_eyes.py CAPTURE.png [--size WxH] [--frame N] [--swap] [--expect stereo|left|mono] [--tol N] [--overlay]

Checks one ScreenShot2 capture of glarea-stereo-test.
 stereo: the capture holds both eyes side by side (width twice the output's): the left half has the red LEFT picture,
         the right half the blue RIGHT picture, each exactly the picture the program drew (every sample), at the area's own
         size and place in both halves, and everything outside the area is the same in both halves.
 left:   a 2D capture (one eye wide) with the red LEFT picture only (the area that could not be shown per eye).
 mono:   a 2D capture with the green MONO picture.
--swap expects the swapped-eye model (the picture of the other eye in each half); a run of the right model must then FAIL.
--overlay: the program draws a yellow label over the area; it must be identical in both eyes and the rest of the area must still be
         what the program drew.
--tol N accepts samples within N levels of the expected ones (a run with a widget opacity of 0.99).
Prints one line per check and exits 1 if any fails.
"""
import sys
import numpy as np
from PIL import Image

FONT = {
 'L': [16,16,16,16,16,16,31], 'E': [31,16,16,30,16,16,31], 'F': [31,16,16,30,16,16,16], 'T': [31,4,4,4,4,4,4],
 'R': [30,17,17,30,20,18,17], 'I': [14,4,4,4,4,4,14], 'G': [14,17,16,23,17,17,14], 'H': [17,17,17,31,17,17,17],
 'M': [17,27,21,21,17,17,17], 'O': [14,17,17,17,17,17,14], 'N': [17,25,21,19,17,17,17],
 '0': [14,17,19,21,25,17,14], '1': [4,12,4,4,4,4,14], '2': [14,17,1,2,4,8,31], '3': [30,1,1,14,1,1,30],
 '4': [2,6,10,18,31,2,2], '5': [31,16,30,1,1,17,14], '6': [6,8,16,30,17,17,14], '7': [31,1,2,4,8,8,8],
 '8': [14,17,17,14,17,17,14], '9': [14,17,17,15,1,2,12],
}


def picture(w, h, tag, bg, frame):
    img = np.zeros((h, w, 3), np.uint8)
    img[:, :] = bg
    img[0, :] = img[h - 1, :] = 255
    img[:, 0] = img[:, w - 1] = 255
    q = h // 4
    gl_y = h // 2 - h // 8
    img[h - (gl_y + q) : h - gl_y, w // 2 - h // 8 : w // 2 - h // 8 + q] = 255
    px = h // 28 or 1

    def text(s, x, top):
        for ch in s:
            for row in range(7):
                for col in range(5):
                    if FONT[ch][row] & (16 >> col):
                        y0 = top + row * px
                        img[h - (h - y0) : y0 + px, x + col * px : x + (col + 1) * px] = 255
            x += 6 * px

    text(tag, 12, 12)
    text(str(frame), 12, 12 + 9 * px)
    return img


TOL = 0


def find_box(half, colour):
    mask = np.all(np.abs(half.astype(int) - colour) <= TOL, axis=2)
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    # the picture's one pixel white frame lies one pixel outside the first and last coloured samples
    return (xs.min() - 1, ys.min() - 1, xs.max() + 2, ys.max() + 2)


def main():
    a = sys.argv[1:]
    path = a[0]
    size = (480, 270)
    frame = 7
    swap = '--swap' in a
    expect = 'stereo'
    if '--size' in a:
        size = tuple(int(v) for v in a[a.index('--size') + 1].split('x'))
    if '--frame' in a:
        frame = int(a[a.index('--frame') + 1])
    global TOL
    if '--tol' in a:
        TOL = int(a[a.index('--tol') + 1])
    if '--expect' in a:
        expect = a[a.index('--expect') + 1]
    img = np.array(Image.open(path).convert('RGB'))
    H, W2, _ = img.shape
    fails = 0

    def report(name, ok, detail=''):
        nonlocal fails
        fails += 0 if ok else 1
        print('%s %s %s' % ('PASS' if ok else 'FAIL', name, detail))

    red, blue, green = (255, 0, 0), (0, 0, 255), (0, 127, 0)
    w, h = size
    if expect == 'stereo':
        W = W2 // 2
        halves = (img[:, :W], img[:, W : 2 * W])
        report('capture holds two eyes', W2 == 2 * W and W2 % 2 == 0, 'width %d, one eye %d' % (W2, W))
        left_colour, right_colour = (blue, red) if swap else (red, blue)
        report('left eye has no %s sample' % ('red' if swap else 'blue'),
               not np.any(np.all(halves[0] == (red if swap else blue), axis=2)))
        report('right eye has no %s sample' % ('blue' if swap else 'red'),
               not np.any(np.all(halves[1] == (blue if swap else red), axis=2)))
        boxes = [find_box(halves[0], left_colour), find_box(halves[1], right_colour)]
        report('both eyes show the area', all(boxes), str(boxes))
        if not all(boxes):
            return 1
        report('the area is at its own size in both eyes',
               all((b[2] - b[0], b[3] - b[1]) == size for b in boxes), '%s' % [(b[2] - b[0], b[3] - b[1]) for b in boxes])
        report('the area is at the same place in both eyes', boxes[0] == boxes[1], str(boxes))
        x0, y0, x1, y1 = boxes[0]
        skip = np.zeros((h, w), bool)
        if '--overlay' in a:
            yellow = [np.all(half == (255, 255, 0), axis=2) for half in halves]
            report('the overlay label is in both eyes', yellow[0].any() and yellow[1].any(), '%d and %d yellow samples' % (yellow[0].sum(), yellow[1].sum()))
            report('the overlay label is identical in both eyes', np.array_equal(yellow[0], yellow[1]))
            ys, xs = np.nonzero(yellow[0])
            ox0, oy0, ox1, oy1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
            report('the overlay lies over the area', ox0 >= x0 and oy0 >= y0 and ox1 <= x1 and oy1 <= y1, '%s' % [(ox0, oy0, ox1, oy1)])
            same = np.all(halves[0][oy0:oy1, ox0:ox1] == halves[1][oy0:oy1, ox0:ox1])
            report('the overlay rectangle, with its text, is the same in both eyes', bool(same))
            skip[oy0 - y0 : oy1 - y0, ox0 - x0 : ox1 - x0] = True
        for i, (name, tag, bg) in enumerate((('left', 'LEFT', left_colour), ('right', 'RIGHT', right_colour))):
            want = picture(w, h, tag, bg, frame)
            got = halves[i][y0:y1, x0:x1]
            bad = int(np.count_nonzero(np.any(np.abs(got.astype(int) - want) > TOL, axis=2) & ~skip)) if got.shape == want.shape else -1
            report('%s eye picture equals what the program drew, every sample' % name, bad == 0, '%d of %d samples differ' % (bad, w * h))
        outside = np.ones((H, W), bool)
        outside[y0:y1, x0:x1] = False
        diff = np.any(halves[0] != halves[1], axis=2) & outside
        report('2D parts identical in both eyes (outside the area)', not diff.any(), '%d samples differ' % int(diff.sum()))
    else:
        tag, bg = ('LEFT', red) if expect == 'left' else ('MONO', green)
        box = find_box(img, bg)
        report('the area is shown', box is not None, str(box))
        if box is None:
            return 1
        report('the area is at its own size', (box[2] - box[0], box[3] - box[1]) == size, str((box[2] - box[0], box[3] - box[1])))
        x0, y0, x1, y1 = box
        want = picture(w, h, tag, bg, frame)
        got = img[y0:y1, x0:x1]
        bad = int(np.count_nonzero(np.any(np.abs(got.astype(int) - want) > TOL, axis=2))) if got.shape == want.shape else -1
        report('the picture equals what the program drew, every sample', bad == 0, '%d of %d samples differ' % (bad, w * h))
        report('capture is one eye wide (a 2D window)', True, 'width %d' % W2)
    return 1 if fails else 0


sys.exit(main())
