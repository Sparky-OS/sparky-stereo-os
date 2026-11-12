// A small WASI (preview 1) for running the fitter's WebAssembly build (p2p.wasm, a wasm32-wasi command) in the
// browser: the seventeen calls it imports, over files held in memory. Files given are read only; files the program
// creates are kept in `written`. Our code, BSD 2-clause.
'use strict';

const E = { SUCCESS: 0, BADF: 8, INVAL: 28, NOENT: 44, NOSYS: 52 };

class Exit extends Error {
  constructor(code) { super('exit ' + code); this.code = code; }
}

export class Wasi {
  constructor(args, env, files) {
    this.args = args;
    this.env = env;
    this.files = files;          // Map: absolute path -> Uint8Array
    this.written = new Map();    // what the program wrote
    this.out = '';
    this.fds = new Map();        // fd -> { path, data, pos, w }
    this.next = 4;
    this.mem = null;
  }
  view() { return new DataView(this.mem.buffer); }
  bytes() { return new Uint8Array(this.mem.buffer); }
  str(p, n) { return new TextDecoder().decode(this.bytes().slice(p, p + n)); }
  resolve(p) {
    const parts = [];
    for (const s of p.split('/')) {
      if (s === '' || s === '.') continue;
      if (s === '..') parts.pop(); else parts.push(s);
    }
    return '/' + parts.join('/');
  }
  isDir(p) {
    if (p === '/') return true;
    const pre = p.endsWith('/') ? p : p + '/';
    for (const k of this.files.keys()) if (k.startsWith(pre)) return true;
    return false;
  }
  strs(list, ptrs, buf) {
    const v = this.view(), b = this.bytes();
    let o = buf;
    list.forEach((s, i) => {
      const e = new TextEncoder().encode(s);
      v.setUint32(ptrs + 4 * i, o, true);
      b.set(e, o);
      b[o + e.length] = 0;
      o += e.length + 1;
    });
    return E.SUCCESS;
  }
  sizes(list, cp, sp) {
    const v = this.view();
    v.setUint32(cp, list.length, true);
    v.setUint32(sp, list.reduce((a, s) => a + new TextEncoder().encode(s).length + 1, 0), true);
    return E.SUCCESS;
  }
  imports() {
    const self = this;
    return {
      args_get: (p, b) => self.strs(self.args, p, b),
      args_sizes_get: (c, s) => self.sizes(self.args, c, s),
      environ_get: (p, b) => self.strs(self.env, p, b),
      environ_sizes_get: (c, s) => self.sizes(self.env, c, s),
      clock_time_get: (id, prec, tp) => { self.view().setBigUint64(tp, BigInt(Math.round(performance.now() * 1e6)), true); return E.SUCCESS; },
      fd_fdstat_get: (fd, buf) => {
        const v = self.view();
        let type = 4;
        if (fd <= 2) type = 2; else if (fd === 3) type = 3; else if (!self.fds.has(fd)) return E.BADF;
        v.setUint8(buf, type);
        v.setUint16(buf + 2, 0, true);
        v.setBigUint64(buf + 8, 0xffffffffffffffffn, true);
        v.setBigUint64(buf + 16, 0xffffffffffffffffn, true);
        return E.SUCCESS;
      },
      fd_fdstat_set_flags: () => E.SUCCESS,
      fd_prestat_get: (fd, buf) => {
        if (fd !== 3) return E.BADF;
        const v = self.view();
        v.setUint8(buf, 0);
        v.setUint32(buf + 4, 1, true);
        return E.SUCCESS;
      },
      fd_prestat_dir_name: (fd, p, n) => { if (fd !== 3) return E.BADF; self.bytes()[p] = 47; return E.SUCCESS; },
      path_open: (dirfd, dirflags, pp, pl, oflags, rb, ri, fdflags, fdp) => {
        if (dirfd !== 3) return E.BADF;
        const path = self.resolve(self.str(pp, pl));
        let data;
        const creat = (oflags & 1) !== 0, trunc = (oflags & 8) !== 0;
        if (self.written.has(path)) data = self.written.get(path);
        else if (self.files.has(path)) data = self.files.get(path);
        if (data === undefined && !creat) return self.isDir(path) ? (self.fds.set(self.next, { path, data: new Uint8Array(0), pos: 0, w: false, dir: true }), self.view().setUint32(fdp, self.next++, true), E.SUCCESS) : E.NOENT;
        if (creat || trunc) data = trunc || data === undefined ? new Uint8Array(0) : data;
        const fd = self.next++;
        self.fds.set(fd, { path, data, pos: 0, w: creat || trunc, len: data.length });
        self.view().setUint32(fdp, fd, true);
        return E.SUCCESS;
      },
      path_filestat_get: (fd, flags, pp, pl, buf) => {
        const path = self.resolve(self.str(pp, pl));
        const data = self.written.get(path) || self.files.get(path);
        const v = self.view();
        for (let k = 0; k < 64; k += 8) v.setBigUint64(buf + k, 0n, true);
        if (data === undefined) {
          if (!self.isDir(path)) return E.NOENT;
          v.setUint8(buf + 16, 3);
          return E.SUCCESS;
        }
        v.setUint8(buf + 16, 4);
        v.setBigUint64(buf + 32, BigInt(data.length), true);
        return E.SUCCESS;
      },
      fd_readdir: (fd, buf, len, cookie, usedp) => { self.view().setUint32(usedp, 0, true); return E.SUCCESS; },
      fd_read: (fd, iovs, n, nr) => {
        const f = self.fds.get(fd);
        if (!f) { self.view().setUint32(nr, 0, true); return fd === 0 ? E.SUCCESS : E.BADF; }
        const v = self.view(), b = self.bytes();
        let got = 0;
        const end = f.w ? f.len : f.data.length;
        for (let k = 0; k < n; k++) {
          const p = v.getUint32(iovs + 8 * k, true), l = v.getUint32(iovs + 8 * k + 4, true);
          const c = Math.max(0, Math.min(l, end - f.pos));
          b.set(f.data.subarray(f.pos, f.pos + c), p);
          f.pos += c;
          got += c;
          if (c < l) break;
        }
        v.setUint32(nr, got, true);
        return E.SUCCESS;
      },
      fd_write: (fd, iovs, n, nw) => {
        const v = self.view(), b = self.bytes();
        let put = 0;
        for (let k = 0; k < n; k++) {
          const p = v.getUint32(iovs + 8 * k, true), l = v.getUint32(iovs + 8 * k + 4, true);
          const chunk = b.slice(p, p + l);
          if (fd === 1 || fd === 2) self.out += new TextDecoder().decode(chunk);
          else {
            const f = self.fds.get(fd);
            if (!f) return E.BADF;
            if (f.pos + l > f.data.length) {
              const nd = new Uint8Array(Math.max(f.pos + l, f.data.length * 2 + 4096));
              nd.set(f.data.subarray(0, f.len));
              f.data = nd;
            }
            f.data.set(chunk, f.pos);
            f.pos += l;
            f.len = Math.max(f.len, f.pos);
          }
          put += l;
        }
        v.setUint32(nw, put, true);
        return E.SUCCESS;
      },
      fd_seek: (fd, off, whence, np) => {
        const f = self.fds.get(fd);
        if (!f) return E.BADF;
        const end = f.w ? f.len : f.data.length;
        const o = Number(off);
        f.pos = whence === 0 ? o : whence === 1 ? f.pos + o : end + o;
        self.view().setBigUint64(np, BigInt(f.pos), true);
        return E.SUCCESS;
      },
      fd_close: (fd) => {
        const f = self.fds.get(fd);
        if (!f) return E.BADF;
        if (f.w) self.written.set(f.path, f.data.slice(0, f.len));
        self.fds.delete(fd);
        return E.SUCCESS;
      },
      proc_exit: (code) => { throw new Exit(code); },
    };
  }
  // run the command once on a compiled module; the exit code and what it printed
  async run(module) {
    const inst = await WebAssembly.instantiate(module, { wasi_snapshot_preview1: this.imports() });
    this.mem = inst.exports.memory;
    try {
      inst.exports._start();
      return 0;
    } catch (e) {
      if (e instanceof Exit) return e.code;
      throw e;
    } finally {
      // files the program left open are kept as written
      for (const f of this.fds.values()) if (f.w) this.written.set(f.path, f.data.slice(0, f.len));
      this.fds.clear();
    }
  }
}
