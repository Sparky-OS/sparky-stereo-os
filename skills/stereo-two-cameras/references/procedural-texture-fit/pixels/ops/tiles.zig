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
//! Version 2 (milestone 2c, close up): edges chipped by a noise that eats into the pieces (chip, chip cells), and
//! each piece's face its own fine grain and its own coarse stain (grain, grain cells, grain octaves, stain, stain
//! cells): the noise is read at the piece's own place in the noise (an offset drawn from the piece), so neighbouring
//! bricks or slabs never share a pattern across a joint, as cut stone and fired brick never do. The grain also
//! roughens the face's height a little. Version 1 graphs draw byte for byte as before.
//! Version 3 (milestone 2d, Daniel's verdicts on the sheets of 2c): the joint as a hollow (hollow: the height inside
//! the joint rises as the square of the distance from its centre line, a "u" in a depression, so a light drawn on it
//! shades the side under the upper piece, as mortar sits in a hollow between bricks; the colour stays the joint's),
//! two more layouts: pairs (two lozenges in every cell, the second turned the other way and moved by its own offset
//! across and down, so the two seeds of a tread plate stand apart instead of in a line) and framed tiles (each square
//! tile of a small central square and four trapezoids around it, the long side at the tile's border, the short side
//! at the square; square inserts over the corners where four tiles meet, as the inserts layout draws them).
//! Version 4 (milestone 2e, Daniel on the floor tiles: "2d looker better, with a tin adjustment"; the second judge saw
//! the one-pixel joint "stair-stepped and of uneven width"): the edge between a joint and a piece filtered over the
//! pixel it falls in (the rise starts half a pixel outside the piece and takes at least one pixel), so a joint of one
//! or two pixels is drawn as an even line at any angle; the words are version 3's.
//! Output: red, green and blue: 0 in the joints, the piece's shade (between the floor value and 0.85) inside, rising
//! across the bevel; inserts (octagons and inserts layouts) at 1, above every piece, so a Layer can take them apart. Alpha: the height, 0 in the joint, 1 on
//! a piece's face.
const c = @import("common.zig");

pub const name = "Tiles";
pub const version: u32 = 1;
pub const inputs: u8 = 0;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 4, .min = 1, .max = 4 },
    .{ .kind = .cycle, .label = "layout", .offset = 1, .def = 0, .min = 0, .max = 10, .choices = "grid|bond|checker|hexagons|lozenges|studs|octagons|planks|inserts|pairs|framed" },
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
    // version 2
    .{ .kind = .float, .label = "chip", .offset = 17, .def = 0, .min = 0, .max = 0.6, .step = 0.01 },
    .{ .kind = .int, .label = "chip cells", .offset = 18, .def = 64, .min = 1, .max = 4096 },
    .{ .kind = .float, .label = "grain", .offset = 19, .def = 0, .min = 0, .max = 1, .step = 0.01 },
    .{ .kind = .int, .label = "grain cells", .offset = 20, .def = 256, .min = 1, .max = 4096 },
    .{ .kind = .int, .label = "grain octaves", .offset = 21, .def = 3, .min = 1, .max = 8 },
    .{ .kind = .float, .label = "stain", .offset = 22, .def = 0, .min = 0, .max = 1, .step = 0.01 },
    .{ .kind = .int, .label = "stain cells", .offset = 23, .def = 16, .min = 1, .max = 4096 },
    // version 3
    .{ .kind = .float, .label = "hollow", .offset = 24, .def = 0, .min = 0, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "second across", .offset = 25, .def = 0.5, .min = -1, .max = 1, .step = 0.01 },
    .{ .kind = .float, .label = "second down", .offset = 26, .def = 0.5, .min = -1, .max = 1, .step = 0.01 },
    .{ .kind = .float, .label = "inner", .offset = 27, .def = 0.33, .min = 0.02, .max = 0.9, .step = 0.01 },
};

