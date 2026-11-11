// The thirteen procedures drawn in the browser (ORDER 508, milestone 2c): on WebGPU, every modern operator by its
// WGSL twin (ops/NAME.wgsl after ops/common.wgsl), the whole at full size and as sixteen tiles each through its own
// window; and beside it the WebAssembly build of the same program (p2p.wasm) drawing the same procedure on the
// processor. A werkkzeug3 operator (a seed's Flat and Text) is drawn by the WebAssembly module and handed to the GPU as
// a picture. Results and timings are posted to the page's server. Our code, BSD 2-clause.
//
// The page's address takes: names=A,B (default: every texture in data/list.txt), wasm=0 (leave the WebAssembly path
// out), repeat=N (timed runs after one warm-up, default 3), size=2048, lod=OCTAVES (the canvas's level of detail).
import { Wasi } from './wasi.js';

const Q = new URLSearchParams(location.search);
const REPEAT = +(Q.get('repeat') || 3);
const SIZE = +(Q.get('size') || 2048);
const LOD = +(Q.get('lod') || 99);
const DO_WASM = Q.get('wasm') !== '0';
const TAG = Q.get('tag') || 'run';
let logText = '';
function log(s) { logText += s + '\n'; const e = document.getElementById('log'); if (e) e.textContent = logText; }
async function post(name, body) { await fetch('/save?name=' + encodeURIComponent(name), { method: 'POST', body }); }

const f32 = Math.fround;
const bitsToF = (w) => { const b = new DataView(new ArrayBuffer(4)); b.setUint32(0, w >>> 0, true); return b.getFloat32(0, true); };

// ------------------------------------------------------------------ the script (the fitter's typed words)
const MODERN = { Noise: 'noise', Cells: 'cells', Tiles: 'tiles', Ramp: 'ramp', Layer: 'layer', Shade: 'shade', Scatter: 'scatter', Wear: 'wear', Tint: 'tint', Quad: 'quad' };

function parse(text) {
  const nodes = [];
  const index = new Map();
  let root = -1;
  for (const raw of text.split('\n')) {
    const t = raw.trim().split(/\s+/);
    if (!t[0] || t[0].startsWith('#')) continue;
    if (t[0] === 'out') { root = index.get(t[1]); continue; }
    const nd = { id: t[0], op: t[1], ins: [], words: [], strs: [], line: raw.trim() };
    if (t[2] !== '-') for (const n of t[2].split(',')) {
      if (!index.has(n)) throw new Error(`${t[0]}: input ${n} is not defined above it`);
      nd.ins.push(index.get(n));
    }
    for (const w of t.slice(3)) { if (w.startsWith('s=')) nd.strs.push(w); else nd.words.push(parseInt(w, 16) >>> 0); }
    index.set(t[0], nodes.length);
    nodes.push(nd);
  }
  if (root < 0) throw new Error('no out line');
  return { nodes, root };
}

// the reach of a node's neighbourhood in parts of the picture (modern.zig's marginOf): Shade one pixel, Wear its radius
// or its drips' length; the canvas is drawn that much wider (p2p.zig's drawCanvas, in single precision as there)
function marginOf(nd) {
  if (nd.op === 'Shade') return f32(1e-9);
  if (nd.op === 'Wear') return f32(bitsToF(nd.words[1] === 2 ? nd.words[3] : nd.words[2]));
  return 0;
}
function canvasFor(g, side, win, mForced) {
  let reach = f32(0);
  let any = false;
  for (let i = 0; i <= g.root; i++) {
    const nd = g.nodes[i];
    if (!MODERN[nd.op]) continue;
    const r = marginOf(nd);
    if (r > 0) any = true;
    reach = f32(reach + r);
  }
  const pxs = f32(f32(win.s) / f32(side));
  let m = any ? Math.ceil(f32(reach / pxs)) + 2 : 0;
  m = (m + 1) & ~1;
  if (mForced !== undefined) m = mForced;
  return { w: side + 2 * m, h: side + 2 * m, m, wx: win.x, wy: win.y, ws: win.s, side };
}

