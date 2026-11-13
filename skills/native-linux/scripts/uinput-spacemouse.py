#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""A simulated 3D mouse for a test, with the kernel's uinput and nothing but the standard library.
It creates an input device with the USB identity of a 3Dconnexion SpaceNavigator (046d:c626), six relative axes
and two buttons, then sends the moves given as arguments, each "count x y z rx ry rz" (one event set per 16 ms).
Run as root, in a virtual machine or on a test machine: the device is real to every program on that system.
usage: uinput-spacemouse.py HOLD_SECONDS MOVE [MOVE...]"""
import fcntl, os, struct, sys, time
EV_SYN, EV_KEY, EV_REL = 0, 1, 2
UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_RELBIT = 0x40045564, 0x40045565, 0x40045566
UI_DEV_SETUP, UI_DEV_CREATE, UI_DEV_DESTROY = 0x405c5503, 0x5501, 0x5502
fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
for ev in (EV_KEY, EV_REL): fcntl.ioctl(fd, UI_SET_EVBIT, ev)
for axis in range(6): fcntl.ioctl(fd, UI_SET_RELBIT, axis)          # REL_X Y Z RX RY RZ
for btn in (0x100, 0x101): fcntl.ioctl(fd, UI_SET_KEYBIT, btn)      # BTN_0, BTN_1
fcntl.ioctl(fd, UI_DEV_SETUP, struct.pack('HHHH80sI', 3, 0x046d, 0xc626, 0x0100, b'3Dconnexion SpaceNavigator', 0))
fcntl.ioctl(fd, UI_DEV_CREATE)
def emit(t, c, v):
    now = time.time(); os.write(fd, struct.pack('qqHHi', int(now), int(now % 1 * 1e6), t, c, v))
hold = float(sys.argv[1]); print('device created', flush=True); time.sleep(hold)
for move in sys.argv[2:]:
    n, *v = [int(t) for t in move.split()]
    for _ in range(n):
        for axis, val in enumerate(v):
            if val: emit(EV_REL, axis, val)
        emit(EV_SYN, 0, 0); time.sleep(0.016)
    print('sent', move, flush=True); time.sleep(2)
emit(EV_KEY, 0x100, 1); emit(EV_SYN, 0, 0); time.sleep(0.1); emit(EV_KEY, 0x100, 0); emit(EV_SYN, 0, 0)
print('button 0 pressed and released', flush=True); time.sleep(2)
fcntl.ioctl(fd, UI_DEV_DESTROY); os.close(fd); print('device removed', flush=True)
