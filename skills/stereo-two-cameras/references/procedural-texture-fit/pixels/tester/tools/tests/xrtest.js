// The tester's per-view drawing without a headset (ORDER 508, milestone 3; ORDER 537: this tree's paths, results read by the driver): GlScene.frameXr given a stand-in for a
// WebXR frame with two views as a flat display gives them (parallel axes 64 mm apart, each frustum shifted so both
// meet at the plane 3 m away: no turn), into the two halves of one canvas, the left view on the left. The scene is
// the one served (with a per-eye texture where its file has one); the pictures only (each texture's picture as it
// would be after its blend). The halves are posted as PNGs. xrtest.html?tag=NAME. Our code, BSD 2-clause.
import { GlScene, M } from '../../site/gl-scene.js';
const Q = new URLSearchParams(location.search);
const TAG = Q.get('tag') || 'xr';
// results are kept in the page and read by the driver (drive.py saves every entry of window.testerFiles): no server routes
window.testerFiles = {};
window.testerState = () => null;
const b64 = (u8) => { let s = ''; for (let i = 0; i < u8.length; i += 32768) s += String.fromCharCode(...u8.subarray(i, i + 32768)); return btoa(s); };
const post = async (name, body) => { window.testerFiles[name] = typeof body === 'string' ? 'text:' + body : 'base64:' + b64(new Uint8Array(body instanceof Blob ? await body.arrayBuffer() : body.buffer || body)); };
const done = (how) => { window.testerResult = JSON.stringify({ result: how, files: Object.keys(window.testerFiles) }); };
async function main() {
  const gltf = await (await fetch('../../site/scene/scene.gltf')).json();
  const buffers = new Map();
  for (const b of gltf.buffers) buffers.set(b.uri, await (await fetch('../../site/scene/' + b.uri)).arrayBuffer());
  const sc = new GlScene(document.getElementById('c'));
  sc.load(gltf, buffers);
  for (let ti = 0; ti < gltf.textures.length; ti++) {
    const tex = gltf.textures[ti];
    const views = tex.extensions && tex.extensions.KHR_texture_procedural_rendering && tex.extensions.KHR_texture_procedural_rendering.views;
    const srcs = views ? [views.find((v) => v.eye === 'left').source, views.find((v) => v.eye === 'right').source] : [tex.source];
    for (let e = 0; e < srcs.length; e++) {
      const bmp = await createImageBitmap(await (await fetch('../../site/scene/' + gltf.images[srcs[e]].uri)).blob(), { colorSpaceConversion: 'none' });
      sc.setPicture(ti, e, bmp);
    }
    sc.textures[ti].mode = 3;
  }
  const cam = sc.cameraPose().world;               // the views start at the scene's camera
  const W = 800, H = 600, near = 0.05, far = 50, D = 3.0, ipd = 0.064;
  const top = near * Math.tan((42 * Math.PI / 180) / 2), aspect = W / H;
  const views = ['left', 'right'].map((eye, k) => {
    const s = k ? 1 : -1;
    const shift = -s * (ipd / 2) * near / D;      // the frustum shifted toward the other eye: both meet at D
    const r = top * aspect;
    const proj = new Float32Array(16);
    const l = -r + shift, rr = r + shift, b = -top, t = top;
    proj[0] = 2 * near / (rr - l); proj[5] = 2 * near / (t - b); proj[8] = (rr + l) / (rr - l); proj[9] = (t + b) / (t - b);
    proj[10] = -(far + near) / (far - near); proj[11] = -1; proj[14] = -2 * far * near / (far - near);
    const eyeWorld = M.mul(cam, M.trs([s * ipd / 2, 0, 0]));   // the same orientation, moved along the camera's own x
    return { eye, projectionMatrix: proj, transform: { inverse: { matrix: M.invertRigid(eyeWorld) } } };
  });
  const frame = { getViewerPose: () => ({ views }) };
  const layer = { framebuffer: null, getViewport: (v) => ({ x: v.eye === 'left' ? 0 : W, y: 0, width: W, height: H }) };
  sc.frameXr(frame, null, layer);
  const gl = sc.gl;
  const px = new Uint8Array(2 * W * H * 4);
  gl.readPixels(0, 0, 2 * W, H, gl.RGBA, gl.UNSIGNED_BYTE, px);
  for (const [k, eye] of [[0, 'left'], [1, 'right']]) {
    const oc = new OffscreenCanvas(W, H), ctx = oc.getContext('2d'), id = ctx.createImageData(W, H);
    for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
      const src = ((H - 1 - j) * 2 * W + k * W + i) * 4, dst = (j * W + i) * 4;
      id.data[dst] = px[src]; id.data[dst + 1] = px[src + 1]; id.data[dst + 2] = px[src + 2]; id.data[dst + 3] = 255;
    }
    ctx.putImageData(id, 0, 0);
    await post(`${TAG}-${eye}.png`, await oc.convertToBlob({ type: 'image/png' }));
  }
  await post(`${TAG}-views.json`, JSON.stringify({ D, ipd, W, H, yfovDeg: 42, camera: Array.from(cam) }));
  done('ok');
}
main().catch(async (e) => { await post(TAG + '-error.txt', String(e.stack || e)); done('failed'); });
