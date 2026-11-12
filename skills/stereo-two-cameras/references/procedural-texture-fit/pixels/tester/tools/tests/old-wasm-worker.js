// The present WebAssembly player (ORDER 508's p2p.wasm, the whole fitter built for wasm32-wasi, 22.4 MB) as the
// eleventh round's page ran it, kept only for the same-bytes proof of the slim player. The module and the WASI shim
// are named by the test page.
let module = null, Wasi = null;

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
      ({ Wasi } = await import(m.wasi));     // the WASI shim of the eighth round (pixels/web/wasi.js)
      module = await WebAssembly.compile(await (await fetch(m.url)).arrayBuffer());
      self.postMessage({ kind: 'ready', ms: performance.now() - t0 });
      return;
    }
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
