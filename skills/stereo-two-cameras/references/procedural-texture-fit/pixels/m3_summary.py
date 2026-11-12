#!/usr/bin/env python3
"""The milestone 3 runs in one table (ORDER 508): m3_summary.py OUTBASE [OUT.md]
For each run folder OUTBASE/TAG with TAG-result.json and TAG-linklog.json: the player, the set rate, the number of
connections, the time to the first frame drawn from the procedures, when every picture was in, the rate the page
measured over the whole transfer and the rate the server's own record gives (first chunk to last), each against the
set rate, the worst one-second window of the server's record against the set rate (whole seconds inside the
transfer), the longest GPU submission (or processor piece), and the work done for a texture after it stopped."""
import glob, json, os, sys

base = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else None
rows = []
for d in sorted(glob.glob(os.path.join(base, '*'))):
    tag = os.path.basename(d)
    rp, lp = os.path.join(d, tag + '-result.json'), os.path.join(d, tag + '-linklog.json')
    if tag.startswith(('strip-', 'twins-', 'ignore')):
        continue                     # pages of their own (the blend strips, the twins, the ignoring viewer)
    if not os.path.exists(rp):
        if os.path.isdir(d):
            rows.append('| %s | no record: stopped at its timeout before every texture had stopped (its screenshots and the page state are in its folder) |' % tag)
        continue
    r = json.load(open(rp))
    if 'settings' not in r:          # the ignoring viewer's record, not a tester run
        continue
    s = r['settings']
    bps = s['bitsPerSecond']
    srv = None
    worst = None
    if os.path.exists(lp):
        L = json.load(open(lp))['log']
        if len(L) > 2:
            t0, t1 = L[0][0], L[-1][0]
            srv = (sum(n for _, n, _ in L) - L[0][1]) * 8 / (t1 - t0) if t1 > t0 else None
            # whole one-second windows inside the transfer, from the first chunk on
            if bps and t1 - t0 >= 3:
                # bytes per whole second from the first chunk on, the first and the last second left out
                secs = int(t1 - t0)
                bins = [0] * (secs + 1)
                for t, n, _ in L:
                    k = int(t - t0)
                    if k <= secs:
                        bins[k] += n
                inner = bins[1:secs]
                worst = max(abs(by * 8 - bps) / bps for by in inner) if inner else None
    texs = r['textures']
    after = sum(x.get('subsAfterStop', 0) + x.get('wasmAfterStop', 0) for x in texs)
    inflight = sum(x.get('subsAfterPicture', 0) for x in texs)
    drawn = sum(1 for x in texs if x['times'].get('procFirst') is not None)
    lg = r.get('longest') or {}
    pr = lambda v: '-' if v is None else '%.2f %%' % (100 * (v - bps) / bps) if bps else '-'
    fmt = lambda ms: '-' if ms is None else ('%.1f s' % (ms / 1000) if ms < 600000 else '%.1f min' % (ms / 60000))
    arr = [x['times'].get('picArrived') for x in texs if x['times'].get('picArrived') is not None]
    rows.append('| %s | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %d of 7 | %d | %d | %s |' % (
        tag, r.get('player'), ('%.1f kbit/s' % (bps / 1000)) if bps else 'none', s['conns'], s['limit'],
        fmt(r.get('firstFrame')), fmt(min(arr)) if arr else '-', fmt(r.get('allIn')), pr(r.get('measuredWhole')), pr(srv),
        '-' if worst is None else '%.1f %%' % (100 * worst),
        (('%.2f ms GPU, %.0f ms submit to done' % (lg['gpuMs'], (r.get('longestWall') or lg)['ms'])) if lg.get('gpuMs') is not None else ('%.0f ms' % lg['ms'])) + (' (%s, %s)' % (lg.get('owner'), lg.get('piece'))) if lg else '-',
        drawn, inflight, after, 'yes' if r.get('playerOff') else ('no' if s.get('nostop') else 'NOT SETTLED')))
head = ['| run | player | set rate | connections | limit | first frame from procedures | first picture in | every picture in | page rate against set | server rate against set | worst 1 s window | longest GPU submission (or processor piece) | drawn from procedure before its picture | work after a picture arrived (in flight) | work after a texture stopped | player shut down |',
        '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
text = '\n'.join(head + rows) + '\n'
print(text)
if out:
    open(out, 'w').write(text)
