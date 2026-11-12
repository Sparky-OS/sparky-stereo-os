#!/usr/bin/env python3
"""A small client for Chromium's DevTools protocol over WebSocket (RFC 6455), standard library only: used by the
proof drivers (drive.py, a11y.py). Our code, BSD 2-clause."""
import base64
import json
import os
import socket
import struct
import time
import urllib.request


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


def target(dport, sport):
    """the WebSocket address of the page served from port sport"""
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


def evaluate(ws, expression, await_promise=False):
    """the value of a JavaScript expression in the page (returned by value)"""
    r = ws.call('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': await_promise})
    if 'exceptionDetails' in r:
        raise RuntimeError('page exception: %s' % json.dumps(r['exceptionDetails'])[:600])
    return r['result'].get('value')


def wait_for(ws, expression, timeout=120, step=0.25):
    """wait until the expression is truthy; returns its value, or None at the timeout"""
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        try:
            v = evaluate(ws, expression)
        except RuntimeError:
            v = None
        if v:
            return v
        time.sleep(step)
    return None


def screenshot(ws, path, full=False):
    r = ws.call('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': bool(full)})
    with open(path, 'wb') as f:
        f.write(base64.b64decode(r['data']))
