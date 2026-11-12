#!/usr/bin/env python3
"""The tables of the comparison matrix (ORDER 537): every run in one table, and each cell's two runs side by side, the
link simulated in the page against the local server's: the first frame, each picture's time, the order of arrival,
the rate's error (the link's own record and the page's reading), the worst one-second window, and the work after a
texture stopped. summary.py OUTBASE [--write]   (OUTBASE/TAG/TAG-result.json, and TAG-linklog.json for the server's)
--write puts runs.md and compare.md into OUTBASE."""
import json
import os
import sys

base = sys.argv[1]
write = '--write' in sys.argv


def fmt_t(ms):
    if ms is None:
        return '-'
    s = ms / 1000
    return '%.1f s' % s if s < 90 else '%.1f min' % (s / 60)


def rate_of(log):
    """bits per second from the first chunk to the last (the first chunk's bytes open the span)"""
    if len(log) < 2:
        return None
    span = log[-1][0] - log[0][0]
    return sum(x[1] for x in log[1:]) * 8 / span if span > 0 else None


def worst_window(log, bps, width=1.0):
    """the largest departure from the set rate over any one second in which the link was busy throughout"""
    if len(log) < 3 or not bps:
        return None
    ts = [x[0] for x in log]
    worst = 0.0
    n = len(log)
    j = 0
    acc = 0
    i = 0
    k = 0
    # windows starting at each half second
    t = ts[0]
    end = ts[-1] - width
    while t <= end:
        while i < n and ts[i] < t:
            i += 1
        k = max(k, i)
        acc = 0
        m = i
        busy = True
        prev = t
        while m < n and ts[m] < t + width:
            if ts[m] - prev > 0.3:
                busy = False
                break
            prev = ts[m]
            acc += log[m][1]
            m += 1
        if busy and t + width - prev <= 0.3 and m > i:
            worst = max(worst, abs(acc * 8 / width / bps - 1))
        t += 0.5
    return worst


rows = []
for tag in sorted(os.listdir(base)):
    p = os.path.join(base, tag, tag + '-result.json')
    if not os.path.isfile(p):
        if os.path.isdir(os.path.join(base, tag)):
            rows.append({'tag': tag, 'missing': True})
        continue
    r = json.load(open(p))
    s = r['settings']
    bps = s['bitsPerSecond']
    pics = [c for c in r['comps'] if c['kind'] == 'picture']
    tex = r['textures']
    link = s.get('link', 'page')
    if link == 'server':
        lp = os.path.join(base, tag, tag + '-linklog.json')
        log = json.load(open(lp))['log'] if os.path.isfile(lp) else []
    else:
        log = r.get('linkLog', [])
    lr = rate_of(log)
    pr = r.get('measuredWhole')
    rows.append({
        'tag': tag, 'player': r['player'], 'bps': bps, 'conns': s['conns'], 'limit': s['limit'], 'link': link,
        'first': r['firstFrame'], 'firstPic': min((c['tEnd'] for c in pics if c['tEnd']), default=None), 'allIn': r['allIn'],
        # each picture's time from the moment the pictures' downloads began (the page's own start varies from run to run)
        'pics': {c['name']: c['tEnd'] - min(x['tStart'] for x in pics if x['tStart'] is not None) for c in pics if c['tEnd'] is not None},
        'picOrder': [c['name'].replace(' picture', '') for c in sorted((c for c in pics if c['tEnd'] is not None), key=lambda c: c['tEnd'])],
        'order': [c['name'] for c in sorted((c for c in r['comps'] if c['tEnd'] is not None), key=lambda c: c['tEnd'])],
        'linkErr': None if not lr or not bps else lr / bps - 1, 'pageErr': None if not pr or not bps else pr / bps - 1,
        'worst': worst_window(log, bps), 'chunks': len(log),
        'afterStop': sum(t['subsAfterStop'] + t['wasmAfterStop'] for t in tex), 'afterPic': sum(t['subsAfterPicture'] for t in tex),
        'before': sum(1 for t in tex if t['times']['procFirst'] is not None and t['times']['picArrived'] is not None and t['times']['procFirst'] < t['times']['picArrived']),
        'ntex': len(tex), 'off': r['playerOff'] is not None, 'longest': r.get('longest'), 'hidden': r.get('hiddenSeconds'),
        'messages': r.get('messageTexts', []), 'wasmBytes': (r.get('wasm') or {}).get('bytes'),
    })

