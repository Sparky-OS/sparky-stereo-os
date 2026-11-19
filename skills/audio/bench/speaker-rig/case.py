#!/usr/bin/python3 -I
"""The speaker page's proof rows, run inside a rig container as the user "rig" in the private PipeWire session (ORDER 23).

  case.py ROW [--ref]     rows: defaults level distance bass testsignal refusal stereo71
Each row drives the real SpeakerSetup type through harness.qml (apply, test), plays a known file with pw-cat, reads what the fake
device received and judges it against a prediction. It prints one JSON line {"row", "ok", "checks": [...]}, exit 0 when ok.
"""
import json, math, os, subprocess, sys, time
import numpy as np
sys.path.insert(0, '/src')
import sp

RATE = 48000
POS51 = ['FL', 'FR', 'FC', 'LFE', 'RL', 'RR']
POS71 = ['FL', 'FR', 'FC', 'LFE', 'RL', 'RR', 'SL', 'SR']
NODE51 = 'alsa_output.rig_51'
NODE71 = 'alsa_output.rig_71'
DEV51 = '/run/sa631/dev51.raw'
DEV71 = '/run/sa631/dev71.raw'
DEVST = '/run/sa631/devst.raw'
CARDS = {'51': (NODE51, POS51, DEV51), '71': (NODE71, POS71, DEV71)}
checks = []

def check(name, ok, **detail):
    checks.append({'name': name, 'ok': bool(ok), **detail})

def sh(*a, **k):
    return subprocess.run(a, capture_output=True, text=True, **k)

def steps(lst):
    json.dump(lst, open('/tmp/steps-run.json', 'w'))
    r = sh('bash', '/src/qml-steps.sh', '/tmp/steps-run.json')
    out = []
    for line in r.stdout.splitlines():
        if line.startswith(('RESULT ', 'DUMP ', 'LEVELS ')):
            k, v = line.split(' ', 1)
            out.append((k, json.loads(v)))
        else:
            out.append(('LOG', line))
    return out

def settle(limit=12.0):
    """Wait until the fake devices' files stop growing: the device is paced at the wall clock, so on a busy machine its file lags pw-cat."""
    paths = ['/run/sa631/dev51.raw', '/run/sa631/dev71.raw', '/run/sa631/devst.raw']
    last = None
    t0 = time.time()
    stable = 0
    while time.time() - t0 < limit:
        cur = [os.path.getsize(p) if os.path.exists(p) else 0 for p in paths]
        stable = stable + 1 if cur == last else 0
        if stable >= 6:
            return
        last = cur
        time.sleep(0.15)

def play_f32(x, target=None, channels=6, pos=POS51):
    mark()
    open('/tmp/in.f32', 'wb').write(x.astype('<f4').tobytes())
    cmd = ['pw-cat', '--playback', '--raw', '--rate', str(RATE), '--channels', str(channels), '--channel-map', ','.join(pos), '--format', 'f32', '--latency', '20ms']
    if target:
        cmd += ['--target', target]
    r = sh(*cmd, '/tmp/in.f32')
    settle()
    return r

def play_s32(a, target=None):
    mark()
    open('/tmp/in.s32', 'wb').write(a.astype('<i4').tobytes())
    cmd = ['pw-cat', '--playback', '--raw', '--rate', str(RATE), '--channels', '6', '--channel-map', ','.join(POS51), '--format', 's32', '--latency', '20ms']
    if target:
        cmd += ['--target', target]
    r = sh(*cmd, '/tmp/in.s32')
    settle()
    return r

MARK = {}

def mark():
    """Remember how much each fake device's file holds before a play: a device that stays open between two plays keeps appending to its file,
    and one that is closed and opened again starts the file anew (and rewrites its .params); only what a play added is measured."""
    for path in (DEV51, DEV71, DEVST):
        if os.path.exists(path) and os.path.exists(path + '.params'):
            MARK[path] = (os.path.getsize(path), os.stat(path + '.params').st_mtime_ns)
        else:
            MARK.pop(path, None)

