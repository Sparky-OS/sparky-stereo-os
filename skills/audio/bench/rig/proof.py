#!/usr/bin/python3 -I
"""proof.py: the audio-defaults rows (ORDER 631), run inside a rig session (session.sh) as the user "rig".

For each source rate and each fake device it plays a deterministic 24-bit test file with pw-cat and reads, from
PipeWire itself (pw-dump) and from the fake device's own record (OUT.params, what the "hardware" was opened with):
the graph's rate (the sink node's format rate), the stream's rate, the rate and format the device was opened with, the
resampler quality the stream carries, whether the path resampled, and, where the path did not resample, whether the
samples that reached the device equal the file's, bit for bit.

  proof.py rows [--rates 44100,48000,...] [--devices dac,only48,pcm16,hdmi] [--seconds 4]  prints JSON lines
"""
import argparse, json, os, struct, subprocess, sys, time, wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mkwav  # noqa: E402

DEV = {'bt': 'bluez_output.rig_bt', 'hot': 'alsa_output.rig_hot', 'dac': 'alsa_output.rig_dac', 'only48': 'alsa_output.rig_only48', 'pcm16': 'alsa_output.rig_pcm16',
       'hdmi': 'alsa_output.rig_hdmi'}
OUTDIR = '/run/sa631'


def dump():
    return json.loads(subprocess.run(['pw-dump'], capture_output=True, text=True, check=True).stdout)


def node_by_name(objs, name):
    for o in objs:
        if o.get('type') == 'PipeWire:Interface:Node' and o['info']['props'].get('node.name') == name:
            return o
    return None


def fmt_of(node):
    f = node['info']['params'].get('Format') or []
    return f[0] if f else {}


FORMAT_BYTES = {'S16_LE': 2, 'S24_3LE': 3, 'S24_LE': 4, 'S32_LE': 4}


def frames_of(path, fmt):
    n = FORMAT_BYTES[fmt]
    data = open(path, 'rb').read()
    nfr = len(data) // (n * 2)
    sh = {'S16_LE': 0, 'S24_3LE': 0, 'S24_LE': 0, 'S32_LE': 0}[fmt]
    def val(off):
        b = data[off:off + n]
        if fmt == 'S16_LE':
            return struct.unpack('<h', b)[0] << 8          # to 24-bit scale
        if fmt == 'S24_3LE':
            return struct.unpack('<i', b + (b'\xff' if b[2] & 0x80 else b'\x00'))[0]
        if fmt == 'S24_LE':
            return (struct.unpack('<i', b)[0] << 8) >> 8
        return struct.unpack('<i', b)[0] >> 8              # S32: the 24 bits that matter
    return nfr, val, n


def compare(path, fmt, rate, seconds):
    """Align the device's record with the test file and compare. Returns (compared frames, exact frames, max error in
    24-bit steps) or None when the file never shows the first test frame."""
    try:
        nfr, val, n = frames_of(path, fmt)
    except (OSError, KeyError):
        return None
    fb = n * 2
    want0 = (mkwav.sample(0, 0), mkwav.sample(0, 1))
    tol = 512 if fmt == 'S16_LE' else 0       # a 16-bit device cannot hold the low 8 bits of the 24-bit file: half a 16-bit step (128) of rounding, one step (256) of dither
    start = None
    for i in range(min(nfr, rate * 3)):
        a, b = val(i * fb), val(i * fb + n)
        if abs(a - want0[0]) <= tol and abs(b - want0[1]) <= tol and i + 1 < nfr:
            a1, b1 = val((i + 1) * fb), val((i + 1) * fb + n)
            if abs(a1 - mkwav.sample(1, 0)) <= tol and abs(b1 - mkwav.sample(1, 1)) <= tol:
                start = i
                break
    if start is None:
        return {'aligned': False}
    count = min(nfr - start, rate * (seconds - 1))
    exact = 0; worst = 0
    for k in range(count):
        a, b = val((start + k) * fb), val((start + k) * fb + n)
        ea, eb = abs(a - mkwav.sample(k, 0)), abs(b - mkwav.sample(k, 1))
        worst = max(worst, ea, eb)
        if ea == 0 and eb == 0:
            exact += 1
    return {'aligned': True, 'compared': count, 'exact': exact, 'max_error_24bit_steps': worst}


