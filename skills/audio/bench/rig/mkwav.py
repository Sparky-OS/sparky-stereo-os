#!/usr/bin/python3 -I
"""mkwav.py OUT.wav RATE SECONDS: a deterministic 24-bit stereo test signal (a pseudo-random sequence of 24-bit samples
at about -6 dBFS, different in each channel), so a copy through a sound path can be aligned and compared sample by
sample. The sequence is a pure function of its position (a 32-bit mix), not of the rate."""
import struct, sys, wave

def sample(n, ch):
    x = (n * 2654435761 + ch * 40503 + 12345) & 0xFFFFFFFF
    x ^= x >> 15; x = (x * 2246822519) & 0xFFFFFFFF; x ^= x >> 13
    v = (x >> 4) & 0xFFFFFF           # 24 bits
    v = (v - 0x800000) // 2           # about -6 dBFS
    return v

def main(out, rate, seconds):
    n = rate * seconds
    w = wave.open(out, 'wb'); w.setnchannels(2); w.setsampwidth(3); w.setframerate(rate)
    buf = bytearray()
    for i in range(n):
        for ch in (0, 1):
            buf += struct.pack('<i', sample(i, ch))[:3]
        if len(buf) > 1 << 20:
            w.writeframes(bytes(buf)); buf.clear()
    w.writeframes(bytes(buf)); w.close()

if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
