#!/usr/bin/python3
"""heading-differs.py EN.png EN_WINDOWS.json OTHER.png OTHER_WINDOWS.json: the Welcome window's heading strip (frame +10,+36,
320x32, the left eye) of a login in another language against the English login's: "translated" when more than 5 % of its
pixels differ, else "same"."""
import json, sys
import numpy as np
from PIL import Image
def strip(cap, wins):
    fg = [w['fg'] for w in json.load(open(wins))['windows'] or [] if w['cls'] == 'org.kde.plasma-welcome'][0]
    x, y = int(fg[0]), int(fg[1])
    return np.asarray(Image.open(cap).convert('RGB').crop((x + 10, y + 36, x + 330, y + 68))).astype(int)
a, b = strip(*sys.argv[1:3]), strip(*sys.argv[3:5])
print('translated' if (np.abs(a - b).max(axis=2) > 24).mean() > 0.05 else 'same')
