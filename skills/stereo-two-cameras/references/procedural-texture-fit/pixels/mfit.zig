//! The modern fit (milestone 2b): from a picture's pixels, a procedure of the modern operators (ops/*.zig), the whole
//! picture first, then a tile's own correction only where the picture differs from the whole's drawing.
//!
//! Every operator enters through its own reading of the pixels (readings.zig) and is printed with it:
//!   Noise    the octaves and their fall (milestone 1's reading), then its kind (fbm, ridged, billowed, and which way
//!            round), its stretch and its warp chosen so the drawing's reading equals the picture's: the skew of the
//!            detail (thin dark or light lines), the change across against down (grain), the bending of the lines;
//!   Tiles    the repeat (milestone 1's reading), then the layout, the pieces per cell, the place of the joints, their
//!            width and bevel chosen by laying the drawing's mean cell over the picture's (the shift that fits best);
//!            the faces' texture by the share of the faces' variation that lies between pieces;
//!   Ramp     the colours at the same ranks as the drawn field's (a histogram match), the joints' own colour apart;
//!   Layer    a second material where milestone 1's reading finds colours off the main axis, its patches by their
//!            size, raggedness and coverage; cracks by long thin dark pieces; Scatter by compact pits, specks and
//!            stones; Wear's drips where the second material runs down; Shade where the relief's sides are lit
//!            one way (structure) or the blobs' sides are (pits, stones);
//!   Tint     per tile, measured brightness and saturation, only where the tile differs.
//! Nothing is searched by the inner measure; no model and no text is an input. The choices are the readings'; the
//! verdict is the eye's, on the sheets.
const std = @import("std");
const P = @import("p2p.zig");
const R = @import("readings.zig");
const M = @import("modern.zig");
const CL = @import("close.zig");
const alloc = std.heap.c_allocator;

extern "c" fn wzb_data(p: ?*anyopaque) [*]u16;

pub const K_NOISE = 0;
pub const K_CELLS = 1;
pub const K_TILES = 2;
pub const K_RAMP = 3;
pub const K_LAYER = 4;
pub const K_SHADE = 5;
pub const K_SCATTER = 6;
pub const K_WEAR = 7;
pub const K_TINT = 8;

var logbuf: std.ArrayList(u8) = .empty;
pub fn note(comptime fmt: []const u8, args: anytype) void {
    var b: [1024]u8 = undefined;
    const s = std.fmt.bufPrint(&b, fmt, args) catch return;
    P.say("{s}", .{s});
    logbuf.appendSlice(alloc, s) catch {};
}

/// milestone 2d: every seed word the fit writes is moved by this much (mfit seed=N), so the four quarters of a picture
/// fitted apart draw four different instances of their noises, not one instance four times
pub var seed_base: i32 = 0;

pub fn mk(k: usize, v: []const f64, ins: []const usize) P.Node {
    var nd = P.Node{ .op = @intCast(P.OP_MODERN + k) };
    const kinds_all = P.ops[P.OP_MODERN + k].kinds;
    const nwv = M.wordsFor(k, @intFromFloat(v[0]));
    if (v.len != nwv) P.die("{s} version {d}: {d} values given, {d} needed", .{ P.ops[P.OP_MODERN + k].name, v[0], v.len, nwv });
    const kinds = kinds_all[0..nwv];
    const prm = M.paramsOf(k);
    for (kinds, 0..) |kd, i| {
        const sv: f64 = if (seed_base != 0 and std.mem.eql(u8, prm[i].label, "seed")) @mod(v[i] + @as(f64, @floatFromInt(seed_base)), 65536) else v[i];
        nd.w[i] = switch (kd) {
            'i' => @bitCast(@as(i32, @intFromFloat(sv))),
            'f' => @bitCast(@as(f32, @floatCast(sv))),
            else => @intFromFloat(sv),
        };
    }
    nd.nw = @intCast(kinds.len);
    nd.nin = @intCast(ins.len);
    for (ins, 0..) |x, i| nd.in[i] = @intCast(x);
    return nd;
}

pub fn add(g: *P.Graph, nd: P.Node) usize {
    if (g.n >= P.MAXN) P.die("graph too large", .{});
    g.nodes[g.n] = nd;
    g.n += 1;
    g.root = g.n - 1;
    return g.n - 1;
}

pub const Drawn = struct {
    rgb: []f32,
    grey: []f32,
    h: []f32,
    pub fn free(d: *Drawn) void {
        alloc.free(d.rgb);
        alloc.free(d.grey);
        alloc.free(d.h);
    }
};

/// draw node `root` of g over the whole picture at n by n pixels: its colours, grey and height
pub fn drawNode(g: *P.Graph, root: usize, n: usize) Drawn {
    return drawWin(g, root, n, .{});
}
pub fn drawWin(g: *P.Graph, root: usize, n: usize, win: P.Win) Drawn {
    const keep = g.root;
    g.root = root;
    defer g.root = keep;
    const bm = P.drawCanvas(g, n, win, 99) orelse P.die("a step of the procedure does not draw", .{});
    const cv = M.c.cv;
    const d = wzb_data(bm);
    var o = Drawn{
        .rgb = alloc.alloc(f32, n * n * 3) catch unreachable,
        .grey = alloc.alloc(f32, n * n) catch unreachable,
        .h = alloc.alloc(f32, n * n) catch unreachable,
    };
    for (0..n) |j| {
        for (0..n) |i| {
            const q = d + 4 * ((j + cv.m) * cv.w + i + cv.m);
            const r = @as(f32, @floatFromInt(q[2])) / 32767.0;
            const gg = @as(f32, @floatFromInt(q[1])) / 32767.0;
            const b = @as(f32, @floatFromInt(q[0])) / 32767.0;
            const k = j * n + i;
            o.rgb[3 * k] = r;
            o.rgb[3 * k + 1] = gg;
            o.rgb[3 * k + 2] = b;
            o.grey[k] = (r + gg + b) / 3.0;
            o.h[k] = @as(f32, @floatFromInt(q[3])) / 32767.0;
        }
    }
    return o;
}

pub fn colourWord(c: [3]f32) f64 {
    var w: u32 = 0xff000000;
    inline for (0..3) |k| {
        const v: u32 = @intFromFloat(@min(255.0, @max(0.0, c[k] * 255.0 + 0.5)));
        w |= v << (16 - 8 * k);
    }
    return @floatFromInt(w);
}

/// the picture: its colours, its values along the main colour axis (rank key) and its luminance
pub const Pic = struct { n: usize, rgb: []const f32, t: []const f32, tsort: []f32 };

/// A Ramp's words: the field's values at eight ranks (or seven after the joint's own stop) and the picture's mean
/// colour at the same ranks of its main colour axis, among the selected pixels of each (a histogram match).
pub fn rampWords(F: []const f32, fsel: ?[]const bool, pic: *const Pic, psel: ?[]const bool, reversed: bool, joint: ?[3]f32) [18]f64 {
    return rampWords2(F, fsel, pic, psel, reversed, joint, null, 0);
}

/// the same with a second stop of its own at place ipos (an insert's colour, measured where the drawing has inserts)
pub fn rampWords2(F: []const f32, fsel: ?[]const bool, pic: *const Pic, psel: ?[]const bool, reversed: bool, joint: ?[3]f32, insert: ?[3]f32, ipos: f32) [18]f64 {
    var fv: std.ArrayList(f32) = .empty;
    defer fv.deinit(alloc);
    for (F, 0..) |v, i| {
        if (fsel == null or fsel.?[i]) fv.append(alloc, v) catch unreachable;
    }
    var pi: std.ArrayList(u32) = .empty;
    defer pi.deinit(alloc);
    for (0..pic.n * pic.n) |i| {
        if (psel == null or psel.?[i]) pi.append(alloc, @intCast(i)) catch unreachable;
    }
    if (fv.items.len < 16 or pi.items.len < 16) P.die("a Ramp has too few pixels to read its colours from ({d} drawn, {d} in the picture)", .{ fv.items.len, pi.items.len });
    std.mem.sort(f32, fv.items, {}, std.sort.asc(f32));
    const Ctx = struct {
        t: []const f32,
        fn lt(c: @This(), a: u32, b: u32) bool {
            return c.t[a] < c.t[b];
        }
    };
    std.mem.sort(u32, pi.items, Ctx{ .t = pic.t }, Ctx.lt);
    var w = [_]f64{0} ** 18;
    w[0] = 1;
    const S: usize = (if (joint != null) @as(usize, 7) else 8) - (if (insert != null) @as(usize, 1) else 0);
    w[1] = 8;
    var k0: usize = 0;
    if (joint) |jc| {
        w[2] = 0;
        w[3] = colourWord(jc);
        k0 = 1;
    }
    if (insert) |ic| {
        w[2 + 2 * k0] = ipos;
        w[3 + 2 * k0] = colourWord(ic);
        k0 += 1;
    }
    var last: f32 = 0;
    for (0..S) |s| {
        const q: f32 = 0.03 + 0.94 * @as(f32, @floatFromInt(s)) / @as(f32, @floatFromInt(S - 1));
        var pos = fv.items[@intFromFloat(q * @as(f32, @floatFromInt(fv.items.len - 1)))];
        if (pos < last) pos = last;
        last = pos;
        const qc = if (reversed) 1.0 - q else q;
        const lo: usize = @intFromFloat(@max(0.0, qc - 0.035) * @as(f32, @floatFromInt(pi.items.len - 1)));
        const hi: usize = @intFromFloat(@min(1.0, qc + 0.035) * @as(f32, @floatFromInt(pi.items.len - 1)));
        var c = [3]f32{ 0, 0, 0 };
        for (pi.items[lo .. hi + 1]) |ix| {
            inline for (0..3) |ch| c[ch] += pic.rgb[3 * ix + ch];
        }
        const cnt: f32 = @floatFromInt(hi - lo + 1);
        inline for (0..3) |ch| c[ch] /= cnt;
        w[2 + 2 * (k0 + s)] = pos;
        w[3 + 2 * (k0 + s)] = colourWord(c);
    }
    return w;
}

pub fn rgbOfWord(w: u32) [3]f32 {
    return .{ @as(f32, @floatFromInt((w >> 16) & 0xff)) / 255.0, @as(f32, @floatFromInt((w >> 8) & 0xff)) / 255.0, @as(f32, @floatFromInt(w & 0xff)) / 255.0 };
}

pub fn absDiff(a: f32, b: f32) f32 {
    return @abs(a - b);
}

/// a field drawn, its values put in the picture's order (rank-matched): what the eye sees of it before the colours
fn ranked(F: []const f32, pic: *const Pic, reversed: bool) []f32 {
    const g = R.rankMap(F, pic.tsort);
    if (reversed) {
        // the field's highest values take the picture's lowest
        const inv = alloc.alloc(f32, F.len) catch unreachable;
        defer alloc.free(inv);
        for (F, 0..) |v, i| inv[i] = 1.0 - v;
        alloc.free(g);
        return R.rankMap(inv, pic.tsort);
    }
    return g;
}

pub const Built = struct { field: usize, reversed: bool, fx: i32, fy: i32, oct: i32, gain: f32, kind: u32, warp: f32, wf: i32 };

pub fn noiseNode(kind: u32, fx: i32, fy: i32, oct: i32, gain: f32, warp: f32, wf: i32, seed: i32) P.Node {
    return mk(K_NOISE, &.{ 1, @floatFromInt(kind), @floatFromInt(fx), @floatFromInt(fy), @floatFromInt(oct), gain, warp, @floatFromInt(wf), @floatFromInt(seed), 1 }, &.{});
}

