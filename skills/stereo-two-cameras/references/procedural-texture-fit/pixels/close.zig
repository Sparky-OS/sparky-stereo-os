//! The close-up layers (milestone 2c): what the eye misses at 1:1 becomes layers, each entering only through its own
//! reading of the pixels at full size, each a rung of the ladder that starts from milestone 2b's whole-picture
//! procedure, each said in the log with its numbers and refused with its reason.
//!
//! Two views of the full-size picture are read: C, its central half at 1:1 (the marks a person sees close up: grain,
//! chipped edges, mortar, pits, the run of furrows); and H, the whole picture at half size (marks that are few or
//! large: spots and how they gather, stones, knots). A drawing is read by the same functions in the same window, so a
//! value that no reading gives directly is chosen so the drawing's reading equals the picture's; nothing is chosen by
//! an inner measure and no model and no text is an input. What the eye refuses is an option (off=NAME,...).
//!
//!   grain    fine detail at 1:1 (the strengths of the two-, four- and eight-pixel bands) the drawing lacks: a fine
//!            Noise laid into the surface's field before its Ramp, or, on a laid structure, each piece's own grain
//!            and stain (Tiles version 2), the Ramp read again;
//!   chips    a structure's joints more ragged in the picture than drawn (edge per pixel of the joints, both blurred
//!            alike): the pieces' edges chipped (Tiles version 2);
//!   mortar   the joints' own variation and light specks in them (Layer version 2 with the joints as a falling mask);
//!   spots    a second material lying in compact spots that gather (Scatter version 2: clustered, rough, a darker
//!            core), their halo (Wear grow) and their runs down (Wear drips), the base ramped on the first material;
//!   furrows  long thin dark pieces at 1:1, mostly one way: Cells version 2 cracks stretched that way, their width
//!            wandering;
//!   knots    few large dark compact pieces in the whole: Scatter version 2 of rough dark ellipses;
//!   stones   light compact pieces in the whole: Scatter version 2 of rough raised discs, lit where their sides are;
//!   pits     dark compact pieces at 1:1: Scatter version 2 of rough sunk discs, lit where their sides are;
//!   patches  a second colour off the main axis lying in large patches that milestone 2b's threshold missed (moss),
//!            or dark smooth patches (wet): a Layer through a ragged noise.
//! Our code, BSD 2-clause like Farbrausch's tree.
const std = @import("std");
const P = @import("p2p.zig");
const R = @import("readings.zig");
const M = @import("modern.zig");
const F = @import("mfit.zig");
const alloc = std.heap.c_allocator;
const note = F.note;

/// a view of the full-size picture: its pixels, the values along its own main colour axis, and the window of the
/// whole picture it shows (a drawing in the same window is read the same way)
pub const View = struct {
    pic: F.Pic,
    mean: [3]f32,
    axis: [3]f32,
    win: P.Win,
};

/// the view of side (N - 2 x0) / step pixels: the picture from (x0, x0), box-averaged step by step
pub fn makeView(full: []const f32, N: usize, x0: usize, side: usize, step: usize, win: P.Win) View {
    const n = side / step;
    const rgb = alloc.alloc(f32, n * n * 3) catch unreachable;
    const k: f32 = @floatFromInt(step * step);
    for (0..n) |y| {
        for (0..n) |x| {
            var s = [3]f32{ 0, 0, 0 };
            for (0..step) |dy| {
                for (0..step) |dx| {
                    const i = 3 * ((x0 + y * step + dy) * N + x0 + x * step + dx);
                    inline for (0..3) |q| s[q] += full[i + q];
                }
            }
            inline for (0..3) |q| rgb[3 * (y * n + x) + q] = s[q] / k;
        }
    }
    // the main colour axis (the same power iteration as milestone 1's reading)
    var mean = [3]f64{ 0, 0, 0 };
    for (0..n * n) |i| {
        inline for (0..3) |q| mean[q] += rgb[3 * i + q];
    }
    inline for (0..3) |q| mean[q] /= @floatFromInt(n * n);
    var cov = [_][3]f64{.{ 0, 0, 0 }} ** 3;
    for (0..n * n) |i| {
        inline for (0..3) |a| {
            inline for (0..3) |b| cov[a][b] += (rgb[3 * i + a] - mean[a]) * (rgb[3 * i + b] - mean[b]);
        }
    }
    var v = [3]f64{ 0.577, 0.577, 0.577 };
    for (0..50) |_| {
        var w = [3]f64{ 0, 0, 0 };
        inline for (0..3) |a| {
            inline for (0..3) |b| w[a] += cov[a][b] * v[b];
        }
        const len = @sqrt(w[0] * w[0] + w[1] * w[1] + w[2] * w[2]);
        if (len <= 0) break;
        inline for (0..3) |a| v[a] = w[a] / len;
    }
    if (v[0] + v[1] + v[2] < 0) {
        inline for (0..3) |a| v[a] = -v[a];
    }
    var out = View{ .pic = undefined, .mean = .{ @floatCast(mean[0]), @floatCast(mean[1]), @floatCast(mean[2]) }, .axis = .{ @floatCast(v[0]), @floatCast(v[1]), @floatCast(v[2]) }, .win = win };
    const t = keyOf(&out, rgb, n);
    out.pic = .{ .n = n, .rgb = rgb, .t = t, .tsort = R.sorted(t) };
    return out;
}

/// colours along the view's own main axis (a drawing's colours too, so the two are compared on one scale)
pub fn keyOf(v: *const View, rgb: []const f32, n: usize) []f32 {
    const t = alloc.alloc(f32, n * n) catch unreachable;
    for (0..n * n) |i| {
        var s: f32 = 0;
        inline for (0..3) |q| s += (rgb[3 * i + q] - v.mean[q]) * v.axis[q];
        t[i] = s;
    }
    return t;
}

fn drawIn(g: *P.Graph, root: usize, v: *const View) F.Drawn {
    return F.drawWin(g, root, v.pic.n, v.win);
}

/// Copies of every node after `old` up to `root` that depends on `old`, with `old` replaced by `new`; map[i] is node
/// i's copy (or i). The copies are added at the end, in order, so every input still lies before its node.
pub fn rewire(g: *P.Graph, root: usize, old: usize, new: usize, map: []usize) usize {
    for (0..root + 1) |i| map[i] = i;
    map[old] = new;
    var i = old + 1;
    while (i <= root) : (i += 1) {
        var nd = g.nodes[i];
        var changed = false;
        for (nd.in[0..nd.nin]) |*x| {
            if (map[x.*] != x.*) {
                x.* = @intCast(map[x.*]);
                changed = true;
            }
        }
        if (changed) map[i] = F.add(g, nd);
    }
    return map[root];
}

pub fn refused(off: []const u8, name: []const u8) bool {
    var it = std.mem.tokenizeScalar(u8, off, ',');
    while (it.next()) |x| {
        if (std.mem.eql(u8, x, name)) return true;
    }
    return false;
}

/// the spread of the detail of band r (the values less their blur of r) over the pixels a mask holds (all: null)
fn bandSd(t: []const f32, n: usize, r: usize, mask: ?[]const bool) f32 {
    const b = R.blur(t, n, r);
    defer alloc.free(b);
    var s: f64 = 0;
    var s2: f64 = 0;
    var k: f64 = 0;
    for (0..n * n) |i| {
        if (mask) |m| {
            if (!m[i]) continue;
        }
        const d: f64 = t[i] - b[i];
        s += d;
        s2 += d * d;
        k += 1;
    }
    if (k < 16) return 0;
    const mn = s / k;
    return @floatCast(@sqrt(@max(0, s2 / k - mn * mn)));
}

/// the spread of the values over a mask
/// a spread that the few lightest or darkest marks do not lead (milestone 2d: the mortar's lime specks are drawn by
/// their own layer, so its colours are matched on the middle half): the interquartile range over 1.349
fn robustSd(t: []const f32, sel: []const bool) f32 {
    var v: std.ArrayList(f32) = .empty;
    defer v.deinit(alloc);
    for (t, sel) |x, s| {
        if (s) v.append(alloc, x) catch unreachable;
    }
    if (v.items.len < 8) return 0;
    std.mem.sort(f32, v.items, {}, std.sort.asc(f32));
    const n = v.items.len;
    return (v.items[(3 * n) / 4] - v.items[n / 4]) / 1.349;
}

fn maskedSd(t: []const f32, mask: []const bool) f32 {
    var s: f64 = 0;
    var s2: f64 = 0;
    var k: f64 = 0;
    for (t, mask) |v, m| {
        if (!m) continue;
        s += v;
        s2 += v * v;
        k += 1;
    }
    if (k < 16) return 0;
    const mn = s / k;
    return @floatCast(@sqrt(@max(0, s2 / k - mn * mn)));
}

fn maskedMean(t: []const f32, mask: []const bool) f32 {
    var s: f64 = 0;
    var k: f64 = 0;
    for (t, mask) |v, m| {
        if (!m) continue;
        s += v;
        k += 1;
    }
    return if (k > 0) @floatCast(s / k) else 0;
}

/// a mask's edge per pixel inside after a blur of r and a threshold at one half (the same on picture and drawing:
/// specks smaller than the blur fall away, so what is counted is the outline of the large shapes)
fn smoothEdge(mask: []const bool, n: usize, r: usize) f32 {
    const f = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(f);
    for (mask, 0..) |m, i| f[i] = if (m) 1 else 0;
    const b = R.blur(f, n, r);
    defer alloc.free(b);
    return R.edgePerArea(b, n, 0.5);
}

const Comp = struct { area: usize, cx: f32, cy: f32, bw: usize, bh: usize };

/// connected pieces of a mask (four neighbours, the picture repeating), by an iterative fill with its own stack
fn components(mask: []const bool, n: usize, out: *std.ArrayList(Comp)) void {
    const m = alloc.alloc(u8, n * n) catch unreachable;
    defer alloc.free(m);
    for (mask, 0..) |x, i| m[i] = if (x) 1 else 0;
    const stack = alloc.alloc(u32, n * n) catch unreachable;
    defer alloc.free(stack);
    for (0..n * n) |s0| {
        if (m[s0] != 1) continue;
        var sp: usize = 0;
        stack[0] = @intCast(s0);
        sp = 1;
        m[s0] = 2;
        var area: usize = 0;
        var x0: usize = n;
        var x1: usize = 0;
        var y0: usize = n;
        var y1: usize = 0;
        var sx: f64 = 0;
        var sy: f64 = 0;
        while (sp > 0) {
            sp -= 1;
            const p = stack[sp];
            const x = p % n;
            const y = p / n;
            area += 1;
            sx += @floatFromInt(x);
            sy += @floatFromInt(y);
            x0 = @min(x0, x);
            x1 = @max(x1, x);
            y0 = @min(y0, y);
            y1 = @max(y1, y);
            const nb = [4]u32{ @intCast(y * n + (x + 1) % n), @intCast(y * n + (x + n - 1) % n), @intCast(((y + 1) % n) * n + x), @intCast(((y + n - 1) % n) * n + x) };
            for (nb) |q| {
                if (m[q] == 1) {
                    m[q] = 2;
                    stack[sp] = q;
                    sp += 1;
                }
            }
        }
        const fa: f64 = @floatFromInt(area);
        out.append(alloc, .{ .area = area, .cx = @floatCast(sx / fa), .cy = @floatCast(sy / fa), .bw = x1 - x0 + 1, .bh = y1 - y0 + 1 }) catch unreachable;
    }
}

