//! p2p: procedures from pixels.
//!
//! From a texture's pixels, find a procedure made of werkkzeug3's texture operators that draws it:
//! the way .kkrieger's textures were made, run backwards. No text and no model is an input: only the
//! pixels, and the prior (which operator chains and which values .kkrieger's artists really used,
//! read from kkrieger.k by prior.py).
//!
//! The method (see the skill page for the sources):
//!   1. read the picture, the artist's order backwards: its two colours and the grey picture between
//!      them; whether it repeats, and the one cell under the repeats with the shapes in it; which octaves
//!      of noise it holds and how strong, from the strength of detail per scale;
//!   2. build the procedure in the artist's idioms from that reading: a Perlin between the two colours;
//!      Flat, GlowRect and Transform for the repeated shape, multiplied in; a real Normals and Bump from
//!      .kkrieger for the relief; more noises over the colour layer while they pay for their bytes;
//!   3. tune every value by direct search, one value at a time (Hooke and Jeeves 1961): whole numbers by
//!      trying the values artists used (every seed for Perlin), decimals and colours by steps that halve;
//!      no derivative is needed, so werkkzeug's own integer code is the renderer;
//!   4. do it at 128 pixels first, then at each finer size up to the picture's own;
//!   5. every kept step is a rung: the procedure up to there is a thinner version of the final one.
//! What adds structure is gated by a reading of its own, measured and never searched: Cell for flat
//! hard-edged patches, Mask for a colour off the main colour axis, Twirl for rings, a mirror for a level
//! pair of rings that agree turned left to right, the bond for rows that agree moved sideways. One run
//! builds one allowed structure (structure=NAME); which of the finished drawings is right is chosen by eye.
//! Joints are .kkrieger's outline trick (the Blur of the shape minus the shape), a bond is a TransformMul.
//! Free moves taken at random from the prior (grow=N) are kept as an option; they are off by default.
//! The measure the search steers by is internal (where light and dark lie, the spread of small filters'
//! answers per scale, the spread of the colours); it is not the verdict: the result is judged by eye.
//!
//! The operators are Farbrausch's own code (wzbridge.cpp over werkkzeug4's wz3_bitmap_code.cpp).
const std = @import("std");

extern "c" fn wzb_init() void;
extern "c" fn wzb_set_limit(bytes: usize) void;
extern "c" fn wzb_apply(name: [*:0]const u8, w: [*]const u32, nin: c_int, inp: [*]?*anyopaque, out: *?*anyopaque, err: [*]u8, errlen: c_int) c_int;
extern "c" fn wzb_free(p: ?*anyopaque) void;
extern "c" fn wzb_width(p: ?*anyopaque) c_int;
extern "c" fn wzb_height(p: ?*anyopaque) c_int;
extern "c" fn wzb_rgba(p: ?*anyopaque, dst: [*]u8) void;
extern "c" fn fopen(path: [*:0]const u8, mode: [*:0]const u8) ?*anyopaque;
extern "c" fn fclose(f: ?*anyopaque) c_int;
extern "c" fn fread(p: [*]u8, s: usize, n: usize, f: ?*anyopaque) usize;
extern "c" fn fwrite(p: [*]const u8, s: usize, n: usize, f: ?*anyopaque) usize;
extern "c" fn write(fd: c_int, p: [*]const u8, n: usize) isize;
extern "c" fn clock() c_long;
extern "c" fn exit(code: c_int) noreturn;

const alloc = std.heap.c_allocator;

fn say(comptime fmt: []const u8, args: anytype) void {
    var buf: [4096]u8 = undefined;
    const s = std.fmt.bufPrint(&buf, fmt, args) catch return;
    _ = write(2, s.ptr, s.len);
}

fn die(comptime fmt: []const u8, args: anytype) noreturn {
    say(fmt ++ "\n", args);
    exit(1);
}

fn seconds() f64 {
    return @as(f64, @floatFromInt(clock())) / 1000000.0;
}

// ---------------------------------------------------------------- operators

const NW = 14;
const MAXIN = 8;
const MAXN = 220;

const OpInfo = struct { name: [:0]const u8, kinds: []const u8, nin: u8 };
// i = whole number, f = decimal, c = colour: the packing of werkkzeug3's operator table (lane 473x's wzlang.py)
const ops = [_]OpInfo{
    .{ .name = "Flat", .kinds = "iic", .nin = 0 },
    .{ .name = "Perlin", .kinds = "iiiififffcc", .nin = 0 },
    .{ .name = "Cell", .kinds = "iiccciiffifif", .nin = 0 },
    .{ .name = "Gradient", .kinds = "iiccfffi", .nin = 0 },
    .{ .name = "Bricks", .kinds = "iicccffiiiiiff", .nin = 0 },
    .{ .name = "Color", .kinds = "ic", .nin = 1 },
    .{ .name = "Range", .kinds = "icc", .nin = 1 },
    .{ .name = "HSCB", .kinds = "ffff", .nin = 1 },
    .{ .name = "Blur", .kinds = "ifff", .nin = 1 },
    .{ .name = "Sharpen", .kinds = "ifff", .nin = 1 },
    .{ .name = "GlowRect", .kinds = "ffffffcffii", .nin = 1 },
    .{ .name = "GlowRectOld", .kinds = "ffffffcffii", .nin = 1 },
    .{ .name = "Dots", .kinds = "ccii", .nin = 1 },
    .{ .name = "Transform", .kinds = "fffffiii", .nin = 1 },
    .{ .name = "TransformMul", .kinds = "ffffficiic", .nin = 1 },
    .{ .name = "Twirl", .kinds = "ffffffi", .nin = 1 },
    .{ .name = "Normals", .kinds = "fi", .nin = 1 },
    .{ .name = "Light", .kinds = "ifffffccfff", .nin = 1 },
    .{ .name = "ColorBalance", .kinds = "fffffffff", .nin = 1 },
    .{ .name = "Unwrap", .kinds = "i", .nin = 1 },
    .{ .name = "Bulge", .kinds = "f", .nin = 1 },
    .{ .name = "Merge", .kinds = "i", .nin = 2 },
    .{ .name = "Distort", .kinds = "fi", .nin = 2 },
    .{ .name = "Bump", .kinds = "ifffffccfffcff", .nin = 2 },
    .{ .name = "Paste", .kinds = "fffffffi", .nin = 2 },
    .{ .name = "Mask", .kinds = "i", .nin = 3 },
    .{ .name = "Format", .kinds = "", .nin = 1 },
    .{ .name = "Pass", .kinds = "", .nin = 1 },
};
const OP_FLAT = 0;
const OP_NORMALS = 16;
const OP_TRANSFORM = 13;
const OP_MERGE = 21;
const OP_BUMP = 23;
const OP_MASK = 25;

fn opIndex(name: []const u8) ?u8 {
    for (ops, 0..) |o, i| if (std.mem.eql(u8, o.name, name)) return @intCast(i);
    return null;
}

fn isGenerator(op: u8) bool {
    return ops[op].nin == 0;
}

/// a word the fitter never changes: the size of a generator, the new size of Transform
fn fixedWord(op: u8, p: usize) bool {
    if (isGenerator(op) and p < 2) return true;
    if (op == OP_TRANSFORM and p >= 6) return true;
    return false;
}

const Node = struct {
    op: u8 = 0,
    nin: u8 = 0,
    in: [MAXIN]u8 = [_]u8{0} ** MAXIN,
    nw: u8 = 0,
    w: [NW]u32 = [_]u32{0} ** NW,
    lock: bool = false, // values read from the picture that the tuning must keep (a repeat count)
    lockw: u16 = 0, // single values the tuning must keep (where a shape's centre was read)
    shape: bool = false, // the Transform that repeats the read shape: the relief's height
    is_base: bool = false, // the top of the surface layer, marked while the cleaning moves operators
    keep: bool = false, // built from a reading: the cleaning by the inner measure does not remove it
    grey: bool = false, // its colours are tuned as greys: a light or an added noise changes shade, not hue
};