/// the surface's noise: its kind, frequency, stretch, fall and warp, each chosen so the drawing's reading equals the
/// picture's (the drawing first put in the picture's order of values, as its Ramp will)
fn readNoise(g: *P.Graph, pic: *const Pic, rd: *const P.Reading) Built {
    const n = pic.n;
    _ = rd;
    var fx: i32 = 4;
    var fy: i32 = 4;
    var gain: f32 = 0.55;
    var oct: i32 = 8;
    var kind: u32 = 0;
    var rev = false;
    // the kind: the skew of the detail (dark or light features on a ground) and how clearly lines run (lines, not spots)
    const sk_pic = R.hpSkew(pic.t, n, 3);
    const co_pic = R.coherence(pic.t, n, 2);
    const kinds = [_]struct { k: u32, rev: bool, name: []const u8 }{
        .{ .k = 0, .rev = false, .name = "fbm" },         .{ .k = 1, .rev = false, .name = "ridged, ridges light" },
        .{ .k = 1, .rev = true, .name = "ridged, ridges dark" }, .{ .k = 2, .rev = false, .name = "billowed" },
        .{ .k = 2, .rev = true, .name = "billowed, turned round" },
    };
    var best_k: usize = 0;
    var best_d: f32 = 1e9;
    var fbm_d: f32 = 1e9;
    // a ridged or billowed kind (lines) is tried only where the picture's own lines run clearly
    const lines_ok = co_pic >= 0.65;
    note("noise: the picture's lines run {d:.3} clearly (ridged and billowed kinds are tried from 0.65)\n", .{co_pic});
    for (kinds, 0..) |kd, i| {
        if (i > 0 and !lines_ok) break;
        const sk = readNoiseCand(g, pic, kd.k, kd.rev, 8, 8, 8, 0.55, 0, 2, .skew);
        const co = readNoiseCand(g, pic, kd.k, kd.rev, 8, 8, 8, 0.55, 0, 2, .coherence);
        const d = absDiff(sk, sk_pic) + 4.0 * absDiff(co, co_pic);
        note("  kind {s}: detail skew {d:.2} (the picture's {d:.2}), lines {d:.3} (the picture's {d:.3})\n", .{ kd.name, sk, sk_pic, co, co_pic });
        if (i == 0) fbm_d = d;
        if (d < best_d) {
            best_d = d;
            best_k = i;
        }
    }
    if (best_k != 0 and fbm_d - best_d < 0.15) best_k = 0;
    kind = kinds[best_k].k;
    rev = kinds[best_k].rev;
    note("noise kind: {s}\n", .{kinds[best_k].name});
    // the frequency of the first octave and the fall: the drawing's strength per octave made to agree with the
    // picture's (the whole row of octaves, as a Laplacian pyramid measures it)
    const op = R.octaves(pic.t, n);
    var bd: f32 = 1e9;
    for ([_]i32{ 1, 2, 4, 8, 16 }) |f| {
        for ([_]f32{ 0.4, 0.5, 0.6, 0.7, 0.8, 0.9 }) |gv| {
            const od = readNoiseOct(g, pic, kind, rev, f, f, octFor(n, f), gv);
            const d = R.octDist(od, op);
            note("  {d} cells, gain {d:.1}: octaves differ {d:.3}\n", .{ f, gv, d });
            if (d < bd) {
                bd = d;
                fx = f;
                fy = f;
                gain = gv;
            }
        }
    }
    note("frequency: {d} cells across the picture for the first octave, each octave {d:.1} of the last\n", .{ fx, gain });
    // grain: the change across against down
    const an_pic = R.aniso(pic.t, n, 2);
    if (an_pic >= 1.2 or an_pic <= 1.0 / 1.2) {
        const f0 = fx;
        bd = 1e9;
        var br: i32 = 1;
        for ([_]i32{ 1, 2, 3, 4, 6, 8, 12 }) |r| {
            const a = if (an_pic > 1) f0 * r else f0;
            const b = if (an_pic > 1) f0 else f0 * r;
            const an = readNoiseCand(g, pic, kind, rev, a, b, octFor(n, @max(a, b)), gain, 0, 2, .aniso);
            note("  stretch {d}: across against down {d:.2} (the picture's {d:.2})\n", .{ r, an, an_pic });
            const d = @abs(@log(an) - @log(an_pic));
            if (d < bd) {
                bd = d;
                br = r;
            }
        }
        if (an_pic > 1) fx = f0 * br else fy = f0 * br;
        note("grain: {d} cells across, {d} down\n", .{ fx, fy });
    } else note("grain: none (across against down {d:.2})\n", .{an_pic});
    oct = octFor(n, @max(fx, fy));
    note("octaves: {d} (to two pixels at {d})\n", .{ oct, n });
    // warp: the bending of the lines, where there are lines (a grain or ridges)
    var warp: f32 = 0;
    var wf: i32 = @max(2, @min(fx, fy) * 2);
    if (kind != 0 or fx != fy) {
        const wg_pic = R.wiggle(pic.t, n, 3);
        bd = 1e9;
        for ([_]f32{ 0, 0.01, 0.025, 0.05, 0.1 }) |wv| {
            const wg = readNoiseCand(g, pic, kind, rev, fx, fy, oct, gain, wv, wf, .wiggle);
            note("  warp {d:.3}: the lines bend {d:.3} (the picture's {d:.3})\n", .{ wv, wg, wg_pic });
            if (absDiff(wg, wg_pic) < bd) {
                bd = absDiff(wg, wg_pic);
                warp = wv;
            }
        }
        note("warp: {d:.3} over {d} cells\n", .{ warp, wf });
    } else wf = 2;
    const ix = add(g, noiseNode(kind, fx, fy, oct, gain, warp, wf, 1));
    return .{ .field = ix, .reversed = rev, .fx = fx, .fy = fy, .oct = oct, .gain = gain, .kind = kind, .warp = warp, .wf = wf };
}

/// octaves from f cells across down to two pixels of an n pixel picture
fn octFor(n: usize, f: i32) i32 {
    var o: i32 = 1;
    var c: usize = @intCast(f);
    while (c * 4 <= n and o < 10) : (o += 1) c *= 2;
    return @max(3, o);
}

const NRead = enum { skew, cross, aniso, ratio, wiggle, coherence };

fn readNoiseOct(g: *P.Graph, pic: *const Pic, kind: u32, rev: bool, fx: i32, fy: i32, oct: i32, gain: f32) [R.NBAND]f32 {
    const n = pic.n;
    const keep = g.n;
    const ix = add(g, noiseNode(kind, fx, fy, oct, gain, 0, 2, 1));
    var dr = drawNode(g, ix, n);
    g.n = keep;
    const rk = ranked(dr.grey, pic, rev);
    dr.free();
    defer alloc.free(rk);
    return R.octaves(rk, n);
}

fn readNoiseCand(g: *P.Graph, pic: *const Pic, kind: u32, rev: bool, fx: i32, fy: i32, oct: i32, gain: f32, warp: f32, wf: i32, what: NRead) f32 {
    const n = pic.n;
    const keep = g.n;
    const ix = add(g, noiseNode(kind, fx, fy, oct, gain, warp, wf, 1));
    var dr = drawNode(g, ix, n);
    g.n = keep;
    const rk = ranked(dr.grey, pic, rev);
    dr.free();
    defer alloc.free(rk);
    return switch (what) {
        .skew => R.hpSkew(rk, n, 3),
        .cross => 0.5 * (R.bandCross(rk, n, n / 64, n / 16, true) + R.bandCross(rk, n, n / 64, n / 16, false)),
        .coherence => R.coherence(rk, n, 2),
        .aniso => R.aniso(rk, n, 2),
        .ratio => R.detailRatio(rk, n),
        .wiggle => R.wiggle(rk, n, 3),
    };
}

pub const Struct = struct { tiles: usize = 0, layout: u32 = 0, nx: i32 = 1, ny: i32 = 1, floor: f32 = 0.3, ok: bool = false, jc: ?[3]f32 = null };

/// the words version 3 of Tiles adds (milestone 2d): the joint's hollow, the second seed's offset, the framed tiles'
/// central square
pub const V3 = struct { hollow: f32 = 0, sox: f32 = 0.5, soy: f32 = 0.5, inner: f32 = 0.33 };

/// Tiles as milestone 2b wrote it (version 1), or version 3 where a layout or a word of version 3 is needed
pub fn tilesNodeV(layout: u32, nx: i32, ny: i32, bond: f32, joint: f32, bevel: f32, round: f32, vary: f32, size: f32, phx: f32, phy: f32, x: V3) P.Node {
    if (layout <= 8 and x.hollow == 0) return tilesNode(layout, nx, ny, bond, joint, bevel, round, vary, size, phx, phy);
    return mk(K_TILES, &.{ 3, @floatFromInt(layout), @floatFromInt(nx), @floatFromInt(ny), bond, joint, bevel, round, 0.02, vary, 7, 0.0015, 32, 0.3, size, phx, phy, 0, 64, 0, 256, 3, 0, 16, x.hollow, x.sox, x.soy, x.inner }, &.{});
}

/// a Tiles node's word as a decimal (f), a whole number (i) or a raw word
pub fn tw(g: *const P.Graph, ix: usize, i: usize) f32 {
    const kd = P.ops[P.OP_MODERN + K_TILES].kinds[i];
    const w = g.nodes[ix].w[i];
    return switch (kd) {
        'i' => @floatFromInt(@as(i32, @bitCast(w))),
        'f' => @as(f32, @bitCast(w)),
        else => @floatFromInt(w),
    };
}

pub fn tilesNode(layout: u32, nx: i32, ny: i32, bond: f32, joint: f32, bevel: f32, round: f32, vary: f32, size: f32, phx: f32, phy: f32) P.Node {
    return mk(K_TILES, &.{ 1, @floatFromInt(layout), @floatFromInt(nx), @floatFromInt(ny), bond, joint, bevel, round, 0.02, vary, 7, 0.0015, 32, 0.3, size, phx, phy }, &.{});
}

