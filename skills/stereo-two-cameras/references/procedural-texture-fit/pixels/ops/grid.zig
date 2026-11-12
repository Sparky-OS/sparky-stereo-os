//! Grid (version 1, milestone 2e): more procedures per picture than four. Daniel, 11 November 2026, on the pictures
//! four procedures did not help: "I double the bet - make it doulbe 4 tiles - 8 tiles on the failed ones - if it
//! happens to work well, we can work backwards to see where it breaks, if not, we increase once more".
//! Quad's rule for cols by rows tiles: its inputs are cols * rows whole procedures, row by row from the top left,
//! each fitted to one tile of the picture as a picture of its own. A tile of a picture cut cols by rows is a
//! rectangle when cols and rows differ (eight tiles on a square picture: four across and two down, or two across and
//! four down); its procedure is drawn at one scale in both directions, s = the smaller of cols and rows tiles to the
//! picture, so the tile (col, row) shows the places s * (x - col / cols), s * (y - row / rows) of its procedure: the
//! rectangle 0 to s / cols across and 0 to s / rows down of a square canvas (p2p.zig's drawGrid and the page's
//! drawGridGpu do that; the fitter fitted that square canvas to the tile with its mirror image beside or below it, so
//! the tile's own pixels are all the procedure saw). With cols = rows = 2 the places are Quad's.
//! Where tiles meet, Quad's seams (cut, mix, keep, smooth) with the band in parts of the picture; at a crossing the
//! two directions multiply. The smooth seam's field of means passes through every tile's centre. The height (alpha)
//! is always mixed linearly.
//! Pure function of the place, no maths library: only + - * /, sqrt and floor.
const c = @import("common.zig");

pub const name = "Grid";
pub const version: u32 = 1;
/// the least inputs: a grid of one tile (the inputs are cols * rows, checked when it draws)
pub const inputs: u8 = 1;
pub const MAXT = 16;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .int, .label = "columns", .offset = 1, .def = 4, .min = 1, .max = 4 },
    .{ .kind = .int, .label = "rows", .offset = 2, .def = 2, .min = 1, .max = 4 },
    .{ .kind = .cycle, .label = "seam", .offset = 3, .def = 3, .min = 0, .max = 3, .choices = "cut|mix|keep|smooth" },
    .{ .kind = .float, .label = "band", .offset = 4, .def = 0.03, .min = 0, .max = 0.25, .step = 0.005 },
    .{ .kind = .rgba, .label = "mean 1", .offset = 5, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 2", .offset = 6, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 3", .offset = 7, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 4", .offset = 8, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 5", .offset = 9, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 6", .offset = 10, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 7", .offset = 11, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 8", .offset = 12, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 9", .offset = 13, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 10", .offset = 14, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 11", .offset = 15, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 12", .offset = 16, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 13", .offset = 17, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 14", .offset = 18, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 15", .offset = 19, .def = 0xff808080, .min = 0, .max = 0xffffffff },
    .{ .kind = .rgba, .label = "mean 16", .offset = 20, .def = 0xff808080, .min = 0, .max = 0xffffffff },
};

/// the words stored: the five and one mean per tile
pub fn wordCount(ver: u32) usize {
    _ = ver;
    return params.len;
}

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 0;
}

/// the scale a tile's procedure is drawn at, in its own canvases to the picture: the smaller of cols and rows
pub fn scaleOf(cols: usize, rows: usize) f32 {
    return @floatFromInt(@min(cols, rows));
}

/// along one direction of n tiles: t is the place in tiles (n x); the weights of the tile t lies in and of the
/// neighbour across the nearer border (Quad's own(), the neighbour named), the picture repeating
pub fn weights(t: f32, b: f32, seam: i32, n: usize, wv: *[4]f32) void {
    for (wv) |*x| x.* = 0;
    const k: i32 = @intFromFloat(@floor(t));
    const ni: i32 = @intCast(n);
    const own_i: usize = @intCast(@mod(k, ni));
    const f = t - @floor(t);
    var own: f32 = 1.0;
    var nb: usize = own_i;
    if (seam != 0 and b > 0) {
        if (f < b) {
            own = 0.5 + 0.5 * c.smoothstep(0, 1, f / b);
            nb = @intCast(@mod(k - 1, ni));
        } else if (1.0 - f < b) {
            own = 0.5 + 0.5 * c.smoothstep(0, 1, (1.0 - f) / b);
            nb = @intCast(@mod(k + 1, ni));
        }
    }
    wv[own_i] += own;
    wv[nb] += 1.0 - own;
}

