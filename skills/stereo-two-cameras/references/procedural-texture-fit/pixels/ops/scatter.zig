//! Scatter (version 1): one seed placed many times. Every cell of a grid that repeats over the picture holds an
//! instance or not (the density), placed off the cell's centre (jitter), sized, turned and shaded each by a value of
//! its own, so the same seed does not read as a repeat. The seed is the second input's picture (a glyph drawn by
//! Text, a leaf, a drip) read as a coverage (its grey), or, with no second input, a soft disc stretched down by
//! the aspect (pits, specks, pebbles, drops). Each instance is laid over the base in its colour and raises or
//! sinks the height by its own amount.
//! Bounded: a place looks at the cells within reach of the largest instance (at most 7 by 7 cells; a size above
//! one and a half cells is refused). The turn is a polynomial sine and cosine (no maths library).
const c = @import("common.zig");

pub const name = "Scatter";
pub const version: u32 = 1;
pub const inputs: u8 = 1; // the base; a second input is the seed's picture
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .int, .label = "cells across", .offset = 1, .def = 16, .min = 1, .max = 4096 },
    .{ .kind = .int, .label = "cells down", .offset = 2, .def = 16, .min = 1, .max = 4096 },
    .{ .kind = .float, .label = "density", .offset = 3, .def = 0.5, .min = 0, .max = 1, .step = 0.02 },
    .{ .kind = .float, .label = "size", .offset = 4, .def = 0.3, .min = 0.005, .max = 1.5, .step = 0.01 },
    .{ .kind = .float, .label = "size variation", .offset = 5, .def = 0.3, .min = 0, .max = 1, .step = 0.02 },
    .{ .kind = .float, .label = "turn", .offset = 6, .def = 0, .min = 0, .max = 0.5, .step = 0.01 },
    .{ .kind = .float, .label = "jitter", .offset = 7, .def = 0.8, .min = 0, .max = 1, .step = 0.05 },
    .{ .kind = .rgba, .label = "colour", .offset = 8, .def = 0xff202020, .min = 0, .max = 0xffffffff },
    .{ .kind = .float, .label = "colour variation", .offset = 9, .def = 0.2, .min = 0, .max = 1, .step = 0.02 },
    .{ .kind = .int, .label = "seed", .offset = 10, .def = 0, .min = 0, .max = 65535 },
    .{ .kind = .float, .label = "height", .offset = 11, .def = -0.3, .min = -1, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "softness", .offset = 12, .def = 0.4, .min = 0.01, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "aspect", .offset = 13, .def = 1, .min = 0.2, .max = 8, .step = 0.1 },
    .{ .kind = .float, .label = "opacity", .offset = 14, .def = 1, .min = 0, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "phase across", .offset = 15, .def = 0, .min = -1, .max = 1, .step = 0.01 },
    .{ .kind = .float, .label = "phase down", .offset = 16, .def = 0, .min = -1, .max = 1, .step = 0.01 },
};

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 0;
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    try c.version(name, w, version);
    const nx = try c.int(&params, w, 1);
    const ny = try c.int(&params, w, 2);
    const dens = try c.flt(&params, w, 3);
    const size = try c.flt(&params, w, 4);
    const svar = try c.flt(&params, w, 5);
    const turn = try c.flt(&params, w, 6);
    const jit = try c.flt(&params, w, 7);
    const col = c.rgb(w[8]);
    const cvar = try c.flt(&params, w, 9);
    const seed: u32 = @intCast(try c.int(&params, w, 10));
    const hgt = try c.flt(&params, w, 11);
    const soft = try c.flt(&params, w, 12);
    const aspect = try c.flt(&params, w, 13);
    const opac = try c.flt(&params, w, 14);
    const phx = try c.flt(&params, w, 15);
    const phy = try c.flt(&params, w, 16);
    const fnx: f32 = @floatFromInt(nx);
    const fny: f32 = @floatFromInt(ny);
    const cw = 1.0 / fnx;
    const ch = 1.0 / fny;
    const m = @min(cw, ch);
    const rmax = size * m * (1.0 + svar) * @max(1.0, aspect);
    const reach_f = @ceil(rmax / m + jit * 0.5 + @max(@abs(phx), @abs(phy)));
    if (reach_f > 3) return c.refuse("Scatter: an instance reaches {d} cells; at most 3 (size times aspect too large for the grid)", .{reach_f});
    const reach: i32 = @intFromFloat(reach_f);
    const stamp: ?c.Pix = if (ins.len >= 2) ins[1] else null;
    for (0..out.h) |j| {
        const v = c.cv.v(j);
        const Y = v * fny - phy;
        const cy: i32 = @intFromFloat(@floor(Y));
        for (0..out.w) |i| {
            const u = c.cv.u(i);
            const X = u * fnx - phx;
            const cx: i32 = @intFromFloat(@floor(X));
            var o = c.getc(ins[0], j * out.w + i);
            var dy: i32 = -reach;
            while (dy <= reach) : (dy += 1) {
                var dx: i32 = -reach;
                while (dx <= reach) : (dx += 1) {
                    const gx = cx + dx;
                    const gy = cy + dy;
                    const h = c.hash3(c.wrap(gx, nx), c.wrap(gy, ny), seed);
                    if (c.rnd01(h) >= dens) continue;
                    const h2 = c.hash(h ^ 0x2545f491);
                    const h3 = c.hash(h2 ^ 0x9e3779b9);
                    const h4 = c.hash(h3 ^ 0x85ebca6b);
                    const h5 = c.hash(h4 ^ 0xc2b2ae35);
                    const px = (@as(f32, @floatFromInt(gx)) + 0.5 + phx + jit * (c.rnd01(h2) - 0.5)) * cw;
                    const py = (@as(f32, @floatFromInt(gy)) + 0.5 + phy + jit * (c.rnd01(h3) - 0.5)) * ch;
                    const r = size * m * (1.0 + svar * (2.0 * c.rnd01(h4) - 1.0));
                    const sc = c.sincosTurns(turn * (2.0 * c.rnd01(h5) - 1.0));
                    const ex = u - px;
                    const ey = v - py;
                    const qx = (ex * sc[1] + ey * sc[0]) / r;
                    const qy = (-ex * sc[0] + ey * sc[1]) / (r * aspect);
                    var cov: f32 = 0;
                    if (stamp) |st| {
                        const sx = (0.5 + 0.5 * qx) * @as(f32, @floatFromInt(st.w)) - 0.5;
                        const sy = (0.5 + 0.5 * qy) * @as(f32, @floatFromInt(st.h)) - 0.5;
                        if (sx > -1 and sy > -1 and sx < @as(f32, @floatFromInt(st.w)) and sy < @as(f32, @floatFromInt(st.h))) {
                            const x0 = @floor(sx);
                            const y0 = @floor(sy);
                            const fx = sx - x0;
                            const fy = sy - y0;
                            const ix: i32 = @intFromFloat(x0);
                            const iy: i32 = @intFromFloat(y0);
                            var acc: f32 = 0;
                            inline for (0..2) |b| {
                                inline for (0..2) |a| {
                                    const xx: i32 = ix + @as(i32, a);
                                    const yy: i32 = iy + @as(i32, b);
                                    const wgt = (if (a == 0) 1.0 - fx else fx) * (if (b == 0) 1.0 - fy else fy);
                                    if (xx >= 0 and yy >= 0 and xx < @as(i32, @intCast(st.w)) and yy < @as(i32, @intCast(st.h)))
                                        acc += wgt * c.grey(st, @as(usize, @intCast(yy)) * st.w + @as(usize, @intCast(xx)));
                                }
                            }
                            cov = acc;
                        }
                    } else {
                        const dd = @sqrt(qx * qx + qy * qy);
                        cov = 1.0 - c.smoothstep(1.0 - soft, 1.0, dd);
                    }
                    if (cov <= 0) continue;
                    const a = cov * opac;
                    const shade = 1.0 + cvar * (2.0 * c.rnd01(c.hash(h5 ^ 0x27d4eb2f)) - 1.0);
                    inline for (0..3) |q| o[q] = c.lerp(o[q], c.clamp01(col[q] * shade), a);
                    o[3] = c.clamp01(o[3] + hgt * cov);
                }
            }
            c.putc(out, j * out.w + i, o);
        }
    }
}
