#!/usr/bin/python3
"""output-of.py WINDOWS.json SESSION.log [x]: the output the Welcome window's centre lies on, from the screens KWin's
window logger names when it loads (SPLASHLOG ... loaded screens=NAME@X,Y,WxH ...); with x, that output's X."""
import json, re, sys
fg = [w['fg'] for w in json.load(open(sys.argv[1]))['windows'] or [] if w['cls'] == 'org.kde.plasma-welcome'][0]
cx, cy = fg[0] + fg[2] / 2, fg[1] + fg[3] / 2
line = [l for l in open(sys.argv[2], errors='replace') if 'loaded screens=' in l][0]
for name, x, y, w, h in re.findall(r'(\S+)@(-?\d+),(-?\d+),(\d+)x(\d+)', line.split('loaded screens=', 1)[1]):
    x, y, w, h = map(int, (x, y, w, h))
    if x <= cx < x + w and y <= cy < y + h:
        print(x if len(sys.argv) > 3 else name); break
