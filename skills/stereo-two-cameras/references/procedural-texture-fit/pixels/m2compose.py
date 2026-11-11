#!/usr/bin/env python3
"""Put a texture's tiled procedures together and make its sheets (milestone 2).

m2compose.py SCRATCH NAME CHOICE CAPTIONFONT OUTDIR [BAND]
SCRATCH/m2/tex/NAME.png is the picture; SCRATCH/m2/fits/NAME/VARIANT/ the fits; SCRATCH/m2/renders/NAME/VARIANT/ their
drawings (m2render.sh). CHOICE names the variant every tile takes ("plain", "shape", "seed"...), or VARIANT:r-c,r-c
pairs joined by '+' for tiles that take another (for example "plain+second:0-2,1-1"); a tile whose chosen variant has
no fit takes plain, and the caption says which tiles did. BAND is the width of the seam band in pixels (64).

The tiles are joined two ways: hard (each tile's drawing in its own square) and blended: every tile's procedure is drawn
on past its border (a werkkzeug picture repeats, so its continuation is the procedure's own), and across a band at
every border the neighbours are mixed with weights that rise and fall linearly and sum to one; the mix keeps the
contrast of the texture (the weighted sum of each tile's departures from its own mean colour is divided by the root of
the sum of the squared weights, after Heitz and Neyret 2018), where a plain average would leave a grey, soft band.

Writes OUTDIR/NAME-sheet.jpg (the picture, the tiled procedures, one procedure for the whole picture, whole and close
up at the corner of four tiles), OUTDIR/NAME-ladder.jpg (the rungs of every tile, put together, with their bytes),
OUTDIR/NAME-tiled.jpg (the tiled procedures at full size, blended) and OUTDIR/NAME.json (the bytes)."""
import json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

S, name, choice, capfont, outdir = sys.argv[1:6]
band = int(sys.argv[6]) if len(sys.argv) > 6 else 64
# how the band mixes neighbours: 'full' mixes the drawings (for surfaces of noise); 'colour' keeps every pixel's own tile and
# mixes only the tiles' mean colours across the band (for shapes and seeds drawn at their place, which already meet at the
# border: a tile continued past its border is its own repeat, not its neighbour, and would lay a ghost of its shapes)
seam = sys.argv[7] if len(sys.argv) > 7 else 'full'
f = ImageFont.truetype(capfont, 13)
fb = ImageFont.truetype(capfont, 15)
os.makedirs(outdir, exist_ok=True)
pic = Image.open('%s/m2/tex/%s.png' % (S, name)).convert('RGB')
if pic.size[1] != pic.size[0]:
    pic = pic.crop((0, 0, pic.size[0], pic.size[0]))
N = pic.size[0]
T = 512
n = N // T

# which variant each tile takes
default, special = choice.split('+')[0], {}
for part in choice.split('+')[1:]:
    var, tl = part.split(':')
    for rc in tl.split(','):
        special[tuple(int(v) for v in rc.split('-'))] = var
took, fellback = {}, []
for r in range(n):
    for c in range(n):
        v = special.get((r, c), default)
        if v in ('coh', 'kc', 'kcs'):
            took[(r, c)] = v
            continue
        if not os.path.exists('%s/m2/fits/%s/%s/L2-%d-%d.script' % (S, name, v, r, c)):
            fellback.append('%d-%d' % (r, c))
            v = 'plain'
        took[(r, c)] = v


def rungs_of(var, r, c):
    """the rung numbers of a tile's ladder: flat colour, the material, cleaned at 128, at 256, the final one"""
    out = open('%s/m2/fits/%s/%s/L2-%d-%d.out' % (S, name, var, r, c), errors='replace').read().splitlines()
    cur, labels = -1, []
    for line in out:
        m = re.match(r'rung (\d+)', line)
        if m:
            cur = int(m.group(1))
            labels.append((cur, line))
        elif line.startswith('cleaned and tuned at'):
            cur += 1
            labels.append((cur, line))
    def first(pred, dflt):
        for k, l in labels:
            if pred(l):
                return k
        return dflt
    last = labels[-1][0] if labels else 0
    r128 = first(lambda l: 'tuned at 128 px' in l, last)
    r256 = first(lambda l: 'tuned at 256 px' in l, last)
    return [0, min(1, last), r128, r256, last]


def log_bytes(var, r, c):
    rows = [l.split() for l in open('%s/m2/fits/%s/%s/L2-%d-%d.log' % (S, name, var, r, c)) if l[0].isdigit()]
    return {int(x[0]): int(x[2]) for x in rows}


def drawing(var, base):
    p = '%s/m2/renders/%s/%s/%s.ppm' % (S, name, var, base)
    return np.asarray(Image.open(p).convert('RGB'), dtype=np.float64) if os.path.exists(p) else None


