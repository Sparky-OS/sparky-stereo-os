#!/usr/bin/env python3
"""Watch one run of the Procedural Texture Rendering page inside its container through Chromium's DevTools protocol:
take screenshots of the page (the scene and the panel) at the moments that show the five loading steps, read the
page's own results (window.testerResult) and, when the local server's link was used, the server's record of every
chunk it sent. The page posts nothing: every result is read here, so the same page runs on a plain static host.

drive.py OUTDIR TAG DEVTOOLS-PORT SERVER-PORT TIMEOUT-S [LINK-LOG-URL]

Screenshots: TAG-1-first.png (one second after the first frame drawn from the procedures), TAG-2-early.png (20 s
later, dial-up only: still drawn from procedures), TAG-3-blend.png (while the first picture blends in), TAG-4-half.png
(half of the picture bytes in), TAG-5-end.png (after every procedure has stopped). Ends when the page has its results
(OUTDIR/TAG-result.json and OUTDIR/DONE are written) or at the timeout. Standard library only; a small WebSocket
client (RFC 6455) is written here. Our code, BSD 2-clause."""
import base64
import json
import os
import socket
import struct
import sys
import time
import urllib.request

out, tag = sys.argv[1], sys.argv[2]
dport = int(sys.argv[3]) if len(sys.argv) > 3 else 9222
sport = int(sys.argv[4]) if len(sys.argv) > 4 else 8508
timeout = float(sys.argv[5]) if len(sys.argv) > 5 else 7200
linklog = sys.argv[6] if len(sys.argv) > 6 else ''


