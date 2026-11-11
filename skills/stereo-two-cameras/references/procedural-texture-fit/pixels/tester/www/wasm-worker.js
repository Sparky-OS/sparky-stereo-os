// The WebAssembly procedure player of the scene tester (ORDER 508, milestone 3), in a worker so the page stays live:
// the fitter's own program (p2p.wasm, milestone 2e's build) draws one piece (a procedure at a size through a window)
// per message, with milestone 2c's WASI shim. The page sends no more work for a texture once its picture is in, and
// ends this worker when the last procedure has stopped. Our code, BSD 2-clause.
import { Wasi } from './web/wasi.js';

let module = null;

function ppmToRgb(bytes) {
  let p = 0;
  const fields = [];
  while (fields.length < 4) {
    while (bytes[p] === 32 || bytes[p] === 10 || bytes[p] === 13 || bytes[p] === 9) p++;
    let s = '';
    while (bytes[p] !== 32 && bytes[p] !== 10 && bytes[p] !== 13 && bytes[p] !== 9) s += String.fromCharCode(bytes[p++]);
    fields.push(s);
  }
  p++;
  const w = +fields[1], h = +fields[2];
  return { w, h, rgb: bytes.slice(p, p + w * h * 3) };
}

self.onmessage = async (ev) => {
  const m = ev.data;
  try {
    if (m.kind === 'init') {
      const t0 = performance.now();
      module = await WebAssembly.compileStreaming(fetch(m.url));
      self.postMessage({ kind: 'ready', ms: performance.now() - t0 });
      return;
    }
    // a piece: side = 2^exp pixels, through window (x, y, s)
    const files = new Map([['/work/p.script', new TextEncoder().encode(m.script)]]);
    const args = ['render', '/work/p.script', '/work/p.ppm', String(m.exp)];
    if (m.win && !(m.win.x === 0 && m.win.y === 0 && m.win.s === 1)) args.push(`window=${m.win.x},${m.win.y},${m.win.s}`);
    const w = new Wasi(['p2p', ...args], ['WZ_FONTMAP=', 'WZ_FONTINDEX=', 'WZ_GLYPHINDEX='], files);
    const t0 = performance.now();
    const code = await w.run(module);
    const ms = performance.now() - t0;
    if (code !== 0 || !w.written.has('/work/p.ppm')) throw new Error('p2p exited ' + code + ': ' + w.out.slice(-300));
    const im = ppmToRgb(w.written.get('/work/p.ppm'));
    self.postMessage({ kind: 'piece', id: m.id, rgb: im.rgb, w: im.w, h: im.h, ms }, [im.rgb.buffer]);
  } catch (e) {
    self.postMessage({ kind: 'error', id: m.id, error: String(e && e.message || e) });
  }
};