def compose(tiles, blend):
    out = np.zeros((N, N, 3))
    if not blend:
        for (r, c), a in tiles.items():
            out[r * T:(r + 1) * T, c * T:(c + 1) * T] = a
        return out
    m = band // 2
    L = T + 2 * m
    ramp = np.ones(L)
    ramp[:2 * m] = (np.arange(2 * m) + 0.5) / (2 * m)
    ramp[-2 * m:] = ramp[:2 * m][::-1]
    w2d = np.outer(ramp, ramp)
    if seam == 'colour':
        hard = compose(tiles, False)
        mean_own = np.zeros((N, N, 3))
        for (r, c), a in tiles.items():
            mean_own[r * T:(r + 1) * T, c * T:(c + 1) * T] = a.reshape(-1, 3).mean(0)
        acc = np.zeros((N, N, 3))
        accw = np.zeros((N, N))
        for (r, c), a in tiles.items():
            mu = a.reshape(-1, 3).mean(0)
            ys = (np.arange(L) + r * T - m) % N
            xs = (np.arange(L) + c * T - m) % N
            iy, ix = np.ix_(ys, xs)
            acc[iy, ix] += w2d[..., None] * mu
            accw[iy, ix] += w2d
        return np.clip(hard - mean_own + acc / accw[..., None], 0, 255)
    acc_mu = np.zeros((N, N, 3))
    acc_dev = np.zeros((N, N, 3))
    acc_w2 = np.zeros((N, N))
    for (r, c), a in tiles.items():
        mu = a.reshape(-1, 3).mean(0)
        ext = np.pad(a, ((m, m), (m, m), (0, 0)), mode='wrap')
        ys = (np.arange(L) + r * T - m) % N
        xs = (np.arange(L) + c * T - m) % N
        iy, ix = np.ix_(ys, xs)
        acc_mu[iy, ix] += w2d[..., None] * mu
        acc_dev[iy, ix] += w2d[..., None] * (ext - mu)
        acc_w2[iy, ix] += w2d ** 2
    return np.clip(acc_mu + acc_dev / np.sqrt(acc_w2)[..., None], 0, 255)


def img(a):
    return Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8))


# the final drawings and the ladder
coherent = default in ('coh', 'kc', 'kcs')
NR = 4 if coherent else 5
ladder = [{} for _ in range(NR)]
lbytes = [0] * NR
missing = []
for (r, c), v in took.items():
    if coherent:
        # the whole picture's rungs, each retuned on the tile's own pixels (variants coh0 to coh3)
        for i in range(NR):
            var_i = 'coh0' if i == 0 else '%s%d' % (default, i)
            a = drawing(var_i, 'L2-%d-%d' % (r, c))
            lg = '%s/m2/fits/%s/%s/L2-%d-%d.log' % (S, name, var_i, r, c)
            if a is None or not os.path.exists(lg):
                missing.append('%s/L2-%d-%d' % (var_i, r, c))
                a = np.full((T, T, 3), 128.0)
            else:
                lbytes[i] += int([l.split() for l in open(lg) if l[0].isdigit()][-1][2])
            ladder[i][(r, c)] = a
        continue
    rk = rungs_of(v, r, c)
    lb = log_bytes(v, r, c)
    fin = drawing(v, 'L2-%d-%d' % (r, c))
    for i, k in enumerate(rk):
        a = fin if i == 4 else drawing(v, 'L2-%d-%d.r%02d' % (r, c, k))
        if a is None:
            missing.append('L2-%d-%d.r%02d' % (r, c, k))
            a = np.full((T, T, 3), 128.0)
        ladder[i][(r, c)] = a
        lbytes[i] += lb.get(k, 0)
tiled_hard = compose(ladder[NR - 1], False)
tiled = compose(ladder[NR - 1], True)
# one procedure for the whole picture, of the same kind as the tiles' where it exists
l0var = 'seed' if default == 'kcs' else 'plain' if default in ('coh', 'kc') else default if os.path.exists('%s/m2/fits/%s/%s/L0-0-0.log' % (S, name, default)) else 'plain'
l0 = drawing(l0var, 'L0-0-0')
try:
    l0rows = [l.split() for l in open('%s/m2/fits/%s/%s/L0-0-0.log' % (S, name, l0var)) if l[0].isdigit()]
    l0_bytes = int(l0rows[-1][2])
except OSError:
    l0_bytes = 0
img(tiled).save(os.path.join(outdir, name + '-tiled.jpg'), quality=90)

# the fair baseline (chain_sizes.py's line for this picture)
base = {}
for line in open('%s/m2/chain-sizes.txt' % S):
    if line.startswith('tex/%s.png:' % name):
        nums = [int(x) for x in re.findall(r'(?<![.\d])(\d{4,})(?![.\d])', line)]
        base = dict(jpeg=nums[0], chain=nums[1], dev=nums[2], png=nums[3], pngchain=nums[4])
