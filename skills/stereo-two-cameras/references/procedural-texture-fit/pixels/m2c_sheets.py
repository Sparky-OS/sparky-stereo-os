#!/usr/bin/env python3
"""The sheets of milestone 2c for Daniel: overviews of the photographs and of the motifs (the picture, milestone 2b,
milestone 2c), a sheet per texture (whole, then 1:1 around the corner of four tiles), "what each added layer bought"
(every rung at 1:1 beside the picture, with its bytes), and the table of bytes against the fair baseline.

m2c_sheets.py FITDIR RENDERDIR LOOK2B EVIDENCE
FITDIR holds the fits (NAME.log with its rungs), RENDERDIR the native drawings of m2c_renderset.py, LOOK2B milestone
2b's drawings at 512 (NAME-2b-w.ppm whole, NAME-2b-c.ppm 1:1) made by m2c_look.py, EVIDENCE the folder written."""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont

S = '/var/tmp/procedures-from-pixels-508'
W = '/K3D/partners/queue/procedures-from-pixels-508'
fit, ren, look, ev = sys.argv[1:5]
os.makedirs(ev + '/sheets', exist_ok=True)
try:
    FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    SMALL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
except OSError:
    FONT = SMALL = ImageFont.load_default()
PHOTOS = ['bark_brown_02', 'coast_sand_rocks_02', 'concrete_floor_02', 'floor_tiles_06', 'plaster_grey_04', 'red_brick_03', 'rock_05', 'rust_coarse_01', 'rusty_metal_02']
MOTIFS = ['ornament_snowflakes', 'floor_tiles_06', 'red_brick_03', 'patterned_terracotta_tiling', 'metal_plate', 'ornament_poinsettias']


def rungs(name):
    out = []
    for l in open('%s/%s.log' % (fit, name)):
        m = re.match(r'rung (\d+): (.*): (\d+) operators, (\d+) bytes', l)
        if m:
            out.append((int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))))
    return out


def done(name):
    for l in open('%s/%s.log' % (fit, name)):
        m = re.match(r"done: the whole picture's procedure (\d+) operators, (\d+) bytes; with the tiles' Tints (\d+) operators, (\d+) bytes", l)
        if m:
            return [int(x) for x in m.groups()]
    raise SystemExit('no done line for ' + name)


# milestone 2b's table: the picture's bytes, its copies, 2b's whole and with Tints
base = {}
for l in open(W + '/evidence/m2b/table.md'):
    c = [x.strip() for x in l.split('|')]
    if len(c) > 8 and c[1] and c[1][0].islower() and c[1] != 'texture':
        num = lambda s: int(re.findall(r'([\d,]+) B', s)[0].replace(',', ''))
        base[c[1]] = {'whole2b': num(c[3]), 'tints2b': num(c[4]), 'jpeg': num(c[6]), 'copies': num(c[7])}


def pic(name, size):
    return Image.open('%s/m2b/full/%s.ppm' % (S, name)).convert('RGB').resize((size, size), Image.LANCZOS)


def crop(name):
    return Image.open('%s/m2b/full/%s.ppm' % (S, name)).convert('RGB').crop((768, 768, 1280, 1280))


def label(d, xy, text, font=FONT):
    d.text(xy, text, fill='black', font=font)


# per texture sheets
for n in sorted(set(PHOTOS + MOTIFS)):
    T = 520
    sh = Image.new('RGB', (3 * T + 40, 2 * T + 110), 'white')
    d = ImageDraw.Draw(sh)
    wd = done(n)
    label(d, (10, 6), '%s: the picture | milestone 2b (%d B) | milestone 2c (%d B: the whole %d B and the tiles\' Tints); whole, then 1:1 around the corner of four tiles' % (n, base[n]['tints2b'], wd[3], wd[1]))
    ims = [pic(n, T), Image.open('%s/%s-2b-w.ppm' % (look, n)).resize((T, T), Image.LANCZOS), Image.open('%s/%s.ppm' % (ren, n)).resize((T, T), Image.LANCZOS)]
    for k, im in enumerate(ims):
        sh.paste(im, (10 + k * (T + 10), 30))
    ims = [crop(n), Image.open('%s/%s-2b-c.ppm' % (look, n)), Image.open('%s/%s-c.ppm' % (ren, n))]
    for k, im in enumerate(ims):
        sh.paste(im.resize((T, T), Image.NEAREST) if im.size[0] != T else im, (10 + k * (T + 10), 40 + T))
    label(d, (10, 2 * T + 52), 'JPEG %s B; its smaller copies (the fair baseline) %s B' % (format(base[n]['jpeg'], ','), format(base[n]['copies'], ',')))
    sh.save('%s/sheets/%s.jpg' % (ev, n), quality=90)