const Graph = struct {
    n: usize = 0,
    root: usize = 0,
    nodes: [MAXN]Node = undefined,

    /// werkkzeug3's storage: one class byte and the parameter words of every operator
    fn bytes(g: *const Graph) usize {
        var b: usize = 0;
        for (g.nodes[0..g.n]) |nd| b += 1 + 4 * @as(usize, ops[nd.op].kinds.len);
        return b;
    }

    /// put a node at position pos; the nodes from pos on move up by one
    fn insert(g: *Graph, pos: usize, nd: Node) void {
        if (g.n >= MAXN) die("graph too large", .{});
        var i = g.n;
        while (i > pos) : (i -= 1) g.nodes[i] = g.nodes[i - 1];
        g.nodes[pos] = nd;
        g.n += 1;
        for (g.nodes[pos + 1 .. g.n]) |*x| {
            for (x.in[0..x.nin]) |*v| {
                if (v.* >= pos) v.* += 1;
            }
        }
        if (g.root >= pos) g.root += 1;
    }

    /// every operator after `from` that took `old` takes `new` instead
    fn rewire(g: *Graph, from: usize, old: usize, new: usize) void {
        for (g.nodes[from + 1 .. g.n]) |*x| {
            for (x.in[0..x.nin]) |*v| {
                if (v.* == old) v.* = @intCast(new);
            }
        }
        if (g.root == old) g.root = new;
    }

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

// ---------------------------------------------------------------- files

fn readFile(path: [*:0]const u8) []u8 {
    const f = fopen(path, "rb") orelse die("cannot open {s}", .{path});
    var list: std.ArrayList(u8) = .empty;
    var buf: [65536]u8 = undefined;
    while (true) {
        const n = fread(&buf, 1, buf.len, f);
        if (n == 0) break;
        list.appendSlice(alloc, buf[0..n]) catch die("out of memory", .{});
    }
    _ = fclose(f);
    return list.items;
}

fn writeFile(path: []const u8, data: []const u8) void {
    var pz: [1024]u8 = undefined;
    const p = std.fmt.bufPrintZ(&pz, "{s}", .{path}) catch die("path too long", .{});
    const f = fopen(p.ptr, "wb") orelse die("cannot write {s}", .{path});
    if (fwrite(data.ptr, 1, data.len, f) != data.len) die("short write to {s}", .{path});
    _ = fclose(f);
}

const Image = struct { w: usize, h: usize, rgb: []f32 };

fn readPpm(path: [*:0]const u8) Image {
    const d = readFile(path);
    var it = std.mem.tokenizeAny(u8, d[0..@min(d.len, 64)], " \t\r\n");
    const magic = it.next() orelse die("{s}: not a PPM", .{path});
    if (!std.mem.eql(u8, magic, "P6")) die("{s}: not a binary PPM (P6)", .{path});
    const w = std.fmt.parseInt(usize, it.next() orelse "", 10) catch die("{s}: bad PPM header", .{path});
    const h = std.fmt.parseInt(usize, it.next() orelse "", 10) catch die("{s}: bad PPM header", .{path});
    const mx = it.next() orelse die("{s}: bad PPM header", .{path});
    if (!std.mem.eql(u8, mx, "255")) die("{s}: only 8-bit PPM", .{path});
    const start = (@intFromPtr(mx.ptr) - @intFromPtr(d.ptr)) + mx.len + 1;
    if (d.len < start + w * h * 3) die("{s}: PPM is cut short", .{path});
    const rgb = alloc.alloc(f32, w * h * 3) catch die("out of memory", .{});
    for (rgb, 0..) |*v, i| v.* = @as(f32, @floatFromInt(d[start + i])) / 255.0;
    return .{ .w = w, .h = h, .rgb = rgb };
}

fn writePpm(path: []const u8, rgba: []const u8, w: usize, h: usize) void {
    var out = alloc.alloc(u8, 32 + w * h * 3) catch die("out of memory", .{});
    defer alloc.free(out);
    const hd = std.fmt.bufPrint(out[0..32], "P6\n{d} {d}\n255\n", .{ w, h }) catch unreachable;
    for (0..w * h) |i| {
        out[hd.len + 3 * i] = rgba[4 * i];
        out[hd.len + 3 * i + 1] = rgba[4 * i + 1];
        out[hd.len + 3 * i + 2] = rgba[4 * i + 2];
    }
    writeFile(path, out[0 .. hd.len + w * h * 3]);
}

fn parseScript(text: []const u8) Graph {
    var g = Graph{};
    var names: [MAXN][]const u8 = undefined;
    var lines = std.mem.tokenizeAny(u8, text, "\r\n");
    var have_out = false;
    while (lines.next()) |line| {
        var t = std.mem.tokenizeAny(u8, line, " \t");
        const id = t.next() orelse continue;
        if (id[0] == '#') continue;
        if (std.mem.eql(u8, id, "out")) {
            const nm = t.next() orelse die("out line without a name", .{});
            for (names[0..g.n], 0..) |x, i| {
                if (std.mem.eql(u8, x, nm)) {
                    g.root = i;
                    have_out = true;
                }
            }
            continue;
        }
        const opn = t.next() orelse die("{s}: no operator", .{id});
        const op = opIndex(opn) orelse die("{s}: operator {s} is not known", .{ id, opn });
        var nd = Node{ .op = op };
        const ins = t.next() orelse die("{s}: no inputs", .{id});
        if (!std.mem.eql(u8, ins, "-")) {
            var ii = std.mem.tokenizeAny(u8, ins, ",");
            while (ii.next()) |nm| {
                var found = false;
                for (names[0..g.n], 0..) |x, i| {
                    if (std.mem.eql(u8, x, nm)) {
                        if (nd.nin >= MAXIN) die("{s}: more than {d} inputs", .{ id, MAXIN });
                        nd.in[nd.nin] = @intCast(i);
                        nd.nin += 1;
                        found = true;
                        break;
                    }
                }
                if (!found) die("{s}: input {s} is not defined above it", .{ id, nm });
            }
        }
        while (t.next()) |hx| {
            if (nd.nw < NW) {
                nd.w[nd.nw] = std.fmt.parseInt(u32, hx, 16) catch die("{s}: bad word {s}", .{ id, hx });
                nd.nw += 1;
            }
        }
        if (g.n >= MAXN) die("more than {d} operators", .{MAXN});
        names[g.n] = id;
        g.nodes[g.n] = nd;
        g.n += 1;
    }
    if (!have_out) die("no out line", .{});
    return g;
}

fn scriptText(g: *const Graph, buf: []u8) []u8 {
    var n: usize = 0;
    for (g.nodes[0..g.n], 0..) |nd, i| {
        n += (std.fmt.bufPrint(buf[n..], "v{d} {s} ", .{ i, ops[nd.op].name }) catch die("script too long", .{})).len;
        if (nd.nin == 0) {
            buf[n] = '-';
            n += 1;
        }
        for (nd.in[0..nd.nin], 0..) |v, k| {
            n += (std.fmt.bufPrint(buf[n..], "{s}v{d}", .{ if (k == 0) "" else ",", v }) catch die("script too long", .{})).len;
        }
        for (0..ops[nd.op].kinds.len) |p| {
            n += (std.fmt.bufPrint(buf[n..], " {x}", .{nd.w[p]}) catch die("script too long", .{})).len;
        }
        buf[n] = '\n';
        n += 1;
    }
    n += (std.fmt.bufPrint(buf[n..], "out v{d}\n", .{g.root}) catch die("script too long", .{})).len;
    return buf[0..n];
}

// ---------------------------------------------------------------- drawing, with a memory of what was drawn

const CACHE = 1 << 13;
const Slot = struct { key: u64 = 0, bm: ?*anyopaque = null, used: bool = false };
var cache: []Slot = undefined;
var cache_count: usize = 0;
var cache_cap: usize = 1500;
var n_draw: u64 = 0; // operators really drawn
var n_eval: u64 = 0; // graphs asked for
var n_refused: u64 = 0;

fn cacheClear() void {
    for (cache) |*s| {
        if (s.used and s.bm != null) wzb_free(s.bm);
        s.* = .{};
    }
    cache_count = 0;
}

fn cacheFind(key: u64) ?*Slot {
    var i: usize = @intCast(key & (CACHE - 1));
    while (cache[i].used) : (i = (i + 1) & (CACHE - 1)) {
        if (cache[i].key == key) return &cache[i];
    }
    return null;
}

fn cachePut(key: u64, bm: ?*anyopaque) void {
    var i: usize = @intCast(key & (CACHE - 1));
    while (cache[i].used) : (i = (i + 1) & (CACHE - 1)) {}
    cache[i] = .{ .key = key, .bm = bm, .used = true };
    cache_count += 1;
}

fn mix(h: u64, v: u64) u64 {
    var x = (h ^ v) *% 0x9E3779B97F4A7C15;
    x ^= x >> 29;
    return x *% 0xBF58476D1CE4E5B9;
}

/// Draw the graph; size 0 keeps the sizes written in it, another value draws every generator at 2^size.
/// The bitmap belongs to the memory: do not free it. null: an operator refused its values.
fn draw(g: *const Graph, size: u32) ?*anyopaque {
    n_eval += 1;
    if (cache_count > cache_cap) cacheClear();
    var hs: [MAXN]u64 = undefined;
    var bm: [MAXN]?*anyopaque = undefined;
    for (0..g.root + 1) |i| {
        const nd = &g.nodes[i];
        var w: [32]u32 = [_]u32{0} ** 32;
        const nk = ops[nd.op].kinds.len;
        for (0..nk) |p| w[p] = nd.w[p];
        if (size != 0) {
            if (isGenerator(nd.op)) {
                w[0] = size;
                w[1] = size;
            }
            if (nd.op == OP_TRANSFORM) {
                w[6] = 0;
                w[7] = 0;
            }
        }
        var h: u64 = mix(0x1234567, @as(u64, nd.op) + (@as(u64, size) << 8));
        for (0..nk) |p| h = mix(h, w[p]);
        for (nd.in[0..nd.nin]) |v| h = mix(h, hs[v]);
        hs[i] = h;
        if (cacheFind(h)) |s| {
            bm[i] = s.bm;
            if (s.bm == null) return null;
            continue;
        }
        var inp: [MAXIN]?*anyopaque = undefined;
        for (nd.in[0..nd.nin], 0..) |v, k| inp[k] = bm[v];
        var out: ?*anyopaque = null;
        var err: [200]u8 = undefined;
        const r = wzb_apply(ops[nd.op].name.ptr, &w, nd.nin, &inp, &out, &err, 200);
        n_draw += 1;
        if (r != 0) {
            n_refused += 1;
            cachePut(h, null);
            return null;
        }
        cachePut(h, out);
        bm[i] = out;
    }
    return bm[g.root];
}

// ---------------------------------------------------------------- the measure the search steers by

const MAXLEV = 10;
const NF = 12; // small filters
const FS = 5; // their side
const NB = 64; // bins of a filter's answers
const TLEV = 6; // the finest levels the filters look at
const NSAMP = 4096; // places looked at per level, at most

const Pyr = struct {
    nlev: usize = 0,
    side: [MAXLEV]usize = undefined,
    lev: [MAXLEV][]f32 = undefined,
    cdf: [3][32]f32 = undefined, // how the values of each channel are spread
    resp: [TLEV][NF][NB]f32 = undefined, // per level and filter: how its answers are spread (cumulative)
    sigma: [TLEV][NF]f32 = undefined, // the picture's own spread of those answers (set for the target only)
    variance: f32 = 0,
    proj: []f32 = undefined,
};

var filt_col: [NF][3]f32 = undefined;
var filt_tap: [NF][FS * FS]f32 = undefined;

/// Small random filters with no mean (Elnekave and Weiss 2022: the spread of a picture's patches along
/// random directions tells textures apart without any trained network). Fixed: every run uses the same ones.
fn makeFilters() void {
    var st: u64 = 0x9E3779B97F4A7C15;
    for (0..NF) |f| {
        var n: f32 = 0;
        var m: f32 = 0;
        for (0..FS * FS) |k| {
            st = st *% 6364136223846793005 +% 1442695040888963407;
            const ua = (@as(f32, @floatFromInt((st >> 40) & 0xffff)) + 1.0) / 65537.0;
            st = st *% 6364136223846793005 +% 1442695040888963407;
            const ub = @as(f32, @floatFromInt((st >> 40) & 0xffff)) / 65536.0;
            filt_tap[f][k] = @sqrt(-2.0 * @log(ua)) * @cos(6.2831853 * ub);
            m += filt_tap[f][k];
        }
        m /= FS * FS;
        for (0..FS * FS) |k| {
            filt_tap[f][k] -= m;
            n += filt_tap[f][k] * filt_tap[f][k];
        }
        for (0..FS * FS) |k| filt_tap[f][k] /= @sqrt(n);
        if (f % 2 == 0) {
            filt_col[f] = .{ 1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0 }; // brightness
        } else {
            var c: [3]f32 = undefined;
            var cn: f32 = 0;
            inline for (0..3) |k| {
                st = st *% 6364136223846793005 +% 1442695040888963407;
                c[k] = @as(f32, @floatFromInt((st >> 40) & 0xffff)) / 32768.0 - 1.0;
                cn += c[k] * c[k];
            }
            inline for (0..3) |k| filt_col[f][k] = c[k] / @sqrt(cn);
        }
    }
}

fn pyrAlloc(side: usize) Pyr {
    var p = Pyr{};
    var s = side;
    while (s >= 4 and p.nlev < MAXLEV) : (s /= 2) {
        p.side[p.nlev] = s;
        p.lev[p.nlev] = alloc.alloc(f32, s * s * 3) catch die("out of memory", .{});
        p.nlev += 1;
    }
    p.proj = alloc.alloc(f32, side * side) catch die("out of memory", .{});
    return p;
}

fn pyrFree(p: *Pyr) void {
    for (0..p.nlev) |l| alloc.free(p.lev[l]);
    alloc.free(p.proj);
}

/// levels by halving (2 by 2 means); the spread of each channel's values; and the spread of the filters'
/// answers. For the target (ref == null) the bins are laid over its own spread; a drawing uses the target's bins.
fn pyrBuild(p: *Pyr, ref: ?*const Pyr) void {
    for (1..p.nlev) |l| {
        const s = p.side[l];
        const a = p.lev[l - 1];
        const b = p.lev[l];
        const s2 = s * 2;
        for (0..s) |y| {
            for (0..s) |x| {
                inline for (0..3) |c| {
                    b[(y * s + x) * 3 + c] = 0.25 * (a[((2 * y) * s2 + 2 * x) * 3 + c] + a[((2 * y) * s2 + 2 * x + 1) * 3 + c] +
                        a[((2 * y + 1) * s2 + 2 * x) * 3 + c] + a[((2 * y + 1) * s2 + 2 * x + 1) * 3 + c]);
                }
            }
        }
    }
    var hist: [3][32]f32 = [_][32]f32{[_]f32{0} ** 32} ** 3;
    const a0 = p.lev[0];
    var sum = [3]f64{ 0, 0, 0 };
    var sum2 = [3]f64{ 0, 0, 0 };
    for (0..a0.len / 3) |i| {
        inline for (0..3) |c| {
            const v = a0[3 * i + c];
            const b: usize = @intFromFloat(@min(31.0, @max(0.0, v * 32.0)));
            hist[c][b] += 1;
            sum[c] += v;
            sum2[c] += v * v;
        }
    }
    const npx = @as(f64, @floatFromInt(a0.len / 3));
    var variance: f64 = 0;
    inline for (0..3) |c| variance += (sum2[c] / npx - (sum[c] / npx) * (sum[c] / npx)) / 3.0;
    p.variance = @floatCast(variance);
    const inv = 3.0 / @as(f32, @floatFromInt(a0.len));
    inline for (0..3) |c| {
        var acc: f32 = 0;
        for (0..32) |b| {
            acc += hist[c][b] * inv;
            p.cdf[c][b] = acc;
        }
    }
    for (0..TLEV) |l| {
        if (l >= p.nlev or p.side[l] < 16) {
            for (0..NF) |f| {
                p.sigma[l][f] = 0;
            }
            continue;
        }
        const s = p.side[l];
        const a = p.lev[l];
        var stride: usize = 1;
        while ((s / stride) * (s / stride) > NSAMP) stride += 1;
        for (0..NF) |f| {
            const cw = filt_col[f];
            for (0..s * s) |i| p.proj[i] = cw[0] * a[3 * i] + cw[1] * a[3 * i + 1] + cw[2] * a[3 * i + 2];
            var h = [_]f32{0} ** NB;
            var e: f64 = 0;
            var cnt: f32 = 0;
            const sg: f32 = if (ref) |r| r.sigma[l][f] else 0;
            var y: usize = 0;
            while (y < s) : (y += stride) {
                var x: usize = 0;
                while (x < s) : (x += stride) {
                    var v: f32 = 0;
                    for (0..FS) |dy| {
                        const row = ((y + dy) % s) * s;
                        for (0..FS) |dx| v += filt_tap[f][dy * FS + dx] * p.proj[row + (x + dx) % s];
                    }
                    cnt += 1;
                    if (ref == null) {
                        e += v * v;
                        // kept in the first places of the level's own storage is not possible; a second pass bins them
                    } else {
                        const b: usize = @intFromFloat(@min(@as(f32, NB - 1), @max(0.0, (v / (4.0 * sg) + 1.0) * (NB / 2))));
                        h[b] += 1;
                    }
                }
            }
            if (ref == null) {
                p.sigma[l][f] = @floatCast(@max(1e-4, @sqrt(e / cnt)));
                const s0 = p.sigma[l][f];
                y = 0;
                while (y < s) : (y += stride) {
                    var x: usize = 0;
                    while (x < s) : (x += stride) {
                        var v: f32 = 0;
                        for (0..FS) |dy| {
                            const row = ((y + dy) % s) * s;
                            for (0..FS) |dx| v += filt_tap[f][dy * FS + dx] * p.proj[row + (x + dx) % s];
                        }
                        const b: usize = @intFromFloat(@min(@as(f32, NB - 1), @max(0.0, (v / (4.0 * s0) + 1.0) * (NB / 2))));
                        h[b] += 1;
                    }
                }
            }
            var acc: f32 = 0;
            for (0..NB) |b| {
                acc += h[b] / cnt;
                p.resp[l][f][b] = acc;
            }
        }
    }
}

var place_weight: f32 = 0.5;
var texture_weight: f32 = 1.0;
var spread_weight: f32 = 1.0;
var place_side: f32 = 32.0;

/// How far a drawing is from the picture, for the search only; every part is a pure number.
/// place:   whether light and dark lie where the picture has them (one minus the correlation, never below
///          none), fully on the coarse levels and less on the fine ones: a noise's grains need not sit on
///          the same pixels, and a flat drawing must not beat a right texture in the wrong place;
/// texture: what the surface is made of: the spread of the answers of small random filters on the six
///          finest levels, drawing against picture (a one-dimensional transport distance per filter);
/// spread:  the spread of each channel's values.
fn distance(a: *const Pyr, t: *const Pyr) f32 {
    var place: f64 = 0;
    var wsum: f64 = 0;
    for (0..a.nlev) |l| {
        const x = a.lev[l];
        const y = t.lev[l];
        const np = @as(f64, @floatFromInt(x.len / 3));
        var su = [3]f64{ 0, 0, 0 };
        var sv = [3]f64{ 0, 0, 0 };
        var suv = [3]f64{ 0, 0, 0 };
        var suu = [3]f64{ 0, 0, 0 };
        var svv = [3]f64{ 0, 0, 0 };
        for (0..x.len / 3) |i| {
            inline for (0..3) |c| {
                const u = x[3 * i + c];
                const v = y[3 * i + c];
                su[c] += u;
                sv[c] += v;
                suv[c] += u * v;
                suu[c] += u * u;
                svv[c] += v * v;
            }
        }
        var cov: f64 = 0;
        var vu: f64 = 0;
        var vv: f64 = 0;
        inline for (0..3) |c| {
            cov += suv[c] / np - (su[c] / np) * (sv[c] / np);
            vu += suu[c] / np - (su[c] / np) * (su[c] / np);
            vv += svv[c] / np - (sv[c] / np) * (sv[c] / np);
        }
        const rho = if (vu > 1e-9 and vv > 1e-9) @max(0.0, cov / @sqrt(vu * vv)) else 0.0;
        const wa = @min(1.0, place_side / @as(f32, @floatFromInt(a.side[l])));
        place += wa * (1.0 - rho);
        wsum += wa;
    }
    place /= wsum;
    var tex: f64 = 0;
    var nt: f64 = 0;
    for (0..TLEV) |l| {
        for (0..NF) |f| {
            if (t.sigma[l][f] == 0) continue;
            var d: f64 = 0;
            for (0..NB) |b| d += @abs(a.resp[l][f][b] - t.resp[l][f][b]);
            tex += d * 8.0 / NB; // in units of the picture's own spread
            nt += 1;
        }
    }
    if (nt > 0) tex /= nt;
    var cd: f64 = 0;
    inline for (0..3) |c| {
        for (0..32) |b| cd += @abs(a.cdf[c][b] - t.cdf[c][b]);
    }
    cd /= 96.0;
    return @floatCast(place_weight * place + texture_weight * tex + spread_weight * cd * 8.0);
}

const Target = struct {
    size: u32, // exponent of the side
    pyr: Pyr,
    scratch: Pyr,
    rgba: []u8,
    slow: f64, // a drawing that takes longer than this is refused: the device must draw it
};

fn makeTarget(img: Image, size: u32) Target {
    const side = @as(usize, 1) << @intCast(size);
    if (img.w != img.h or img.w < side or img.w % side != 0) die("the picture must be square, a power of two, at least {d} pixels", .{side});
    var t = Target{ .size = size, .pyr = pyrAlloc(side), .scratch = pyrAlloc(side), .rgba = alloc.alloc(u8, side * side * 4) catch die("out of memory", .{}), .slow = 0.2 * @as(f64, @floatFromInt(side * side)) / 16384.0 };
    const f = img.w / side;
    const inv = 1.0 / @as(f32, @floatFromInt(f * f));
    for (0..side) |y| {
        for (0..side) |x| {
            inline for (0..3) |c| {
                var s: f32 = 0;
                for (0..f) |dy| {
                    for (0..f) |dx| s += img.rgb[((y * f + dy) * img.w + x * f + dx) * 3 + c];
                }
                t.pyr.lev[0][(y * side + x) * 3 + c] = s * inv;
            }
        }
    }
    pyrBuild(&t.pyr, null);
    return t;
}

fn freeTarget(t: *Target) void {
    pyrFree(&t.pyr);
    pyrFree(&t.scratch);
    alloc.free(t.rgba);
}

const BAD: f32 = 1e9;
var n_slow: u64 = 0;

fn score(g: *const Graph, t: *Target) f32 {
    const t0 = seconds();
    const bm = draw(g, t.size) orelse return BAD;
    if (seconds() - t0 > t.slow) {
        n_slow += 1;
        return BAD;
    }
    const side = @as(usize, 1) << @intCast(t.size);
    if (wzb_width(bm) != side or wzb_height(bm) != side) return BAD;
    wzb_rgba(bm, t.rgba.ptr);
    const l0 = t.scratch.lev[0];
    for (0..side * side) |i| {
        l0[3 * i] = @as(f32, @floatFromInt(t.rgba[4 * i])) / 255.0;
        l0[3 * i + 1] = @as(f32, @floatFromInt(t.rgba[4 * i + 1])) / 255.0;
        l0[3 * i + 2] = @as(f32, @floatFromInt(t.rgba[4 * i + 2])) / 255.0;
    }
    pyrBuild(&t.scratch, &t.pyr);
    return distance(&t.scratch, &t.pyr);
}

// ---------------------------------------------------------------- the prior

const Inst = struct { op: u8, w: [NW]u32 };
const Chain = struct { slot: u8, consumer: Inst, len: u8, items: [5]Inst };
const Stat = struct {
    n: u32 = 0,
    vals: [24]u32 = undefined, // the distinct whole numbers artists used (when few)
    nvals: u32 = 0,
    many: bool = false,
    lo: f32 = 0,
    hi: f32 = 0,
    sd: f32 = 0,
    sum: f64 = 0,
    sum2: f64 = 0,
};

var insts: std.ArrayList(Inst) = .empty;
var unary: std.ArrayList(u32) = .empty; // indices into insts of one-input operators
var chains: std.ArrayList(Chain) = .empty;
var stats: [ops.len][NW]Stat = undefined;

fn parseInst(tok: *std.mem.TokenIterator(u8, .any)) ?Inst {
    const nm = tok.next() orelse return null;
    const op = opIndex(nm) orelse return null;
    var r = Inst{ .op = op, .w = [_]u32{0} ** NW };
    var k: usize = 0;
    while (tok.peek()) |hx| {
        if (hx[0] == '|' or hx[0] == ';') break;
        _ = tok.next();
        if (k < NW) r.w[k] = std.fmt.parseInt(u32, hx, 16) catch 0;
        k += 1;
    }
    return r;
}

fn f32of(w: u32) f32 {
    return @bitCast(w);
}
fn wordOf(f: f32) u32 {
    return @bitCast(f);
}
fn i32of(w: u32) i32 {
    return @bitCast(w);
}

fn loadPrior(path: [*:0]const u8) void {
    for (&stats) |*row| {
        for (row) |*s| s.* = .{};
    }
    const text = readFile(path);
    var lines = std.mem.tokenizeAny(u8, text, "\n");
    while (lines.next()) |line| {
        var tok = std.mem.tokenizeAny(u8, line, " ");
        const kind = tok.next() orelse continue;
        if (kind[0] == 'I') {
            const in = parseInst(&tok) orelse continue;
            if (in.op >= OP_MERGE + 5) continue;
            insts.append(alloc, in) catch die("out of memory", .{});
            if (ops[in.op].nin == 1) unary.append(alloc, @intCast(insts.items.len - 1)) catch die("out of memory", .{});
            for (ops[in.op].kinds, 0..) |kd, p| {
                const s = &stats[in.op][p];
                const v: f32 = if (kd == 'f') f32of(in.w[p]) else @floatFromInt(i32of(in.w[p]));
                if (kd == 'f' and !std.math.isFinite(v)) continue;
                if (s.n == 0 or v < s.lo) s.lo = v;
                if (s.n == 0 or v > s.hi) s.hi = v;
                s.n += 1;
                s.sum += v;
                s.sum2 += @as(f64, v) * v;
                if (kd == 'i' and !s.many) {
                    var seen = false;
                    for (s.vals[0..s.nvals]) |x| {
                        if (x == in.w[p]) seen = true;
                    }
                    if (!seen) {
                        if (s.nvals < 24) {
                            s.vals[s.nvals] = in.w[p];
                            s.nvals += 1;
                        } else s.many = true;
                    }
                }
            }
        } else if (kind[0] == 'C') {
            var ch: Chain = undefined;
            ch.slot = std.fmt.parseInt(u8, tok.next() orelse continue, 10) catch continue;
            ch.consumer = parseInst(&tok) orelse continue;
            _ = tok.next(); // |
            ch.len = 0;
            while (ch.len < 5) {
                ch.items[ch.len] = parseInst(&tok) orelse break;
                ch.len += 1;
                if (tok.peek() == null) break;
                _ = tok.next(); // ;
            }
            if (ch.len > 0) chains.append(alloc, ch) catch die("out of memory", .{});
        }
    }
    for (&stats) |*row| {
        for (row) |*s| {
            if (s.n > 1) {
                const m = s.sum / @as(f64, @floatFromInt(s.n));
                const v = s.sum2 / @as(f64, @floatFromInt(s.n)) - m * m;
                s.sd = @floatCast(@sqrt(@max(v, 0)));
            }
        }
    }
    if (insts.items.len == 0 or chains.items.len == 0) die("the prior is empty", .{});
}

// ---------------------------------------------------------------- random numbers (fixed start: the same run gives the same procedure)

var rng_state: u64 = 0x2545F4914F6CDD1D;
fn rnd() u64 {
    rng_state ^= rng_state >> 12;
    rng_state ^= rng_state << 25;
    rng_state ^= rng_state >> 27;
    return rng_state *% 0x2545F4914F6CDD1D;
}
fn rndN(n: usize) usize {
    return @intCast((rnd() >> 11) % n);
}
fn rndF() f32 {
    return @as(f32, @floatFromInt(rnd() >> 40)) / 16777216.0;
}

// ---------------------------------------------------------------- the picture's palette

var palette: [12]u32 = undefined; // 00rrggbb
var npal: usize = 0;

fn makePalette(t: *const Target) void {
    const px = t.pyr.lev[0];
    const n = px.len / 3;
    const K = 8;
    var cen: [K][3]f32 = undefined;
    for (0..K) |k| {
        const i = (n * (2 * k + 1)) / (2 * K);
        cen[k] = .{ px[3 * i], px[3 * i + 1], px[3 * i + 2] };
    }
    for (0..12) |_| {
        var sum: [K][3]f64 = [_][3]f64{.{ 0, 0, 0 }} ** K;
        var cnt: [K]f64 = [_]f64{0} ** K;
        for (0..n) |i| {
            var best: usize = 0;
            var bd: f32 = 1e9;
            for (0..K) |k| {
                var d: f32 = 0;
                inline for (0..3) |c| d += (px[3 * i + c] - cen[k][c]) * (px[3 * i + c] - cen[k][c]);
                if (d < bd) {
                    bd = d;
                    best = k;
                }
            }
            inline for (0..3) |c| sum[best][c] += px[3 * i + c];
            cnt[best] += 1;
        }
        for (0..K) |k| {
            if (cnt[k] > 0) {
                inline for (0..3) |c| cen[k][c] = @floatCast(sum[k][c] / cnt[k]);
            }
        }
    }
    npal = 0;
    for (0..K) |k| {
        palette[npal] = rgbWord(cen[k]);
        npal += 1;
    }
    var mean = [3]f32{ 0, 0, 0 };
    const top = t.pyr.lev[t.pyr.nlev - 1];
    for (0..top.len / 3) |i| {
        inline for (0..3) |c| mean[c] += top[3 * i + c];
    }
    inline for (0..3) |c| mean[c] /= @floatFromInt(top.len / 3);
    palette[npal] = rgbWord(mean);
    npal += 1;
    palette[npal] = 0x000000;
    npal += 1;
    palette[npal] = 0xffffff;
    npal += 1;
    palette[npal] = 0x808080;
    npal += 1;
}

fn rgbWord(c: [3]f32) u32 {
    var w: u32 = 0;
    inline for (0..3) |k| {
        const v: u32 = @intFromFloat(@min(255.0, @max(0.0, c[k] * 255.0 + 0.5)));
        w = (w << 8) | v;
    }
    return w;
}

// ---------------------------------------------------------------- tuning values: direct search, one value at a time

fn tryWord(g: *Graph, t: *Target, i: usize, p: usize, v: u32, best: *f32, budget: *i64) bool {
    const old = g.nodes[i].w[p];
    if (v == old) return false;
    g.nodes[i].w[p] = v;
    budget.* -= 1;
    const s = score(g, t);
    if (s < best.*) {
        best.* = s;
        return true;
    }
    g.nodes[i].w[p] = old;
    return false;
}

/// tune the values of the operators first..last (inclusive); deep also walks wide whole-number ranges (seeds)
fn tune(g: *Graph, t: *Target, first: usize, last: usize, budget_in: i64, deep: bool, passes: usize) f32 {
    var budget = budget_in;
    var best = score(g, t);
    if (best >= BAD) return best;
    var scale: f32 = 1.0;
    for (0..passes) |pass| {
        var improved = false;
        var i = first;
        while (i <= last and budget > 0) : (i += 1) {
            const op = g.nodes[i].op;
            if (g.nodes[i].lock) continue;
            for (ops[op].kinds, 0..) |kd, p| {
                if (budget <= 0) break;
                if (fixedWord(op, p)) continue;
                if ((g.nodes[i].lockw >> @intCast(p)) & 1 == 1) continue;
                const st = &stats[op][p];
                switch (kd) {
                    'i' => {
                        if (st.nvals <= 1 and !st.many) continue;
                        if (!st.many) {
                            for (st.vals[0..st.nvals]) |v| {
                                if (tryWord(g, t, i, p, v, &best, &budget)) improved = true;
                            }
                        } else if (deep and pass == 0 and st.hi - st.lo <= 300) {
                            // Perlin's seed is taken modulo 256 by the operator: all of them are tried
                            var v: i32 = if (op == OP_PERLIN and p == 5) 0 else @intFromFloat(st.lo);
                            const hi: i32 = if (op == OP_PERLIN and p == 5) 255 else @intFromFloat(st.hi);
                            while (v <= hi) : (v += 1) {
                                if (tryWord(g, t, i, p, @bitCast(v), &best, &budget)) improved = true;
                            }
                        } else {
                            const cur = i32of(g.nodes[i].w[p]);
                            const span: usize = @intFromFloat(st.hi - st.lo + 1);
                            for (0..6) |_| {
                                const v = @as(i32, @intFromFloat(st.lo)) + @as(i32, @intCast(rndN(span)));
                                _ = cur;
                                if (@as(f32, @floatFromInt(v)) < st.lo or @as(f32, @floatFromInt(v)) > st.hi) continue;
                                if (tryWord(g, t, i, p, @bitCast(v), &best, &budget)) improved = true;
                            }
                        }
                    },
                    'f' => {
                        if (st.sd <= 0) continue;
                        const step = 0.5 * st.sd * scale;
                        const lo = if (st.lo >= 0) @max(0.0, st.lo - st.sd) else st.lo - st.sd;
                        const hi = st.hi + st.sd;
                        const dirs = [_]f32{ 1, -1 };
                        for (dirs) |d| {
                            var moved = false;
                            var k: usize = 0;
                            while (k < 3) : (k += 1) {
                                const cur = f32of(g.nodes[i].w[p]);
                                const v = @min(hi, @max(lo, cur + d * step));
                                if (!tryWord(g, t, i, p, wordOf(v), &best, &budget)) break;
                                moved = true;
                            }
                            if (moved) {
                                improved = true;
                                break;
                            }
                        }
                    },
                    'c' => {
                        const step: i32 = @intFromFloat(@max(2.0, 48.0 * scale));
                        if (g.nodes[i].grey) {
                            const ds = [_]i32{ step, -step };
                            for (ds) |d| {
                                var k: usize = 0;
                                while (k < 3) : (k += 1) {
                                    const cur = g.nodes[i].w[p];
                                    var v = cur;
                                    inline for (.{ 0, 8, 16 }) |sh| {
                                        const ch: i32 = @intCast((cur >> sh) & 0xff);
                                        const nv: u32 = @intCast(@min(255, @max(0, ch + d)));
                                        v = (v & ~(@as(u32, 0xff) << sh)) | (nv << sh);
                                    }
                                    if (!tryWord(g, t, i, p, v, &best, &budget)) break;
                                    improved = true;
                                }
                            }
                            continue;
                        }
                        const shifts = [_]u5{ 0, 8, 16, 24 };
                        for (shifts) |sh| {
                            if (sh == 24 and (st.lo == st.hi or !deep)) break; // alpha: only where artists varied it
                            const ds = [_]i32{ step, -step };
                            for (ds) |d| {
                                var k: usize = 0;
                                while (k < 3) : (k += 1) {
                                    const cur = g.nodes[i].w[p];
                                    const ch: i32 = @intCast((cur >> sh) & 0xff);
                                    const nv: u32 = @intCast(@min(255, @max(0, ch + d)));
                                    const v = (cur & ~(@as(u32, 0xff) << sh)) | (nv << sh);
                                    if (!tryWord(g, t, i, p, v, &best, &budget)) break;
                                    improved = true;
                                }
                            }
                        }
                    },
                    else => {},
                }
            }
        }
        scale *= if (improved) 0.7 else 0.4;
        if (budget <= 0) break;
    }
    return best;
}

// ---------------------------------------------------------------- moves taken from the prior

fn nodeOf(in: Inst) Node {
    var nd = Node{ .op = in.op, .nin = ops[in.op].nin, .nw = @intCast(ops[in.op].kinds.len) };
    nd.w = in.w;
    // colours: half of the time one of the picture's own
    for (ops[in.op].kinds, 0..) |kd, p| {
        if (kd == 'c' and rndN(2) == 0) nd.w[p] = (nd.w[p] & 0xff000000) | palette[rndN(npal)];
    }
    // a seed the artists' range allows, so two layers do not share one noise
    for (ops[in.op].kinds, 0..) |kd, p| {
        const st = &stats[in.op][p];
        if (kd == 'i' and st.many and !fixedWord(in.op, p) and rndN(2) == 0) {
            const span: usize = @intFromFloat(st.hi - st.lo + 1);
            nd.w[p] = @bitCast(@as(i32, @intFromFloat(st.lo)) + @as(i32, @intCast(rndN(span))));
        }
    }
    return nd;
}

const Move = struct { first: usize, last: usize, ok: bool };

/// a real one-input operator put after operator k
fn moveWrap(g: *Graph, k: usize) Move {
    var nd = nodeOf(insts.items[unary.items[rndN(unary.items.len)]]);
    nd.in[0] = @intCast(k);
    g.insert(k + 1, nd);
    g.rewire(k + 1, k, k + 1);
    return .{ .first = k + 1, .last = k + 1, .ok = true };
}

/// a real chain (a generator and the one-input operators above it) joined to operator k by the
/// several-input operator that consumed that chain in .kkrieger
fn moveChain(g: *Graph, k: usize) Move {
    const ch = chains.items[rndN(chains.items.len)];
    if (g.n + ch.len + 3 >= MAXN) return .{ .first = 0, .last = 0, .ok = false };
    var pos = k + 1;
    for (ch.items[0..ch.len], 0..) |it, j| {
        var nd = nodeOf(it);
        if (j > 0) nd.in[0] = @intCast(pos - 1);
        g.insert(pos, nd);
        pos += 1;
    }
    const end = pos - 1;
    var cons = nodeOf(ch.consumer);
    var other: usize = k;
    if (cons.op == OP_MASK) {
        // the third input: a flat colour of the picture
        var fl = Node{ .op = OP_FLAT, .nw = 3 };
        fl.w[2] = 0xff000000 | palette[rndN(npal)];
        g.insert(pos, fl);
        other = pos;
        pos += 1;
        const slots = [3][2]u8{ .{ 1, 2 }, .{ 0, 2 }, .{ 0, 1 } };
        const s = slots[@min(ch.slot, 2)];
        const flip = rndN(2);
        cons.in[@min(ch.slot, 2)] = @intCast(end);
        cons.in[s[flip]] = @intCast(k);
        cons.in[s[1 - flip]] = @intCast(other);
    } else {
        const slot: usize = if (ch.slot == 0) 0 else 1;
        cons.nin = 2;
        cons.in[slot] = @intCast(end);
        cons.in[1 - slot] = @intCast(k);
    }
    g.insert(pos, cons);
    g.rewire(pos, k, pos);
    return .{ .first = k + 1, .last = pos, .ok = true };
}

/// two operators already in the graph joined the way a real consumer joined its inputs (a relief lit from
/// a layer that is already there, a layer bent by another)
fn moveJoin(g: *Graph, k: usize) Move {
    if (g.n < 2) return .{ .first = 0, .last = 0, .ok = false };
    const ch = chains.items[rndN(chains.items.len)];
    if (ch.consumer.op == OP_MASK) return .{ .first = 0, .last = 0, .ok = false };
    const j = rndN(g.n);
    if (j >= k) return .{ .first = 0, .last = 0, .ok = false };
    var pos = k + 1;
    var second: usize = j;
    const first = pos;
    if (ch.consumer.op == OP_BUMP) {
        // Bump wants normals: a real Normals over the chosen operator
        var idx: usize = 0;
        var tries: usize = 0;
        while (tries < 200) : (tries += 1) {
            idx = unary.items[rndN(unary.items.len)];
            if (insts.items[idx].op == OP_NORMALS) break;
        }
        if (insts.items[idx].op != OP_NORMALS) return .{ .first = 0, .last = 0, .ok = false };
        var nm = nodeOf(insts.items[idx]);
        nm.in[0] = @intCast(j);
        g.insert(pos, nm);
        second = pos;
        pos += 1;
    }
    var cons = nodeOf(ch.consumer);
    cons.nin = 2;
    const flip: usize = if (ch.consumer.op == OP_MERGE) rndN(2) else 0;
    cons.in[flip] = @intCast(k);
    cons.in[1 - flip] = @intCast(second);
    g.insert(pos, cons);
    g.rewire(pos, k, pos);
    return .{ .first = first, .last = pos, .ok = true };
}

fn randomMove(g: *Graph) Move {
    const k = if (rndN(2) == 0) g.root else rndN(g.n);
    const r = rndN(100);
    if (r < 50) return moveChain(g, k);
    if (r < 88) return moveWrap(g, k);
    return moveJoin(g, k);
}

// ---------------------------------------------------------------- reading the picture before any search
//
// The reverse of the artist's order (lane 473x read the idioms from .kkrieger's graphs): the artist
// drew a noise, mapped it to two colours, drew one shape and repeated it, lit a relief. Backwards:
// the two colours and the grey picture between them, the repeat and the one shape under it, the noise's
// octaves from the strength of detail per scale. Hu, He, Deschaintre, Dorsey and Rushmeier (2022) take a
// bitmap apart the same way (parts, a noise model of several layers per part, then all values tuned together).

const OP_PERLIN = 1;
const OP_GLOWRECT = 10;

const Reading = struct {
    n: usize = 0,
    c0: u32 = 0,
    c1: u32 = 0,
    t: []f32 = undefined, // the picture along its main colour axis, 0..1
    nx: usize = 1, // repeats across
    ny: usize = 1, // and down
    share: f32 = 0, // how much of the picture's contrast the repeated cell explains
    nrect: usize = 0,
    rect: [3][4]f32 = undefined, // centre x, y and half sizes, in cells
    dark: f32 = 0, // the joints' brightness against the shapes'
    grain_down: bool = false, // which way the grain runs
    aniso: f32 = 1, // how much stronger the detail is one way than the other (1: no grain)
    joint: u32 = 0xff404040, // the joints' colour as a share of the surface's: the dark end of the picture's own colours
    ox: f32 = 0,
    oy: f32 = 0,
    f0: u32 = 0, // the noise: first octave, how many, the fall per octave, the strength
    oct: u32 = 1,
    fade: f32 = 1,
    amp: f32 = 1,
    // the readings that gate the operators that add structure (each is measured, none is searched)
    flat: f32 = 0, // share of the picture lying in flat patches
    edge: f32 = 0, // how much of the picture's change sits in few pixels (hard edges)
    off: f32 = 0, // share of the pixels whose colour lies off the main colour axis, as one cluster
    off_coh: f32 = 0, // how alike those pixels' colours are (1: one colour)
    off_col: u32 = 0, // that cluster's colour
    nring: usize = 0, // rings or swirls: centres x, y, radius (shares of the side) and how round the lines run there
    ring: [3][4]f32 = undefined,
    ring_best: f32 = 0,
    mirror: f32 = 0, // left-right likeness about the upright line at mirror_x
    mirror_x: f32 = 0.5,
    mirror_a: usize = 0, // the two rings that are each other's mirror picture
    mirror_b: usize = 0,
    bond: f32 = 0, // how much better a row agrees with the next one moved sideways than as it lies
    bond_shift: f32 = 0, // that move, in bricks
    bonded: bool = false,
    rows: usize = 1,
    bricks: usize = 1,
    row0: f32 = 0, // where the first row starts, as a share of the side
    jmul: u32 = 0xff404040, // the joints' own colour over the shapes' own colour, measured in the joints
    jw: [2]f32 = .{ 0.02, 0.02 }, // the joints' width across and down, as shares of the cell
};

/// the picture made smaller by whole steps: the mean of every block
fn shrink(t: []const f32, n: usize, m: usize) []f32 {
    const out = alloc.alloc(f32, m * m) catch die("out of memory", .{});
    const k = n / m;
    for (0..m) |y| {
        for (0..m) |x| {
            var sum: f32 = 0;
            for (0..k) |dy| {
                for (0..k) |dx| sum += t[(y * k + dy) * n + x * k + dx];
            }
            out[y * m + x] = sum / @as(f32, @floatFromInt(k * k));
        }
    }
    return out;
}

/// Flat patches with hard edges (the reading that allows Cell). A patch is flat when the 5 by 5 pixels
/// around a place differ by little; edges are hard when most of the picture's change sits in few pixels.
/// Read on the picture at a quarter of its side, where fine noise has averaged out and a patch is still a patch.
fn readFlat(t: []const f32, n: usize, r: *Reading) void {
    const m: usize = @max(@as(usize, 64), n / 4);
    const s = if (m < n) shrink(t, n, m) else alloc.dupe(f32, t) catch die("out of memory", .{});
    defer alloc.free(s);
    var nflat: usize = 0;
    const g2 = alloc.alloc(f32, m * m) catch die("out of memory", .{});
    defer alloc.free(g2);
    var total: f64 = 0;
    for (0..m) |y| {
        for (0..m) |x| {
            var lo: f32 = 1e9;
            var hi: f32 = -1e9;
            for (0..5) |dy| {
                for (0..5) |dx| {
                    const v = s[((y + dy + m - 2) % m) * m + (x + dx + m - 2) % m];
                    lo = @min(lo, v);
                    hi = @max(hi, v);
                }
            }
            if (hi - lo < 0.08) nflat += 1;
            const gx = s[y * m + (x + 1) % m] - s[y * m + (x + m - 1) % m];
            const gy = s[((y + 1) % m) * m + x] - s[((y + m - 1) % m) * m + x];
            g2[y * m + x] = gx * gx + gy * gy;
            total += g2[y * m + x];
        }
    }
    std.mem.sort(f32, g2, {}, std.sort.desc(f32));
    var top: f64 = 0;
    for (g2[0 .. m * m / 20]) |v| top += v;
    r.flat = @as(f32, @floatFromInt(nflat)) / @as(f32, @floatFromInt(m * m));
    r.edge = if (total > 0) @floatCast(top / total) else 0;
}

/// Rings and swirls (the reading that allows Twirl). Around the centre of a ring the picture changes along
/// the line to the centre and not across it. For every centre on a grid and a disc around it: the share of
/// the change that runs along the radius (0.5 for lines with no order, 1 for perfect rings), and the same
/// share for the two halves of the disc's radius, so one round blob is not taken for rings.
fn readRings(t: []const f32, n: usize, r: *Reading) void {
    const m: usize = @min(n, 256); // a typed result: @min with a known bound gives the smallest type that holds it
    const s = if (m < n) shrink(t, n, m) else alloc.dupe(f32, t) catch die("out of memory", .{});
    defer alloc.free(s);
    const gx = alloc.alloc(f32, m * m) catch die("out of memory", .{});
    defer alloc.free(gx);
    const gy = alloc.alloc(f32, m * m) catch die("out of memory", .{});
    defer alloc.free(gy);
    var mean_e: f64 = 0;
    for (0..m) |y| {
        for (0..m) |x| {
            gx[y * m + x] = s[y * m + (x + 1) % m] - s[y * m + (x + m - 1) % m];
            gy[y * m + x] = s[((y + 1) % m) * m + x] - s[((y + m - 1) % m) * m + x];
            mean_e += gx[y * m + x] * gx[y * m + x] + gy[y * m + x] * gy[y * m + x];
        }
    }
    mean_e /= @floatFromInt(m * m);
    const R: i32 = @intCast(m / 10);
    const step: usize = 4;
    const gs = m / step;
    const sc = alloc.alloc(f32, gs * gs) catch die("out of memory", .{});
    defer alloc.free(sc);
    for (0..gs) |cyi| {
        for (0..gs) |cxi| {
            const cx: i32 = @intCast(cxi * step);
            const cy: i32 = @intCast(cyi * step);
            var along = [2]f64{ 0, 0 };
            var all = [2]f64{ 0, 0 };
            var dy: i32 = -R;
            while (dy <= R) : (dy += 1) {
                var dx: i32 = -R;
                while (dx <= R) : (dx += 1) {
                    const d2 = dx * dx + dy * dy;
                    if (d2 > R * R or d2 < 9) continue;
                    const xx: usize = @intCast(@mod(cx + dx, @as(i32, @intCast(m))));
                    const yy: usize = @intCast(@mod(cy + dy, @as(i32, @intCast(m))));
                    const a = gx[yy * m + xx];
                    const b = gy[yy * m + xx];
                    const dot = a * @as(f32, @floatFromInt(dx)) + b * @as(f32, @floatFromInt(dy));
                    const h: usize = if (4 * d2 > R * R) 1 else 0;
                    along[h] += dot * dot / @as(f32, @floatFromInt(d2));
                    all[h] += a * a + b * b;
                }
            }
            const area: f64 = 3.1416 * @as(f64, @floatFromInt(R * R));
            var v: f32 = 0;
            // both halves must hold their share of the picture's change, and both must run round
            if (all[0] > 0.25 * 0.5 * area * mean_e and all[1] > 0.75 * 0.5 * area * mean_e) {
                v = @floatCast(@min(along[0] / all[0], along[1] / all[1]));
            }
            sc[cyi * gs + cxi] = v;
        }
    }
    r.nring = 0;
    r.ring_best = 0;
    for (0..3) |_| {
        var bi: usize = 0;
        var bv: f32 = 0;
        for (sc, 0..) |v, i| {
            if (v > bv) {
                bv = v;
                bi = i;
            }
        }
        if (r.nring == 0) r.ring_best = bv;
        if (bv < 0.74) break;
        const bx = bi % gs;
        const by = bi / gs;
        r.ring[r.nring] = .{ @as(f32, @floatFromInt(bx * step)) / @as(f32, @floatFromInt(m)), @as(f32, @floatFromInt(by * step)) / @as(f32, @floatFromInt(m)), @as(f32, @floatFromInt(R)) / @as(f32, @floatFromInt(m)), bv };
        r.nring += 1;
        // the next centre lies outside this disc
        const rg: i32 = @intCast(2 * @as(usize, @intCast(R)) / step);
        for (0..gs) |y| {
            for (0..gs) |x| {
                var ddx: i32 = @as(i32, @intCast(x)) - @as(i32, @intCast(bx));
                var ddy: i32 = @as(i32, @intCast(y)) - @as(i32, @intCast(by));
                const half: i32 = @intCast(gs / 2);
                if (ddx > half) ddx -= @intCast(gs);
                if (ddx < -half) ddx += @intCast(gs);
                if (ddy > half) ddy -= @intCast(gs);
                if (ddy < -half) ddy += @intCast(gs);
                if (ddx * ddx + ddy * ddy <= rg * rg) sc[y * gs + x] = 0;
            }
        }
    }
}

/// Left-right likeness (the reading that allows a mirror). Two of the found ring centres at one height
/// are a candidate pair; the reading is how alike the picture around one is to the picture around the
/// other turned left to right. The way the lines run is compared, not the brightness or the strength of
/// the edges: a carving lit from one side is bright on one flank and dark on the other, and its mirror
/// twin is lit the other way.
/// The whole picture against its own mirror picture was tried first and does not separate a carving
/// from a noise (0.11 to 0.27 against 0.08 to 0.21): the ornament is a small part of the stone.
fn readMirror(t: []const f32, n: usize, r: *Reading) void {
    r.mirror = 0;
    if (r.nring < 2) return;
    const m: usize = @min(n, 256);
    const s = if (m < n) shrink(t, n, m) else alloc.dupe(f32, t) catch die("out of memory", .{});
    defer alloc.free(s);
    // which way the lines run at every place (the mean over 5 by 5 of the change across squared minus the
    // change down squared, and of twice their product): it does not depend on which flank is the lit one
    const j1 = alloc.alloc(f32, m * m) catch die("out of memory", .{});
    defer alloc.free(j1);
    const j2 = alloc.alloc(f32, m * m) catch die("out of memory", .{});
    defer alloc.free(j2);
    for (0..m) |y| {
        for (0..m) |x| {
            var s1: f32 = 0;
            var s2: f32 = 0;
            for (0..5) |dy| {
                for (0..5) |dx| {
                    const yy = (y + dy + m - 2) % m;
                    const xx = (x + dx + m - 2) % m;
                    const gx = s[yy * m + (xx + 1) % m] - s[yy * m + (xx + m - 1) % m];
                    const gy = s[((yy + 1) % m) * m + xx] - s[((yy + m - 1) % m) * m + xx];
                    s1 += gx * gx - gy * gy;
                    s2 += 2.0 * gx * gy;
                }
            }
            j1[y * m + x] = s1;
            j2[y * m + x] = s2;
        }
    }
    {
        // only the direction counts, not how strong the line is: lines that face the light are strong,
        // and their mirror twins face away from it
        var mx: f32 = 0;
        for (j1, j2) |a, b| mx = @max(mx, @sqrt(a * a + b * b));
        for (j1, j2) |*a, *b| {
            const l = @sqrt(a.* * a.* + b.* * b.*);
            if (l < 0.02 * mx) {
                a.* = 0;
                b.* = 0;
            } else {
                a.* /= l;
                b.* /= l;
            }
        }
    }
    const mi: i32 = @intCast(m);
    for (0..r.nring) |i| {
        for (i + 1..r.nring) |j| {
            // a mirror about an upright line keeps the height: the two centres lie level, within one radius
            if (@abs(r.ring[i][1] - r.ring[j][1]) > r.ring[i][2]) {
                say("  rings {d} and {d} do not lie level: no mirror pair\n", .{ i, j });
                continue;
            }
            const R: i32 = @intFromFloat(1.3 * r.ring[i][2] * @as(f32, @floatFromInt(m)));
            const ax: i32 = @intFromFloat(r.ring[i][0] * @as(f32, @floatFromInt(m)));
            const ay: i32 = @intFromFloat(r.ring[i][1] * @as(f32, @floatFromInt(m)));
            const bx: i32 = @intFromFloat(r.ring[j][0] * @as(f32, @floatFromInt(m)));
            const by: i32 = @intFromFloat(r.ring[j][1] * @as(f32, @floatFromInt(m)));
            var bests = [2]f32{ -1, -1 };
            var best_ox: i32 = 0;
            inline for (.{ 0, 1 }) |flip| {
            const O = @divTrunc(R, 2);
            var oy: i32 = -O;
            while (oy <= O) : (oy += 2) {
                var ox: i32 = -O;
                while (ox <= O) : (ox += 2) {
                    var saa: f64 = 0;
                    var sbb: f64 = 0;
                    var sab: f64 = 0;
                    var dy: i32 = -R;
                    while (dy <= R) : (dy += 2) {
                        var dx: i32 = -R;
                        while (dx <= R) : (dx += 2) {
                            if (dx * dx + dy * dy > R * R) continue;
                            const ia = @as(usize, @intCast(@mod(ay + dy, mi))) * m + @as(usize, @intCast(@mod(ax + dx, mi)));
                            const ib = @as(usize, @intCast(@mod(by + oy + dy, mi))) * m + @as(usize, @intCast(@mod(bx + ox + (if (flip == 0) -dx else dx), mi)));
                            // a line turned left to right leans the other way: the product changes its sign
                            const b2 = if (flip == 0) -j2[ib] else j2[ib];
                            saa += j1[ia] * j1[ia] + j2[ia] * j2[ia];
                            sbb += j1[ib] * j1[ib] + j2[ib] * j2[ib];
                            sab += j1[ia] * j1[ib] + j2[ia] * b2;
                        }
                    }
                    const c: f32 = if (saa > 0 and sbb > 0) @floatCast(sab / @sqrt(saa * sbb)) else 0;
                    if (c > bests[flip]) {
                        bests[flip] = c;
                        if (flip == 0) best_ox = ox;
                    }
                }
            }
            }
            // rings are their own mirror picture, a spiral is not: what counts is how much better the
            // turned picture agrees than the picture as it lies
            const best = bests[0] - @max(0.0, bests[1]);
            say("  rings {d} and {d}: one against the other turned left to right {d:.2}, as it lies {d:.2}\n", .{ i, j, bests[0], bests[1] });
            if (best > r.mirror) {
                r.mirror = best;
                r.mirror_x = 0.5 * @as(f32, @floatFromInt(ax + bx + best_ox)) / @as(f32, @floatFromInt(m));
                r.mirror_a = i;
                r.mirror_b = j;
            }
        }
    }
}

/// The bond (the reading that allows rows moved against each other). The picture is cut into its rows
/// (ky of them, starting at the darkest line); every row's mean across is compared with the next row's,
/// as it lies and moved sideways. In a plain grid a row agrees best with the next as it lies; in a wall
/// it agrees best moved by part of a brick. Also gives the bricks per row, from a row against itself.
fn readBond(t: []const f32, n: usize, ky: usize, r: *Reading) void {
    r.rows = ky;
    if (ky < 2) return;
    const period = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(ky));
    // where the rows start: the darkest line of the picture's rows, folded over one period
    const fold = alloc.alloc(f32, n) catch die("out of memory", .{});
    defer alloc.free(fold);
    const ph: usize = @intFromFloat(@round(period));
    var best_y: usize = 0;
    var best_v: f32 = 1e9;
    for (0..n) |y| {
        var sum: f32 = 0;
        for (0..n) |x| sum += t[y * n + x];
        fold[y] = sum / @as(f32, @floatFromInt(n));
    }
    for (0..ph) |y0| {
        var sum: f32 = 0;
        for (0..ky) |j| sum += fold[(y0 + @as(usize, @intFromFloat(@as(f32, @floatFromInt(j)) * period))) % n];
        if (sum < best_v) {
            best_v = sum;
            best_y = y0;
        }
    }
    r.row0 = @as(f32, @floatFromInt(best_y)) / @as(f32, @floatFromInt(n));
    const prof = alloc.alloc(f32, ky * n) catch die("out of memory", .{});
    defer alloc.free(prof);
    for (0..ky) |j| {
        const ya: usize = best_y + @as(usize, @intFromFloat((@as(f32, @floatFromInt(j)) + 0.25) * period));
        const yb: usize = best_y + @as(usize, @intFromFloat((@as(f32, @floatFromInt(j)) + 0.75) * period));
        var mean: f32 = 0;
        for (0..n) |x| {
            var sum: f32 = 0;
            for (ya..yb + 1) |y| sum += t[(y % n) * n + x];
            prof[j * n + x] = sum / @as(f32, @floatFromInt(yb + 1 - ya));
            mean += prof[j * n + x];
        }
        mean /= @floatFromInt(n);
        for (0..n) |x| prof[j * n + x] -= mean;
    }
    // bricks per row: a row against itself moved sideways, all rows together, with the peak test
    const auto = alloc.alloc(f32, n) catch die("out of memory", .{});
    defer alloc.free(auto);
    const cross = alloc.alloc(f32, n) catch die("out of memory", .{});
    defer alloc.free(cross);
    for (0..n) |sft| {
        var na: f64 = 0;
        var nc: f64 = 0;
        var da: f64 = 0;
        for (0..ky) |j| {
            const a = prof[j * n .. (j + 1) * n];
            const b = prof[((j + 1) % ky) * n .. ((j + 1) % ky + 1) * n];
            for (0..n) |x| {
                na += a[x] * a[(x + sft) % n];
                nc += a[x] * b[(x + sft) % n];
                da += a[x] * a[x];
            }
        }
        auto[sft] = if (da > 0) @floatCast(na / da) else 0;
        cross[sft] = if (da > 0) @floatCast(nc / da) else 0;
    }
    var peak: [33]f32 = undefined;
    var mx: f32 = 0;
    for (2..33) |k| {
        const lag = n / k;
        const half = n / (2 * k);
        peak[k] = auto[lag] - @max(0.0, auto[half]);
        if (peak[k] > mx) mx = peak[k];
    }
    r.bricks = 1;
    if (mx >= 0.25) {
        var k: usize = 32;
        while (k >= 2) : (k -= 1) {
            if (peak[k] >= 0.8 * mx) {
                r.bricks = k;
                break;
            }
        }
    }
    if (r.bricks < 2) return;
    const bl = n / r.bricks;
    var bs: usize = 0;
    var bc: f32 = -1e9;
    for (0..bl) |sft| {
        if (cross[sft] > bc) {
            bc = cross[sft];
            bs = sft;
        }
    }
    r.bond = bc - cross[0];
    r.bond_shift = @as(f32, @floatFromInt(bs)) / @as(f32, @floatFromInt(bl));
}
/// strength of detail per scale of a grey picture (n by n), finest first
fn scalarBands(field: []const f32, n: usize, out: *[MAXLEV]f32) usize {
    var a = alloc.dupe(f32, field) catch die("out of memory", .{});
    var s = n;
    var l: usize = 0;
    while (s >= 4 and l < MAXLEV) : (l += 1) {
        const h = s / 2;
        const b = alloc.alloc(f32, h * h) catch die("out of memory", .{});
        var e: f64 = 0;
        for (0..h) |y| {
            for (0..h) |x| {
                const m = 0.25 * (a[2 * y * s + 2 * x] + a[2 * y * s + 2 * x + 1] + a[(2 * y + 1) * s + 2 * x] + a[(2 * y + 1) * s + 2 * x + 1]);
                b[y * h + x] = m;
                inline for (.{ 0, 1 }) |dy| {
                    inline for (.{ 0, 1 }) |dx| {
                        const d = a[(2 * y + dy) * s + 2 * x + dx] - m;
                        e += d * d;
                    }
                }
            }
        }
        out[l] = @floatCast(@sqrt(e / @as(f64, @floatFromInt(s * s))));
        alloc.free(a);
        a = b;
        s = h;
    }
    alloc.free(a);
    return l;
}

