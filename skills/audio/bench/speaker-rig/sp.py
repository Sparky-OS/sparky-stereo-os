#!/usr/bin/python3 -I
"""Measuring helpers of the speaker rig (ORDER 23): make a multichannel test file, play it to a node, read what a fake device received.

  sp.py mk OUT.f32 CHANNELS RATE SPEC     SPEC: "ch:kind:args;..." kinds: impulse(N) tone(HZ,AMP) noise(AMP,SEED) silence
  sp.py rd DEVICE_RAW            JSON: channels, rate, format, frames, per-channel rms dBFS and first non-zero frame
"""
import json, math, struct, sys
import numpy as np

def make(channels, rate, spec, seconds=2.0):
    n = int(rate * seconds)
    x = np.zeros((n, channels), dtype=np.float32)
    for part in spec.split(';'):
        if not part:
            continue
        ch, kind, *args = part.split(':')
        ch = int(ch)
        a = [float(v) for v in args[0].split(',')] if args else []
        if kind == 'impulse':
            x[int(a[0]), ch] = 0.5
        elif kind == 'tone':
            t = np.arange(n) / rate
            x[:, ch] = (a[1] * np.sin(2 * math.pi * a[0] * t)).astype(np.float32)
        elif kind == 'noise':
            r = np.random.default_rng(int(a[1]))
            x[:, ch] = (a[0] * r.standard_normal(n)).astype(np.float32).clip(-0.99, 0.99)
    return x

def read_device(path):
    p = json.load(open(path + '.params'))
    ch, fmt = p['channels'], p['format']
    raw = open(path, 'rb').read()
    if fmt == 'S32_LE':
        a = np.frombuffer(raw[: len(raw) // (4 * ch) * 4 * ch], dtype='<i4').astype(np.float64) / 2147483648.0
    elif fmt == 'S16_LE':
        a = np.frombuffer(raw[: len(raw) // (2 * ch) * 2 * ch], dtype='<i2').astype(np.float64) / 32768.0
    else:
        raise SystemExit('format ' + fmt)
    return a.reshape(-1, ch), p

def db(v):
    return -999.0 if v <= 0 else 20 * math.log10(v)

def report(path):
    a, p = read_device(path)
    out = {'params': p, 'frames': int(a.shape[0]), 'channels': []}
    for c in range(a.shape[1]):
        col = a[:, c]
        nz = np.nonzero(np.abs(col) > 1e-7)[0]
        sel = col[nz[0]:nz[-1] + 1] if len(nz) else col[:0]
        out['channels'].append({'first': int(nz[0]) if len(nz) else None, 'last': int(nz[-1]) if len(nz) else None,
                                'rmsdb': db(float(np.sqrt(np.mean(sel ** 2)))) if len(sel) else -999.0, 'peak': float(np.abs(col).max())})
    return out

if __name__ == '__main__':
    if sys.argv[1] == 'mk':
        x = make(int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
        open(sys.argv[2], 'wb').write(x.astype('<f4').tobytes())
    elif sys.argv[1] == 'rd':
        print(json.dumps(report(sys.argv[2])))
