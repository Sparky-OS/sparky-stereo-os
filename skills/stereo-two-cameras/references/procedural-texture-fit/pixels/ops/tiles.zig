//! Tiles (version 1): structure by distance. Every piece of a laid surface is a distance field: how far a place
//! lies inside its piece. From it come the joint (outside every piece), the bevel (the first part inside, rising),
//! each piece's own shade (a value of its own, drawn from its cell), and the height for the relief. Layouts:
//! a grid of slabs, bricks in a running bond, a checker of slabs in two shades, hexagons, lozenges turned one way
//! and the other on alternate cells (a tread plate), studs (discs), octagonal tiles with square inserts at their
//! corners, and planks of uneven length in rows. Per piece: its shade varies, its edges move inward by a jitter, and
//! the whole layout may be warped by noise for hand-made edges. Inserts: square tiles whose corners give way to a
//! small square insert, upright, where four tiles meet.
//! Sources: Inigo Quilez, "2D distance functions" (iquilezles.org): the rounded box and the rhombus, written from
//! the formulas; the hexagons are the cells of a lattice, their edge where the nearest centre and the second
//! nearest are equally far (Worley 1996's F2 - F1 on a regular lattice). No code copied.
//! Output: red, green and blue: 0 in the joints, the piece's shade (between the floor value and 0.85) inside, rising
//! across the bevel; inserts (octagons and inserts layouts) at 1, above every piece, so a Layer can take them apart. Alpha: the height, 0 in the joint, 1 on
//! a piece's face.
const c = @import("common.zig");

pub const name = "Tiles";
pub const version: u32 = 1;
pub const inputs: u8 = 0;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .cycle, .label = "layout", .offset = 1, .def = 0, .min = 0, .max = 8, .choices = "grid|bond|checker|hexagons|lozenges|studs|octagons|planks|inserts" },
    .{ .kind = .int, .label = "pieces across", .offset = 2, .def = 4, .min = 1, .max = 1024 },
    .{ .kind = .int, .label = "pieces down", .offset = 3, .def = 8, .min = 1, .max = 1024 },
    .{ .kind = .float, .label = "bond", .offset = 4, .def = 0.5, .min = 0, .max = 1, .step = 0.01 },
    .{ .kind = .float, .label = "joint", .offset = 5, .def = 0.08, .min = 0, .max = 0.9, .step = 0.005 },
    .{ .kind = .float, .label = "bevel", .offset = 6, .def = 0.05, .min = 0.001, .max = 1, .step = 0.005 },
    .{ .kind = .float, .label = "round", .offset = 7, .def = 0.05, .min = 0, .max = 1, .step = 0.01 },
    .{ .kind = .float, .label = "jitter", .offset = 8, .def = 0.02, .min = 0, .max = 0.5, .step = 0.005 },
    .{ .kind = .float, .label = "variation", .offset = 9, .def = 0.4, .min = 0, .max = 1, .step = 0.02 },
    .{ .kind = .int, .label = "seed", .offset = 10, .def = 0, .min = 0, .max = 65535 },
    .{ .kind = .float, .label = "warp", .offset = 11, .def = 0, .min = 0, .max = 0.2, .step = 0.001 },
    .{ .kind = .int, .label = "warp cells", .offset = 12, .def = 16, .min = 1, .max = 1024 },
    .{ .kind = .float, .label = "floor", .offset = 13, .def = 0.3, .min = 0.02, .max = 0.98, .step = 0.02 },
    .{ .kind = .float, .label = "size", .offset = 14, .def = 0.5, .min = 0.01, .max = 2, .step = 0.01 },
    .{ .kind = .float, .label = "phase across", .offset = 15, .def = 0, .min = -4, .max = 4, .step = 0.01 },
    .{ .kind = .float, .label = "phase down", .offset = 16, .def = 0, .min = -4, .max = 4, .step = 0.01 },
};

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 0;
}

inline fn len2(x: f32, y: f32) f32 {
    return @sqrt(x * x + y * y);
}

/// Quilez's rounded box: the signed distance from p to a box of half sides bx, by with corners of radius r
fn roundBox(px: f32, py: f32, bx: f32, by: f32, r: f32) f32 {
    const qx = @abs(px) - bx + r;
    const qy = @abs(py) - by + r;
    return len2(@max(qx, 0), @max(qy, 0)) + @min(@max(qx, qy), 0) - r;
}