fn perlinNode(f0: u32, oct: u32, fade: f32, seed: u32, amp: f32, c0: u32, c1: u32) Node {
    var nd = Node{ .op = OP_PERLIN, .nw = 11 };
    nd.w[2] = f0;
    nd.w[3] = oct;
    nd.w[4] = wordOf(fade);
    nd.w[5] = seed;
    nd.w[6] = 0;
    nd.w[7] = wordOf(amp);
    nd.w[8] = wordOf(1.0);
    nd.w[9] = c0;
    nd.w[10] = c1;
    return nd;
}

fn corrLag(t: []const f32, n: usize, lag: f32, along_x: bool) f32 {
    const l0: usize = @intFromFloat(@floor(lag));
    const fr = lag - @floor(lag);
    var num0: f64 = 0;
    var num1: f64 = 0;
    var den: f64 = 0;
    for (0..n) |y| {
        for (0..n) |x| {
            const v = t[y * n + x];
            const a = if (along_x) t[y * n + (x + l0) % n] else t[((y + l0) % n) * n + x];
            const b = if (along_x) t[y * n + (x + l0 + 1) % n] else t[((y + l0 + 1) % n) * n + x];
            num0 += v * a;
            num1 += v * b;
            den += v * v;
        }
    }
    if (den <= 0) return 0;
    return @floatCast(((1.0 - fr) * num0 + fr * num1) / den);
}