/// the structure: the layout whose mean cell lies best over the picture's, at the shift that fits best
fn readStructure(g: *P.Graph, pic: *const Pic, rd: *const P.Reading, opt: MOpt) Struct {
    const n = pic.n;
    var out = Struct{};
    if (rd.nrect == 0 or rd.share < 0.02) {
        note("structure: none read (no repeat with a shape)\n", .{});
        return out;
    }
    var cw: usize = 0;
    var ch: usize = 0;
    const pc = R.meanCell(pic.t, n, rd.nx, rd.ny, &cw, &ch);
    defer alloc.free(pc);
    note("structure: the picture repeats {d} by {d} (a cell of {d} by {d} pixels at {d})\n", .{ rd.nx, rd.ny, cw, ch, n });
    const Cand = struct { layout: u32, ax: i32, ay: i32, bond: f32, size: f32, round: f32 };
    var cands: std.ArrayList(Cand) = .empty;
    defer cands.deinit(alloc);
    const pieces = [_][2]i32{ .{ 1, 1 }, .{ 1, 2 }, .{ 2, 1 }, .{ 2, 2 } };
    for (pieces) |pp| {
        cands.append(alloc, .{ .layout = 0, .ax = pp[0], .ay = pp[1], .bond = 0, .size = 0.5, .round = 0.05 }) catch unreachable;
        if (@mod(pp[1], 2) == 0) cands.append(alloc, .{ .layout = 1, .ax = pp[0], .ay = pp[1], .bond = 0.5, .size = 0.5, .round = 0.05 }) catch unreachable;
        if (@mod(pp[0], 2) == 0 and @mod(pp[1], 2) == 0) cands.append(alloc, .{ .layout = 2, .ax = pp[0], .ay = pp[1], .bond = 0, .size = 0.5, .round = 0.05 }) catch unreachable;
    }
    // lozenges only where the cell's edges run on the diagonals (their own reading); upright shapes never take them
    const diag = R.diagonal(pc, cw, ch);
    const lozenges_ok = diag >= 0.12;
    note("structure: the cell's edges run on the diagonals {d:.3} (lozenges are tried from 0.12)\n", .{diag});
    for ([_]f32{ 0.5, 0.7, 0.9 }) |sz| {
        if (lozenges_ok) {
            cands.append(alloc, .{ .layout = 4, .ax = 1, .ay = 1, .bond = 0, .size = sz, .round = 0.3 }) catch unreachable;
            cands.append(alloc, .{ .layout = 4, .ax = 2, .ay = 2, .bond = 0, .size = sz, .round = 0.3 }) catch unreachable;
        }
        cands.append(alloc, .{ .layout = 6, .ax = 1, .ay = 1, .bond = 0, .size = sz * 0.6, .round = 0.05 }) catch unreachable;
        cands.append(alloc, .{ .layout = 8, .ax = 1, .ay = 1, .bond = 0, .size = sz * 0.4, .round = 0.05 }) catch unreachable;
    }
    const names = [_][]const u8{ "grid", "bond", "checker", "hexagons", "lozenges", "studs", "octagons", "planks", "inserts", "pairs", "framed" };
    var best: Cand = cands.items[0];
    var best_a = R.Align{};
    var best_key: f32 = -1;
    for (cands.items) |cd| {
        const keep = g.n;
        const ix = add(g, tilesNode(cd.layout, @as(i32, @intCast(rd.nx)) * cd.ax, @as(i32, @intCast(rd.ny)) * cd.ay, cd.bond, 0.015, 0.03, cd.round, 0.0, cd.size, 0, 0));
        var dr = drawNode(g, ix, n);
        g.n = keep;
        var dcw: usize = 0;
        var dch: usize = 0;
        // the checker's two shades say which slab is which: its grey, signed; joints alone: the height, either sign
        // inserts are drawn above every piece (1); they are read as darker than the tiles (a light insert is not read
        // yet), so their cell is laid turned over
        if (cd.layout == 6 or cd.layout == 8) {
            for (dr.grey) |*v| v.* = 1.0 - v.*;
        }
        const dc = R.meanCell(dr.grey, n, rd.nx, rd.ny, &dcw, &dch);
        // the checker's two shades, and inserts (the darker pieces where four tiles meet), are laid by their grey,
        // signed; joints alone by grey or height, either sign (a light mortar against drawn dark joints)
        const signed = cd.layout == 2 or cd.layout == 6 or cd.layout == 8;
        var a = R.alignCells(pc, dc, cw, ch, signed);
        alloc.free(dc);
        if (!signed) {
            // the relief's height too: joints alone, either sign; the closer of the two counts
            const dh = R.meanCell(dr.h, n, rd.nx, rd.ny, &dcw, &dch);
            const ah = R.alignCells(pc, dh, cw, ch, false);
            alloc.free(dh);
            if (@abs(ah.corr) > @abs(a.corr)) a = ah;
        }
        dr.free();
        const key = if (signed) a.corr else @abs(a.corr);
        note("  {s} {d} by {d} pieces a cell{s}: the cells agree {d:.3} at a shift of {d}, {d} pixels\n", .{ names[cd.layout], cd.ax, cd.ay, if (cd.layout == 4 or cd.layout == 6 or cd.layout == 8) " (sized)" else "", a.corr, a.sx, a.sy });
        if (key > best_key + 0.005) {
            best_key = key;
            best = cd;
            best_a = a;
        }
    }
    if (best_key < 0.25) {
        note("structure: refused, no layout's cell agrees with the picture's by 0.25 or more (best {d:.3})\n", .{best_key});
        return out;
    }
    // milestone 2d: framed tiles (Daniel on the terracotta: "one tiny centralized square with surrounding trapezoids,
    // larger side to the outside border, smaller one are the square facate - that are overlaped by the black square"),
    // tried where the inserts layout won, both laid as a map of their parts (inserts dark, joints darker than faces)
    var x3 = V3{};
    var layout_v: u32 = best.layout;
    if (best.layout == 8) {
        if (!opt.framed) note("framed tiles: not tried (framed=0)\n", .{}) else {
            const nx8 = @as(i32, @intCast(rd.nx)) * best.ax;
            const ny8 = @as(i32, @intCast(rd.ny)) * best.ay;
            const ref = partsAgree(g, pic, rd, pc, cw, ch, tilesNodeV(8, nx8, ny8, 0, 0.015, 0.03, best.round, 0, best.size, 0, 0, .{}));
            note("framed tiles: the inserts layout laid as a map of its parts agrees {d:.3}\n", .{ref.corr});
            var bf: f32 = ref.corr + 0.01;
            var bin: f32 = 0;
            for ([_]f32{ 0.2, 0.27, 0.33, 0.4, 0.5 }) |inner| {
                const a = partsAgree(g, pic, rd, pc, cw, ch, tilesNodeV(10, nx8, ny8, 0, 0.015, 0.03, best.round, 0, best.size, 0, 0, .{ .inner = inner }));
                note("  framed, a central square {d:.2} of the tile: the cells agree {d:.3} at a shift of {d}, {d} pixels\n", .{ inner, a.corr, a.sx, a.sy });
                if (a.corr > bf) {
                    bf = a.corr;
                    bin = inner;
                    best_a = a;
                }
            }
            if (bin > 0) {
                layout_v = 10;
                x3.inner = bin;
                note("framed tiles: chosen, a central square {d:.2} of the tile with four trapezoids around it\n", .{bin});
            } else note("framed tiles: not chosen (none agrees 0.01 better than the inserts layout)\n", .{});
        }
    }
    // milestone 2d: the lozenges' two seeds apart (Daniel on the metal plate: "we need a way to shift the two seeds in
    // space, they are forming a line"): two lozenges a cell, the second moved by an offset read from the picture; laid
    // over the picture's cell of one pair (each row of the repeat holding one of the two)
    var pairs_ny: i32 = 0;
    if (best.layout == 4 and lozenges_ok) {
        if (!opt.pairs) note("pairs: not tried (pairs=0)\n", .{}) else if (rd.ny >= 4) {
            const nxp: i32 = @intCast(rd.nx);
            const keep_a = best_a;
            const keep_size = best.size;
            const keep_cw = cw;
            const keep_ch = ch;
            const ref_node = tilesNodeV(4, nxp * best.ax, @as(i32, @intCast(rd.ny)) * best.ay, 0, 0.015, 0.03, best.round, 0, best.size, 0, 0, .{});
            var bkp: f32 = -1;
            var bref: f32 = 0;
            for ([_]i32{ -1, 0, 1 }) |dny| {
                const nyp: i32 = @divFloor(@as(i32, @intCast(rd.ny)), 2) + dny;
                if (nyp < 1) continue;
                var pcw: usize = 0;
                var pch: usize = 0;
                const pc2 = R.meanCell(pic.t, n, @intCast(nxp), @intCast(nyp), &pcw, &pch);
                defer alloc.free(pc2);
                const ra = lozAgree(g, n, pc2, @intCast(nxp), @intCast(nyp), pcw, pch, ref_node);
                note("  pairs over a cell of 1 by {d} of the picture: the checker of lozenges agrees {d:.3}\n", .{ nyp, ra.corr });
                for ([_]f32{ 0.5, 0.7, 0.9 }) |sz| {
                    for ([_]f32{ 0.3, 0.4, 0.5, 0.6, 0.7 }) |soy| {
                        const a = lozAgree(g, n, pc2, @intCast(nxp), @intCast(nyp), pcw, pch, tilesNodeV(9, nxp, nyp, 0, 0.015, 0.03, best.round, 0, sz, 0, 0, .{ .sox = 0.5, .soy = soy }));
                        if (@abs(a.corr) - @abs(ra.corr) > bkp) {
                            bkp = @abs(a.corr) - @abs(ra.corr);
                            bref = @abs(ra.corr);
                            pairs_ny = nyp;
                            x3.sox = 0.5;
                            x3.soy = soy;
                            best.size = sz;
                            best_a = a;
                            cw = pcw;
                            ch = pch;
                        }
                    }
                }
            }
            if (bkp > 0.005) {
                layout_v = 9;
                note("pairs: chosen, {d} by {d} cells over the picture, the second lozenge moved {d:.2} across and {d:.2} down a cell, size {d:.2} (they agree {d:.3}, the checker {d:.3})\n", .{ rd.nx, pairs_ny, x3.sox, x3.soy, best.size, bref + bkp, bref });
            } else {
                note("pairs: not chosen (no pair agrees 0.005 better than the checker)\n", .{});
                pairs_ny = 0;
                best_a = keep_a;
                best.size = keep_size;
                cw = keep_cw;
                ch = keep_ch;
            }
        }
    }
    const nx = if (layout_v == 9) @as(i32, @intCast(rd.nx)) else @as(i32, @intCast(rd.nx)) * best.ax;
    const ny = if (layout_v == 9) pairs_ny else @as(i32, @intCast(rd.ny)) * best.ay;
    // the shift moves the drawing onto the picture: the phase in pieces
    const pax: f32 = if (layout_v == 9) 1 else @floatFromInt(best.ax);
    const pay: f32 = if (layout_v == 9) 1 else @floatFromInt(best.ay);
    const phx0 = -@as(f32, @floatFromInt(best_a.sx)) / @as(f32, @floatFromInt(cw)) * pax;
    const phy0 = -@as(f32, @floatFromInt(best_a.sy)) / @as(f32, @floatFromInt(ch)) * pay;
    // the pattern repeats every period pieces (a bond every two rows, a checker and lozenges every two pieces): the
    // phase is taken within one period
    const perx: f32 = if (layout_v == 2 or layout_v == 4) 2 else 1;
    const pery: f32 = if (layout_v == 1 or layout_v == 2 or layout_v == 4) 2 else 1;
    const phx = phx0 - perx * @floor(phx0 / perx);
    const phy = phy0 - pery * @floor(phy0 / pery);
    note("structure: {s}, {d} by {d} pieces over the picture, the joints moved {d:.3}, {d:.3} pieces\n", .{ names[layout_v], nx, ny, phx, phy });
    // the joint's width and the bevel, by laying the cells over each other at that place
    var bj: f32 = 0.06;
    var bb: f32 = 0.04;
    var bk: f32 = -1;
    // inserts: their size is read with the joints (else a wide joint stands in for a larger insert)
    const ins = layout_v == 6 or layout_v == 8 or layout_v == 10;
    var bsz = best.size;
    const sizes = if (ins) [_]f32{ 0.28, 0.33, 0.38, 0.43 } else [_]f32{ best.size, best.size, best.size, best.size };
    const bevels = if (ins) [_]f32{ 0.06, 0.06, 0.06, 0.06 } else [_]f32{ 0.02, 0.06, 0.14, 0.3 };
    for ([_]f32{ 0.02, 0.04, 0.07, 0.11, 0.16, 0.24 }) |jt| {
        if (layout_v == 9) break; // pairs: the cell is the pair's, not the repeat's; the starting width is kept, said
        for (0..4) |k4| {
            const bv = bevels[k4];
            const szv = sizes[k4];
            const keep = g.n;
            const ix = add(g, tilesNodeV(layout_v, nx, ny, best.bond, jt, bv, best.round, 0, szv, phx, phy, x3));
            var dr = drawNode(g, ix, n);
            g.n = keep;
            // a layout is pieces with joints between them: at least 0.3 of the picture must be faces
            var faces: usize = 0;
            for (dr.h, dr.grey) |hv, gv| {
                if (hv > 0.85 and gv <= 0.86) faces += 1;
            }
            if (@as(f32, @floatFromInt(faces)) < 0.3 * @as(f32, @floatFromInt(n * n))) {
                dr.free();
                continue;
            }
            var dcw: usize = 0;
            var dch: usize = 0;
            const sg = layout_v == 2 or layout_v == 6 or layout_v == 8 or layout_v == 10;
            if (layout_v == 6 or layout_v == 8 or layout_v == 10) {
                for (dr.grey) |*v| v.* = 1.0 - v.*;
            }
            const dc = R.meanCell(if (sg) dr.grey else dr.h, n, rd.nx, rd.ny, &dcw, &dch);
            const a = R.alignCells(pc, dc, cw, ch, sg);
            alloc.free(dc);
            dr.free();
            const key = if (sg) a.corr else @abs(a.corr);
            // the joints are already at their place: only a shift of under an eighth of a cell either way counts
            const dsx = @min(a.sx, cw - a.sx);
            const dsy = @min(a.sy, ch - a.sy);
            if (key > bk and dsx * 8 < cw and dsy * 8 < ch) {
                bk = key;
                bj = jt;
                bb = bv;
                bsz = szv;
            }
        }
    }
    if (bk < -0.5) note("joints: no width agreed at the joints' place; the starting width {d:.2} and bevel {d:.2} are kept (said, not chosen)\n", .{ bj, bb }) else note("joints: {d:.2} of a piece wide, bevel {d:.2}{s} (the cells agree {d:.3})\n", .{ bj, bb, if (ins) ", inserts read with them" else "", bk });
    if (ins) note("inserts: {d:.2} of a piece across\n", .{bsz});
    const ix = add(g, tilesNodeV(layout_v, nx, ny, best.bond, bj, bb, best.round, 0.6, bsz, phx, phy, x3));
    out = .{ .tiles = ix, .layout = layout_v, .nx = nx, .ny = ny, .floor = 0.3, .ok = true };
    return out;
}

/// the mean of the picture's colours where sel holds
pub fn meanColour(pic: *const Pic, sel: []const bool) [3]f32 {
    var c = [3]f64{ 0, 0, 0 };
    var k: f64 = 0;
    for (sel, 0..) |s, i| {
        if (!s) continue;
        inline for (0..3) |ch| c[ch] += pic.rgb[3 * i + ch];
        k += 1;
    }
    if (k == 0) return .{ 0.5, 0.5, 0.5 };
    return .{ @floatCast(c[0] / k), @floatCast(c[1] / k), @floatCast(c[2] / k) };
}