class WS:
    def __init__(self, url):
        rest = url.split('://', 1)[1]
        hostport, path = rest.split('/', 1)
        host, port = hostport.split(':')
        self.s = socket.create_connection((host, int(port)), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        req = ('GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
               'Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n') % (path, hostport, key)
        self.s.sendall(req.encode())
        head = b''
        while b'\r\n\r\n' not in head:
            b = self.s.recv(1)
            if not b:
                raise RuntimeError('the DevTools socket closed during the handshake')
            head += b
        if b' 101 ' not in head.split(b'\r\n', 1)[0]:
            raise RuntimeError('no WebSocket: %r' % head[:200])
        self.n = 0
        self.events = []

    def send(self, obj):
        data = json.dumps(obj).encode()
        hdr = bytes([0x81])
        ln = len(data)
        if ln < 126:
            hdr += bytes([0x80 | ln])
        elif ln < 65536:
            hdr += bytes([0x80 | 126]) + struct.pack('>H', ln)
        else:
            hdr += bytes([0x80 | 127]) + struct.pack('>Q', ln)
        mask = os.urandom(4)
        self.s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def exact(self, n):
        b = b''
        while len(b) < n:
            c = self.s.recv(n - len(b))
            if not c:
                raise RuntimeError('the DevTools socket closed')
            b += c
        return b

    def recv(self):
        msg = b''
        while True:
            h = self.exact(2)
            fin, op, ln = h[0] & 0x80, h[0] & 0x0f, h[1] & 0x7f
            if ln == 126:
                ln = struct.unpack('>H', self.exact(2))[0]
            elif ln == 127:
                ln = struct.unpack('>Q', self.exact(8))[0]
            payload = self.exact(ln)
            if op == 0x9:          # ping: answer
                self.s.sendall(bytes([0x8a, 0x80 | len(payload)]) + b'\0\0\0\0' + payload)
                continue
            msg += payload
            if fin:
                return json.loads(msg)

    def call(self, method, params=None):
        self.n += 1
        mid = self.n
        self.send({'id': mid, 'method': method, 'params': params or {}})
        while True:
            m = self.recv()
            if 'method' in m and m['method'] in ('Runtime.exceptionThrown', 'Runtime.consoleAPICalled', 'Log.entryAdded'):
                self.events.append(m)
            if m.get('id') == mid:
                if 'error' in m:
                    raise RuntimeError('%s: %s' % (method, m['error']))
                return m.get('result', {})


def target():
    for _ in range(120):
        try:
            lst = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list' % dport, timeout=5))
            for tg in lst:
                if tg.get('type') == 'page' and ':%d/' % sport in tg.get('url', ''):
                    return tg['webSocketDebuggerUrl']
        except OSError:
            pass
        time.sleep(0.5)
    raise SystemExit('no page target in DevTools')


ws = WS(target())
ws.call('Runtime.enable')
ws.call('Log.enable')
shots = {}
t0 = time.monotonic()
log = open(os.path.join(out, tag + '-drive.log'), 'a')


def shot(name):
    if name in shots:
        return
    r = ws.call('Page.captureScreenshot', {'format': 'png'})
    p = os.path.join(out, '%s-%s.png' % (tag, name))
    with open(p, 'wb') as f:
        f.write(base64.b64decode(r['data']))
    shots[name] = time.monotonic() - t0
    log.write('%.1f screenshot %s\n' % (shots[name], name))
    log.flush()


first_seen = None
while time.monotonic() - t0 < timeout:
    try:
        rr = ws.call('Runtime.evaluate', {'expression': 'window.testerResult', 'returnByValue': True})
        res = rr['result'].get('value')
    except (RuntimeError, KeyError) as e:
        res = None
    if res:
        with open(os.path.join(out, tag + '-result.json'), 'w') as f:
            f.write(res)
        # a test page's own files (window.testerFiles: name -> 'text:...' or 'base64:...'), one at a time
        try:
            names = json.loads(ws.call('Runtime.evaluate', {'expression': 'JSON.stringify(Object.keys(window.testerFiles || {}))', 'returnByValue': True})['result']['value'])
        except (RuntimeError, KeyError, ValueError):
            names = []
        for nm in names:
            if not all(ch.isalnum() or ch in '._-' for ch in nm) or len(nm) > 160:
                continue
            v = ws.call('Runtime.evaluate', {'expression': 'window.testerFiles[%s]' % json.dumps(nm), 'returnByValue': True})['result'].get('value', '')
            with open(os.path.join(out, nm), 'wb') as f:
                f.write(base64.b64decode(v[7:]) if v.startswith('base64:') else v[5:].encode())
        try:
            shot('5-end')
        except RuntimeError:
            pass
        with open(os.path.join(out, 'DONE'), 'w') as f:
            f.write('ok')
        break
    try:
        r = ws.call('Runtime.evaluate', {'expression': 'window.testerState ? JSON.stringify(testerState()) : "null"', 'returnByValue': True})
        st = json.loads(r['result']['value'])
    except (RuntimeError, KeyError, ValueError) as e:
        log.write('%.1f state unreadable: %s\n' % (time.monotonic() - t0, e))
        st = None
    if st:
        if st.get('firstFrame') is not None and first_seen is None:
            first_seen = time.monotonic()
        if first_seen and time.monotonic() - first_seen > 1.0:
            shot('1-first')
        if first_seen and time.monotonic() - first_seen > 20 and st.get('allIn') is None:
            shot('2-early')
        if any(x['mode'] == 'blend' for x in st['textures']):
            shot('3-blend')
        lim = [c for c in st['comps'] if c['size']]
        got = sum(c['received'] for c in st['comps'] if c.get('kind') == 'picture')
        allp = sum(c['size'] for c in st['comps'] if c.get('kind') == 'picture') or 1
        if got >= allp / 2 and st.get('allIn') is None:
            shot('4-half')
        if st.get('settled') is not None and (time.monotonic() - t0) > 0:
            time.sleep(1.5)
            shot('5-end')
    time.sleep(0.25 if not first_seen or time.monotonic() - first_seen < 30 else 1.0)
try:
    shot('5-end')
except RuntimeError:
    pass
try:
    r = ws.call('Runtime.evaluate', {'expression': 'window.testerState ? JSON.stringify(testerState()) : "null"', 'returnByValue': True})
    with open(os.path.join(out, tag + '-state.json'), 'w') as f:
        f.write(r['result']['value'])
except (RuntimeError, KeyError, OSError) as e:
    log.write('final state not read: %s\n' % e)
with open(os.path.join(out, tag + '-console.json'), 'w') as f:
    json.dump(ws.events, f, indent=1)
if linklog:
    try:
        data = urllib.request.urlopen(linklog, timeout=30).read()
        with open(os.path.join(out, tag + '-linklog.json'), 'wb') as f:
            f.write(data)
    except OSError as e:
        log.write('link log not read: %s\n' % e)
log.write('end after %.1f s; screenshots %s\n' % (time.monotonic() - t0, json.dumps(shots)))
log.close()
