//! The WebAssembly procedure player of Procedural Texture Rendering (ORDER 537): the modern operators only.
//!
//! It draws a procedure written in the p2p script (one operator per line: `ID OPERATOR INPUTS WORDS...`, an `out ID`
//! line) at a size, through a window of the picture, as `p2p render SCRIPT OUT.ppm EXPONENT window=X,Y,SIDE` does
//! (ORDER 508's fitter, p2p.zig: drawCanvas, drawQuad, drawGrid, drawStack, cropRgba), with the operators' own files
//! (ops/*.zig, unchanged) and nothing else: no werkkzeug3 bridge, no fonts, no fitter. A procedure that names another
//! operator is refused with a sentence. Our code, BSD 2-clause.
//!
//! Built for wasm32-wasi with the C library only for its allocator (ops/wear.zig takes std.heap.c_allocator); the
//! module imports nothing. The page calls ptr_alloc, writes the script, calls ptr_render and reads side*side*3 bytes
//! of red, green and blue at the returned place, or the sentence at ptr_error.
const std = @import("std");
const c = @import("ops/common.zig");

const noise = @import("ops/noise.zig");
const cells = @import("ops/cells.zig");
const tiles = @import("ops/tiles.zig");
const ramp = @import("ops/ramp.zig");
const layer = @import("ops/layer.zig");
const shade = @import("ops/shade.zig");
const scatter = @import("ops/scatter.zig");
const wear = @import("ops/wear.zig");
const tint = @import("ops/tint.zig");
const quad = @import("ops/quad.zig");
const grid = @import("ops/grid.zig");
const stack = @import("ops/stack.zig");

// the order of ORDER 508's modern.zig: Scatter is 6 (its second input is a seed of its own size), Quad 9, Grid 10, Stack 11
const list = .{ noise, cells, tiles, ramp, layer, shade, scatter, wear, tint, quad, grid, stack };
const K_SCATTER = 6;
const K_QUAD = 9;
const K_GRID = 10;
const K_STACK = 11;

const NW = 28;
const MAXIN = 16;
const MAXN = 220;
const alloc = std.heap.c_allocator;

const Node = struct {
    op: u8 = 0,
    nin: u8 = 0,
    in: [MAXIN]u8 = [_]u8{0} ** MAXIN,
    nw: u8 = 0,
    w: [NW]u32 = [_]u32{0} ** NW,
};

const Graph = struct {
    n: usize = 0,
    root: usize = 0,
    nodes: [MAXN]Node = undefined,

    /// drop the operators the result does not use
    fn prune(g: *Graph) void {
        var used = [_]bool{false} ** MAXN;
        used[g.root] = true;
        var i = g.root + 1;
        while (i > 0) {
            i -= 1;
            if (!used[i]) continue;
            const nd = g.nodes[i];
            for (nd.in[0..nd.nin]) |v| used[v] = true;
        }
        var map: [MAXN]u8 = undefined;
        var k: usize = 0;
        for (0..g.n) |j| {
            if (!used[j]) continue;
            map[j] = @intCast(k);
            var nd = g.nodes[j];
            for (nd.in[0..nd.nin]) |*v| v.* = map[v.*];
            g.nodes[k] = nd;
            k += 1;
        }
        g.root = map[g.root];
        g.n = k;
    }
};

const Win = struct { x: f32 = 0, y: f32 = 0, s: f32 = 1 };

/// A picture: four 15-bit channels per pixel (blue, green, red, alpha), w by w pixels with a margin of m on each side
const Bm = struct {
    d: []u16,
    w: usize,
    m: usize,
};

var err_buf: [400]u8 = undefined;
var err_len: usize = 0;
const Fail = error{Refused};

fn fail(comptime fmt: []const u8, args: anytype) Fail {
    const s = std.fmt.bufPrint(&err_buf, fmt, args) catch "the procedure does not draw";
    err_len = s.len;
    return error.Refused;
}