/// the picture's colour at a rank of its main axis among the selected pixels
pub fn colourAtRankSel(pic: *const Pic, q: f32, sel: []const bool) [3]f32 {
    var idx: std.ArrayList(u32) = .empty;
    defer idx.deinit(alloc);
    for (sel, 0..) |s, i| {
        if (s) idx.append(alloc, @intCast(i)) catch unreachable;
    }
    if (idx.items.len < 16) return colourAtRank(pic, q);
    const Ctx = struct {
        t: []const f32,
        fn lt(c: @This(), a: u32, b: u32) bool {
            return c.t[a] < c.t[b];
        }
    };
    std.mem.sort(u32, idx.items, Ctx{ .t = pic.t }, Ctx.lt);
    const m = idx.items.len;
    const lo: usize = @intFromFloat(@max(0.0, q - 0.02) * @as(f32, @floatFromInt(m - 1)));
    const hi: usize = @intFromFloat(@min(1.0, q + 0.02) * @as(f32, @floatFromInt(m - 1)));
    var c = [3]f32{ 0, 0, 0 };
    for (idx.items[lo .. hi + 1]) |ix| {
        inline for (0..3) |ch| c[ch] += pic.rgb[3 * ix + ch];
    }
    inline for (0..3) |ch| c[ch] /= @floatFromInt(hi - lo + 1);
    return c;
}

/// the picture's colour at a rank of its main axis (the mean of a band of ranks around it)
pub fn colourAtRank(pic: *const Pic, q: f32) [3]f32 {
    const n2 = pic.n * pic.n;
    const idx = alloc.alloc(u32, n2) catch unreachable;
    defer alloc.free(idx);
    for (idx, 0..) |*v, i| v.* = @intCast(i);
    const Ctx = struct {
        t: []const f32,
        fn lt(c: @This(), a: u32, b: u32) bool {
            return c.t[a] < c.t[b];
        }
    };
    std.mem.sort(u32, idx, Ctx{ .t = pic.t }, Ctx.lt);
    const lo: usize = @intFromFloat(@max(0.0, q - 0.02) * @as(f32, @floatFromInt(n2 - 1)));
    const hi: usize = @intFromFloat(@min(1.0, q + 0.02) * @as(f32, @floatFromInt(n2 - 1)));
    var c = [3]f32{ 0, 0, 0 };
    for (idx[lo .. hi + 1]) |ix| {
        inline for (0..3) |ch| c[ch] += pic.rgb[3 * ix + ch];
    }
    inline for (0..3) |ch| c[ch] /= @floatFromInt(hi - lo + 1);
    return c;
}

pub const Rung = struct { root: usize, label: []const u8 };

pub const MOpt = struct {
    full: ?[*:0]const u8 = null, // the picture at full size: tiles of 512 corrected where they differ
    tile: usize = 512,
    seeds: ?[*:0]const u8 = null, // milestone 2's seed, as the eye chose it (a .chosen file): a glyph scattered at the repeat
    light: bool = true, // light=0: the eye left the light off (its sheet shows the procedure with and without it)
    close: bool = true, // close=0: milestone 2b's procedure, without the close-up layers of milestone 2c
    grain_in_field: bool = false, // grainat=field: the close-up grain laid into the field before the Ramp
    off: []const u8 = "", // off=NAME,...: close-up layers the eye refused (grain, chips, mortar, patches, spots, furrows, knots, stones, pits)
    seed: i32 = 0, // seed=N: every seed word moved by N (a quarter of a picture fitted apart, milestone 2d)
    joints_full: bool = true, // joints=scan: the joints' width and bevel as the scan at 512 read them (milestone 2b); else read again at 1:1
    pairs: bool = true, // pairs=0: the lozenges' two seeds are not tried apart (milestone 2c's checker only)
    framed: bool = true, // framed=0: framed tiles are not tried (milestone 2c's inserts only)
    on: []const u8 = "", // on=NAME,...: close-up layers the eye asked for below their readings' thresholds (spots); their values still read
    marks_soft: bool = true, // marks=fixed: the second material's and the spots' edges as milestone 2c drew them; else their softness read
    grain_cap: bool = true, // grainfit=closest: a piece's grain chosen closest to the picture's bands (milestone 2c); else the closest that exceeds none of them
};

