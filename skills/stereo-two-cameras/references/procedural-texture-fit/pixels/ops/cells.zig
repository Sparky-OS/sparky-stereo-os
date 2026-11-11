//! Cells (version 1): cellular noise over the whole picture, one point jittered in every cell of a grid that
//! repeats, and its variants: cracks (the distance to the nearest point against the second nearest, small along
//! the borders between cells), stones and pebbles (a dome in each cell with a gap at its border and a shade of its
//! own), and patches or scales (one flat shade per cell). The place may be warped by noise first, for ragged cracks.
//! Source: Steven Worley, "A Cellular Texture Basis Function" (SIGGRAPH 1996): F1, F2 and F2 - F1 and the
//! per-cell id; written from the paper, no code copied. The search looks at the 3 by 3 cells around a place, which
//! finds the nearest point exactly while the jitter stays inside a cell, and the second nearest in all but rare
//! places (Worley's own note on the neighbourhood).
//! Output: a grey field (0 to 1) in red, green and blue, and the same value as the height in alpha.
const c = @import("common.zig");

pub const name = "Cells";
pub const version: u32 = 1;
pub const inputs: u8 = 0;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .cycle, .label = "kind", .offset = 1, .def = 0, .min = 0, .max = 2, .choices = "cracks|stones|patches" },
    .{ .kind = .int, .label = "cells across", .offset = 2, .def = 8, .min = 1, .max = 2048 },
    .{ .kind = .int, .label = "cells down", .offset = 3, .def = 8, .min = 1, .max = 2048 },
    .{ .kind = .float, .label = "jitter", .offset = 4, .def = 0.9, .min = 0, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "width", .offset = 5, .def = 0.08, .min = 0.001, .max = 1, .step = 0.01 },
    .{ .kind = .float, .label = "warp", .offset = 6, .def = 0, .min = 0, .max = 0.5, .step = 0.005 },
    .{ .kind = .int, .label = "warp cells", .offset = 7, .def = 8, .min = 1, .max = 512 },
    .{ .kind = .int, .label = "seed", .offset = 8, .def = 0, .min = 0, .max = 65535 },
    .{ .kind = .float, .label = "variation", .offset = 9, .def = 0.5, .min = 0, .max = 1, .step = 0.05 },
};

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 0;
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    _ = ins;
    try c.version(name, w, version);
    const kind = try c.int(&params, w, 1);
    const nx = try c.int(&params, w, 2);
    const ny = try c.int(&params, w, 3);
    const jit = try c.flt(&params, w, 4);
    const width = try c.flt(&params, w, 5);
    const warp = try c.flt(&params, w, 6);
    const wf = try c.int(&params, w, 7);
    const seed: u32 = @intCast(try c.int(&params, w, 8));
    const vary = try c.flt(&params, w, 9);
    const fnx: f32 = @floatFromInt(nx);
    const fny: f32 = @floatFromInt(ny);
    // distances are measured in cells of the mean side, so width means the same across and down
    const sx = @sqrt(fnx * fny) / fnx;
    const sy = @sqrt(fnx * fny) / fny;
    for (0..out.h) |j| {
        const v0 = c.cv.v(j);
        for (0..out.w) |i| {
            const p = c.warped(c.cv.u(i), v0, warp, wf, seed ^ 0x2c1b);
            const X = p[0] * fnx;
            const Y = p[1] * fny;
            const cx: i32 = @intFromFloat(@floor(X));
            const cy: i32 = @intFromFloat(@floor(Y));
            var d1: f32 = 1e9;
            var d2: f32 = 1e9;
            var id1: u32 = 0;
            var dy: i32 = -1;
            while (dy <= 1) : (dy += 1) {
                var dx: i32 = -1;
                while (dx <= 1) : (dx += 1) {
                    const gx = cx + dx;
                    const gy = cy + dy;
                    const h = c.hash3(c.wrap(gx, nx), c.wrap(gy, ny), seed);
                    const ox = 0.5 + jit * (c.rnd01(h) - 0.5);
                    const oy = 0.5 + jit * (c.rnd01(c.hash(h ^ 0x68e31da4)) - 0.5);
                    const ex = (@as(f32, @floatFromInt(gx)) + ox - X) * sx;
                    const ey = (@as(f32, @floatFromInt(gy)) + oy - Y) * sy;
                    const d = @sqrt(ex * ex + ey * ey);
                    if (d < d1) {
                        d2 = d1;
                        d1 = d;
                        id1 = h;
                    } else if (d < d2) d2 = d;
                }
            }
            const cellv = c.rnd01(c.hash(id1 ^ 0x1b873593));
            const shade = 1.0 - vary + vary * cellv;
            const g: f32 = switch (kind) {
                0 => c.smoothstep(0, width, d2 - d1),
                1 => blk: {
                    const gap = c.smoothstep(0, width, d2 - d1);
                    const dome = 1.0 - c.clamp01(d1 * d1);
                    break :blk shade * gap * (0.35 + 0.65 * dome);
                },
                else => shade,
            };
            c.putc(out, j * out.w + i, .{ g, g, g, g });
        }
    }
}