fn nameOf(k: usize) []const u8 {
    inline for (list, 0..) |m, i| {
        if (i == k) return m.name;
    }
    unreachable;
}
fn inputsOf(k: usize) u8 {
    inline for (list, 0..) |m, i| {
        if (i == k) return m.inputs;
    }
    unreachable;
}
fn wordsFor(k: usize, ver: u32) usize {
    inline for (list, 0..) |m, i| {
        if (i == k) {
            if (@hasDecl(m, "wordCount")) return m.wordCount(ver);
            return m.params.len;
        }
    }
    unreachable;
}
fn marginOf(k: usize, w: []const u32) f32 {
    inline for (list, 0..) |m, i| {
        if (i == k) return m.margin(w);
    }
    unreachable;
}
fn wordsOf(nd: *const Node) usize {
    return @min(@as(usize, NW), wordsFor(nd.op, nd.w[0]));
}
fn opIndex(name: []const u8) ?u8 {
    inline for (list, 0..) |m, i| {
        if (std.mem.eql(u8, m.name, name)) return @intCast(i);
    }
    return null;
}

fn newBm(w: usize, m: usize) Fail!Bm {
    const d = alloc.alloc(u16, w * w * 4) catch return fail("no memory for a {d}x{d} picture", .{ w, w });
    @memset(d, 0);
    return .{ .d = d, .w = w, .m = m };
}
fn freeBm(b: ?Bm) void {
    if (b) |x| alloc.free(x.d);
}

fn parseScript(text: []const u8, g: *Graph) Fail!void {
    g.n = 0;
    g.root = 0;
    var names: [MAXN][]const u8 = undefined;
    var lines = std.mem.tokenizeAny(u8, text, "\r\n");
    var have_out = false;
    while (lines.next()) |line| {
        var t = std.mem.tokenizeAny(u8, line, " \t");
        const id = t.next() orelse continue;
        if (id[0] == '#') continue;
        if (std.mem.eql(u8, id, "out")) {
            const nm = t.next() orelse return fail("out line without a name", .{});
            for (names[0..g.n], 0..) |x, i| {
                if (std.mem.eql(u8, x, nm)) {
                    g.root = i;
                    have_out = true;
                }
            }
            continue;
        }
        const opn = t.next() orelse return fail("{s}: no operator", .{id});
        const op = opIndex(opn) orelse return fail("{s}: operator {s} is not one this player draws (it draws the modern operators: Noise, Cells, Tiles, Ramp, Layer, Shade, Scatter, Wear, Tint, Quad, Grid, Stack)", .{ id, opn });
        var nd = Node{ .op = op };
        const ins = t.next() orelse return fail("{s}: no inputs", .{id});
        if (!std.mem.eql(u8, ins, "-")) {
            var ii = std.mem.tokenizeAny(u8, ins, ",");
            while (ii.next()) |nm| {
                var found = false;
                for (names[0..g.n], 0..) |x, i| {
                    if (std.mem.eql(u8, x, nm)) {
                        if (nd.nin >= MAXIN) return fail("{s}: more than {d} inputs", .{ id, MAXIN });
                        nd.in[nd.nin] = @intCast(i);
                        nd.nin += 1;
                        found = true;
                        break;
                    }
                }
                if (!found) return fail("{s}: input {s} is not defined above it", .{ id, nm });
            }
        }
        while (t.next()) |hx| {
            if (std.mem.startsWith(u8, hx, "s=")) return fail("{s}: a string belongs to a Text operator, which this player does not draw", .{id});
            if (nd.nw < NW) {
                nd.w[nd.nw] = std.fmt.parseInt(u32, hx, 16) catch return fail("{s}: bad word {s}", .{ id, hx });
                nd.nw += 1;
            }
        }
        if (g.n >= MAXN) return fail("more than {d} operators", .{MAXN});
        names[g.n] = id;
        g.nodes[g.n] = nd;
        g.n += 1;
    }
    if (!have_out) return fail("no out line", .{});
}

