#!/usr/bin/python3 -I
# verdict-theme.py RUNS SET THEME [LIMITS...]: every check of ORDER 715 for one theme of one package set (the captures batch-theme.sh
# saved), each against a prediction written from the limits before the frames are read. Exit 0 only when every check passes.
#   limits  D = popped 4, sunk 10 (the display's defaults)   L = 8, 20   Z = 0, 0 (flat)   R = 3.25, 8.13 (a laptop's line)
#   levels  the swirl and its orbit lines stand at half the popped limit, the wordmark at the popped limit, the background at 0;
#           pixels of a view 1920 wide, scaled to the eye's width, rounded to whole pixels: right minus left is minus that.
#   checks  1 the panel as the left and the right eye: one full-size picture, the shifts of the swirl and the wordmark as predicted,
#             the background not moved, one wordmark and not two
#           2 the panel as anaglyph: the red and the cyan picture apart by the same shifts
#           3 the television as frame packing: the two eyes of the frame (rows 0-1079 and 1125-2204) apart by the shifts at 1920
#           4 both screens, panel main: the panel shows what it shows alone, the television (not named) shows the panel's left eye
#           5 both screens, television main: the television shows what it shows alone, the panel (not named) shows the television's left eye
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = __file__.rsplit('/', 1)[0]
LIM = {'D': (4.0, 10.0), 'L': (8.0, 20.0), 'Z': (0.0, 0.0), 'R': (3.25, 8.13)}
runs, setname, theme = sys.argv[1:4]
limits = sys.argv[4:] or ['D', 'L', 'Z', 'R']
fails = 0
total = 0


def whole(d, w):
    return int(d * w / 1920 + 0.5)


def run(*args):
    return subprocess.run(['python3', '-I', HERE + '/measure.py', *args], capture_output=True, text=True)


def parse(out):
    # "right minus left: wordmark +N px (...), swirl +N px (...); background strip ...: largest difference N; wordmarks ...: left A, right B"
    import re
    m = re.search(r'wordmark ([+-]\d+) px.*swirl ([+-]\d+) px.*largest difference (\d+); wordmarks along the bottom: left (\d+), right (\d+)', out)
    return tuple(int(x) for x in m.groups())


def check(ok, text):
    global fails, total
    total += 1
    fails += 0 if ok else 1
    print(('PASS  ' if ok else 'FAIL  ') + text)


def png(name):
    return '%s/%s-%s.ppm' % (runs, setname + '-' + theme, name)


def exists(path):
    try:
        open(path).close()
        return True
    except OSError:
        return False


for l in limits:
    p, s = LIM[l]
    pre = '%s %s limits %s (popped %g sunk %g)' % (setname, theme, l, p, s)
    for kind, wide in (('eyes', 1366), ('anaglyph', 1366), ('fp', 1920)):
        wm_pred, sw_pred = -whole(p, wide), -whole(p / 2, wide)
        if kind == 'eyes':
            a, b = png('%s-panel-left-1-eDP-1' % l), png('%s-panel-right-1-eDP-1' % l)
            r = run('eyes', a, b, 'L/R')
        elif kind == 'anaglyph':
            r = run('anaglyph', png('%s-panel-anaglyph-modern-1-eDP-1' % l), 'anaglyph')
        else:
            r = run('fp', png('%s-tv-fp-1-HDMI-A-1' % l), 'frame packing')
        if r.returncode:
            check(False, '%s, %s: %s' % (pre, kind, (r.stdout + r.stderr).strip()[:200]))
            continue
        wm, sw, bg, cl, cr = parse(r.stdout)
        ok = (wm, sw) == (wm_pred, sw_pred) and bg <= 2 and cl == 1 and cr == 1
        check(ok, '%s, %s: wordmark %+d px (predicted %+d), swirl %+d px (predicted %+d), background largest difference %d, wordmarks left %d right %d' %
              (pre, kind, wm, wm_pred, sw, sw_pred, bg, cl, cr))
    # 4 and 5: both screens
    alone_panel = png('%s-panel-anaglyph-modern-1-eDP-1' % l)
    alone_tv = png('%s-tv-fp-1-HDMI-A-1' % l)
    r = run('one', alone_panel, png('%s-both-panelmain-1-eDP-1' % l), 'panel main, eDP-1 against the panel alone')
    check(r.returncode == 0, '%s, both screens panel main: %s' % (pre, r.stdout.strip()))
    r = subprocess.run(['python3', '-I', HERE + '/check-eye.py', png('%s-panel-left-1-eDP-1' % l),
                        png('%s-both-panelmain-1-HDMI-A-1' % l), 'television not named'], capture_output=True, text=True)
    check(r.returncode == 0, '%s, both screens panel main: %s' % (pre, r.stdout.strip()))
    r = run('one', alone_tv, png('%s-both-tvmain-1-HDMI-A-1' % l), 'television main, HDMI-A-1 against the television alone')
    check(r.returncode == 0, '%s, both screens television main: %s' % (pre, r.stdout.strip()))
    r = subprocess.run(['python3', '-I', HERE + '/check-eye.py', alone_tv,
                        png('%s-both-tvmain-1-eDP-1' % l), 'panel not named'], capture_output=True, text=True)
    check(r.returncode == 0, '%s, both screens television main: %s' % (pre, r.stdout.strip()))
print('VERDICT %s %s: %d of %d checks pass' % (setname, theme, total - fails, total))
sys.exit(1 if fails else 0)
