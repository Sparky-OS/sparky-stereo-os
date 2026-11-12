#!/usr/bin/env python3
"""Every procedure of the scene against its picture (ORDER 508, milestone 3): m3_sizes.py SCENE-DIR [OUT.md]
For each mixed texture: the procedure's file as the scene carries it (its text) and gzip-compressed (what an HTTP
server could send), its p2p byte count from milestone 2e's table, the picture as the scene carries it (JPEG quality
85), the picture with its lower-resolution copies to 1 pixel (the fair baseline of milestone 2: what a traditional
asset ships), and the time each takes at 14.4 and 56 kbit/s."""
import gzip, io, json, os, sys
from PIL import Image
d = sys.argv[1]
g = json.load(open(os.path.join(d, 'scene.gltf')))
N = 'SPARKY_texture_mixed'
procs = g['extensions'][N]['procedures']
p2pbytes = {'red_brick_03': 574, 'floor_tiles_06': 256, 'metal_plate': 1436, 'patterned_terracotta_tiling': 851,
            'rock_05': 616, 'bark_brown_02': 1133, 'rusty_metal_02': 3379}     # evidence/m2e/table.md, the defaults
rows = ['| texture | procedure file | gzip | p2p count (2e) | picture (JPEG 85) | picture with its smaller copies | procedure against picture | at 14.4 kbit/s: procedure / picture | at 56 kbit/s: procedure / picture |', '|---|---|---|---|---|---|---|---|---|']
T = {'proc': 0, 'gz': 0, 'pic': 0, 'chain': 0}
t = lambda b, bps: '%.1f s' % (b * 8 / bps) if b * 8 / bps < 120 else '%.1f min' % (b * 8 / bps / 60)
for tex in g['textures']:
    ext = tex['extensions'][N]
    p = procs[ext['procedure']]
    data = open(os.path.join(d, p['uri']), 'rb').read()
    gz = len(gzip.compress(data, 9))
    im = g['images'][tex['source']]
    pic = os.path.getsize(os.path.join(d, im['uri']))
    img = Image.open(os.path.join(d, im['uri'])).convert('RGB')
    chain, w = 0, img.size[0] // 2
    while w >= 1:
        b = io.BytesIO(); img.resize((w, w), Image.LANCZOS).save(b, 'JPEG', quality=85, optimize=True); chain += b.tell(); w //= 2
    name = os.path.basename(p['uri']).replace('.p2p', '')
    T['proc'] += len(data); T['gz'] += gz; T['pic'] += pic; T['chain'] += pic + chain
    rows.append('| %s | %d B | %d B | %d B | %d B | %d B (+%.1f %%) | 1 : %.0f | %s / %s | %s / %s |' % (tex['name'], len(data), gz, p2pbytes.get(name, 0), pic, pic + chain, 100 * chain / pic, pic / len(data),
                t(len(data), 14400), t(pic, 14400), t(len(data), 56000), t(pic, 56000)))
rows.append('| all seven | %d B | %d B | | %d B | %d B | 1 : %.0f | %s / %s | %s / %s |' % (T['proc'], T['gz'], T['pic'], T['chain'], T['pic'] / T['proc'], t(T['proc'], 14400), t(T['pic'], 14400), t(T['proc'], 56000), t(T['pic'], 56000)))
text = '\n'.join(rows) + '\n'
print(text)
if len(sys.argv) > 2:
    open(sys.argv[2], 'w').write(text)