/// how unevenly points lie over blocks of the picture: the variance of the counts per block over their mean (1 for
/// points thrown at random, more where they gather)
fn dispersion(pts: []const Comp, n: usize, blocks: usize) f32 {
    var cnt = [_]u32{0} ** 256;
    // typed: @min with a constant 16 would make B a five-bit integer, and B * B would wrap to 0 in a fast build
    const B: usize = @min(blocks, 16);
    for (pts) |p| {
        const xi: usize = @min(n - 1, @as(usize, @intFromFloat(@max(0, p.cx))));
        const yi: usize = @min(n - 1, @as(usize, @intFromFloat(@max(0, p.cy))));
        cnt[(yi * B / n) * B + xi * B / n] += 1;
    }
    var s: f64 = 0;
    var s2: f64 = 0;
    for (cnt[0 .. B * B]) |c| {
        const v: f64 = @floatFromInt(c);
        s += v;
        s2 += v * v;
    }
    const k: f64 = @floatFromInt(B * B);
    const mn = s / k;
    if (mn <= 0) return 0;
    return @floatCast((s2 / k - mn * mn) / mn);
}

/// the compact pieces of a mask: at least min_area pixels, filling 0.35 of their box, at most 3 times as long as wide
fn compact(all: []const Comp, min_area: usize, max_area: usize, out: *std.ArrayList(Comp)) void {
    for (all) |c| {
        if (c.area < min_area or c.area > max_area) continue;
        const fa: f32 = @floatFromInt(c.area);
        const bw: f32 = @floatFromInt(c.bw);
        const bh: f32 = @floatFromInt(c.bh);
        if (fa < 0.35 * bw * bh or @max(bw, bh) > 3 * @min(bw, bh)) continue;
        out.append(alloc, c) catch unreachable;
    }
}

fn meanRadius(cs: []const Comp) f32 {
    if (cs.len == 0) return 0;
    var s: f32 = 0;
    for (cs) |c| s += @sqrt(@as(f32, @floatFromInt(c.area)) / std.math.pi);
    return s / @as(f32, @floatFromInt(cs.len));
}

fn meanDown(cs: []const Comp) f32 {
    if (cs.len == 0) return 1;
    var s: f32 = 0;
    for (cs) |c| s += @as(f32, @floatFromInt(c.bh)) / @as(f32, @floatFromInt(c.bw));
    return s / @as(f32, @floatFromInt(cs.len));
}

/// Compact pieces of the detail (the values less their blur of r) darker (dark) or lighter than k spreads, between
/// min_area and max_area pixels, filling 0.35 of their box and at most 3 times as long as wide; the pixels outside
/// `only` (when given) do not count. Unlike milestone 2b's reading, pieces under min_area are not counted at all, so
/// the mean size is the size of the marks, not of the grain between them.
const Marks = struct { count: usize = 0, radius: f32 = 0, down: f32 = 1, left_light: f32 = 0, up_light: f32 = 0 };
fn marks(t: []const f32, n: usize, r: usize, k: f32, dark: bool, min_area: usize, max_area: usize, only: ?[]const bool) Marks {
    const b = R.blur(t, n, r);
    defer alloc.free(b);
    var sd: f64 = 0;
    var cnt: f64 = 0;
    for (0..n * n) |i| {
        if (only) |o| {
            if (!o[i]) continue;
        }
        sd += (t[i] - b[i]) * (t[i] - b[i]);
        cnt += 1;
    }
    const sdev: f32 = @floatCast(@sqrt(sd / @max(1, cnt)));
    const m = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(m);
    for (0..n * n) |i| {
        const d = t[i] - b[i];
        const in = if (only) |o| o[i] else true;
        m[i] = in and ((dark and d < -k * sdev) or (!dark and d > k * sdev));
    }
    var all: std.ArrayList(Comp) = .empty;
    defer all.deinit(alloc);
    components(m, n, &all);
    var cs: std.ArrayList(Comp) = .empty;
    defer cs.deinit(alloc);
    compact(all.items, min_area, max_area, &cs);
    var out = Marks{ .count = cs.items.len, .radius = meanRadius(cs.items), .down = meanDown(cs.items) };
    // light on the marks' sides: the detail just above against just below, left against right
    var upl: f64 = 0;
    var lfl: f64 = 0;
    for (cs.items) |c| {
        const cxp: usize = @intFromFloat(c.cx);
        const cyp: usize = @intFromFloat(c.cy);
        const rr: usize = @intFromFloat(@max(2.0, @sqrt(@as(f32, @floatFromInt(c.area)) / std.math.pi)));
        const ya = (cyp + n - rr) % n;
        const yb = (cyp + rr) % n;
        const xa = (cxp + n - rr) % n;
        const xb = (cxp + rr) % n;
        upl += (t[ya * n + cxp] - b[ya * n + cxp]) - (t[yb * n + cxp] - b[yb * n + cxp]);
        lfl += (t[cyp * n + xa] - b[cyp * n + xa]) - (t[cyp * n + xb] - b[cyp * n + xb]);
    }
    if (cs.items.len > 0) {
        const fc: f64 = @floatFromInt(cs.items.len);
        out.up_light = @floatCast(upl / fc / (sdev + 1e-9));
        out.left_light = @floatCast(lfl / fc / (sdev + 1e-9));
    }
    return out;
}

/// Runs of a mask along the rows (across) or the columns: how many runs a line holds, and their mean length
fn runs(mask: []const bool, n: usize, across: bool) [2]f32 {
    var nr: f64 = 0;
    var len: f64 = 0;
    for (0..n) |k| {
        var prev = false;
        for (0..n) |m| {
            const v = if (across) mask[k * n + m] else mask[m * n + k];
            if (v) len += 1;
            if (v and !prev) nr += 1;
            prev = v;
        }
    }
    return .{ @floatCast(nr / @as(f64, @floatFromInt(n))), @floatCast(len / @max(1, nr)) };
}

/// a Scatter version 2 node: disc instances (no stamp) over `base`; sizes in parts of a cell, as version 1
fn scatter2(base: usize, cells: i32, dens: f32, size: f32, svar: f32, col: [3]f32, cvar: f32, seed: i32, height: f32, soft: f32, aspect: f32, ccl: i32, clu: f32, rough: f32, rcl: i32, core: f32) P.Node {
    return F.mk(F.K_SCATTER, &.{ 2, @floatFromInt(cells), @floatFromInt(cells), dens, size, svar, 0.5, 0.8, F.colourWord(col), cvar, @floatFromInt(seed), height, soft, aspect, 1, 0, 0, @floatFromInt(ccl), clu, rough, @floatFromInt(rcl), core }, &.{base});
}

fn scatter2o(base: usize, cells: i32, dens: f32, size: f32, svar: f32, col: [3]f32, cvar: f32, seed: i32, height: f32, soft: f32, aspect: f32, ccl: i32, clu: f32, rough: f32, rcl: i32, core: f32, opacity: f32) P.Node {
    return F.mk(F.K_SCATTER, &.{ 2, @floatFromInt(cells), @floatFromInt(cells), dens, size, svar, 0.5, 0.8, F.colourWord(col), cvar, @floatFromInt(seed), height, soft, aspect, opacity, 0, 0, @floatFromInt(ccl), clu, rough, @floatFromInt(rcl), core }, &.{base});
}

/// What the close-up phase starts from and builds on
pub const Ctx = struct {
    g: *P.Graph,
    rd: *const P.Reading,
    st: F.Struct,
    nb: F.Built,
    root: usize, // the colour so far (milestone 2b's whole-picture procedure)
    main_ramp: usize, // the Ramp that colours the surface's field (or a structure's faces)
    face_layer: usize, // a structure's noise laid into its faces (0: none)
    second: bool, // milestone 2b laid a second material
    second_layer: usize, // its Layer (0: none)
    patches: bool = false, // the close-up phase laid a second colour in patches
    grain_in_field: bool = false, // grainat=field: the grain laid into the field before the Ramp
    tiles0: usize = 0, // the structure as milestone 2b drew it
    spots: bool = false, // the close-up phase laid spots
    motif: bool, // a figure on a ground: the marks would be the motif's own edges
    field: usize = 0, // the surface's field as the Ramps read it (the grain layer once it is laid)
    rungs: *std.ArrayList(F.Rung),
    off: []const u8,
    on: []const u8 = "", // milestone 2d: layers the eye asked for below their readings' thresholds (on=spots)
    marks_soft: bool = true, // milestone 2d: the spots' softness and blend read (marks=fixed: milestone 2c's)
    joints_full: bool = false, // milestone 2d: the structure's joints were read again at 1:1
    grain_cap: bool = true, // milestone 2d: a piece's grain may not exceed the picture's faces in any band
    full: []const f32,
    N: usize,
};

/// the close-up phase: every layer by its reading, each a rung; the new colour root
pub fn run(cx: *Ctx) usize {
    const t0 = P.seconds();
    if (cx.field == 0) cx.field = cx.nb.field;
    cx.tiles0 = cx.st.tiles;
    const N = cx.N;
    if (N < 1024) {
        note("close up: the picture is {d} pixels; the close-up readings need 1024 or more, so none is read\n", .{N});
        return cx.root;
    }
    const C = makeView(cx.full, N, N / 4, N / 2, @max(1, N / 2 / 1024), .{ .x = 0.25, .y = 0.25, .s = 0.5 });
    const H = makeView(cx.full, N, 0, N, @max(1, N / 1024), .{});
    note("close up: C, the central half at {d} pixels ({s}), and H, the whole at {d} pixels\n", .{ C.pic.n, if (N / 2 / 1024 == 1) "1:1" else "reduced", H.pic.n });
    if (cx.motif) {
        note("close up: a figure on a ground; the marks are not read (the motif's edges would count)\n", .{});
        grainLayer(cx, &C, &H);
        return cx.root;
    }
    if (cx.st.ok) {
        structLayers(cx, &C, &H);
        mortarLayers(cx, &C);
    } else {
        grainLayer(cx, &C, &H);
    }
    patchesLayer(cx, &H);
    spotsLayer(cx, &C, &H);
    furrowsLayer(cx, &C);
    knotsLayer(cx, &H);
    stonesLayer(cx, &H);
    pitsLayer(cx, &H);
    note("close up: {d:.1} s\n", .{P.seconds() - t0});
    return cx.root;
}

fn push(cx: *Ctx, label: []const u8) void {
    cx.g.root = cx.root;
    cx.rungs.append(alloc, .{ .root = cx.root, .label = label }) catch unreachable;
}

// ---------------------------------------------------------------- grain

/// the strengths of the finest three bands (two, four and eight pixels) of a drawing's colours on the view's axis
fn bands(cx: *Ctx, root: usize, v: *const View) [3]f32 {
    var d = drawIn(cx.g, root, v);
    defer d.free();
    const k = keyOf(v, d.rgb, v.pic.n);
    defer alloc.free(k);
    const o = R.octaves(k, v.pic.n);
    return .{ o[0], o[1], o[2] };
}

