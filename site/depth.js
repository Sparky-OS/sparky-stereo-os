/* One scene and a perspective camera. The edition browser's 3D Canvas route
 * supplies its parallel per-eye cameras at the matrix uniforms. No page-side
 * eye packing, colour filters, depth preferences or external library. */
(() => {
  'use strict';
  const wrap = document.querySelector('.depth-decoration');
  if (!wrap) return;
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const canvas = wrap.querySelector('canvas');
  let gl, program, projection, modelView, colour, position;
  let timer = 0, elapsed = 0, previous = 0, inView = false, lost = false;
  const duration = 4800; // Stops before five seconds; no continuous distraction.
  const faces = [];
  const quad = (x, y, z, w, h, rgb) => {
    faces.push({vertices: new Float32Array([
      x,y,z, x+w,y,z, x+w,y+h,z, x,y,z, x+w,y+h,z, x,y+h,z
    ]), rgb});
  };
  const windowPlane = (x, y, z, w, h, rgb) => {
    quad(x,y,z,w,h,rgb);
    quad(x+.025,y+.025,z+.002,w-.05,h-.05,[.15,.17,.20]);
    quad(x+.025,y+h-.14,z+.004,w-.05,.115,rgb);
    for (let n=0;n<3;n++) quad(x+w-.09-n*.09,y+h-.105,z+.006,.035,.035,[.96,.89,.82]);
    for (let n=0;n<4;n++) quad(x+.10,y+h-.25-n*.13,z+.006,w*(n%2?.42:.66),.025,[.51,.58,.64]);
  };
  windowPlane(-1.18,-.72,-.65,1.95,1.30,[.28,.47,.65]);
  windowPlane(-.66,-.53,0,1.55,1.10,[.35,.67,.94]);
  windowPlane(-.05,-.43,.65,1.03,.69,[.94,.83,.72]);

  function setup() {
    if (gl) return true;
    gl = canvas.getContext('webgl', {alpha:true, antialias:true, depth:true});
    if (!gl) return false;
    function shader(type, source) {
      const item=gl.createShader(type);
      gl.shaderSource(item,source); gl.compileShader(item);
      if (!gl.getShaderParameter(item,gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(item));
      return item;
    }
    try {
      const vertex=shader(gl.VERTEX_SHADER,`attribute vec3 position;
        uniform mat4 projectionMatrix; uniform mat4 modelViewMatrix;
        void main() { gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`);
      const fragment=shader(gl.FRAGMENT_SHADER,`precision mediump float;
        uniform vec3 colour; void main() { gl_FragColor=vec4(colour,1.0); }`);
      program=gl.createProgram(); gl.attachShader(program,vertex); gl.attachShader(program,fragment);
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program,gl.LINK_STATUS)) throw Error(gl.getProgramInfoLog(program));
      gl.deleteShader(vertex); gl.deleteShader(fragment); gl.useProgram(program);
      position=gl.getAttribLocation(program,'position');
      projection=gl.getUniformLocation(program,'projectionMatrix');
      modelView=gl.getUniformLocation(program,'modelViewMatrix');
      colour=gl.getUniformLocation(program,'colour');
      for (const face of faces) {
        face.buffer=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,face.buffer);
        gl.bufferData(gl.ARRAY_BUFFER,face.vertices,gl.STATIC_DRAW);
      }
      gl.enable(gl.DEPTH_TEST); gl.enableVertexAttribArray(position);
      return true;
    } catch (error) {
      console.warn('Depth decoration unavailable:',error.message);
      lost=true; return false;
    }
  }
  function draw() {
    const scale=Math.min(devicePixelRatio||1,1.5);
    const width=Math.max(1,Math.round(wrap.clientWidth*scale));
    const height=Math.max(1,Math.round(wrap.clientHeight*scale));
    if (canvas.width!==width || canvas.height!==height) { canvas.width=width; canvas.height=height; }
    gl.viewport(0,0,width,height); gl.clearColor(0,0,0,0);
    gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    const near=.8, far=12, focal=2.3, aspect=width/height;
    // Column-major perspective and view matrices retain world depth, allowing
    // the browser to replace the camera before each eye's geometry is drawn.
    const p=new Float32Array([focal/aspect,0,0,0, 0,focal,0,0,
      0,0,(far+near)/(near-far),-1, 0,0,2*far*near/(near-far),0]);
    const angle=-.28+.30*Math.sin(elapsed/duration*Math.PI/2);
    const c=Math.cos(angle),s=Math.sin(angle);
    const view=new Float32Array([c,0,-s,0, 0,1,0,0, s,0,c,0, 0,0,-3.4,1]);
    gl.uniformMatrix4fv(projection,false,p); gl.uniformMatrix4fv(modelView,false,view);
    for (const face of faces) {
      gl.bindBuffer(gl.ARRAY_BUFFER,face.buffer); gl.vertexAttribPointer(position,3,gl.FLOAT,false,0,0);
      gl.uniform3fv(colour,face.rgb); gl.drawArrays(gl.TRIANGLES,0,6);
    }
    wrap.classList.add('depth-ready');
  }
  function allowed() { return !motion.matches && !document.hidden && inView && !lost; }
  function frame(now) {
    timer=0;
    if (!allowed()) { previous=0; return; }
    if (previous) elapsed=Math.min(duration,elapsed+now-previous);
    previous=now;
    draw();
    if (elapsed<duration) timer=requestAnimationFrame(frame);
  }
  function update() {
    if (timer) cancelAnimationFrame(timer);
    timer=0; previous=0;
    if (motion.matches || lost) wrap.classList.remove('depth-ready');
    if (allowed() && setup()) timer=requestAnimationFrame(frame);
  }
  canvas.addEventListener('webglcontextlost',event=>{
    event.preventDefault(); lost=true; update();
  });
  motion.addEventListener('change',update);
  document.addEventListener('visibilitychange',update);
  new IntersectionObserver(entries=>{ inView=entries[0].isIntersecting; update(); }).observe(wrap);
  new ResizeObserver(update).observe(wrap);
})();
