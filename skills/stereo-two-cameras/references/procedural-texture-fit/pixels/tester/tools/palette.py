#!/usr/bin/env python3
"""Choose the page's segment colours by WCAG 2.2's contrast formula (relative luminance, 1.4.3 and 1.4.11):
each fill must stand 3:1 against the panel (non-text contrast) and leave the text on it 4.5:1.
palette.py prints the colours and their ratios for both colour schemes."""
import colorsys


def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def at_lum(h, s, target):
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        r, g, b = colorsys.hls_to_rgb(h / 360, mid, s)
        c = '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))
        if lum(c) < target:
            lo = mid
        else:
            hi = mid
    return c


SCHEMES = {
    'light': {'fg': '#1d1d1f', 'bg': '#f3f3f5', 'panel': '#ffffff', 'muted': '#5a5a64', 'line': '#85858f', 'bar': '#f3f3f5', 'bad': '#b3261e', 'target': 0.262},
    'dark': {'fg': '#ececee', 'bg': '#0e0e10', 'panel': '#151518', 'muted': '#a4a4ae', 'line': '#7a7a85', 'bar': '#19191c', 'bad': '#ff8a80', 'target': 0.1335},
}
HUES = {'proc': (262, 0.62), 'down': (208, 0.70), 'blend': (36, 0.85), 'pic': (145, 0.55), 'badfill': (4, 0.75)}
for name, s in SCHEMES.items():
    print(name)
    for k in ('muted', 'bad'):
        print('  %-6s %s on panel %.2f, on bg %.2f, on bar %.2f' % (k, s[k], ratio(s[k], s['panel']), ratio(s[k], s['bg']), ratio(s[k], s['bar'])))
    print('  fg     %s on panel %.2f, on bg %.2f, on bar %.2f' % (s['fg'], ratio(s['fg'], s['panel']), ratio(s['fg'], s['bg']), ratio(s['fg'], s['bar'])))
    print('  line   %s on panel %.2f, on bg %.2f' % (s['line'], ratio(s['line'], s['panel']), ratio(s['line'], s['bg'])))
    for k, (h, sat) in HUES.items():
        c = at_lum(h, sat, s['target'])
        print('  %-6s %s against panel %.2f, against bar %.2f, text on it %.2f' % (k, c, ratio(c, s['panel']), ratio(c, s['bar']), ratio(s['fg'], c)))