def device(path=DEV51):
    a, p = sp.read_device(path)
    if path in MARK and os.path.exists(path + '.params'):
        size, mt = MARK[path]
        if os.stat(path + '.params').st_mtime_ns == mt and os.path.getsize(path) >= size:
            frame = p['channels'] * (4 if p['format'] == 'S32_LE' else 2)
            a = a[size // frame:]
    return a, p

def rms_db(v):
    return sp.db(float(np.sqrt(np.mean(np.square(v))))) if len(v) else -999.0

def noise6(seconds=2.0, amp=0.1):
    n = int(RATE * seconds)
    x = np.zeros((n, 6), dtype=np.float32)
    for c in range(6):
        x[:, c] = (amp * np.random.default_rng(100 + c).standard_normal(n)).astype(np.float32)
    return x

def start_of(col):
    nz = np.nonzero(np.abs(col) > 1e-9)[0]
    return int(nz[0]) if len(nz) else None

def apply_state(state, node=NODE51, system=False, make_default=True):
    return steps([{'op': 'apply', 'node': node, 'state': state, 'system': system, 'makeDefault': make_default}])

def dev_state(**kw):
    d = {'positions': POS51}
    d.update(kw)
    return {'devices': {NODE51: d}}

def files_in_user_config():
    base = os.path.expanduser('~/.config/pipewire/pipewire.conf.d')
    return sorted(os.listdir(base)) if os.path.isdir(base) else []


def pid_of(name):
    r = sh('pidof', name)
    return r.stdout.strip()

def set_levels(node, levels_db, raised=False):
    """The page's own path: SpeakerLevels sets the device's channel volumes (the values Show Channels shows)."""
    st = [{'op': 'levels', 'node': node, 'name': 'bind'}, {'op': 'wait', 'ms': 1800}]
    for ch, db in levels_db.items():
        st.append({'op': 'setlevel', 'node': node, 'channel': ch, 'db': db, 'raised': raised})
    st += [{'op': 'wait', 'ms': 800}, {'op': 'levels', 'node': node, 'name': 'after'}]
    return [v for k, v in steps(st) if k == 'LEVELS']

def sink_volumes_db(node):
    """The other view: what pactl (and so Show Channels) reads for each channel, in dB."""
    r = sh('pactl', '-f', 'json', 'list', 'sinks')
    for s_ in json.loads(r.stdout):
        if s_['name'] == node:
            return [float(v['db'].split()[0]) if v['db'] != '-inf dB' else -999.0 for v in s_['volume'].values()]
    return None

def noise_n(n_ch, seconds=2.0, amp=0.1):
    n = int(RATE * seconds)
    x = np.zeros((n, n_ch), dtype=np.float32)
    for c in range(n_ch):
        x[:, c] = (amp * np.random.default_rng(100 + c).standard_normal(n)).astype(np.float32)
    return x

def play_to(x, pos, target=None):
    return play_f32(x, target=target, channels=len(pos), pos=pos)

def row_defaults():
    # every speaker at its defaults: no file, no sink, no filter, and the signal is bit exact on 5.1
    check('no drop-in written', files_in_user_config() == [])
    names = sh('pw-cli', 'ls', 'Node').stdout
    check('no setup sink in the graph', 'speaker_setup' not in names)
    n = int(RATE * 2)
    a = np.zeros((n, 6), dtype=np.int64)
    for c in range(6):
        a[:, c] = (np.random.default_rng(7 + c).integers(-2 ** 23, 2 ** 23 - 1, n) * 256)
        a[0, c] = 256 * (c + 1)
    play_s32(a)
    d, p = device()
    check('device opened with 6 channels', p['channels'] == 6, params=p)
    got = (d * 2147483648.0).round().astype(np.int64)
    for c, ch in enumerate(POS51):
        s = start_of(d[:, c])
        same = s is not None and len(got) >= s + n and np.array_equal(got[s:s + n, c], a[:, c])
        mism = int((got[s:s + n, c] != a[:n, c]).sum()) if s is not None and len(got) >= s + n else -1
        check('bit exact on ' + ch, same, start=s, mismatches=mism, first_got=[int(v) for v in got[s:s + 3, c]] if s is not None else None, first_want=[int(v) for v in a[:3, c]], at=[int(i) for i in np.nonzero(got[s:s + n, c] != a[:n, c])[0][:3]] if s is not None and mism > 0 else None)
    meta = sh('pw-metadata', '-n', 'settings').stdout
    check('graph rate not forced', "key:'clock.force-rate' value:'0'" in meta)

def row_level(card):
    # a level is the device's channel volume: live, no file, no setup sink, no restart; the other views follow
    node, pos, devpath = CARDS[card]
    npos = len(pos)
    x = noise_n(npos)
    play_to(x, pos, node)
    base, _ = device(devpath)
    start0 = [start_of(base[:, c]) for c in range(npos)]
    pw_before = (pid_of('pipewire'), pid_of('wireplumber'))
    levels = {0: -6.0, 2: -3.5, npos - 1: -12.0}
    if npos == 8:
        levels[6] = -9.0
    r = set_levels(node, levels)
    after = [v for v in r if v['name'] == 'after'][0]
    check('the page sees the sink and reads its channels', after['available'] and len(after['levels']) == npos, levels=[round(v, 2) for v in after['levels']])
    for ch, db in levels.items():
        check(f'the page reads back {db} dB on {pos[ch]}', abs(after['levels'][ch] - db) < 0.01, read=round(after['levels'][ch], 3))
    seen = sink_volumes_db(node)
    check('Show Channels (the server) holds the same values', seen is not None and all(abs(seen[c] - levels.get(c, 0.0)) < 0.06 for c in range(npos)), seen=seen)
    check('no file, no setup sink', files_in_user_config() == [] and 'speaker_setup' not in sh('pw-cli', 'ls', 'Node').stdout)
    check('no restart: the same PipeWire and WirePlumber', (pid_of('pipewire'), pid_of('wireplumber')) == pw_before)
    play_to(x, pos, node)
    got, _ = device(devpath)
    for c, ch in enumerate(pos):
        a = base[start0[c]:start0[c] + 90000, c]
        s_ = start_of(got[:, c])
        b = got[s_:s_ + 90000, c]
        delta = rms_db(b) - rms_db(a)
        want = levels.get(c, 0.0)
        check(f'{ch} measures {want} dB', abs(delta - want) < 0.03, measured=round(delta, 4))
    # the other direction: Show Channels' own change (pactl) shows in the page at once
    sh('pactl', 'set-sink-volume', node, *(['0dB'] * npos))
    time.sleep(1.0)
    r = [v for k, v in steps([{'op': 'levels', 'node': node, 'name': 'reset'}]) if k == 'LEVELS'][0]
    check('a change made as Show Channels makes it shows in the page', all(abs(v) < 0.05 for v in r['levels']), levels=[round(v, 2) for v in r['levels']])
    # above 0 dB when the Sound page allows it
    r = set_levels(node, {1: 6.0}, raised=True)
    after = [v for v in r if v['name'] == 'after'][0]
    check('with Raise maximum volume on, +6 dB is kept', abs(after['levels'][1] - 6.0) < 0.01, read=round(after['levels'][1], 3))
    r = set_levels(node, {1: 6.0}, raised=False)
    after = [v for v in r if v['name'] == 'after'][0]
    check('with it off, +6 dB is cut to 0 dB', abs(after['levels'][1]) < 0.01, read=round(after['levels'][1], 3))

def row_distance(card):
    node, pos, devpath = CARDS[card]
    npos = len(pos)
    n = RATE * 2
    x = np.zeros((n, npos), dtype=np.float32)
    for c in range(npos):
        x[1000, c] = 0.5
    base_d = {'FL': 2.0, 'FR': 3.0, 'FC': 3.5, 'LFE': 2.5, 'RL': 4.0, 'RR': 5.0, 'SL': 3.2, 'SR': 3.8}
    dist = {p: base_d[p] for p in pos}
    far = max(dist.values())
    r = apply_state({'devices': {node: {'positions': pos, 'distances': dist}}}, node=node)
    res = [v for k, v in r if k == 'RESULT']
    check('the page applied the distances', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    play_to(x, pos, 'speaker_setup.' + node)
    got, _ = device(devpath)
    first = {ch: start_of(got[:, c]) for c, ch in enumerate(pos)}
    far_ch = [p for p in pos if dist[p] == far][0]
    ref = first[far_ch]
    check(f'the farthest speaker ({far_ch}) is not delayed', ref is not None)
    for ch, d in dist.items():
        want = (far - d) / 343.0 * RATE
        meas = first[ch] - ref
        check(f'{ch} at {d} m is {want:.1f} samples before the farthest', abs(meas - round(want)) <= 1, measured=meas, predicted=round(want, 2))
    for c, ch in enumerate(pos):
        check(f'{ch} carries one impulse', int((np.abs(got[:, c]) > 1e-9).sum()) == 1)
    check('no level node in the filter', 'linear' not in open(os.path.expanduser('~/.config/pipewire/pipewire.conf.d/50-speaker-page.conf')).read())

def tone_levels_n(pos, devpath, freq, ch_in, target, amp=0.25, seconds=2.0):
    n = int(RATE * seconds)
    x = np.zeros((n, len(pos)), dtype=np.float32)
    x[:, ch_in] = (amp * np.sin(2 * math.pi * freq * np.arange(n) / RATE)).astype(np.float32)
    play_to(x, pos, target)
    got, _ = device(devpath)
    out = {}
    for c, ch in enumerate(pos):
        s_ = start_of(got[:, c])
        seg = got[s_ + 12000:s_ + 12000 + 48000, c] if s_ is not None else np.zeros(0)
        out[ch] = rms_db(seg) if len(seg) else -999.0
    return out, sp.db(amp / math.sqrt(2))

def row_bass(card):
    node, pos, devpath = CARDS[card]
    small = [p for p in pos if p != 'LFE']
    fc = 80 if card == '51' else 100
    r = apply_state({'devices': {node: {'positions': pos, 'small': small, 'crossover': fc}}}, node=node)
    res = [v for k, v in r if k == 'RESULT']
    check(f'the page applied the crossover ({len(small)} small speakers, {fc} Hz)', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    lp = lambda f: 1 / (1 + (f / fc) ** 4)
    hp = lambda f: (f / fc) ** 4 / (1 + (f / fc) ** 4)
    for src in ([0] if card == '51' else [0, 6]):
        for f in (40, 200, 1000):
            lv, ref = tone_levels_n(pos, devpath, f, src, 'speaker_setup.' + node)
            want_lfe = ref + 20 * math.log10(lp(f))
            want_src = ref + 20 * math.log10(hp(f))
            check(f'{f} Hz on {pos[src]} reaches the subwoofer channel at the LR4 low pass', abs(lv['LFE'] - want_lfe) < 0.4 if f < 1000 else lv['LFE'] < ref - 70,
                  measured=round(lv['LFE'], 2), predicted=round(want_lfe, 2), input_db=round(ref, 2))
            check(f'{f} Hz on {pos[src]} leaves {pos[src]} at the LR4 high pass', abs(lv[pos[src]] - want_src) < 0.4, measured=round(lv[pos[src]], 2), predicted=round(want_src, 2))
            others = [lv[c] for c in pos if c not in (pos[src], 'LFE')]
            check(f'{f} Hz on {pos[src]} puts nothing on the other speakers', max(others) < -150, measured=[round(v, 1) for v in others])
    lv, ref = tone_levels_n(pos, devpath, 40, pos.index('LFE'), 'speaker_setup.' + node)
    check('the subwoofer channel keeps its own content', abs(lv['LFE'] - ref) < 0.1, measured=round(lv['LFE'], 2), input_db=round(ref, 2))
    r = apply_state({}, node=node)
    res = [v for k, v in r if k == 'RESULT']
    check('back to defaults applied and the file is gone', bool(res) and res[0]['ok'] and files_in_user_config() == [])
    lv, ref = tone_levels_n(pos, devpath, 40, 0, node)
    check('with every speaker large 40 Hz stays on FL and the subwoofer gets nothing', abs(lv['FL'] - ref) < 0.05 and lv['LFE'] < -150, measured={k: round(v, 1) for k, v in lv.items()})

def burst_report(d, pos):
    out = []
    for c, name in enumerate(pos):
        col = d[:, c]
        nz = np.nonzero(np.abs(col) > 1e-9)[0]
        out.append((name, rms_db(col[nz[0]:nz[-1] + 1]) if len(nz) else None, int(len(nz))))
    return out

def row_testsignal(card):
    node, pos, devpath = CARDS[card]
    npos = len(pos)
    seconds = 1
    st = [{'op': 'seconds', 'value': seconds}]
    for ch in pos:
        st += [{'op': 'test', 'node': node, 'position': ch}, {'op': 'wait', 'ms': 2200}]
        mark()
        steps(st)
        st = []
        d, p = device(devpath)
        chosen = [o for o in burst_report(d, pos) if o[2] > 0]
        check(f'test of {ch}: only {ch} sounds', [o[0] for o in chosen] == [ch], channels=[o[0] for o in chosen])
        if chosen:
            check(f'test of {ch}: the burst is at -20 dBFS', abs(chosen[0][1] + 20.0) < 0.05, measured=round(chosen[0][1], 3), frames=chosen[0][2])
            check(f'test of {ch}: the burst is {seconds} s long', abs(chosen[0][2] - seconds * RATE) <= 2, frames=chosen[0][2])
    mark()
    steps([{'op': 'test', 'node': node, 'position': 'all'}, {'op': 'wait', 'ms': 1500 * npos + 3000}])
    d, p = device(devpath)
    starts = []
    for c, name in enumerate(pos):
        s_ = start_of(d[:, c])
        starts.append(s_)
        seg = d[s_:s_ + RATE, c]
        check(f'sequence: {name} has its burst at -20 dBFS', abs(rms_db(seg) + 20.0) < 0.05, measured=round(rms_db(seg), 3))
    check('sequence: one after the other, 1.5 s apart', all(abs((starts[i + 1] - starts[i]) - 1.5 * RATE) <= RATE // 100 for i in range(npos - 1)), starts=starts)
    # a speaker at -6 dB (its channel volume) measures -26 dBFS: the level holds through channel volumes
    set_levels(node, {2: -6.0})
    mark()
    steps([{'op': 'test', 'node': node, 'position': pos[2]}, {'op': 'wait', 'ms': 2200}])
    d, p = device(devpath)
    col = d[:, 2]
    nz = np.nonzero(np.abs(col) > 1e-9)[0]
    check(f'with {pos[2]} at -6 dB (its channel volume) its test measures -26 dBFS', len(nz) > 0 and abs(rms_db(col[nz[0]:nz[-1] + 1]) + 26.0) < 0.05,
          measured=round(rms_db(col[nz[0]:nz[-1] + 1]), 3) if len(nz) else None)

def row_refusal():
    before = files_in_user_config()
    default_before = [v for k, v in steps([{'op': 'dump', 'name': 'b'}]) if k == 'DUMP'][0]['defaultSink']
    check('the module is made unreadable by the harness (root)', os.path.exists('/tmp/module-hidden'))
    r = apply_state({'devices': {NODE51: {'positions': POS51, 'small': ['FL']}}})
    res = [v for k, v in r if k == 'RESULT']
    check('the page refuses the change', bool(res) and res[0]['ok'] is False, message=res[0]['message'] if res else None)
    check('and says why and that the earlier settings stay', bool(res) and 'The change was not kept.' in res[0]['message'].get('text', '') and 'earlier settings stay' in res[0]['message'].get('text', ''))
    check('the file is gone again', files_in_user_config() == before)
    d = [v for k, v in steps([{'op': 'dump', 'name': 'a'}]) if k == 'DUMP'][0]
    check('the default output is as it was', d['defaultSink'] == default_before, before=default_before, after=d['defaultSink'])
    check('no setup sink exists', not any(x['setupActive'] for x in d['devices']))
    r = apply_state({'devices': {'alsa_output.nothing_here': {'positions': POS51, 'small': ['FL']}}}, node='alsa_output.nothing_here')
    res = [v for k, v in r if k == 'RESULT']
    check('a device that is not there is refused before anything is written', bool(res) and res[0]['ok'] is False and 'no longer connected' in res[0]['message'].get('text', ''), message=res[0]['message'] if res else None)
    check('and nothing was written', files_in_user_config() == before)
    r = apply_state({'devices': {NODE51: {'positions': POS51, 'distances': {p: 99 for p in POS51} | {'FL': 1}}}})
    res = [v for k, v in r if k == 'RESULT']
    check('a value outside the range is refused and nothing written', bool(res) and res[0]['ok'] is False and files_in_user_config() == before, message=res[0]['message'] if res else None)

def row_cards():
    d = [v for k, v in steps([{'op': 'dump', 'name': 's'}]) if k == 'DUMP'][0]
    by = {x['name']: x for x in d['devices']}
    check('the 5.1 card is offered', by[NODE51]['eligible'] and by[NODE51]['channels'] == 6)
    check('the 7.1 card is offered', by[NODE71]['eligible'] and by[NODE71]['channels'] == 8)
    st = by['alsa_output.rig_st']
    check('the stereo card is not offered, with its sentence', (not st['eligible']) and st['reason'] == 'Speaker Setup is for devices whose current profile has more than two channels. The profile of this device has 2.', reason=st['reason'])
    r = apply_state({'devices': {NODE71: {'positions': POS71, 'label': '\u626c\u58f0\u5668\u8bbe\u7f6e\uff1arig 71', 'small': ['FL', 'FR', 'SL', 'SR'], 'crossover': 100,
                                          'distances': {p: (3.0 if p != 'RL' else 2.0) for p in POS71}}}}, node=NODE71)
    res = [v for k, v in r if k == 'RESULT']
    check('a 7.1 setup with a Chinese label, delays and bass management is applied', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)

def row_everyaccount():
    etc = '/etc/pipewire/pipewire.conf.d/50-speaker-page.conf'
    check('nothing in /etc to begin with', not os.path.exists(etc))
    r = apply_state(dev_state(distances={p: 3.0 for p in POS51} | {'RL': 2.0}), system=True)
    res = [v for k, v in r if k == 'RESULT']
    check('the page applied the setup for every account', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    check('the file is in /etc, written by root, with the mark line', os.path.exists(etc) and os.stat(etc).st_uid == 0 and open(etc).readline().startswith('# Written by the Speaker Setup page'))
    check('this account has no file of its own', files_in_user_config() == [])
    check('the setup sink is in the graph', 'speaker_setup.' + NODE51 in sh('pw-cli', 'ls', 'Node').stdout)
    r = apply_state({}, system=True)
    res = [v for k, v in r if k == 'RESULT']
    check('back to defaults for every account applied', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    check('and the file is gone', not os.path.exists(etc))

def row_everyaccount_refused():
    etc = '/etc/pipewire/pipewire.conf.d/50-speaker-page.conf'
    r = apply_state(dev_state(distances={p: 3.0 for p in POS51} | {'RL': 2.0}), system=True)
    res = [v for k, v in r if k == 'RESULT']
    check('polkit refuses and the page says so', bool(res) and res[0]['ok'] is False and 'did not allow the change for every account' in res[0]['message'].get('text', ''), message=res[0]['message'] if res else None)
    check('nothing was written', not os.path.exists(etc) and files_in_user_config() == [])
    check('and no setup sink exists', 'speaker_setup' not in sh('pw-cli', 'ls', 'Node').stdout)

def links_of(prefix):
    out = sh('pw-link', '-l').stdout.splitlines()
    res = []
    cur = None
    for l in out:
        if not l.startswith((' ', '\t')):
            cur = l.strip()
        elif '|->' in l and cur and cur.startswith(prefix):
            res.append(l.split('|->')[1].strip())
    return res

def sinks_named(text):
    return has_node(text)

def has_node(name):
    return ('node.name = "%s"' % name) in sh('pw-cli', 'ls', 'Node').stdout

def dist_state(node, pos):
    return {'devices': {node: {'positions': pos, 'distances': {p: (3.0 if p != 'FL' else 2.0) for p in pos}}}}

def impulse_offset(devpath, pos, target=None):
    n = RATE * 2
    x = np.zeros((n, len(pos)), dtype=np.float32)
    for c in range(len(pos)):
        x[1000, c] = 0.5
    play_to(x, pos, target)
    got, _ = device(devpath)
    first = {ch: start_of(got[:, c]) for c, ch in enumerate(pos)}
    return first

def node_id_of(name):
    for o in json.loads(sh('pw-dump').stdout):
        if o.get('info', {}).get('props', {}).get('node.name') == name:
            return o['id']
    return -1

def row_leave():
    # the device leaves while a setup exists: the setup's output goes to no other device and says so; the device comes back
    r = apply_state(dist_state(NODE51, POS51))
    res = [v for k, v in r if k == 'RESULT']
    check('the setup is applied with the device there', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    pw_before = (pid_of('pipewire'), pid_of('wireplumber'))
    f = impulse_offset(DEV51, POS51)
    check('with the device there FL, 1 m nearer, is 2.9 ms (140 samples) later than the others', abs((f['FL'] - f['RR']) - round(1.0 / 343.0 * RATE)) <= 1, offset=f['FL'] - f['RR'])
    node_id = node_id_of(NODE51)
    sh('pw-cli', 'destroy', str(node_id))
    time.sleep(4)
    nodes = sh('pw-cli', 'ls', 'Node').stdout
    check('the device is gone from the graph', not has_node('alsa_output.rig_51'))
    check('the setup sink and its output stay (the output waits)', sinks_named('speaker_setup.alsa_output.rig_51') and sinks_named('speaker_setup_out.alsa_output.rig_51'))
    out_links = links_of('speaker_setup_out.alsa_output.rig_51')
    check('the setup output is linked to no device', out_links == [], links=out_links)
    # sound played into the setup goes nowhere else
    x = noise_n(6)
    play_to(x, POS51, 'speaker_setup.alsa_output.rig_51')
    time.sleep(1)
    other_files = [p for p in (DEV71, DEVST) if os.path.exists(p) and os.path.getsize(p) > 0 and np.any(np.fromfile(p, dtype='<i4')[:200000] != 0)]
    check('nothing plays into another output (the 7.1 and stereo cards received no sound)', other_files == [], files=other_files)
    d = [v for k, v in steps([{'op': 'dump', 'name': 'gone'}]) if k == 'DUMP'][0]
    by = {x_['name']: x_ for x_ in d['devices']}
    check('the page no longer lists the device (its page says it is not connected)', NODE51 not in by)
    sink = by.get('speaker_setup.alsa_output.rig_51', {})
    check('the setup sink row says its device is not connected', sink.get('deviceConnected') is False and 'is not connected' in sink.get('reason', ''), reason=sink.get('reason'))
    r = apply_state(dist_state(NODE51, POS51))
    res = [v for k, v in r if k == 'RESULT']
    check('an Apply for the missing device is refused with "no longer connected"', bool(res) and res[0]['ok'] is False and 'no longer connected' in res[0]['message'].get('text', ''))
    # it comes back
    sh('pw-cli', 'create-node', 'adapter', '{ factory.name=api.alsa.pcm.sink node.name=alsa_output.rig_51 node.nick=rig_51 node.description=rig_51 media.class=Audio/Sink device.api=alsa api.alsa.path=sa_51 audio.channels=6 audio.position=[ FL FR FC LFE RL RR ] priority.session=1000 session.suspend-timeout-seconds=0 object.linger=true }')
    time.sleep(5)
    check('the device is back', has_node('alsa_output.rig_51'))
    out_links = links_of('speaker_setup_out.alsa_output.rig_51')
    check('the setup output is linked to the device again, without anyone restarting', any('alsa_output.rig_51' in l for l in out_links), links=out_links)
    check('no restart happened', (pid_of('pipewire'), pid_of('wireplumber')) == pw_before)
    f = impulse_offset(DEV51, POS51, 'speaker_setup.alsa_output.rig_51')
    check('the delay is applied again through the returned device', abs((f['FL'] - f['RR']) - round(1.0 / 343.0 * RATE)) <= 1, offset=f['FL'] - f['RR'])
    d = [v for k, v in steps([{'op': 'dump', 'name': 'back'}]) if k == 'DUMP'][0]
    by = {x_['name']: x_ for x_ in d['devices']}
    check('the page lists the device and its setup again', by.get(NODE51, {}).get('setupActive') is True and by.get('speaker_setup.' + NODE51, {}).get('deviceConnected') is True)

def row_late():
    # a start where the device appears after the filter: PipeWire loads the module, the card shows six seconds later
    r = apply_state(dist_state(NODE51, POS51))
    res = [v for k, v in r if k == 'RESULT']
    check('the setup is applied', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    sh('systemctl', '--user', 'restart', 'wireplumber.service', 'pipewire.service')
    time.sleep(2.5)
    nodes = sh('pw-cli', 'ls', 'Node').stdout
    check('two seconds after the start the card is not there yet', not has_node('alsa_output.rig_51'))
    check('and the setup sink exists already, waiting', sinks_named('speaker_setup.alsa_output.rig_51'))
    time.sleep(9)
    check('later the card appears', has_node('alsa_output.rig_51'))
    out_links = links_of('speaker_setup_out.alsa_output.rig_51')
    check('the setup output is linked to the card that came late', any('alsa_output.rig_51' in l for l in out_links), links=out_links)
    f = impulse_offset(DEV51, POS51, 'speaker_setup.alsa_output.rig_51')
    check('and the delay is applied', abs((f['FL'] - f['RR']) - round(1.0 / 343.0 * RATE)) <= 1, offset=f['FL'] - f['RR'])

ROWS = {'defaults': row_defaults, 'level51': lambda: row_level('51'), 'level71': lambda: row_level('71'), 'distance51': lambda: row_distance('51'),
        'distance71': lambda: row_distance('71'), 'bass51': lambda: row_bass('51'), 'bass71': lambda: row_bass('71'),
        'testsignal51': lambda: row_testsignal('51'), 'testsignal71': lambda: row_testsignal('71'), 'refusal': row_refusal, 'cards': row_cards,
        'everyaccount': row_everyaccount, 'everyaccount-refused': row_everyaccount_refused, 'leave': row_leave, 'late': row_late}

if __name__ == '__main__':
    row = sys.argv[1]
    try:
        ROWS[row]()
    except Exception as e:  # a row that could not run is a failed row
        check('the row ran', False, error=repr(e))
    ok = all(c['ok'] for c in checks)
    print(json.dumps({'row': row, 'ok': ok, 'checks': checks}))
    sys.exit(0 if ok else 1)
