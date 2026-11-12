#!/usr/bin/env python3
"""The bytes of milestone 2e's procedures against the fair baseline (2d's table: the picture as JPEG q90 and its
lower-resolution copies): m2e_table.py SCRATCH OUT.md. Bytes are read from each procedure's render log (p2p's count)."""
import os, re, sys
S, out = sys.argv[1], sys.argv[2]
base = {'bark_brown_02': (1481516, 613240), 'coast_sand_rocks_02': (1123703, 436804), 'concrete_floor_02': (2185160, 690841),
        'floor_tiles_06': (770833, 292807), 'metal_plate': (876766, 319202), 'ornament_snowflakes': (234849, 155636),
        'patterned_terracotta_tiling': (544773, 206820), 'red_brick_03': (1808818, 563247), 'rock_05': (1706741, 591032),
        'rusty_metal_02': (1017947, 414440)}
rows = [
    ('red_brick_03', 'r02 over r01, by r02\'s height (default)', 'm2e/st/bricks-h.ppm.out'),
    ('red_brick_03', 'r02 over r01, alpha 0.5', 'm2e/st/bricks-a50.ppm.out'),
    ('rusty_metal_02', 's5: four-5, one and four-7 by their marks, 2c-7 spots (default)', 'm2e/st/rm-s5.ppm.out'),
    ('rusty_metal_02', 's1: thirds, 2c-7 at 0.15', 'm2e/st/rm-s1.ppm.out'),
    ('rusty_metal_02', 'sixteen procedures', 'm2e/grid/rusty_metal_02-4x4.ppm.out'),
    ('metal_plate', 'B: pattern with the bevel over the surface colours (default)', 'm2e/st/plate-B.ppm.out'),
    ('metal_plate', 'C: relief and cast shadow, surface over at 0.4', 'm2e/st/plate-C.ppm.out'),
    ('patterned_terracotta_tiling', 'finest grain and each piece\'s stain', 'm2e/fit/terra-fine.ppm.out'),
    ('patterned_terracotta_tiling', 'finest grain, each piece\'s stain and the second colour (default)', 'm2e/fit/terra-stain.ppm.out'),
    ('floor_tiles_06', 'one, the joint\'s darkest line (default)', 'm2e/fit/floor-dark.ppm.out'),
    ('floor_tiles_06', 'four internal tiles', 'm2e/fitq/floor-four.ppm.out'),
    ('ornament_snowflakes', 'tabler-icons snowflake seed', 'm2e/fit/snow-tabler.ppm.out'),
    ('ornament_snowflakes', 'bootstrap-icons snow3 seed (default)', 'm2e/fit/snow-bootstrap.ppm.out'),
    ('ornament_snowflakes', 'two glyphs (snow3 and the hexagram)', 'm2e/st/snow-two.ppm.out'),
]
for n in ['rock_05', 'concrete_floor_02', 'coast_sand_rocks_02', 'bark_brown_02', 'rusty_metal_02']:
    for g, lab in [('2x2', 'four (every band)'), ('4x2', 'eight, 4 by 2'), ('2x4', 'eight, 2 by 4'), ('4x4', 'sixteen')]:
        rows.append((n, lab, 'm2e/grid/%s-%s.ppm.out' % (n, g)))
L = ['# Bytes of milestone 2e\'s procedures against the fair baseline', '',
     'The fair baseline is 2d\'s: the picture as JPEG quality 90 with its lower-resolution copies to 1 pixel. Bytes are p2p\'s count (one class byte and four bytes per word, a Text\'s strings to whole words); a Stack or a Grid stores a node two layers share once. The fonts a seed needs are not counted (cut to one glyph as WOFF2 they were 300 to 720 B in milestone 2).', '',
     '| texture | procedure | operators | bytes | procedure + picture against picture + copies |', '|---|---|---|---|---|']
for n, lab, f in rows:
    p = os.path.join(S, f)
    if not os.path.exists(p):
        L.append('| %s | %s | not drawn | | |' % (n, lab)); continue
    m = re.search(r'(\d+) operators, (\d+) bytes', open(p).read())
    ops, b = int(m.group(1)), int(m.group(2))
    jpg, cp = base[n]
    L.append('| %s | %s | %d | %d B | %+.1f %% |' % (n, lab, ops, b, 100.0 * ((b + jpg) / (jpg + cp) - 1)))
open(out, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L[-8:]))