fn grainLayer(cx: *Ctx, C: *const View, H: *const View) void {
    if (refused(cx.off, "grain")) {
        note("grain: left off by eye (off=grain)\n", .{});
        return;
    }
    const g = cx.g;
    if (cx.motif) {
        // a figure on a ground: its edges are no grain; the ground alone (the values near the median) is read
        const n = C.pic.n;
        const med = R.quantile(C.pic.t, 0.5);
        const gm = alloc.alloc(bool, n * n) catch unreachable;
        defer alloc.free(gm);
        const dev = alloc.alloc(f32, n * n) catch unreachable;
        defer alloc.free(dev);
        for (0..n * n) |i| dev[i] = @abs(C.pic.t[i] - med);
        const mad = R.quantile(dev, 0.5);
        const tb = R.blur(C.pic.t, n, 4);
        defer alloc.free(tb);
        for (0..n * n) |i| gm[i] = @abs(tb[i] - med) < 3 * mad + 0.02;
        var dd = drawIn(cx.g, cx.root, C);
        const kd = keyOf(C, dd.rgb, n);
        dd.free();
        defer alloc.free(kd);
        const p1 = bandSd(C.pic.t, n, 1, gm);
        const d1 = bandSd(kd, n, 1, gm);
        note("grain: a figure on a ground; the ground's detail at 1:1 is {d:.4}, drawn {d:.4} (grain from 1.4 times)\n", .{ p1, d1 });
        if (p1 < 1.4 * d1 + 0.002) {
            note("grain: none on the ground\n", .{});
            return;
        }
    }
    const op = R.octaves(C.pic.t, C.pic.n);
    const od = bands(cx, cx.root, C);
    const gap0 = op[0] - od[0];
    const gap1 = op[1] - od[1];
    const gap2 = op[2] - od[2];
    note("grain: at 1:1 the picture's 2, 4 and 8 pixel bands are {d:.2}, {d:.2}, {d:.2} stronger (log variance) than the drawing's (grain is laid from 0.70)\n", .{ gap0, gap1, gap2 });
    if (@max(gap0, gap1) < 0.7) {
        note("grain: none\n", .{});
        return;
    }
    var map: [P.MAXN]usize = undefined;
    const field = cx.field;
    // first: the surface's own noise continued one or two octaves finer (the same kind, stretch and warp: a ridged,
    // stretched bark keeps its furrows sharp at 1:1); the drawing's bands and its grain's direction against the picture's
    const an_pic = R.aniso(C.pic.t, C.pic.n, 1);
    var cont_best: u32 = 0;
    var cont_d: f32 = 1e9;
    const nf = g.nodes[cx.nb.field];
    if (nf.op == P.OP_MODERN + F.K_NOISE and !cx.grain_in_field) {
        for ([_]u32{ 1, 2 }) |more| {
            const keep = g.n;
            var nn = nf;
            nn.w[4] = @min(12, nf.w[4] + more);
            const ni = F.add(g, nn);
            const nr = rewire(g, cx.root, cx.nb.field, ni, &map);
            const o = bands(cx, nr, C);
            var dd = drawIn(g, nr, C);
            const kk = keyOf(C, dd.rgb, C.pic.n);
            dd.free();
            const an = R.aniso(kk, C.pic.n, 1);
            alloc.free(kk);
            g.n = keep;
            const d = (op[0] - o[0]) * (op[0] - o[0]) + (op[1] - o[1]) * (op[1] - o[1]) + (op[2] - o[2]) * (op[2] - o[2]) + @log(an / an_pic) * @log(an / an_pic);
            note("  the surface's noise {d} octave(s) finer: bands {d:.2} {d:.2} {d:.2} (the picture's {d:.2} {d:.2} {d:.2}), across against down {d:.2} (the picture's {d:.2})\n", .{ more, o[0], o[1], o[2], op[0], op[1], op[2], an, an_pic });
            if (d < cont_d) {
                cont_d = d;
                cont_best = more;
            }
        }
    }
    var best_k: f32 = 0;
    var best_g: f32 = 0.75;
    var best_d: f32 = 1e9;
    const Try = struct { k: f32, gn: f32 };
    var tries: std.ArrayList(Try) = .empty;
    defer tries.deinit(alloc);
    for ([_]f32{ 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0 }) |k| tries.append(alloc, .{ .k = k, .gn = 0.75 }) catch unreachable;
    var round: usize = 0;
    while (round < 2) : (round += 1) {
        for (tries.items) |tr| {
            const keep = g.n;
            const nr = grainBuild(cx, H, field, tr.k, tr.gn, &map);
            const o = bands(cx, nr, C);
            var dd = drawIn(g, nr, C);
            const kk = keyOf(C, dd.rgb, C.pic.n);
            dd.free();
            const an = R.aniso(kk, C.pic.n, 1);
            alloc.free(kk);
            g.n = keep;
            const d = (op[0] - o[0]) * (op[0] - o[0]) + (op[1] - o[1]) * (op[1] - o[1]) + (op[2] - o[2]) * (op[2] - o[2]) + @log(an / an_pic) * @log(an / an_pic);
            note("  grain {d:.2}, fall {d:.2}: bands {d:.2} {d:.2} {d:.2} (the picture's {d:.2} {d:.2} {d:.2})\n", .{ tr.k, tr.gn, o[0], o[1], o[2], op[0], op[1], op[2] });
            if (d < best_d) {
                best_d = d;
                best_k = tr.k;
                best_g = tr.gn;
            }
        }
        tries.clearRetainingCapacity();
        for ([_]f32{ 0.55, 0.95 }) |gn| tries.append(alloc, .{ .k = best_k, .gn = gn }) catch unreachable;
    }
    if (cont_best > 0 and cont_d <= best_d) {
        var nn = nf;
        nn.w[4] = @min(12, nf.w[4] + cont_best);
        const ni = F.add(g, nn);
        cx.root = rewire(g, cx.root, cx.nb.field, ni, &map);
        cx.main_ramp = map[cx.main_ramp];
        cx.field = map[cx.field];
        cx.nb.field = ni;
        note("grain: the surface's own noise continued {d} octave(s) finer (it matches the picture's bands and grain better than a grain of its own: {d:.3} against {d:.3})\n", .{ cont_best, cont_d, best_d });
        push(cx, "+ the surface's noise continued finer (Noise)");
        return;
    }
    cx.root = grainBuild(cx, H, field, best_k, best_g, &map);
    if (cx.grain_in_field) {
        cx.main_ramp = map[cx.main_ramp];
        cx.field = cx.g.nodes[cx.main_ramp].in[0];
        note("grain: a Noise of 128 cells, 4 octaves, each {d:.2} of the last, laid at a strength of {d:.2} into the field before its Ramp (grainat=field; the Ramp read again on the whole)\n", .{ best_g, best_k });
        push(cx, "+ grain (Noise into the field, Ramp read again)");
    } else {
        note("grain: a Noise of 128 cells, 4 octaves, each {d:.2} of the last, laid at a strength of {d:.2} over the surface's colours (Layer, detail)\n", .{ best_g, best_k });
        push(cx, "+ grain (Noise, Layer)");
    }
}

/// The grain laid, everything after it rewired; the new root. Two paths, each a different picture, so both are kept:
/// after the surface's Ramp (the default: the colours and the coarse look of the rung below stay, the grain is added
/// as a grey departure, the detail mode of Layer) or in the field before the Ramp (grainat=field: the grain takes the
/// picture's colours by rank, the Ramp read again on H; strong grain then evens the coarse look out).
fn grainBuild(cx: *Ctx, H: *const View, field: usize, k: f32, gn: f32, map: []usize) usize {
    const g = cx.g;
    // a strength k: the Layer's amount up to 1, beyond it the noise's own contrast
    const nz = F.add(g, F.mk(F.K_NOISE, &.{ 1, 0, 128, 128, 4, gn, 0, 2, 3, @max(1.0, k) }, &.{}));
    if (!cx.grain_in_field) {
        const lg = F.add(g, F.mk(F.K_LAYER, &.{ 1, 3, -1, -0.5, @min(1.0, k), 0, 0.2 }, &.{ cx.main_ramp, nz, nz }));
        return rewire(g, cx.root, cx.main_ramp, lg, map);
    }
    const lg = F.add(g, F.mk(F.K_LAYER, &.{ 1, 3, -1, -0.5, @min(1.0, k), 0, 0.2 }, &.{ field, nz, field }));
    var dl = drawIn(g, lg, H);
    defer dl.free();
    const rw = F.rampWords(dl.grey, null, &H.pic, null, cx.nb.reversed, null);
    const nr = F.add(g, F.mk(F.K_RAMP, &rw, &.{lg}));
    return rewire(g, cx.root, cx.main_ramp, nr, map);
}

// ---------------------------------------------------------------- a laid structure: chips, grain and stain

