#!/bin/sh
# Draw several tile-and-graph pairs and stack their sheets into one picture.
# Usage: look3.sh BUILD_DIR OUT.jpg TILE1.png GRAPH1.txt [TILE2.png GRAPH2.txt ...]
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
B=$1; OUT=$2; shift 2
L=""
while [ $# -gt 1 ]; do
  s="${2%.txt}.jpg"
  PYTHONPATH="$HERE" python3 "$HERE/look.py" "$B" "$1" "$s" "$2"
  L="$L $s"; shift 2
done
python3 - "$OUT" $L <<'PY'
import sys
from PIL import Image
ims = [Image.open(p) for p in sys.argv[2:]]
out = Image.new("RGB", (ims[0].width, sum(i.height + 6 for i in ims) - 6), "white")
y = 0
for i in ims:
    out.paste(i, (0, y)); y += i.height + 6
out.save(sys.argv[1], quality=88)
PY