pub fn run(path: [*:0]const u8, prefix: []const u8, opt: MOpt) void {
    const t0 = P.seconds();
    P.say_refusals = true;
    seed_base = opt.seed;
    if (opt.seed != 0) note("seeds: every seed word moved by {d} (seed={d})\n", .{ opt.seed, opt.seed });
    const img = P.readPpm(path);
    const n = img.w;
    if (img.h != n) P.die("the picture must be square ({d}x{d})", .{ img.w, img.h });
    var full: u32 = 0;
    while ((@as(usize, 1) << @intCast(full)) < n) full += 1;
    var tread = P.makeTarget(img, full);
    var rd = P.readPicture(&tread);
    P.freeTarget(&tread);
    const tsort = R.sorted(rd.t);
    const pic = Pic{ .n = n, .rgb = img.rgb, .t = rd.t, .tsort = tsort };
    var g = P.Graph{};
    var rungs: std.ArrayList(Rung) = .empty;
    note("the picture: {d} by {d}; milestone 1's readings above\n", .{ n, n });

    // 1. the surface's noise
    const nb = readNoise(&g, &pic, &rd);

    // 2. a motif on a ground (milestone 2's seed, as the eye chose it), or the structure with the noise in its faces
    var motif = false;
    if (opt.seeds) |sp| {
        P.loadSeed(sp);
        if (P.nseeds == 1) motif = true else note("motif: the seed file holds {d} seeds, one per piece: the eye refused them in milestone 2, so the motif stays with the image\n", .{P.nseeds});
    }
    var st = if (motif or opt.seeds != null) Struct{} else readStructure(&g, &pic, &rd, opt);
    if (st.ok and opt.full != null) {
        if (opt.joints_full) jointsAtFull(&g, &st, opt.full.?, opt.framed, CL.refused(opt.on, "framed")) else note("joints at 1:1: not read (joints=scan: the scan's width at 512 kept)\n", .{});
    }
    if (opt.seeds != null and !motif) note("structure: not read (a figure on a ground: its motif is the seed's)\n", .{});
    var colour: usize = 0;
    var main_ramp: usize = 0;
    var face_layer: usize = 0;
    var ground_c = [3]f32{ 0, 0, 0 };
    var ink_c = [3]f32{ 0, 0, 0 };
    if (opt.seeds != null) {
        ground_c = rgbOfWord(if (motif) P.seeds[0].ground else rd.c0);
        ink_c = rgbOfWord(if (motif) P.seeds[0].ink else rd.c1);
        const gsel = alloc.alloc(bool, n * n) catch unreachable;
        defer alloc.free(gsel);
        for (0..n * n) |i| {
            var dg: f32 = 0;
            var di: f32 = 0;
            inline for (0..3) |q| {
                dg += (pic.rgb[3 * i + q] - ground_c[q]) * (pic.rgb[3 * i + q] - ground_c[q]);
                di += (pic.rgb[3 * i + q] - ink_c[q]) * (pic.rgb[3 * i + q] - ink_c[q]);
            }
            gsel[i] = 4.0 * dg <= di;
        }
        var dn = drawNode(&g, nb.field, n);
        defer dn.free();
        const rw = rampWords(dn.grey, null, &pic, gsel, nb.reversed, null);
        colour = add(&g, mk(K_RAMP, &rw, &.{nb.field}));
        main_ramp = colour;
        rungs.append(alloc, .{ .root = colour, .label = "ground: Noise, Ramp" }) catch unreachable;
        if (motif) {
            const sd = &P.seeds[0];
            var fl = P.Node{ .op = P.OP_FLAT, .nw = 3 };
            fl.w[0] = 7;
            fl.w[1] = 7;
            fl.w[2] = 0xff000000;
            const fi = add(&g, fl);
            var tx = P.seedText(sd, 0.5, 0.5, 0.5, 0.5, 128);
            tx.nin = 1;
            tx.in[0] = @intCast(fi);
            const ti = add(&g, tx);
            const cw = 1.0 / sd.nx;
            const ch = 1.0 / sd.ny;
            const m = @min(cw, ch);
            const hw = sd.box.hw * cw;
            const hh = sd.box.hh * ch;
            const phx = sd.box.cx - 0.5 + sd.ox * sd.nx;
            const phy = sd.box.cy - 0.5 + sd.oy * sd.ny;
            colour = add(&g, mk(K_SCATTER, &.{ 1, sd.nx, sd.ny, 1, hw / m, 0, 0, 0, colourWord(ink_c), 0, 1, 0.3, 0.5, hh / hw, 1, phx, phy }, &.{ colour, ti }));
            note("motif: U+{X} of {s} (milestone 2's seed, chosen by eye), {d} by {d} over the picture, {d:.3} by {d:.3} of the picture: Scatter of its glyph\n", .{ sd.cp, sd.key, sd.nx, sd.ny, 2 * hw, 2 * hh });
            rungs.append(alloc, .{ .root = colour, .label = "+ the motif (Text, Scatter)" }) catch unreachable;
        }
    } else if (st.ok) {
        // the faces' texture: the share of the faces' variation that lies between pieces, matched
        var dt = drawNode(&g, st.tiles, n);
        defer dt.free();
        const face = alloc.alloc(bool, n * n) catch unreachable;
        defer alloc.free(face);
        const jsel = alloc.alloc(bool, n * n) catch unreachable;
        defer alloc.free(jsel);
        for (0..n * n) |i| {
            face[i] = dt.h[i] > 0.85;
            jsel[i] = dt.h[i] < 0.15;
        }
        const between_pic = betweenShare(pic.t, dt.grey, face, n);
        var bk: f32 = 0.1;
        var bd: f32 = 1e9;
        for ([_]f32{ 0.03, 0.06, 0.1, 0.16, 0.25, 0.4 }) |k| {
            const keep = g.n;
            const lx = add(&g, mk(K_LAYER, &.{ 1, 3, 0, st.floor, k, 2, 0.15 }, &.{ st.tiles, nb.field, st.tiles }));
            var dl = drawNode(&g, lx, n);
            g.n = keep;
            const bs = betweenShare(dl.grey, dt.grey, face, n);
            dl.free();
            note("  texture {d:.2} in the faces: {d:.2} of the faces' variation between pieces (the picture's {d:.2})\n", .{ k, bs, between_pic });
            if (absDiff(bs, between_pic) < bd) {
                bd = absDiff(bs, between_pic);
                bk = k;
            }
        }
        const lx = add(&g, mk(K_LAYER, &.{ 1, 3, 0, st.floor, bk, 2, 0.15 }, &.{ st.tiles, nb.field, st.tiles }));
        var dl = drawNode(&g, lx, n);
        defer dl.free();
        const jc = st.jc orelse meanColour(&pic, jsel);
        note("joint colour {x:0>6} ({s})\n", .{ @as(u32, @intFromFloat(colourWord(jc))) & 0xffffff, if (st.jc != null) "the picture's mean in the joints' core at 1:1" else "the picture's mean where the drawing has its joints" });
        const rw = rampWords(dl.grey, face, &pic, face, false, jc);
        colour = add(&g, mk(K_RAMP, &rw, &.{lx}));
        main_ramp = colour;
        face_layer = lx;
        if (st.layout == 6 or st.layout == 8 or st.layout == 10) {
            // inserts: the structure's value 1 (above every piece); their own colour, measured where the drawing has
            // them, laid by a Layer whose mask is the structure itself
            const isel = alloc.alloc(bool, n * n) catch unreachable;
            defer alloc.free(isel);
            for (0..n * n) |i| isel[i] = dt.grey[i] > 0.93;
            const ic = colourWord(meanColour(&pic, isel));
            note("insert colour {x:0>6} (the picture's mean where the drawing has its inserts)\n", .{@as(u32, @intFromFloat(ic)) & 0xffffff});
            const ir = add(&g, mk(K_RAMP, &.{ 1, 2, 0, ic, 1, ic, 1, ic, 1, ic, 1, ic, 1, ic, 1, ic, 1, ic }, &.{st.tiles}));
            colour = add(&g, mk(K_LAYER, &.{ 1, 0, 0.87, 0.93, 1, 0, 0 }, &.{ colour, ir, st.tiles }));
        }
        rungs.append(alloc, .{ .root = colour, .label = "Tiles, Noise in the faces, Ramp" }) catch unreachable;
    } else {
        var dn = drawNode(&g, nb.field, n);
        defer dn.free();
        const rw = rampWords(dn.grey, null, &pic, null, nb.reversed, null);
        colour = add(&g, mk(K_RAMP, &rw, &.{nb.field}));
        main_ramp = colour;
        rungs.append(alloc, .{ .root = colour, .label = "Noise, Ramp" }) catch unreachable;
    }

    // 3. a second material (milestone 1's reading: colours off the main axis, as one cluster)
    var second_mask: ?usize = null;
    var second_layer: usize = 0;
    var second_col = [3]f32{ 0, 0, 0 };
    if (rd.off >= 0.01 and rd.off_coh >= 0.8) {
        second_col = rgbOfWord(rd.off_col);
        const sel = alloc.alloc(bool, n * n) catch unreachable;
        defer alloc.free(sel);
        const mask = alloc.alloc(f32, n * n) catch unreachable;
        defer alloc.free(mask);
        offMask(&pic, &rd, mask, sel);
        var share: f32 = 0;
        for (sel) |s| share += if (s) 1 else 0;
        share /= @floatFromInt(n * n);
        const cl = @max(R.corrLength(mask, n, false), 1.0);
        const cells: i32 = @max(1, @as(i32, @intFromFloat(@as(f32, @floatFromInt(n)) / (2.5 * cl))));
        const epa_pic = R.edgePerArea(mask, n, 0.5);
        note("second material {x:0>6}: {d:.3} of the pixels, patches about {d:.0} pixels across ({d} cells), edge {d:.3} per pixel inside\n", .{ rd.off_col & 0xffffff, share, cl, cells, epa_pic });
        var bw: f32 = 0;
        var bdd: f32 = 1e9;
        var lo: f32 = 0.5;
        var hi: f32 = 0.6;
        for ([_]f32{ 0, 0.02, 0.05, 0.1 }) |wv| {
            const keep = g.n;
            const mx = add(&g, noiseNode(0, cells, cells, 6, 0.6, wv, cells * 2, 5));
            var dm = drawNode(&g, mx, n);
            g.n = keep;
            const thr = R.quantile(dm.grey, 1.0 - share);
            const bin = alloc.alloc(f32, n * n) catch unreachable;
            for (dm.grey, 0..) |v, i| bin[i] = if (v > thr) 1 else 0;
            const epa = R.edgePerArea(bin, n, 0.5);
            alloc.free(bin);
            note("  patches warped {d:.2}: edge {d:.3} per pixel inside\n", .{ wv, epa });
            if (absDiff(epa, epa_pic) < bdd) {
                bdd = absDiff(epa, epa_pic);
                bw = wv;
                lo = R.quantile(dm.grey, 1.0 - 1.4 * share);
                hi = R.quantile(dm.grey, 1.0 - 0.6 * share);
            }
            dm.free();
        }
        const mx = add(&g, noiseNode(0, cells, cells, 6, 0.6, bw, cells * 2, 5));
        second_mask = mx;
        var dn = drawNode(&g, nb.field, n);
        defer dn.free();
        const rw = rampWords(dn.grey, null, &pic, sel, nb.reversed, null);
        const r2 = add(&g, mk(K_RAMP, &rw, &.{nb.field}));
        if (opt.marks_soft) {
            // the softness of its edges and how much it is laid (blend) read: the dark marks' slope at their border and
            // their contrast, the drawing's made to agree with the picture's (wider soft thresholds, less amount)
            const pg = alloc.alloc(f32, n * n) catch unreachable;
            defer alloc.free(pg);
            for (0..n * n) |i| pg[i] = (pic.rgb[3 * i] + pic.rgb[3 * i + 1] + pic.rgb[3 * i + 2]) / 3.0;
            const pe = markEdge(pg, n);
            const base_c = colour;
            var bdist: f32 = 1e9;
            var bw2: f32 = 1;
            var bam: f32 = 1;
            const mid = 0.5 * (lo + hi);
            const hw = 0.5 * (hi - lo);
            for ([_]f32{ 1, 2, 4, 8 }) |wk| {
                for ([_]f32{ 1, 0.8, 0.6 }) |am| {
                    const keep = g.n;
                    const lx = add(&g, mk(K_LAYER, &.{ 1, 0, mid - hw * wk, mid + hw * wk, am, 2, 0.1 }, &.{ base_c, r2, mx }));
                    var dl = drawNode(&g, lx, n);
                    g.n = keep;
                    const de = markEdge(dl.grey, n);
                    dl.free();
                    const d = @abs(@log((de[0] + 1e-4) / (pe[0] + 1e-4))) + @abs(@log((de[1] + 1e-4) / (pe[1] + 1e-4)));
                    note("  second material softened {d:.0} times, laid {d:.1}: edges {d:.3}, contrast {d:.2} (the picture's {d:.3}, {d:.2})\n", .{ wk, am, de[0], de[1], pe[0], pe[1] });
                    if (d < bdist) {
                        bdist = d;
                        bw2 = wk;
                        bam = am;
                    }
                }
            }
            lo = mid - hw * bw2;
            hi = mid + hw * bw2;
            colour = add(&g, mk(K_LAYER, &.{ 1, 0, lo, hi, bam, 2, 0.1 }, &.{ colour, r2, mx }));
            note("second material: its edges softened {d:.0} times and laid {d:.1} (read: the dark marks' edges and contrast)\n", .{ bw2, bam });
        } else colour = add(&g, mk(K_LAYER, &.{ 1, 0, lo, hi, 1, 2, 0.1 }, &.{ colour, r2, mx }));
        second_layer = colour;
        note("second material laid where its noise is above {d:.3} to {d:.3}\n", .{ lo, hi });
        rungs.append(alloc, .{ .root = colour, .label = "+ second material (Noise, Ramp, Layer)" }) catch unreachable;
        // drips: the second material running down
        const ld = R.corrLength(mask, n, true);
        if (ld >= 1.5 * cl and ld - cl >= 3) {
            const len = (ld - cl) / @as(f32, @floatFromInt(n));
            colour = add(&g, mk(K_WEAR, &.{ 1, 2, 0.01, len, 0.15, 0.6, 0.6, colourWord(second_col), 64, 0.5, 9, 1.0 }, &.{ colour, mx }));
            note("drips: the patches run {d:.0} pixels down against {d:.0} across: Wear drips {d:.3} of the picture long\n", .{ ld, cl, len });
            rungs.append(alloc, .{ .root = colour, .label = "+ drips (Wear)" }) catch unreachable;
        } else note("drips: none (the patches run {d:.0} pixels down, {d:.0} across)\n", .{ ld, cl });
    } else note("second material: none (milestone 1's reading: {d:.3} of the pixels off the axis, alike {d:.2})\n", .{ rd.off, rd.off_coh });

    // 4. cracks: long thin dark pieces (not on a figure on a ground: the motif's own edges would count)
    const ground_only = opt.seeds != null;
    if (ground_only) note("cracks, stones, pits and specks: not read on a figure on a ground (the motif's edges would count as them)\n", .{});
    const bl = R.blobs(pic.t, n, 4, 2.0, true, 300);
    if (!ground_only and !st.ok and bl.lines >= 0.015 and bl.line_spacing > 4) {
        const cells: i32 = @max(2, @as(i32, @intFromFloat(@as(f32, @floatFromInt(n)) / bl.line_spacing)));
        const width = @min(0.5, bl.line_width / bl.line_spacing);
        const kx = add(&g, mk(K_CELLS, &.{ 1, 0, @floatFromInt(cells), @floatFromInt(cells), 0.9, width, 0.3 / @as(f64, @floatFromInt(cells)), @floatFromInt(cells * 4), 3, 0.5 }, &.{}));
        const crack_c = colourAtRank(&pic, 0.04);
        const face_c = colourAtRank(&pic, 0.5);
        var ratio: [3]f32 = undefined;
        inline for (0..3) |q| ratio[q] = @min(1.0, crack_c[q] / @max(0.01, face_c[q]));
        const kr = add(&g, mk(K_RAMP, &.{ 1, 2, 0, colourWord(ratio), 1, colourWord(.{ 1, 1, 1 }), 1, 0xffffffff, 1, 0xffffffff, 1, 0xffffffff, 1, 0xffffffff, 1, 0xffffffff, 1, 0xffffffff }, &.{kx}));
        colour = add(&g, mk(K_LAYER, &.{ 1, 1, -1, -0.5, 1, 4, 0.7 }, &.{ colour, kr, kx }));
        note("cracks: {d:.3} of the picture in long thin dark pieces, {d:.1} pixels apart, {d:.1} wide: Cells cracks {d} across\n", .{ bl.lines, bl.line_spacing, bl.line_width, cells });
        rungs.append(alloc, .{ .root = colour, .label = "+ cracks (Cells, Ramp, Layer)" }) catch unreachable;
    } else note("cracks: none ({d:.3} of the picture in long thin dark pieces)\n", .{bl.lines});

    // 5. pits, specks and stones: compact blobs darker or lighter than the surface around them
    var lit_reading: ?[2]f32 = null;
    var lit_src: LitSrc = .slopes;
    const stones = R.blobs(pic.t, n, 16, 1.4, false, 4000);
    if (!ground_only and !st.ok and stones.count >= 8 and stones.radius >= 5) {
        colour = addScatter(&g, &pic, colour, stones, 0.5, n, 0.85);
        note("stones: {d} light blobs of about {d:.1} pixels: Scatter, raised\n", .{ stones.count, stones.radius });
        rungs.append(alloc, .{ .root = colour, .label = "+ stones (Scatter)" }) catch unreachable;
        lit_reading = .{ stones.left_light, stones.up_light };
        lit_src = .stones;
    }
    // on a structure, the detail is read on the faces only: joints and inserts are the structure's, not pits or specks
    var tb = pic.t;
    var tb_own = false;
    var facesel: ?[]bool = null;
    defer if (facesel) |fsl| alloc.free(fsl);
    if (st.ok) {
        var ds = drawNode(&g, st.tiles, n);
        defer ds.free();
        const bt = R.blur(pic.t, n, 6);
        defer alloc.free(bt);
        const t2 = alloc.alloc(f32, n * n) catch unreachable;
        for (0..n * n) |i| t2[i] = if (ds.h[i] > 0.85) pic.t[i] else bt[i];
        const fsl = alloc.alloc(bool, n * n) catch unreachable;
        for (0..n * n) |i| fsl[i] = ds.h[i] > 0.85 and ds.grey[i] <= 0.86;
        facesel = fsl;
        tb = t2;
        tb_own = true;
        note("pits and specks: read on the structure's faces only\n", .{});
    }
    defer if (tb_own) alloc.free(tb);
    const pits = R.blobs(tb, n, 6, 2.5, true, 300);
    if (!ground_only and pits.count >= 8 and pits.radius >= 2.5) {
        colour = addScatterSel(&g, &pic, colour, pits, -0.35, n, 0.03, facesel);
        note("pits: {d} dark blobs of about {d:.1} pixels: Scatter, sunk\n", .{ pits.count, pits.radius });
        rungs.append(alloc, .{ .root = colour, .label = "+ pits (Scatter)" }) catch unreachable;
        if (lit_reading == null and pits.radius >= 3) {
            lit_reading = .{ -pits.left_light, -pits.up_light };
            lit_src = .pits;
        }
    } else note("pits: {d} dark blobs of about {d:.1} pixels (8 or more of 2.5 pixels or more are pits)\n", .{ pits.count, pits.radius });
    const specks = R.blobs(tb, n, 6, 2.5, false, 300);
    if (!ground_only and specks.count >= 8 and specks.radius >= 2.5) {
        colour = addScatterSel(&g, &pic, colour, specks, 0.1, n, 0.97, facesel);
        note("specks: {d} light blobs of about {d:.1} pixels: Scatter\n", .{ specks.count, specks.radius });
        rungs.append(alloc, .{ .root = colour, .label = "+ specks (Scatter)" }) catch unreachable;
    } else note("specks: {d} light blobs of about {d:.1} pixels (8 or more of 2.5 pixels or more are specks)\n", .{ specks.count, specks.radius });

    // 6. the light: on a structure, the picture's light against the drawn relief's slopes
    if (st.ok) {
        var dc = drawNode(&g, colour, n);
        defer dc.free();
        const lr = slopeLight(pic.t, dc.h, n);
        note("light on the relief: the picture brightens {d:.3} with the slope across, {d:.3} down (fit share {d:.3})\n", .{ lr[0], lr[1], lr[2] });
        if (lr[2] >= 0.01) {
            lit_reading = .{ lr[0], lr[1] };
            lit_src = .slopes;
        }
    }
    if (!opt.light and lit_reading != null) {
        note("light: read, and left off by eye (light=0: the sheet of the rungs shows it with and without)\n", .{});
        lit_reading = null;
    }
    if (lit_reading) |lr| {
        const len = @sqrt(lr[0] * lr[0] + lr[1] * lr[1]);
        if (len > (if (lit_src == .slopes) @as(f32, 0.05) else @as(f32, 0.3))) {
            const lx = -lr[0] / len * 0.6;
            const ly = -lr[1] / len * 0.6;
            // the depth: the drawn relief's light reading made to agree with the picture's
            var best_d: f32 = 0.004;
            var bd: f32 = 1e9;
            const target = len;
            for ([_]f32{ 0.001, 0.002, 0.004, 0.008, 0.016 }) |dp| {
                const keep = g.n;
                const sx = add(&g, mk(K_SHADE, &.{ 1, lx, ly, 0.8, dp, 0.8 }, &.{colour}));
                var ds = drawNode(&g, sx, n);
                g.n = keep;
                const lr2 = litReading(lit_src, ds.grey, ds.h, n);
                ds.free();
                const got = @sqrt(lr2[0] * lr2[0] + lr2[1] * lr2[1]);
                note("  depth {d:.3}: the drawing brightens {d:.3} with the slope (the picture {d:.3})\n", .{ dp, got, target });
                if (absDiff(got, target) < bd) {
                    bd = absDiff(got, target);
                    best_d = dp;
                }
            }
            colour = add(&g, mk(K_SHADE, &.{ 1, lx, ly, 0.8, best_d, 0.8 }, &.{colour}));
            note("light: from {d:.2}, {d:.2} (across, down; up 0.8), depth {d:.3}\n", .{ lx, ly, best_d });
            rungs.append(alloc, .{ .root = colour, .label = "+ light (Shade)" }) catch unreachable;
        } else note("light: none read (the sides differ by {d:.3})\n", .{len});
    } else note("light: none read\n", .{});

    // 7. close up (milestone 2c): what the eye misses at 1:1, each layer by its own reading of the full-size picture
    if (opt.close and opt.full != null) {
        const fimg0 = P.readPpm(opt.full.?);
        var cx = CL.Ctx{ .g = &g, .rd = &rd, .st = st, .nb = nb, .root = colour, .main_ramp = main_ramp, .face_layer = face_layer, .second = second_mask != null, .second_layer = second_layer, .motif = opt.seeds != null, .rungs = &rungs, .off = opt.off, .on = opt.on, .marks_soft = opt.marks_soft, .grain_cap = opt.grain_cap, .full = fimg0.rgb, .N = fimg0.w, .grain_in_field = opt.grain_in_field };
        colour = CL.run(&cx);
    } else if (!opt.close) note("close up: left out (close=0: milestone 2b's procedure)\n", .{});
    const whole_root = colour;
    // 8. tiles: the whole picture's procedure at each tile's place, and a tile's own correction where it differs
    var ntint: usize = 0;
    var ndiff: usize = 0;
    if (opt.full) |fp| {
        const fimg = P.readPpm(fp);
        const N = fimg.w;
        const T = opt.tile;
        const nt = N / T;
        const ws = @as(f32, @floatFromInt(T)) / @as(f32, @floatFromInt(N));
        note("tiles: {d} by {d} of {d} pixels at full size ({d})\n", .{ nt, nt, T, N });
        var tints: [64][2]f32 = undefined;
        for (0..nt) |r| {
            for (0..nt) |cc| {
                const win = P.Win{ .x = @as(f32, @floatFromInt(cc)) * ws, .y = @as(f32, @floatFromInt(r)) * ws, .s = ws };
                var dw = drawWin(&g, whole_root, T, win);
                defer dw.free();
                var mp = [3]f64{ 0, 0, 0 };
                var md = [3]f64{ 0, 0, 0 };
                var sp: f64 = 0;
                var sd: f64 = 0;
                for (0..T) |y| {
                    for (0..T) |x| {
                        const fi = 3 * ((r * T + y) * N + cc * T + x);
                        const di = 3 * (y * T + x);
                        if (opt.seeds != null and !motif) {
                            // a motif that stays with the image: the tile's colour is measured on its ground only
                            var dg: f32 = 0;
                            var dk: f32 = 0;
                            inline for (0..3) |q| {
                                dg += (fimg.rgb[fi + q] - ground_c[q]) * (fimg.rgb[fi + q] - ground_c[q]);
                                dk += (fimg.rgb[fi + q] - ink_c[q]) * (fimg.rgb[fi + q] - ink_c[q]);
                            }
                            if (4.0 * dg > dk) continue;
                        }
                        var a = [3]f64{ 0, 0, 0 };
                        var b = [3]f64{ 0, 0, 0 };
                        inline for (0..3) |q| {
                            a[q] = fimg.rgb[fi + q];
                            b[q] = dw.rgb[di + q];
                            mp[q] += a[q];
                            md[q] += b[q];
                        }
                        const ma = (a[0] + a[1] + a[2]) / 3.0;
                        const mb = (b[0] + b[1] + b[2]) / 3.0;
                        sp += @abs(a[0] - ma) + @abs(a[1] - ma) + @abs(a[2] - ma);
                        sd += @abs(b[0] - mb) + @abs(b[1] - mb) + @abs(b[2] - mb);
                    }
                }
                const lp = (mp[0] + mp[1] + mp[2]);
                const ld = (md[0] + md[1] + md[2]);
                const gb: f32 = @floatCast(lp / @max(1e-6, ld) - 1.0);
                const gs: f32 = @floatCast((sp / @max(1e-6, lp)) / @max(1e-6, sd / @max(1e-6, ld)) - 1.0);
                tints[r * nt + cc] = .{ gb, gs };
            }
        }
        for (0..nt) |r| {
            for (0..nt) |cc| {
                const tv = tints[r * nt + cc];
                if (@abs(tv[0]) >= 0.03 or @abs(tv[1]) >= 0.08) {
                    colour = add(&g, mk(K_TINT, &.{ 1, @as(f32, @floatFromInt(cc)) * ws, @as(f32, @floatFromInt(r)) * ws, ws, std.math.clamp(tv[0], -0.9, 4), std.math.clamp(tv[1], -1, 4) }, &.{colour}));
                    ntint += 1;
                    note("  tile {d},{d}: brightness {d:.3}, saturation {d:.3}: Tint\n", .{ r, cc, tv[0], tv[1] });
                } else note("  tile {d},{d}: brightness {d:.3}, saturation {d:.3}: the whole's procedure as it is\n", .{ r, cc, tv[0], tv[1] });
            }
        }
        note("tiles: {d} of {d} take a Tint of their own\n", .{ ntint, nt * nt });
        if (ntint > 0) rungs.append(alloc, .{ .root = colour, .label = "+ the tiles' own Tints" }) catch unreachable;
        _ = &ndiff;
    }
    g.root = colour;
    // the rungs, each a thinner version of the final procedure (its operators up to there)
    var buf: [1 << 16]u8 = undefined;
    var name: [1024]u8 = undefined;
    for (rungs.items, 0..) |rg, k| {
        var c = g;
        c.root = rg.root;
        c.prune();
        P.writeFile(std.fmt.bufPrint(&name, "{s}.r{d:0>2}.script", .{ prefix, k }) catch unreachable, P.scriptText(&c, &buf));
        note("rung {d}: {s}: {d} operators, {d} bytes\n", .{ k, rg.label, c.n, c.bytes() });
    }
    var fin = g;
    fin.prune();
    P.writeFile(std.fmt.bufPrint(&name, "{s}.script", .{prefix}) catch unreachable, P.scriptText(&fin, &buf));
    var wg = g;
    wg.root = whole_root;
    wg.prune();
    P.writeFile(std.fmt.bufPrint(&name, "{s}.whole.script", .{prefix}) catch unreachable, P.scriptText(&wg, &buf));
    note("done: the whole picture's procedure {d} operators, {d} bytes; with the tiles' Tints {d} operators, {d} bytes; {d:.1} s\n", .{ wg.n, wg.bytes(), fin.n, fin.bytes(), P.seconds() - t0 });
    P.writeFile(std.fmt.bufPrint(&name, "{s}.log", .{prefix}) catch unreachable, logbuf.items);
}

