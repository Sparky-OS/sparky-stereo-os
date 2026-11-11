#!/usr/bin/env python3
"""Milestone 2b's sheets and table, from the final fits and their drawings (every sheet is looked at before a word
is written about it).

m2b_sheets.py SCRATCH EVIDENCE CAPTIONFONT
SCRATCH/m2b/fit5/NAME.{script,log,rNN.script} the fits; SCRATCH/m2b/nat/ their drawings (the whole at 2048 with the
tiles' Tints, the rungs at 512); SCRATCH/m2/ev and ev-seed milestone 2's tiled drawings and byte counts (its json).
Writes EVIDENCE/overview-photos.jpg, overview-motifs.jpg, what-each-operator-bought.jpg, sheets/NAME.jpg,
table.md and found/NAME.txt."""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

S, EV, capfont = sys.argv[1:4]
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
f = ImageFont.truetype(capfont, 14)
fs = ImageFont.truetype(capfont, 12)
os.makedirs(EV + '/sheets', exist_ok=True)
os.makedirs(EV + '/found', exist_ok=True)

PHOTOS = ['bark_brown_02', 'coast_sand_rocks_02', 'concrete_floor_02', 'floor_tiles_06', 'plaster_grey_04',
          'red_brick_03', 'rock_05', 'rust_coarse_01', 'rusty_metal_02']
MOTIFS = ['ornament_snowflakes', 'floor_tiles_06', 'red_brick_03', 'patterned_terracotta_tiling', 'metal_plate',
          'ornament_poinsettias']


def log(n):
    return open('%s/m2b/fit5/%s.log' % (S, n)).read()


def bytes_of(n):
    m = re.search(r"the whole picture's procedure (\d+) operators, (\d+) bytes; with the tiles' Tints (\d+) operators, (\d+) bytes", log(n))
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))


def rungs(n):
    return [(int(a), b, int(c), int(d)) for a, b, c, d in re.findall(r'^rung (\d+): (.*): (\d+) operators, (\d+) bytes$', log(n), re.M)]


def m2json(n, motif):
    p = '%s/m2/%s/%s.json' % (S, 'ev-seed' if motif else 'ev', n)
    return json.load(open(p))


def pic(n):
    return Image.open('%s/m2b/full/%s.ppm' % (S, n)).convert('RGB')


def m2img(n, motif):
    return Image.open('%s/m2/%s/%s-tiled.jpg' % (S, 'ev-seed' if motif else 'ev', n)).convert('RGB')


def mb(n):
    return Image.open('%s/m2b/nat/%s.ppm' % (S, n)).convert('RGB')


