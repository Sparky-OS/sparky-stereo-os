#!/usr/bin/env python3
"""The page's link while its tab is hidden: the window is minimized through DevTools for a while in the middle of a
download, and the link's own record is read afterwards. A hidden page's timers wake about once a second, so the bytes
must come in lumps while the average rate holds.
hidden.py OUTDIR TAG DEVTOOLS-PORT SERVER-PORT TIMEOUT-S [unused]      writes TAG-hidden.json
CONTROL=1: the allowance for a hidden tab is switched off first; the rate while hidden must then collapse."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import devtools  # noqa: E402

out, tag = sys.argv[1], sys.argv[2]
dport, sport = int(sys.argv[3]), int(sys.argv[4])
timeout = float(sys.argv[5]) if len(sys.argv) > 5 else 300
HIDE = float(os.environ.get('HIDE') or '20')      # seconds the window stays minimized
TAIL = float(os.environ.get('TAIL') or '0')       # with a long HIDE: also measure the last TAIL seconds of it (after five minutes a browser may wake a hidden page only once a minute)
ws = devtools.WS(devtools.target(dport, sport))
ws.call('Runtime.enable')
ev = lambda js: devtools.evaluate(ws, js)
res = {}
devtools.wait_for(ws, 'window.testerState && testerState().firstFrame && testerState().comps.some((c) => c.kind === "picture" && c.received > 0) && true', timeout=120)
time.sleep(3)
# the control (CONTROL=1 in the environment): the hidden tab's allowance set to the ordinary 0.1 s, so the lost time
# is not made up and the rate while hidden must collapse
if os.environ.get('CONTROL') == '1':
    res['control'] = devtools.evaluate(ws, 'import("./link.js").then((m) => { m.PageLink.HIDDEN_BURST = 0.1; return m.PageLink.HIDDEN_BURST; })', await_promise=True)
win = ws.call('Browser.getWindowForTarget')
res['before'] = ev('document.visibilityState')
t_hide = ev('performance.now()')
ws.call('Browser.setWindowBounds', {'windowId': win['windowId'], 'bounds': {'windowState': 'minimized'}})
time.sleep(1.0)
res['minimized'] = ev('document.visibilityState')
time.sleep(HIDE - 1.0)
ws.call('Browser.setWindowBounds', {'windowId': win['windowId'], 'bounds': {'windowState': 'normal'}})
time.sleep(0.5)
t_show = ev('performance.now()')
res['after'] = ev('document.visibilityState')
r = devtools.wait_for(ws, 'window.testerResult', timeout=timeout)
if r:
    R = json.loads(r)
    bps = R['settings']['bitsPerSecond']
    log = R['linkLog']
    # the link's clock starts at its reset; the page's clock at navigation: place the hidden interval on the link's clock
    # through the pictures' first chunk (R.rate holds the page clock of every chunk handed over)
    off = R['rate'][0][0] / 1000 - log[0][0]
    a, b = t_hide / 1000 - off + 1.5, t_show / 1000 - off - 0.5
    inside = [x for x in log if a <= x[0] <= b]
    gaps = sorted(set(round(x[0], 1) for x in inside))
    wakes = len(gaps)
    by = sum(x[1] for x in inside)
    if TAIL > 0:
        ta, tb = b - TAIL, b
        late = [x for x in log if ta <= x[0] <= tb]
        res['last_seconds_hidden'] = {'seconds': TAIL, 'bytes': sum(x[1] for x in late), 'rate_error': (sum(x[1] for x in late) * 8 / TAIL) / bps - 1,
                                      'wakes': len(set(round(x[0]) for x in late)), 'longest_gap_between_lumps': max((y[0] - x[0] for x, y in zip(late, late[1:])), default=None)}
    res.update({
        'set_bits_per_second': bps, 'hiddenSeconds': R.get('hiddenSeconds'), 'messages': R.get('messageTexts'),
        'whole_transfer_error': R['measuredWhole'] / bps - 1,
        'while_hidden': {'seconds': b - a, 'bytes': by, 'rate_error': (by * 8 / (b - a)) / bps - 1, 'distinct_tenths_of_a_second_with_bytes': wakes,
                         'largest_lump_bytes': max((sum(x[1] for x in inside if round(x[0], 1) == g) for g in gaps), default=0)},
        'chunk_bytes': max(x[1] for x in log),
    })
    with open(os.path.join(out, tag + '-result.json'), 'w') as f:
        f.write(r)
with open(os.path.join(out, tag + '-hidden.json'), 'w') as f:
    json.dump(res, f, indent=1)
print(json.dumps(res, indent=1))
with open(os.path.join(out, 'DONE'), 'w') as f:
    f.write('ok')