/// the words a version stores: 17 in version 1, 24 in version 2, 28 in versions 3 and 4
pub fn wordCount(ver: u32) usize {
    return if (ver >= 3) 28 else if (ver >= 2) 24 else 17;
}

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
    const ver = try c.versionUpTo(name, w, 4);
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
    var chip: f32 = 0;
    var ccells: i32 = 1;
    var grain: f32 = 0;
    var gcells: i32 = 1;
    var goct: u32 = 1;
    var stain: f32 = 0;
    var scells: i32 = 1;
    if (ver >= 2) {
        chip = try c.flt(&params, w, 17);
        ccells = try c.int(&params, w, 18);
        grain = try c.flt(&params, w, 19);
        gcells = try c.int(&params, w, 20);
        goct = @intCast(try c.int(&params, w, 21));
        stain = try c.flt(&params, w, 22);
        scells = try c.int(&params, w, 23);
    }
    var hollow: f32 = 0;
    var sox: f32 = 0.5;
    var soy: f32 = 0.5;
    var inner: f32 = 0.33;
    if (ver >= 3) {
        hollow = try c.flt(&params, w, 24);
        sox = try c.flt(&params, w, 25);
        soy = try c.flt(&params, w, 26);
        inner = try c.flt(&params, w, 27);
    }
    if (ver < 3 and layout > 8) return c.refuse("Tiles: layout {d} needs version 3", .{layout});
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
                9 => {
                    // pairs: two lozenges in every cell, the first at the cell's centre turned one way, the second
                    // turned the other way and moved by its offset (in parts of the cell); each is looked for in
                    // the cell and its neighbours, since a lozenge reaches over its cell's border
                    const col: i32 = @intFromFloat(@floor(X));
                    const row: i32 = @intFromFloat(@floor(Y));
                    const half = 0.5 * size * len2(cw, ch);
                    var best: f32 = 1e9;
                    var dr: i32 = -1;
                    while (dr <= 1) : (dr += 1) {
                        var dk: i32 = -1;
                        while (dk <= 1) : (dk += 1) {
                            for (0..2) |sdi| {
                                const s: f32 = if (sdi == 0) 1.0 else -1.0;
                                const ox: f32 = if (sdi == 0) 0.5 else 0.5 + sox;
                                const oy: f32 = if (sdi == 0) 0.5 else 0.5 + soy;
                                const lx = (X - (@as(f32, @floatFromInt(col + dk)) + ox)) * cw;
                                const ly = (Y - (@as(f32, @floatFromInt(row + dr)) + oy)) * ch;
                                const ax = 0.70710678 * (lx + s * ly);
                                const ay = 0.70710678 * (ly - s * lx);
                                const d = rhombus(ax, ay, half, half * round) + 0.5 * jw;
                                if (d < best) {
                                    best = d;
                                    cid = c.hash3(c.wrap(col + dk, nx), c.wrap(row + dr, ny), seed ^ @as(u32, @intCast(sdi * 0x2b7e)));
                                }
                            }
                        }
                    }
                    sd = best;
                },
                10 => {
                    // framed tiles: the inserts layout's square tile, cut into a small central square (inner, in
                    // parts of the piece) and four trapezoids by joints along the square's edges and along the
                    // diagonals from its corners to the tile's corners; the inserts over the corners as layout 8
                    const col: i32 = @intFromFloat(@floor(X));
                    const row: i32 = @intFromFloat(@floor(Y));
                    const fx = X - @floor(X);
                    const fy = Y - @floor(Y);
                    const ccol = if (fx < 0.5) col else col + 1;
                    const crow = if (fy < 0.5) row else row + 1;
                    const qx = (if (fx < 0.5) fx else fx - 1.0) * cw;
                    const qy = (if (fy < 0.5) fy else fy - 1.0) * ch;
                    const dins = @max(@abs(qx), @abs(qy)) - 0.5 * size * m;
                    const tile = roundBox((fx - 0.5) * cw, (fy - 0.5) * ch, 0.5 * (cw - jw), 0.5 * (ch - jw), rr);
                    const lx = @abs((fx - 0.5) * cw);
                    const ly = @abs((fy - 0.5) * ch);
                    const a = 0.5 * inner * m;
                    const mx = @max(lx, ly);
                    var part: u32 = 0;
                    var dint: f32 = 0;
                    if (mx <= a) {
                        dint = a - mx;
                    } else {
                        dint = @min(mx - a, 0.70710678 * @abs(lx - ly));
                        part = if (ly >= lx) (if (fy < 0.5) @as(u32, 1) else 2) else (if (fx < 0.5) @as(u32, 3) else 4);
                    }
                    const piece = @max(tile, -(dint - 0.5 * jw));
                    const tile_cut = @max(piece, -(dins - jw));
                    if (dins < tile_cut) {
                        sd = dins;
                        insert = true;
                        cid = c.hash3(c.wrap(ccol, nx), c.wrap(crow, ny), seed ^ 0x5151);
                    } else {
                        sd = tile_cut;
                        cid = c.hash3(c.wrap(col, nx), c.wrap(row, ny), seed ^ (part *% 0x9e37));
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
            if (chip > 0 and !insert) {
                // chipped edges: a noise that is positive on about half the edge eats into the piece there
                const cn = c.fbm(p[0], p[1], ccells, ccells, 3, 0.5, seed ^ 0xc41b, .fbm);
                sd += chip * m * c.clamp01(2.0 * cn);
            }
            const r = c.rnd01(c.hash(cid ^ 0x1b873593));
            const cellv = if (layout == 2)
                0.25 + 0.5 * parity + 0.25 * vary * (r - 0.5)
            else
                0.5 + vary * (r - 0.5);
            const h = if (ver >= 4) c.smoothstep(-0.5 * c.cv.px(), @max(bw, 0.5 * c.cv.px()), -sd) else c.smoothstep(0, bw, -sd);
            var face = if (insert) 1.0 else floor + (0.85 - floor) * c.clamp01(cellv);
            var rough: f32 = 0;
            if (!insert and (grain > 0 or stain > 0)) {
                // the piece's own place in the noise: every piece shows another part of it
                const ox = c.rnd01(c.hash(cid ^ 0x6a09e667));
                const oy = c.rnd01(c.hash(cid ^ 0xbb67ae85));
                if (grain > 0) {
                    rough = c.fbm(p[0] + ox, p[1] + oy, gcells, gcells, goct, 0.6, seed ^ 0x9a11, .fbm);
                    face += grain * (0.85 - floor) * rough;
                }
                if (stain > 0) face += stain * (0.85 - floor) * c.fbm(p[0] + oy, p[1] + ox, scells, scells, 3, 0.5, seed ^ 0x5a17, .fbm);
                // the face stays above the floor, so no grain reads as the bevel's darker values
                face = @min(0.9, @max(floor, face));
            }
            const g = h * face;
            var hh = if (insert) 0.6 * h else if (grain > 0) c.clamp01(h * (1.0 + 0.3 * grain * rough)) else h;
            if (hollow > 0 and !insert) {
                // the joint as a hollow: from its centre line (0) the height rises as the square of the distance to
                // half the hollow at the pieces' edges, where the bevel takes it on to the face
                const hj = 0.5 * hollow;
                if (sd >= 0) {
                    const t = c.clamp01(1.0 - sd / @max(1e-6, 0.5 * jw));
                    hh = hj * t * t;
                } else hh = hj + (1.0 - hj) * hh;
            }
            c.putc(out, j * out.w + i, .{ g, g, g, hh });
        }
    }
}