/// the smooth seam's field along one direction: a smoothstep between the centres of neighbouring tiles
pub fn centres(t: f32, n: usize, wv: *[4]f32) void {
    for (wv) |*x| x.* = 0;
    const s = t - 0.5;
    const a = c.smoothstep(0, 1, s - @floor(s));
    const k: i32 = @intFromFloat(@floor(s));
    const ni: i32 = @intCast(n);
    const c0: usize = @intCast(@mod(k, ni));
    const c1: usize = @intCast(@mod(k + 1, ni));
    wv[c0] += 1.0 - a;
    wv[c1] += a;
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    try c.version(name, w, version);
    const cols: usize = @intCast(try c.int(&params, w, 1));
    const rows: usize = @intCast(try c.int(&params, w, 2));
    const seam = try c.int(&params, w, 3);
    const band = try c.flt(&params, w, 4);
    const nt = cols * rows;
    if (ins.len != nt) return c.refuse("Grid: {d} by {d} tiles take {d} procedures, the graph gives {d}", .{ cols, rows, nt, ins.len });
    var mean: [MAXT][3]f32 = undefined;
    for (0..nt) |q| mean[q] = c.rgb(w[5 + q]);
    const fc: f32 = @floatFromInt(cols);
    const fr: f32 = @floatFromInt(rows);
    const bx = fc * band;
    const by = fr * band;
    var wy: [4]f32 = undefined;
    var wx: [4]f32 = undefined;
    var my: [4]f32 = undefined;
    var mx: [4]f32 = undefined;
    for (0..out.h) |j| {
        const ty = fr * c.cv.v(j);
        weights(ty, by, seam, rows, &wy);
        centres(ty, rows, &my);
        for (0..out.w) |i| {
            const k = j * out.w + i;
            const tx = fc * c.cv.u(i);
            weights(tx, bx, seam, cols, &wx);
            var o = [4]f32{ 0, 0, 0, 0 };
            if (seam == 3) {
                centres(tx, cols, &mx);
                var mu = [3]f32{ 0, 0, 0 };
                for (0..nt) |q| {
                    const mw = my[q / cols] * mx[q % cols];
                    if (mw == 0) continue;
                    inline for (0..3) |ch| mu[ch] += mw * mean[q][ch];
                }
                for (0..nt) |q| {
                    const wq = wy[q / cols] * wx[q % cols];
                    if (wq == 0) continue;
                    const p = c.getc(ins[q], k);
                    inline for (0..3) |ch| o[ch] += wq * (p[ch] - mean[q][ch]);
                    o[3] += wq * p[3];
                }
                inline for (0..3) |ch| o[ch] += mu[ch];
            } else if (seam == 2) {
                var s2: f32 = 0;
                for (0..nt) |q| {
                    const wq = wy[q / cols] * wx[q % cols];
                    s2 += wq * wq;
                }
                const inv = 1.0 / @sqrt(s2);
                var mu = [3]f32{ 0, 0, 0 };
                for (0..nt) |q| {
                    const wq = wy[q / cols] * wx[q % cols];
                    if (wq == 0) continue;
                    const p = c.getc(ins[q], k);
                    inline for (0..3) |ch| {
                        mu[ch] += wq * mean[q][ch];
                        o[ch] += wq * (p[ch] - mean[q][ch]);
                    }
                    o[3] += wq * p[3];
                }
                inline for (0..3) |ch| o[ch] = mu[ch] + o[ch] * inv;
            } else {
                for (0..nt) |q| {
                    const wq = wy[q / cols] * wx[q % cols];
                    if (wq == 0) continue;
                    const p = c.getc(ins[q], k);
                    inline for (0..4) |ch| o[ch] += wq * p[ch];
                }
            }
            c.putc(out, k, o);
        }
    }
}