/// Quilez's rhombus: the signed distance from p to a rhombus of half diagonals bx, by
fn rhombus(px: f32, py: f32, bx: f32, by: f32) f32 {
    const qx = @abs(px);
    const qy = @abs(py);
    const ndot = bx * (bx - 2 * qx) - by * (by - 2 * qy);
    const h = @min(1.0, @max(-1.0, ndot / (bx * bx + by * by)));
    const d = len2(qx - 0.5 * bx * (1 - h), qy - 0.5 * by * (1 + h));
    const s = qx * by + qy * bx - bx * by;
    return if (s < 0) -d else d;
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    _ = ins;
    try c.version(name, w, version);
    const layout = try c.int(&params, w, 1);
    const nx = try c.int(&params, w, 2);
    const ny = try c.int(&params, w, 3);
    const bond = try c.flt(&params, w, 4);
    const joint = try c.flt(&params, w, 5);
    const bevel = try c.flt(&params, w, 6);
    const round = try c.flt(&params, w, 7);
    const jit = try c.flt(&params, w, 8);
    const vary = try c.flt(&params, w, 9);
    const seed: u32 = @intCast(try c.int(&params, w, 10));
    const warp = try c.flt(&params, w, 11);
    const wf = try c.int(&params, w, 12);
    const floor = try c.flt(&params, w, 13);
    const size = try c.flt(&params, w, 14);
    const phx = try c.flt(&params, w, 15);
    const phy = try c.flt(&params, w, 16);
    const fnx: f32 = @floatFromInt(nx);
    const fny: f32 = @floatFromInt(ny);
    const cw = 1.0 / fnx;
    const ch = 1.0 / fny;
    const m = @min(cw, ch); // lengths are parts of the smaller side of a piece
    const jw = joint * m;
    const bw = bevel * m;
    const rr = round * m;
    for (0..out.h) |j| {
        const v0 = c.cv.v(j);
        for (0..out.w) |i| {
            const p = c.warped(c.cv.u(i), v0, warp, wf, seed ^ 0x7a11);
            const X = p[0] * fnx - phx;
            const Y = p[1] * fny - phy;
            var sd: f32 = 1; // the distance inside the piece is -sd, in parts of the picture
            var cid: u32 = 0;
            var parity: f32 = 0;
            var insert = false;
            switch (layout) {
                0, 1, 2 => {
                    const row: i32 = @intFromFloat(@floor(Y));
                    const Xs = if (layout == 1) X - bond * @as(f32, @floatFromInt(row)) else X;
                    const col: i32 = @intFromFloat(@floor(Xs));
                    const fx = Xs - @floor(Xs);
                    const fy = Y - @floor(Y);
                    cid = c.hash3(c.wrap(col, nx), c.wrap(row, ny), seed);
                    parity = @floatFromInt(@mod(col + row, 2));
                    const jx = jit * m * (c.rnd01(c.hash(cid ^ 0x11)) - 0.5);
                    const jy = jit * m * (c.rnd01(c.hash(cid ^ 0x22)) - 0.5);
                    const sh = jit * m * c.rnd01(c.hash(cid ^ 0x33));
                    sd = roundBox((fx - 0.5) * cw - jx, (fy - 0.5) * ch - jy, 0.5 * (cw - jw) - sh, 0.5 * (ch - jw) - sh, rr);
                },
                3 => {
                    // hexagons: rows of centres, every second row moved half a piece; the edge lies where the
                    // nearest centre and the second nearest are equally far
                    const r0: i32 = @intFromFloat(@floor(Y));
                    var d1: f32 = 1e9;
                    var d2: f32 = 1e9;
                    var dr: i32 = -1;
                    while (dr <= 2) : (dr += 1) {
                        const r = r0 + dr;
                        const off: f32 = if (@mod(r, 2) == 1) 0.5 else 0.0;
                        const k0: i32 = @intFromFloat(@floor(X - off));
                        var dk: i32 = -1;
                        while (dk <= 2) : (dk += 1) {
                            const k = k0 + dk;
                            const ex = (@as(f32, @floatFromInt(k)) + off + 0.5 - X) * cw;
                            const ey = (@as(f32, @floatFromInt(r)) + 0.5 - Y) * ch;
                            const d = len2(ex, ey);
                            if (d < d1) {
                                d2 = d1;
                                d1 = d;
                                cid = c.hash3(c.wrap(k, nx), c.wrap(r, ny), seed);
                            } else if (d < d2) d2 = d;
                        }
                    }
                    sd = -(0.5 * (d2 - d1)) + 0.5 * jw + jit * m * c.rnd01(c.hash(cid ^ 0x33));
                },
                4 => {
                    // lozenges, turned a quarter of a right angle one way on one cell and the other way on the next
                    const col: i32 = @intFromFloat(@floor(X));
                    const row: i32 = @intFromFloat(@floor(Y));
                    cid = c.hash3(c.wrap(col, nx), c.wrap(row, ny), seed);
                    const lx = (X - @floor(X) - 0.5) * cw;
                    const ly = (Y - @floor(Y) - 0.5) * ch;
                    const s: f32 = if (@mod(col + row, 2) == 0) 1.0 else -1.0;
                    const ax = 0.70710678 * (lx + s * ly);
                    const ay = 0.70710678 * (ly - s * lx);
                    const half = 0.5 * size * len2(cw, ch);
                    sd = rhombus(ax, ay, half, half * round) + 0.5 * jw;
                },
                5 => {
                    const col: i32 = @intFromFloat(@floor(X));
                    const row: i32 = @intFromFloat(@floor(Y));
                    cid = c.hash3(c.wrap(col, nx), c.wrap(row, ny), seed);
                    const lx = (X - @floor(X) - 0.5) * cw;
                    const ly = (Y - @floor(Y) - 0.5) * ch;
                    sd = len2(lx, ly) - 0.5 * size * m * (1.0 - jit * c.rnd01(c.hash(cid ^ 0x33)));
                },
                6, 8 => {
                    // octagonal tiles with square inserts turned on their corner where four tiles meet (6), or square
                    // tiles with upright square inserts at their corners (8)
                    const col: i32 = @intFromFloat(@floor(X));
                    const row: i32 = @intFromFloat(@floor(Y));
                    const fx = X - @floor(X);
                    const fy = Y - @floor(Y);
                    const ccol = if (fx < 0.5) col else col + 1;
                    const crow = if (fy < 0.5) row else row + 1;
                    const qx = (if (fx < 0.5) fx else fx - 1.0) * cw;
                    const qy = (if (fy < 0.5) fy else fy - 1.0) * ch;
                    const dins = if (layout == 6)
                        0.70710678 * (@abs(qx) + @abs(qy) - 0.5 * size * m)
                    else
                        @max(@abs(qx), @abs(qy)) - 0.5 * size * m;
                    const tile = roundBox((fx - 0.5) * cw, (fy - 0.5) * ch, 0.5 * (cw - jw), 0.5 * (ch - jw), rr);
                    const tile_cut = @max(tile, -(dins - jw));
                    if (dins < tile_cut) {
                        sd = dins;
                        insert = true;
                        cid = c.hash3(c.wrap(ccol, nx), c.wrap(crow, ny), seed ^ 0x5151);
                    } else {
                        sd = tile_cut;
                        cid = c.hash3(c.wrap(col, nx), c.wrap(row, ny), seed);
                    }
                },
                else => {
                    // planks of uneven length: each row is cut at some of its whole-number places (size: the share
                    // of places cut), the row moved by a length of its own; a plank spans at most eight places
                    const row: i32 = @intFromFloat(@floor(Y));
                    const rh = c.hash3(0, c.wrap(row, ny), seed ^ 0x4242);
                    const Xs = X - 8.0 * c.rnd01(rh);
                    const k0: i32 = @intFromFloat(@floor(Xs));
                    var lo = k0;
                    var hi = k0 + 1;
                    var n: i32 = 0;
                    while (n < 8 and c.rnd01(c.hash3(c.wrap(lo, nx), c.wrap(row, ny), seed ^ 0x9191)) >= size) : (n += 1) lo -= 1;
                    n = 0;
                    while (n < 8 and c.rnd01(c.hash3(c.wrap(hi, nx), c.wrap(row, ny), seed ^ 0x9191)) >= size) : (n += 1) hi += 1;
                    const span: f32 = @floatFromInt(hi - lo);
                    const fx = (Xs - @as(f32, @floatFromInt(lo))) / span;
                    const fy = Y - @floor(Y);
                    cid = c.hash3(c.wrap(lo, nx), c.wrap(row, ny), seed);
                    const sh = jit * m * c.rnd01(c.hash(cid ^ 0x33));
                    sd = roundBox((fx - 0.5) * cw * span, (fy - 0.5) * ch, 0.5 * (cw * span - jw) - sh, 0.5 * (ch - jw) - sh, rr);
                },
            }
            const r = c.rnd01(c.hash(cid ^ 0x1b873593));
            const cellv = if (layout == 2)
                0.25 + 0.5 * parity + 0.25 * vary * (r - 0.5)
            else
                0.5 + vary * (r - 0.5);
            const h = c.smoothstep(0, bw, -sd);
            const face = if (insert) 1.0 else floor + (0.85 - floor) * c.clamp01(cellv);
            const g = h * face;
            const hh = if (insert) 0.6 * h else h;
            c.putc(out, j * out.w + i, .{ g, g, g, hh });
        }
    }
}