def row(rate, dev, seconds, player='pw-cat'):
    wav = f'/tmp/sa631-{rate}.wav'
    if not os.path.exists(wav):
        mkwav.main(wav, rate, seconds)
    for f in (f'{OUTDIR}/{dev}.raw', f'{OUTDIR}/{dev}.raw.params'):
        pass
    outbase = {'bt': 'bt', 'hot': 'hot', 'dac': 'dac', 'only48': 'only48', 'pcm16': 'pcm16', 'hdmi': 'hdmi'}[dev]
    for suffix in ('.raw', '.raw.params'):
        try:
            os.remove(f'{OUTDIR}/{outbase}{suffix}')
        except FileNotFoundError:
            pass
    if player == 'paplay':
        cmd = ['paplay', '--device=' + DEV[dev], wav]
    else:
        cmd = ['pw-cat', '-p', '--target', DEV[dev], wav]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.6)
    objs = dump()
    sink = node_by_name(objs, DEV[dev])
    stream = None
    for o in objs:
        if o.get('type') == 'PipeWire:Interface:Node' and o['info']['props'].get('media.class') == 'Stream/Output/Audio':
            stream = o
    graph_rate = fmt_of(sink).get('rate') if sink else None
    out = {'source_rate': rate, 'device': dev, 'graph_rate': graph_rate}
    if stream:
        sp = stream['info']['props']
        out['stream_rate'] = fmt_of(stream).get('rate')
        out['stream_resample_quality'] = sp.get('resample.quality', 'unset (PipeWire default 4)')
    meta = subprocess.run(['pw-metadata', '-n', 'settings'], capture_output=True, text=True).stdout
    for line in meta.splitlines():
        for key in ('clock.rate', 'clock.allowed-rates'):
            if f"key:'{key}'" in line:
                out['settings_' + key.replace('.', '_').replace('-', '_')] = line.split("value:'")[1].split("'")[0]
    p.wait(timeout=seconds + 10)
    time.sleep(0.3)
    try:
        par = json.load(open(f'{OUTDIR}/{outbase}.raw.params'))
        out['device_rate'] = par['rate']; out['device_format'] = par['format']
        out['sink_props_resample_quality'] = sink['info']['props'].get('resample.quality', 'unset (PipeWire default 4)') if sink else None
        out['sink_props_dither_method'] = sink['info']['props'].get('dither.method', 'unset') if sink else None
        out['resampled_at_stream'] = out.get('stream_rate') != graph_rate
        out['resampled_at_device'] = graph_rate != par['rate']
        out['resampled'] = out['resampled_at_stream'] or out['resampled_at_device']
        out['bit_exact'] = None
        if not out['resampled']:
            c = compare(f'{OUTDIR}/{outbase}.raw', par['format'], par['rate'], seconds)
            out['samples'] = c
            if c and c.get('aligned'):
                out['bit_exact'] = c['exact'] == c['compared'] if par['format'] != 'S16_LE' else None
    except (OSError, ValueError) as e:
        out['error'] = f'no device record: {e}'
    return out


def sample16(n, ch):
    return mkwav.sample(n, ch) >> 8


