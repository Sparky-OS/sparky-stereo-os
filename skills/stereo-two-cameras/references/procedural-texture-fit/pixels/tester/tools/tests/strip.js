// The blend strip (ORDER 508, milestone 3; ORDER 537: this tree's paths, results read by the driver): one texture of the scene drawn by its procedure at full size, its picture
// loaded, then the scene tester's own material shader drawn at blend times 0, 0.1 ... 1 for the cross-fade and for
// coarse first then detail, at 1:1 (the centre, 512 pixels) and whole (the texture at 512); every frame read back and
// posted to the server as a PNG. strip.html?tex=INDEX&tag=NAME. Our code, BSD 2-clause.
import { GpuPlayer, parse } from '../../site/gpu-player.js';
import { GlScene } from '../../site/gl-scene.js';

const Q = new URLSearchParams(location.search);
const TI = +(Q.get('tex') || 0), TAG = Q.get('tag') || 'strip', FULL = 2048, TILE = 512;
const log = (s) => { document.getElementById('log').textContent += s + '\n'; };
// results are kept in the page and read by the driver (drive.py saves every entry of window.testerFiles): no server routes
window.testerFiles = {};
window.testerState = () => null;
const b64 = (u8) => { let s = ''; for (let i = 0; i < u8.length; i += 32768) s += String.fromCharCode(...u8.subarray(i, i + 32768)); return btoa(s); };
const post = async (name, body) => { window.testerFiles[name] = typeof body === 'string' ? 'text:' + body : 'base64:' + b64(new Uint8Array(body instanceof Blob ? await body.arrayBuffer() : body.buffer || body)); };
const done = (how) => { window.testerResult = JSON.stringify({ result: how, files: Object.keys(window.testerFiles) }); };

async function main() {
  const gltf = await (await fetch('../../site/scene/scene.gltf')).json();
  const ext = gltf.extensions.KHR_texture_procedural_rendering;
  const tex = gltf.textures[TI];
  const proc = ext.procedures[tex.extensions.KHR_texture_procedural_rendering.procedure];
  const text = await (await fetch('../../site/scene/' + proc.uri)).text();
  const g = parse(text);
  const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
  const device = await adapter.requestDevice({ requiredLimits: { maxStorageBufferBindingSize: adapter.limits.maxStorageBufferBindingSize, maxBufferSize: adapter.limits.maxBufferSize } });
  const gpu = new GpuPlayer(device, '../../site/ops/');
  const canvas = document.getElementById('c');
  const sc = new GlScene(canvas);
  sc.unlit = true;
  // one square: positions (x, y) = (u, 1 - v), facing +Z
  const P = new Float32Array([0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0]), N = new Float32Array([0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1]);
  const T = new Float32Array([0, 1, 1, 1, 1, 0, 0, 0]), I = new Uint16Array([0, 1, 2, 0, 2, 3]);
  const buf = new Uint8Array(P.byteLength + N.byteLength + T.byteLength + I.byteLength);
  let o = 0;
  const views = [];
  for (const a of [P, N, T, I]) { buf.set(new Uint8Array(a.buffer), o); views.push({ buffer: 0, byteOffset: o, byteLength: a.byteLength }); o += a.byteLength; }
  const mini = { buffers: [{ uri: 'q' }], bufferViews: views,
    accessors: [{ bufferView: 0, componentType: 5126, count: 4, type: 'VEC3' }, { bufferView: 1, componentType: 5126, count: 4, type: 'VEC3' },
      { bufferView: 2, componentType: 5126, count: 4, type: 'VEC2' }, { bufferView: 3, componentType: 5123, count: 6, type: 'SCALAR' }],
    meshes: [{ primitives: [{ attributes: { POSITION: 0, NORMAL: 1, TEXCOORD_0: 2 }, indices: 3, material: 0 }] }],
    materials: [{ pbrMetallicRoughness: { baseColorTexture: { index: 0 } } }], textures: [{}], nodes: [{ mesh: 0 }], cameras: [] };
  sc.load(mini, new Map([['q', buf.buffer]]));
  const n = FULL / TILE;
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const rgb = await gpu.drawRgb(g, TILE, { x: x / n, y: y / n, s: 1 / n });
    sc.setProcedureTile(0, 0, FULL, x * TILE, y * TILE, TILE, rgb);
  }
  log('procedure drawn');
  const im = gltf.images[tex.source];
  const blob = await (await fetch('../../site/scene/' + im.uri)).blob();
  const bmp = await createImageBitmap(blob, { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
  sc.setPicture(0, 0, bmp);
  const gl = sc.gl;
  const ortho = (x0, x1) => { const m = new Float32Array(16); const s = 2 / (x1 - x0); m[0] = s; m[5] = s; m[10] = -1; m[12] = -(x0 + x1) / (x1 - x0); m[13] = m[12]; m[15] = 1; return m; };
  const ident = new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);
  const px = new Uint8Array(512 * 512 * 4);
  for (const [vname, proj] of [['crop', ortho(0.375, 0.625)], ['whole', ortho(0, 1)]]) {
    for (const [mname, mode] of [['cross', 1], ['coarse', 2]]) {
      for (let k = 0; k <= 10; k++) {
        sc.textures[0].mode = k === 0 ? 0 : k === 10 ? 3 : mode;
        sc.textures[0].t = k / 10;
        sc.begin(null, [0, 0, 512, 512]);
        gl.disable(gl.CULL_FACE);
        gl.clearColor(0, 0, 0, 1);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        sc.drawAll(ident, proj, 0);
        gl.readPixels(0, 0, 512, 512, gl.RGBA, gl.UNSIGNED_BYTE, px);
        const oc = new OffscreenCanvas(512, 512);
        const ctx = oc.getContext('2d');
        const id = ctx.createImageData(512, 512);
        for (let j = 0; j < 512; j++) id.data.set(px.subarray((511 - j) * 2048, (512 - j) * 2048), j * 2048);
        ctx.putImageData(id, 0, 0);
        await post(`${TAG}-${vname}-${mname}-${String(k).padStart(2, '0')}.png`, await oc.convertToBlob({ type: 'image/png' }));
      }
    }
  }
  log('done');
  done('ok');
}
main().catch(async (e) => { log('FAILED ' + (e.stack || e)); await post(TAG + '-error.txt', String(e.stack || e)); done('failed'); });
