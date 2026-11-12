// The page's two players against each other (ORDER 537): every procedure of the scene drawn whole at 256 pixels and
// in sixteen 512 pixel tiles (what the page draws) by the WebGPU player (site/gpu-player.js) and by the WebAssembly
// player (site/player/ptr-player.wasm, which draws the fitter's own bytes); for every piece the largest difference
// of any channel in levels of 255 and the share of pixels that differ. A GPU rounds differently from a processor,
// so the bound is one level; a control draws another window and must differ by many.
import { GpuPlayer, parse } from '../../site/gpu-player.js';
const out = document.getElementById('out');
const say = (s) => { out.textContent += s + '\n'; };
const site = new URL('../../site/', location.href);
window.testerState = () => null;

function wasmPlayer() {
  const w = new Worker(new URL('wasm-worker.js', site), { type: 'module' });
  let next = 1;
  const waiting = new Map();
  const ready = new Promise((resolve, reject) => {
    w.onmessage = (ev) => {
      const m = ev.data;
      if (m.kind === 'ready') { resolve(m); return; }
      const p = waiting.get(m.id);
      if (!p) { if (m.kind === 'error') reject(new Error(m.error)); return; }
      waiting.delete(m.id);
      if (m.kind === 'piece') p.resolve(m); else p.reject(new Error(m.error));
    };
  });
  w.postMessage({ kind: 'init', url: new URL('player/ptr-player.wasm', site).href });
  return { ready, piece: (script, exp, win) => new Promise((resolve, reject) => { const id = next++; waiting.set(id, { resolve, reject }); w.postMessage({ kind: 'piece', id, script, exp, win }); }) };
}
function compare(a, b) {
  let max = 0, px = 0;
  for (let i = 0; i < a.length; i += 3) {
    const d = Math.max(Math.abs(a[i] - b[i]), Math.abs(a[i + 1] - b[i + 1]), Math.abs(a[i + 2] - b[i + 2]));
    if (d) { px++; if (d > max) max = d; }
  }
  return { max, share: px / (a.length / 3) };
}

async function main() {
  const gltf = await (await fetch(new URL('scene/scene.gltf', site))).json();
  const procs = gltf.extensions.KHR_texture_procedural_rendering.procedures;
  const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
  const device = await adapter.requestDevice({ requiredFeatures: adapter.features.has('timestamp-query') ? ['timestamp-query'] : [], requiredLimits: { maxStorageBufferBindingSize: adapter.limits.maxStorageBufferBindingSize, maxBufferSize: adapter.limits.maxBufferSize } });
  const gpu = new GpuPlayer(device, new URL('ops/', site).href);
  const cpu = wasmPlayer();
  await cpu.ready;
  const R = { adapter: [adapter.info.vendor, adapter.info.architecture].filter(Boolean).join(' '), pieces: [], worst: 0, worstShare: 0, control: null };
  for (const p of procs) {
    const text = await (await fetch(new URL('scene/' + p.uri, site))).text();
    const g = parse(text);
    const pieces = [{ label: 'whole at 256', side: 256, win: { x: 0, y: 0, s: 1 } }];
    for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) pieces.push({ label: `tile ${x},${y} of 4x4 at 512`, side: 512, win: { x: x / 4, y: y / 4, s: 0.25 } });
    let worst = 0, share = 0;
    for (const pc of pieces) {
      gpu.owner = p.name; gpu.piece = pc.label;
      const [a, b] = await Promise.all([gpu.drawRgb(g, pc.side, pc.win), cpu.piece(text, Math.log2(pc.side), pc.win)]);
      const c = compare(a, b.rgb);
      R.pieces.push({ procedure: p.name, piece: pc.label, max: c.max, share: +c.share.toFixed(6) });
      worst = Math.max(worst, c.max); share = Math.max(share, c.share);
    }
    R.worst = Math.max(R.worst, worst); R.worstShare = Math.max(R.worstShare, share);
    say(`${p.name}: largest difference ${worst} level(s), on at most ${(100 * share).toFixed(4)} % of a piece's pixels`);
    if (!R.control) {
      const a = await gpu.drawRgb(g, 256, { x: 0.5, y: 0.5, s: 0.5 });
      const b = await cpu.piece(text, 8, { x: 0, y: 0, s: 1 });
      R.control = compare(a, b.rgb);
      say(`control (another window must differ): ${R.control.max} levels on ${(100 * R.control.share).toFixed(1)} % of the pixels`);
    }
  }
  R.pass = R.worst <= 1 && R.control.max > 8;
  say(`${R.pieces.length} pieces on ${R.adapter}: largest difference ${R.worst} level(s): ${R.pass ? 'within one level' : 'OVER one level'}`);
  window.testerResult = JSON.stringify(R);
}
main().catch((e) => { say('failed: ' + (e.stack || e)); window.testerResult = JSON.stringify({ failed: String(e.stack || e), pass: false }); });
