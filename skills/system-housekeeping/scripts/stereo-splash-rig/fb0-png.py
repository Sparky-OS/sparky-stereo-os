#!/usr/bin/python3 -I
# fb0-png.py TAG-fb0.info TAG-fb0.raw OUT.ppm: the guest's /dev/fb0 as a picture (32 bits per pixel, XRGB), at its
# visible mode (DRM's fbdev emulation shows the smallest screen's size from a buffer as large as the largest; Plymouth's
# frame-buffer renderer draws the visible size).
import sys
from PIL import Image
name, mode, size, stride, bpp = open(sys.argv[1]).read().split()[-5:]
w, h = (int(v) for v in mode.split(':')[1].split('p')[0].split('i')[0].split('x'))
stride, bpp = int(stride), int(bpp)
if bpp != 32:
    raise SystemExit('%s: %d bits per pixel, not read' % (sys.argv[1], bpp))
raw = open(sys.argv[2], 'rb').read()[:stride * h]
Image.frombuffer('RGB', (w, h), raw, 'raw', 'BGRX', stride, 1).save(sys.argv[3], 'PPM')
print('%s %dx%d' % (name, w, h))
