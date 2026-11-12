#!/usr/bin/env python3
"""Cut a square picture into cols by rows tiles for the fitter (milestone 2e: eight tiles, 4 by 2 and 2 by 4, and
sixteen): m2e_tiles.py FULL.ppm OUTDIR COLS ROWS [FIT=512]
A tile of a square picture is a rectangle when cols and rows differ; the fitter reads square pictures, so the tile is
laid with its own mirror image beside it (a tall tile) or below it (a wide one) into a square of its longer side: the
procedure sees only the tile's own pixels, and the square repeats without a seam. Grid draws the tile from the
procedure's top left part (0 to s/cols across, 0 to s/rows down, s the smaller of cols and rows), which is where the
tile lies in that square. Writes OUTDIR/tR-C.full.ppm (the square at full size) and OUTDIR/tR-C.ppm (box-reduced to
FIT pixels, or the full square when it is not larger)."""
import os, sys
from PIL import Image, ImageOps

full, out, cols, rows = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
fit = int(sys.argv[5]) if len(sys.argv) > 5 else 512
im = Image.open(full).convert('RGB')
W, H = im.size
if W != H or W % cols or W % rows:
    sys.exit('%s: a square picture whose side divides by the columns and rows is needed (%dx%d)' % (full, W, H))
tw, th = W // cols, H // rows
os.makedirs(out, exist_ok=True)
for r in range(rows):
    for c in range(cols):
        t = im.crop((c * tw, r * th, (c + 1) * tw, (r + 1) * th))
        L = max(tw, th)
        sq = Image.new('RGB', (L, L))
        sq.paste(t, (0, 0))
        if tw < th:
            for k in range(1, L // tw):
                sq.paste(ImageOps.mirror(t) if k % 2 else t, (k * tw, 0))
        elif th < tw:
            for k in range(1, L // th):
                sq.paste(ImageOps.flip(t) if k % 2 else t, (0, k * th))
        sq.save(os.path.join(out, 't%d-%d.full.ppm' % (r, c)))
        (sq.resize((fit, fit), Image.BOX) if L > fit else sq).save(os.path.join(out, 't%d-%d.ppm' % (r, c)))
print('%s: %d by %d tiles of %dx%d, squares of %d, fitted at %d' % (os.path.basename(full), cols, rows, tw, th, max(tw, th), min(fit, max(tw, th))))
