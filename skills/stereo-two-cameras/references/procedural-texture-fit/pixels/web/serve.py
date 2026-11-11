#!/usr/bin/env python3
"""The page's server inside the browser container: serves ROOT read-only and saves what the page posts.

serve.py ROOT OUTDIR PORT
GET  /...            files under ROOT (the page, its scripts, the procedures, the module, the fonts)
POST /save?name=X    the body is written to OUTDIR/X (X: letters, digits, dot, dash, underscore only)
POST /done           writes OUTDIR/DONE and stops the server
Outside input is data: the name is checked, never used as a path beyond OUTDIR."""
import http.server, os, re, sys, threading, urllib.parse

root, outdir, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
os.makedirs(outdir, exist_ok=True)
NAME = re.compile(r'^[A-Za-z0-9._-]{1,120}$')


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=root, **k)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(n) if n > 0 else b''
        if u.path == '/save':
            q = urllib.parse.parse_qs(u.query)
            name = q.get('name', [''])[0]
            if not NAME.match(name):
                self.send_response(400)
                self.end_headers()
                return
            with open(os.path.join(outdir, name), 'wb') as f:
                f.write(body)
            self.send_response(200)
            self.end_headers()
            return
        if u.path == '/done':
            with open(os.path.join(outdir, 'DONE'), 'wb') as f:
                f.write(body)
            self.send_response(200)
            self.end_headers()
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        self.send_response(404)
        self.end_headers()


http.server.SimpleHTTPRequestHandler.extensions_map['.wasm'] = 'application/wasm'
http.server.SimpleHTTPRequestHandler.extensions_map['.wgsl'] = 'text/plain'
s = http.server.ThreadingHTTPServer(('127.0.0.1', port), H)
s.serve_forever()
