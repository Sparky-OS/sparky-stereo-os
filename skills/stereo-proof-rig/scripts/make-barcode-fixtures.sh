#!/bin/sh
# make-barcode-fixtures.sh OUT: inside the rig, a full side by side clip whose every column can be told from every other.
#   bar3d.mkv  two 960x540 views, side by side, H.264 lossless (qp 0) with the frame packing SEI type 3, Matroska, one view's display
#              size; in each view, ten bands of 40 rows hold the bits of the column's number (white 1, black 0, lowest bit first),
#              a band at rows 400 to 439 holds the eye (white right, black left)
set -e
out=$1; mkdir -p "$out"; cd "$out"
python3 - <<'PY'
from PIL import Image
W, H = 960, 540
img = Image.new("RGB", (2 * W, H), (0, 0, 0))
px = img.load()
for eye in (0, 1):
    for x in range(W):
        for k in range(10):
            v = 255 if (x >> k) & 1 else 0
            for y in range(40 * k, 40 * k + 40):
                px[eye * W + x, y] = (v, v, v)
        for y in range(400, 440):
            px[eye * W + x, y] = (255, 255, 255) if eye else (0, 0, 0)
img.save("bar3d.png")
PY
ffmpeg -nostdin -v error -y -loop 1 -framerate 25 -i bar3d.png -t 20 -c:v libx264 -pix_fmt yuv420p -x264-params qp=0:frame-packing=3 -f h264 bar3d.h264
mkvmerge -q -o bar3d.mkv --default-duration 0:25fps --display-dimensions 0:960x540 bar3d.h264
rm bar3d.h264
ffmpeg -nostdin -hide_banner -i bar3d.mkv -frames:v 1 -vf showinfo -f null - 2>&1 | grep -i "stereo\|s:1920" | head -3
ls -la