fn structLayers(cx: *Ctx, C: *const View, H: *const View) void {
    const g = cx.g;
    const t_old = cx.st.tiles;
    const n = C.pic.n;
    const tn = g.nodes[t_old];
    // version 2 of the same Tiles: its 17 words, then chip, chip cells, grain, grain cells, octaves, stain, stain cells;
    // a version 3 node (milestone 2d: a hollow joint, pairs, framed tiles) keeps its version and its four last words
    var wfull = [_]f64{0} ** 28;
    const kinds = P.ops[P.OP_MODERN + F.K_TILES].kinds;
    const v3 = tn.w[0] >= 3;
    const nw: usize = if (v3) 28 else 24;
    for (0..17) |i| wfull[i] = switch (kinds[i]) {
        'i' => @floatFromInt(@as(i32, @bitCast(tn.w[i]))),
        'f' => @floatCast(@as(f32, @bitCast(tn.w[i]))),
        else => @floatFromInt(tn.w[i]),
    };
    if (v3) {
        for (24..28) |i| wfull[i] = @floatCast(@as(f32, @bitCast(tn.w[i])));
    }
    wfull[0] = if (v3) 3 else 2;
    const w = wfull[0..nw];
    const pieces: f64 = @floatFromInt(@max(cx.st.nx, cx.st.ny));
    w[17] = 0;
    w[18] = 6 * pieces;
    w[19] = 0;
    w[20] = 256;
    w[21] = 3;
    w[22] = 0;
    w[23] = 2 * pieces;
    // the picture's joints and faces at 1:1, as the drawn structure places them
    var d0 = drawIn(g, t_old, C);
    defer d0.free();
    const jm = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(jm);
    const fm = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(fm);
    for (0..n * n) |i| {
        jm[i] = d0.h[i] < 0.15;
        fm[i] = d0.h[i] > 0.85 and d0.grey[i] <= 0.86;
    }
    const tb = R.blur(C.pic.t, n, 2);
    defer alloc.free(tb);
    const kj = maskedMean(tb, jm);
    const kf = maskedMean(tb, fm);
    // the joints' side of a threshold nearer the joints than the faces, so the faces' own texture seldom crosses it
    const thr = kj + 0.35 * (kf - kj);
    const pm = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(pm);
    for (0..n * n) |i| pm[i] = if (kj > kf) tb[i] > thr else tb[i] < thr;
    const e_pic = smoothEdge(pm, n, 3);
    // chips: the drawn joints' outline against the picture's
    var chip: f32 = 0;
    if (refused(cx.off, "chips")) note("chips: left off by eye (off=chips)\n", .{}) else {
        var best_d: f32 = 1e9;
        var e0: f32 = 0;
        // milestone 2d: finer chip cells too (with the joints read at 1:1 the bevel no longer hides a coarse bite)
        const c0 = w[18];
        var bcc = c0;
        const ccs = if (cx.grain_cap) [_]f64{ c0, 2 * c0, 4 * c0 } else [_]f64{ c0, c0, c0 };
        // with the joints read at 1:1, a chip bites at most half the joint's width into a piece (deeper bites, lit,
        // drew black broken edges on the bricks: by eye)
        const jw_read: f64 = @as(f32, @bitCast(cx.g.nodes[t_old].w[5]));
        for (ccs, 0..) |cc, cci| for ([_]f32{ 0, 0.03, 0.06, 0.1, 0.15 }) |ch| {
            if (cci > 0 and (ch == 0 or cc == ccs[cci - 1])) continue;
            if (cx.joints_full and ch > 0.5 * jw_read) continue;
            w[17] = ch;
            w[18] = cc;
            const keep = g.n;
            const ti = F.add(g, F.mk(F.K_TILES, w, &.{}));
            var dt = drawIn(g, ti, C);
            g.n = keep;
            const dm = alloc.alloc(bool, n * n) catch unreachable;
            for (0..n * n) |i| dm[i] = dt.h[i] < 0.5;
            const e = smoothEdge(dm, n, 3);
            alloc.free(dm);
            dt.free();
            if (ch == 0) e0 = e;
            note("  chip {d:.2} of {d} cells: the joints' outline {d:.4} per pixel inside (the picture's {d:.4})\n", .{ ch, @as(i32, @intFromFloat(cc)), e, e_pic });
            if (F.absDiff(e, e_pic) < best_d) {
                best_d = F.absDiff(e, e_pic);
                chip = ch;
                bcc = cc;
            }
        };
        w[18] = bcc;
        if (e_pic < 1.2 * e0) {
            chip = 0;
            note("chips: none (the picture's joints are not more ragged than drawn: {d:.4} against {d:.4}; chips from 1.2 times)\n", .{ e_pic, e0 });
        } else note("chips: {d:.2} of a piece's side, {d} noise cells across\n", .{ chip, @as(i32, @intFromFloat(w[18])) });
    }
    w[17] = chip;
    // grain and stain in the faces: the faces' 2, 4 and 8 pixel detail and their coarse variation inside a piece
    const p1 = bandSd(C.pic.t, n, 1, fm);
    const p3 = bandSd(C.pic.t, n, 3, fm);
    const p12 = bandSd(tb, n, 12, fm);
    var map: [P.MAXN]usize = undefined;
    var bg: f32 = 0;
    var bs: f32 = 0;
    var bgc: f64 = 256;
    if (refused(cx.off, "grain")) note("grain: left off by eye (off=grain)\n", .{}) else {
        var best_d: f32 = 1e9;
        var first = true;
        var d1_0: f32 = 0;
        var b0 = [3]f32{ 0, 0, 0 };
        // milestone 2d: finer grain cells too (Daniel on the bricks: "too much granulated"; a grain of 256 cells
        // across adds its detail at 8 to 12 pixels, where the picture's faces are already matched)
        const gcs = if (cx.grain_cap) [_]f64{ 256, 512, 1024 } else [_]f64{ 256, 256, 256 };
        for (gcs, 0..) |gc, gci| for ([_]f32{ 0, 0.25, 0.5, 0.75, 1.0 }) |gr| {
            if (gci > 0 and (gr == 0 or gc == gcs[gci - 1])) continue;
            for ([_]f32{ 0, 0.3, 0.6 }) |sn| {
                w[19] = gr;
                w[20] = gc;
                w[22] = sn;
                const keep = g.n;
                const nr = structBuild(cx, H, w, &map);
                var dd = drawIn(g, nr, C);
                g.n = keep;
                const k = keyOf(C, dd.rgb, n);
                dd.free();
                const kb = R.blur(k, n, 1);
                const d1 = bandSd(k, n, 1, fm);
                const d3 = bandSd(k, n, 3, fm);
                const d12 = bandSd(kb, n, 12, fm);
                alloc.free(k);
                alloc.free(kb);
                if (first) {
                    d1_0 = d1;
                    b0 = .{ d1, d3, d12 };
                    first = false;
                }
                const dist = @log((d1 + 1e-4) / (p1 + 1e-4)) * @log((d1 + 1e-4) / (p1 + 1e-4)) + @log((d3 + 1e-4) / (p3 + 1e-4)) * @log((d3 + 1e-4) / (p3 + 1e-4)) + @log((d12 + 1e-4) / (p12 + 1e-4)) * @log((d12 + 1e-4) / (p12 + 1e-4));
                // milestone 2d (Daniel on the bricks: "too much granulated"): the grain may not raise a band of the
                // drawn faces above the picture's (or above the faces without grain, where they are above it already)
                const over = cx.grain_cap and (d1 > @max(p1, 1.02 * b0[0]) or d3 > @max(p3, 1.02 * b0[1]) or d12 > @max(p12, 1.02 * b0[2]));
                note("  grain {d:.2} of {d} cells, stain {d:.2}: the faces' detail {d:.4} {d:.4} {d:.4} (the picture's {d:.4} {d:.4} {d:.4}){s}\n", .{ gr, @as(i32, @intFromFloat(gc)), sn, d1, d3, d12, p1, p3, p12, if (over) ": raises a band above the picture's, not taken" else "" });
                if (!over and dist < best_d) {
                    bgc = gc;
                    best_d = dist;
                    bg = gr;
                    bs = sn;
                }
            }
        };
        if (p1 < 1.4 * d1_0 and bg == 0 and bs == 0) note("grain: none in the faces (the picture's faces {d:.4}, drawn {d:.4})\n", .{ p1, d1_0 }) else note("grain: each piece's own grain {d:.2} of {d} cells and stain {d:.2} (Tiles version 2)\n", .{ bg, @as(i32, @intFromFloat(bgc)), bs });
    }
    w[19] = bg;
    w[20] = bgc;
    w[22] = bs;
    if (chip == 0 and bg == 0 and bs == 0) return;
    cx.root = structBuild(cx, H, w, &map);
    cx.main_ramp = map[cx.main_ramp];
    cx.face_layer = map[cx.face_layer];
    cx.st.tiles = map[t_old];
    push(cx, "+ chipped edges, each piece's grain and stain (Tiles version 2, Ramp read again)");
}

/// the structure drawn by Tiles version 2 with words w, the faces' Ramp read again on H as milestone 2b read it, the
/// rest rewired; the new root (map: each old node's copy)
fn structBuild(cx: *Ctx, H: *const View, w: []const f64, map: []usize) usize {
    const g = cx.g;
    const n = H.pic.n;
    const ti = F.add(g, F.mk(F.K_TILES, w, &.{}));
    const r1 = rewire(g, cx.root, cx.st.tiles, ti, map);
    // the faces' Ramp, read again: the drawn faces and joints of the new structure, the joints' own colour
    const lx = map[cx.face_layer];
    var dt = drawIn(g, ti, H);
    defer dt.free();
    var dl = drawIn(g, lx, H);
    defer dl.free();
    const face = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(face);
    const jsel = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(jsel);
    for (0..n * n) |i| {
        face[i] = dt.h[i] > 0.85;
        jsel[i] = dt.h[i] < 0.15;
    }
    const jc = F.meanColour(&H.pic, jsel);
    const rw = F.rampWords(dl.grey, face, &H.pic, face, false, jc);
    const rr = map[cx.main_ramp];
    if (rr == cx.main_ramp) P.die("close up: the faces' Ramp does not follow the structure", .{});
    for (0..18) |i| {
        g.nodes[rr].w[i] = switch (P.ops[P.OP_MODERN + F.K_RAMP].kinds[i]) {
            'i' => @bitCast(@as(i32, @intFromFloat(rw[i]))),
            'f' => @bitCast(@as(f32, @floatCast(rw[i]))),
            else => @intFromFloat(rw[i]),
        };
    }
    return r1;
}

// ---------------------------------------------------------------- mortar

