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
NODE51 = 'alsa_output.rig_51'
DEV51 = '/run/sa631/dev51.raw'
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
        if line.startswith(('RESULT ', 'DUMP ')):
            k, v = line.split(' ', 1)
            out.append((k, json.loads(v)))
        else:
            out.append(('LOG', line))
    return out

def play_f32(x, target=None, channels=6, pos=POS51):
    open('/tmp/in.f32', 'wb').write(x.astype('<f4').tobytes())
    cmd = ['pw-cat', '--playback', '--raw', '--rate', str(RATE), '--channels', str(channels), '--channel-map', ','.join(pos), '--format', 'f32', '--latency', '20ms']
    if target:
        cmd += ['--target', target]
    r = sh(*cmd, '/tmp/in.f32')
    time.sleep(1.0)
    return r

def play_s32(a, target=None):
    open('/tmp/in.s32', 'wb').write(a.astype('<i4').tobytes())
    cmd = ['pw-cat', '--playback', '--raw', '--rate', str(RATE), '--channels', '6', '--channel-map', ','.join(POS51), '--format', 's32', '--latency', '20ms']
    if target:
        cmd += ['--target', target]
    r = sh(*cmd, '/tmp/in.s32')
    time.sleep(1.0)
    return r

def device(path=DEV51):
    return sp.read_device(path)

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

def row_defaults():
    # every speaker at its defaults: no file, no setup sink, and the signal is bit exact
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
        check('bit exact on ' + ch, same, start=s)
    meta = sh('pw-metadata', '-n', 'settings').stdout
    check('graph rate not forced', "key:'clock.force-rate' value:'0'" in meta)

