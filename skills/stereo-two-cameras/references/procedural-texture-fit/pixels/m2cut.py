#!/usr/bin/env python3
"""Cut a picture into the tiles of the three levels the procedures are fitted to (milestone 2).

m2cut.py PICTURE.png OUTDIR [TILE]
Level 0 is the whole picture, level 1 its 2 by 2 quarters, level 2 its tiles of TILE pixels at full size (512 by default);
every level's tile is handed to the fitter at TILE pixels (a larger window box-averaged down), so every fit runs at the
same size and a procedure is then drawn at its window's own size. Writes OUTDIR/L{level}-{row}-{col}.ppm and
OUTDIR/tiles.txt (one line per tile: name level row col x y side)."""
import os, sys
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
tile = int(sys.argv[3]) if len(sys.argv) > 3 else 512
im = Image.open(src).convert('RGB')
w, h = im.size
if w != h or w % tile:
    sys.exit('the picture must be square and a whole number of tiles wide (%dx%d, tile %d)' % (w, h, tile))
os.makedirs(out, exist_ok=True)
rows = []
level, n = 0, 1
while w // n >= tile:
    side = w // n
    for r in range(n):
        for c in range(n):
            win = im.crop((c * side, r * side, (c + 1) * side, (r + 1) * side))
            if side != tile:
                win = win.reduce(side // tile)  # box average: the fitter sees the window as a tile of TILE pixels
            name = 'L%d-%d-%d' % (level, r, c)
            win.save(os.path.join(out, name + '.ppm'))
            rows.append('%s %d %d %d %d %d %d' % (name, level, r, c, c * side, r * side, side))
    level += 1
    n *= 2
with open(os.path.join(out, 'tiles.txt'), 'w') as f:
    f.write('\n'.join(rows) + '\n')
print(len(rows), 'tiles in', level, 'levels')
