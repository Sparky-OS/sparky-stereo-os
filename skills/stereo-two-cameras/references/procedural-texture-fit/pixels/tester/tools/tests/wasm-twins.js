// The same-bytes proof (ORDER 537): every procedure of the scene drawn whole at 256 pixels and in sixteen 512 pixel
// tiles (what the page draws) by the slim player (site/player/ptr-player.wasm) and by the present one (ORDER 508's
// p2p.wasm); the two results of every piece are compared byte for byte. A negative control draws one piece through
// another window and must differ. The driver reads window.testerResult.
const Q = new URLSearchParams(location.search);
const out = document.getElementById('out');
const say = (s) => { out.textContent += s + '\n'; };
const site = new URL('../../site/', location.href);

function player(workerUrl, wasmUrl, wasiUrl) {
  const w = new Worker(workerUrl, { type: 'module' });
  let next = 1;
  const waiting = new Map();
  const ready = new Promise((resolve, reject) => {
    w.onmessage = (ev) => {
      const m = ev.data;
      if (m.kind === 'ready') { resolve(m); return; }
      if (m.id == null && m.kind === 'error') { reject(new Error(m.error)); return; }
      const p = waiting.get(m.id);
      if (!p) return;
      waiting.delete(m.id);
      if (m.kind === 'piece') p.resolve(m); else p.reject(new Error(m.error));
    };
    w.onerror = (e) => reject(new Error(e.message));
  });
  w.postMessage({ kind: 'init', url: wasmUrl, wasi: wasiUrl });
  return { ready, piece: (script, exp, win) => new Promise((resolve, reject) => { const id = next++; waiting.set(id, { resolve, reject }); w.postMessage({ kind: 'piece', id, script, exp, win }); }) };
}

const hex = async (u8) => [...new Uint8Array(await crypto.subtle.digest('SHA-256', u8))].map((b) => b.toString(16).padStart(2, '0')).join('');
function differ(a, b) {
  if (a.length !== b.length) return -1;
  let n = 0;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) n++;
  return n;
}

async function main() {
  const R = { pieces: [], same: 0, different: 0, control: null, slimBytes: null, t0: performance.now() };
  const gltf = await (await fetch(new URL('scene/scene.gltf', site))).json();
  const procs = gltf.extensions.KHR_texture_procedural_rendering.procedures;
  const slim = player(new URL('wasm-worker.js', site), new URL('player/ptr-player.wasm', site).href);
  // the other player: the present one (ORDER 508's), or with other=URL another build of the slim one (for timing)
  // present=URL and wasi=URL name the fitter's own WebAssembly build and its WASI shim (the defaults are where this
  // work keeps its copy of the eleventh round's; in the skill's tree: the module built by pixels/build.sh with
  // P2P_TARGET=wasm32-wasi, and wasi=../../../web/wasi.js)
  const present = new URL(Q.get('present') || '../../from508/tester/player/p2p.wasm', location.href).href;
  const wasi = new URL(Q.get('wasi') || '../../from508/web/wasi.js', location.href).href;
  const old = Q.get('other')
    ? player(new URL('wasm-worker.js', site), new URL(Q.get('other'), location.href).href)
    : player(new URL('old-wasm-worker.js', location.href), present, wasi);
  R.other = Q.get('other') || 'the present player (p2p.wasm)';
  const [a] = await Promise.all([slim.ready, old.ready]);
  R.slimBytes = a.bytes;
  const tiles = Q.get('tiles') === '0' ? 0 : 4;
  for (const p of procs) {
    const text = await (await fetch(new URL('scene/' + p.uri, site))).text();
    const pieces = [{ label: 'whole at 256', exp: 8, win: { x: 0, y: 0, s: 1 } }];
    for (let y = 0; y < tiles; y++) for (let x = 0; x < tiles; x++) pieces.push({ label: `tile ${x},${y} of 4x4 at 512`, exp: 9, win: { x: x / 4, y: y / 4, s: 1 / 4 } });
    for (const pc of pieces) {
      const [s, o] = await Promise.all([slim.piece(text, pc.exp, pc.win), old.piece(text, pc.exp, pc.win)]);
      const d = differ(s.rgb, o.rgb);
      const rec = { procedure: p.name, piece: pc.label, bytes: s.rgb.length, differing: d, sha256: await hex(s.rgb), sha256Present: await hex(o.rgb), msSlim: Math.round(s.ms), msPresent: Math.round(o.ms) };
      R.pieces.push(rec);
      if (d === 0) R.same++; else R.different++;
      say(`${d === 0 ? 'same' : 'DIFFERENT (' + d + ')'}  ${p.name}, ${pc.label}: ${rec.sha256.slice(0, 16)}  slim ${rec.msSlim} ms, present ${rec.msPresent} ms`);
    }
    if (!R.control) {
      // the negative control: the same procedure through another window must not give the same bytes
      const s = await slim.piece(text, 8, { x: 0.5, y: 0.5, s: 0.5 });
      const o = await old.piece(text, 8, { x: 0, y: 0, s: 1 });
      R.control = { procedure: p.name, differing: differ(s.rgb, o.rgb) };
      say(`control (another window must differ): ${R.control.differing} bytes differ`);
    }
  }
  R.seconds = (performance.now() - R.t0) / 1000;
  say(`${R.same} pieces the same, ${R.different} different, in ${R.seconds.toFixed(0)} s`);
  window.testerResult = JSON.stringify(R);
}
window.testerState = () => null;
main().catch((e) => { say('failed: ' + (e.stack || e)); window.testerResult = JSON.stringify({ failed: String(e.stack || e) }); });
