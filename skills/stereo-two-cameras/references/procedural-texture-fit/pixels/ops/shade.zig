//! Shade (version 1): a material lit by a light from a direction, by its own height. The slope is measured in parts
//! of the picture (the height difference over the place difference, the height's depth given as a part of the
//! picture's width), so a tile is lit as the whole picture is at the same place: werkkzeug's Bump lights from a
//! lamp at a place in the picture it is drawn on, which lit every tile as a cushion of its own (milestone 2's
//! quilted rust). Lambert's cosine law with an ambient share; a flat face keeps its colour.
//! Reads one pixel each way: its margin is one pixel.
const c = @import("common.zig");

pub const name = "Shade";
pub const version: u32 = 1;
pub const inputs: u8 = 1;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .float, .label = "to the light across", .offset = 1, .def = -0.5, .min = -1, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "to the light down", .offset = 2, .def = -0.5, .min = -1, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "to the light up", .offset = 3, .def = 0.7, .min = 0.05, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "depth", .offset = 4, .def = 0.004, .min = 0, .max = 0.2, .step = 0.0005 },
    .{ .kind = .float, .label = "strength", .offset = 5, .def = 0.6, .min = 0, .max = 1, .step = 0.05 },
};

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 1e-9; // one pixel, whatever the size: the drawing adds it
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    try c.version(name, w, version);
    var lx = try c.flt(&params, w, 1);
    var ly = try c.flt(&params, w, 2);
    var lz = try c.flt(&params, w, 3);
    const depth = try c.flt(&params, w, 4);
    const k = try c.flt(&params, w, 5);
    const ln = @sqrt(lx * lx + ly * ly + lz * lz);
    lx /= ln;
    ly /= ln;
    lz /= ln;
    const src = ins[0];
    const W = out.w;
    const H = out.h;
    const step = 2.0 * c.cv.px();
    for (0..H) |j| {
        const jm = if (j > 0) j - 1 else j;
        const jp = if (j + 1 < H) j + 1 else j;
        for (0..W) |i| {
            const im = if (i > 0) i - 1 else i;
            const ip = if (i + 1 < W) i + 1 else i;
            const hx = (@as(f32, @floatFromInt(src.d[4 * (j * W + ip) + 3])) - @as(f32, @floatFromInt(src.d[4 * (j * W + im) + 3]))) / 32767.0;
            const hy = (@as(f32, @floatFromInt(src.d[4 * (jp * W + i) + 3])) - @as(f32, @floatFromInt(src.d[4 * (jm * W + i) + 3]))) / 32767.0;
            const nx = -depth * hx / step;
            const ny = -depth * hy / step;
            const nn = @sqrt(nx * nx + ny * ny + 1.0);
            const lam = @max(0.0, (nx * lx + ny * ly + lz) / nn) / lz; // 1 on a flat face
            const s = 1.0 + k * (lam - 1.0);
            const col = c.getc(src, j * W + i);
            c.putc(out, j * W + i, .{ col[0] * s, col[1] * s, col[2] * s, col[3] });
        }
    }
}