function needed(g) {
  const need = new Array(g.nodes.length).fill(false);
  need[g.root] = true;
  for (let i = g.root; i >= 0; i--) if (need[i]) for (const k of g.nodes[i].ins) need[k] = true;
  return need;
}

// ------------------------------------------------------------------ the WebAssembly module (the processor's path)
let wasmModule = null;
let files = null;

async function runWasm(args) {
  const w = new Wasi(['p2p', ...args], ['WZ_FONTMAP=', 'WZ_FONTINDEX=/data/fonts/candidates.tsv', 'WZ_GLYPHINDEX='], files);
  const code = await w.run(wasmModule);
  return { code, out: w.out, written: w.written };
}

function ppmToRgb(bytes) {
  // P6 W H 255, then the bytes
  let p = 0, fields = [];
  while (fields.length < 4) {
    while (bytes[p] === 32 || bytes[p] === 10 || bytes[p] === 13 || bytes[p] === 9) p++;
    let s = '';
    while (bytes[p] !== 32 && bytes[p] !== 10 && bytes[p] !== 13 && bytes[p] !== 9) s += String.fromCharCode(bytes[p++]);
    fields.push(s);
  }
  p++;
  return { w: +fields[1], h: +fields[2], rgb: bytes.subarray(p, p + (+fields[1]) * (+fields[2]) * 3) };
}

// a werkkzeug3 node (and what it reads) drawn by the WebAssembly module at its own size: a seed's stamp
const stampCache = new Map();
async function stampOf(g, k) {
  const key = g.nodes[k].line;
  if (stampCache.has(key)) return stampCache.get(key);
  const keep = new Set();
  const visit = (i) => { if (keep.has(i)) return; keep.add(i); for (const j of g.nodes[i].ins) visit(j); };
  visit(k);
  const lines = [...keep].sort((a, b) => a - b).map((i) => g.nodes[i].line);
  for (const i of keep) if (MODERN[g.nodes[i].op]) throw new Error(`the stamp ${g.nodes[k].id} reads a modern operator; not drawn here`);
  const sub = lines.join('\n') + `\nout ${g.nodes[k].id}\n`;
  files.set('/work/stamp.script', new TextEncoder().encode(sub));
  const r = await runWasm(['render', '/work/stamp.script', '/work/stamp.ppm']);
  if (r.code !== 0 || !r.written.has('/work/stamp.ppm')) throw new Error('the stamp did not draw: ' + r.out);
  const im = ppmToRgb(r.written.get('/work/stamp.ppm'));
  // back to 15 bits (the 8-bit picture is the 15-bit one shifted by 7: the stamp is read as a coverage, its grey)
  const px = new Uint32Array(im.w * im.h * 2);
  for (let i = 0; i < im.w * im.h; i++) {
    const r8 = im.rgb[3 * i], g8 = im.rgb[3 * i + 1], b8 = im.rgb[3 * i + 2];
    const q = (v) => Math.min(32767, Math.round(v * 32767 / 255));
    px[2 * i] = q(b8) | (q(g8) << 16);
    px[2 * i + 1] = q(r8) | (32767 << 16);
  }
  const st = { w: im.w, h: im.h, px };
  stampCache.set(key, st);
  return st;
}

// ------------------------------------------------------------------ the GPU
let device = null;
const pipes = new Map();

async function pipeline(op) {
  if (pipes.has(op)) return pipes.get(op);
  const src = (await (await fetch('ops/common.wgsl')).text()) + '\n' + (await (await fetch(`ops/${MODERN[op]}.wgsl`)).text());
  const module = device.createShaderModule({ code: src });
  const info = await module.getCompilationInfo();
  for (const m of info.messages) if (m.type === 'error') throw new Error(`${op}.wgsl ${m.lineNum}:${m.linePos} ${m.message}`);
  const p = await device.createComputePipelineAsync({ layout: 'auto', compute: { module, entryPoint: 'main' } });
  pipes.set(op, p);
  return p;
}