/// Draw modern operator k on the canvas c.cv (ORDER 508's modern.apply, on our own pictures)
fn apply(k: usize, w: []const u32, inp: []const Bm) Fail!Bm {
    var pins: [MAXIN]c.Pix = undefined;
    for (inp, 0..) |p, i| {
        pins[i] = .{ .d = p.d.ptr, .w = p.w, .h = p.w };
        const is_seed = (k == K_SCATTER and i == 1);
        if (!is_seed and (p.w != c.cv.w or p.w != c.cv.h))
            return fail("{s}: input {d} is {d}x{d}, the canvas {d}x{d}", .{ nameOf(k), i + 1, p.w, p.w, c.cv.w, c.cv.h });
    }
    if (inp.len < inputsOf(k)) return fail("{s} takes {d} input(s), the graph gives {d}", .{ nameOf(k), inputsOf(k), inp.len });
    if (w[0] == 0) return fail("{s} has no version word (the first word must say the version)", .{nameOf(k)});
    const o = try newBm(c.cv.w, c.cv.m);
    const po = c.Pix{ .d = o.d.ptr, .w = o.w, .h = o.w };
    var r: error{Refused}!void = {};
    inline for (list, 0..) |m, i| {
        if (i == k) r = m.draw(po, pins[0..inp.len], w);
    }
    r catch {
        freeBm(o);
        return fail("{s}", .{c.err_buf[0..c.err_len]});
    };
    return o;
}

/// Draw every operator up to the root on the canvas c.cv, as p2p's draw does; a picture is freed after its last reader
fn draw(g: *const Graph) Fail!Bm {
    var bm: [MAXN]?Bm = [_]?Bm{null} ** MAXN;
    var last: [MAXN]usize = undefined;
    for (0..g.root + 1) |i| last[i] = i;
    for (0..g.root + 1) |i| {
        const nd = &g.nodes[i];
        for (nd.in[0..nd.nin]) |v| last[v] = i;
    }
    last[g.root] = g.root + 1;
    errdefer for (bm[0 .. g.root + 1]) |b| freeBm(b);
    for (0..g.root + 1) |i| {
        const nd = &g.nodes[i];
        var w: [32]u32 = [_]u32{0} ** 32;
        const nk = wordsOf(nd);
        for (0..nk) |p| w[p] = nd.w[p];
        var inp: [MAXIN]Bm = undefined;
        for (nd.in[0..nd.nin], 0..) |v, k| inp[k] = bm[v].?;
        bm[i] = try apply(nd.op, w[0..nk], inp[0..nd.nin]);
        for (0..i + 1) |j| {
            if (bm[j] != null and last[j] <= i) {
                freeBm(bm[j]);
                bm[j] = null;
            }
        }
    }
    const out = bm[g.root].?;
    bm[g.root] = null;
    return out;
}

fn isWhole(op: u8) bool {
    return op == K_QUAD or op == K_GRID or op == K_STACK;
}

/// the margin a procedure needs on a canvas whose pixels are pxs parts of its own picture
fn marginFor(sub: *const Graph, pxs: f32) usize {
    var reach: f32 = 0;
    var any = false;
    for (sub.nodes[0 .. sub.root + 1]) |*nd| {
        const r = marginOf(nd.op, nd.w[0..wordsOf(nd)]);
        if (r > 0) any = true;
        reach += r; // neighbourhoods chained one after another add up
    }
    return if (any) @as(usize, @intFromFloat(@ceil(reach / pxs))) + 2 else 0;
}

fn part(g: *const Graph, q: usize) Fail!*Graph {
    const sub = alloc.create(Graph) catch return fail("out of memory", .{});
    sub.* = g.*;
    sub.root = g.nodes[g.root].in[q];
    sub.prune();
    return sub;
}