def overview(names, motif, out, title):
    G = 300
    cols = 3
    cw = 3 * G + 2 * 4 + 24
    rh = G + 64
    rows = (len(names) + cols - 1) // cols
    sh = Image.new('RGB', (cols * cw, rows * rh + 30), 'white')
    d = ImageDraw.Draw(sh)
    d.text((8, 6), title, fill=(0, 0, 0), font=f)
    for k, n in enumerate(names):
        x = (k % cols) * cw + 8
        y = (k // cols) * rh + 30
        j = m2json(n, motif)
        _, wb, _, tb = bytes_of(n)
        d.text((x, y), n + (' (motif)' if motif else ''), fill=(0, 0, 0), font=f)
        for i, im in enumerate((pic(n), m2img(n, motif), mb(n))):
            sh.paste(im.resize((G, G), Image.LANCZOS), (x + i * (G + 4), y + 18))
        d.text((x, y + G + 22), 'picture | milestone 2: %s B | milestone 2b: %s B (whole %s B, the rest the tiles\' Tints)' %
               (format(j['rung_bytes'][-1], ','), format(tb, ','), format(wb, ',')), fill=(0, 0, 0), font=fs)
        d.text((x, y + G + 38), 'JPEG %s B, its smaller copies %s B' % (format(j['baseline']['jpeg'], ','), format(j['baseline']['chain'], ',')), fill=(0, 0, 0), font=fs)
    sh.save(out, quality=88)


overview(PHOTOS, False, EV + '/overview-photos.jpg', 'Milestone 2b, the nine photographs at full size (2048): the picture | milestone 2 (16 tiles, the whole picture\'s procedure retuned per tile) | milestone 2b (the whole picture\'s procedure of modern operators, a Tint where a tile differs)')
overview(MOTIFS, True, EV + '/overview-motifs.jpg', 'Milestone 2b, the six textures with motifs (2048): the picture | milestone 2 (with its seeds) | milestone 2b (Tiles for laid surfaces, Scatter of a glyph for a motif)')

# per texture: whole and 1:1 at the corner where four tiles meet
for n in sorted(set(PHOTOS + MOTIFS)):
    motif = n in MOTIFS and n not in PHOTOS
    G = 520
    C = 512
    sh = Image.new('RGB', (3 * G + 2 * 6 + 16, G + C + 90), 'white')
    d = ImageDraw.Draw(sh)
    ims = (pic(n), m2img(n, motif), mb(n))
    _, wb, _, tb = bytes_of(n)
    j = m2json(n, motif)
    d.text((8, 6), '%s: the picture | milestone 2 (%s B) | milestone 2b (%s B: the whole %s B and the tiles\' Tints); whole, then 1:1 around the corner of four tiles (1024, 1024)' %
           (n, format(j['rung_bytes'][-1], ','), format(tb, ','), format(wb, ',')), fill=(0, 0, 0), font=fs)
    for i, im in enumerate(ims):
        sh.paste(im.resize((G, G), Image.LANCZOS), (8 + i * (G + 6), 26))
        sh.paste(im.crop((1024 - C // 2, 1024 - C // 2, 1024 + C // 2, 1024 + C // 2)), (8 + i * (G + 6) + (G - C) // 2, G + 40))
    d.text((8, G + C + 50), 'JPEG %s B; its smaller copies (the fair baseline) %s B' % (format(j['baseline']['jpeg'], ','), format(j['baseline']['chain'], ',')), fill=(0, 0, 0), font=fs)
    sh.save('%s/sheets/%s.jpg' % (EV, n), quality=88)

# what each operator bought: every texture's rungs side by side, each labelled with what it added and its bytes
names = sorted(set(PHOTOS + MOTIFS))
G = 210
maxr = max(len(rungs(n)) for n in names)
sh = Image.new('RGB', (230 + maxr * (G + 6) + G + 10, len(names) * (G + 44) + 40), 'white')
d = ImageDraw.Draw(sh)
d.text((8, 6), 'What each operator bought: per texture the picture, then each rung of its procedure (each adds the operators named, with the procedure\'s bytes so far); 512 pixels, shown at %d' % G, fill=(0, 0, 0), font=fs)
for k, n in enumerate(names):
    y = 32 + k * (G + 44)
    d.text((8, y + G // 2), n, fill=(0, 0, 0), font=fs)
    x = 230
    sh.paste(pic(n).resize((G, G), Image.LANCZOS), (x, y))
    d.text((x, y + G + 2), 'the picture', fill=(0, 0, 0), font=fs)
    x += G + 6
    for r, label, ops, by in rungs(n):
        im = Image.open('%s/m2b/nat/%s.r%02d.ppm' % (S, n, r)).convert('RGB')
        sh.paste(im.resize((G, G), Image.LANCZOS), (x, y))
        lab = label.replace("+ the tiles' own Tints", '+ Tints').replace(' (', '\n(')
        d.multiline_text((x, y + G + 2), '%s\n%d ops, %s B' % (lab.split('\n')[0], ops, format(by, ',')), fill=(0, 0, 0), font=fs, spacing=1)
        x += G + 6
sh.save(EV + '/what-each-operator-bought.jpg', quality=88)

# the table
L = ['# Bytes against the fair baseline (milestone 2b)', '',
     'The fair baseline is chain_sizes.py of skill stereo-two-cameras: the picture\'s lower-resolution copies to 1 pixel, box-averaged, JPEG quality 90, which a traditional asset ships beside the picture (milestone 2\'s numbers, the same pictures).',
     'Milestone 2b: one procedure of modern operators for the whole picture, drawn at any tile\'s window (the 16 tiles of 512 put together are the whole drawing at 2048, byte for byte), and a Tint (25 bytes) for each tile whose brightness or saturation differs.',
     'A seed\'s glyph costs its key; the font must be present where the procedure is drawn (Symbola is on the machine; cut to the one glyph as WOFF2 it would weigh 544 bytes, milestone 2\'s measure).', '',
     '| texture | the rungs (bytes, each adds operators) | the whole picture\'s procedure | with the tiles\' Tints | milestone 2 (tiled) | the picture as JPEG q90 | its copies (fair baseline) | procedures + picture against picture + copies |',
     '|---|---|---|---|---|---|---|---|']
seen = set()
for n in PHOTOS + MOTIFS:
    motif = n in MOTIFS and n not in PHOTOS
    key = n
    if key in seen:
        continue
    seen.add(key)
    j = m2json(n, motif)
    wo, wb, to, tb = bytes_of(n)
    rs = ' / '.join(format(b, ',') for _, _, _, b in rungs(n))
    jp, ch = j['baseline']['jpeg'], j['baseline']['chain']
    gain = (jp + tb) / (jp + ch) - 1
    L.append('| %s | %s | %d operators, %s B | %d operators, %s B | %s B | %s B | %s B (+%.1f %%) | %+.1f %% |' %
             (n, rs, wo, format(wb, ','), to, format(tb, ','), format(j['rung_bytes'][-1], ','), format(jp, ','), format(ch, ','), 100 * ch / jp, 100 * gain))
open(EV + '/table.md', 'w').write('\n'.join(L) + '\n')

for n in names:
    t = subprocess.run(['python3', W + '/scripts/script2text.py', '%s/m2b/fit5/%s.script' % (S, n), '11'], capture_output=True, text=True).stdout
    open('%s/found/%s.txt' % (EV, n), 'w').write('# %s: the procedure found from the pixels alone (typed form), drawn at 2048\n%s' % (n, t))
    open('%s/found/%s.log' % (EV, n), 'w').write(log(n))
print('sheets written')