def row_level():
    x = noise6()
    play_f32(x)
    base, _ = device()
    start0 = [start_of(base[:, c]) for c in range(6)]
    levels = {'FL': -6.0, 'FC': 3.5, 'RR': -12.0}
    r = apply_state(dev_state(levels=levels))
    res = [v for k, v in r if k == 'RESULT']
    check('the page applied the levels', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    play_f32(x)
    got, _ = device()
    for c, ch in enumerate(POS51):
        a = base[start0[c]:start0[c] + 90000, c]
        s = start_of(got[:, c])
        b = got[s:s + 90000, c]
        delta = rms_db(b) - rms_db(a)
        want = levels.get(ch, 0.0)
        check(f'{ch} changed by {want} dB', abs(delta - want) < 0.02, measured=round(delta, 4))

def row_distance():
    n = RATE * 2
    x = np.zeros((n, 6), dtype=np.float32)
    for c in range(6):
        x[1000, c] = 0.5
    dist = {'FL': 2.0, 'FR': 3.0, 'FC': 3.5, 'LFE': 2.5, 'RL': 4.0, 'RR': 5.0}
    r = apply_state(dev_state(distances=dist))
    res = [v for k, v in r if k == 'RESULT']
    check('the page applied the distances', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    play_f32(x)
    got, _ = device()
    pos = {ch: start_of(got[:, c]) for c, ch in enumerate(POS51)}
    ref = pos['RR']
    check('the farthest speaker is not delayed (RR first at 1000 + stream offset)', ref is not None)
    for ch, d in dist.items():
        want = (5.0 - d) / 343.0 * RATE
        meas = pos[ch] - ref
        check(f'{ch} at {d} m is {want:.1f} samples before the farthest', abs(meas - round(want)) <= 1, measured=meas, predicted=round(want, 2))
    # one impulse per channel, no more: nothing smeared
    for c, ch in enumerate(POS51):
        check(f'{ch} carries one impulse', int((np.abs(got[:, c]) > 1e-9).sum()) == 1)

def tone_levels(freq, ch_in, amp=0.25, seconds=2.0):
    n = int(RATE * seconds)
    x = np.zeros((n, 6), dtype=np.float32)
    x[:, ch_in] = (amp * np.sin(2 * math.pi * freq * np.arange(n) / RATE)).astype(np.float32)
    play_f32(x)
    got, _ = device()
    out = {}
    for c, ch in enumerate(POS51):
        s = start_of(got[:, c])
        seg = got[s + 12000:s + 12000 + 48000, c] if s is not None else np.zeros(0)
        out[ch] = rms_db(seg) if len(seg) else -999.0
    return out, sp.db(amp / math.sqrt(2))

def row_bass():
    small = ['FL', 'FR', 'FC', 'RL', 'RR']
    r = apply_state(dev_state(small=small, crossover=80))
    res = [v for k, v in r if k == 'RESULT']
    check('the page applied the crossover', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    lr4_lp = lambda f, fc: 1 / (1 + (f / fc) ** 4)
    lr4_hp = lambda f, fc: (f / fc) ** 4 / (1 + (f / fc) ** 4)
    for f in (40, 200, 1000):
        lv, ref = tone_levels(f, 0)
        want_lfe = ref + 20 * math.log10(lr4_lp(f, 80))
        want_fl = ref + 20 * math.log10(lr4_hp(f, 80))
        check(f'{f} Hz on FL reaches the subwoofer channel at the LR4 low pass', abs(lv['LFE'] - want_lfe) < 0.4 if f < 1000 else lv['LFE'] < ref - 70,
              measured=round(lv['LFE'], 2), predicted=round(want_lfe, 2), input_db=round(ref, 2))
        check(f'{f} Hz on FL leaves FL at the LR4 high pass', abs(lv['FL'] - want_fl) < 0.4, measured=round(lv['FL'], 2), predicted=round(want_fl, 2))
        others = [lv[c] for c in ('FR', 'FC', 'RL', 'RR')]
        check(f'{f} Hz on FL puts nothing on the other speakers', max(others) < -150, measured=[round(v, 1) for v in others])
    lv, ref = tone_levels(40, 3)
    check('the subwoofer channel keeps its own content (40 Hz on LFE arrives at its level)', abs(lv['LFE'] - ref) < 0.1, measured=round(lv['LFE'], 2), input_db=round(ref, 2))
    # every speaker large: no crossover, the subwoofer gets nothing from the others and the file is gone
    r = apply_state({})
    res = [v for k, v in r if k == 'RESULT']
    check('back to defaults applied', bool(res) and res[0]['ok'])
    check('and the file is gone', files_in_user_config() == [])
    lv, ref = tone_levels(40, 0)
    check('with every speaker large 40 Hz stays on FL and the subwoofer gets nothing', abs(lv['FL'] - ref) < 0.05 and lv['LFE'] < -150, measured={k: round(v, 1) for k, v in lv.items()})

def row_testsignal():
    seconds = 1
    pos_ok = {}
    st = [{'op': 'seconds', 'value': seconds}]
    for ch in POS51:
        st += [{'op': 'test', 'node': NODE51, 'position': ch}, {'op': 'wait', 'ms': 2200}]
        steps(st)
        st = []
        d, p = device()
        out = []
        for c, name in enumerate(POS51):
            col = d[:, c]
            nz = np.nonzero(np.abs(col) > 1e-9)[0]
            out.append((name, rms_db(col[nz[0]:nz[-1] + 1]) if len(nz) else None, int(len(nz))))
        chosen = [o for o in out if o[2] > 0]
        check(f'test of {ch}: only {ch} sounds', [o[0] for o in chosen] == [ch], channels=[o[0] for o in chosen])
        if chosen:
            check(f'test of {ch}: the burst is at -20 dBFS', abs(chosen[0][1] + 20.0) < 0.05, measured=round(chosen[0][1], 3), frames=chosen[0][2])
            check(f'test of {ch}: the burst is {seconds} s long', abs(chosen[0][2] - seconds * RATE) <= 2, frames=chosen[0][2])
    # the sequence: every speaker once, in the order of the channel map
    steps([{'op': 'test', 'node': NODE51, 'position': 'all'}, {'op': 'wait', 'ms': 11000}])
    d, p = device()
    starts = []
    for c, name in enumerate(POS51):
        s = start_of(d[:, c])
        starts.append(s)
        seg = d[s:s + RATE, c]
        check(f'sequence: {name} has its burst at -20 dBFS', abs(rms_db(seg) + 20.0) < 0.05, measured=round(rms_db(seg), 3))
    check('sequence: one after the other, 1.5 s apart (1 s of noise and 0.5 s of silence)', all(abs((starts[i + 1] - starts[i]) - 1.5 * RATE) <= RATE // 100 for i in range(5)), starts=starts)
    # through a setup the person's levels are heard: FC at -6 dB gives -26 dBFS
    r = apply_state(dev_state(levels={'FC': -6.0}))
    steps([{'op': 'test', 'node': NODE51, 'position': 'FC'}, {'op': 'wait', 'ms': 2200}])
    d, p = device()
    col = d[:, 2]
    nz = np.nonzero(np.abs(col) > 1e-9)[0]
    check('through the speaker setup the test of FC follows its level (-26 dBFS)', len(nz) > 0 and abs(rms_db(col[nz[0]:nz[-1] + 1]) + 26.0) < 0.05,
          measured=round(rms_db(col[nz[0]:nz[-1] + 1]), 3) if len(nz) else None)

def row_refusal():
    before = files_in_user_config()
    default_before = [v for k, v in steps([{'op': 'dump', 'name': 'b'}]) if k == 'DUMP'][0]['defaultSink']
    # PipeWire cannot load the filter: the module is made unreadable for it
    mod = '/usr/lib/x86_64-linux-gnu/pipewire-0.3/libpipewire-module-filter-chain.so'
    check('the module is made unreadable by the harness (root)', os.path.exists('/tmp/module-hidden'))
    r = apply_state(dev_state(levels={'FL': -3.0}))
    res = [v for k, v in r if k == 'RESULT']
    check('the page refuses the change', bool(res) and res[0]['ok'] is False, message=res[0]['message'] if res else None)
    check('and says why and that the earlier settings stay', bool(res) and 'The change was not kept.' in res[0]['message'].get('text', '') and 'earlier settings stay' in res[0]['message'].get('text', ''))
    check('the file is gone again', files_in_user_config() == before)
    d = [v for k, v in steps([{'op': 'dump', 'name': 'a'}]) if k == 'DUMP'][0]
    check('the default output is as it was', d['defaultSink'] == default_before, before=default_before, after=d['defaultSink'])
    check('no setup sink exists', not any(x['setupActive'] for x in d['devices']))
    # a device that left: refused before anything is written
    r = apply_state({'devices': {'alsa_output.nothing_here': {'positions': POS51, 'levels': {'FL': -3}}}}, node='alsa_output.nothing_here')
    res = [v for k, v in r if k == 'RESULT']
    check('a device that is not there is refused before anything is written', bool(res) and res[0]['ok'] is False and 'no longer connected' in res[0]['message'].get('text', ''), message=res[0]['message'] if res else None)
    check('and nothing was written', files_in_user_config() == before)
    # a refused value
    r = apply_state({'devices': {NODE51: {'positions': POS51, 'levels': {'FL': 99}}}})
    res = [v for k, v in r if k == 'RESULT']
    check('a value outside the range is refused and nothing written', bool(res) and res[0]['ok'] is False and files_in_user_config() == before, message=res[0]['message'] if res else None)

def row_stereo71():
    d = [v for k, v in steps([{'op': 'dump', 'name': 's'}]) if k == 'DUMP'][0]
    by = {x['name']: x for x in d['devices']}
    check('the 5.1 card is offered', by['alsa_output.rig_51']['eligible'] and by['alsa_output.rig_51']['channels'] == 6)
    check('the 7.1 card is offered', by['alsa_output.rig_71']['eligible'] and by['alsa_output.rig_71']['channels'] == 8)
    st = by['alsa_output.rig_st']
    check('the stereo card is not offered, with its sentence', (not st['eligible']) and st['reason'] == 'Speaker Setup is for devices whose current profile has more than two channels. The profile of this device has 2.', reason=st['reason'])
    # 7.1: all eight channels through a setup with levels, a delay and bass management
    P71 = by['alsa_output.rig_71']['positions']
    state = {'devices': {'alsa_output.rig_71': {'positions': P71, 'label': '\u626c\u58f0\u5668\u8bbe\u7f6e\uff1arig 71', 'levels': {'SL': -4.0}, 'small': ['FL', 'FR', 'SL', 'SR'], 'crossover': 100,
                                                  'distances': {p: (3.0 if p != 'RL' else 2.0) for p in P71}}}}
    r = apply_state(state, node='alsa_output.rig_71')
    res = [v for k, v in r if k == 'RESULT']
    check('a 7.1 setup with a Chinese label, levels, delays and bass management is applied', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)

def row_everyaccount():
    # every account: the state goes through the KAuth helper as root into /etc, and the person's own folder stays empty
    etc = '/etc/pipewire/pipewire.conf.d/50-speaker-page.conf'
    check('nothing in /etc to begin with', not os.path.exists(etc))
    r = apply_state(dev_state(levels={'FL': -6.0}, distances={p: 3.0 for p in POS51} | {'RL': 2.0}), system=True)
    res = [v for k, v in r if k == 'RESULT']
    check('the page applied the setup for every account', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    check('the file is in /etc, written by root, with the mark line', os.path.exists(etc) and os.stat(etc).st_uid == 0 and open(etc).readline().startswith('# Written by the Speaker Setup page'))
    check('this account has no file of its own', files_in_user_config() == [])
    names = sh('pw-cli', 'ls', 'Node').stdout
    check('the setup sink is in the graph', 'speaker_setup.' + NODE51 in names)
    r = apply_state({}, system=True)
    res = [v for k, v in r if k == 'RESULT']
    check('back to defaults for every account applied', bool(res) and res[0]['ok'], message=res[0]['message'] if res else None)
    check('and the file is gone, nothing else in the folder touched', not os.path.exists(etc))

def row_everyaccount_refused():
    etc = '/etc/pipewire/pipewire.conf.d/50-speaker-page.conf'
    r = apply_state(dev_state(levels={'FL': -6.0}), system=True)
    res = [v for k, v in r if k == 'RESULT']
    check('polkit refuses and the page says so', bool(res) and res[0]['ok'] is False and 'did not allow the change for every account' in res[0]['message'].get('text', ''), message=res[0]['message'] if res else None)
    check('nothing was written', not os.path.exists(etc) and files_in_user_config() == [])
    names = sh('pw-cli', 'ls', 'Node').stdout
    check('and no setup sink exists', 'speaker_setup' not in names)

ROWS = {'defaults': row_defaults, 'level': row_level, 'distance': row_distance, 'bass': row_bass, 'testsignal': row_testsignal, 'refusal': row_refusal, 'stereo71': row_stereo71, 'everyaccount': row_everyaccount, 'everyaccount-refused': row_everyaccount_refused}

if __name__ == '__main__':
    row = sys.argv[1]
    try:
        ROWS[row]()
    except Exception as e:  # a row that could not run is a failed row
        check('the row ran', False, error=repr(e))
    ok = all(c['ok'] for c in checks)
    print(json.dumps({'row': row, 'ok': ok, 'checks': checks}))
    sys.exit(0 if ok else 1)
