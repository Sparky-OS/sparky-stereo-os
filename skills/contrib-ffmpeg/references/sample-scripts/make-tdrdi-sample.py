#!/usr/bin/env python3
# ORDER 174. Adds a prefix SEI NAL unit with a three-dimensional reference displays information
# message (payloadType 176, H.265 G.14.2.3 syntax, G.14.3.3 semantics) before the first coded slice
# of a single-layer HEVC stream. The mantissas are longer than 8 bits and, for the second display,
# longer than 32 bits (their length is Max(0, exponent + prec - 31) bits, up to 62).
#
#   make-tdrdi-sample.py IN.bit OUT.hevc [short]
#
# With the argument short only display 0 is written (mantissas of 32 bits or less).
#
# display 0: left_view_id 0, right_view_id 1, prec_ref_display_width 31, exponent 20 (20 bit mantissa
#            0x9A5C3), prec_ref_viewing_dist 31, exponent 30 (30 bit mantissa 0x2ABCDEF1),
#            additional shift 520 - 512
# display 1: left_view_id 1, right_view_id 0, exponent 40 (40 bit mantissa 0xA5A5A5A5A5),
#            exponent 45 (45 bit mantissa 0x1234567890AB)
import sys

PREC_W = 31
PREC_D = 31
DISPLAYS = [
    (0, 1, 20, 0x9A5C3, 30, 0x2ABCDEF1, 520),
    (1, 0, 40, 0xA5A5A5A5A5, 45, 0x1234567890AB, 512),
]


class Bits:
    def __init__(self):
        self.b = []

    def u(self, n, v):
        assert 0 <= v < (1 << n) or n == 0, (n, v)
        self.b += [(v >> i) & 1 for i in range(n - 1, -1, -1)]

    def ue(self, v):
        v += 1
        n = v.bit_length()
        self.u(n - 1, 0)
        self.u(n, v)

    def rbsp_trailing(self):
        self.b.append(1)
        while len(self.b) % 8:
            self.b.append(0)
        return bytes(int(''.join(map(str, self.b[i:i + 8])), 2) for i in range(0, len(self.b), 8))


def escape(rbsp):
    out, zeros = bytearray(), 0
    for c in rbsp:
        if zeros >= 2 and c <= 3:
            out.append(3)
            zeros = 0
        out.append(c)
        zeros = zeros + 1 if c == 0 else 0
    return bytes(out)


def payload():
    b = Bits()
    b.ue(PREC_W)
    b.u(1, 1)                       # ref_viewing_distance_flag
    b.ue(PREC_D)
    b.ue(len(DISPLAYS) - 1)         # num_ref_displays_minus1
    for left, right, ew, mw, ed, md, shift in DISPLAYS:
        b.ue(left)
        b.ue(right)
        b.u(6, ew)
        b.u(max(0, ew + PREC_W - 31), mw)
        b.u(6, ed)
        b.u(max(0, ed + PREC_D - 31), md)
        b.u(1, 1)                   # additional_shift_present_flag
        b.u(10, shift)
    b.u(1, 0)                       # three_dimensional_reference_displays_extension_flag
    # sei_payload() ends byte aligned with payload_bit_equal_to_one and zero bits
    b.b.append(1)
    while len(b.b) % 8:
        b.b.append(0)
    return bytes(int(''.join(map(str, b.b[i:i + 8])), 2) for i in range(0, len(b.b), 8))


def sei_nal():
    p = payload()
    body = bytes([176, len(p)]) + p + b'\x80'      # payloadType 176 (< 255), payloadSize, rbsp trailing
    assert len(p) < 255
    return bytes([39 << 1, 1]) + escape(body)


def split(data):
    pos, out = [], []
    i = 0
    while True:
        i = data.find(b'\x00\x00\x01', i)
        if i < 0:
            break
        pos.append(i + 3)
        i += 3
    for k, s in enumerate(pos):
        e = pos[k + 1] - 3 if k + 1 < len(pos) else len(data)
        while e > s and data[e - 1] == 0:
            e -= 1
        out.append(data[s:e])
    return out


def main():
    src, dst = sys.argv[1:3]
    if len(sys.argv) > 3 and sys.argv[3] == 'short':
        del DISPLAYS[1:]
    out, done = bytearray(), False
    for nal in split(open(src, 'rb').read()):
        t = (nal[0] >> 1) & 0x3f
        if t < 32 and not done:
            out += b'\x00\x00\x01' + sei_nal()
            done = True
        # start codes as the hevc muxer writes them: four bytes before a parameter set, three otherwise
        out += (b'\x00\x00\x00\x01' if t in (32, 33, 34) else b'\x00\x00\x01') + nal
    assert done
    open(dst, 'wb').write(out)


main()