fn mortarLayers(cx: *Ctx, C: *const View) void {
    const g = cx.g;
    const n = C.pic.n;
    // the joints as milestone 2b drew them: chipped edges would count the pieces' bitten corners as mortar
    var dt = drawIn(g, cx.tiles0, C);
    defer dt.free();
    const jm = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(jm);
    const fm = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(fm);
    var share: f32 = 0;
    for (0..n * n) |i| {
        jm[i] = dt.h[i] < 0.1 and dt.grey[i] < 0.1;
        fm[i] = dt.h[i] > 0.85 and dt.grey[i] <= 0.86;
        if (jm[i]) share += 1;
    }
    share /= @floatFromInt(n * n);
    // the mortar is a material of its own where its colour stands apart from the faces' by more than they vary
    const kj = maskedMean(C.pic.t, jm);
    const kf = maskedMean(C.pic.t, fm);
    const sf = maskedSd(C.pic.t, fm);
    note("mortar: the joints hold {d:.3} of the picture at 1:1, their colour {d:.3} from the faces' (the faces spread {d:.3}; a mortar of its own from 0.03 of the picture and half a spread apart)\n", .{ share, kj - kf, sf });
    if (share < 0.03 or @abs(kj - kf) < 0.5 * sf) return;
    if (refused(cx.off, "mortar")) {
        note("mortar: left off by eye (off=mortar)\n", .{});
        return;
    }
    var dc = drawIn(g, cx.root, C);
    const kd = keyOf(C, dc.rgb, n);
    dc.free();
    defer alloc.free(kd);
    // milestone 2d: the joints' spread read on their core (two pixels in from their edges at 1:1), where the
    // mortar's own colours are; the edges hold the pieces' shadows and chips, and a joint read at 1:1 is wide
    const jf = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(jf);
    for (0..n * n) |i| jf[i] = if (jm[i]) 1 else 0;
    const jb = R.blur(jf, n, 2);
    defer alloc.free(jb);
    const jcore = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(jcore);
    var ncore: usize = 0;
    for (0..n * n) |i| {
        jcore[i] = jm[i] and (!cx.joints_full or jb[i] > 0.99);
        if (jcore[i]) ncore += 1;
    }
    const jmm = if (ncore > 200) jcore else jm;
    const pj = maskedSd(C.pic.t, jmm);
    const dj = maskedSd(kd, jmm);
    note("mortar: the joints' colours spread {d:.4} in the picture, {d:.4} drawn (noise in the mortar from twice the drawn and 0.01 more)\n", .{ pj, dj });
    if (pj > 2 * dj + 0.01 and cx.grain_cap) {
        // milestone 2d (Daniel on the metal plate: "colors still off"): the mortar's own colours, not only its
        // shade: the joints' own main colour axis (the plate's green against its rust, the mortar's greys), the
        // noise coloured by a Ramp at the same ranks of that axis among the joints' pixels, mixed into the joints by
        // an amount chosen so their spread along that axis agrees with the picture's
        var mj = [3]f64{ 0, 0, 0 };
        var nj: f64 = 0;
        for (0..n * n) |i| {
            if (!jmm[i]) continue;
            inline for (0..3) |q| mj[q] += C.pic.rgb[3 * i + q];
            nj += 1;
        }
        inline for (0..3) |q| mj[q] /= @max(1, nj);
        var cv = [9]f64{ 0, 0, 0, 0, 0, 0, 0, 0, 0 };
        for (0..n * n) |i| {
            if (!jmm[i]) continue;
            inline for (0..3) |a| {
                inline for (0..3) |b| cv[a * 3 + b] += (C.pic.rgb[3 * i + a] - mj[a]) * (C.pic.rgb[3 * i + b] - mj[b]);
            }
        }
        var ax = [3]f64{ 0.577, 0.577, 0.577 };
        for (0..30) |_| {
            var nx = [3]f64{ 0, 0, 0 };
            inline for (0..3) |a| {
                inline for (0..3) |b| nx[a] += cv[a * 3 + b] * ax[b];
            }
            const l = @sqrt(nx[0] * nx[0] + nx[1] * nx[1] + nx[2] * nx[2]) + 1e-12;
            inline for (0..3) |a| ax[a] = nx[a] / l;
        }
        const tj = alloc.alloc(f32, n * n) catch unreachable;
        defer alloc.free(tj);
        for (0..n * n) |i| {
            var v: f64 = 0;
            inline for (0..3) |q| v += (C.pic.rgb[3 * i + q] - mj[q]) * ax[q];
            tj[i] = @floatCast(v);
        }
        const picj = F.Pic{ .n = n, .rgb = C.pic.rgb, .t = tj, .tsort = tj };
        const pja = robustSd(tj, jmm);
        const nz = F.add(g, F.noiseNode(0, 96, 96, 4, 0.7, 0, 2, 13));
        var dn = drawIn(g, nz, C);
        const rw = F.rampWords(dn.grey, null, &picj, jmm, false, null);
        dn.free();
        const mr = F.add(g, F.mk(F.K_RAMP, &rw, &.{nz}));
        var best_k: f32 = 0;
        var best_d: f32 = 1e9;
        for ([_]f32{ 0.06, 0.12, 0.2, 0.32, 0.5, 0.75, 1.0 }) |k| {
            const keep = g.n;
            const lm = F.add(g, F.mk(F.K_LAYER, &.{ 2, 0, 0.12, 0.03, k, 0, 0 }, &.{ cx.root, mr, cx.st.tiles }));
            var dd = drawIn(g, lm, C);
            g.n = keep;
            const k2 = alloc.alloc(f32, n * n) catch unreachable;
            for (0..n * n) |i| {
                var v: f64 = 0;
                inline for (0..3) |q| v += (dd.rgb[3 * i + q] - mj[q]) * ax[q];
                k2[i] = @floatCast(v);
            }
            dd.free();
            const sv = robustSd(k2, jmm);
            alloc.free(k2);
            note("  mortar colours {d:.2}: the joints spread {d:.4} along their own colour axis, the middle half's spread (the picture's {d:.4})\n", .{ k, sv, pja });
            if (F.absDiff(sv, pja) < best_d) {
                best_d = F.absDiff(sv, pja);
                best_k = k;
            }
        }
        cx.root = F.add(g, F.mk(F.K_LAYER, &.{ 2, 0, 0.12, 0.03, best_k, 0, 0 }, &.{ cx.root, mr, cx.st.tiles }));
        note("mortar: its own colours (a Ramp along the joints' colour axis {d:.2} {d:.2} {d:.2}) laid {d:.2} into the joints\n", .{ ax[0], ax[1], ax[2], best_k });
        push(cx, "+ mortar's own colours (Noise, Ramp, Layer)");
    } else if (pj > 2 * dj + 0.01) {
        var best_k: f32 = 0;
        var best_d: f32 = 1e9;
        const nz = F.add(g, F.noiseNode(0, 96, 96, 4, 0.7, 0, 2, 13));
        for ([_]f32{ 0.06, 0.12, 0.2, 0.32, 0.5, 0.75, 1.0 }) |k| {
            const keep = g.n;
            const lm = F.add(g, F.mk(F.K_LAYER, &.{ 2, 3, 0.12, 0.03, k, 0, 0 }, &.{ cx.root, nz, cx.st.tiles }));
            var dd = drawIn(g, lm, C);
            g.n = keep;
            const k2 = keyOf(C, dd.rgb, n);
            dd.free();
            const sv = maskedSd(k2, jmm);
            alloc.free(k2);
            note("  mortar noise {d:.2}: the joints spread {d:.4} (the picture's {d:.4})\n", .{ k, sv, pj });
            if (F.absDiff(sv, pj) < best_d) {
                best_d = F.absDiff(sv, pj);
                best_k = k;
            }
        }
        cx.root = F.add(g, F.mk(F.K_LAYER, &.{ 2, 3, 0.12, 0.03, best_k, 0, 0 }, &.{ cx.root, nz, cx.st.tiles }));
        note("mortar: a Noise of 96 cells laid {d:.2} into the joints (Layer version 2, the joints as a falling mask)\n", .{best_k});
        push(cx, "+ mortar's own variation (Noise, Layer)");
    } else note("mortar: its colours as drawn\n", .{});
    // light specks in the mortar (lime, sand): light compact marks of 10 pixels or more within the joints
    const sp = marks(C.pic.t, n, 6, 2.5, false, 10, 400, jm);
    const cnt_whole: f32 = @as(f32, @floatFromInt(sp.count)) / (share * 0.25);
    note("mortar specks: {d} light marks of about {d:.1} pixels in the joints at 1:1 (specks: 6 or more, 10 pixels or more each)\n", .{ sp.count, sp.radius });
    if (sp.count >= 6) {
        const col = F.colourAtRankSel(&C.pic, 0.97, jm);
        // instances anywhere, laid only in the joints: cells so that the joints' share of them meets the count
        const cells: i32 = @max(4, @as(i32, @intFromFloat(@sqrt(cnt_whole / 0.5))));
        const cellpx = @as(f32, @floatFromInt(cx.N)) / @as(f32, @floatFromInt(cells));
        const size = @min(0.45, @max(0.01, sp.radius * @as(f32, @floatFromInt(cx.N / 2)) / @as(f32, @floatFromInt(n)) / cellpx));
        const sc = F.add(g, scatter2(cx.root, cells, 0.5, size, 0.5, col, 0.15, 17, 0.1, 0.4, 1, 8, 0, 0.5, 3, 0));
        cx.root = F.add(g, F.mk(F.K_LAYER, &.{ 2, 0, 0.12, 0.03, 1, 0, 0 }, &.{ cx.root, sc, cx.st.tiles }));
        note("mortar specks: Scatter version 2, {d} cells across, light, laid in the joints only\n", .{cells});
        push(cx, "+ mortar specks (Scatter, Layer)");
    }
}

// ---------------------------------------------------------------- moss and wet patches

