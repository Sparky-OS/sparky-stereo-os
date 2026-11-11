#!/usr/bin/env python3
"""The scene tester's own server (ORDER 508, milestone 3): the tester page, the scene, and a virtual link.

    python3 serve.py [--port 8508] [--scene DIR] [--save DIR]

Open the address it prints in a browser on this machine; stop it with Ctrl+C. It listens on 127.0.0.1 only, needs
no network and installs nothing.

The virtual link: every request whose query carries link=1 is sent through one link of a set rate in bytes per
second, shared by all such requests at once (each connection takes its turn chunk by chunk, so N connections share
the rate fairly). A chunk is written when its slot on the link has passed, so the bytes leave at the set rate. The
tester sets the rate with POST /link {"rate": BYTES_PER_SECOND} (0: no limit). Every chunk sent is recorded
(GET /link/log; POST /link/reset clears it) so the rate the page shows can be checked against the bytes really sent.
HTTP headers are not counted or limited; only bodies are.

--save DIR (proofs only): POST /save?name=X writes the body to DIR/X; POST /done writes DIR/DONE.
Outside input is data: paths are resolved under the served folders, names are checked. Our code, BSD 2-clause."""
import argparse
import http.server
import json
import os
import re
import threading
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = re.compile(r'^[A-Za-z0-9._-]{1,160}$')
TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
         '.wgsl': 'text/plain; charset=utf-8', '.wasm': 'application/wasm', '.gltf': 'model/gltf+json',
         '.bin': 'application/octet-stream', '.jpg': 'image/jpeg', '.png': 'image/png', '.mp3': 'audio/mpeg',
         '.p2p': 'text/plain; charset=utf-8', '.json': 'application/json', '.md': 'text/markdown; charset=utf-8',
         '.css': 'text/css; charset=utf-8', '.txt': 'text/plain; charset=utf-8'}


class Link:
    """One link shared by every limited request: a slot of n/rate seconds per chunk, taken in turn."""

    def __init__(self):
        self.lock = threading.Lock()
        self.rate = 0.0
        self.free_at = 0.0
        self.t0 = time.monotonic()
        self.log = []          # (seconds since reset, bytes, path)

    def chunk(self):
        r = self.rate
        return 65536 if r <= 0 else max(32, min(65536, int(r / 50)))

    def send(self, wfile, data, path):
        pos = 0
        while pos < len(data):
            with self.lock:
                n = min(self.chunk(), len(data) - pos)
                now = time.monotonic()
                if self.rate > 0:
                    start = max(now, self.free_at)
                    self.free_at = start + n / self.rate
                    due = self.free_at
                else:
                    due = now
            wait = due - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            wfile.write(data[pos:pos + n])
            wfile.flush()
            with self.lock:
                self.log.append((round(time.monotonic() - self.t0, 4), n, path))
            pos += n


LINK = Link()


class H(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    roots = {}
    save = None

    def log_message(self, fmt, *args):
        pass

    def resolve(self, path):
        """URL path -> file under one of the served folders, or None."""
        path = urllib.parse.unquote(path)
        if path in ('', '/'):
            path = '/index.html'
        for prefix, root in self.roots.items():
            if path.startswith(prefix):
                rel = path[len(prefix):]
                full = os.path.realpath(os.path.join(root, rel))
                if os.path.commonpath([full, os.path.realpath(root)]) == os.path.realpath(root) and os.path.isfile(full):
                    return full
                return None
        return None

    def reply(self, code, body=b'', ctype='application/json'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == '/link/log':
            with LINK.lock:
                body = json.dumps({'rate': LINK.rate, 'log': LINK.log}).encode()
            return self.reply(200, body)
        if u.path == '/link':
            return self.reply(200, json.dumps({'rate': LINK.rate}).encode())
        full = self.resolve(u.path)
        if not full:
            return self.reply(404, b'not found', 'text/plain')
        with open(full, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', TYPES.get(os.path.splitext(full)[1].lower(), 'application/octet-stream'))
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if self.command == 'HEAD':
            return
        q = urllib.parse.parse_qs(u.query)
        if q.get('link', ['0'])[0] == '1':
            LINK.send(self.wfile, data, u.path)
        else:
            self.wfile.write(data)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(n) if n > 0 else b''
        if u.path == '/link':
            try:
                rate = float(json.loads(body or b'{}').get('rate', 0))
            except (ValueError, AttributeError):
                return self.reply(400, b'{"error":"rate is a number of bytes per second"}')
            if rate < 0 or rate > 1e10:
                return self.reply(400, b'{"error":"rate out of range"}')
            with LINK.lock:
                LINK.rate = rate
                LINK.free_at = time.monotonic()
            return self.reply(200, json.dumps({'rate': rate}).encode())
        if u.path == '/link/reset':
            with LINK.lock:
                LINK.log = []
                LINK.t0 = time.monotonic()
                LINK.free_at = LINK.t0
            return self.reply(200, b'{}')
        if self.save and u.path == '/save':
            name = urllib.parse.parse_qs(u.query).get('name', [''])[0]
            if not NAME.match(name):
                return self.reply(400, b'{"error":"bad name"}')
            with open(os.path.join(self.save, name), 'wb') as f:
                f.write(body)
            return self.reply(200, b'{}')
        if self.save and u.path == '/done':
            with open(os.path.join(self.save, 'DONE'), 'wb') as f:
                f.write(body)
            return self.reply(200, b'{}')
        return self.reply(404, b'{}')


def main():
    ap = argparse.ArgumentParser(description='the scene tester\'s server')
    ap.add_argument('--port', type=int, default=8508)
    ap.add_argument('--scene', default=os.path.join(HERE, 'scene'))
    ap.add_argument('--save')
    ap.add_argument('--npm', help='proofs only: a folder of npm packages served under /npm/')
    a = ap.parse_args()
    src = os.path.dirname(HERE)
    H.roots = {'/scene/': a.scene, '/ops/': os.path.join(src, 'ops'), '/web/': os.path.join(src, 'web'),
               '/player/': os.path.join(HERE, 'player'), '/': os.path.join(HERE, 'www')}
    if a.npm:
        H.roots = {'/npm/': a.npm, **H.roots}
    if a.save:
        os.makedirs(a.save, exist_ok=True)
        H.save = a.save
    s = http.server.ThreadingHTTPServer(('127.0.0.1', a.port), H)
    s.daemon_threads = True
    print('The scene tester: open http://127.0.0.1:%d/ in a browser on this machine. Stop with Ctrl+C.' % a.port, flush=True)
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        print('stopped')


if __name__ == '__main__':
    main()