/// How soft the dark marks' edges are and how far they stand out (milestone 2d; Daniel on the rusted metal: "more
/// blur and blend on the more disperse darker areas"): the darkest fifth's border pixels' mean slope over the
/// darkest fifth's difference from the rest (a sharp edge is steep for its contrast, a blurred one gentle), and that
/// difference over the rest's spread.
pub fn markEdge(t: []const f32, n: usize) [2]f32 {
    const q = R.quantile(t, 0.2);
    var md: f64 = 0;
    var nd: f64 = 0;
    var mr: f64 = 0;
    var nr: f64 = 0;
    var vr: f64 = 0;
    for (t) |v| {
        if (v < q) {
            md += v;
            nd += 1;
        } else {
            mr += v;
            vr += v * v;
            nr += 1;
        }
    }
    if (nd == 0 or nr == 0) return .{ 0, 0 };
    md /= nd;
    mr /= nr;
    const sr = @sqrt(@max(1e-12, vr / nr - mr * mr));
    var ge: f64 = 0;
    var ne: f64 = 0;
    for (1..n - 1) |y| {
        for (1..n - 1) |x| {
            const i = y * n + x;
            const a = t[i] < q;
            if (a == (t[i + 1] < q) and a == (t[i + n] < q)) continue;
            ge += 0.5 * (@abs(t[i + 1] - t[i - 1]) + @abs(t[i + n] - t[i - n]));
            ne += 1;
        }
    }
    const c = @abs(mr - md);
    if (ne == 0 or c < 1e-6) return .{ 0, 0 };
    return .{ @floatCast(ge / ne / c), @floatCast(c / sr) };
}

/// a structure drawn at full size as a map of its parts (inserts 0, joints 0.3, faces 0.7), correlated with the
/// picture's grey, no shift (milestone 2d: framed tiles at 1:1)
fn partsFull(g: *P.Graph, nd: P.Node, N: usize, t: []const f32, jv: f64) f32 {
    const keep = g.n;
    const ix = add(g, nd);
    var dr = drawNode(g, ix, N);
    g.n = keep;
    defer dr.free();
    var sa: f64 = 0;
    var sb: f64 = 0;
    var saa: f64 = 0;
    var sbb: f64 = 0;
    var sab: f64 = 0;
    for (0..N * N) |i| {
        const a: f64 = if (dr.grey[i] > 0.93) 0 else if (dr.h[i] < 0.15) jv else 0.7;
        const b: f64 = t[i];
        sa += a;
        sb += b;
        saa += a * a;
        sbb += b * b;
        sab += a * b;
    }
    const k: f64 = @floatFromInt(N * N);
    const cov = sab / k - (sa / k) * (sb / k);
    const va = saa / k - (sa / k) * (sa / k);
    const vb = sbb / k - (sb / k) * (sb / k);
    return @floatCast(cov / (@sqrt(va * vb) + 1e-12));
}

/// a structure laid as a map of its parts (inserts 0, joints 0.3, faces 0.7) over the picture's mean cell, signed:
/// how the inserts layout and the framed tiles are compared (milestone 2d)
fn partsAgree(g: *P.Graph, pic: *const Pic, rd: *const P.Reading, pc: []const f32, cw: usize, ch: usize, nd: P.Node) R.Align {
    const n = pic.n;
    const keep = g.n;
    const ix = add(g, nd);
    var dr = drawNode(g, ix, n);
    g.n = keep;
    defer dr.free();
    const map = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(map);
    for (0..n * n) |i| map[i] = if (dr.grey[i] > 0.93) 0 else if (dr.h[i] < 0.15) 0.3 else 0.7;
    var dcw: usize = 0;
    var dch: usize = 0;
    const dc = R.meanCell(map, n, rd.nx, rd.ny, &dcw, &dch);
    defer alloc.free(dc);
    return R.alignCells(pc, dc, cw, ch, true);
}

/// lozenges (a checker or pairs) over the picture's cell of nx by ny, by grey or by height, either sign: the closer
fn lozAgree(g: *P.Graph, n: usize, pc: []const f32, nx: usize, ny: usize, cw: usize, ch: usize, nd: P.Node) R.Align {
    const keep = g.n;
    const ix = add(g, nd);
    var dr = drawNode(g, ix, n);
    g.n = keep;
    defer dr.free();
    var dcw: usize = 0;
    var dch: usize = 0;
    const dg = R.meanCell(dr.grey, n, nx, ny, &dcw, &dch);
    defer alloc.free(dg);
    const dh = R.meanCell(dr.h, n, nx, ny, &dcw, &dch);
    defer alloc.free(dh);
    const a = R.alignCells(pc, dg, cw, ch, false);
    const b = R.alignCells(pc, dh, cw, ch, false);
    return if (@abs(b.corr) > @abs(a.corr)) b else a;
}