# overviews
def overview(names, title, path):
    T = 300
    rows = (len(names) + 2) // 3
    sh = Image.new('RGB', (3 * (3 * T + 40), rows * (T + 70) + 40), 'white')
    d = ImageDraw.Draw(sh)
    label(d, (10, 8), title)
    for k, n in enumerate(names):
        x0 = 10 + (k % 3) * (3 * T + 40)
        y0 = 36 + (k // 3) * (T + 70)
        wd = done(n)
        label(d, (x0, y0), n, SMALL)
        ims = [pic(n, T), Image.open('%s/%s-2b-w.ppm' % (look, n)).resize((T, T), Image.LANCZOS), Image.open('%s/%s.ppm' % (ren, n)).resize((T, T), Image.LANCZOS)]
        for j, im in enumerate(ims):
            sh.paste(im, (x0 + j * (T + 5), y0 + 18))
        label(d, (x0, y0 + T + 22), 'picture | 2b: %s B | 2c: %s B (whole %s B, the rest the tiles\' Tints)' % (format(base[n]['tints2b'], ','), format(wd[3], ','), format(wd[1], ',')), SMALL)
    sh.save(path, quality=88)


overview(PHOTOS, 'Milestone 2c, the nine photographs at full size (2048): the picture | milestone 2b | milestone 2c (the close-up layers each by its reading, a Tint where a tile differs)', ev + '/overview-photos.jpg')
overview(MOTIFS, 'Milestone 2c, the six textures with motifs or laid structures (2048): the picture | milestone 2b | milestone 2c', ev + '/overview-motifs.jpg')

# what each added layer bought: every rung at 1:1 (the corner of four tiles), the picture first
names = sorted(set(PHOTOS + MOTIFS))
T = 256
maxr = max(len(rungs(n)) for n in names)
sh = Image.new('RGB', (10 + (maxr + 1) * (T + 8), len(names) * (T + 58) + 40), 'white')
d = ImageDraw.Draw(sh)
label(d, (10, 8), 'What each added layer bought: at 1:1 around the corner of four tiles, the picture, then every rung of the procedure (each adds what its label names), with its bytes')
for r, n in enumerate(names):
    y0 = 36 + r * (T + 58)
    label(d, (10, y0), n, SMALL)
    sh.paste(crop(n).resize((T, T), Image.LANCZOS), (10, y0 + 16))
    label(d, (10, y0 + T + 18), 'the picture', SMALL)
    for k, (i, lab, ops, b) in enumerate(rungs(n)):
        p = '%s/%s.r%02d-c.ppm' % (ren, n, i)
        if not os.path.exists(p):
            continue
        x = 10 + (k + 1) * (T + 8)
        sh.paste(Image.open(p).resize((T, T), Image.LANCZOS), (x, y0 + 16))
        words = lab.replace('+ ', '')
        label(d, (x, y0 + T + 18), (words[:38] + ('...' if len(words) > 38 else '')), SMALL)
        label(d, (x, y0 + T + 33), '%d operators, %s B' % (ops, format(b, ',')), SMALL)
sh.save(ev + '/what-each-layer-bought.jpg', quality=88)

# the table
with open(ev + '/table.md', 'w') as f:
    f.write('# Bytes against the fair baseline (milestone 2c)\n\n')
    f.write('The fair baseline is chain_sizes.py of skill stereo-two-cameras: the picture\'s lower-resolution copies to 1 pixel, box-averaged, JPEG quality 90 (milestone 2\'s numbers, the same pictures).\n')
    f.write('Milestone 2c: milestone 2b\'s whole-picture procedure, then each close-up layer its reading allowed (a rung each), then a Tint for each tile whose brightness or saturation differs.\n\n')
    f.write('| texture | the rungs (bytes; each adds what it names) | the whole picture\'s procedure | with the tiles\' Tints | milestone 2b with its Tints | the picture as JPEG q90 | its copies (fair baseline) | procedures + picture against picture + copies |\n')
    f.write('|---|---|---|---|---|---|---|---|\n')
    for n in names:
        wd = done(n)
        rr = '<br>'.join('%d B %s' % (b, lab) for (i, lab, ops, b) in rungs(n))
        gain = (wd[3] + base[n]['jpeg']) / (base[n]['jpeg'] + base[n]['copies']) - 1
        f.write('| %s | %s | %d operators, %s B | %d operators, %s B | %s B | %s B | %s B | %.1f %% |\n' % (
            n, rr, wd[0], format(wd[1], ','), wd[2], format(wd[3], ','), format(base[n]['tints2b'], ','), format(base[n]['jpeg'], ','), format(base[n]['copies'], ','), 100 * gain))
print('sheets in', ev)