fn patchesLayer(cx: *Ctx, H: *const View) void {
    const g = cx.g;
    const n = H.pic.n;
    if (cx.st.ok) return;
    if (cx.second) {
        note("patches: milestone 2b's second material is laid already\n", .{});
        return;
    }
    if (refused(cx.off, "patches")) {
        note("patches: left off by eye (off=patches)\n", .{});
        return;
    }
    // colours off the main axis by 0.05 or more (milestone 2b read 0.10), grouped by the way they lean (three groups
    // of directions, by cosine; fixed starting directions, so the same picture gives the same groups)
    const c0 = F.rgbOfWord(cx.rd.c0);
    const c1 = F.rgbOfWord(cx.rd.c1);
    var ax = [3]f32{ c1[0] - c0[0], c1[1] - c0[1], c1[2] - c0[2] };
    const al = @sqrt(ax[0] * ax[0] + ax[1] * ax[1] + ax[2] * ax[2]) + 1e-6;
    inline for (0..3) |q| ax[q] /= al;
    const dirs = alloc.alloc([3]f32, n * n) catch unreachable;
    defer alloc.free(dirs);
    const lab = alloc.alloc(u8, n * n) catch unreachable;
    defer alloc.free(lab);
    var noff: usize = 0;
    for (0..n * n) |i| {
        var d = [3]f32{ H.pic.rgb[3 * i] - c0[0], H.pic.rgb[3 * i + 1] - c0[1], H.pic.rgb[3 * i + 2] - c0[2] };
        const pr = d[0] * ax[0] + d[1] * ax[1] + d[2] * ax[2];
        inline for (0..3) |q| d[q] -= pr * ax[q];
        const len = @sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
        lab[i] = 255;
        if (len > 0.05) {
            inline for (0..3) |q| dirs[i][q] = d[q] / len;
            lab[i] = 0;
            noff += 1;
        }
    }
    // starting directions: the three primaries made orthogonal to the axis
    var cen: [3][3]f32 = undefined;
    for (0..3) |k| {
        var e = [3]f32{ 0, 0, 0 };
        e[k] = 1;
        const pr = e[0] * ax[0] + e[1] * ax[1] + e[2] * ax[2];
        inline for (0..3) |q| e[q] -= pr * ax[q];
        const len = @sqrt(e[0] * e[0] + e[1] * e[1] + e[2] * e[2]) + 1e-9;
        inline for (0..3) |q| cen[k][q] = e[q] / len;
    }
    var cnt = [3]f32{ 0, 0, 0 };
    for (0..12) |_| {
        var acc = [_][3]f32{.{ 0, 0, 0 }} ** 3;
        cnt = .{ 0, 0, 0 };
        for (0..n * n) |i| {
            if (lab[i] == 255) continue;
            var bk: u8 = 0;
            var bc: f32 = -2;
            for (0..3) |k| {
                const cs = dirs[i][0] * cen[k][0] + dirs[i][1] * cen[k][1] + dirs[i][2] * cen[k][2];
                if (cs > bc) {
                    bc = cs;
                    bk = @intCast(k);
                }
            }
            lab[i] = bk;
            inline for (0..3) |q| acc[bk][q] += dirs[i][q];
            cnt[bk] += 1;
        }
        for (0..3) |k| {
            const len = @sqrt(acc[k][0] * acc[k][0] + acc[k][1] * acc[k][1] + acc[k][2] * acc[k][2]);
            if (len > 0) {
                inline for (0..3) |q| cen[k][q] = acc[k][q] / len;
            }
        }
    }
    // the group whose pixels lie in the largest patches (the mask blurred by 2, so speckled moss joins up)
    var best_k: usize = 3;
    var best_cl: f32 = 0;
    var best_share: f32 = 0;
    const mask = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(mask);
    for (0..3) |k| {
        const share = cnt[k] / @as(f32, @floatFromInt(n * n));
        for (0..n * n) |i| mask[i] = if (lab[i] == k) 1 else 0;
        const mb = R.blur(mask, n, 2);
        const cl = R.corrLength(mb, n, false);
        alloc.free(mb);
        note("patches: colours leaning one way ({d}): {d:.3} of the whole, in patches about {d:.0} pixels across at {d}\n", .{ k, share, cl, n });
        if (share >= 0.03 and cl >= 5 and cl * share > best_cl * best_share) {
            best_k = k;
            best_cl = cl;
            best_share = share;
        }
    }
    if (best_k < 3) {
        const share = best_share;
        const sel = alloc.alloc(bool, n * n) catch unreachable;
        defer alloc.free(sel);
        for (0..n * n) |i| {
            sel[i] = lab[i] == best_k;
            mask[i] = if (sel[i]) 1 else 0;
        }
        const mb = R.blur(mask, n, 2);
        defer alloc.free(mb);
        const cells: i32 = @max(2, @as(i32, @intFromFloat(@as(f32, @floatFromInt(n)) / (2.5 * best_cl))));
        const epa_pic = R.edgePerArea(mb, n, 0.5);
        var bw: f32 = 0;
        var bdd: f32 = 1e9;
        var lo: f32 = 0.5;
        var hi: f32 = 0.6;
        for ([_]f32{ 0, 0.03, 0.08 }) |wv| {
            const keep = g.n;
            const mx = F.add(g, F.noiseNode(0, cells, cells, 7, 0.65, wv, cells * 2, 21));
            var dm = drawIn(g, mx, H);
            g.n = keep;
            const thr = R.quantile(dm.grey, 1.0 - share);
            const bin = alloc.alloc(f32, n * n) catch unreachable;
            for (dm.grey, 0..) |v, i| bin[i] = if (v > thr) 1 else 0;
            const epa = R.edgePerArea(bin, n, 0.5);
            alloc.free(bin);
            note("  patches warped {d:.2}: edge {d:.3} per pixel inside (the picture's {d:.3})\n", .{ wv, epa, epa_pic });
            if (F.absDiff(epa, epa_pic) < bdd) {
                bdd = F.absDiff(epa, epa_pic);
                bw = wv;
                lo = R.quantile(dm.grey, 1.0 - 1.3 * share);
                hi = R.quantile(dm.grey, 1.0 - 0.7 * share);
            }
            dm.free();
        }
        const mx = F.add(g, F.noiseNode(0, cells, cells, 7, 0.65, bw, cells * 2, 21));
        var dn = drawIn(g, cx.field, H);
        defer dn.free();
        const rw = F.rampWords(dn.grey, null, &H.pic, sel, cx.nb.reversed, null);
        const r2 = F.add(g, F.mk(F.K_RAMP, &rw, &.{cx.field}));
        cx.root = F.add(g, F.mk(F.K_LAYER, &.{ 1, 0, lo, hi, 1, 2, 0.1 }, &.{ cx.root, r2, mx }));
        const sc = F.meanColour(&H.pic, sel);
        note("patches: a second colour {x:0>6} ({d:.3} of the whole) in ragged patches of {d} cells (warp {d:.2}), laid where the noise is above {d:.3} to {d:.3}\n", .{ @as(u32, @intFromFloat(F.colourWord(sc))) & 0xffffff, share, cells, bw, lo, hi });
        cx.patches = true;
        push(cx, "+ patches of a second colour (Noise, Ramp, Layer)");
        return;
    }
    // wet: dark patches with less detail (blocks of 32 pixels: their brightness against their detail)
    const B = 32;
    const nbk = n / B;
    const hp = R.blur(H.pic.t, n, 2);
    defer alloc.free(hp);
    var ms: [1024]f32 = undefined;
    var ds: [1024]f32 = undefined;
    const nbb = @min(nbk * nbk, 1024);
    for (0..nbk) |by| {
        for (0..nbk) |bx| {
            if (by * nbk + bx >= nbb) continue;
            var s: f64 = 0;
            var s2: f64 = 0;
            for (0..B) |y| {
                for (0..B) |x| {
                    const i = (by * B + y) * n + bx * B + x;
                    s += H.pic.t[i];
                    const d: f64 = H.pic.t[i] - hp[i];
                    s2 += d * d;
                }
            }
            ms[by * nbk + bx] = @floatCast(s / (B * B));
            ds[by * nbk + bx] = @floatCast(@sqrt(s2 / (B * B)));
        }
    }
    var mm: f64 = 0;
    var md: f64 = 0;
    for (0..nbb) |i| {
        mm += ms[i];
        md += ds[i];
    }
    mm /= @floatFromInt(nbb);
    md /= @floatFromInt(nbb);
    var sxy: f64 = 0;
    var sxx: f64 = 0;
    var syy: f64 = 0;
    for (0..nbb) |i| {
        sxy += (ms[i] - mm) * (ds[i] - md);
        sxx += (ms[i] - mm) * (ms[i] - mm);
        syy += (ds[i] - md) * (ds[i] - md);
    }
    const corr: f32 = @floatCast(sxy / @sqrt(sxx * syy + 1e-18));
    note("wet: over blocks of {d} pixels the brightness and the detail agree {d:.2} (dark and smooth patches from 0.50)\n", .{ B, corr });
    if (corr < 0.5) return;
    // the wet blocks: darker and smoother than the mean
    const sel2 = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(sel2);
    var wshare: f32 = 0;
    for (0..n) |y| {
        for (0..n) |x| {
            const b = @min(nbb - 1, (y / B) * nbk + x / B);
            sel2[y * n + x] = ms[b] < mm and ds[b] < md;
            if (sel2[y * n + x]) wshare += 1;
        }
    }
    wshare /= @floatFromInt(n * n);
    const wm = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(wm);
    for (0..n * n) |i| wm[i] = if (sel2[i]) 1 else 0;
    const cl2 = @max(R.corrLength(wm, n, false), 8.0);
    const cells: i32 = @max(2, @as(i32, @intFromFloat(@as(f32, @floatFromInt(n)) / (2.5 * cl2))));
    const mx = F.add(g, F.noiseNode(0, cells, cells, 6, 0.6, 0.03, cells * 2, 23));
    var dm = drawIn(g, mx, H);
    const lo = R.quantile(dm.grey, 1.0 - 1.3 * wshare);
    const hi = R.quantile(dm.grey, 1.0 - 0.7 * wshare);
    dm.free();
    // the wet patches' colour against the rest's, as a factor per channel: the surface multiplied by it there, so its
    // detail stays and shrinks with the brightness, as a wet surface's does
    const wc = F.meanColour(&H.pic, sel2);
    const dry = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(dry);
    for (0..n * n) |i| dry[i] = !sel2[i];
    const dc = F.meanColour(&H.pic, dry);
    var ratio: [3]f32 = undefined;
    inline for (0..3) |q| ratio[q] = @min(1.0, wc[q] / @max(0.01, dc[q]));
    const rw0 = F.colourWord(ratio);
    const top = F.add(g, F.mk(F.K_RAMP, &.{ 1, 2, 0, rw0, 1, rw0, 1, 0xff808080, 1, 0xff808080, 1, 0xff808080, 1, 0xff808080, 1, 0xff808080, 1, 0xff808080 }, &.{cx.field}));
    cx.root = F.add(g, F.mk(F.K_LAYER, &.{ 1, 1, lo, hi, 1, 0, 0 }, &.{ cx.root, top, mx }));
    note("wet: {d:.2} of the whole in dark smooth patches of {d} cells, the surface multiplied there by {d:.2} {d:.2} {d:.2}\n", .{ wshare, cells, ratio[0], ratio[1], ratio[2] });
    push(cx, "+ wet patches (Noise, Ramp, Layer)");
}

// ---------------------------------------------------------------- spots, their halo and their runs

/// Marks at one end of the main colour axis: the darkest (or lightest) q of the view, blurred by 2 so the granules of
/// one mark join, its compact pieces (12 to 4000 pixels); how much of the end they hold, their size, how they gather,
/// and how far the marks' colour stands from the rest (in the rest's own spreads)
const AxisMarks = struct { region: []bool, comps: std.ArrayList(Comp), share: f32, rad: f32, disp: f32, contrast: f32, down: f32 };
fn axisMarks(v: *const View, dark: bool, q: f32) AxisMarks {
    const n = v.pic.n;
    const thr = R.quantile(v.pic.t, if (dark) q else 1.0 - q);
    const f = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(f);
    for (0..n * n) |i| f[i] = if ((dark and v.pic.t[i] < thr) or (!dark and v.pic.t[i] > thr)) 1 else 0;
    const fb = R.blur(f, n, 2);
    defer alloc.free(fb);
    const region = alloc.alloc(bool, n * n) catch unreachable;
    var area: usize = 0;
    for (0..n * n) |i| {
        region[i] = fb[i] > 0.5;
        if (region[i]) area += 1;
    }
    var all: std.ArrayList(Comp) = .empty;
    defer all.deinit(alloc);
    components(region, n, &all);
    var cs: std.ArrayList(Comp) = .empty;
    compact(all.items, 12, 4000, &cs);
    var ca: usize = 0;
    for (cs.items) |c| ca += c.area;
    const rest = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(rest);
    for (0..n * n) |i| rest[i] = !region[i];
    const contrast = @abs(maskedMean(v.pic.t, region) - maskedMean(v.pic.t, rest)) / @max(1e-6, maskedSd(v.pic.t, rest));
    return .{ .region = region, .comps = cs, .share = @as(f32, @floatFromInt(ca)) / @as(f32, @floatFromInt(@max(1, area))), .rad = meanRadius(cs.items), .disp = dispersion(cs.items, n, 8), .contrast = contrast, .down = meanDown(cs.items) };
}