/// How often the picture repeats across (or down): read from the mean of every column (or row), where a
/// joint adds up along its whole length and a noise averages out. A repeat is a peak: the profile agrees
/// with itself one period away and not half a period away (a smooth noise agrees less the further away).
fn repeats(t: []const f32, n: usize, along_x: bool) usize {
    const m = alloc.alloc(f32, n) catch die("out of memory", .{});
    defer alloc.free(m);
    var mean: f32 = 0;
    for (0..n) |i| {
        var sum: f32 = 0;
        for (0..n) |j| sum += if (along_x) t[j * n + i] else t[i * n + j];
        m[i] = sum / @as(f32, @floatFromInt(n));
        mean += m[i];
    }
    mean /= @floatFromInt(n);
    for (m) |*v| v.* -= mean;
    var peak: [25]f32 = undefined;
    var mx: f32 = 0;
    for (2..25) |k| {
        const lag = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(k));
        peak[k] = corr1(m, lag) - @max(0.0, corr1(m, lag * 0.5));
        if (peak[k] > mx) mx = peak[k];
    }
    if (mx < 0.3) return 1;
    var k: usize = 24;
    while (k >= 2) : (k -= 1) {
        if (peak[k] >= 0.8 * mx) return k;
    }
    return 1;
}

fn repeats2(t: []const f32, n: usize, along_x: bool) usize {
    var peak: [25]f32 = undefined;
    var mx: f32 = 0;
    for (2..25) |k| {
        const lag = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(k));
        peak[k] = corrLag(t, n, lag, along_x) - @max(0.0, corrLag(t, n, lag * 0.5, along_x));
        if (peak[k] > mx) mx = peak[k];
    }
    if (mx < 0.15) return 1;
    var k: usize = 24;
    while (k >= 2) : (k -= 1) {
        if (peak[k] >= 0.8 * mx) return k;
    }
    return 1;
}

