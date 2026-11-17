#!/usr/bin/python3 -I
# make-panel-edid.py OUT.bin: an EDID 1.4 for a 1366x768 laptop panel (eDP), one detailed timing whose refresh rate
# is 60005 mHz by KWin's and Plymouth's formula ((clock * 10^6 / htotal + vtotal / 2) / vtotal, clock in kHz), the rate
# a laptop's boot line names for its panel (mode=1366x768@60005). Size 344 x 193 mm (a 15.6 inch panel).
import sys


def refresh(clock_khz, htotal, vtotal):
    return (clock_khz * 1000000 // htotal + vtotal // 2) // vtotal


best = None
for hblank in range(120, 260, 2):
    for vblank in range(10, 60):
        h, v = 1366 + hblank, 768 + vblank
        for clock10 in range(6500, 8000):
            if refresh(clock10 * 10, h, v) == 60005:
                best = (clock10, hblank, vblank)
                break
        if best:
            break
    if best:
        break
clock10, hblank, vblank = best
e = bytearray(128)
e[0:8] = bytes([0, 255, 255, 255, 255, 255, 255, 0])
e[8:10] = bytes([0x30, 0xe4])          # manufacturer "LGD"
e[10:12] = (0x0400).to_bytes(2, 'little')
e[16], e[17] = 1, 26                    # week 1 of 2016
e[18], e[19] = 1, 4                     # EDID 1.4
e[20] = 0xa5                            # digital, 8 bits per colour, DisplayPort
e[21], e[22] = 34, 19                   # 34 x 19 cm
e[23] = 120                             # gamma 2.20
e[24] = 0x02 | 0x01 << 4                # preferred timing is native; RGB 4:4:4
e[38:54] = bytes([1, 1] * 8)            # no standard timings
d = bytearray(18)
d[0:2] = clock10.to_bytes(2, 'little')
d[2] = 1366 & 0xff
d[3] = hblank & 0xff
d[4] = ((1366 >> 8) << 4) | (hblank >> 8)
d[5] = 768 & 0xff
d[6] = vblank & 0xff
d[7] = ((768 >> 8) << 4) | (vblank >> 8)
d[8], d[9] = 48, 32                     # h front porch, h sync
d[10] = (3 << 4) | 5                    # v front porch 3, v sync 5
d[11] = 0
d[12], d[13] = 344 & 0xff, 193 & 0xff
d[14] = ((344 >> 8) << 4) | (193 >> 8)
d[17] = 0x18                            # digital separate sync, negative both
e[54:72] = d
e[72:90] = bytes([0, 0, 0, 0xfc, 0]) + b'TEST PANEL\n  '
e[90:108] = bytes([0, 0, 0, 0x10, 0] + [0] * 13)
e[108:126] = bytes([0, 0, 0, 0x10, 0] + [0] * 13)
e[127] = (256 - sum(e[:127]) % 256) % 256
open(sys.argv[1], 'wb').write(e)
print('clock %d kHz htotal %d vtotal %d refresh %d mHz' % (clock10 * 10, 1366 + hblank, 768 + vblank,
                                                            refresh(clock10 * 10, 1366 + hblank, 768 + vblank)))