pc = lambda x: '-' if x is None else '%+.2f %%' % (100 * x)
out = ['| run | player | link | set rate | connections | limit | first frame from procedures | first picture in | every picture in | link\'s own record against set | page\'s reading against set | worst 1 s window | drawn from procedure before its picture | work after a picture arrived (in flight) | work after a texture stopped | player shut down |',
       '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for x in rows:
    if x.get('missing'):
        out.append('| %s | no record: the run did not reach its end |' % x['tag'])
        continue
    out.append('| %s | %s | %s | %.1f kbit/s | %d | %s | %s | %s | %s | %s | %s | %s | %d of %d | %d | %d | %s |' % (
        x['tag'], x['player'], x['link'], x['bps'] / 1000, x['conns'], x['limit'], fmt_t(x['first']), fmt_t(x['firstPic']), fmt_t(x['allIn']),
        pc(x['linkErr']), pc(x['pageErr']), '-' if x['worst'] is None else '%.1f %%' % (100 * x['worst']), x['before'], x['ntex'], x['afterPic'], x['afterStop'], 'yes' if x['off'] else 'no'))
runs_md = '\n'.join(out)

# each cell's two runs side by side
cells = {}
for x in rows:
    if x.get('missing'):
        continue
    key = (x['player'], x['bps'], x['conns'], x['limit'])
    cells.setdefault(key, {})[x['link']] = x
cmp_ = ['| player | set rate | connections | limit | first frame: page link, server link | first picture in: page, server | every picture in: page, server | a picture\'s time from the pictures\' start, largest difference | order the pictures came in | link\'s own record against set: page, server | page\'s reading against set: page, server | worst 1 s window: page, server | work after a texture stopped: page, server |',
        '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for key in sorted(cells, key=lambda k: (k[0], k[1], k[3], k[2])):
    c = cells[key]
    a, b = c.get('page'), c.get('server')
    if not a or not b:
        cmp_.append('| %s | %.1f kbit/s | %d | %s | only the %s run has a record |' % (key[0], key[1] / 1000, key[2], key[3], 'page' if a else 'server'))
        continue
    diffs = [(abs(a['pics'][n] - b['pics'][n]), n, a['pics'][n], b['pics'][n]) for n in a['pics'] if n in b['pics'] and a['pics'][n] and b['pics'][n]]
    d = max(diffs) if diffs else None
    # the order the pictures came in; where it differs, how close in time the swapped ones were
    if a['picOrder'] == b['picOrder']:
        order = 'the same'
    else:
        swapped = [n for i, n in enumerate(a['picOrder']) if b['picOrder'][i] != n]
        gap = max(abs(a['pics'][n + ' picture'] - b['pics'][n + ' picture']) for n in swapped) / 1000
        order = 'page: %s; server: %s (those that changed places ended within %.1f s of their time in the other run)' % (' > '.join(a['picOrder']), ' > '.join(b['picOrder']), gap)
    cmp_.append('| %s | %.1f kbit/s | %d | %s | %s, %s | %s, %s | %s, %s | %s | %s | %s, %s | %s, %s | %s, %s | %d, %d |' % (
        key[0], key[1] / 1000, key[2], key[3], fmt_t(a['first']), fmt_t(b['first']), fmt_t(a['firstPic']), fmt_t(b['firstPic']), fmt_t(a['allIn']), fmt_t(b['allIn']),
        '-' if not d else '%.1f s (%.2f %%), %s' % (d[0] / 1000, 100 * d[0] / max(d[2], d[3]), d[1].replace(' picture', '')), order,
        pc(a['linkErr']), pc(b['linkErr']), pc(a['pageErr']), pc(b['pageErr']),
        '-' if a['worst'] is None else '%.1f %%' % (100 * a['worst']), '-' if b['worst'] is None else '%.1f %%' % (100 * b['worst']), a['afterStop'], b['afterStop']))
compare_md = '\n'.join(cmp_)
print(runs_md)
print()
print(compare_md)
notes = [(x['tag'], m) for x in rows if not x.get('missing') for m in x['messages'] if 'sound' not in m.lower()]
if notes:
    print('\nmessages in the panel:')
    for tag, m in notes:
        print('- %s: %s' % (tag, m))
hid = [(x['tag'], x['hidden']) for x in rows if not x.get('missing') and x.get('hidden')]
if hid:
    print('\nhidden seconds:', hid)
if write:
    open(os.path.join(base, 'runs.md'), 'w').write(runs_md + '\n')
    open(os.path.join(base, 'compare.md'), 'w').write(compare_md + '\n')
