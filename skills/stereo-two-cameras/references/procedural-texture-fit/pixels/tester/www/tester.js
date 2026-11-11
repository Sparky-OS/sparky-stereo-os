// The scene tester (ORDER 508, milestone 3): a web scene of mixed textures loaded in the order Daniel set (every
// procedure first; drawing starts at once from them; the pictures download beside it over several connections; each
// procedure blends into its picture as it arrives; then it is no longer computed), through a virtual link set in one
// panel after Macromedia's Simulate Download (Flash) and download-time estimate (Dreamweaver). Our code, BSD 2-clause.
import { t } from './strings.js';
import { GpuPlayer, parse, unknownParts } from './gpu-player.js';
import { GlScene, M } from './gl-scene.js';

const EXT = 'SPARKY_texture_mixed';       // working name of the mixed texture extension (MIXED-TEXTURE.md)
const KNOWN = { p2p: [1] };               // procedure languages and version words this player knows
const Q = new URLSearchParams(location.search);
const PRESETS = [   // id, label, bits per second (0: no limit); kbit/s = 1000 bit/s
  ['d144', '14.4 kbit/s ' + t('presetDialup'), 14400], ['d288', '28.8 kbit/s ' + t('presetDialup'), 28800],
  ['d336', '33.6 kbit/s ' + t('presetDialup'), 33600], ['d56', '56 kbit/s ' + t('presetDialup'), 56000],
  ['isdn', '128 kbit/s ' + t('presetIsdn'), 128000], ['dsl15', '1.5 Mbit/s ' + t('presetDsl'), 1.5e6],
  ['dsl8', '8 Mbit/s ' + t('presetDsl'), 8e6], ['g4', '20 Mbit/s ' + t('presetMobile'), 20e6],
  ['cable', '50 Mbit/s ' + t('presetCable'), 50e6], ['fibre300', '300 Mbit/s ' + t('presetFibre'), 300e6],
  ['fibre1g', '1 Gbit/s ' + t('presetFibre'), 1e9], ['none', t('presetNone'), 0], ['custom', t('custom'), -1]];
const S = {
  speed: Q.get('speed') || 'd56',
  kbps: +(Q.get('kbps') || 56),
  conns: Math.max(1, Math.min(6, +(Q.get('conns') || 6))),
  limit: Q.get('limit') === 'everything' ? 'everything' : 'pictures',
  blend: Q.get('blend') === 'cross' ? 'cross' : 'coarse',
  blendSec: Math.max(0.1, +(Q.get('blendsec') || 2)),
  player: ['webgpu', 'wasm'].includes(Q.get('player')) ? Q.get('player') : 'auto',
  detailed: Q.get('detailed') !== '0',
  proof: Q.get('proof') === '1',
  nostop: Q.get('nostop') === '1',
  tag: Q.get('tag') || 'run',
  scene: Q.get('scene') || 'scene/scene.gltf',
  full: +(Q.get('full') || 2048),
  tile: +(Q.get('tile') || 512),
  first: +(Q.get('first') || 256),
  fps: +(Q.get('fps') || 0),          // 0: every display frame; proofs draw fewer to spare the shared GPU
};
const bitsPerSecond = () => { const p = PRESETS.find((x) => x[0] === S.speed); return !p ? 56000 : p[2] < 0 ? S.kbps * 1000 : p[2]; };
const now = () => performance.now();
const fmtBytes = (b) => b >= 1e6 ? (b / 1e6).toFixed(2) + ' MB' : b >= 1e3 ? (b / 1e3).toFixed(1) + ' KB' : b + ' B';
const fmtTime = (s) => !isFinite(s) ? '-' : s < 1 ? (s * 1000).toFixed(0) + ' ms' : s < 90 ? s.toFixed(1) + ' s' : s < 5400 ? (s / 60).toFixed(1) + ' min' : (s / 3600).toFixed(2) + ' h';
const fmtRate = (bps) => bps >= 1e6 ? (bps / 1e6).toFixed(2) + ' Mbit/s' : (bps / 1e3).toFixed(1) + ' kbit/s';

const R = {          // what the run measured
  tag: S.tag, settings: { ...S, bitsPerSecond: bitsPerSecond() }, ua: navigator.userAgent,
  player: null, playerNote: '', adapter: null, firstFrame: null, firstAny: null, allIn: null, settled: null, playerOff: null,
  messages: [], comps: [], textures: [], rate: [], submissions: 0, longest: null, wasm: { calls: 0, ms: 0, ready: null },
};
let scene = null, gpu = null, worker = null, gltf = null, scriptMod = null, xr = null;
const comps = R.comps, texs = R.textures;
const say = (key, ...a) => { const s = t(key, ...a); R.messages.push({ t: now(), text: s }); render(); };