const PD = 48; // the profile's reach each way from a joint's centre line, in pixels at full size

/// The picture across its joints at full size (milestone 2d): every pixel's distance to the nearest joint line of the
/// structure as its words place it (signed: below a horizontal line or right of an upright one is positive), the
/// grey and the colour summed per pixel of distance, horizontal and upright joints apart; pixels near a crossing (a
/// quarter of a piece) are left out. The bond's rows move as Tiles moves them.
const Prof = struct {
    hs: [2 * PD + 1]f64 = [_]f64{0} ** (2 * PD + 1),
    hn: [2 * PD + 1]f64 = [_]f64{0} ** (2 * PD + 1),
    vs: [2 * PD + 1]f64 = [_]f64{0} ** (2 * PD + 1),
    vn: [2 * PD + 1]f64 = [_]f64{0} ** (2 * PD + 1),
    fn h(p: *const Prof, k: i32) f64 {
        const i: usize = @intCast(k + PD);
        return if (p.hn[i] > 0) p.hs[i] / p.hn[i] else 0;
    }
    fn v(p: *const Prof, k: i32) f64 {
        const i: usize = @intCast(k + PD);
        return if (p.vn[i] > 0) p.vs[i] / p.vn[i] else 0;
    }
};

const JGeom = struct { layout: u32, nx: f32, ny: f32, bond: f32, phx: f32, phy: f32 };

/// the signed distance in pixels to the nearest joint line, and whether that line is horizontal; null near a crossing
fn jointAt(gm: JGeom, N: usize, i: usize, j: usize) ?struct { s: f32, horiz: bool } {
    const Nf: f32 = @floatFromInt(N);
    const u = (@as(f32, @floatFromInt(i)) + 0.5) / Nf;
    const v = (@as(f32, @floatFromInt(j)) + 0.5) / Nf;
    const X = u * gm.nx - gm.phx;
    const Y = v * gm.ny - gm.phy;
    const row = @floor(Y);
    const Xs = if (gm.layout == 1) X - gm.bond * row else X;
    const fx = Xs - @floor(Xs);
    const fy = Y - row;
    const cwp = Nf / gm.nx;
    const chp = Nf / gm.ny;
    const dl = fx * cwp;
    const dr = (1 - fx) * cwp;
    const dt = fy * chp;
    const db = (1 - fy) * chp;
    const dh = @min(dt, db);
    const dv = @min(dl, dr);
    if (dh <= dv) {
        if (dv < 0.25 * cwp) return null;
        return .{ .s = if (dt < db) dt else -db, .horiz = true };
    }
    if (dh < 0.25 * chp) return null;
    return .{ .s = if (dl < dr) dl else -dr, .horiz = false };
}

fn profileOf(t: []const f32, rgb: ?[]const f32, N: usize, gm: JGeom, prof: *Prof, centre: [2]f32, half: f32, jcol: *[4]f64) void {
    for (0..N) |j| {
        for (0..N) |i| {
            const ja = jointAt(gm, N, i, j) orelse continue;
            const k: i32 = @intFromFloat(@round(ja.s));
            if (k < -PD or k > PD) continue;
            const ix: usize = @intCast(k + PD);
            const val: f64 = t[j * N + i];
            if (ja.horiz) {
                prof.hs[ix] += val;
                prof.hn[ix] += 1;
            } else {
                prof.vs[ix] += val;
                prof.vn[ix] += 1;
            }
            if (rgb) |c| {
                const off = if (ja.horiz) centre[0] else centre[1];
                if (@abs(ja.s - off) <= half) {
                    inline for (0..3) |q| jcol[q] += c[3 * (j * N + i) + q];
                    jcol[3] += 1;
                }
            }
        }
    }
}

/// one side's joint in a profile: its centre (the middle at half depth), its width at half depth and at a quarter
const JRead = struct { centre: f32 = 0, w50: f32 = 0, w10: f32 = 0, depth: f32 = 0, face: f32 = 0, ok: bool = false };
fn readJoint(p: *const Prof, horiz: bool, reach: i32) JRead {
    var o = JRead{};
    const get = if (horiz) &Prof.h else &Prof.v;
    var f: f64 = 0;
    var fk: f64 = 0;
    var k: i32 = -reach;
    while (k <= reach) : (k += 1) {
        if (@as(i32, @intCast(@abs(k))) * 2 < reach) continue;
        f += get(p, k);
        fk += 1;
    }
    if (fk == 0) return o;
    f /= fk;
    // the extremum within half the reach
    var ext: f64 = 0;
    var ek: i32 = 0;
    k = -@divFloor(reach, 2);
    while (k <= @divFloor(reach, 2)) : (k += 1) {
        const d = get(p, k) - f;
        if (@abs(d) > @abs(ext)) {
            ext = d;
            ek = k;
        }
    }
    // the faces' spread: the profile's own wobble far from the joint
    var sd: f64 = 0;
    k = -reach;
    while (k <= reach) : (k += 1) {
        if (@as(i32, @intCast(@abs(k))) * 2 < reach) continue;
        sd += (get(p, k) - f) * (get(p, k) - f);
    }
    sd = @sqrt(sd / fk);
    o.face = @floatCast(f);
    o.depth = @floatCast(ext);
    if (@abs(ext) < 0.02 or @abs(ext) < 3 * sd) return o;
    // the crossings at half and at a tenth of the depth, each side of the extremum, interpolated
    var w: [2]f32 = undefined;
    for ([_]f64{ 0.5, 0.25 }, 0..) |lev, li| {
        var lo: f32 = @floatFromInt(ek);
        var hi: f32 = @floatFromInt(ek);
        var a = ek;
        while (a > -reach and (get(p, a - 1) - f) / ext >= lev) : (a -= 1) {}
        if (a > -reach) {
            const y0 = (get(p, a) - f) / ext;
            const y1 = (get(p, a - 1) - f) / ext;
            lo = @as(f32, @floatFromInt(a)) - @as(f32, @floatCast((y0 - lev) / @max(1e-9, y0 - y1)));
        } else lo = @floatFromInt(-reach);
        var b = ek;
        while (b < reach and (get(p, b + 1) - f) / ext >= lev) : (b += 1) {}
        if (b < reach) {
            const y0 = (get(p, b) - f) / ext;
            const y1 = (get(p, b + 1) - f) / ext;
            hi = @as(f32, @floatFromInt(b)) + @as(f32, @floatCast((y0 - lev) / @max(1e-9, y0 - y1)));
        } else hi = @floatFromInt(reach);
        w[li] = hi - lo;
        if (li == 0) o.centre = 0.5 * (lo + hi);
    }
    o.w50 = w[0];
    o.w10 = w[1];
    o.ok = true;
    return o;
}