fn spotsLayer(cx: *Ctx, C: *const View, H: *const View) void {
    const g = cx.g;
    const n = H.pic.n;
    if (cx.st.ok) return;
    if (cx.patches) {
        note("spots: the second colour is laid as patches already\n", .{});
        return;
    }
    if (refused(cx.off, "spots")) {
        note("spots: left off by eye (off=spots)\n", .{});
        return;
    }
    var am = axisMarks(H, true, 0.2);
    defer alloc.free(am.region);
    defer am.comps.deinit(alloc);
    note("spots: the darkest fifth of the whole at {d}, its granules joined, lies {d:.2} in {d} compact marks of about {d:.1} pixels, gathered {d:.1}, {d:.2} spreads darker than the rest (spots: 0.45 in 30 or more, 5 pixels, 2.2 spreads)\n", .{ n, am.share, am.comps.items.len, am.rad, am.disp, am.contrast });
    if (am.share < 0.45 or am.comps.items.len < 30 or am.rad < 5 or am.contrast < 2.2) {
        if (!refused(cx.on, "spots")) return;
        note("spots: asked for by eye (on=spots) below the reading's thresholds; every value below is still read from the pixels\n", .{});
    }
    const region = am.region;
    var map: [P.MAXN]usize = undefined;
    // milestone 2b's second material goes: the spots carry it now
    if (cx.second_layer != 0) {
        cx.root = rewire(g, cx.root, cx.second_layer, g.nodes[cx.second_layer].in[0], &map);
        cx.main_ramp = map[cx.main_ramp];
        note("spots: milestone 2b's second material (a Layer through a noise) is taken out; the spots carry it\n", .{});
    }
    // the base: the first material, read away from the spots and their stains
    const rb_f = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(rb_f);
    for (0..n * n) |i| rb_f[i] = if (region[i]) 1 else 0;
    const near = R.blur(rb_f, n, @intFromFloat(@max(2, 2 * am.rad)));
    defer alloc.free(near);
    const stain_thr = R.quantile(H.pic.t, 0.35);
    // the first material: the lighter half, away from every spot and stain (the lightest three tenths read greyer
    // than the metal between the spots, and the tiles' Tints then pushed the whole toward yellow: by eye)
    const base_thr = R.quantile(H.pic.t, 0.5);
    const clean = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(clean);
    var ncl: usize = 0;
    for (0..n * n) |i| {
        clean[i] = !region[i] and H.pic.t[i] >= base_thr;
        if (clean[i]) ncl += 1;
    }
    var dn = drawIn(g, cx.field, H);
    const rw = F.rampWords(dn.grey, null, &H.pic, if (ncl > 1000) clean else null, cx.nb.reversed, null);
    dn.free();
    const base = F.add(g, F.mk(F.K_RAMP, &rw, &.{cx.field}));
    cx.root = rewire(g, cx.root, cx.main_ramp, base, &map);
    cx.main_ramp = base;
    note("spots: the surface's Ramp read again on the first material alone ({d:.2} of the whole)\n", .{@as(f32, @floatFromInt(ncl)) / @as(f32, @floatFromInt(n * n))});
    // colours: the spot as a whole, its darkest granules, the stain around it
    const spot_c = F.meanColour(&H.pic, region);
    const stained = alloc.alloc(bool, n * n) catch unreachable;
    defer alloc.free(stained);
    for (0..n * n) |i| stained[i] = !region[i] and H.pic.t[i] < stain_thr;
    const halo_c = F.meanColour(&H.pic, stained);
    const cnt: f32 = @floatFromInt(am.comps.items.len);
    const clu: f32 = if (am.disp >= 2.0) 1.0 else if (am.disp >= 1.3) 0.5 else 0;
    // cells: with a cluster of 1 about half the cells hold one, at a density of 0.9
    const meanok: f32 = if (clu >= 1) 0.45 else if (clu > 0) 0.7 else 1.0;
    const cells: i32 = @max(4, @as(i32, @intFromFloat(@sqrt(cnt / (0.9 * meanok)))));
    const cellpx = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(cells));
    const size = @min(0.4, @max(0.01, am.rad / cellpx));
    const asp = @min(2.5, @max(0.6, am.down));
    var colour = cx.root;
    const black = F.add(g, F.mk(F.K_RAMP, &.{ 1, 2, 0, 0xff000000, 1, 0xff000000, 1, 0xff000000, 1, 0xff000000, 1, 0xff000000, 1, 0xff000000, 1, 0xff000000, 1, 0xff000000 }, &.{cx.field}));
    const sm = F.add(g, scatter2(black, cells, 0.9, size, 0.8, .{ 1, 1, 1 }, 0, 31, 0, 0.5, asp, 8, clu, 0.6, 3, 0));
    // the halo: how much of the ring around the spots is stained, against far from them
    var ring: f32 = 0;
    var ringn: f32 = 0;
    var far: f32 = 0;
    var farn: f32 = 0;
    for (0..n * n) |i| {
        if (region[i]) continue;
        const st: f32 = if (stained[i]) 1 else 0;
        if (near[i] > 0.05) {
            ring += st;
            ringn += 1;
        } else {
            far += st;
            farn += 1;
        }
    }
    const ringv = ring / @max(1, ringn);
    const farv = far / @max(1, farn);
    note("spots: {d} cells across, size {d:.2} of a cell, {d:.1} times as long down, gathered {d:.1}; the spot {x:0>6}, the stain {x:0>6}\n", .{ cells, size, asp, clu, @as(u32, @intFromFloat(F.colourWord(spot_c))) & 0xffffff, @as(u32, @intFromFloat(F.colourWord(halo_c))) & 0xffffff });
    note("halo: beside the spots {d:.3} of the pixels are stained, far from them {d:.3} (a halo from 1.5 times)\n", .{ ringv, farv });
    if (ringv >= 1.5 * farv and ringv > 0.02 and !refused(cx.off, "halo")) {
        // the stain reaches as far as the picture's stained ring does (two radii beyond the spot), at its share
        const rr = @min(0.1, 3.0 * am.rad / @as(f32, @floatFromInt(n)));
        colour = F.add(g, F.mk(F.K_WEAR, &.{ 1, 3, rr, 0.05, 0.15, 0.6, @min(0.9, 1.5 * ringv), F.colourWord(halo_c), @as(f64, @floatFromInt(cells)) * 2, 0.3, 33, 4.0 }, &.{ colour, sm }));
        note("halo: Wear grow over {d:.4} of the picture in the stain's colour\n", .{rr});
    }
    // runs down: at 1:1 the darkest fifth stays alike further down than across
    const nc = C.pic.n;
    const thc = R.quantile(C.pic.t, 0.2);
    const mc = alloc.alloc(f32, nc * nc) catch unreachable;
    defer alloc.free(mc);
    for (0..nc * nc) |i| mc[i] = if (C.pic.t[i] < thc) 1 else 0;
    const mcb = R.blur(mc, nc, 4);
    defer alloc.free(mcb);
    const la = R.corrLength(mcb, nc, false);
    const ld = R.corrLength(mcb, nc, true);
    note("drips: at 1:1 the darkest fifth stays alike {d:.0} pixels down, {d:.0} across (runs from 1.3 times)\n", .{ ld, la });
    if (ld >= 1.3 * la and ld - la >= 3 and !refused(cx.off, "drips")) {
        const len = @min(0.25, 3.0 * (ld - la) / @as(f32, @floatFromInt(cx.N)));
        colour = F.add(g, F.mk(F.K_WEAR, &.{ 1, 2, 0.01, len, 0.2, 0.7, 0.5, F.colourWord(halo_c), @as(f64, @floatFromInt(cells)) * 4, 0.6, 35, 1.0 }, &.{ colour, sm }));
        note("drips: Wear drips {d:.3} of the picture long from the spots\n", .{len});
    }
    // the spots themselves: the same instances as the mask, the spot's colour, darker granules at the core; milestone
    // 2d: their softness and how much they are laid (blend) read from the darkest fifth's edges and contrast
    var soft: f32 = 0.5;
    var opac: f32 = 1;
    if (cx.marks_soft) {
        const pe = F.markEdge(H.pic.t, n);
        var bd: f32 = 1e9;
        for ([_]f32{ 0.5, 0.7, 0.85, 1.0 }) |sf| {
            for ([_]f32{ 1, 0.75, 0.5 }) |op| {
                const keep = g.n;
                const cand = F.add(g, scatter2o(colour, cells, 0.9, size, 0.8, spot_c, 0.25, 31, -0.2, sf, asp, 8, clu, 0.6, 3, -0.45, op));
                var dd = drawIn(g, cand, H);
                g.n = keep;
                const k = keyOf(H, dd.rgb, n);
                dd.free();
                const de = F.markEdge(k, n);
                alloc.free(k);
                const d = @abs(@log((de[0] + 1e-4) / (pe[0] + 1e-4))) + @abs(@log((de[1] + 1e-4) / (pe[1] + 1e-4)));
                note("  spots softness {d:.2}, laid {d:.2}: edges {d:.3}, contrast {d:.2} (the picture's {d:.3}, {d:.2})\n", .{ sf, op, de[0], de[1], pe[0], pe[1] });
                if (d < bd) {
                    bd = d;
                    soft = sf;
                    opac = op;
                }
            }
        }
        note("spots: softness {d:.2}, laid {d:.2} (read: the darkest fifth's edges and contrast)\n", .{ soft, opac });
    }
    colour = F.add(g, scatter2o(colour, cells, 0.9, size, 0.8, spot_c, 0.25, 31, -0.2, soft, asp, 8, clu, 0.6, 3, -0.45, opac));
    cx.root = colour;
    cx.spots = true;
    push(cx, "+ spots that gather, their halo and runs (Ramp on the first material, Scatter, Wear)");
}

// ---------------------------------------------------------------- furrows

fn furrowsLayer(cx: *Ctx, C: *const View) void {
    const g = cx.g;
    const n = C.pic.n;
    if (cx.st.ok) return;
    if (refused(cx.off, "furrows")) {
        note("furrows: left off by eye (off=furrows)\n", .{});
        return;
    }
    // the dark lines at 1:1: the detail (blurred by 1, less its blur of 12) a spread darker; their runs across and down
    const dark = darkLines(C.pic.t, n);
    defer alloc.free(dark);
    const ra = runs(dark, n, true);
    const rdn = runs(dark, n, false);
    var dd = drawIn(g, cx.root, C);
    const kd = keyOf(C, dd.rgb, n);
    dd.free();
    defer alloc.free(kd);
    const ddk = darkLines(kd, n);
    defer alloc.free(ddk);
    const da = runs(ddk, n, true);
    const ddn = runs(ddk, n, false);
    const el_pic = @max(rdn[1] / ra[1], ra[1] / rdn[1]);
    const el_dr = @max(ddn[1] / da[1], da[1] / ddn[1]);
    note("furrows: at 1:1 the dark lines run {d:.1} pixels down and {d:.1} across ({d:.2} times longer one way; drawn {d:.2}), {d:.2} of them across a row (furrows from 1.5 times, and 1.2 times the drawn)\n", .{ rdn[1], ra[1], el_pic, el_dr, ra[0] });
    if (el_pic < 1.5 or el_pic < 1.2 * el_dr) {
        note("furrows: none\n", .{});
        return;
    }
    const down = rdn[1] > ra[1];
    const N: f32 = @floatFromInt(cx.N);
    const scale = N / 2 / @as(f32, @floatFromInt(n));
    // one furrow per cell border: as many cells across as dark runs per row (on the whole), as long as a run
    const per_line = if (down) ra[0] else rdn[0];
    const run_long = (if (down) rdn[1] else ra[1]) * scale;
    const run_wide = (if (down) ra[1] else rdn[1]) * scale;
    const across: i32 = @max(2, @as(i32, @intFromFloat(per_line * N / (@as(f32, @floatFromInt(n)) * scale))));
    // the cells as long as the lines are elongated (squared: a run of the threshold breaks a furrow into pieces)
    const along: i32 = @max(1, @as(i32, @intFromFloat(@as(f32, @floatFromInt(across)) / (1.5 * el_pic * el_pic))));
    _ = run_long;
    const nx: i32 = if (down) across else along;
    const ny: i32 = if (down) along else across;
    const mean_side = N / @sqrt(@as(f32, @floatFromInt(nx * ny)));
    const width0 = @min(0.5, 0.5 * run_wide / mean_side);
    var best_w = width0;
    var best_d: f32 = 1e9;
    var share_pic: f32 = 0;
    for (dark) |v| share_pic += if (v) 1 else 0;
    share_pic /= @floatFromInt(n * n);
    const crack_c = F.colourAtRank(&C.pic, 0.03);
    const face_c = F.colourAtRank(&C.pic, 0.5);
    var ratio: [3]f32 = undefined;
    inline for (0..3) |q| ratio[q] = @min(1.0, crack_c[q] / @max(0.01, face_c[q]));
    for ([_]f32{ 0.5, 1, 1.6, 2.5 }) |kw| {
        const keep = g.n;
        const lx = furrowNodes(g, cx.root, nx, ny, width0 * kw, ratio);
        var d2 = drawIn(g, lx, C);
        g.n = keep;
        const k2 = keyOf(C, d2.rgb, n);
        d2.free();
        const dk2 = darkLines(k2, n);
        alloc.free(k2);
        var sh: f32 = 0;
        for (dk2) |v| sh += if (v) 1 else 0;
        sh /= @floatFromInt(n * n);
        const r2 = runs(dk2, n, !down);
        alloc.free(dk2);
        note("  furrow width {d:.3}: {d:.3} of the picture in dark lines, runs {d:.1} pixels long (the picture's {d:.3}, {d:.1})\n", .{ width0 * kw, sh, r2[1], share_pic, if (down) rdn[1] else ra[1] });
        if (F.absDiff(sh, share_pic) < best_d) {
            best_d = F.absDiff(sh, share_pic);
            best_w = width0 * kw;
        }
    }
    cx.root = furrowNodes(g, cx.root, nx, ny, best_w, ratio);
    note("furrows: Cells version 2 cracks, {d} across by {d} down, width {d:.3} wandering 0.8, darkened to the picture's darkest\n", .{ nx, ny, best_w });
    push(cx, "+ furrows (Cells, Ramp, Layer)");
}

