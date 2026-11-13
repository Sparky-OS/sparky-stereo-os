/* The desktop's three levels as one small world: a window behind the screen,
 * the window in use at the screen, its menu in front. One scene, one perspective
 * camera in two matrix uniforms: the edition browser's 3D Canvas route puts its
 * two parallel cameras there. No eye packing, colour filter, depth setting or
 * library on the page; any other browser shows an ordinary moving drawing. */
(() => {
  'use strict';
  const wrap = document.querySelector('.depth-decoration');
  if (!wrap) return;
  const canvas = wrap.querySelector('canvas');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');

  /* Where the planes stand decides what each eye sees, so the distances follow
   * the browser's two rules for its screen plane, with D the camera's distance
   * to the window in use:
   *   - five times the camera's near distance: NEAR = D / 5;
   *   - where the nearest and the farthest part have equal and opposite
   *     parallax, 2nf / (n + f): D / (1 + R) and D / (1 - R) balance at D.
   * R = 0.4 is the desktop's default popped limit over its sunk limit (4 and 10),
   * so the menu comes forward as far as a menu does and no further. */
  const D = 3.4, NEAR = D / 5, FAR = 14, FOCAL = 2.3, R = 0.4;
  const SWEEP = 0.8, DURATION = 4800; // the viewpoint's sideways start; stops before five seconds
  const rgb = (r, g, b) => [r / 255, g / 255, b / 255];
  const BODY = rgb(38, 43, 51), ROW = rgb(130, 148, 163), BUTTON = rgb(245, 227, 209);
  const PLANES = [
    {name: 'sunk', distance: D / (1 - R), frame: [71, 120, 166], marker: [176, 200, 222]},
    {name: 'screen', distance: D, frame: [89, 171, 240], marker: [232, 242, 252]},
    {name: 'popped', distance: D / (1 + R), frame: [240, 212, 184], marker: [230, 126, 34]}
  ];
  const data = [];
  /* A rectangle given as it lies on the screen plane (x, y, width, height) and
   * drawn at its plane's distance, scaled so it covers the same part of the view. */
  const rect = (plane, x, y, w, h, colour, lift) => {
    const k = plane.distance / D, z = D - plane.distance + (lift || 0);
    const x0 = x * k, y0 = y * k, x1 = (x + w) * k, y1 = (y + h) * k;
    for (const [px, py] of [[x0, y0], [x1, y0], [x1, y1], [x0, y0], [x1, y1], [x0, y1]])
      data.push(px, py, z, colour[0], colour[1], colour[2]);
  };
  const frame = plane => rgb(...plane.frame), mark = plane => rgb(...plane.marker);
  const windowAt = (plane, x, y, w, h) => {
    rect(plane, x, y, w, h, frame(plane));
    rect(plane, x + .03, y + .03, w - .06, h - .19, BODY, .002);
    rect(plane, x + .05, y + h - .125, .09, .09, mark(plane), .004); // the window's icon
    for (let n = 0; n < 3; n++) rect(plane, x + w - .11 - n * .11, y + h - .105, .05, .05, BUTTON, .004);
    for (let n = 0; n < 4; n++) rect(plane, x + .12, y + h - .36 - n * .17, (w - .24) * (n % 2 ? .45 : .7), .035, ROW, .004);
    plane.markerLift = .004;
  };
  const menuAt = (plane, x, y, w, h) => {
    rect(plane, x, y, w, h, frame(plane));
    rect(plane, x + .03, y + .03, w - .06, h - .06, BODY, .002);
    const step = (h - .06) / 4;
    for (let n = 0; n < 4; n++) {
      const top = y + h - .03 - step * (n + 1);
      if (n === 1) rect(plane, x + .06, top + .03, w - .12, step - .06, mark(plane), .004); // the chosen entry
      rect(plane, x + .14, top + step / 2 - .018, (w - .28) * (n % 2 ? .8 : .6), .036, n === 1 ? BODY : ROW, .006);
    }
    plane.markerLift = .004;
  };
  windowAt(PLANES[0], -1.45, -.35, 1.8, 1.4);
  windowAt(PLANES[1], -.95, -.8, 1.8, 1.5);
  menuAt(PLANES[2], .15, -1.05, 1.1, 1.25);
  const vertices = new Float32Array(data);

  let gl, projection, modelView, timer = 0, elapsed = 0, previous = 0, inView = false, lost = false;
  function off(reason) {
    lost = true; wrap.classList.remove('depth-ready'); wrap.classList.add('depth-off');
    if (reason) console.warn('Depth drawing not shown:', reason);
  }
  function setup() {
    if (gl) return true;
    gl = canvas.getContext('webgl', {alpha: true, antialias: true, depth: true});
    if (!gl) { off('this browser offers no WebGL'); return false; }
    try {
      const shader = (type, source) => {
        const item = gl.createShader(type);
        gl.shaderSource(item, source); gl.compileShader(item);
        if (!gl.getShaderParameter(item, gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(item));
        return item;
      };
      const program = gl.createProgram();
      gl.attachShader(program, shader(gl.VERTEX_SHADER, `attribute vec3 position; attribute vec3 colour;
        uniform mat4 projectionMatrix; uniform mat4 modelViewMatrix; varying vec3 tint;
        void main() { tint = colour; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`));
      gl.attachShader(program, shader(gl.FRAGMENT_SHADER, `precision mediump float; varying vec3 tint;
        void main() { gl_FragColor = vec4(tint, 1.0); }`));
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error(gl.getProgramInfoLog(program));
      gl.useProgram(program);
      projection = gl.getUniformLocation(program, 'projectionMatrix');
      modelView = gl.getUniformLocation(program, 'modelViewMatrix');
      gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
      gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
      const position = gl.getAttribLocation(program, 'position'), colour = gl.getAttribLocation(program, 'colour');
      gl.enableVertexAttribArray(position); gl.vertexAttribPointer(position, 3, gl.FLOAT, false, 24, 0);
      gl.enableVertexAttribArray(colour); gl.vertexAttribPointer(colour, 3, gl.FLOAT, false, 24, 12);
      gl.enable(gl.DEPTH_TEST);
      // The scene's own numbers, for a measurement to read; nothing on the page uses them.
      canvas.dataset.scene = JSON.stringify({distance: D, near: NEAR, focal: FOCAL, planes: PLANES.map(p => (
        {name: p.name, distance: p.distance, markerDistance: p.distance - p.markerLift, frame: p.frame, marker: p.marker,
         around: p.name === 'popped' ? [38, 43, 51] : p.frame}))});
      return true;
    } catch (error) {
      off(error.message); return false;
    }
  }
  function draw() {
    const scale = Math.min(devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.round(wrap.clientWidth * scale));
    const height = Math.max(1, Math.round(wrap.clientHeight * scale));
    if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
    gl.viewport(0, 0, width, height); gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    const aspect = width / height;
    // Column-major matrices. The viewpoint moves sideways and comes to rest in
    // front of the window in use, which stays where it is: a shear of x by z.
    // No plane ever tilts, so each keeps one distance in every frame, as on the
    // desktop, and the browser reads the same scene depth from the first frame.
    const p = new Float32Array([FOCAL / aspect, 0, 0, 0, 0, FOCAL, 0, 0,
      0, 0, (FAR + NEAR) / (NEAR - FAR), -1, 0, 0, 2 * FAR * NEAR / (NEAR - FAR), 0]);
    const side = -SWEEP * (1 - Math.sin(elapsed / DURATION * Math.PI / 2));
    const view = new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, -side / D, 0, 1, 0, 0, 0, -D, 1]);
    gl.uniformMatrix4fv(projection, false, p); gl.uniformMatrix4fv(modelView, false, view);
    gl.drawArrays(gl.TRIANGLES, 0, vertices.length / 6);
    wrap.classList.add('depth-ready');
    if (elapsed >= DURATION) canvas.dataset.rest = '1'; else delete canvas.dataset.rest;
  }
  function allowed() { return !motion.matches && !document.hidden && inView && !lost; }
  function tick(now) {
    timer = 0;
    if (!allowed()) { previous = 0; return; }
    if (previous) elapsed = Math.min(DURATION, elapsed + now - previous);
    previous = now;
    draw();
    if (elapsed < DURATION) timer = requestAnimationFrame(tick);
  }
  function update() {
    if (timer) cancelAnimationFrame(timer);
    timer = 0; previous = 0;
    if (motion.matches || lost) wrap.classList.remove('depth-ready');
    if (allowed() && setup()) timer = requestAnimationFrame(tick);
  }
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault(); off('the WebGL context was lost'); update();
  });
  motion.addEventListener('change', update);
  document.addEventListener('visibilitychange', update);
  new IntersectionObserver(entries => { inView = entries[0].isIntersecting; update(); }).observe(wrap);
  new ResizeObserver(update).observe(wrap);
})();