def dither(source16):
    """Plays a test file to the 16-bit-only device at 48 kHz (no conversion) and reports the error of the 16-bit samples
    that reached it against the file's own values, as a histogram in 16-bit steps: all zero is bit-exact, a spread of
    -1, 0 and +1 in a 1:2:1 proportion is triangular dither (TPDF)."""
    import collections, wave
    wav = '/tmp/sa631-d16.wav' if source16 else '/tmp/sa631-d24.wav'
    if source16:
        w = wave.open(wav, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000)
        buf = bytearray()
        for i in range(48000 * 3):
            for ch in (0, 1):
                buf += struct.pack('<h', sample16(i, ch))
        w.writeframes(bytes(buf)); w.close()
    else:
        mkwav.main(wav, 48000, 3)
    for suffix in ('.raw', '.raw.params'):
        try:
            os.remove(f'{OUTDIR}/pcm16{suffix}')
        except FileNotFoundError:
            pass
    p = subprocess.Popen(['pw-cat', '-p', '--target', DEV['pcm16'], wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    sink = node_by_name(dump(), DEV['pcm16'])
    props = {k: v for k, v in sink['info']['props'].items() if 'dither' in k or 'quality' in k}
    p.wait(timeout=20)
    time.sleep(0.3)
    nfr, val, n = frames_of(f'{OUTDIR}/pcm16.raw', 'S16_LE')
    ref = (lambda k, ch: sample16(k, ch) if source16 else mkwav.sample(k, ch) / 256.0)
    start = None
    for i in range(48000 * 2):
        if abs((val(i * 4) >> 8) - ref(0, 0)) <= 2 and abs((val(i * 4 + 2) >> 8) - ref(0, 1)) <= 2 \
                and abs((val((i + 1) * 4) >> 8) - ref(1, 0)) <= 2:
            start = i
            break
    err = collections.Counter()
    for k in range(48000):
        err[round((val((start + k) * 4) >> 8) - ref(k, 0))] += 1
    print(json.dumps({'source': '16 bit' if source16 else '24 bit', 'sink_props': props, 'error_histogram_16bit_steps': sorted(err.items())}))


def apply_row(a):
    """Runs `sparky-stereo-audio apply` in the session and prints the rates the running sound system follows after it."""
    def settings():
        out = {}
        for line in subprocess.run(['pw-metadata', '-n', 'settings'], capture_output=True, text=True).stdout.splitlines():
            for key in ('clock.rate', 'clock.allowed-rates'):
                if f"key:'{key}'" in line:
                    out[key] = line.split("value:'")[1].split("'")[0]
        return out
    before = settings()
    try:
        r = subprocess.run(['sparky-stereo-audio', 'apply'], capture_output=True, text=True, env=dict(os.environ, LANG='C'))
        res = {'apply_exit': r.returncode, 'apply_out': r.stdout.strip(), 'apply_err': r.stderr.strip()}
    except FileNotFoundError:
        res = {'apply_exit': 'sparky-stereo-audio is not installed'}
    print(json.dumps({'before': before, **res, 'after': settings()}))


HOT = ('create-node adapter { factory.name=api.alsa.pcm.sink node.name=alsa_output.rig_hot media.class=Audio/Sink '
       'api.alsa.path=sa_hot device.bus=usb audio.position=[FL FR] priority.session=1500 }\n')


class Plugged:
    """A sound device that exists while the object lives: pw-cli keeps the node it created until it exits."""
    def __enter__(self):
        self.p = subprocess.Popen(['pw-cli'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        self.p.stdin.write(HOT); self.p.stdin.flush()
        time.sleep(1.5)
        return self

    def __exit__(self, *a):
        self.p.terminate(); self.p.wait(timeout=5)
        time.sleep(1.5)


def default_sink():
    out = subprocess.run(['pw-metadata', '-n', 'default'], capture_output=True, text=True).stdout
    names = {}
    for line in out.splitlines():
        for key in ('default.audio.sink', 'default.configured.audio.sink'):
            if f"key:'{key}'" in line:
                names[key] = line.split("value:'")[1].split("'")[0]
    return names


def hook_row():
    """The headset hook (sparky-stereo-hardware): a USB output that appears after the first 10 s takes the sound and
    gives it back when it goes. Prints the default sink before, while the device is there, and after."""
    time.sleep(11)
    row_ = {'before': default_sink()}
    with Plugged():
        row_['while_plugged'] = default_sink()
    row_['after_unplug'] = default_sink()
    print(json.dumps(row_))


def liveapply_row(a):
    """A device plugged in during the session: the list the session follows, before and after `sparky-stereo-audio apply`,
    and a 96 kHz file played to the new device and to the DAC."""
    out = {'before': row(96000, 'dac', 4)}
    with Plugged():
        try:
            r = subprocess.run(['sparky-stereo-audio', 'apply'], capture_output=True, text=True, env=dict(os.environ, LANG='C'))
            out['apply_exit'] = r.returncode
            out['apply_err'] = r.stderr.strip()
        except FileNotFoundError:
            out['apply_exit'] = 'sparky-stereo-audio is not installed'
        out['hot_after'] = row(96000, 'hot', 4)
        out['dac_after'] = row(96000, 'dac', 4)
    print(json.dumps(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['rows', 'dither', 'apply', 'hook', 'liveapply'])
    ap.add_argument('--player', default='pw-cat')
    ap.add_argument('--source16', action='store_true')
    ap.add_argument('--rates', default='44100,48000,88200,96000,192000')
    ap.add_argument('--devices', default='dac,only48,pcm16,hdmi')
    ap.add_argument('--seconds', type=int, default=4)
    a = ap.parse_args()
    if a.cmd == 'dither':
        return dither(a.source16)
    if a.cmd == 'apply':
        return apply_row(a)
    if a.cmd == 'hook':
        return hook_row()
    if a.cmd == 'liveapply':
        return liveapply_row(a)
    for dev in a.devices.split(','):
        for r in a.rates.split(','):
            print(json.dumps(row(int(r), dev, a.seconds, a.player)), flush=True)
            time.sleep(0.8)


if __name__ == '__main__':
    main()
