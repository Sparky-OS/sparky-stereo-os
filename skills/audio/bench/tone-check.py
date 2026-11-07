#!/usr/bin/env python3
# tone-check.py WAV --freq HZ [--tol HZ] [--min-dbfs DB] [--min-snr DB] [--skip S]
# Reads a mono or stereo 16-bit WAV, drops the first SKIP seconds (link set-up), and passes only when the loudest
# spectral peak is within TOL of FREQ, the RMS level is at least MIN_DBFS and the peak band holds at least MIN_SNR dB
# more energy than the rest. One JSON line; exit 0 pass, 1 fail.
import argparse, json, sys, wave
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("wav"); ap.add_argument("--freq", type=float, required=True)
ap.add_argument("--tol", type=float, default=20.0); ap.add_argument("--min-dbfs", type=float, default=-40.0)
ap.add_argument("--min-snr", type=float, default=20.0); ap.add_argument("--skip", type=float, default=1.0)
a = ap.parse_args()
try:
    w = wave.open(a.wav, "rb")
    n, ch, sw, rate = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
    raw = w.readframes(n)
except Exception as e:
    print(json.dumps({"file": a.wav, "pass": False, "error": str(e)})); sys.exit(1)
if sw != 2:
    print(json.dumps({"file": a.wav, "pass": False, "error": "sample width %d, 16-bit expected" % sw})); sys.exit(1)
x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
if ch > 1: x = x.reshape(-1, ch).mean(axis=1)
x = x[int(a.skip * rate):]
if len(x) < rate // 2:
    print(json.dumps({"file": a.wav, "pass": False, "error": "only %d samples after the skip" % len(x), "rate": rate})); sys.exit(1)
rms = float(np.sqrt(np.mean(x * x)))
dbfs = 20 * np.log10(rms) if rms > 0 else -200.0
win = np.hanning(len(x)); spec = np.abs(np.fft.rfft(x * win)) ** 2; fr = np.fft.rfftfreq(len(x), 1.0 / rate)
spec[0] = 0
k = int(np.argmax(spec)); peak = float(fr[k])
band = np.abs(fr - peak) <= 3 * rate / len(x) * 4
sig = float(spec[band].sum()); rest = float(spec[~band].sum()) + 1e-30
snr = 10 * np.log10(sig / rest) if sig > 0 else -200.0
ok = abs(peak - a.freq) <= a.tol and dbfs >= a.min_dbfs and snr >= a.min_snr
print(json.dumps({"file": a.wav, "pass": bool(ok), "rate": rate, "seconds": round(len(x) / rate, 2), "peak_hz": round(peak, 1),
                  "expected_hz": a.freq, "rms_dbfs": round(float(dbfs), 1), "snr_db": round(float(snr), 1)}))
sys.exit(0 if ok else 1)