fn corr1(m: []const f32, lag: f32) f32 {
    const n = m.len;
    const l0: usize = @intFromFloat(@floor(lag));
    const fr = lag - @floor(lag);
    var num: f64 = 0;
    var den: f64 = 0;
    for (0..n) |i| {
        num += m[i] * ((1.0 - fr) * m[(i + l0) % n] + fr * m[(i + l0 + 1) % n]);
        den += m[i] * m[i];
    }
    return if (den > 0) @floatCast(num / den) else 0;
}

/// the mean of all repeats: the one cell under the picture; returns how much of the contrast it explains
/// With held_out, the cell is made from every second repeat only and judged on the others: a larger cell
/// always fits its own pixels better, so only what it predicts elsewhere counts.
fn meanCell(t: []const f32, n: usize, nx: usize, ny: usize, tm: f64, cell: *[]f32, idx: []u32, cw_out: *usize, ch_out: *usize, held_out: bool) f32 {
    const cwf = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(nx));
    const chf = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(ny));
    const cw: usize = @intFromFloat(@round(cwf));
    const ch: usize = @intFromFloat(@round(chf));
    cw_out.* = cw;
    ch_out.* = ch;
    cell.* = alloc.alloc(f32, cw * ch) catch die("out of memory", .{});
    const cnt = alloc.alloc(f32, cw * ch) catch die("out of memory", .{});
    defer alloc.free(cnt);
    @memset(cell.*, 0);
    @memset(cnt, 0);
    for (0..n) |y| {
        for (0..n) |x| {
            const u = @mod(@as(f32, @floatFromInt(x)), cwf) / cwf;
            const w = @mod(@as(f32, @floatFromInt(y)), chf) / chf;
            const i = @min(ch - 1, @as(usize, @intFromFloat(w * @as(f32, @floatFromInt(ch))))) * cw + @min(cw - 1, @as(usize, @intFromFloat(u * @as(f32, @floatFromInt(cw)))));
            idx[y * n + x] = @intCast(i);
            const odd = ((@as(usize, @intFromFloat(@as(f32, @floatFromInt(x)) / cwf)) + @as(usize, @intFromFloat(@as(f32, @floatFromInt(y)) / chf))) & 1) == 1;
            if (held_out and odd) continue;
            cell.*[i] += t[y * n + x];
            cnt[i] += 1;
        }
    }
    for (cell.*, cnt) |*c, k| c.* = if (k > 0) c.* / k else @floatCast(tm);
    var ve: f64 = 0;
    var vt: f64 = 0;
    if (held_out) {
        if (nx * ny < 2) return -1;
        for (0..n) |y| {
            for (0..n) |x| {
                const odd = ((@as(usize, @intFromFloat(@as(f32, @floatFromInt(x)) / cwf)) + @as(usize, @intFromFloat(@as(f32, @floatFromInt(y)) / chf))) & 1) == 1;
                if (!odd) continue;
                const i = y * n + x;
                ve += (t[i] - cell.*[idx[i]]) * (t[i] - cell.*[idx[i]]);
                vt += (t[i] - tm) * (t[i] - tm);
            }
        }
        return @floatCast(1.0 - ve / @max(vt, 1e-9));
    }
    for (0..n * n) |i| {
        ve += (cell.*[idx[i]] - tm) * (cell.*[idx[i]] - tm);
        vt += (t[i] - tm) * (t[i] - tm);
    }
    return @floatCast(ve / @max(vt, 1e-9));
}