fn drawCanvas(g: *const Graph, side: usize, win: Win, maxoct: u32) Fail!Bm {
    const rop = g.nodes[g.root].op;
    if (rop == K_QUAD) return drawTiles(g, side, win, maxoct, 2, 2, 2.0, K_QUAD);
    if (rop == K_GRID) {
        const rt = &g.nodes[g.root];
        const cols: usize = @intCast(rt.w[1]);
        const rows: usize = @intCast(rt.w[2]);
        if (cols < 1 or rows < 1 or cols > 4 or rows > 4 or rt.nin != cols * rows)
            return fail("a Grid of {d} by {d} tiles takes {d} procedures, the graph gives {d}", .{ cols, rows, cols * rows, rt.nin });
        return drawTiles(g, side, win, maxoct, cols, rows, grid.scaleOf(cols, rows), K_GRID);
    }
    if (rop == K_STACK) return drawStack(g, side, win, maxoct);
    for (g.nodes[0..g.root]) |nd| {
        if (isWhole(nd.op)) return fail("a {s} is the procedure's last operator (it draws whole procedures, each on its own canvas)", .{nameOf(nd.op)});
    }
    var m = marginFor(g, win.s / @as(f32, @floatFromInt(side)));
    m = (m + 1) & ~@as(usize, 1); // even, so a canvas of a power-of-two side stays a multiple of four pixels
    c.cv = .{ .w = side + 2 * m, .h = side + 2 * m, .m = m, .wx = win.x, .wy = win.y, .ws = win.s, .maxoct = maxoct };
    return draw(g);
}

/// A Quad's four inputs or a Grid's cols by rows, each a procedure drawn on its own canvas (input q at the place
/// sc (x - column / cols), sc (y - row / rows)), every canvas of one side and margin; then the operator lays them together
fn drawTiles(g: *const Graph, side: usize, win: Win, maxoct: u32, cols: usize, rows: usize, sc: f32, k: usize) Fail!Bm {
    const rt = &g.nodes[g.root];
    const nt = cols * rows;
    if (rt.nin != nt) return fail("a {s} takes {d} procedures, the graph gives {d}", .{ nameOf(k), nt, rt.nin });
    var subs: [grid.MAXT]?*Graph = [_]?*Graph{null} ** grid.MAXT;
    defer for (subs) |s| {
        if (s) |x| alloc.destroy(x);
    };
    const pxs = sc * win.s / @as(f32, @floatFromInt(side));
    var m: usize = 0;
    for (0..nt) |q| {
        const sub = try part(g, q);
        subs[q] = sub;
        for (sub.nodes[0 .. sub.root + 1]) |nd| {
            if (isWhole(nd.op)) return fail("a {s}'s inputs hold a {s} (one per procedure, its last operator; a Stack may lay them)", .{ nameOf(k), nameOf(nd.op) });
        }
        m = @max(m, marginFor(sub, pxs));
    }
    m = (m + 1) & ~@as(usize, 1);
    const cw = side + 2 * m;
    var parts: [grid.MAXT]?Bm = [_]?Bm{null} ** grid.MAXT;
    defer for (parts) |p| freeBm(p);
    const fc: f32 = @floatFromInt(cols);
    const fr: f32 = @floatFromInt(rows);
    for (0..nt) |q| {
        const col: f32 = @floatFromInt(q % cols);
        const row: f32 = @floatFromInt(q / cols);
        // the Quad's places are written as p2p writes them (2x - column), the Grid's as it writes those
        if (k == K_QUAD) {
            c.cv = .{ .w = cw, .h = cw, .m = m, .wx = 2.0 * win.x - col, .wy = 2.0 * win.y - row, .ws = 2.0 * win.s, .maxoct = maxoct };
        } else {
            c.cv = .{ .w = cw, .h = cw, .m = m, .wx = sc * (win.x - col / fc), .wy = sc * (win.y - row / fr), .ws = sc * win.s, .maxoct = maxoct };
        }
        parts[q] = try draw(subs[q].?);
    }
    c.cv = .{ .w = cw, .h = cw, .m = m, .wx = win.x, .wy = win.y, .ws = win.s, .maxoct = maxoct };
    var w: [32]u32 = [_]u32{0} ** 32;
    const nk = wordsOf(rt);
    for (0..nk) |p| w[p] = rt.w[p];
    var inp: [grid.MAXT]Bm = undefined;
    for (0..nt) |q| inp[q] = parts[q].?;
    return apply(k, w[0..nk], inp[0..nt]);
}