function uniform(cv, nd, nin, pass, sw, sh) {
  const b = new ArrayBuffer(48 + 128);
  const v = new DataView(b);
  v.setUint32(0, cv.w, true); v.setUint32(4, cv.h, true); v.setUint32(8, cv.m, true); v.setUint32(12, LOD, true);
  v.setFloat32(16, cv.wx, true); v.setFloat32(20, cv.wy, true); v.setFloat32(24, cv.ws, true); v.setUint32(28, nin, true);
  v.setUint32(32, sw, true); v.setUint32(36, sh, true); v.setUint32(40, pass, true); v.setUint32(44, nd.words.length, true);
  nd.words.forEach((w, i) => v.setUint32(48 + 4 * i, w, true));
  const buf = device.createBuffer({ size: b.byteLength, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
  device.queue.writeBuffer(buf, 0, b);
  return buf;
}

// Draw the procedure on the canvas of side pixels showing window win: encode every needed node, submit once, wait
// for the GPU; the root's buffer and the canvas. Buffers are freed after their last reader.
async function drawGpu(g, side, win, mForced) {
  if (g.nodes[g.root].op === 'Quad') return drawQuadGpu(g, side, win);
  for (let i = 0; i < g.root; i++) if (g.nodes[i].op === 'Quad') throw new Error('a Quad is the procedure\'s last operator');
  const cv = canvasFor(g, side, win, mForced);
  const need = needed(g);
  const readers = new Array(g.nodes.length).fill(0);
  for (let i = 0; i <= g.root; i++) if (need[i]) for (const k of g.nodes[i].ins) readers[k]++;
  const bufs = new Array(g.nodes.length).fill(null);
  const stamps = new Array(g.nodes.length).fill(null);
  const size = cv.w * cv.h * 8;
  const enc = device.createCommandEncoder();
  const transient = [];
  const pool = [];
  const dummy = device.createBuffer({ size: 16, usage: GPUBufferUsage.STORAGE });
  transient.push(dummy);
  for (let i = 0; i <= g.root; i++) {
    if (!need[i]) continue;
    const nd = g.nodes[i];
    if (!MODERN[nd.op]) {
      const st = await stampOf(g, i);
      const b = device.createBuffer({ size: st.px.byteLength, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST });
      device.queue.writeBuffer(b, 0, st.px);
      stamps[i] = { buf: b, w: st.w, h: st.h };
      transient.push(b);
      continue;
    }
    const p = await pipeline(nd.op);
    const out = pool.pop() || device.createBuffer({ size, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC });
    bufs[i] = out;
    const ins = nd.ins.map((k) => bufs[k]);
    let sw = 0, sh = 0;
    const entries = (ub) => {
      const e = [{ binding: 0, resource: { buffer: ub } }, { binding: 1, resource: { buffer: out } }];
      if (nd.op === 'Scatter') {
        e.push({ binding: 2, resource: { buffer: bufs[nd.ins[0]] } });
        e.push({ binding: 3, resource: { buffer: nd.ins.length >= 2 ? stamps[nd.ins[1]].buf : dummy } });
      } else if (nd.op === 'Wear') {
        e.push({ binding: 2, resource: { buffer: ins[0] } });
        e.push({ binding: 3, resource: { buffer: nd.ins.length >= 2 ? ins[1] : ins[0] } });
        e.push({ binding: 4, resource: { buffer: wtmp } });
      } else {
        ins.forEach((b, k) => e.push({ binding: 2 + k, resource: { buffer: b } }));
      }
      return e;
    };
    if (nd.op === 'Scatter' && nd.ins.length >= 2) { sw = stamps[nd.ins[1]].w; sh = stamps[nd.ins[1]].h; }
    for (const k of nd.ins) if (!MODERN[g.nodes[k].op] && !(nd.op === 'Scatter' && k === nd.ins[1])) throw new Error(`${nd.id} reads the werkkzeug3 picture ${g.nodes[k].id} on the canvas; only a Scatter's stamp may be one`);
    let wtmp = null;
    if (nd.op === 'Wear') { wtmp = device.createBuffer({ size: cv.w * cv.h * 4, usage: GPUBufferUsage.STORAGE }); transient.push(wtmp); }
    const passes = nd.op === 'Wear' ? 2 : 1;
    for (let ps = 0; ps < passes; ps++) {
      const ub = uniform(cv, nd, nd.ins.length, ps, sw, sh);
      transient.push(ub);
      const bg = device.createBindGroup({ layout: p.getBindGroupLayout(0), entries: entries(ub) });
      const cp = enc.beginComputePass();
      cp.setPipeline(p);
      cp.setBindGroup(0, bg);
      cp.dispatchWorkgroups(Math.ceil(cv.w / 8), Math.ceil(cv.h / 8));
      cp.end();
    }
    for (const k of nd.ins) if (--readers[k] === 0 && bufs[k]) { pool.push(bufs[k]); bufs[k] = null; }
  }
  const t0 = performance.now();
  device.queue.submit([enc.finish()]);
  await device.queue.onSubmittedWorkDone();
  const t = performance.now() - t0;
  for (const b of transient) b.destroy();
  for (const b of pool) b.destroy();
  return { buf: bufs[g.root], cv, ms: t };
}

// one input of a Quad as a procedure of its own: the nodes it needs, renumbered (p2p.zig's quadPart)
function quadPart(g, r) {
  const keep = new Set();
  const visit = (i) => { if (keep.has(i)) return; keep.add(i); for (const j of g.nodes[i].ins) visit(j); };
  visit(r);
  const order = [...keep].sort((a, b) => a - b);
  const map = new Map(order.map((i, k) => [i, k]));
  const nodes = order.map((i) => ({ ...g.nodes[i], ins: g.nodes[i].ins.map((j) => map.get(j)) }));
  return { nodes, root: map.get(r) };
}

// Four procedures per picture (milestone 2d; p2p.zig's drawQuad): input q drawn on its own canvas, at the place
// 2x - column, 2y - row, every canvas of one side and margin; then the Quad pass lays them together with its seam.
async function drawQuadGpu(g, side, win) {
  const rt = g.nodes[g.root];
  if (rt.ins.length !== 4) throw new Error(`Quad takes four procedures, the graph gives ${rt.ins.length}`);
  const subs = rt.ins.map((k) => quadPart(g, k));
  const local = { x: 0, y: 0, s: f32(2 * win.s) };
  let m = 0;
  for (const sg of subs) m = Math.max(m, canvasFor(sg, side, local).m);
  const parts = [];
  let ms = 0;
  for (let q = 0; q < 4; q++) {
    const r = await drawGpu(subs[q], side, { x: f32(f32(2 * win.x) - (q % 2)), y: f32(f32(2 * win.y) - (q >> 1)), s: f32(2 * win.s) }, m);
    parts.push(r.buf);
    ms += r.ms;
  }
  const cv = { w: side + 2 * m, h: side + 2 * m, m, wx: win.x, wy: win.y, ws: win.s, side };
  const p = await pipeline('Quad');
  const out = device.createBuffer({ size: cv.w * cv.h * 8, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC });
  const ub = uniform(cv, rt, 4, 0, 0, 0);
  const entries = [{ binding: 0, resource: { buffer: ub } }, { binding: 1, resource: { buffer: out } }];
  parts.forEach((b, k) => entries.push({ binding: 2 + k, resource: { buffer: b } }));
  const enc = device.createCommandEncoder();
  const cp = enc.beginComputePass();
  cp.setPipeline(p);
  cp.setBindGroup(0, device.createBindGroup({ layout: p.getBindGroupLayout(0), entries }));
  cp.dispatchWorkgroups(Math.ceil(cv.w / 8), Math.ceil(cv.h / 8));
  cp.end();
  const t0 = performance.now();
  device.queue.submit([enc.finish()]);
  await device.queue.onSubmittedWorkDone();
  ms += performance.now() - t0;
  ub.destroy();
  for (const b of parts) b.destroy();
  return { buf: out, cv, ms };
}

async function readRgb(res) {
  const { buf, cv } = res;
  const rb = device.createBuffer({ size: cv.w * cv.h * 8, usage: GPUBufferUsage.MAP_READ | GPUBufferUsage.COPY_DST });
  const enc = device.createCommandEncoder();
  enc.copyBufferToBuffer(buf, 0, rb, 0, cv.w * cv.h * 8);
  device.queue.submit([enc.finish()]);
  await rb.mapAsync(GPUMapMode.READ);
  const px = new Uint32Array(rb.getMappedRange().slice(0));
  rb.unmap();
  rb.destroy();
  buf.destroy();
  const s = cv.side;
  const rgb = new Uint8Array(s * s * 3);
  for (let j = 0; j < s; j++) for (let i = 0; i < s; i++) {
    const k = (j + cv.m) * cv.w + i + cv.m;
    const lo = px[2 * k], hi = px[2 * k + 1];
    const o = 3 * (j * s + i);
    rgb[o] = Math.min(255, (hi & 0xffff) >> 7);
    rgb[o + 1] = Math.min(255, (lo >>> 16) >> 7);
    rgb[o + 2] = Math.min(255, (lo & 0xffff) >> 7);
  }
  return rgb;
}

async function pngOf(rgb, w, h) {
  const c = new OffscreenCanvas(w, h);
  const ctx = c.getContext('2d');
  const id = ctx.createImageData(w, h);
  for (let i = 0; i < w * h; i++) { id.data[4 * i] = rgb[3 * i]; id.data[4 * i + 1] = rgb[3 * i + 1]; id.data[4 * i + 2] = rgb[3 * i + 2]; id.data[4 * i + 3] = 255; }
  ctx.putImageData(id, 0, 0);
  return await c.convertToBlob({ type: 'image/png' });
}

async function sha256(bytes) {
  const d = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
  return [...d].map((x) => x.toString(16).padStart(2, '0')).join('');
}

function median(a) { const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; }

// ------------------------------------------------------------------ the run
async function main() {
  const result = { tag: TAG, ua: navigator.userAgent, size: SIZE, lod: LOD, repeat: REPEAT, textures: {} };
  try {
    const list = (await (await fetch('data/list.txt')).text()).trim().split('\n');
    const names = Q.get('names') ? Q.get('names').split(',') : list;
    files = new Map();
    for (const f of (await (await fetch('data/files.txt')).text()).trim().split('\n')) {
      const [path, url] = f.split('\t');
      files.set(path, new Uint8Array(await (await fetch(url)).arrayBuffer()));
    }
    wasmModule = await WebAssembly.compileStreaming(fetch('data/p2p.wasm'));
    if (!navigator.gpu) throw new Error('this browser offers no WebGPU (navigator.gpu is missing)');
    const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
    if (!adapter) throw new Error('WebGPU gave no adapter');
    result.adapter = { vendor: adapter.info.vendor, architecture: adapter.info.architecture, device: adapter.info.device, description: adapter.info.description };
    log(`adapter: ${JSON.stringify(result.adapter)}`);
    if (adapter.info.architecture === 'swiftshader' || adapter.info.isFallbackAdapter) {
      // said, not hidden: the drawings are right on a software adapter, but its timings are the processor's
      result.software = true;
      log('the adapter is a software one (SwiftShader): the drawings are right, the timings are not the GPU\'s; on NVIDIA run the browser with a display (see run-browser.sh, XVFB=1)');
    }
    device = await adapter.requestDevice({ requiredLimits: { maxStorageBufferBindingSize: adapter.limits.maxStorageBufferBindingSize, maxBufferSize: adapter.limits.maxBufferSize } });
    device.lost.then((i) => log('device lost: ' + i.message));
    for (const name of names) {
      const text = await (await fetch(`data/${name}.script`)).text();
      const g = parse(text);
      const r = { operators: g.nodes.length };
      // WebGPU: the whole, one warm-up (shaders compiled, stamps drawn), then timed runs
      let res = await drawGpu(g, SIZE, { x: 0, y: 0, s: 1 });
      res.buf.destroy();
      const tw = [];
      for (let k = 0; k < REPEAT; k++) { res = await drawGpu(g, SIZE, { x: 0, y: 0, s: 1 }); tw.push(res.ms); if (k < REPEAT - 1) res.buf.destroy(); }
      r.gpu_whole_ms = tw;
      const rgb = await readRgb(res);
      await post(`${TAG}-${name}-webgpu.png`, await pngOf(rgb, SIZE, SIZE));
      // WebGPU: the sixteen tiles, each through its own window, put together
      const T = SIZE / 4;
      const tiles = new Uint8Array(SIZE * SIZE * 3);
      const tt = [];
      for (let k = 0; k <= REPEAT; k++) {
        let total = 0;
        for (let rr = 0; rr < 4; rr++) for (let cc = 0; cc < 4; cc++) {
          const rt = await drawGpu(g, T, { x: cc / 4, y: rr / 4, s: 0.25 });
          total += rt.ms;
          if (k === REPEAT) {
            const t = await readRgb(rt);
            for (let j = 0; j < T; j++) tiles.set(t.subarray(j * T * 3, (j + 1) * T * 3), ((rr * T + j) * SIZE + cc * T) * 3);
          } else rt.buf.destroy();
        }
        if (k > 0) tt.push(total);
      }
      r.gpu_tiles_ms = tt;
      await post(`${TAG}-${name}-webgpu-tiles.png`, await pngOf(tiles, SIZE, SIZE));
      // the WebAssembly module: the whole and the tiles, on the processor, in this page
      if (DO_WASM) {
        files.set(`/work/${name}.script`, new TextEncoder().encode(text));
        const exp = Math.round(Math.log2(SIZE));
        let t0 = performance.now();
        const w = await runWasm(['render', `/work/${name}.script`, `/work/${name}.ppm`, String(exp)]);
        r.wasm_whole_ms = performance.now() - t0;
        if (w.code !== 0) throw new Error(`${name}: the WebAssembly drawing failed: ${w.out}`);
        const ppm = w.written.get(`/work/${name}.ppm`);
        r.wasm_whole_sha256 = await sha256(ppm);
        const im = ppmToRgb(ppm);
        await post(`${TAG}-${name}-wasm.png`, await pngOf(im.rgb, im.w, im.h));
        t0 = performance.now();
        r.wasm_tiles_sha256 = [];
        for (let rr = 0; rr < 4; rr++) for (let cc = 0; cc < 4; cc++) {
          const wt = await runWasm(['render', `/work/${name}.script`, `/work/${name}-t.ppm`, String(exp - 2), `window=${cc / 4},${rr / 4},0.25`]);
          if (wt.code !== 0) throw new Error(`${name}: a WebAssembly tile failed: ${wt.out}`);
          r.wasm_tiles_sha256.push(await sha256(wt.written.get(`/work/${name}-t.ppm`)));
        }
        r.wasm_tiles_ms = performance.now() - t0;
      }
      log(`${name}: WebGPU whole ${median(tw).toFixed(1)} ms, 16 tiles ${median(tt).toFixed(1)} ms` + (DO_WASM ? `, WebAssembly whole ${r.wasm_whole_ms.toFixed(0)} ms, 16 tiles ${r.wasm_tiles_ms.toFixed(0)} ms` : ''));
      result.textures[name] = r;
      await post(`${TAG}-result.json`, JSON.stringify(result, null, 1));
    }
  } catch (e) {
    result.error = String(e && e.stack || e);
    log('FAILED: ' + result.error);
  }
  await post(`${TAG}-result.json`, JSON.stringify(result, null, 1));
  await post(`${TAG}-log.txt`, logText);
  await fetch('/done', { method: 'POST', body: result.error ? 'failed' : 'ok' });
}

main();
