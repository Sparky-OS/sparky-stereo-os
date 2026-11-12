//! Quad (version 1, milestone 2d): four procedures per picture. Daniel, 11 November 2026: "the current procedure
//! canvas become one quarter of the final image, not more operations on top, but four different operations per
//! quadrant, meaning, 4 simple procedures maped to one hi res image".
//! Its four inputs are four whole procedures, each fitted to one quarter of the picture as if that quarter were a
//! picture of its own: input 1 the top left quarter, 2 the top right, 3 the bottom left, 4 the bottom right. Each
//! input is drawn on its own canvas: where this operator shows the place x, y of the whole picture, input q is drawn
//! at its own place 2x - column, 2y - row (p2p.zig's drawCanvas and the page's drawGpu do that before this operator
//! runs; every canvas has the same side and margin, so pixel k of an input lies under pixel k of the output).
//! Where two quarters meet (the cross in the middle, and the picture's own edges, since the picture repeats), the
//! seam: cut (each quarter alone up to its border), mix (the two, or four at the corner, mixed linearly across a band
//! on each side of the border), keep (mixed so the detail keeps its contrast: Eric Heitz and Fabrice Neyret's
//! variance-preserving blend, 2018, written from the paper: the mean of the means plus the departures from each
//! input's own mean, divided by the root of the sum of the squared weights; the means are the inputs' mean colours,
//! measured by the fitter and stored here), smooth (the coarse colour laid as one smooth field through the four means,
//! each mean at its quarter's centre and a smoothstep between them, the picture repeating; each quarter's departure
//! from its own mean mixed linearly across the band: a quarter darker than its neighbour shades into it over the
//! whole distance between their centres, not at a line). The weight of a quarter falls from 1, a band away from its border, to
//! one half on the border along a smoothstep, and its neighbour's rises to match; at a corner the two directions
//! multiply. The height (alpha) is always mixed linearly.
//! Pure function of the place, no maths library: only + - * /, sqrt and floor.
const c = @import("common.zig");

pub const name = "Quad";
pub const version: u32 = 1;
pub const inputs: u8 = 4;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .cycle, .label = "seam", .offset = 1, .def = 3, .min = 0, .max = 3, .choices = "cut|mix|keep|smooth" },
    .{ .kind = .float, .label = "band", .offset = 2, .def = 0.03, .min = 0, .max = 0.25, .step = 0.005 },
    .{ .kind = .rgba, .label = "mean 1", .offset = 3, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 2", .offset = 4, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 3", .offset = 5, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 4", .offset = 6, .def = 0xff808080, .min = 0, .max = 0xffffffff },
};

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 0;
}

/// along one direction: t is the place in quarters (2x); the weight of the quarter t lies in (own), the other's is
/// 1 - own. b is the band in quarters.
pub fn own(t: f32, b: f32, seam: i32) f32 {
    if (seam == 0 or b <= 0) return 1.0;
    const f = t - @floor(t);
    if (f < b) return 0.5 + 0.5 * c.smoothstep(0, 1, f / b);
    if (1.0 - f < b) return 0.5 + 0.5 * c.smoothstep(0, 1, (1.0 - f) / b);
    return 1.0;
}

/// which column (or row) of quarters the place t (in quarters) lies in: 0 or 1, the picture repeating
pub fn side(t: f32) usize {
    const k: i32 = @intFromFloat(@floor(t));
    return @intCast(@mod(k, 2));
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    try c.version(name, w, version);
    const seam = try c.int(&params, w, 1);
    const band = try c.flt(&params, w, 2);
    const mean = [4][3]f32{ c.rgb(w[3]), c.rgb(w[4]), c.rgb(w[5]), c.rgb(w[6]) };
    const b = 2.0 * band;
    for (0..out.h) |j| {
        const ty = 2.0 * c.cv.v(j);
        const ry = side(ty);
        const oy = own(ty, b, seam);
        const wy = if (ry == 0) [2]f32{ oy, 1.0 - oy } else [2]f32{ 1.0 - oy, oy };
        for (0..out.w) |i| {
            const k = j * out.w + i;
            const tx = 2.0 * c.cv.u(i);
            const rx = side(tx);
            const ox = own(tx, b, seam);
            const wx = if (rx == 0) [2]f32{ ox, 1.0 - ox } else [2]f32{ 1.0 - ox, ox };
            var wq: [4]f32 = undefined;
            for (0..4) |q| wq[q] = wy[q / 2] * wx[q % 2];
            var o = [4]f32{ 0, 0, 0, 0 };
            if (seam == 3) {
                // the means' field: a smoothstep between the quarters' centres (at 0.5 + whole numbers of 2x)
                const sx = tx - 0.5;
                const sy = ty - 0.5;
                const ax = c.smoothstep(0, 1, sx - @floor(sx));
                const ay = c.smoothstep(0, 1, sy - @floor(sy));
                const cx0 = side(sx);
                const cy0 = side(sy);
                var mw: [4]f32 = undefined;
                for (0..4) |q| {
                    const fxw = if (q % 2 == cx0) 1.0 - ax else ax;
                    const fyw = if (q / 2 == cy0) 1.0 - ay else ay;
                    mw[q] = fxw * fyw;
                }
                var mu = [3]f32{ 0, 0, 0 };
                for (0..4) |q| {
                    inline for (0..3) |ch| mu[ch] += mw[q] * mean[q][ch];
                }
                for (0..4) |q| {
                    if (wq[q] == 0) continue;
                    const p = c.getc(ins[q], k);
                    inline for (0..3) |ch| o[ch] += wq[q] * (p[ch] - mean[q][ch]);
                    o[3] += wq[q] * p[3];
                }
                inline for (0..3) |ch| o[ch] += mu[ch];
            } else if (seam == 2) {
                var s2: f32 = 0;
                for (0..4) |q| s2 += wq[q] * wq[q];
                const inv = 1.0 / @sqrt(s2);
                var mu = [3]f32{ 0, 0, 0 };
                for (0..4) |q| {
                    if (wq[q] == 0) continue;
                    const p = c.getc(ins[q], k);
                    inline for (0..3) |ch| {
                        mu[ch] += wq[q] * mean[q][ch];
                        o[ch] += wq[q] * (p[ch] - mean[q][ch]);
                    }
                    o[3] += wq[q] * p[3];
                }
                inline for (0..3) |ch| o[ch] = mu[ch] + o[ch] * inv;
            } else {
                for (0..4) |q| {
                    if (wq[q] == 0) continue;
                    const p = c.getc(ins[q], k);
                    inline for (0..4) |ch| o[ch] += wq[q] * p[ch];
                }
            }
            c.putc(out, k, o);
        }
    }
}
