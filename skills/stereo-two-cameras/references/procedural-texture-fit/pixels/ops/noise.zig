//! Noise (version 1): fractal gradient noise over the whole picture, with its ridged and billowed kinds, a different
//! frequency across and down for grain that runs one way (brushed metal, fibres, bark), and the noise warped by
//! noise (Quilez's domain warping) for furrows, wood grain, veins and clouds.
//! Sources: Perlin, "An Image Synthesizer" (SIGGRAPH 1985) and "Improving Noise" (SIGGRAPH 2002) for the gradient
//! noise and its fade; Musgrave in Ebert et al., "Texturing and Modeling: A Procedural Approach" (1994 and later
//! editions) for the fractal sum and the ridged kind; Inigo Quilez, "domain warping" (iquilezles.org, 2002) for
//! the warp. Written from those texts; no code copied.
//! Output: a grey field (0 to 1) in red, green and blue, and the same value as the height in alpha.
const c = @import("common.zig");

pub const name = "Noise";
pub const version: u32 = 1;
pub const inputs: u8 = 0;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .cycle, .label = "kind", .offset = 1, .def = 0, .min = 0, .max = 2, .choices = "fbm|ridged|billow" },
    .{ .kind = .int, .label = "cells across", .offset = 2, .def = 4, .min = 1, .max = 4096 },
    .{ .kind = .int, .label = "cells down", .offset = 3, .def = 4, .min = 1, .max = 4096 },
    .{ .kind = .int, .label = "octaves", .offset = 4, .def = 6, .min = 1, .max = 12 },
    .{ .kind = .float, .label = "gain", .offset = 5, .def = 0.5, .min = 0.05, .max = 0.95, .step = 0.05 },
    .{ .kind = .float, .label = "warp", .offset = 6, .def = 0, .min = 0, .max = 1, .step = 0.01 },
    .{ .kind = .int, .label = "warp cells", .offset = 7, .def = 2, .min = 1, .max = 256 },
    .{ .kind = .int, .label = "seed", .offset = 8, .def = 0, .min = 0, .max = 65535 },
    .{ .kind = .float, .label = "contrast", .offset = 9, .def = 1, .min = 0.05, .max = 20, .step = 0.1 },
};

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 0;
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    _ = ins;
    try c.version(name, w, version);
    const kind: c.NoiseKind = @enumFromInt(@as(u32, @intCast(try c.int(&params, w, 1))));
    const fx = try c.int(&params, w, 2);
    const fy = try c.int(&params, w, 3);
    const oct: u32 = @intCast(try c.int(&params, w, 4));
    const gain = try c.flt(&params, w, 5);
    const warp = try c.flt(&params, w, 6);
    const wf = try c.int(&params, w, 7);
    const seed: u32 = @intCast(try c.int(&params, w, 8));
    const con = try c.flt(&params, w, 9);
    for (0..out.h) |j| {
        const v0 = c.cv.v(j);
        for (0..out.w) |i| {
            const p = c.warped(c.cv.u(i), v0, warp, wf, seed);
            const n = c.fbm(p[0], p[1], fx, fy, oct, gain, seed, kind);
            const g = if (kind == .fbm) c.clamp01(0.5 + 0.5 * con * n) else c.clamp01(0.5 + con * (n - 0.5));
            c.putc(out, j * out.w + i, .{ g, g, g, g });
        }
    }
}
