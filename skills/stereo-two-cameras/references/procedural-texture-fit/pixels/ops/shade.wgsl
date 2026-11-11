// Shade (version 1): the WGSL twin of shade.zig: the slope from one pixel each way, clamped at the canvas's edge.
// Bindings: 1 the output, 2 the material.
@group(0) @binding(1) var<storage, read_write> outp: array<vec2<u32>>;
@group(0) @binding(2) var<storage, read> in0: array<vec2<u32>>;

fn alphaAt(i: u32, j: u32) -> f32 { return f32(in0[j * u.w + i].y >> 16u); }

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3<u32>) {
    if (id.x >= u.w || id.y >= u.h) { return; }
    var lx = wf(1u);
    var ly = wf(2u);
    var lz = wf(3u);
    let depth = wf(4u);
    let k = wf(5u);
    let ln = sqrt(lx * lx + ly * ly + lz * lz);
    lx /= ln;
    ly /= ln;
    lz /= ln;
    let i = id.x;
    let j = id.y;
    let im = select(i, i - 1u, i > 0u);
    let ip = select(i, i + 1u, i + 1u < u.w);
    let jm = select(j, j - 1u, j > 0u);
    let jp = select(j, j + 1u, j + 1u < u.h);
    let stp = 2.0 * pxs();
    let hx = (alphaAt(ip, j) - alphaAt(im, j)) / 32767.0;
    let hy = (alphaAt(i, jp) - alphaAt(i, jm)) / 32767.0;
    let nx = -depth * hx / stp;
    let ny = -depth * hy / stp;
    let nn = sqrt(nx * nx + ny * ny + 1.0);
    let lam = max(0.0, (nx * lx + ny * ly + lz) / nn) / lz;
    let s = 1.0 + k * (lam - 1.0);
    let col = unpack(in0[j * u.w + i]);
    outp[j * u.w + i] = pack(vec4<f32>(col.x * s, col.y * s, col.z * s, col.w));
}