fn readPicture(t: *Target) Reading {
    var r = Reading{};
    const n = @as(usize, 1) << @intCast(t.size);
    r.n = n;
    const px = t.pyr.lev[0];
    // the main colour axis
    var mean = [3]f64{ 0, 0, 0 };
    for (0..n * n) |i| {
        inline for (0..3) |c| mean[c] += px[3 * i + c];
    }
    inline for (0..3) |c| mean[c] /= @floatFromInt(n * n);
    var cov = [_][3]f64{.{ 0, 0, 0 }} ** 3;
    for (0..n * n) |i| {
        inline for (0..3) |a| {
            inline for (0..3) |b| cov[a][b] += (px[3 * i + a] - mean[a]) * (px[3 * i + b] - mean[b]);
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
    r.t = alloc.alloc(f32, n * n) catch die("out of memory", .{});
    var lo: f64 = 1e9;
    var hi: f64 = -1e9;
    for (0..n * n) |i| {
        var s: f64 = 0;
        inline for (0..3) |c| s += (px[3 * i + c] - mean[c]) * v[c];
        r.t[i] = @floatCast(s);
        lo = @min(lo, s);
        hi = @max(hi, s);
    }
    // the two colours: where 1 % and 99 % of the pixels lie along the axis
    var hist = [_]u32{0} ** 256;
    const span = @max(hi - lo, 1e-6);
    for (r.t) |s| hist[@intFromFloat(@min(255.0, (s - lo) / span * 256.0))] += 1;
    var acc: u32 = 0;
    var p1: f64 = lo;
    var p99: f64 = hi;
    var got1 = false;
    for (0..256) |b| {
        acc += hist[b];
        if (!got1 and acc * 100 >= n * n) {
            p1 = lo + span * @as(f64, @floatFromInt(b)) / 256.0;
            got1 = true;
        }
        if (acc * 100 >= n * n * 99) {
            p99 = lo + span * @as(f64, @floatFromInt(b + 1)) / 256.0;
            break;
        }
    }
    if (p99 - p1 < 1e-4) p99 = p1 + 1e-4;
    var ca: [3]f32 = undefined;
    var cb: [3]f32 = undefined;
    inline for (0..3) |c| {
        ca[c] = @floatCast(mean[c] + p1 * v[c]);
        cb[c] = @floatCast(mean[c] + p99 * v[c]);
    }
    {
        // the mortar is the darkest of the same colours: the dark end over the middle, channel by channel
        var jc: [3]f32 = undefined;
        inline for (0..3) |c| jc[c] = @min(1.0, @max(0.0, ca[c]) / @max(0.02, 0.5 * (ca[c] + cb[c])));
        r.joint = 0xff000000 | rgbWord(jc);
    }
    r.c0 = 0xff000000 | rgbWord(ca);
    r.c1 = 0xff000000 | rgbWord(cb);
    {
        // a second colour: pixels whose colour lies off the axis between the two colours, as one cluster
        var cnt: f64 = 0;
        var sumd = [3]f64{ 0, 0, 0 };
        var sumc = [3]f64{ 0, 0, 0 };
        var suml: f64 = 0;
        for (0..n * n) |i| {
            var d: [3]f64 = undefined;
            var l: f64 = 0;
            inline for (0..3) |c| {
                d[c] = px[3 * i + c] - mean[c] - r.t[i] * v[c];
                l += d[c] * d[c];
            }
            l = @sqrt(l);
            if (l < 0.10) continue;
            cnt += 1;
            suml += l;
            inline for (0..3) |c| {
                sumd[c] += d[c];
                sumc[c] += px[3 * i + c];
            }
        }
        if (cnt > 0) {
            r.off = @floatCast(cnt / @as(f64, @floatFromInt(n * n)));
            r.off_coh = @floatCast(@sqrt(sumd[0] * sumd[0] + sumd[1] * sumd[1] + sumd[2] * sumd[2]) / @max(suml, 1e-9));
            const oc = [3]f32{ @floatCast(sumc[0] / cnt), @floatCast(sumc[1] / cnt), @floatCast(sumc[2] / cnt) };
            r.off_col = 0xff000000 | rgbWord(oc);
        }
    }
    for (r.t) |*s| s.* = @floatCast(@min(1.0, @max(0.0, (s.* - p1) / (p99 - p1))));
    readFlat(r.t, n, &r);
    readRings(r.t, n, &r);
    readMirror(r.t, n, &r);

    {
        // grain: the change from a pixel to its neighbour across against the change to the one below
        var ex: f64 = 0;
        var ey: f64 = 0;
        for (0..n) |y| {
            for (0..n) |x| {
                const here = r.t[y * n + x];
                const dx = r.t[y * n + (x + 1) % n] - here;
                const dy = r.t[((y + 1) % n) * n + x] - here;
                ex += dx * dx;
                ey += dy * dy;
            }
        }
        const q = @sqrt(@max(ex, 1e-12) / @max(ey, 1e-12));
        r.aniso = @floatCast(@max(q, 1.0 / q));
        r.grain_down = q > 1.0; // more change across than down: the fibres run down the picture
    }
    // the repeat, and the one cell under it
    var tm: f64 = 0;
    for (r.t) |s| tm += s;
    tm /= @floatFromInt(n * n);
    const tz = alloc.alloc(f32, n * n) catch die("out of memory", .{});
    for (tz, r.t) |*z, s| z.* = s - @as(f32, @floatCast(tm));
    var kx = repeats(tz, n, true);
    var ky = repeats(tz, n, false);
    readBond(r.t, n, ky, &r);
    // a wall is laid in a bond when a row agrees with the next one clearly better moved sideways than as it lies
    r.bonded = ky >= 2 and r.bricks >= 2 and r.bond >= 0.2;
    // the picture with every row moved back by its place in the bond: all bricks lie over each other
    const tc = alloc.dupe(f32, r.t) catch die("out of memory", .{});
    const roll = alloc.alloc(usize, n) catch die("out of memory", .{});
    @memset(roll, 0);
    if (r.bonded) {
        const period = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(ky));
        const y0: usize = @intFromFloat(r.row0 * @as(f32, @floatFromInt(n)));
        const sft = r.bond_shift * @as(f32, @floatFromInt(n / r.bricks));
        for (0..n) |y| {
            const j: usize = @intFromFloat(@as(f32, @floatFromInt((y + n - y0) % n)) / period);
            roll[y] = @as(usize, @intFromFloat(@round(@as(f32, @floatFromInt(j)) * sft))) % n;
            for (0..n) |x| tc[y * n + x] = r.t[y * n + (x + roll[y]) % n];
        }
    }
    // joints seen in the column or row means are trusted as they are (thin joints explain little contrast)
    const by_profile = kx > 1 or ky > 1;
    // rows shifted against each other hide their upright joints from the column means: the picture
    // against itself, moved sideways, still shows them
    if (r.bonded) kx = r.bricks;
    if (kx == 1) kx = repeats2(tz, n, true);
    if (ky == 1) ky = repeats2(tz, n, false);
    const resid = alloc.dupe(f32, r.t) catch die("out of memory", .{});
    if (kx > 1 or ky > 1) {
        // rows that are shifted against each other (a wall's bond) repeat every second row: the larger
        // cells are tried too, and kept when they explain clearly more
        const idx = alloc.alloc(u32, n * n) catch die("out of memory", .{});
        var cell: []f32 = undefined;
        var cw: usize = 0;
        var ch: usize = 0;
        const cands = [4][2]usize{ .{ kx, ky }, .{ kx, ky / 2 }, .{ kx / 2, ky }, .{ kx / 2, ky / 2 } };
        var best_share: f32 = -1;
        var held0: f32 = -1;
        r.nx = kx;
        r.ny = ky;
        for (cands, 0..) |cd, ci| {
            if (cd[0] < 1 or cd[1] < 1) continue;
            if (ci > 0 and r.bonded) continue; // the rows are already laid over each other
            if (ci == 1 and ky % 2 != 0) continue;
            if (ci == 2 and kx % 2 != 0) continue;
            if (ci == 3 and (kx % 2 != 0 or ky % 2 != 0)) continue;
            var c2: []f32 = undefined;
            const sh = meanCell(tc, n, cd[0], cd[1], tm, &c2, idx, &cw, &ch, true);
            alloc.free(c2);
            const need: f32 = if (ci == 0) 1.0 else 1.03;
            if (ci == 0) held0 = sh;
            say("  cell {d} by {d}: predicts {d:.1} % of the contrast of the repeats it was not made from\n", .{ cd[0], cd[1], sh * 100.0 });
            if (sh > 0.02 and (best_share < 0 or sh > best_share * need)) {
                best_share = sh;
                r.nx = cd[0];
                r.ny = cd[1];
            }
        }
        // joints seen in the means are trusted when the cell does not predict the other repeats much worse
        // than no cell at all: thin joints give about zero, a cloud that happens to repeat twice gives far below
        if (best_share < 0 and by_profile and held0 > -0.10) best_share = 0.02;
        if (best_share < 0 and by_profile) say("  a repeat seen in the means is refused: its cell predicts {d:.0} % of the other repeats\n", .{held0 * 100.0});
        r.share = if (best_share < 0) 0 else meanCell(tc, n, r.nx, r.ny, tm, &cell, idx, &cw, &ch, false);
        if (best_share < 0) cell = alloc.alloc(f32, 1) catch die("out of memory", .{});
        if (best_share >= 0) {
            for (0..n) |y| {
                for (0..n) |x| resid[y * n + (x + roll[y]) % n] = tc[y * n + x] - cell[idx[y * n + x]] + @as(f32, @floatCast(tm));
            }
        }
        if (best_share >= 0.02) {
            // the darkest column and row are the joints: the cell starts there
            var bx: usize = 0;
            var by: usize = 0;
            var mnx: f32 = 1e9;
            var mny: f32 = 1e9;
            for (0..cw) |x| {
                var s: f32 = 0;
                for (0..ch) |y| s += cell[y * cw + x];
                if (s / @as(f32, @floatFromInt(ch)) < mnx) {
                    mnx = s / @as(f32, @floatFromInt(ch));
                    bx = x;
                }
            }
            for (0..ch) |y| {
                var s: f32 = 0;
                for (0..cw) |x| s += cell[y * cw + x];
                if (s / @as(f32, @floatFromInt(cw)) < mny) {
                    mny = s / @as(f32, @floatFromInt(cw));
                    by = y;
                }
            }
            r.ox = @as(f32, @floatFromInt(bx)) / @as(f32, @floatFromInt(cw));
            r.oy = @as(f32, @floatFromInt(by)) / @as(f32, @floatFromInt(ch));
            if (r.nx == kx and r.ny == ky) {
                // one shape per cell: its sides are where the column and row means rise out of the joints
                const pxs = alloc.alloc(f32, cw) catch die("out of memory", .{});
                const pys = alloc.alloc(f32, ch) catch die("out of memory", .{});
                for (0..cw) |x| {
                    var sum: f32 = 0;
                    for (0..ch) |y| sum += cell[y * cw + (x + bx) % cw];
                    pxs[x] = sum / @as(f32, @floatFromInt(ch));
                }
                for (0..ch) |y| {
                    var sum: f32 = 0;
                    for (0..cw) |x| sum += cell[((y + by) % ch) * cw + x];
                    pys[y] = sum / @as(f32, @floatFromInt(cw));
                }
                var ext: [2][2]f32 = undefined;
                var lowest: f32 = 1e9;
                var middle: f32 = 0;
                inline for (.{ 0, 1 }) |ax| {
                    const pr = if (ax == 0) pxs else pys;
                    const len = pr.len;
                    const sorted = alloc.dupe(f32, pr) catch die("out of memory", .{});
                    std.mem.sort(f32, sorted, {}, std.sort.asc(f32));
                    const med = sorted[len / 2];
                    const thp = 0.5 * (sorted[0] + med);
                    lowest = @min(lowest, sorted[0]);
                    middle = med;
                    var lo_i: usize = 0;
                    var hi_i: usize = len - 1;
                    const reps = if (ax == 0) r.nx else r.ny;
                    if (reps > 1 and med - sorted[0] > 1e-4) {
                        while (lo_i < len - 1 and pr[lo_i] <= thp) lo_i += 1;
                        while (hi_i > lo_i and pr[hi_i] <= thp) hi_i -= 1;
                    }
                    ext[ax] = .{ 0.5 * @as(f32, @floatFromInt(lo_i + hi_i + 1)) / @as(f32, @floatFromInt(len)), 0.5 * @as(f32, @floatFromInt(hi_i - lo_i + 1)) / @as(f32, @floatFromInt(len)) };
                }
                r.rect[0] = .{ ext[0][0], ext[1][0], ext[0][1], ext[1][1] };
                r.nrect = 1;
                {
                    // the joints' own colour over the shapes' own: both lie on the picture's colour axis, at
                    // the cell's mean brightness outside and inside the shape
                    var tj: f64 = 0;
                    var nj: f64 = 0;
                    var tb2: f64 = 0;
                    var nb2: f64 = 0;
                    for (0..ch) |y| {
                        for (0..cw) |x| {
                            const u = @as(f32, @floatFromInt(x)) / @as(f32, @floatFromInt(cw));
                            const w = @as(f32, @floatFromInt(y)) / @as(f32, @floatFromInt(ch));
                            const c = cell[((y + by) % ch) * cw + (x + bx) % cw];
                            if (@abs(u - ext[0][0]) < ext[0][1] and @abs(w - ext[1][0]) < ext[1][1]) {
                                tb2 += c;
                                nb2 += 1;
                            } else {
                                tj += c;
                                nj += 1;
                            }
                        }
                    }
                    if (nj > 0 and nb2 > 0) {
                        var jc: [3]f32 = undefined;
                        inline for (0..3) |c| {
                            // the mean outside the shape is thinned by the shape's own soft edge: the darkest
                            // line of the cell is the joint itself
                            const cj = ca[c] + (cb[c] - ca[c]) * @min(lowest, @as(f32, @floatCast(tj / nj)));
                            const cbk = ca[c] + (cb[c] - ca[c]) * @max(middle, @as(f32, @floatCast(tb2 / nb2)));
                            jc[c] = @min(1.0, @max(0.0, cj) / @max(0.02, cbk));
                        }
                        r.jmul = 0xff000000 | rgbWord(jc);
                    }
                    r.jw = .{ @max(0.004, 1.0 - 2.0 * ext[0][1]), @max(0.004, 1.0 - 2.0 * ext[1][1]) };
                }
                r.dark = if (middle > 0) @min(1.0, @max(0.0, lowest / middle)) else 0.5;
            }
            // bright shapes: connected parts above the middle between the cell's dark and bright
            var cmin: f32 = 1e9;
            var cmax: f32 = -1e9;
            for (cell) |c| {
                cmin = @min(cmin, c);
                cmax = @max(cmax, c);
            }
            const th = 0.5 * (cmin + cmax);
            const seen = alloc.alloc(bool, cw * ch) catch die("out of memory", .{});
            @memset(seen, false);
            const stack = alloc.alloc([2]i32, cw * ch * 4 + 4) catch die("out of memory", .{});
            var areas = [3]f32{ 0, 0, 0 };
            var sb: f64 = 0;
            var nb: f64 = 0;
            var sd: f64 = 0;
            var ndk: f64 = 0;
            for (cell) |c| {
                if (c > th) {
                    sb += c;
                    nb += 1;
                } else {
                    sd += c;
                    ndk += 1;
                }
            }
            if (r.nrect == 0) r.dark = if (nb > 0 and ndk > 0 and sb > 0) @floatCast((sd / ndk) / (sb / nb)) else 0.5;
            for (0..ch) |y0| {
                if (r.nrect > 0 and r.nx == kx and r.ny == ky) break;
                for (0..cw) |x0| {
                    // rolled coordinates: the cell starts at the joints
                    const rx0 = (x0 + bx) % cw;
                    const ry0 = (y0 + by) % ch;
                    if (seen[ry0 * cw + rx0] or cell[ry0 * cw + rx0] <= th) continue;
                    var sp: usize = 0;
                    stack[0] = .{ @intCast(x0), @intCast(y0) };
                    sp = 1;
                    seen[ry0 * cw + rx0] = true;
                    var x_lo: i32 = @intCast(x0);
                    var x_hi: i32 = @intCast(x0);
                    var y_lo: i32 = @intCast(y0);
                    var y_hi: i32 = @intCast(y0);
                    var area: f32 = 0;
                    while (sp > 0) {
                        sp -= 1;
                        const p = stack[sp];
                        area += 1;
                        x_lo = @min(x_lo, p[0]);
                        x_hi = @max(x_hi, p[0]);
                        y_lo = @min(y_lo, p[1]);
                        y_hi = @max(y_hi, p[1]);
                        const dirs = [4][2]i32{ .{ 1, 0 }, .{ -1, 0 }, .{ 0, 1 }, .{ 0, -1 } };
                        for (dirs) |d| {
                            const qx = p[0] + d[0];
                            const qy = p[1] + d[1];
                            const ux: usize = @intCast(@mod(qx + @as(i32, @intCast(bx)), @as(i32, @intCast(cw))));
                            const uy: usize = @intCast(@mod(qy + @as(i32, @intCast(by)), @as(i32, @intCast(ch))));
                            if (seen[uy * cw + ux] or cell[uy * cw + ux] <= th) continue;
                            if (x_hi - x_lo >= @as(i32, @intCast(cw)) or y_hi - y_lo >= @as(i32, @intCast(ch))) continue;
                            seen[uy * cw + ux] = true;
                            stack[sp] = .{ qx, qy };
                            sp += 1;
                        }
                    }
                    if (area < 0.06 * @as(f32, @floatFromInt(cw * ch))) continue;
                    // keep the three largest
                    var slot: usize = 3;
                    for (0..3) |k| {
                        if (area > areas[k]) {
                            slot = k;
                            break;
                        }
                    }
                    if (slot == 3) continue;
                    var k: usize = 2;
                    while (k > slot) : (k -= 1) {
                        areas[k] = areas[k - 1];
                        r.rect[k] = r.rect[k - 1];
                    }
                    areas[slot] = area;
                    const fw: f32 = @floatFromInt(cw);
                    const fh: f32 = @floatFromInt(ch);
                    r.rect[slot] = .{
                        @mod(0.5 * @as(f32, @floatFromInt(x_lo + x_hi + 1)) / fw, 1.0),
                        @mod(0.5 * @as(f32, @floatFromInt(y_lo + y_hi + 1)) / fh, 1.0),
                        @min(0.5, 0.5 * @as(f32, @floatFromInt(x_hi - x_lo + 1)) / fw),
                        @min(0.5, 0.5 * @as(f32, @floatFromInt(y_hi - y_lo + 1)) / fh),
                    };
                    if (r.nrect < 3) r.nrect += 1;
                }
            }
        }
    }
    if (r.nrect == 0) {
        r.nx = 1;
        r.ny = 1;
        @memcpy(resid, r.t);
    }

    // the noise: which octaves, how strong, from the strength of detail per scale of what the cell leaves
    var tb: [MAXLEV]f32 = undefined;
    const nl = scalarBands(resid, n, &tb);
    const nk: usize = @intCast(t.size - 1);
    var basis: [MAXLEV][MAXLEV]f32 = undefined;
    const rgba = alloc.alloc(u8, n * n * 4) catch die("out of memory", .{});
    const fld = alloc.alloc(f32, n * n) catch die("out of memory", .{});
    for (0..nk) |k| {
        var g = Graph{};
        g.nodes[0] = perlinNode(@intCast(k), 1, 1.0, 1, 1.0, 0xff000000, 0xffffffff);
        g.n = 1;
        const bm = draw(&g, t.size) orelse die("Perlin does not draw", .{});
        wzb_rgba(bm, rgba.ptr);
        for (0..n * n) |i| fld[i] = @as(f32, @floatFromInt(rgba[4 * i])) / 255.0;
        _ = scalarBands(fld, n, &basis[k]);
    }
    var x = [_]f64{0} ** MAXLEV;
    for (0..300) |_| {
        for (0..nk) |k| {
            var num: f64 = 0;
            var den: f64 = 0;
            for (0..nl) |l| {
                var rest: f64 = @as(f64, tb[l]) * tb[l];
                for (0..nk) |j| {
                    if (j != k) rest -= x[j] * @as(f64, basis[j][l]) * basis[j][l];
                }
                const bk = @as(f64, basis[k][l]) * basis[k][l];
                num += bk * rest;
                den += bk * bk;
            }
            x[k] = if (den > 0) @max(0.0, num / den) else 0;
        }
    }
    var amax: f64 = 0;
    for (0..nk) |k| amax = @max(amax, @sqrt(x[k]));
    var first: usize = 0;
    var last: usize = 0;
    var have = false;
    for (0..nk) |k| {
        if (@sqrt(x[k]) >= 0.15 * amax and amax > 0) {
            if (!have) first = k;
            have = true;
            last = k;
        }
    }
    r.f0 = @intCast(first);
    r.oct = @intCast(last - first + 1);
    const a0 = @max(@sqrt(x[first]), 1e-3);
    const a1 = @max(@sqrt(x[last]), 1e-3);
    r.fade = if (last > first) @floatCast(std.math.pow(f64, a1 / a0, 1.0 / @as(f64, @floatFromInt(last - first)))) else 1.0;
    r.fade = @min(2.0, @max(0.25, r.fade));
    r.amp = @floatCast(@min(8.0, @max(0.05, a0)));
    say("readings: flat patches {d:.2}, hard edges {d:.2}; off-axis colour {d:.3} of the pixels, alike {d:.2}, {x:0>6}; rings best {d:.2}, {d} kept; mirror {d:.2} at {d:.2}; rows {d}, bricks {d}, bond {d:.2} at {d:.2} of a brick\n", .{ r.flat, r.edge, r.off, r.off_coh, r.off_col & 0xffffff, r.ring_best, r.nring, r.mirror, r.mirror_x, r.rows, r.bricks, r.bond, r.bond_shift });
    for (r.ring[0..r.nring]) |rg| say("  ring at {d:.2}, {d:.2}, radius {d:.2}: {d:.2}\n", .{ rg[0], rg[1], rg[2], rg[3] });
    if (r.nrect > 0) say("  joints: {x:0>6} of the shapes' colour, {d:.3} and {d:.3} of the cell wide; laid in a bond: {s}\n", .{ r.jmul & 0xffffff, r.jw[0], r.jw[1], if (r.bonded) "yes" else "no" });
    say("read: grain {d:.2}; colours {x:0>6} to {x:0>6}; repeats {d} by {d} (cell explains {d:.0} % of the contrast, {d} shapes); noise octaves {d} to {d}, fall {d:.2}, strength {d:.2}\n", .{ r.aniso, r.c0 & 0xffffff, r.c1 & 0xffffff, r.nx, r.ny, r.share * 100.0, r.nrect, first, last, r.fade, r.amp });
    return r;
}

fn flatNode(col: u32) Node {
    var nd = Node{ .op = OP_FLAT, .nw = 3 };
    nd.w[2] = col;
    return nd;
}

/// add nodes at the end of the graph; the last added is the result
fn append(g: *Graph, nd: Node) usize {
    g.insert(g.n, nd);
    g.root = g.n - 1;
    return g.n - 1;
}

fn grey(v: f32) u32 {
    const b: u32 = @intFromFloat(@min(255.0, @max(0.0, v * 255.0)));
    return 0xff000000 | (b << 16) | (b << 8) | b;
}

// ---------------------------------------------------------------- more of the artists' operators, each a step
//
// Every step makes a handful of candidates in one of .kkrieger's idioms over the colour layer (operator
// `base`), tunes each a little, the best three more, and keeps the best only if it pays for its bytes.

const OP_CELL = 2;
const OP_RANGE = 6;
const OP_HSCB = 7;
const OP_BLUR = 8;
const OP_TWIRL = 15;
const OP_TRANSFORMMUL = 14;
const OP_DISTORT = 22;

const Cand = struct { g: Graph, first: usize, last: usize, base: usize, s: f32 = BAD };

fn keepBest(g: *Graph, t: *Target, base: *usize, cur: *f32, opt: Options, cands: []Cand) bool {
    var order: [3]usize = undefined;
    var nord: usize = 0;
    for (cands, 0..) |*c, i| {
        c.s = cost(tune(&c.g, t, c.first, c.last, opt.quick, false, 1), c.g.bytes(), g.bytes(), opt);
        if (c.s >= BAD) continue;
        var at: usize = nord;
        while (at > 0 and cands[order[at - 1]].s > c.s) at -= 1;
        if (at >= 3) continue;
        var j: usize = @min(nord, 2);
        while (j > at) : (j -= 1) order[j] = order[j - 1];
        order[at] = i;
        if (nord < 3) nord += 1;
    }
    var best_s: f32 = BAD;
    var best_raw: f32 = BAD;
    var best_i: usize = 0;
    for (order[0..nord]) |i| {
        const c = &cands[i];
        _ = tune(&c.g, t, c.first, c.last, opt.deep * 2, true, 3);
        const raw = tune(&c.g, t, 0, c.g.n - 1, opt.deep, false, 1);
        const s = cost(raw, c.g.bytes(), g.bytes(), opt);
        if (s < best_s) {
            best_s = s;
            best_raw = raw;
            best_i = i;
        }
    }
    if (nord == 0 or (!opt.force and best_s >= cur.* * (1.0 - opt.gain))) return false;
    g.* = cands[best_i].g;
    base.* = cands[best_i].base;
    cur.* = best_raw;
    return true;
}

/// put `nd` right after operator k as its only consumer (a one-input operator over the colour layer)
fn wrapOne(c: *Graph, k: usize, nd_in: Node) void {
    var nd = nd_in;
    nd.nin = 1;
    nd.in[0] = @intCast(k);
    c.insert(k + 1, nd);
    c.rewire(k + 1, k, k + 1);
}

/// grain and fibres: the colour layer stretched the way the reading says; a Twirl needs the ring reading
fn stepGrain(g: *Graph, t: *Target, base: *usize, cur: *f32, opt: Options, rd: *const Reading) bool {
    const cands = alloc.alloc(Cand, 8) catch die("out of memory", .{});
    defer alloc.free(cands);
    var n: usize = 0;
    const k = base.*;
    // the way the grain runs is read, not searched: the layer is repeated across the grain, so its detail is
    // finer that way and longer along it. Bending by a noise (Distort) is left out: on these pictures it
    // turned fibres into worms running at a slant.
    const reps = [_]f32{ 2, 4, 8, 16 };
    for (reps) |rp| {
        // how long the fibres are can be set by eye (stretch=N): the measure prefers the shortest on wood
        if (opt.stretch > 0 and rp != opt.stretch) continue;
        var c = g.*;
        var tr = Node{ .op = OP_TRANSFORM, .nw = 8, .lock = true };
        tr.w[0] = wordOf(0.0);
        tr.w[1] = wordOf(if (rd.grain_down) 1.0 / rp else 1.0);
        tr.w[2] = wordOf(if (rd.grain_down) 1.0 else 1.0 / rp);
        tr.w[3] = wordOf(0.5);
        tr.w[4] = wordOf(0.5);
        wrapOne(&c, k, tr);
        cands[n] = .{ .g = c, .first = 0, .last = k, .base = k + 1 };
        n += 1;
    }
    return keepBest(g, t, base, cur, opt, cands[0..n]);
}

/// A second material (allowed by the off-axis colour reading): a mask from a noise, the artists' Perlin with
/// amplify and gamma, filled with the colour read off the axis; that colour is not tuned.
fn stepSecond(g: *Graph, t: *Target, base: *usize, cur: *f32, opt: Options, rd: *const Reading) bool {
    const cands = alloc.alloc(Cand, 24) catch die("out of memory", .{});
    defer alloc.free(cands);
    var n: usize = 0;
    const k = base.*;
    var f0: u32 = 0;
    while (f0 < 6) : (f0 += 1) {
        for (0..3) |_| {
            var c = g.*;
            var mk = perlinNode(f0, 3, 0.7, @intCast(rndN(256)), 3.0, 0xff000000, 0xffffffff);
            mk.w[8] = wordOf(2.0);
            mk.grey = true;
            c.insert(k + 1, mk);
            var fl = flatNode(rd.off_col);
            fl.lock = true;
            c.insert(k + 2, fl);
            var ms = Node{ .op = OP_MASK, .nin = 3, .nw = 1 };
            ms.in[0] = @intCast(k + 1);
            ms.in[1] = @intCast(k + 2);
            ms.in[2] = @intCast(k);
            c.insert(k + 3, ms);
            c.rewire(k + 3, k, k + 3);
            cands[n] = .{ .g = c, .first = k + 1, .last = k + 1, .base = k + 3 };
            n += 1;
        }
    }
    return keepBest(g, t, base, cur, opt, cands[0..n]);
}

/// Patches (allowed by the flat-patch reading): Cell in its flat mode, as a mask for the picture's light colour,
/// and a Blur over the result, which softens the patches' edges as the eye asked.
fn stepPatches(g: *Graph, t: *Target, base: *usize, cur: *f32, opt: Options, rd: *const Reading) bool {
    const cands = alloc.alloc(Cand, 24) catch die("out of memory", .{});
    defer alloc.free(cands);
    var n: usize = 0;
    const k = base.*;
    // Cell in its flat mode (mode 2: every cell one shade between the two colours, no edge lines; read in
    // GenBitmap::Cell and drawn to check): the reading says flat patches, so the mode is not searched.
    // How many cells is tried; with edge lines (modes 1, 3, 7) the result is a web, which the eye refused.
    // Only how many cells and which seed are tried. The cells' shades (black to white, as the mask), the
    // light colour they let through (the picture's own light end) and the Mask stay as built: left to the
    // tuning, the inner measure turned every cell white and the patches were gone.
    const counts = [_]u32{ 12, 24, 48, 96 };
    for (0..12) |ti| {
        var c = g.*;
        var ce = Node{ .op = OP_CELL, .nw = 13, .lockw = 0x1f9c };
        ce.w[2] = 0xff000000;
        ce.w[3] = 0xffffffff;
        ce.w[4] = 0xff000000;
        ce.w[5] = counts[ti % 4];
        ce.w[6] = @intCast(rndN(256));
        ce.w[7] = wordOf(1.0);
        ce.w[8] = wordOf(1.0);
        ce.w[9] = 2;
        ce.w[10] = wordOf(0.06);
        ce.w[11] = 0;
        ce.w[12] = wordOf(0.0);
        c.insert(k + 1, ce);
        var fl = flatNode(rd.c1);
        fl.lock = true;
        c.insert(k + 2, fl);
        var ms = Node{ .op = OP_MASK, .nin = 3, .nw = 1, .lock = true };
        ms.in[0] = @intCast(k + 1);
        ms.in[1] = @intCast(k + 2);
        ms.in[2] = @intCast(k);
        c.insert(k + 3, ms);
        c.rewire(k + 3, k, k + 3);
        var bl = Node{ .op = OP_BLUR, .nw = 4, .lock = true };
        bl.w[0] = 1;
        bl.w[1] = wordOf(opt.blur);
        bl.w[2] = wordOf(opt.blur);
        bl.w[3] = wordOf(1.0);
        wrapOne(&c, k + 3, bl);
        cands[n] = .{ .g = c, .first = k + 1, .last = k + 1, .base = k + 4 };
        n += 1;
    }
    return keepBest(g, t, base, cur, opt, cands[0..n]);
}

/// Rings and swirls (allowed by the ring reading): one Twirl at every centre the reading found; the centres
/// and the radius are not tuned, the turn and its fall are.
fn stepRings(g: *Graph, t: *Target, base: *usize, cur: *f32, opt: Options, rd: *const Reading) bool {
    const cands = alloc.alloc(Cand, 8) catch die("out of memory", .{});
    defer alloc.free(cands);
    var n: usize = 0;
    const k = base.*;
    const turns = [_]f32{ 0.5, -0.5, 1.0, -1.0 };
    const falls = [_]f32{ 1.0, 2.0 };
    for (turns) |tn| {
        for (falls) |fa| {
            var c = g.*;
            var kk = k;
            for (rd.ring[0..rd.nring]) |rg| {
                // the radius is the reading's too: left free, the tuning grew one knot into a swirl half the picture wide
                // the fall is one of the two tried, not tuned: tuned, it went to 0, which turns the whole disc as
                // one plate with a visible rim
                var tw = Node{ .op = OP_TWIRL, .nw = 7, .lockw = (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5) | (1 << 6) };
                tw.w[0] = wordOf(tn);
                tw.w[1] = wordOf(fa);
                tw.w[2] = wordOf(1.3 * rg[2]);
                tw.w[3] = wordOf(1.3 * rg[2]);
                tw.w[4] = wordOf(rg[0]);
                tw.w[5] = wordOf(rg[1]);
                tw.w[6] = 0;
                wrapOne(&c, kk, tw);
                kk += 1;
            }
            cands[n] = .{ .g = c, .first = k + 1, .last = kk, .base = kk };
            n += 1;
        }
    }
    return keepBest(g, t, base, cur, opt, cands[0..n]);
}

/// A mirrored spiral (allowed by the mirror reading), the way t.cem.03's artists carved theirs: a GlowRect at
/// the ring's centre, twisted by a Twirl and by a second one, mirrored by a Transform with a negative scale
/// across, both merged; that drawing is the height of a lit relief over the surface.
fn stepMirror(g: *Graph, t: *Target, cur: *f32, opt: Options, rd: *const Reading) bool {
    const a = rd.ring[rd.mirror_a];
    const rr = 1.5 * a[2];
    const turns = [_]f32{ 1.5, -1.5, 2.5, -2.5 };
    var best: Graph = undefined;
    var best_s: f32 = BAD;
    var o2 = opt;
    o2.force = true;
    o2.relief = 4;
    for (turns) |tn| {
        var c = g.*;
        const root0 = c.root;
        var fl = flatNode(0xff000000);
        fl.lock = true;
        _ = append(&c, fl);
        const n0 = c.n - 1;
        var gr = Node{ .op = OP_GLOWRECT, .nin = 1, .nw = 11, .lock = true };
        gr.in[0] = @intCast(c.n - 1);
        gr.w[0] = wordOf(a[0] + 0.5 * rr);
        gr.w[1] = wordOf(a[1]);
        gr.w[2] = wordOf(0.01);
        gr.w[3] = wordOf(0.01);
        gr.w[4] = wordOf(0.5 * rr);
        gr.w[5] = wordOf(0.22 * rr);
        gr.w[6] = 0xffffffff;
        gr.w[7] = wordOf(1.0);
        gr.w[8] = wordOf(0.5);
        gr.w[9] = 1;
        gr.w[10] = 0;
        _ = append(&c, gr);
        inline for (.{ 1.0, 0.5 }, .{ 1.0, 2.0 }) |part, fa| {
            var tw = Node{ .op = OP_TWIRL, .nin = 1, .nw = 7, .lockw = (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5) | (1 << 6) };
            tw.in[0] = @intCast(c.n - 1);
            tw.w[0] = wordOf(tn * part);
            tw.w[1] = wordOf(fa);
            tw.w[2] = wordOf(1.2 * rr);
            tw.w[3] = wordOf(1.2 * rr);
            tw.w[4] = wordOf(a[0]);
            tw.w[5] = wordOf(a[1]);
            tw.w[6] = 0;
            _ = append(&c, tw);
        }
        const twisted = c.n - 1;
        var tr = Node{ .op = OP_TRANSFORM, .nin = 1, .nw = 8, .lock = true };
        tr.in[0] = @intCast(twisted);
        tr.w[0] = wordOf(0.0);
        tr.w[1] = wordOf(-1.0);
        tr.w[2] = wordOf(1.0);
        tr.w[3] = wordOf(0.5 - (2.0 * rd.mirror_x - 1.0));
        tr.w[4] = wordOf(0.5);
        tr.w[5] = 0;
        _ = append(&c, tr);
        var mg = Node{ .op = OP_MERGE, .nin = 2, .nw = 1, .shape = true, .lock = true };
        mg.in[0] = @intCast(twisted);
        mg.in[1] = @intCast(c.n - 1);
        mg.w[0] = 0;
        _ = append(&c, mg);
        c.root = root0;
        var s: f32 = BAD;
        if (!tryRelief(&c, t, &s, o2)) continue;
        for (c.nodes[n0..c.n]) |*x| x.keep = true;
        say("  the spiral turned {d:.1} and its mirror twin: measure {d:.5}\n", .{ tn, s });
        if (s < best_s) {
            best_s = s;
            best = c;
        }
    }
    if (best_s >= BAD) return false;
    g.* = best;
    cur.* = best_s;
    return true;
}

/// The repeated shape with its joints made by .kkrieger's outline trick. The shape is drawn once in white on
/// black and repeated (Transform; in a bond the rows are laid by a TransformMul, each moved down one row and
/// sideways by the measured part of a brick). The joints are the Blur of the shape minus the shape, their
/// brightness set (HSCB), turned into the mortar's colour (Range: white to the joints' colour measured in the
/// picture) and multiplied into the surface. The blurred shape is the height of the relief, for the lit edge.
const Outline = struct { first: usize, sub: usize, hscb: usize, root: usize };

fn appendOutline(g: *Graph, r: *const Reading, colour: usize, opt: Options) Outline {
    const first = g.n;
    const fx: f32 = @floatFromInt(r.nx);
    const fy: f32 = @floatFromInt(r.ny);
    const a = r.rect[0];
    const edge: f32 = 0.008;
    var fl = flatNode(0xff000000);
    fl.lock = true;
    _ = append(g, fl);
    var nd = Node{ .op = OP_GLOWRECT, .nin = 1, .nw = 11, .lock = true };
    nd.in[0] = @intCast(g.n - 1);
    nd.w[0] = wordOf(a[0]);
    nd.w[1] = wordOf(if (r.bonded) @mod((r.oy + a[1]) / fy, 1.0) else a[1]);
    nd.w[2] = wordOf(edge);
    nd.w[3] = wordOf(if (r.bonded) edge / fy else edge);
    nd.w[4] = wordOf(@max(0.01, a[2] - edge));
    nd.w[5] = wordOf(if (r.bonded) @max(0.002, (a[3] - edge) / fy) else @max(0.01, a[3] - edge));
    nd.w[6] = 0xffffffff;
    nd.w[7] = wordOf(1.0);
    nd.w[8] = wordOf(0.5);
    nd.w[9] = 1;
    nd.w[10] = 0;
    _ = append(g, nd);
    var tr = Node{ .op = OP_TRANSFORM, .nin = 1, .nw = 8, .lock = true };
    tr.in[0] = @intCast(g.n - 1);
    tr.w[0] = wordOf(0.0);
    tr.w[1] = wordOf(1.0 / fx);
    tr.w[2] = wordOf(if (r.bonded) 1.0 else 1.0 / fy);
    tr.w[3] = wordOf(@mod(0.5 * fx - r.ox, 1.0));
    tr.w[4] = wordOf(if (r.bonded) 0.5 else @mod(0.5 * fy - r.oy, 1.0));
    tr.w[5] = 0;
    _ = append(g, tr);
    if (r.bonded) {
        // RotateMul in wz3_bitmap_code.cpp: mode 16 doubles the picture `count` times, each time merging it
        // with itself moved; the first move is (t - 0.5) / (2^count - 1), and a move of t - 0.5 carries the
        // picture by minus that. Without mode 16 it adds `count` copies of the first picture, the i-th moved
        // i times (t - 0.5) / count.
        var mul = Node{ .op = OP_TRANSFORMMUL, .nin = 1, .nw = 10, .lock = true };
        mul.in[0] = @intCast(g.n - 1);
        var pow2: u32 = 0;
        while ((@as(usize, 1) << @intCast(pow2)) < r.ny) pow2 += 1;
        const is_pow2 = (@as(usize, 1) << @intCast(pow2)) == r.ny;
        mul.w[0] = wordOf(0.0);
        mul.w[1] = wordOf(1.0);
        mul.w[2] = wordOf(1.0);
        mul.w[3] = wordOf(0.5 - (fy - 1.0) * r.bond_shift / fx);
        mul.w[4] = wordOf(0.5 - (fy - 1.0) / fy);
        mul.w[5] = 0;
        mul.w[6] = 0xffffffff;
        mul.w[7] = if (is_pow2) 16 else 0;
        mul.w[8] = if (is_pow2) pow2 else @intCast(r.ny - 1);
        mul.w[9] = 0xffffffff;
        _ = append(g, mul);
    }
    const shape = g.n - 1;
    // wholly kept from the tuning: with its strength free, the tuning faded the outline away on the brick wall
    var bl = Node{ .op = OP_BLUR, .nin = 1, .nw = 4, .lock = true, .shape = true };
    bl.in[0] = @intCast(shape);
    bl.w[0] = 1;
    // the blur reaches across the joint: what it carries out of the shapes fills the joint from both sides
    bl.w[1] = wordOf(@max(0.001, opt.jointw * r.jw[0] / fx));
    bl.w[2] = wordOf(@max(0.001, opt.jointw * r.jw[1] / fy));
    bl.w[3] = wordOf(1.0);
    const blurred = append(g, bl);
    var sub = Node{ .op = OP_MERGE, .nin = 2, .nw = 1, .lock = true };
    sub.in[0] = @intCast(blurred);
    sub.in[1] = @intCast(shape);
    sub.w[0] = 1; // Merge 1 is the first minus the second: what the blur carried outside the shape
    const subi = append(g, sub);
    // the brightness is set after the outline is drawn once: its brightest place becomes the full joint
    var hs = Node{ .op = OP_HSCB, .nin = 1, .nw = 4, .lock = true };
    hs.in[0] = @intCast(g.n - 1);
    hs.w[0] = wordOf(0.0);
    hs.w[1] = wordOf(1.0);
    hs.w[2] = wordOf(1.0);
    hs.w[3] = wordOf(2.0);
    const hsi = append(g, hs);
    var rg = Node{ .op = OP_RANGE, .nin = 1, .nw = 3, .lock = true };
    rg.in[0] = @intCast(g.n - 1);
    rg.w[0] = 1;
    rg.w[1] = 0xffffffff;
    rg.w[2] = r.jmul;
    _ = append(g, rg);
    var mg = Node{ .op = OP_MERGE, .nin = 2, .nw = 1, .lock = true };
    mg.in[0] = @intCast(colour);
    mg.in[1] = @intCast(g.n - 1);
    mg.w[0] = 2;
    const root = append(g, mg);
    for (g.nodes[first..g.n]) |*x| x.keep = true;
    return .{ .first = first, .sub = subi, .hscb = hsi, .root = root };
}

/// hard edges, contrast and softness: real Range, HSCB and Blur instances over the colour layer
fn stepTone(g: *Graph, t: *Target, base: *usize, cur: *f32, opt: Options) bool {
    const cands = alloc.alloc(Cand, 24) catch die("out of memory", .{});
    defer alloc.free(cands);
    var n: usize = 0;
    const k = base.*;
    const which = [_]u8{ OP_RANGE, OP_HSCB, OP_BLUR };
    for (which) |op| {
        for (0..7) |_| {
            const in = randomInst(op) orelse break;
            var c = g.*;
            wrapOne(&c, k, nodeOf(in));
            cands[n] = .{ .g = c, .first = k + 1, .last = k + 1, .base = k + 1 };
            n += 1;
        }
    }
    return keepBest(g, t, base, cur, opt, cands[0..n]);
}

// ---------------------------------------------------------------- the search

const Best = struct { g: Graph, s: f32, first: usize, last: usize };

fn randomInst(op: u8) ?Inst {
    for (0..400) |_| {
        const in = insts.items[rndN(insts.items.len)];
        if (in.op == op) return in;
    }
    return null;
}

fn cost(s: f32, bytes_new: usize, bytes_old: usize, opt: Options) f32 {
    const d: f32 = @as(f32, @floatFromInt(bytes_new)) - @as(f32, @floatFromInt(bytes_old));
    return s * (1.0 + opt.byte_cost * d);
}

/// one more noise over the colour layer (operator `base`): which octaves and how it joins are tried in turn,
/// the best few tuned (seed included), the best kept if it pays for its bytes
fn addNoise(g: *Graph, t: *Target, base: *usize, cur: *f32, opt: Options) bool {
    const TOPN = 3;
    var top: [TOPN]Best = undefined;
    var ntop: usize = 0;
    const modes = [_]u32{ 0, 2, 1 };
    const octs = [_]u32{ 1, 3 };
    var f0: u32 = 0;
    while (f0 + 1 < t.size) : (f0 += 1) {
        for (octs) |oc| {
            for (modes) |md| {
                var c = g.*;
                const k = base.*;
                var pn = perlinNode(f0, oc, 0.7, @intCast(rndN(256)), 1.0, if (md == 2) 0xffa0a0a0 else 0xff000000, if (md == 2) 0xffffffff else 0xff404040);
                pn.nin = 0;
                pn.grey = true;
                c.insert(k + 1, pn);
                var mg = Node{ .op = OP_MERGE, .nin = 2, .nw = 1 };
                mg.in[0] = @intCast(k);
                mg.in[1] = @intCast(k + 1);
                mg.w[0] = md;
                c.insert(k + 2, mg);
                c.rewire(k + 2, k, k + 2);
                const s = cost(tune(&c, t, k + 1, k + 1, opt.quick, false, 1), c.bytes(), g.bytes(), opt);
                if (s >= BAD) continue;
                var at: usize = ntop;
                while (at > 0 and top[at - 1].s > s) at -= 1;
                if (at >= TOPN) continue;
                var j: usize = @min(ntop, TOPN - 1);
                while (j > at) : (j -= 1) top[j] = top[j - 1];
                top[at] = .{ .g = c, .s = s, .first = k + 1, .last = k + 1 };
                if (ntop < TOPN) ntop += 1;
            }
        }
    }
    var best_s: f32 = BAD;
    var best_raw: f32 = BAD;
    var best_i: usize = 0;
    for (0..ntop) |i| {
        _ = tune(&top[i].g, t, top[i].first, top[i].last, opt.deep * 2, true, 3);
        const raw = tune(&top[i].g, t, 0, top[i].g.n - 1, opt.deep, false, 1);
        const s = cost(raw, top[i].g.bytes(), g.bytes(), opt);
        if (s < best_s) {
            best_s = s;
            best_raw = raw;
            best_i = i;
        }
    }
    if (ntop == 0 or best_s >= cur.* * (1.0 - opt.gain)) return false;
    g.* = top[best_i].g;
    cur.* = best_raw;
    base.* += 2;
    return true;
}

/// a relief lit the way .kkrieger's artists lit theirs: a real Normals over an operator already there,
/// a real Bump over the result, their values tuned
fn tryRelief(g: *Graph, t: *Target, cur: *f32, opt: Options) bool {
    var best: Graph = undefined;
    var best_s: f32 = BAD;
    for (0..opt.relief) |trial| {
        var c = g.*;
        const nmi = randomInst(OP_NORMALS) orelse return false;
        const bui = randomInst(OP_BUMP) orelse return false;
        // the height: the repeated shape when there is one (the artist's usual height), else the picture so far
        var h = c.root;
        for (c.nodes[0..c.n], 0..) |nd, i| {
            if (nd.shape) h = i;
        }
        const old = c.root;
        if (trial % 2 == 1) {
            // the bevel: the height softened first, as the artists did before Normals
            if (randomInst(OP_BLUR)) |bi| {
                var bl = nodeOf(bi);
                bl.nin = 1;
                bl.in[0] = @intCast(h);
                h = append(&c, bl);
            }
        }
        var nm = nodeOf(nmi);
        nm.in[0] = @intCast(h);
        const ni = append(&c, nm);
        var bu = nodeOf(bui);
        // the light starts white over a grey shade, no shine: a material's own colours come from its
        // colour layer, and .kkrieger's coloured lamps are not part of a surface
        bu.w[6] = 0xffffffff;
        bu.w[7] = 0xff808080;
        bu.w[11] = 0xff000000;
        bu.lockw = 1 << 11; // no shine is added by the tuning: a glossy groove edge is wrong to the eye
        bu.grey = true;
        bu.nin = 2;
        bu.in[0] = @intCast(old);
        bu.in[1] = @intCast(ni);
        _ = append(&c, bu);
        const s = tune(&c, t, old + 1, c.n - 1, opt.quick * 2, false, 2);
        if (s < best_s) {
            best_s = s;
            best = c;
        }
    }
    if (best_s >= BAD) return false;
    _ = tune(&best, t, best.n - 3, best.n - 1, opt.deep * 2, true, 3);
    const raw = tune(&best, t, 0, best.n - 1, opt.deep, false, 1);
    if (!opt.force and cost(raw, best.bytes(), g.bytes(), opt) >= cur.* * (1.0 - opt.gain)) return false;
    g.* = best;
    cur.* = raw;
    return true;
}

fn saveRung(prefix: []const u8, rung: usize, g: *const Graph, t: *Target, s: f32, log: *std.ArrayList(u8), tsec: f64) void {
    var name: [1024]u8 = undefined;
    var buf: [1 << 16]u8 = undefined;
    const p = std.fmt.bufPrint(&name, "{s}.r{d:0>2}.script", .{ prefix, rung }) catch die("path too long", .{});
    writeFile(p, scriptText(g, &buf));
    var line: [200]u8 = undefined;
    const l = std.fmt.bufPrint(&line, "{d} {d} {d} {d:.6} {d:.1}\n", .{ rung, g.n, g.bytes(), s, tsec }) catch unreachable;
    log.appendSlice(alloc, l) catch die("out of memory", .{});
    _ = t;
}

fn fit(target_path: [*:0]const u8, prior_path: [*:0]const u8, prefix: []const u8, opt: Options) void {
    const t0 = seconds();
    const img = readPpm(target_path);
    var full: u32 = 0;
    while ((@as(usize, 1) << @intCast(full)) < img.w) full += 1;
    const work = @min(opt.work, full);
    var t = makeTarget(img, work);
    loadPrior(prior_path);
    makePalette(&t);
    rng_state = 0x2545F4914F6CDD1D ^ (opt.seed *% 0x9E3779B97F4A7C15);
    _ = rnd();
    say("picture {d}x{d}; searching at {d}x{d}; prior: {d} operator instances, {d} chains\n", .{ img.w, img.h, @as(usize, 1) << @intCast(work), @as(usize, 1) << @intCast(work), insts.items.len, chains.items.len });

    var log: std.ArrayList(u8) = .empty;
    var g = Graph{};
    g.nodes[0] = Node{ .op = OP_FLAT, .nw = 3 };
    g.nodes[0].w[2] = 0xff000000 | palette[8];
    g.n = 1;
    g.root = 0;
    var cur = tune(&g, &t, 0, 0, 200, true, 3);
    var rung: usize = 0;
    saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
    say("rung 0: flat colour, {d} bytes, measure {d:.5}\n", .{ g.bytes(), cur });

    // the picture read backwards: the noise between its two colours, the repeated shape, the relief
    // read at the picture's own size: a thin joint is lost in a smaller copy
    var tread = makeTarget(img, full);
    const rd = readPicture(&tread);
    freeTarget(&tread);
    {
        var line: [200]u8 = undefined;
        var len: usize = 0;
        inline for (@typeInfo(Structure).@"enum".fields) |f| {
            if (allowed(&rd, @enumFromInt(f.value), opt)) {
                const w = std.fmt.bufPrint(line[len..], " {s}", .{f.name}) catch unreachable;
                len += w.len;
            }
        }
        say("allowed by the readings:{s}\n", .{line[0..len]});
    }
    if (opt.read_only) return;
    if (!allowed(&rd, opt.structure, opt)) die("structure {s} is refused: its reading does not allow it on this picture", .{@tagName(opt.structure)});
    var base: usize = 0;
    var has_relief = false;
    {
        var c = Graph{};
        c.nodes[0] = perlinNode(rd.f0, rd.oct, rd.fade, 1, rd.amp, rd.c0, rd.c1);
        c.n = 1;
        c.root = 0;
        const s = tune(&c, &t, 0, 0, opt.deep * 3, true, 3);
        if (cost(s, c.bytes(), g.bytes(), opt) < cur) {
            g = c;
            cur = s;
            rung += 1;
            saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
            say("rung {d}: the noise between the two colours, {d} bytes, measure {d:.5}\n", .{ rung, g.bytes(), cur });
        }
    }
    if (opt.surface2 and g.nodes[0].op == OP_PERLIN) {
        // the surface repeated 2 by 2 over the picture: the same noise, its granules half the size and four times as many
        var tr = Node{ .op = OP_TRANSFORM, .nw = 8, .lock = true };
        tr.w[0] = wordOf(0.0);
        tr.w[1] = wordOf(0.5);
        tr.w[2] = wordOf(0.5);
        tr.w[3] = wordOf(0.5);
        tr.w[4] = wordOf(0.5);
        wrapOne(&g, 0, tr);
        base = 1;
        cur = tune(&g, &t, 0, 1, opt.deep * 3, true, 3);
        rung += 1;
        saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
        say("rung {d}: the surface repeated 2 by 2, {d} bytes, measure {d:.5}\n", .{ rung, g.bytes(), cur });
    }
    if (opt.structure == .shape) {
        const colour = g.root;
        const ol = appendOutline(&g, &rd, colour, opt);
        {
            var gs = g;
            gs.root = ol.sub;
            const bm = draw(&gs, t.size) orelse die("the outline does not draw", .{});
            wzb_rgba(bm, t.rgba.ptr);
            var mx: u8 = 1;
            const side = @as(usize, 1) << @intCast(t.size);
            for (0..side * side) |i| mx = @max(mx, t.rgba[4 * i]);
            g.nodes[ol.hscb].w[3] = wordOf(@min(16.0, 255.0 / @as(f32, @floatFromInt(mx))));
            say("  the outline's brightest place is {d} of 255: brightness set to {d:.2}\n", .{ mx, f32of(g.nodes[ol.hscb].w[3]) });
        }
        _ = tune(&g, &t, colour + 1, g.n - 1, opt.deep * 3, false, 3);
        cur = tune(&g, &t, 0, g.n - 1, opt.deep * 2, true, 2);
        rung += 1;
        saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
        say("rung {d}: the repeated shape{s}, joints by the outline, {d} operators, {d} bytes, measure {d:.5}\n", .{ rung, if (rd.bonded) " in a bond" else "", g.n, g.bytes(), cur });
    }
    var structure_done = opt.structure == .shape or opt.structure == .plain;

    const TOP = 4;
    var size = work;
    var ncand = opt.candidates;
    while (true) {
        if (!structure_done) {
            // the one structure this run builds; its best candidate is kept without the pay test, because
            // the choice between the structures is made by eye, on the finished drawings
            structure_done = true;
            var of = opt;
            of.force = true;
            var ok = false;
            const base0 = base;
            switch (opt.structure) {
                .patches => ok = stepPatches(&g, &t, &base, &cur, of, &rd),
                .second => ok = stepSecond(&g, &t, &base, &cur, of, &rd),
                .grain => ok = stepGrain(&g, &t, &base, &cur, of, &rd),
                .rings => {
                    if (rd.aniso >= opt.grain) _ = stepGrain(&g, &t, &base, &cur, of, &rd);
                    ok = stepRings(&g, &t, &base, &cur, of, &rd);
                },
                .mirror => {
                    ok = stepMirror(&g, &t, &cur, of, &rd);
                    if (ok) has_relief = true;
                },
                else => {},
            }
            if (ok) {
                for (g.nodes[0..g.n], 0..) |*x, i| {
                    if (i > base0 and i <= base) x.keep = true;
                }
                rung += 1;
                saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
                say("rung {d}: structure {s}, {d} operators, {d} bytes, measure {d:.5}, {d:.0} s\n", .{ rung, @tagName(opt.structure), g.n, g.bytes(), cur, seconds() - t0 });
            } else say("structure {s} could not be built: no candidate drew\n", .{@tagName(opt.structure)});
        }
        if (!has_relief and tryRelief(&g, &t, &cur, opt)) {
            has_relief = true;
            rung += 1;
            saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
            say("rung {d} at {d} px: a lit relief, {d} operators, {d} bytes, measure {d:.5}\n", .{ rung, @as(usize, 1) << @intCast(size), g.n, g.bytes(), cur });
        }
        if (size < full or full == work) {
            // tone adds no structure and is kept only when it pays
            if (g.n + 4 < opt.max_ops and stepTone(&g, &t, &base, &cur, opt)) {
                rung += 1;
                saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
                say("rung {d} at {d} px: tone (Range, HSCB or Blur), {d} operators, {d} bytes, measure {d:.5}, {d:.0} s\n", .{ rung, @as(usize, 1) << @intCast(size), g.n, g.bytes(), cur, seconds() - t0 });
            }
        }
        for (0..opt.noises) |_| {
            if (g.n + 2 >= opt.max_ops or !addNoise(&g, &t, &base, &cur, opt)) break;
            rung += 1;
            saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
            say("rung {d} at {d} px: one more noise, {d} operators, {d} bytes, measure {d:.5}, {d:.0} s\n", .{ rung, @as(usize, 1) << @intCast(size), g.n, g.bytes(), cur, seconds() - t0 });
        }
        if (!has_relief and tryRelief(&g, &t, &cur, opt)) {
            has_relief = true;
            rung += 1;
            saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
            say("rung {d} at {d} px: a lit relief, {d} operators, {d} bytes, measure {d:.5}\n", .{ rung, @as(usize, 1) << @intCast(size), g.n, g.bytes(), cur });
        }
        var fails: usize = if (opt.grow == 0) opt.patience else 0;
        ncand = opt.grow;
        while (g.n < opt.max_ops and fails < opt.patience) {
            var top: [TOP]Best = undefined;
            var ntop: usize = 0;
            for (0..ncand) |_| {
                var c = g;
                const before_bytes = c.bytes();
                const mv = randomMove(&c);
                if (!mv.ok) continue;
                var s = tune(&c, &t, mv.first, mv.last, opt.quick, false, 1);
                if (s >= BAD) continue;
                // a longer procedure must pay for its bytes
                s *= 1.0 + opt.byte_cost * @as(f32, @floatFromInt(c.bytes() - before_bytes));
                var at: usize = ntop;
                while (at > 0 and top[at - 1].s > s) at -= 1;
                if (at >= TOP) continue;
                var j: usize = @min(ntop, TOP - 1);
                while (j > at) : (j -= 1) top[j] = top[j - 1];
                top[at] = .{ .g = c, .s = s, .first = mv.first, .last = mv.last };
                if (ntop < TOP) ntop += 1;
            }
            var best_s: f32 = BAD;
            var best_raw: f32 = BAD;
            var best_i: usize = 0;
            for (0..ntop) |i| {
                _ = tune(&top[i].g, &t, top[i].first, top[i].last, opt.deep, true, 3);
                const raw = tune(&top[i].g, &t, 0, top[i].g.n - 1, opt.deep, false, 1);
                top[i].s = raw * (1.0 + opt.byte_cost * @as(f32, @floatFromInt(top[i].g.bytes() - g.bytes())));
                if (top[i].s < best_s) {
                    best_s = top[i].s;
                    best_raw = raw;
                    best_i = i;
                }
            }
            if (ntop > 0 and best_s < cur * (1.0 - opt.gain)) {
                g = top[best_i].g;
                cur = best_raw;
                rung += 1;
                fails = 0;
                saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
                say("rung {d} at {d} px: {d} operators, {d} bytes, measure {d:.5}, top {s}, {d:.0} s\n", .{ rung, @as(usize, 1) << @intCast(size), g.n, g.bytes(), cur, ops[g.nodes[g.root].op].name, seconds() - t0 });
            } else {
                fails += 1;
            }
        }
        // operators that no longer earn their bytes go; the surface layer's top is followed through it
        for (g.nodes[0..g.n], 0..) |*x, xi| x.is_base = xi == base;
        var i: usize = 0;
        while (i < g.n) {
            const nd = g.nodes[i];
            if (i == g.root or nd.nin == 0 or nd.keep) {
                i += 1;
                continue;
            }
            var removed = false;
            for (0..nd.nin) |slot| {
                var c = g;
                if (nd.is_base) c.nodes[nd.in[slot]].is_base = true;
                c.rewire(i, i, nd.in[slot]);
                c.prune();
                const s = score(&c, &t);
                if (s <= cur * (1.0 + opt.byte_cost * @as(f32, @floatFromInt(g.bytes() - c.bytes())))) {
                    g = c;
                    cur = s;
                    removed = true;
                    break;
                }
            }
            if (!removed) i += 1;
        }
        for (g.nodes[0..g.n], 0..) |x, xi| {
            if (x.is_base) base = xi;
        }
        cur = tune(&g, &t, 0, g.n - 1, opt.final, size == work, 2);
        rung += 1;
        saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
        say("cleaned and tuned at {d} px: {d} operators, {d} bytes, measure {d:.5}, {d:.0} s\n", .{ @as(usize, 1) << @intCast(size), g.n, g.bytes(), cur, seconds() - t0 });
        if (size >= full) break;
        // the next finer size: what only shows there is added there
        size += 1;
        cacheClear();
        cache_cap = if (size >= 9) 500 else 1500;
        freeTarget(&t);
        t = makeTarget(img, size);
        cur = score(&g, &t);
        if (base >= g.n) base = g.root;
    }
    var buf: [1 << 16]u8 = undefined;
    var name: [1024]u8 = undefined;
    writeFile(std.fmt.bufPrint(&name, "{s}.script", .{prefix}) catch unreachable, scriptText(&g, &buf));
    const bm = draw(&g, full) orelse die("the final procedure does not draw", .{});
    const rgba = alloc.alloc(u8, img.w * img.w * 4) catch die("out of memory", .{});
    wzb_rgba(bm, rgba.ptr);
    writePpm(std.fmt.bufPrint(&name, "{s}.ppm", .{prefix}) catch unreachable, rgba, img.w, img.w);
    const tail = std.fmt.bufPrint(&buf, "# rung operators bytes measure seconds\n# total {d:.1} s, {d} graphs asked, {d} operators drawn, {d} refused, {d} too slow\n", .{ seconds() - t0, n_eval, n_draw, n_refused, n_slow }) catch unreachable;
    log.appendSlice(alloc, tail) catch {};
    writeFile(std.fmt.bufPrint(&name, "{s}.log", .{prefix}) catch unreachable, log.items);
    say("done: {d} operators, {d} bytes, {d:.1} s, {d} graphs asked, {d} operators drawn, {d} refused\n", .{ g.n, g.bytes(), seconds() - t0, n_eval, n_draw, n_refused });
}

const Options = struct {
    seed: u64 = 1,
    work: u32 = 7,
    candidates: usize = 80,
    quick: i64 = 30,
    deep: i64 = 250,
    final: i64 = 400,
    max_ops: usize = 40,
    patience: usize = 3,
    gain: f32 = 0.005,
    read_only: bool = false,
    grain: f32 = 1.2,
    grow: usize = 0, // free moves from the prior tried per step after the reading (0: none)
    relief: usize = 16,
    noises: usize = 2,
    byte_cost: f32 = 0.0003,
    structure: Structure = .plain, // the one structure built in this run; the readings must allow it
    force: bool = false, // inside a structure step: the best candidate is kept without the pay test
    surface2: bool = false, // the surface layer repeated 2 by 2 (finer, more numerous granules)
    blur: f32 = 0.002, // the Blur over patches (the operator's own radius value; 0.006 already smears a patch away)
    stretch: f32 = 0, // the grain's stretch (2, 4, 8 or 16); 0 lets the inner measure pick
    jointw: f32 = 1.0, // the joints' width against the width read from the picture
};

/// What adds structure. Each needs its own reading; the inner measure accepts any of them on almost any
/// picture, so none is tried without one, and the choice between the allowed ones is the eye's.
const Structure = enum { plain, shape, patches, second, grain, rings, mirror };

fn allowed(rd: *const Reading, st: Structure, opt: Options) bool {
    return switch (st) {
        .plain => true,
        .shape => rd.nrect > 0,
        .patches => rd.nrect == 0 and rd.flat >= 0.03 and rd.edge >= 0.35,
        .second => rd.nrect == 0 and rd.off >= 0.01 and rd.off_coh >= 0.8,
        .grain => rd.nrect == 0 and rd.aniso >= opt.grain,
        .rings => rd.nrect == 0 and rd.nring > 0,
        .mirror => rd.nrect == 0 and rd.nring >= 2 and rd.mirror >= 0.10,
    };
}

fn argStr(argv: [*]const [*:0]const u8, i: usize) []const u8 {
    return std.mem.span(argv[i]);
}

pub export fn main(argc: c_int, argv: [*]const [*:0]const u8) c_int {
    const n: usize = @intCast(argc);
    wzb_init();
    makeFilters();
    wzb_set_limit(@as(usize, 3) << 30);
    cache = alloc.alloc(Slot, CACHE) catch die("out of memory", .{});
    for (cache) |*s| s.* = .{};
    if (n >= 4 and std.mem.eql(u8, argStr(argv, 1), "render")) {
        // p2p render SCRIPT OUT.ppm [SIZE-EXPONENT]
        const g = parseScript(readFile(argv[2]));
        const size: u32 = if (n > 4) std.fmt.parseInt(u32, argStr(argv, 4), 10) catch 0 else 0;
        const bm = draw(&g, size) orelse die("the procedure does not draw", .{});
        const w: usize = @intCast(wzb_width(bm));
        const h: usize = @intCast(wzb_height(bm));
        const rgba = alloc.alloc(u8, w * h * 4) catch die("out of memory", .{});
        wzb_rgba(bm, rgba.ptr);
        writePpm(argStr(argv, 3), rgba, w, h);
        say("{d} operators, {d} bytes, {d}x{d}\n", .{ g.n, g.bytes(), w, h });
        return 0;
    }
    if (n >= 5 and std.mem.eql(u8, argStr(argv, 1), "fit")) {
        // p2p fit TARGET.ppm PRIOR.txt OUT-PREFIX [name=value ...]
        var opt = Options{};
        for (5..n) |i| {
            const a = argStr(argv, i);
            const eq = std.mem.indexOfScalar(u8, a, '=') orelse die("option {s}: write name=value", .{a});
            const k = a[0..eq];
            const v = a[eq + 1 ..];
            if (std.mem.eql(u8, k, "seed")) {
                opt.seed = std.fmt.parseInt(u64, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "work")) {
                opt.work = std.fmt.parseInt(u32, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "candidates")) {
                opt.candidates = std.fmt.parseInt(usize, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "quick")) {
                opt.quick = std.fmt.parseInt(i64, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "deep")) {
                opt.deep = std.fmt.parseInt(i64, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "final")) {
                opt.final = std.fmt.parseInt(i64, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "maxops")) {
                opt.max_ops = std.fmt.parseInt(usize, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "patience")) {
                opt.patience = std.fmt.parseInt(usize, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "gain")) {
                opt.gain = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "placeweight")) {
                place_weight = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "texture")) {
                texture_weight = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "spread")) {
                spread_weight = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "place")) {
                place_side = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "readonly")) {
                opt.read_only = v[0] == '1';
            } else if (std.mem.eql(u8, k, "grow")) {
                opt.grow = std.fmt.parseInt(usize, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "relief")) {
                opt.relief = std.fmt.parseInt(usize, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "noises")) {
                opt.noises = std.fmt.parseInt(usize, v, 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "structure")) {
                opt.structure = std.meta.stringToEnum(Structure, v) orelse die("structure {s} is not known (plain, shape, patches, second, grain, rings, mirror)", .{v});
            } else if (std.mem.eql(u8, k, "surface2")) {
                opt.surface2 = v[0] == '1';
            } else if (std.mem.eql(u8, k, "blur")) {
                opt.blur = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "stretch")) {
                opt.stretch = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "jointw")) {
                opt.jointw = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "bytecost")) {
                opt.byte_cost = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else die("option {s} is not known (seed, work, candidates, quick, deep, final, maxops, patience, gain, placeweight, texture, spread, place, bytecost)", .{k});
        }
        fit(argv[2], argv[3], argStr(argv, 4), opt);
        return 0;
    }
    say("usage: p2p render SCRIPT OUT.ppm [SIZE-EXPONENT]\n       p2p fit TARGET.ppm PRIOR.txt OUT-PREFIX [name=value ...]\n", .{});
    return 2;
}
