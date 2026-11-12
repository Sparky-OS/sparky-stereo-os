#!/usr/bin/env python3
"""Procedural Texture Rendering: the local server, the other way to run the demo (the first is any static host).

    python3 serve.py [--port 8537] [--site DIR] [--prefix /]

Open the address it prints in a browser on this machine; stop it with Ctrl+C. It listens on 127.0.0.1 only, needs
no network and installs nothing. It serves the site folder as any static host would, and beside it a link of its
own, which the page offers as "the local server's" when it finds it:

every request whose query carries link=1 is sent through one link of a set rate in bytes per second, shared by all
such requests at once (each connection takes its turn chunk by chunk, so N connections share the rate fairly). A
chunk is written when its slot on the link has passed, so the bytes leave at the set rate; a slot may start up to
0.1 s in the past (five chunks' time where chunks are capped, above 25.6 Mbit/s), so a sender that wakes late makes
the time up (a token bucket that deep). The page sets the rate with POST link {"rate": BYTES_PER_SECOND} (0: no
limit). Every chunk sent is recorded (GET link/log; POST link/reset clears it) so the rate the page shows can be
checked against the bytes really sent. HTTP headers are not counted or limited; only bodies are.

The page's own link (site/link.js) follows the same rule inside the browser; this server is the reference the
proofs compare it with, and the way to limit the real transfer rather than its release to the page.

Outside input is data: paths are resolved under the served folders. Our code, BSD 2-clause."""
import argparse
import http.server
import json
import os
import threading
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
         '.wgsl': 'text/plain; charset=utf-8', '.wasm': 'application/wasm', '.gltf': 'model/gltf+json',
         '.bin': 'application/octet-stream', '.jpg': 'image/jpeg', '.png': 'image/png', '.mp3': 'audio/mpeg',
         '.p2p': 'text/plain; charset=utf-8', '.json': 'application/json', '.md': 'text/markdown; charset=utf-8',
         '.css': 'text/css; charset=utf-8', '.txt': 'text/plain; charset=utf-8'}


class Link:
    """One link shared by every limited request: a slot of n/rate seconds per chunk, taken in turn. A slot may begin
    up to BURST seconds in the past, so time lost when a sender wakes late (a loaded machine) is made up, as a token
    bucket of BURST seconds' depth does; idle time longer than that is lost, as on a real line."""

    BURST = 0.1

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
                    # the bucket's depth: 0.1 s, or five chunks' time where chunks are capped (above 25.6 Mbit/s)
                    start = max(now - min(self.BURST, 5 * self.chunk() / self.rate), self.free_at)
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
    prefix = '/'

    def log_message(self, fmt, *args):
        pass

    def resolve(self, path):
        """URL path -> file under one of the served folders, or None."""
        path = urllib.parse.unquote(path)
        for prefix, root in self.roots.items():
            if path.startswith(prefix):
                rel = path[len(prefix):]
                if rel == '' or rel.endswith('/'):
                    rel += 'index.html'
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
        if u.path == self.prefix + 'link/log':
            with LINK.lock:
                body = json.dumps({'rate': LINK.rate, 'log': LINK.log}).encode()
            return self.reply(200, body)
        if u.path == self.prefix + 'link':
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
        if u.path == self.prefix + 'link':
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
        if u.path == self.prefix + 'link/reset':
            with LINK.lock:
                LINK.log = []
                LINK.t0 = time.monotonic()
                LINK.free_at = LINK.t0
            return self.reply(200, b'{}')
        return self.reply(404, b'{}')


def main():
    ap = argparse.ArgumentParser(description='Procedural Texture Rendering: the local server')
    ap.add_argument('--port', type=int, default=8537)
    ap.add_argument('--site', default=os.path.join(os.path.dirname(HERE), 'site'))
    ap.add_argument('--prefix', default='/', help='the path the site is served under, for example /demos/ptr/')
    ap.add_argument('--also', action='append', default=[], metavar='PATH=DIR', help='proofs only: one more folder under a path of its own')
    a = ap.parse_args()
    prefix = '/' + a.prefix.strip('/') + '/' if a.prefix.strip('/') else '/'
    H.prefix = prefix
    H.roots = {}
    for extra in a.also:
        p, _, d = extra.partition('=')
        H.roots['/' + p.strip('/') + '/'] = d
    H.roots[prefix] = a.site
    s = http.server.ThreadingHTTPServer(('127.0.0.1', a.port), H)
    s.daemon_threads = True
    print('Procedural Texture Rendering: open http://127.0.0.1:%d%s in a browser on this machine. Stop with Ctrl+C.' % (a.port, prefix), flush=True)
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        print('stopped')


if __name__ == '__main__':
    main()
