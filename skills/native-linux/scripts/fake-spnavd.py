#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""A stand-in for spacenavd for tests: listens on the daemon's socket and sends motion events in the
plain protocol (version 0): eight 32-bit integers per event, [0] = 0 for motion, x y z rx ry rz, period in ms.
It never answers requests, so libspnav stays at protocol 0.  usage: fake-spnavd.py SOCKET LOG TRIGGER_DIR
A file TRIGGER_DIR/go-N holding "count x y z rx ry rz" makes it send that many events to every client."""
import os, socket, struct, sys, time, select
path, log, trig = sys.argv[1:4]
def say(*a):
    with open(log, 'a') as f: f.write('%.3f %s\n' % (time.time(), ' '.join(str(x) for x in a)))
try: os.unlink(path)
except FileNotFoundError: pass
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.bind(path); os.chmod(path, 0o666); s.listen(4)
say('listening', path)
clients, done = [], set()
while True:
    r, _, _ = select.select([s] + clients, [], [], 0.1)
    for x in r:
        if x is s:
            c, _ = s.accept(); clients.append(c); say('client connected', len(clients))
        else:
            try: d = x.recv(4096)
            except OSError: d = b''
            if not d: clients.remove(x); say('client gone')
            else: say('client sent', len(d), 'bytes', d[:32].hex())
    for name in sorted(os.listdir(trig)):
        if name.startswith('go-') and name not in done:
            done.add(name)
            n, *v = [int(t) for t in open(os.path.join(trig, name)).read().split()]
            for i in range(n):
                for c in list(clients):
                    try: c.sendall(struct.pack('8i', 0, *v, 16))
                    except OSError: clients.remove(c); say('client closed its end after', i, 'events of', name)
                time.sleep(0.016)
            say('sent', name, n, 'motion events', v, 'to', len(clients), 'clients')