// ------------------------------------------------------------------ the virtual link
async function setRate() {
  const bps = bitsPerSecond();
  await fetch('/link', { method: 'POST', body: JSON.stringify({ rate: bps / 8 }) });
}

class Loader {
  constructor(n) { this.n = n; this.active = 0; this.queue = []; }
  get(comp) {
    return new Promise((resolve, reject) => { this.queue.push({ comp, resolve, reject }); this.pump(); });
  }
  pump() { while (this.active < this.n && this.queue.length) this.run(this.queue.shift()); }
  async run(job) {
    const c = job.comp;
    this.active++;
    c.state = 'loading';
    c.tStart = now();
    try {
      const r = await fetch(c.url + (c.limited ? '?link=1' : ''), { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const total = +r.headers.get('Content-Length') || c.size || 0;
      if (total) c.size = total;
      const reader = r.body.getReader();
      const parts = [];
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        parts.push(value);
        c.received += value.length;
        if (c.limited) R.rate.push([now(), value.length]);
      }
      const buf = new Uint8Array(c.received);
      let o = 0;
      for (const p of parts) { buf.set(p, o); o += p.length; }
      c.state = 'done';
      c.tEnd = now();
      job.resolve(buf.buffer);
    } catch (e) {
      c.state = 'failed';
      c.error = String(e.message || e);
      c.tEnd = now();
      job.reject(e);
    } finally {
      this.active--;
      this.pump();
    }
  }
}

function comp(name, kind, url, size, limited) {
  const c = { name, kind, url, size: size || 0, received: 0, state: 'waiting', tStart: null, tEnd: null, error: null, limited };
  comps.push(c);
  return c;
}

// ------------------------------------------------------------------ the procedure players
async function startPlayer() {
  if (S.player !== 'wasm' && navigator.gpu) {
    const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
    if (adapter) {
      const info = adapter.info || {};
      R.adapter = { vendor: info.vendor, architecture: info.architecture, device: info.device, description: info.description };
      const device = await adapter.requestDevice({ requiredLimits: { maxStorageBufferBindingSize: adapter.limits.maxStorageBufferBindingSize, maxBufferSize: adapter.limits.maxBufferSize } });
      device.lost.then((i) => { if (!R.playerOff) say('msgProcedureFailed', 'WebGPU', 'device lost: ' + i.message); });
      gpu = new GpuPlayer(device, 'ops/');
      gpu.onSubmit = (rec) => {
        R.submissions++;
        const tx = texs.find((x) => x.name === rec.owner);
        if (tx) { tx.subs++; tx.lastWork = rec.t + rec.ms; if (tx.times.stop != null && rec.t >= tx.times.stop) tx.subsAfterStop++; if (tx.times.picArrived != null && rec.t >= tx.times.picArrived) tx.subsAfterPicture++; }
        if (!R.longest || rec.ms > R.longest.ms) R.longest = { ...rec };
      };
      R.player = 'webgpu';
      R.playerNote = t('playerWebgpu', [info.vendor, info.architecture, info.description].filter(Boolean).join(' '));
      if (info.architecture === 'swiftshader' || adapter.isFallbackAdapter) say('msgSoftwareAdapter', info.architecture || 'fallback');
      return;
    }
  }
  R.player = 'wasm';
  R.playerNote = S.player === 'wasm' ? t('playerWasmChosen') : t('playerWasmNoWebgpu', navigator.gpu ? 'no adapter' : 'navigator.gpu is missing');
  worker = new Worker('wasm-worker.js', { type: 'module' });
  await new Promise((resolve, reject) => {
    worker.onmessage = (ev) => { if (ev.data.kind === 'ready') { R.wasm.ready = ev.data.ms; resolve(); } else reject(new Error(ev.data.error)); };
    worker.onerror = (e) => reject(new Error(e.message));
    worker.postMessage({ kind: 'init', url: 'player/p2p.wasm' });
  });
  let next = 1;
  const waiting = new Map();
  worker.onmessage = (ev) => {
    const m = ev.data;
    const w = waiting.get(m.id);
    if (!w) return;
    waiting.delete(m.id);
    if (m.kind === 'piece') w.resolve(m); else w.reject(new Error(m.error));
  };
  worker.piece = (script, exp, win) => new Promise((resolve, reject) => {
    const id = next++;
    waiting.set(id, { resolve, reject });
    worker.postMessage({ kind: 'piece', id, script, exp, win });
  });
}

// one piece of a texture's procedure as RGB: side pixels through window win
async function drawPiece(tx, eye, side, win, label) {
  const g = eye ? tx.gRight : tx.g;
  const text = eye ? tx.textRight : tx.text;
  const t0 = now();
  let rgb;
  if (gpu) {
    gpu.owner = tx.name;
    gpu.piece = label;
    rgb = await gpu.drawRgb(g, side, win);
  } else {
    const m = await worker.piece(text, Math.round(Math.log2(side)), win);
    R.wasm.calls++;
    R.wasm.ms += m.ms;
    tx.wasm++;
    tx.lastWork = now();
    if (tx.times.stop != null && t0 >= tx.times.stop) tx.wasmAfterStop++;
    if (tx.times.picArrived != null && t0 >= tx.times.picArrived) tx.subsAfterPicture++;
    const ms = m.ms;
    if (!R.longest || ms > R.longest.ms) R.longest = { owner: tx.name, piece: label, ms, t: t0, cpu: true };
    rgb = m.rgb;
  }
  tx.cpuMs += now() - t0;
  return rgb;
}

// the jobs: every texture's whole drawing at S.first pixels first, then its full-size tiles; a texture whose picture
// is in gets no more work (unless the negative control nostop=1 asks to keep drawing)
const jobs = [];
let jobsRunning = false;
async function runJobs() {
  if (jobsRunning) return;
  jobsRunning = true;
  while (jobs.length) {
    const j = jobs.shift();
    const tx = j.tx;
    if (!S.nostop && tx.times.picArrived != null) continue;
    if (tx.failed) continue;
    try {
      if (j.kind === 'whole') {
        const rgb = await drawPiece(tx, j.eye, S.first, { x: 0, y: 0, s: 1 }, 'whole at ' + S.first);
        if (tx.mode === 'procedure' || tx.mode === 'none') {
          scene.setProcedureWhole(tx.i, j.eye, S.first, rgb);
          if (j.eye === tx.eyes - 1 && tx.times.procFirst == null) { tx.times.procFirst = now(); tx.mode = 'procedure'; }
        }
      } else {
        const n = S.full / S.tile;
        const rgb = await drawPiece(tx, j.eye, S.tile, { x: j.x / n, y: j.y / n, s: 1 / n }, `tile ${j.x},${j.y} of ${n}x${n}`);
        if (tx.mode === 'procedure') scene.setProcedureTile(tx.i, j.eye, S.full, j.x * S.tile, j.y * S.tile, S.tile, rgb);
        tx.tiles++;
        if (tx.tiles === n * n * tx.eyes && tx.times.procFull == null) tx.times.procFull = now();
        if (S.nostop && tx.times.stop != null) jobs.push({ ...j });    // the negative control: never stops
      }
    } catch (e) {
      tx.failed = true;
      say('msgProcedureFailed', tx.name, e.message || e);
    }
    await new Promise((r) => setTimeout(r, 0));
  }
  jobsRunning = false;
  maybeSettled();
}

// ------------------------------------------------------------------ the scene
async function main() {
  renderPanel();
  try { scene = new GlScene(document.getElementById('scene')); } catch (e) { say('msgNoWebgl'); if (S.proof) finishProof(); return; }
  if (S.nostop) say('msgNoStop');
  await fetch('/link/reset', { method: 'POST' });
  await setRate();
  const loader = new Loader(S.conns);
  const base = new URL(S.scene, location.href);
  const rel = (u) => new URL(u, base).pathname;
  const everything = S.limit === 'everything';
  const desc = comp(base.pathname.split('/').pop() + ' (' + t('kindDescription') + ')', 'description', base.pathname, 0, everything);
  const playerReady = startPlayer();
  try {
    gltf = JSON.parse(new TextDecoder().decode(await loader.get(desc)));
  } catch (e) { say('msgSceneFailed', e.message || e); if (S.proof) finishProof(); return; }
  scene.initTextures(gltf.textures.length);
  // the scene's components, named as the scene names them
  const root = (gltf.extensions || {})[EXT] || { procedures: [] };
  const procComps = root.procedures.map((p) => comp(p.name || p.uri, 'procedure', rel(p.uri), p.byteLength, everything));
  const modelComps = gltf.buffers.map((b) => comp(b.name || b.uri, 'model', rel(b.uri), b.byteLength, everything));
  const scripts = ((gltf.extras || {}).scripts || []).map((s) => comp(s.name || s.url, 'script', rel(s.url), 0, everything));
  const audio = (((gltf.extensions || {}).KHR_audio_emitter || {}).audio || []).filter((a) => a.uri).map((a) => comp(a.name || a.uri, 'sound', rel(a.uri), 0, everything));
  const picComps = gltf.images.map((im) => comp(im.name || im.uri, 'picture', rel(im.uri), 0, true));
  // sizes the description does not give: asked of the server (HEAD, no body), as Dreamweaver reads the files' sizes
  await Promise.all(comps.filter((c) => !c.size).map(async (c) => {
    const r = await fetch(c.url, { method: 'HEAD', cache: 'no-store' });
    if (r.ok) c.size = +r.headers.get('Content-Length') || 0;
  }));
  // the textures
  gltf.textures.forEach((tex, i) => {
    const ext = (tex.extensions || {})[EXT];
    const views = ext && ext.views;
    const right = views ? views.find((v) => v.eye === 'right') : null;
    texs.push({ i, name: tex.name || 'texture ' + i, ext: !!ext, proc: ext ? ext.procedure : null, procRight: right ? right.procedure : null,
      pic: tex.source, picRight: right ? right.source : null, eyes: right ? 2 : 1, mode: 'none', tiles: 0,
      subs: 0, subsAfterStop: 0, subsAfterPicture: 0, wasm: 0, wasmAfterStop: 0, cpuMs: 0, lastWork: null, failed: false,
      times: { procArrived: null, procFirst: null, procFull: null, picQueued: null, picStart: null, picArrived: null, blendStart: null, blendEnd: null, stop: null } });
  });
  render();
  await playerReady;
  // (1) every procedure first
  const procText = await Promise.all(procComps.map((c) => loader.get(c).then((b) => new TextDecoder().decode(b), () => null)));
  for (const tx of texs) {
    if (!tx.ext) continue;
    const p = root.procedures[tx.proc];
    tx.times.procArrived = procComps[tx.proc].tEnd;
    const known = KNOWN[p.language] && KNOWN[p.language].includes(p.version);
    let bad = !known ? `${p.language} version ${p.version}` : null;
    if (!bad && procText[tx.proc] == null) bad = 'not loaded';
    if (!bad) {
      try {
        tx.text = procText[tx.proc];
        tx.g = parse(tx.text);
        if (tx.eyes === 2) { tx.textRight = procText[tx.procRight]; tx.gRight = parse(tx.textRight); }
        if (gpu) { const u = unknownParts(tx.g); if (u.length) bad = u.join(', '); }
      } catch (e) { bad = e.message; }
    }
    if (bad) { tx.failed = true; say('msgUnknownVersion', tx.name, bad); continue; }
    for (let e = 0; e < tx.eyes; e++) jobs.push({ tx, eye: e, kind: 'whole' });
  }
  // the WGSL operators these procedures use, compiled at once and side by side
  if (gpu) await Promise.all([...new Set(texs.filter((x) => x.g).flatMap((x) => [...x.g.nodes, ...(x.gRight ? x.gRight.nodes : [])].map((n) => n.op)))].map((op) => gpu.pipeline(op)));
  runJobs();       // (2) drawing starts at once from the procedures
  const bufs = await Promise.all(modelComps.map((c) => loader.get(c)));
  const map = new Map(gltf.buffers.map((b, i) => [b.uri, bufs[i]]));
  scene.load(gltf, map);
  for (const tx of texs) if (!tx.ext) tx.mode = 'none';
  requestAnimationFrame(frame);
  // full-size tiles, texture by texture
  const n = S.full / S.tile;
  for (const tx of texs) if (tx.ext && !tx.failed) for (let e = 0; e < tx.eyes; e++) for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) jobs.push({ tx, eye: e, kind: 'tile', x, y });
  runJobs();
  // (3) the pictures beside the drawing, over S.conns connections; the script first, the sound last
  scripts.forEach((c) => loader.get(c).then(async (b) => {
    const url = URL.createObjectURL(new Blob([b], { type: 'text/javascript' }));
    scriptMod = await import(url);
  }, () => {}));
  for (const tx of texs) {
    for (let e = 0; e < tx.eyes; e++) {
      const ii = e ? tx.picRight : tx.pic;
      if (ii == null) continue;
      const c = picComps[ii];
      if (e === 0) { tx.times.picQueued = now(); tx.picComp = c; }
      loader.get(c).then(async (buf) => {
        const bmp = await createImageBitmap(new Blob([buf], { type: gltf.images[ii].mimeType || 'image/jpeg' }), { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
        scene.setPicture(tx.i, e, bmp);
        bmp.close();
        tx.picsIn = (tx.picsIn || 0) + 1;
        if (R.allIn == null && picComps.every((p) => p.state === 'done' || p.state === 'failed')) R.allIn = Math.max(...picComps.map((p) => p.tEnd || 0));
        if (tx.picsIn === tx.eyes) {
          tx.times.picStart = c.tStart;
          tx.times.picArrived = c.tEnd;
          // (4) the procedure blends into its picture
          tx.times.blendStart = now();
          tx.mode = tx.failed || tx.times.procFirst == null ? 'picture' : 'blend';
          if (tx.mode === 'picture') finishTexture(tx);
        }
      }, (err) => { say('msgPictureFailed', tx.name, err.message || err); tx.picFailed = true; maybeSettled(); });
    }
  }
  audio.forEach((c) => loader.get(c).then(async (b) => {
    try { const ac = new AudioContext(); await ac.decodeAudioData(b.slice(0)); c.decoded = true; ac.close(); } catch (e) { c.decodeError = String(e); }
    if (!R.messages.some((m) => m.text === t('msgSoundBlocked'))) say('msgSoundBlocked');
  }, () => {}));
}

// (5) the blend has ended: the procedure is no longer computed nor sampled
function finishTexture(tx) {
  tx.times.blendEnd = tx.times.blendEnd || now();
  tx.mode = 'picture';
  tx.times.stop = now();
  if (!S.nostop) scene.releaseProcedure(tx.i);
  else if (tx.ext && !tx.failed) {
    // the negative control: the procedure is drawn again and again after its picture is in
    const n = S.full / S.tile;
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) jobs.push({ tx, eye: 0, kind: 'tile', x, y });
    runJobs();
  }
  maybeSettled();
}

function maybeSettled() {
  if (R.settled != null) return;
  const picC = comps.filter((c) => c.kind === 'picture');
  if (R.allIn == null && picC.every((c) => c.state === 'done' || c.state === 'failed')) R.allIn = Math.max(...picC.map((c) => c.tEnd || 0));
  const allTex = texs.every((tx) => tx.mode === 'picture' || tx.picFailed || (!tx.ext && tx.mode !== 'blend'));
  if (!allTex || (jobsRunning && !S.nostop)) return;
  R.settled = now();
  if (!S.nostop) {
    // nothing is left for the procedure player: it is shut down
    if (gpu) { gpu.device.destroy(); }
    if (worker) worker.terminate();
    R.playerOff = now();
  }
  if (S.proof) setTimeout(finishProof, 3000);
}

let frames = 0;
function frame() {
  const tNow = now();
  for (const tx of texs) {
    if (tx.mode !== 'blend') continue;
    const k = (tNow - tx.times.blendStart) / (S.blendSec * 1000);
    if (k >= 1) { scene.textures[tx.i].mode = 3; finishTexture(tx); continue; }
    scene.textures[tx.i].mode = S.blend === 'cross' ? 1 : 2;
    scene.textures[tx.i].t = k;
  }
  for (const tx of texs) if (tx.mode === 'picture') scene.textures[tx.i].mode = 3;
  const ready = texs.every((tx) => !tx.ext || tx.failed || tx.times.procFirst != null || tx.mode === 'picture');
  if (!xr) {
    if (scriptMod && scriptMod.update) scriptMod.update(scene, tNow / 1000);
    scene.frame2d();
    frames++;
    if (R.firstAny == null) R.firstAny = tNow;
    if (ready && R.firstFrame == null) {
      R.firstFrame = tNow;
      const f = document.getElementById('first');
      f.hidden = false;
      f.textContent = t('firstFrame', fmtTime(tNow / 1000));
    }
    if (S.fps > 0) setTimeout(() => requestAnimationFrame(frame), 1000 / S.fps); else requestAnimationFrame(frame);
  }
}

// ------------------------------------------------------------------ WebXR: one view per eye from the session
async function setupXr(btn, line) {
  if (!navigator.xr || !(await navigator.xr.isSessionSupported('immersive-vr').catch(() => false))) { line.textContent = t('no3d'); btn.hidden = true; return; }
  btn.hidden = false;
  btn.onclick = async () => {
    const session = await navigator.xr.requestSession('immersive-vr', { optionalFeatures: ['local'] });
    const gl = scene.gl;
    await gl.makeXRCompatible();
    const layer = new XRWebGLLayer(session, gl);
    session.updateRenderState({ baseLayer: layer });
    const local = await session.requestReferenceSpace('local');
    // the reference space's origin at the scene's camera: poses in it are then poses in the scene
    const w = scene.cameraPose().world;
    const inv = M.invertRigid(w);
    const q = matToQuat(inv);
    const ref = local.getOffsetReferenceSpace(new XRRigidTransform({ x: inv[12], y: inv[13], z: inv[14] }, { x: q[0], y: q[1], z: q[2], w: q[3] }));
    xr = session;
    line.textContent = t('in3d');
    const loop = (time, fr) => {
      session.requestAnimationFrame(loop);
      for (const tx of texs) if (tx.mode === 'blend' && (performance.now() - tx.times.blendStart) / (S.blendSec * 1000) >= 1) { scene.textures[tx.i].mode = 3; finishTexture(tx); }
      scene.frameXr(fr, ref, layer);
    };
    session.requestAnimationFrame(loop);
    session.addEventListener('end', () => { xr = null; line.textContent = ''; requestAnimationFrame(frame); });
  };
}
function matToQuat(m) {
  const tr = m[0] + m[5] + m[10];
  let x, y, z, w;
  if (tr > 0) { const s = Math.sqrt(tr + 1) * 2; w = 0.25 * s; x = (m[6] - m[9]) / s; y = (m[8] - m[2]) / s; z = (m[1] - m[4]) / s; }
  else if (m[0] > m[5] && m[0] > m[10]) { const s = Math.sqrt(1 + m[0] - m[5] - m[10]) * 2; w = (m[6] - m[9]) / s; x = 0.25 * s; y = (m[4] + m[1]) / s; z = (m[8] + m[2]) / s; }
  else if (m[5] > m[10]) { const s = Math.sqrt(1 + m[5] - m[0] - m[10]) * 2; w = (m[8] - m[2]) / s; x = (m[4] + m[1]) / s; y = 0.25 * s; z = (m[9] + m[6]) / s; }
  else { const s = Math.sqrt(1 + m[10] - m[0] - m[5]) * 2; w = (m[1] - m[4]) / s; x = (m[8] + m[2]) / s; y = (m[9] + m[6]) / s; z = 0.25 * s; }
  return [x, y, z, w];
}

// ------------------------------------------------------------------ the panel
const el = (tag, attrs = {}, ...kids) => { const e = document.createElement(tag); Object.assign(e, attrs); for (const k of kids) e.append(k); return e; };
let ui = {};
function renderPanel() {
  const p = document.getElementById('panel');
  p.textContent = '';
  p.append(el('h1', { textContent: t('panel') }), el('p', { className: 'note', textContent: t('panelNote') }));
  const sel = el('select', { id: 'speed' });
  for (const [id, label] of PRESETS) sel.append(el('option', { value: id, textContent: label, selected: id === S.speed }));
  const kb = el('input', { id: 'kbps', type: 'number', min: 1, step: 0.1, value: S.kbps, hidden: S.speed !== 'custom', style: 'width:90px' });
  sel.onchange = async () => { S.speed = sel.value; kb.hidden = S.speed !== 'custom'; R.settings.bitsPerSecond = bitsPerSecond(); await setRate(); render(); };
  kb.onchange = async () => { S.kbps = +kb.value; R.settings.bitsPerSecond = bitsPerSecond(); await setRate(); render(); };
  const conns = el('select', { id: 'conns' });
  for (let i = 1; i <= 6; i++) conns.append(el('option', { value: i, textContent: String(i), selected: i === S.conns }));
  const lim = el('select', { id: 'limit' }, el('option', { value: 'pictures', textContent: t('limitPictures'), selected: S.limit === 'pictures' }), el('option', { value: 'everything', textContent: t('limitEverything'), selected: S.limit === 'everything' }));
  const bl = el('select', { id: 'blend' }, el('option', { value: 'coarse', textContent: t('blendCoarse'), selected: S.blend === 'coarse' }), el('option', { value: 'cross', textContent: t('blendCross'), selected: S.blend === 'cross' }));
  const bs = el('input', { id: 'blendsec', type: 'number', min: 0.1, step: 0.1, value: S.blendSec, style: 'width:70px' });
  const det = el('input', { id: 'detailed', type: 'checkbox', checked: S.detailed });
  det.onchange = () => { S.detailed = det.checked; render(); };
  const restart = el('button', { textContent: t('restart') });
  restart.onclick = () => {
    const q = new URLSearchParams({ speed: sel.value, kbps: kb.value, conns: conns.value, limit: lim.value, blend: bl.value, blendsec: bs.value, detailed: det.checked ? '1' : '0' });
    if (S.player !== 'auto') q.set('player', S.player);
    location.search = q.toString();
  };
  const row = (label, ...k) => el('div', { className: 'row' }, el('label', { textContent: label }), ...k);
  p.append(row(t('speed'), sel, kb), row(t('connections'), conns), row(t('limitTo'), lim), row(t('blend'), bl), row(t('blendSeconds'), bs),
    el('div', { className: 'row' }, restart, el('label', { style: 'min-width:0' }, det, ' ' + t('detailed'))));
  ui.summary = el('table');
  ui.stream = el('div', { className: 'bar', id: 'stream' }, el('i'));
  ui.streamText = el('div', { className: 'note' });
  ui.detail = el('table', { id: 'detail' });
  ui.timeline = el('canvas', { id: 'timeline' });
  ui.player = el('div');
  ui.msgs = el('div', { id: 'msgs' });
  ui.xrBtn = el('button', { textContent: t('enter3d'), hidden: true });
  ui.xrLine = el('div', { className: 'note' });
  const legend = el('div', { className: 'legend' });
  for (const [k, c] of [['legendProcedure', '--proc'], ['legendDownload', '--down'], ['legendBlend', '--blend'], ['legendPicture', '--pic']]) legend.append(el('span', {}, el('i', { style: `background:var(${c})` }), t(k)));
  p.append(el('h2', { textContent: t('summary') }), ui.summary, el('h2', { textContent: t('simulated') }), ui.stream, ui.streamText,
    el('h2', { textContent: t('timeline') }), legend, ui.timeline, el('h2', { textContent: t('player') }), ui.player, ui.msgs,
    el('div', { className: 'row' }, ui.xrBtn), ui.xrLine, ui.detailHead = el('h2', { textContent: t('component') }), ui.detail);
  setupXr(ui.xrBtn, ui.xrLine);
}

function measuredRate(windowMs) {
  const r = R.rate;
  if (r.length < 2) return null;
  const tEnd = r[r.length - 1][0];
  let bytes = 0, k = r.length - 1;
  if (windowMs) {
    while (k > 0 && r[k - 1][0] >= tEnd - windowMs) { bytes += r[k][1]; k--; }
    const span = tEnd - r[k][0];
    return span > 0 ? bytes * 8 / (span / 1000) : null;
  }
  for (let i = 1; i < r.length; i++) bytes += r[i][1];
  const span = tEnd - r[0][0];
  return span > 0 ? bytes * 8 / (span / 1000) : null;
}

function render() {
  if (!ui.summary) return;
  const bps = bitsPerSecond();
  const time = (b) => bps > 0 ? fmtTime(b * 8 / bps) : '-';
  const sum = (k) => comps.filter((c) => k(c)).reduce((a, c) => a + c.size, 0);
  const proc = sum((c) => c.kind === 'procedure'), pic = sum((c) => c.kind === 'picture');
  const other = sum((c) => c.kind !== 'procedure' && c.kind !== 'picture');
  const nP = comps.filter((c) => c.kind === 'procedure').length, nI = comps.filter((c) => c.kind === 'picture').length;
  const limited = (b, kind) => S.limit === 'everything' || kind === 'picture' ? time(b) : t('noLimit');
  const firstBytes = S.limit === 'everything' ? sum((c) => c.kind !== 'picture' && c.kind !== 'script' && c.kind !== 'sound') : 0;
  ui.summary.innerHTML = '';
  const tr = (...cells) => { const r = el('tr'); cells.forEach((c, i) => r.append(el(i ? 'td' : 'th', { className: i ? 'num' : '', textContent: c }))); return r; };
  ui.summary.append(tr(t('procedures') + ` (${nP})`, fmtBytes(proc), limited(proc, 'procedure')),
    tr(t('pictures') + ` (${nI})`, fmtBytes(pic), limited(pic, 'picture')),
    tr(t('otherParts'), fmtBytes(other), limited(other, 'other')),
    tr(t('total'), fmtBytes(proc + pic + other), S.limit === 'everything' ? time(proc + pic + other) : time(pic)),
    tr(t('usableAfter'), '', S.limit === 'everything' ? (bps > 0 ? time(firstBytes) : t('noLimit')) : t('notLimited')));
  const lim = comps.filter((c) => c.limited);
  const got = lim.reduce((a, c) => a + c.received, 0), all = lim.reduce((a, c) => a + c.size, 0) || 1;
  ui.stream.firstChild.style.width = (100 * got / all).toFixed(1) + '%';
  ui.stream.className = 'bar' + (got >= all ? ' done' : '');
  const el0 = now() / 1000;
  const mr = measuredRate(R.allIn ? 0 : 3000);
  const left = bps > 0 ? (all - got) * 8 / bps : 0;
  ui.streamText.textContent = [fmtBytes(got) + ' / ' + fmtBytes(all), R.allIn ? t('done', fmtTime(R.allIn / 1000)) : t('elapsed', fmtTime(el0)) + ', ' + t('remaining', fmtTime(left)),
    mr ? t('measured', fmtRate(mr), bps > 0 ? fmtRate(bps) : t('noLimit')) : ''].filter(Boolean).join(' · ');
  ui.detail.hidden = ui.detailHead.hidden = !S.detailed;
  if (S.detailed) {
    ui.detail.innerHTML = '';
    const h = el('tr');
    for (const k of ['component', 'kind', 'size', 'state']) h.append(el('th', { textContent: t(k) }));
    ui.detail.append(h);
    const kindKey = { description: 'kindDescription', procedure: 'kindProcedure', model: 'kindModel', picture: 'kindPicture', script: 'kindScript', sound: 'kindSound' };
    for (const c of comps) {
      const frac = c.size ? Math.min(1, c.received / c.size) : (c.state === 'done' ? 1 : 0);
      const st = c.state === 'done' ? t('arrived', fmtTime(c.tEnd / 1000)) : c.state === 'failed' ? t('failed', c.error) : c.state === 'loading' ? t('loading') + ' ' + (100 * frac).toFixed(0) + '%' : t('waiting');
      const bar = el('div', { className: 'bar big' + (c.state === 'done' ? ' done' : c.state === 'failed' ? ' bad' : c.kind === 'procedure' ? ' proc' : '') }, el('i', { style: `width:${(100 * frac).toFixed(1)}%` }), el('b', { textContent: st }));
      const r = el('tr');
      r.append(el('td', { textContent: c.name, title: c.name }), el('td', { textContent: t(kindKey[c.kind]) }), el('td', { className: 'num', textContent: fmtBytes(c.size) }), el('td', { style: 'width:42%' }, bar));
      ui.detail.append(r);
    }
  }
  drawTimeline();
  const lines = [R.playerNote || ''];
  if (R.longest) lines.push(t(R.player === 'wasm' ? 'longestPiece' : 'longest') + ': ' + t('longestValue', R.longest.ms.toFixed(1), R.longest.owner, R.longest.piece));
  if (R.player === 'webgpu') lines.push(t('submissions', R.submissions, texs.reduce((a, x) => a + x.subsAfterStop, 0)));
  if (R.player === 'wasm') lines.push(t('wasmCalls', R.wasm.calls, texs.reduce((a, x) => a + x.wasmAfterStop, 0)));
  if (R.playerOff) lines.push(t('playerOff'));
  ui.player.innerHTML = '';
  for (const l of lines) ui.player.append(el('div', { textContent: l }));
  ui.msgs.innerHTML = '';
  for (const m of R.messages) ui.msgs.append(el('div', { textContent: m.text, className: m.text === t('msgSoundBlocked') ? 'info' : '' }));
}

function drawTimeline() {
  const c = ui.timeline;
  const w = c.clientWidth || 430, rowH = 18, h = 16 + rowH * Math.max(1, texs.length);
  c.style.height = h + 'px';
  if (c.width !== w * devicePixelRatio || c.height !== h * devicePixelRatio) { c.width = w * devicePixelRatio; c.height = h * devicePixelRatio; }
  const g = c.getContext('2d');
  g.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  const css = getComputedStyle(document.documentElement);
  const col = (n) => css.getPropertyValue(n).trim();
  g.clearRect(0, 0, w, h);
  const end = Math.max(now(), 1000), x0 = 110, sx = (w - x0 - 4) / end;
  const X = (tm) => x0 + tm * sx;
  g.font = '11px system-ui'; g.fillStyle = col('--muted');
  g.fillText('0', x0, 10);
  g.fillText(fmtTime(end / 1000), w - 50, 10);
  texs.forEach((tx, k) => {
    const y = 16 + k * rowH;
    g.fillStyle = col('--fg');
    g.fillText(tx.name.slice(0, 17), 0, y + 11);
    const T = tx.times;
    const bar = (a, b, cl) => { if (a == null) return; g.fillStyle = col(cl); g.fillRect(X(a), y + 3, Math.max(1, X(b == null ? now() : b) - X(a)), rowH - 7); };
    bar(T.procFirst, T.blendStart, '--proc');
    const pc = tx.picComp;
    if (pc && pc.tStart != null) { g.fillStyle = col('--down'); g.fillRect(X(pc.tStart), y + rowH - 6, Math.max(1, X(pc.tEnd == null ? now() : pc.tEnd) - X(pc.tStart)), 3); }
    bar(T.blendStart, T.stop, '--blend');
    bar(T.stop, null, '--pic');
    if (tx.lastWork != null) { g.fillStyle = col('--fg'); g.fillRect(X(tx.lastWork), y + 1, 1.5, rowH - 3); }
    if (tx.failed || tx.picFailed) { g.fillStyle = col('--bad'); g.fillText('!', w - 10, y + 11); }
  });
}
setInterval(render, 250);

// ------------------------------------------------------------------ proofs: the results, posted to the server
window.testerState = () => ({
  t: now(), firstFrame: R.firstFrame, allIn: R.allIn, settled: R.settled, playerOff: R.playerOff, player: R.player,
  comps: comps.map((c) => ({ name: c.name, state: c.state, received: c.received, size: c.size })),
  textures: texs.map((x) => ({ name: x.name, mode: x.mode, failed: x.failed, tiles: x.tiles, subs: x.subs, times: x.times })), messages: R.messages.map((m) => m.text),
  jobs: jobs.length, jobsRunning, submissions: R.submissions,
});
async function finishProof() {
  R.end = now();
  R.measuredWhole = measuredRate(0);
  R.frames = frames;
  if (gpu) R.submissionLog = gpu.submissions.map((s) => [s.owner, s.piece, +s.t.toFixed(2), +s.ms.toFixed(3)]);
  await fetch('/save?name=' + encodeURIComponent(S.tag + '-result.json'), { method: 'POST', body: JSON.stringify(R) });
  await fetch('/done', { method: 'POST', body: 'ok' });
}

main().catch((e) => { say('msgProcedureFailed', 'tester', e.stack || e); if (S.proof) finishProof(); });