/// The joints read again at 1:1 (milestone 2d; Daniel on the floor tiles: "the tile joints are gigantic, on the
/// original they are very thin lines"; on the bricks: "too much mortar ... mortar usually has a "u" shape to it in
/// a depression"). The scan at 512 cannot see a joint of two pixels at 2048; here the picture's grey across its
/// joints at full size gives the joints' place (the phase corrected by the profile's centre), their width at half
/// depth, the bevel (from half depth to a tenth), the joints' own colour, and the joint's profile inside: where the
/// joint's sides are darker than its middle on the side under a piece, a hollow lit from above, chosen among
/// hollows drawn with a light by the drawn profile that agrees best with the picture's.
fn jointsAtFull(g: *P.Graph, st: *Struct, path: [*:0]const u8, try_framed: bool, ask_framed: bool) void {
    // the drawings at full size are large: the memory of drawn pictures is emptied when this reading ends
    defer P.cacheClear();
    var layout = st.layout;
    if (!(layout <= 2 or layout == 8 or layout == 10)) {
        note("joints at 1:1: not read for this layout (its joints are not straight lines between pieces)\n", .{});
        return;
    }
    const img = P.readPpm(path);
    const N = img.w;
    const t = alloc.alloc(f32, N * N) catch unreachable;
    defer alloc.free(t);
    for (0..N * N) |i| t[i] = (img.rgb[3 * i] + img.rgb[3 * i + 1] + img.rgb[3 * i + 2]) / 3.0;
    const ti = st.tiles;
    var gm = JGeom{ .layout = layout, .nx = tw(g, ti, 2), .ny = tw(g, ti, 3), .bond = tw(g, ti, 4), .phx = tw(g, ti, 15), .phy = tw(g, ti, 16) };
    const Nf: f32 = @floatFromInt(N);
    const mpx = @min(Nf / gm.nx, Nf / gm.ny);
    const reach: i32 = @intFromFloat(@min(@as(f32, PD), 0.35 * mpx));
    var pr = Prof{};
    var jc0 = [4]f64{ 0, 0, 0, 0 };
    profileOf(t, null, N, gm, &pr, .{ 0, 0 }, 0, &jc0);
    const hj = readJoint(&pr, true, reach);
    const vj = readJoint(&pr, false, reach);
    if (!hj.ok and !vj.ok) {
        note("joints at 1:1: no joint stands out of the faces across the drawn joint lines (depth {d:.3} and {d:.3}); the scan's width kept\n", .{ hj.depth, vj.depth });
        return;
    }
    // the place: the profile's centre moves the joints (in pieces)
    if (hj.ok) gm.phy += hj.centre / (Nf / gm.ny);
    if (vj.ok) gm.phx += vj.centre / (Nf / gm.nx);
    const nw: f32 = (if (hj.ok) @as(f32, 1) else 0) + (if (vj.ok) @as(f32, 1) else 0);
    const w50 = ((if (hj.ok) hj.w50 else 0) + (if (vj.ok) vj.w50 else 0)) / nw;
    const w10 = ((if (hj.ok) hj.w10 else 0) + (if (vj.ok) vj.w10 else 0)) / nw;
    const joint = std.math.clamp(w50 / mpx, 0.002, 0.5);
    // the bevel: from half depth to a quarter, never wider than half the joint (a shadow or a stain beside the joint
    // reaches further than the pieces' rounded edge)
    const bevel = std.math.clamp(@min(0.5 * (w10 - w50), 0.5 * w50) / mpx, 0.002, 0.5);
    note("joints at 1:1: {d:.1} pixels wide at half depth, {d:.1} at a quarter (horizontal {d:.1}, upright {d:.1}; centres moved {d:.1} and {d:.1} pixels); the joint {d:.4} of a piece, the bevel {d:.4} (the scan at 512 read {d:.4} and {d:.4})\n", .{ w50, w10, hj.w50, vj.w50, hj.centre, vj.centre, joint, bevel, tw(g, ti, 5), tw(g, ti, 6) });
    // the joints' own colour, in their core at full size
    var pr2 = Prof{};
    var jc = [4]f64{ 0, 0, 0, 0 };
    profileOf(t, img.rgb, N, gm, &pr2, .{ 0, 0 }, @max(0.5, 0.25 * w50), &jc);
    if (jc[3] > 50) {
        st.jc = .{ @floatCast(jc[0] / jc[3]), @floatCast(jc[1] / jc[3]), @floatCast(jc[2] / jc[3]) };
        note("joints at 1:1: their colour {x:0>6} (the picture's mean in their core, {d:.0} pixels)\n", .{ @as(u32, @intFromFloat(colourWord(st.jc.?))) & 0xffffff, jc[3] });
    }
    // the hollow: inside the horizontal joints, the picture's profile against hollows drawn with a light from above
    // and from below; a hollow only where it agrees 0.05 better than the flat joint
    var x3 = V3{};
    if (layout <= 2 and hj.ok and w50 >= 6) {
        const half: i32 = @intFromFloat(@ceil(0.5 * w10));
        var best_c: f32 = -2;
        var flat_c: f32 = -2;
        var best_h: f32 = 0;
        var best_ly: f32 = -0.6;
        for ([_]f32{ -0.6, 0.6 }) |ly| {
            for ([_]f32{ 0, 0.25, 0.5, 0.75, 1.0 }) |hv| {
                const keep = g.n;
                const tn = add(g, tilesNodeV(layout, @intFromFloat(gm.nx), @intFromFloat(gm.ny), gm.bond, joint, bevel, tw(g, ti, 7), 0, tw(g, ti, 14), gm.phx, gm.phy, .{ .hollow = hv }));
                const flat = add(g, mk(K_RAMP, &.{ 1, 2, 0, 0xff808080, 1, 0xff808080, 1, 0xff808080, 1, 0xff808080, 1, 0xff808080, 1, 0xff808080, 1, 0xff808080, 1, 0xff808080 }, &.{tn}));
                const sh = add(g, mk(K_SHADE, &.{ 1, 0, ly, 0.8, 0.004, 0.8 }, &.{flat}));
                var dd = drawNode(g, sh, N);
                g.n = keep;
                var dp = Prof{};
                var dummy = [4]f64{ 0, 0, 0, 0 };
                profileOf(dd.grey, null, N, gm, &dp, .{ 0, 0 }, 0, &dummy);
                dd.free();
                // the shapes inside the joint, each less its mean, correlated
                var ma: f64 = 0;
                var mb: f64 = 0;
                var cnt: f64 = 0;
                var k: i32 = -half;
                while (k <= half) : (k += 1) {
                    ma += pr.h(k);
                    mb += dp.h(k);
                    cnt += 1;
                }
                ma /= cnt;
                mb /= cnt;
                var sab: f64 = 0;
                var saa: f64 = 0;
                var sbb: f64 = 0;
                k = -half;
                while (k <= half) : (k += 1) {
                    sab += (pr.h(k) - ma) * (dp.h(k) - mb);
                    saa += (pr.h(k) - ma) * (pr.h(k) - ma);
                    sbb += (dp.h(k) - mb) * (dp.h(k) - mb);
                }
                const cr: f32 = @floatCast(sab / (@sqrt(saa * sbb) + 1e-12));
                note("  hollow {d:.2}, light at 0, {d:.1}: the joint's profile agrees {d:.3} with the picture's\n", .{ hv, ly, cr });
                if (hv == 0 and cr > flat_c) flat_c = cr;
                if (cr > best_c) {
                    best_c = cr;
                    best_h = hv;
                    best_ly = ly;
                }
            }
        }
        if (best_h > 0 and best_c >= flat_c + 0.05) {
            x3.hollow = best_h;
            note("joints at 1:1: a hollow {d:.2} (a u in a depression; with a light at 0, {d:.1} it agrees {d:.3}, flat {d:.3}; the light itself is read later on the whole relief)\n", .{ best_h, best_ly, best_c, flat_c });
        } else note("joints at 1:1: flat (no hollow agrees 0.05 better than the flat joint: {d:.3} against {d:.3})\n", .{ best_c, flat_c });
    } else if (layout <= 2) note("joints at 1:1: the hollow not read (joints under 6 pixels at full size, or no horizontal joint)\n", .{});
    // the structure again with the joints read at 1:1 (version 3 where a hollow or a layout of version 3 needs it)
    const old = g.nodes[ti];
    const isv3 = old.w[0] >= 3;
    var x = x3;
    if (isv3) {
        x.sox = tw(g, ti, 25);
        x.soy = tw(g, ti, 26);
        x.inner = tw(g, ti, 27);
    }
    // framed tiles at 1:1: at 512 their inner joints are under a pixel, so the inserts layout and framed tiles are
    // compared again here, at full size, as maps of their parts over the picture's grey, in the place now read
    if (layout == 8 and try_framed) {
        const sz8 = std.math.clamp(tw(g, ti, 14) - (tw(g, ti, 5) - joint), 0.05, 1.5);
        const nxi: i32 = @intFromFloat(gm.nx);
        const nyi: i32 = @intFromFloat(gm.ny);
        // the joints in the map as the profile read them: darker or lighter than the faces
        const jd = if (vj.ok) vj.depth else hj.depth;
        const jv: f64 = if (jd > 0) 1.0 else 0.4;
        const ref = partsFull(g, tilesNodeV(8, nxi, nyi, gm.bond, joint, bevel, @min(tw(g, ti, 7), 2 * joint), 0, sz8, gm.phx, gm.phy, .{}), N, t, jv);
        note("framed tiles at 1:1: the inserts layout as a map of its parts agrees {d:.4} with the picture\n", .{ref});
        note("framed tiles at 1:1: the joints {s} than the faces in the map ({s})\n", .{ if (jd > 0) "lighter" else "darker", if (ask_framed) "framed asked for by eye: on=framed" else "framed chosen only where it agrees better" });
        var bc = if (ask_framed) @as(f32, -2) else ref + 0.005;
        var bi: f32 = 0;
        for ([_]f32{ 0.2, 0.25, 0.3, 0.33, 0.36, 0.4, 0.45, 0.5 }) |inner| {
            const c = partsFull(g, tilesNodeV(10, nxi, nyi, gm.bond, joint, bevel, @min(tw(g, ti, 7), 2 * joint), 0, sz8, gm.phx, gm.phy, .{ .inner = inner }), N, t, jv);
            note("  framed, a central square {d:.2} of the tile: {d:.4}\n", .{ inner, c });
            if (c > bc) {
                bc = c;
                bi = inner;
            }
        }
        if (bi > 0) {
            layout = 10;
            st.layout = 10;
            x.inner = bi;
            if (ask_framed) note("framed tiles at 1:1: asked for by eye (Daniel: \"one tiny centralized square with surrounding trapezoids\"); the central square's size read\n", .{});
            note("framed tiles at 1:1: chosen, a central square {d:.2} of the tile and four trapezoids around it (they agree {d:.4}, the inserts layout {d:.4})\n", .{ bi, bc, ref });
        } else note("framed tiles at 1:1: not chosen (none agrees 0.005 better than the inserts layout)\n", .{});
    }
    // inserts keep the side the scan read (their visible half side is half the size less half the joint), and a
    // corner is rounded no more than twice the joint is wide (a thin joint between square slabs meets square)
    var size = tw(g, ti, 14);
    if (layout == 8 or layout == 10) {
        size = std.math.clamp(size - (tw(g, ti, 5) - joint), 0.05, 1.5);
        note("joints at 1:1: the inserts {d:.3} of a piece across (their visible side kept as the scan read it)\n", .{size});
    }
    const round = @min(tw(g, ti, 7), 2 * joint);
    if (round < tw(g, ti, 7)) note("joints at 1:1: the corners rounded {d:.4} of a piece (no more than twice the joint)\n", .{round});
    g.nodes[ti] = tilesNodeV(layout, @intFromFloat(gm.nx), @intFromFloat(gm.ny), gm.bond, joint, bevel, round, tw(g, ti, 9), size, gm.phx, gm.phy, x);
}

/// the share of the faces' variation that lies between pieces: the variance of the means of the pieces (pieces told
/// apart by the drawn structure's own face value) over the variance of the faces
pub fn betweenShare(v: []const f32, ids: []const f32, face: []const bool, n: usize) f32 {
    const NB = 64;
    var s = [_]f64{0} ** NB;
    var c = [_]f64{0} ** NB;
    var tot: f64 = 0;
    var tot2: f64 = 0;
    var k: f64 = 0;
    for (0..n * n) |i| {
        if (!face[i]) continue;
        const b: usize = @intFromFloat(@min(@as(f32, NB - 1), ids[i] * NB));
        s[b] += v[i];
        c[b] += 1;
        tot += v[i];
        tot2 += v[i] * v[i];
        k += 1;
    }
    if (k < 2) return 0;
    const mean = tot / k;
    const vt = tot2 / k - mean * mean;
    var vb: f64 = 0;
    for (0..NB) |b| {
        if (c[b] == 0) continue;
        const m = s[b] / c[b];
        vb += c[b] * (m - mean) * (m - mean);
    }
    vb /= k;
    return @floatCast(vb / @max(1e-12, vt));
}

/// the off-axis mask: how far each pixel's colour lies from the line between the picture's two colours, toward the
/// second material's colour; sel marks the pixels milestone 1's reading counts (further than 0.10)
pub fn offMask(pic: *const Pic, rd: *const P.Reading, mask: []f32, sel: []bool) void {
    const c0 = rgbOfWord(rd.c0);
    const c1 = rgbOfWord(rd.c1);
    var ax = [3]f32{ c1[0] - c0[0], c1[1] - c0[1], c1[2] - c0[2] };
    const al = @sqrt(ax[0] * ax[0] + ax[1] * ax[1] + ax[2] * ax[2]) + 1e-6;
    inline for (0..3) |q| ax[q] /= al;
    for (0..pic.n * pic.n) |i| {
        var d = [3]f32{ pic.rgb[3 * i] - c0[0], pic.rgb[3 * i + 1] - c0[1], pic.rgb[3 * i + 2] - c0[2] };
        const p = d[0] * ax[0] + d[1] * ax[1] + d[2] * ax[2];
        inline for (0..3) |q| d[q] -= p * ax[q];
        const dist = @sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
        mask[i] = @min(1.0, dist / 0.2);
        sel[i] = dist > 0.10;
    }
}

pub const LitSrc = enum { slopes, stones, pits };

/// the same light reading on a drawing as was made on the picture: slopes of the drawn relief, or the sides of blobs
pub fn litReading(src: LitSrc, grey: []const f32, h: []const f32, n: usize) [2]f32 {
    switch (src) {
        .slopes => {
            const r = slopeLight(grey, h, n);
            return .{ r[0], r[1] };
        },
        .stones => {
            const b = R.blobs(grey, n, 16, 1.4, false, 4000);
            return .{ b.left_light, b.up_light };
        },
        .pits => {
            const b = R.blobs(grey, n, 6, 2.5, true, 300);
            return .{ -b.left_light, -b.up_light };
        },
    }
}

/// regress the picture's values on the drawn relief's slopes (where the relief slopes): how much brighter it is where
/// the relief rises across and down; and the share of the variation the slopes explain
pub fn slopeLight(t: []const f32, h: []const f32, n: usize) [3]f32 {
    var sxx: f64 = 0;
    var syy: f64 = 0;
    var sxy: f64 = 0;
    var sxt: f64 = 0;
    var syt: f64 = 0;
    var st: f64 = 0;
    var stt: f64 = 0;
    var k: f64 = 0;
    for (0..n) |y| {
        for (0..n) |x| {
            const gx: f64 = h[y * n + (x + 1) % n] - h[y * n + (x + n - 1) % n];
            const gy: f64 = h[((y + 1) % n) * n + x] - h[((y + n - 1) % n) * n + x];
            if (@abs(gx) + @abs(gy) < 0.02) continue;
            const v: f64 = t[y * n + x];
            sxx += gx * gx;
            syy += gy * gy;
            sxy += gx * gy;
            sxt += gx * v;
            syt += gy * v;
            st += v;
            stt += v * v;
            k += 1;
        }
    }
    if (k < 100) return .{ 0, 0, 0 };
    const mt = st / k;
    const det = sxx * syy - sxy * sxy;
    if (@abs(det) < 1e-12) return .{ 0, 0, 0 };
    // centred: the slopes have mean about zero over a repeating relief
    const a = (syy * (sxt - mt * 0) - sxy * syt) / det;
    const b = (sxx * syt - sxy * sxt) / det;
    const explained = a * sxt + b * syt - 0;
    const vt = stt - k * mt * mt;
    return .{ @floatCast(a), @floatCast(b), @floatCast(@max(0, explained - 0) / @max(1e-12, vt)) };
}

/// pits, specks or stones: a soft disc scattered at the blobs' density and size, in the picture's colour at a rank
fn addScatter(g: *P.Graph, pic: *const Pic, base: usize, b: R.Blobs, height: f32, n: usize, rank: f32) usize {
    return addScatterSel(g, pic, base, b, height, n, rank, null);
}

/// the same, its colour at the rank among the selected pixels only (a structure's faces: not its joints or inserts)
fn addScatterSel(g: *P.Graph, pic: *const Pic, base: usize, b: R.Blobs, height: f32, n: usize, rank: f32, sel: ?[]const bool) usize {
    // half the cells hold one: cells = sqrt(count / 0.5) across, over the picture
    const cells: i32 = @max(2, @as(i32, @intFromFloat(@sqrt(@as(f32, @floatFromInt(b.count)) / 0.5))));
    const cellpx = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(cells));
    const size = @min(0.45, @max(0.01, b.radius / cellpx));
    const col = if (sel) |sl| colourAtRankSel(pic, rank, sl) else colourAtRank(pic, rank);
    const asp = @min(4.0, @max(0.5, b.down));
    return add(g, mk(K_SCATTER, &.{ 1, @floatFromInt(cells), @floatFromInt(cells), 0.5, size, 0.4, 0.5, 0.8, colourWord(col), 0.25, 11, height, 0.5, asp, 0.9, 0, 0 }, &.{base}));
}
