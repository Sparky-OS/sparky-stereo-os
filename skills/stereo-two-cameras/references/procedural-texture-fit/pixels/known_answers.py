#!/usr/bin/env python3
"""Milestone 1e's known answers: .kkrieger's Text textures drawn with the machine's own fonts (Arial, Times New Roman,
Verdana, as installed) beside the stand-ins of milestone 1d and the shipped game's title screen.
known_answers.py REAL_DIR STANDIN_DIR TITLE.jpg CAPTION_FONT OUT_DIR"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
real, stand, title, capfont, out = sys.argv[1:6]
f = ImageFont.truetype(capfont, 15); fs = ImageFont.truetype(capfont, 12)
def font_lines(n, d):
    return [l[6:].strip() for l in open(os.path.join(d, n + '.out'), encoding='utf-8', errors='replace') if l.startswith('text: ')]
# 1: the title screen beside both drawings of flat.credits.kk01
t = Image.open(title).convert('RGB'); t = t.resize((int(t.width * 512 / t.height), 512))
a = Image.open(os.path.join(real, 'flat.credits.kk01.ppm')).convert('RGB')
b = Image.open(os.path.join(stand, 'flat.credits.kk01.ppm')).convert('RGB')
W = t.width + 1024 + 32; sheet = Image.new('RGB', (W, 512 + 150), 'white'); d = ImageDraw.Draw(sheet)
sheet.paste(t, (8, 40)); sheet.paste(a, (t.width + 16, 40)); sheet.paste(b, (t.width + 16 + 512 + 8, 40))
d.text((8, 8), 'the shipped game (title screen capture)', fill='black', font=f)
d.text((t.width + 16, 8), 'flat.credits.kk01, the machine\'s Arial 2.82', fill='black', font=f)
d.text((t.width + 16 + 520, 8), 'the same graph, Liberation Sans standing in (1d)', fill='black', font=f)
cap = ["Left: \".kkrieger title screen.jpg\" on Wikimedia Commons, by .theprodukkt, BSD licence (a JPEG of the 3D scene: the texture blended and stretched to the screen).",
       "Middle: our drawing of the artists' own graph with the font werkkzeug3 names (an empty name is Arial), found installed on this machine: " + '; '.join(font_lines('flat.credits.kk01', real)),
       "Right: the drawing of milestone 1d, " + '; '.join(font_lines('flat.credits.kk01', stand)),
       "The real font draws the same four texts at the same places and sizes; the letter shapes inside the same widths are Arial's own."]
for i, l in enumerate(cap): d.text((8, 512 + 50 + 18 * i), l[:230], fill='black', font=fs)
sheet.save(os.path.join(out, 'title-screen-real-and-standin.jpg'), quality=90)
# 2: twenty-four textures, real fonts above, stand-ins below
names = ['r.kkrieger.g', 'r.kkrieger.e', 'r.kkrieger.k', 'r.kkrieger.r', 'r.kkrieger.i', 't.menu.text01', 'flat.credits.kk01', 'flat.credits.chaos01',
         'flat.credits.gizmo01', 'flat.credits.code01', 'flat.credits.end01', 'flat.credits.ryg01', 'flat.credits.kb01', 'r.drip.drrtyhund.01',
         't.cin.01', 'f.2d.pn01', 'font1.tex', 'amiga_font.tex', 'filigran_messing_font.tex', 'b.blade.01', '0.wood.crate01', 't.metal.yello.02',
         'flat.kkrieger.g01', 't.kkrieger.gback01']
names = [n for n in names if os.path.exists(os.path.join(real, n + '.ppm'))]
c = 6; s = 200; rows = (len(names) + c - 1) // c
sheet = Image.new('RGB', (c * (s + 8) + 8, rows * (2 * s + 40) + 60), 'white'); d = ImageDraw.Draw(sheet)
d.text((8, 8), 'Each pair: above, drawn with the machine\'s Arial 2.82, Times New Roman 2.82, Verdana 2.35; below, with milestone 1d\'s stand-ins (Liberation Sans, Liberation Serif, DejaVu Sans).', fill='black', font=fs)
for i, n in enumerate(names):
    x = 8 + (i % c) * (s + 8); y = 32 + (i // c) * (2 * s + 40)
    sheet.paste(Image.open(os.path.join(real, n + '.ppm')).convert('RGB').resize((s, s), Image.LANCZOS), (x, y))
    sheet.paste(Image.open(os.path.join(stand, n + '.ppm')).convert('RGB').resize((s, s), Image.LANCZOS), (x, y + s + 2))
    d.text((x, y + 2 * s + 6), n[:30], fill='black', font=fs)
sheet.save(os.path.join(out, 'overview-real-above-standin-below.jpg'), quality=88)
print('ok', len(names))
