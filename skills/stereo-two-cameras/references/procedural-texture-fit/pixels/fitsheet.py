#!/usr/bin/env python3
"""Sheets for fits read over the whole font index: the picture and the found procedure's drawing, whole and close up,
what the reading said, the found graph as typed text (characters also as code points), and the found font's credit
from its own name table (designer, copyright) with its licence class.

fitsheet.py INDEX.tsv REF_DIR FIT_DIR OUT_DIR CAPTION_FONT NAME...   (REF_DIR/NAME.ppm, FIT_DIR/NAME.{ppm,script,out})
Writes OUT_DIR/NAME.jpg for every name and OUT_DIR/overview.jpg (the pairs at half size)."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
index, ref, fit, out, capfont = sys.argv[1:6]
names = sys.argv[6:]
here = os.path.dirname(os.path.abspath(__file__))
rows = [l.rstrip('\n').split('\t') for l in open(index, encoding='utf-8')]
col = {n: i for i, n in enumerate(rows[0])}
by_key = {r[0]: r for r in rows[1:]}
f = ImageFont.truetype(capfont, 14)
import json, re
def shown(t):
    """the caption font draws Latin, Greek and Cyrillic; other characters are written as code points"""
    return ''.join(ch if ord(ch) < 0x530 or 0x2000 <= ord(ch) < 0x2070 else '<U+%04X>' % ord(ch) for ch in t)
os.makedirs(out, exist_ok=True)
pairs = []
for n in names:
    a = Image.open(os.path.join(ref, n + '.ppm')).convert('RGB')
    fp = os.path.join(fit, n + '.ppm')
    b = Image.open(fp).convert('RGB') if os.path.exists(fp) else Image.new('RGB', a.size, (128, 128, 128))
    lines = []
    o = os.path.join(fit, n + '.out')
    outl = open(o, encoding='utf-8', errors='replace').read().splitlines() if os.path.exists(o) else []
    lines += [shown(l.strip()) for l in outl if l.startswith('figure: ') or l.startswith('  text "') or l.startswith('  colour piece')][:8]
    done = [l for l in outl if l.startswith('done: ')]
    if done:
        lines.append(done[-1])
    refused = [l for l in outl if 'is refused' in l or l.startswith('structure ')]
    lines += refused[:1]
    sp = os.path.join(fit, n + '.script')
    keys = []
    if os.path.exists(sp):
        typed = subprocess.run([sys.executable, '-I', os.path.join(here, 'script2text.py'), sp], capture_output=True, text=True).stdout.splitlines()
        lines.append('found from the pixels alone (%d operators):' % len(typed))
        for t in typed:
            # the characters also as code points: a caption font draws no Hebrew in order and no private-use icon
            q = [json.loads(m) for m in re.findall(r'"(?:[^"\\]|\\.)*"', t)]
            if len(q) >= 2 and ' Text ' in t:
                cps = ' '.join('U+%04X' % ord(ch) for ch in q[0])
                lines.append('   ' + shown(t)[:150] + '   [' + cps[:110] + ']')
                keys.append(q[1])
            else:
                lines.append('   ' + shown(t)[:170])
    for k in dict.fromkeys(keys):
        r = by_key.get(k)
        if r is None:
            if k in ('', 'times new roman', 'verdana'):
                lines.append('font: "%s" is werkkzeug3\'s own name (an empty name is Arial), drawn with the font installed on this machine' % k)
            continue
        lines.append('font: %s %s, %s, from %s; designer: %s; %s; licence: %s' % (r[col['family']], r[col['style']], r[col['version']].split(';')[0], r[col['source']],
                     r[col['designer']], r[col['copyright']][:110], r[col['class']] if 'class' in col else '-'))
    w = a.width
    g = 256
    small = a.convert('L').resize((w // 16, w // 16), Image.BOX)
    data = list(small.getdata()); bg = max(set(data), key=data.count)
    px = small.load(); k = g // 16; m = w // 16; best = -1; cx = cy = (w - g) // 2
    for y in range(0, m - k + 1, 2):
        for x in range(0, m - k + 1, 2):
            v = sum(abs(px[x + i, y + j] - bg) for i in range(k) for j in range(k))
            if v > best:
                best, cx, cy = v, x * 16, y * 16
    tiles = [('picture, whole', a.resize((g, g), Image.LANCZOS)), ('found, whole', b.resize((g, g), Image.LANCZOS)),
             ('picture, close up 1:1', a.crop((cx, cy, cx + g, cy + g))), ('found, close up 1:1', b.crop((cx, cy, cx + g, cy + g)))]
    sheet = Image.new('RGB', (4 * g + 5 * 6, g + 30 + 18 * len(lines) + 8), 'white')
    d = ImageDraw.Draw(sheet)
    for i, (lab, im) in enumerate(tiles):
        x = 6 + i * (g + 6)
        sheet.paste(im, (x, 22))
        d.text((x, 2), lab, fill='black', font=f)
    for i, l in enumerate(lines):
        d.text((6, g + 28 + 18 * i), l[:180], fill='black', font=f)
    sheet.save(os.path.join(out, n + '.jpg'), quality=90)
    pairs.append((n, a.resize((g, g), Image.LANCZOS), b.resize((g, g), Image.LANCZOS)))
cols = 3
ov = Image.new('RGB', (cols * (2 * 256 + 24), ((len(pairs) + cols - 1) // cols) * (256 + 30)), 'white')
d = ImageDraw.Draw(ov)
for i, (n, a, b) in enumerate(pairs):
    x = (i % cols) * (2 * 256 + 24); y = (i // cols) * (256 + 30)
    ov.paste(a, (x, y + 20)); ov.paste(b, (x + 258, y + 20))
    d.text((x, y + 2), n + ': picture | found', fill='black', font=f)
ov.save(os.path.join(out, 'overview.jpg'), quality=88)
print('sheets', len(pairs))