/// pixels of dark lines: the detail (blurred by 5, less its blur of 32) 0.8 of a spread darker (set on seven
/// pictures: the bark's lines run 1.78 times longer down than across, the six others 1.01 to 1.31)
fn darkLines(t: []const f32, n: usize) []bool {
    const a = R.blur(t, n, 5);
    defer alloc.free(a);
    const b = R.blur(a, n, 32);
    defer alloc.free(b);
    var sd: f64 = 0;
    for (0..n * n) |i| sd += (a[i] - b[i]) * (a[i] - b[i]);
    const s: f32 = @floatCast(@sqrt(sd / @as(f64, @floatFromInt(n * n))));
    const m = alloc.alloc(bool, n * n) catch unreachable;
    for (0..n * n) |i| m[i] = a[i] - b[i] < -0.8 * s;
    return m;
}

fn furrowNodes(g: *P.Graph, root: usize, nx: i32, ny: i32, width: f32, ratio: [3]f32) usize {
    const mx: f64 = @floatFromInt(@max(nx, ny));
    const kx = F.add(g, F.mk(F.K_CELLS, &.{ 2, 0, @floatFromInt(nx), @floatFromInt(ny), 0.7, width, 0.15 / mx, mx * 2, 41, 0.5, 0.8, mx }, &.{}));
    const kr = F.add(g, F.mk(F.K_RAMP, &.{ 1, 2, 0, F.colourWord(ratio), 1, F.colourWord(.{ 1, 1, 1 }), 1, 0xffffffff, 1, 0xffffffff, 1, 0xffffffff, 1, 0xffffffff, 1, 0xffffffff, 1, 0xffffffff }, &.{kx}));
    return F.add(g, F.mk(F.K_LAYER, &.{ 1, 1, -1, -0.5, 1, 4, 0.7 }, &.{ root, kr, kx }));
}

// ---------------------------------------------------------------- knots, stones, pits

fn knotsLayer(cx: *Ctx, H: *const View) void {
    const g = cx.g;
    const n = H.pic.n;
    if (cx.st.ok) return;
    if (cx.spots) {
        note("knots: the dark marks are the spots already\n", .{});
        return;
    }
    if (refused(cx.off, "knots")) {
        note("knots: left off by eye (off=knots)\n", .{});
        return;
    }
    const b = marks(H.pic.t, n, 48, 2.2, true, 300, 12000, null);
    note("knots: {d} large dark compact marks of about {d:.1} pixels in the whole at {d} (knots: 3 to 40, of 300 pixels or more each)\n", .{ b.count, b.radius, n });
    if (b.count < 3 or b.count > 40) return;
    const cells: i32 = @max(2, @as(i32, @intFromFloat(@sqrt(@as(f32, @floatFromInt(b.count)) / 0.3))));
    const cellpx = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(cells));
    const asp = @min(2.5, @max(0.6, b.down));
    const size = @min(0.9 / (asp * 1.3), @max(0.02, b.radius / cellpx));
    const col = F.colourAtRank(&H.pic, 0.03);
    cx.root = F.add(g, scatter2(cx.root, cells, 0.3, size, 0.3, col, 0.2, 43, -0.4, 0.6, asp, 4, 0, 0.3, 3, -0.4));
    note("knots: Scatter version 2, {d} cells across at a density of 0.3, rough dark ellipses {d:.1} times as long down\n", .{ cells, asp });
    push(cx, "+ knots (Scatter)");
}

const MarkArgs = struct { r: usize, k: f32, dark: bool, min: usize, max: usize };

/// the light on marks: their sides lit one way in the picture; a Shade whose depth makes the drawing's marks lit as
/// much (the same reading on the drawing)
fn lightOn(cx: *Ctx, ma: MarkArgs, reading: [2]f32, v: *const View) void {
    const g = cx.g;
    const sg: f32 = if (ma.dark) -1 else 1;
    const len = @sqrt(reading[0] * reading[0] + reading[1] * reading[1]);
    if (len <= 0.3) {
        note("  light on them: none read (the sides differ by {d:.3})\n", .{len});
        return;
    }
    const lx = -sg * reading[0] / len * 0.6;
    const ly = -sg * reading[1] / len * 0.6;
    var best: f32 = 0.004;
    var bd: f32 = 1e9;
    for ([_]f32{ 0.001, 0.002, 0.004, 0.008 }) |dp| {
        const keep = g.n;
        const sx = F.add(g, F.mk(F.K_SHADE, &.{ 1, lx, ly, 0.8, dp, 0.8 }, &.{cx.root}));
        var ds = drawIn(g, sx, v);
        g.n = keep;
        const k = keyOf(v, ds.rgb, v.pic.n);
        const r = marks(k, v.pic.n, ma.r, ma.k, ma.dark, ma.min, ma.max, null);
        alloc.free(k);
        ds.free();
        const got = @sqrt(r.left_light * r.left_light + r.up_light * r.up_light);
        note("  light depth {d:.3}: the drawn marks' sides differ by {d:.3} (the picture's {d:.3})\n", .{ dp, got, len });
        if (F.absDiff(got, len) < bd) {
            bd = F.absDiff(got, len);
            best = dp;
        }
    }
    cx.root = F.add(g, F.mk(F.K_SHADE, &.{ 1, lx, ly, 0.8, best, 0.8 }, &.{cx.root}));
    note("  light on them: from {d:.2}, {d:.2}, depth {d:.3} (Shade)\n", .{ lx, ly, best });
}

fn stonesLayer(cx: *Ctx, H: *const View) void {
    const g = cx.g;
    const n = H.pic.n;
    if (cx.st.ok) return;
    if (refused(cx.off, "stones")) {
        note("stones: left off by eye (off=stones)\n", .{});
        return;
    }
    var am = axisMarks(H, false, 0.2);
    defer alloc.free(am.region);
    defer am.comps.deinit(alloc);
    note("stones: the lightest fifth of the whole at {d}, joined, lies {d:.2} in {d} compact marks of about {d:.1} pixels, {d:.2} spreads lighter than the rest (stones: 0.45 in 8 or more, 5 pixels, 2.2 spreads)\n", .{ n, am.share, am.comps.items.len, am.rad, am.contrast });
    if (am.share < 0.45 or am.comps.items.len < 8 or am.rad < 5 or am.contrast < 2.2) return;
    const cnt: f32 = @floatFromInt(am.comps.items.len);
    const cells: i32 = @max(2, @as(i32, @intFromFloat(@sqrt(cnt / 0.5))));
    const cellpx = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(cells));
    const asp = @min(2.5, @max(0.5, am.down));
    const size = @min(0.6, @max(0.02, am.rad / cellpx));
    const col = F.meanColour(&H.pic, am.region);
    cx.root = F.add(g, scatter2(cx.root, cells, 0.5, size, 0.45, col, 0.15, 47, 0.5, 0.12, asp, 8, 0, 0.45, 2, 0.1));
    note("stones: Scatter version 2, {d} cells across, rough light raised discs in {x:0>6}\n", .{ cells, @as(u32, @intFromFloat(F.colourWord(col))) & 0xffffff });
    const b = marks(H.pic.t, n, 24, 1.3, false, 80, 6000, null);
    lightOn(cx, .{ .r = 24, .k = 1.3, .dark = false, .min = 80, .max = 6000 }, .{ b.left_light, b.up_light }, H);
    push(cx, "+ stones (Scatter, Shade)");
}

fn pitsLayer(cx: *Ctx, C: *const View) void {
    const g = cx.g;
    const n = C.pic.n;
    if (refused(cx.off, "pits")) {
        note("pits: left off by eye (off=pits)\n", .{});
        return;
    }
    // on a structure the pits are read on its faces only
    var tb = C.pic.t;
    var own = false;
    var fsel: ?[]bool = null;
    defer if (fsel) |f| alloc.free(f);
    if (cx.st.ok) {
        var ds = drawIn(g, cx.st.tiles, C);
        defer ds.free();
        const bt = R.blur(C.pic.t, n, 6);
        defer alloc.free(bt);
        const t2 = alloc.alloc(f32, n * n) catch unreachable;
        const f = alloc.alloc(bool, n * n) catch unreachable;
        for (0..n * n) |i| {
            f[i] = ds.h[i] > 0.85;
            t2[i] = if (f[i]) C.pic.t[i] else bt[i];
        }
        tb = t2;
        own = true;
        fsel = f;
    }
    defer if (own) alloc.free(tb);
    const b = marks(tb, n, 12, 2.5, true, 40, 1500, null);
    var dd = drawIn(g, cx.root, C);
    const kd = keyOf(C, dd.rgb, n);
    dd.free();
    defer alloc.free(kd);
    const bd = marks(kd, n, 12, 2.5, true, 40, 1500, null);
    note("pits: in the whole at {d} {d} dark compact marks of about {d:.1} pixels, drawn {d} (pits: 3 or more, of 40 pixels or more each, twice the drawn)\n", .{ n, b.count, b.radius, bd.count });
    if (b.count < 3 or b.count < 2 * bd.count) return;
    const cells: i32 = @max(2, @as(i32, @intFromFloat(@sqrt(@as(f32, @floatFromInt(b.count)) / 0.5))));
    const cellpx = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(cells));
    const size = @min(0.45, @max(0.01, b.radius / cellpx));
    const col = if (fsel) |f| F.colourAtRankSel(&C.pic, 0.03, f) else F.colourAtRank(&C.pic, 0.03);
    const asp = @min(3.0, @max(0.5, b.down));
    cx.root = F.add(g, scatter2(cx.root, cells, 0.5, size, 0.5, col, 0.2, 53, -0.5, 0.35, asp, 8, 0, 0.35, 3, -0.3));
    note("pits: Scatter version 2, {d} cells across, rough sunk discs\n", .{cells});
    if (cx.st.ok and cx.joints_full) {
        // milestone 2d: with the joints read at 1:1 the pieces' edges are narrow, and the light read on the pits
        // darkens them into black outlines (by eye); on such a structure the pits stay colour only
        note("  light on them: not laid on a structure whose joints were read at 1:1 (the pieces' narrow edges went black)\n", .{});
        push(cx, "+ pits (Scatter)");
        return;
    }
    lightOn(cx, .{ .r = 12, .k = 2.5, .dark = true, .min = 40, .max = 1500 }, .{ b.left_light, b.up_light }, C);
    push(cx, "+ pits (Scatter, Shade)");
}
