// The tester's WebGPU player against the native drawings (ORDER 508, milestone 3): each of the scene's procedures
// drawn whole at 2048 and as sixteen 512 tiles by gpu-player.js (one submission per operator), posted as raw RGB, so
// they can be compared with p2p's own drawings. twins.html?tag=NAME. Our code, BSD 2-clause.
import { GpuPlayer, parse } from './gpu-player.js';
const Q = new URLSearchParams(location.search);
const TAG = Q.get('tag') || 'twins';
const log = (s) => { document.getElementById('log').textContent += s + '\n'; };
const post = (name, body) => fetch('/save?name=' + encodeURIComponent(name), { method: 'POST', body });
async function main() {
  const gltf = await (await fetch('scene/scene.gltf')).json();
  const procs = gltf.extensions.SPARKY_texture_mixed.procedures;
  const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
  const device = await adapter.requestDevice({ requiredFeatures: adapter.features.has('timestamp-query') ? ['timestamp-query'] : [], requiredLimits: { maxStorageBufferBindingSize: adapter.limits.maxStorageBufferBindingSize, maxBufferSize: adapter.limits.maxBufferSize } });
  const gpu = new GpuPlayer(device, 'ops/');
  const out = { adapter: adapter.info.vendor + ' ' + adapter.info.architecture, textures: {} };
  for (const p of procs) {
    const name = p.uri.split('/').pop().replace('.p2p', '');
    const g = parse(await (await fetch('scene/' + p.uri)).text());
    gpu.owner = name; gpu.piece = 'whole';
    const s0 = gpu.submissions.length;
    const whole = await gpu.drawRgb(g, 2048, { x: 0, y: 0, s: 1 });
    await post(`${TAG}-${name}-whole.rgb`, whole);
    const tiles = new Uint8Array(2048 * 2048 * 3);
    for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
      gpu.piece = `tile ${x},${y}`;
      const t = await gpu.drawRgb(g, 512, { x: x / 4, y: y / 4, s: 0.25 });
      for (let j = 0; j < 512; j++) tiles.set(t.subarray(j * 1536, (j + 1) * 1536), ((y * 512 + j) * 2048 + x * 512) * 3);
    }
    await post(`${TAG}-${name}-tiles.rgb`, tiles);
    const subs = gpu.submissions.slice(s0);
    const wholeSubs = subs.filter((s) => s.piece === 'whole');
    const gmax = (l) => Math.max(...l.map((s) => (s.gpuMs != null ? s.gpuMs : 0)));
    const tileSubs = subs.filter((s) => s.piece !== 'whole');
    out.textures[name] = { submissionsWhole: wholeSubs.length, longestWholeMs: Math.max(...wholeSubs.map((s) => s.ms)), sumWholeMs: wholeSubs.reduce((a, s) => a + s.ms, 0),
      longestWholeGpuMs: gmax(wholeSubs), sumWholeGpuMs: wholeSubs.reduce((a, s) => a + (s.gpuMs || 0), 0),
      submissionsTiles: tileSubs.length, longestTileMs: Math.max(...tileSubs.map((s) => s.ms)), longestTileGpuMs: gmax(tileSubs) };
    log(name + ' ' + JSON.stringify(out.textures[name]));
  }
  await post(TAG + '-twins.json', JSON.stringify(out, null, 1));
  await fetch('/done', { method: 'POST', body: 'ok' });
}
main().catch(async (e) => { await post(TAG + '-error.txt', String(e.stack || e)); await fetch('/done', { method: 'POST', body: 'failed' }); });
