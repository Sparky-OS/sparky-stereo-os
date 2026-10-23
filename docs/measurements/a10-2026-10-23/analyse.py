import csv, sys, statistics as st, os
# Per case: KWin's own per-frame log for eDP-1 (and HDMI-A-1), inside the recorded window from marks.csv,
# plus the 1 Hz machine log. KWin timestamps are CLOCK_MONOTONIC ns; marks are /proc/uptime s (no suspend in the run).
d = sys.argv[1]
marks = {}
for name, t in csv.reader(open(os.path.join(d, 'marks.csv'))):
    marks[name] = float(t)
cases = [n for n in marks if not n.endswith('-end')]
def frames(out):
    p = os.path.join(d, f'kwin perf statistics {out}.csv')
    rows = list(csv.DictReader(open(p)))
    keys = ('target pageflip timestamp', 'pageflip timestamp', 'render start', 'render end', 'refresh duration')
    ok = []
    for r in rows:
        try:
            if all(r.get(k) not in (None, '') for k in keys) and int(r['render start']) > 0 and int(r['render end']) > 0:
                ok.append(r)
        except ValueError:
            pass
    return ok
F = {o: frames(o) for o in ('eDP-1', 'HDMI-A-1')}
sysrows = list(csv.DictReader(open(os.path.join(d, 'sys.csv'))))
def num(x):
    try: return float(x)
    except: return None
print(f"{'case':34} {'out':8} {'frames':>6} {'fps':>5} {'render med':>10} {'p95':>6} {'p99':>6} {'max':>6} {'late':>4} | cpu% gpu% cpu°C")
for c in cases:
    a, b = marks[c], marks.get(c + '-end')
    if b is None: continue
    s = [r for r in sysrows if a <= float(r['uptime']) <= b]
    cpu = st.mean(num(r['cpu_busy']) for r in s) if s else float('nan')
    gpu = st.mean(num(r['gpu_busy_card0']) for r in s if num(r['gpu_busy_card0']) is not None) if s else float('nan')
    tc = st.mean(num(r['cpu_temp']) for r in s if num(r['cpu_temp'])) / 1000 if s else float('nan')
    for o, rows in F.items():
        w = [r for r in rows if a * 1e9 <= int(r['pageflip timestamp']) <= b * 1e9]
        if len(w) < 10:
            print(f"{c:34} {o:8} {len(w):6} (idle output: too few frames)"); continue
        rt = [(int(r['render end']) - int(r['render start'])) / 1e6 for r in w]
        q = st.quantiles(rt, n=100)
        late = sum(1 for r in w if int(r['pageflip timestamp']) - int(r['target pageflip timestamp']) > int(r['refresh duration']) / 2)
        print(f"{c:34} {o:8} {len(w):6} {len(w)/(b-a):5.1f} {st.median(rt):10.3f} {q[94]:6.3f} {q[98]:6.3f} {max(rt):6.2f} {late:4} | {cpu:4.0f} {gpu:4.0f} {tc:5.1f}")