counts = {}
for v in took.values():
    counts[v] = counts.get(v, 0) + 1
rec = dict(name=name, choice=choice, seam=seam, l0_variant=l0var, took={'%d-%d' % k: v for k, v in took.items()}, fellback=fellback, band=band,
           rung_bytes=lbytes, l0_bytes=l0_bytes, baseline=base, missing=missing)
json.dump(rec, open(os.path.join(outdir, name + '.json'), 'w'), indent=1)

# the sheet: whole, then 1:1 at the corner where four tiles meet
P = 384
pa = np.asarray(pic, dtype=np.float64)
cy = cx = N // 2
crop = lambda a: img(a[cy - P // 2:cy + P // 2, cx - P // 2:cx + P // 2])
whole = lambda a: img(a).resize((P, P), Image.LANCZOS)
cols = [('the picture', pa), ('%s, seams %s %d px' % ('one procedure retuned per tile' if coherent else 'a procedure per tile', 'mixed over' if seam == 'full' else 'colour-matched over', band), tiled),
        ('tiled, hard borders', tiled_hard), ('one procedure for the whole picture (%s)' % l0var, l0 if l0 is not None else np.full((N, N, 3), 128.0))]
lines = ['%s: %d by %d pixels, tiles of %d pixels (%d by %d); tiles took: %s%s' % (
    name, N, N, T, n, n, ', '.join('%s %d' % kv for kv in sorted(counts.items())),
    ('; no fit of the chosen kind, plain taken: ' + ' '.join(fellback)) if fellback else ''),
    'bytes: the tiled procedures %s B (rungs %s); one procedure for the whole picture %s B' % (
        format(lbytes[NR - 1], ','), ' / '.join(format(b, ',') for b in lbytes), format(l0_bytes, ',')),
    'the picture as JPEG q90 %s B; its lower-resolution copies (the fair baseline) %s B (+%.1f %%); procedures + picture against picture + copies: %+.1f %%' % (
        format(base.get('jpeg', 0), ','), format(base.get('chain', 0), ','), 100.0 * base.get('chain', 0) / max(1, base.get('jpeg', 1)),
        100.0 * ((base.get('jpeg', 0) + lbytes[NR - 1]) / max(1, base.get('jpeg', 0) + base.get('chain', 0)) - 1)),
    'close-ups: 1:1, %d by %d pixels at the middle of the picture, where four tiles meet (the borders cross at the centre of each close-up)' % (P, P)]
W = 4 * (P + 8) + 8
sheet = Image.new('RGB', (W, 2 * (P + 26) + 22 * len(lines) + 16), 'white')
d = ImageDraw.Draw(sheet)
for i, (lab, a) in enumerate(cols):
    x = 8 + i * (P + 8)
    d.text((x, 4), lab, fill='black', font=f)
    sheet.paste(whole(a), (x, 22))
    d.text((x, P + 30), lab + ', close up', fill='black', font=f)
    sheet.paste(crop(a), (x, P + 48))
for i, l in enumerate(lines):
    d.text((8, 2 * P + 60 + 22 * i), l, fill='black', font=fb if i == 0 else f)
sheet.save(os.path.join(outdir, name + '-sheet.jpg'), quality=88)

# the ladder: every tile at the same rung, put together
R = 300
labs = ['rung 0: one flat colour per tile', 'rung 1: the noise between two colours', 'rung 2: as found at 128 px',
        'rung 3: as found at 256 px', 'rung 4: the found procedures']
if coherent:
    labs = ['rung 0: one flat colour per tile', 'rung 1: the noise between two colours', 'rung 2: the whole\'s procedure at 128 px',
            'rung 3: the whole\'s procedure']
lad = Image.new('RGB', ((NR + 1) * (R + 6) + 6, R + 70), 'white')
d = ImageDraw.Draw(lad)
d.text((6, 4), 'the picture', fill='black', font=f)
lad.paste(img(pa).resize((R, R), Image.LANCZOS), (6, 22))
for i in range(NR):
    x = 6 + (i + 1) * (R + 6)
    d.text((x, 4), labs[i], fill='black', font=f)
    lad.paste(img(compose(ladder[i], True)).resize((R, R), Image.LANCZOS), (x, 22))
    d.text((x, R + 26), '%s bytes for %d tiles' % (format(lbytes[i], ','), n * n), fill='black', font=f)
d.text((6, R + 46), '%s: the levels of detail; each rung of a tile is a thinner version of the same tile\'s procedure%s' % (name, ' (the whole picture\'s rungs, each retuned on the tile\'s own pixels)' if coherent else ''), fill='black', font=f)
lad.save(os.path.join(outdir, name + '-ladder.jpg'), quality=88)
print(name, 'rungs', lbytes, 'whole', l0_bytes, 'fell back', fellback, 'missing', len(missing))
