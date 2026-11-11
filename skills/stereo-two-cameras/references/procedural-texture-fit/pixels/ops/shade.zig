//! Shade (version 1): a material lit by a light from a direction, by its own height. The slope is measured in parts
//! of the picture (the height difference over the place difference, the height's depth given as a part of the
//! picture's width), so a tile is lit as the whole picture is at the same place: werkkzeug's Bump lights from a
//! lamp at a place in the picture it is drawn on, which lit every tile as a cushion of its own (milestone 2's
//! quilted rust). Lambert's cosine law with an ambient share; a flat face keeps its colour.
//! Reads one pixel each way: its margin is one pixel.
//! Version 2 (milestone 2e, Daniel on the metal plate: "a depth map and shadow - the one that is procedural"): a cast
//! shadow too. From each place, steps toward the light along the relief (steps, up to the shadow's length, in parts
//! of the picture): the ray rises from the place by the relief's whole height over the shadow's length (a piece of
//! full height casts a shadow that long), and where the relief stands above the ray the place lies in the shadow, by
//! how far it stands above (soft over a twentieth of the height), darkened by the shadow's strength.
//! Its margin is the shadow's length. A second input, where given, is the relief the light and the shadow read (its
//! height), the colour still the first's: a structure's own height lights a material whose colours were laid over it.
//! Version 1 graphs draw as before.
const c = @import("common.zig");

pub const name = "Shade";
pub const version: u32 = 1;
pub fn wordCount(ver: u32) usize {
    return if (ver >= 2) 9 else 6;
}
pub const inputs: u8 = 1;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 2, .min = 1, .max = 2 },
    .{ .kind = .float, .label = "to the light across", .offset = 1, .def = -0.5, .min = -1, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "to the light down", .offset = 2, .def = -0.5, .min = -1, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "to the light up", .offset = 3, .def = 0.7, .min = 0.05, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "depth", .offset = 4, .def = 0.004, .min = 0, .max = 0.2, .step = 0.0005 },
    .{ .kind = .float, .label = "strength", .offset = 5, .def = 0.6, .min = 0, .max = 1, .step = 0.05 },
    // version 2
    .{ .kind = .float, .label = "shadow", .offset = 6, .def = 0.5, .min = 0, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "shadow length", .offset = 7, .def = 0.01, .min = 0, .max = 0.2, .step = 0.001 },
    .{ .kind = .int, .label = "shadow steps", .offset = 8, .def = 16, .min = 1, .max = 64 },
};

pub fn margin(w: []const u32) f32 {
    if (w.len >= 9 and w[0] >= 2) return @max(1e-9, c.f32of(w[7]));
    return 1e-9; // one pixel, whatever the size: the drawing adds it
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    const ver = try c.versionUpTo(name, w, 2);
    var shk: f32 = 0;
    var shl: f32 = 0;
    var shn: i32 = 1;
    if (ver >= 2) {
        shk = try c.flt(&params, w, 6);
        shl = try c.flt(&params, w, 7);
        shn = try c.int(&params, w, 8);
    }
    var lx = try c.flt(&params, w, 1);
    var ly = try c.flt(&params, w, 2);
    var lz = try c.flt(&params, w, 3);
    const depth = try c.flt(&params, w, 4);
    const k = try c.flt(&params, w, 5);
    const ln = @sqrt(lx * lx + ly * ly + lz * lz);
    lx /= ln;
    ly /= ln;
    lz /= ln;
    const src = if (ver >= 2 and ins.len >= 2) ins[1] else ins[0];
    const col_src = ins[0];
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
            var s = 1.0 + k * (lam - 1.0);
            if (ver >= 2 and shk > 0 and shl > 0 and depth > 0) {
                // toward the light in the picture's plane, a pixel at a time of the shadow's length
                const lxy = @sqrt(lx * lx + ly * ly);
                if (lxy > 1e-6) {
                    const dx = lx / lxy;
                    const dy = ly / lxy;
                    const h0 = @as(f32, @floatFromInt(src.d[4 * (j * W + i) + 3])) / 32767.0;
                    var occ: f32 = 0;
                    const fi: f32 = @floatFromInt(i);
                    const fj: f32 = @floatFromInt(j);
                    var st: i32 = 1;
                    while (st <= shn) : (st += 1) {
                        const dist = shl * @as(f32, @floatFromInt(st)) / @as(f32, @floatFromInt(shn));
                        const px = dist / c.cv.px();
                        const si = @min(@as(f32, @floatFromInt(W - 1)), @max(0.0, @floor(fi + dx * px + 0.5)));
                        const sj = @min(@as(f32, @floatFromInt(H - 1)), @max(0.0, @floor(fj + dy * px + 0.5)));
                        const hs = @as(f32, @floatFromInt(src.d[4 * (@as(usize, @intFromFloat(sj)) * W + @as(usize, @intFromFloat(si))) + 3])) / 32767.0;
                        const ray = h0 + dist / shl;
                        occ = @max(occ, c.clamp01((hs - ray) * 20.0));
                    }
                    s *= 1.0 - shk * occ;
                }
            }
            const col = c.getc(col_src, j * W + i);
            c.putc(out, j * W + i, .{ col[0] * s, col[1] * s, col[2] * s, col[3] });
        }
    }
}
