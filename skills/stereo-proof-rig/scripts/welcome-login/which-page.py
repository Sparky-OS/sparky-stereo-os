#!/usr/bin/python3
"""which-page.py CAPTURE WINDOWS.json REFS_DIR: which of the reference pages (REFS_DIR/text-NAME.png: the first line of a
page's description, cut from a capture at frame +10,+92, 620x36) the Welcome window in CAPTURE shows, by mean difference;
prints the name, or "unknown" when none is within 8 levels. (A heading alone does not tell KDE's live page, "Welcome to
Sparky Stereo OS!", from the edition's first page.)"""
import glob, json, os, sys
import numpy as np
from PIL import Image
cap, wins, refs = sys.argv[1:4]
fg = [w['fg'] for w in json.load(open(wins))['windows'] or [] if w['cls'] == 'org.kde.plasma-welcome']
if not fg:
    print('no window'); sys.exit(0)
x, y = int(fg[0][0]), int(fg[0][1])
crop = np.asarray(Image.open(cap).convert('RGB').crop((x + 10, y + 92, x + 630, y + 128))).astype(int)
best = min((float(np.abs(crop - np.asarray(Image.open(r).convert('RGB')).astype(int)).mean()), os.path.basename(r)[5:-4])
           for r in glob.glob(os.path.join(refs, 'text-*.png')))
print(best[1] if best[0] < 8 else 'unknown')
