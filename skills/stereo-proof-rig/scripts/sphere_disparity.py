import sys, json
import numpy as np
from PIL import Image
# usage: measure.py CAP.png X0 Y0 X1 Y1 -- per-eye centroid of the red, green and blue spheres inside the box (one eye's coordinates)
cap = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int)
x0, y0, x1, y1 = map(int, sys.argv[2:6])
h, w, _ = cap.shape
stereo = w >= 2 * 1280 - 1 and w % 2 == 0 and w > 1500
ew = w // 2 if stereo else w
eyes = {'L': cap[:, :ew], 'R': cap[:, ew:]} if stereo else {'L': cap, 'R': cap}
def blob(img, ch):
    box = img[y0:y1, x0:x1]
    r, g, b = box[..., 0], box[..., 1], box[..., 2]
    m = {'red': (r > 120) & (g < 60) & (b < 60), 'green': (g > 120) & (r < 60) & (b < 60), 'blue': (b > 120) & (r < 60) & (g < 60)}[ch]
    ys, xs = np.nonzero(m)
    return (float(xs.mean()) + x0, float(ys.mean()) + y0, int(m.sum())) if len(xs) > 20 else None
out = {'stereo_capture': bool(stereo), 'eyes_equal_pixels_differing': int((eyes['L'] != eyes['R']).any(axis=2).sum())}
for ch in ('red', 'green', 'blue'):
    L, R = blob(eyes['L'], ch), blob(eyes['R'], ch)
    out[ch] = {'L': L, 'R': R, 'disparity_px (xL - xR, + = in front of the screen)': None if not (L and R) else round(L[0] - R[0], 3), 'vertical_px': None if not (L and R) else round(L[1] - R[1], 3)}
print(json.dumps(out, indent=1))