/// A Stack's inputs, each a whole procedure drawn over the same window, their inner pixels copied to canvases without
/// a margin; then the Stack lays them, the bottom one first
fn drawStack(g: *const Graph, side: usize, win: Win, maxoct: u32) Fail!Bm {
    const rt = &g.nodes[g.root];
    if (rt.nin < 2 or rt.nin > stack.MAXL) return fail("a Stack lays two to four procedures, the graph gives {d}", .{rt.nin});
    var parts: [stack.MAXL]?Bm = [_]?Bm{null} ** stack.MAXL;
    defer for (parts) |p| freeBm(p);
    for (0..rt.nin) |q| {
        const sub = try part(g, q);
        defer alloc.destroy(sub);
        for (sub.nodes[0 .. sub.root + 1]) |nd| {
            if (nd.op == K_STACK) return fail("a Stack's procedure {d} holds another Stack (one Stack per procedure, its last operator)", .{q + 1});
        }
        const bm = try drawCanvas(sub, side, win, maxoct);
        defer freeBm(bm);
        const cp = try newBm(side, 0);
        for (0..side) |j| {
            const a = ((j + bm.m) * bm.w + bm.m) * 4;
            @memcpy(cp.d[j * side * 4 .. (j + 1) * side * 4], bm.d[a .. a + side * 4]);
        }
        parts[q] = cp;
    }
    c.cv = .{ .w = side, .h = side, .m = 0, .wx = win.x, .wy = win.y, .ws = win.s, .maxoct = maxoct };
    var w: [32]u32 = [_]u32{0} ** 32;
    const nk = wordsOf(rt);
    for (0..nk) |p| w[p] = rt.w[p];
    var inp: [stack.MAXL]Bm = undefined;
    for (0..rt.nin) |q| inp[q] = parts[q].?;
    return apply(K_STACK, w[0..nk], inp[0..rt.nin]);
}

fn render(text: []const u8, side: usize, win: Win) Fail![]u8 {
    if (side < 1 or side > 4096 or (side & (side - 1)) != 0) return fail("the side {d} is not a power of two up to 4096", .{side});
    const g = alloc.create(Graph) catch return fail("out of memory", .{});
    defer alloc.destroy(g);
    try parseScript(text, g);
    const bm = try drawCanvas(g, side, win, 99);
    defer freeBm(bm);
    const out = alloc.alloc(u8, side * side * 3) catch return fail("no memory for the result", .{});
    // 8 bits the way p2p's wzb_rgba gives them: the 15-bit channel shifted by 7, red first
    for (0..side) |j| {
        for (0..side) |i| {
            const q = bm.d[4 * ((j + bm.m) * bm.w + i + bm.m) ..];
            const o = 3 * (j * side + i);
            inline for (0..3) |ch| {
                const x = q[2 - ch] >> 7;
                out[o + ch] = if (x > 255) 255 else @intCast(x);
            }
        }
    }
    return out;
}

export fn ptr_alloc(n: u32) ?[*]u8 {
    const m = alloc.alloc(u8, @max(n, 1)) catch return null;
    return m.ptr;
}
export fn ptr_free(p: ?[*]u8, n: u32) void {
    if (p) |x| alloc.free(x[0..@max(n, 1)]);
}
/// Draw the script at side pixels through the window (wx, wy, ws): the place of side*side*3 bytes (free it with
/// ptr_free), or null with a sentence at ptr_error
export fn ptr_render(script: [*]const u8, len: u32, side: u32, wx: f32, wy: f32, ws: f32) ?[*]u8 {
    err_len = 0;
    const out = render(script[0..len], side, .{ .x = wx, .y = wy, .s = ws }) catch return null;
    return out.ptr;
}
export fn ptr_error() [*]const u8 {
    return &err_buf;
}
export fn ptr_error_len() u32 {
    return @intCast(err_len);
}
/// the version of this player's interface
export fn ptr_version() u32 {
    return 1;
}
