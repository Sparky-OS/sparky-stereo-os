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
    aniso: f32 = 1, // how much stronger the detail is one way than the other (1: no grain)
    joint: u32 = 0xff404040, // the joints' colour as a share of the surface's: the dark end of the picture's own colours
    ox: f32 = 0,
    oy: f32 = 0,
    f0: u32 = 0, // the noise: first octave, how many, the fall per octave, the strength
    oct: u32 = 1,
    fade: f32 = 1,
    amp: f32 = 1,
};

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
    for (r.t) |*s| s.* = @floatCast(@min(1.0, @max(0.0, (s.* - p1) / (p99 - p1))));

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
    }
    // the repeat, and the one cell under it
    var tm: f64 = 0;
    for (r.t) |s| tm += s;
    tm /= @floatFromInt(n * n);
    const tz = alloc.alloc(f32, n * n) catch die("out of memory", .{});
    for (tz, r.t) |*z, s| z.* = s - @as(f32, @floatCast(tm));
    var kx = repeats(tz, n, true);
    var ky = repeats(tz, n, false);
    // joints seen in the column or row means are trusted as they are (thin joints explain little contrast)
    const by_profile = kx > 1 or ky > 1;
    // rows shifted against each other hide their upright joints from the column means: the picture
    // against itself, moved sideways, still shows them
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
        r.nx = kx;
        r.ny = ky;
        for (cands, 0..) |cd, ci| {
            if (cd[0] < 1 or cd[1] < 1) continue;
            if (ci == 1 and ky % 2 != 0) continue;
            if (ci == 2 and kx % 2 != 0) continue;
            if (ci == 3 and (kx % 2 != 0 or ky % 2 != 0)) continue;
            var c2: []f32 = undefined;
            const sh = meanCell(r.t, n, cd[0], cd[1], tm, &c2, idx, &cw, &ch, true);
            alloc.free(c2);
            const need: f32 = if (ci == 0) 1.0 else 1.03;
            say("  cell {d} by {d}: predicts {d:.1} % of the contrast of the repeats it was not made from\n", .{ cd[0], cd[1], sh * 100.0 });
            if (sh > 0.02 and (best_share < 0 or sh > best_share * need)) {
                best_share = sh;
                r.nx = cd[0];
                r.ny = cd[1];
            }
        }
        if (best_share < 0 and by_profile) best_share = 0.02;
        r.share = if (best_share < 0) 0 else meanCell(r.t, n, r.nx, r.ny, tm, &cell, idx, &cw, &ch, false);
        if (best_share < 0) cell = alloc.alloc(f32, 1) catch die("out of memory", .{});
        if (best_share >= 0) {
            for (0..n * n) |i| resid[i] = r.t[i] - cell[idx[i]] + @as(f32, @floatCast(tm));
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

/// the shape drawn once and repeated, the way .kkrieger's walls and tiles are built:
/// Flat (the joints), one GlowRect per shape, Transform to repeat. Returns the index of its last operator.
fn appendShape(g: *Graph, r_in: *const Reading, bond: bool) usize {
    // bond: the same shape on every second row, moved half a cell sideways, as a wall is laid
    var rr = r_in.*;
    if (bond) {
        if (rr.nrect == 1) {
            const a = rr.rect[0];
            rr.rect[0] = .{ a[0], a[1] * 0.5, a[2], a[3] * 0.5 };
            rr.rect[1] = .{ @mod(a[0] + 0.5, 1.0), 0.5 + a[1] * 0.5, a[2], a[3] * 0.5 };
            rr.ny = rr.ny / 2;
            rr.oy = rr.oy * 0.5;
        } else {
            rr.rect[0] = .{ 0.5, 0.25, 0.46, 0.21 };
            rr.rect[1] = .{ 0.0, 0.75, 0.46, 0.21 };
        }
        rr.nrect = 2;
    }
    const r = &rr;
    var jf = flatNode(r.joint);
    jf.grey = true; // its shade is tuned, its hue stays the picture's
    _ = append(g, jf);
    for (0..r.nrect) |k| {
        var nd = Node{ .op = OP_GLOWRECT, .nin = 1, .nw = 11, .grey = true, .lockw = 3 };
        nd.in[0] = @intCast(g.n - 1);
        const edge: f32 = 0.008;
        nd.w[0] = wordOf(r.rect[k][0]);
        nd.w[1] = wordOf(r.rect[k][1]);
        nd.w[2] = wordOf(edge);
        nd.w[3] = wordOf(edge);
        nd.w[4] = wordOf(@max(0.01, r.rect[k][2] - edge));
        nd.w[5] = wordOf(@max(0.01, r.rect[k][3] - edge));
        nd.w[6] = 0xffffffff;
        nd.w[7] = wordOf(1.0);
        nd.w[8] = wordOf(0.5);
        nd.w[9] = 1;
        nd.w[10] = 0;
        _ = append(g, nd);
    }
    var tr = Node{ .op = OP_TRANSFORM, .nin = 1, .nw = 8, .lock = true, .shape = true };
    tr.in[0] = @intCast(g.n - 1);
    const fx: f32 = @floatFromInt(r.nx);
    const fy: f32 = @floatFromInt(r.ny);
    tr.w[0] = wordOf(0.0);
    tr.w[1] = wordOf(1.0 / fx);
    tr.w[2] = wordOf(1.0 / fy);
    tr.w[3] = wordOf(@mod(0.5 * fx - r.ox, 1.0));
    tr.w[4] = wordOf(@mod(0.5 * fy - r.oy, 1.0));
    tr.w[5] = 0;
    return append(g, tr);
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
    if (nord == 0 or best_s >= cur.* * (1.0 - opt.gain)) return false;
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

/// grain and fibres: the colour layer stretched one way, bent by a noise (Distort), or twirled
fn stepGrain(g: *Graph, t: *Target, base: *usize, cur: *f32, opt: Options) bool {
    const cands = alloc.alloc(Cand, 24) catch die("out of memory", .{});
    defer alloc.free(cands);
    var n: usize = 0;
    const k = base.*;
    const reps = [_]f32{ 2, 4, 8 };
    for (reps) |rp| {
        inline for (.{ 0, 1 }) |ax| {
            var c = g.*;
            var tr = Node{ .op = OP_TRANSFORM, .nw = 8, .lock = true };
            tr.w[0] = wordOf(0.0);
            tr.w[1] = wordOf(if (ax == 0) 1.0 / rp else 1.0);
            tr.w[2] = wordOf(if (ax == 1) 1.0 / rp else 1.0);
            tr.w[3] = wordOf(0.5);
            tr.w[4] = wordOf(0.5);
            wrapOne(&c, k, tr);
            cands[n] = .{ .g = c, .first = 0, .last = k, .base = k + 1 };
            n += 1;
        }
    }
    var f0: u32 = 0;
    while (f0 < 4) : (f0 += 1) {
        for (0..2) |_| {
            const di = randomInst(OP_DISTORT) orelse break;
            var c = g.*;
            var pn = perlinNode(f0, 2, 0.7, @intCast(rndN(256)), 1.0, 0xff000000, 0xffffffff);
            pn.grey = true;
            c.insert(k + 1, pn);
            var ds = nodeOf(di);
            ds.nin = 2;
            ds.in[0] = @intCast(k);
            ds.in[1] = @intCast(k + 1);
            c.insert(k + 2, ds);
            c.rewire(k + 2, k, k + 2);
            cands[n] = .{ .g = c, .first = k + 1, .last = k + 2, .base = k + 2 };
            n += 1;
        }
    }
    for (0..6) |_| {
        const ti = randomInst(OP_TWIRL) orelse break;
        var c = g.*;
        wrapOne(&c, k, nodeOf(ti));
        cands[n] = .{ .g = c, .first = k + 1, .last = k + 1, .base = k + 1 };
        n += 1;
    }
    return keepBest(g, t, base, cur, opt, cands[0..n]);
}

/// a second material through a mask made from a noise (the artists' Perlin with amplify and gamma) or from cells
fn stepMask(g: *Graph, t: *Target, base: *usize, cur: *f32, opt: Options) bool {
    const cands = alloc.alloc(Cand, 48) catch die("out of memory", .{});
    defer alloc.free(cands);
    var n: usize = 0;
    const k = base.*;
    var f0: u32 = 0;
    while (f0 < 5) : (f0 += 1) {
        for (0..8) |pi| {
            if (n >= 44) break;
            var c = g.*;
            var mk: Node = undefined;
            if (pi % 4 == 3) {
                const ci = randomInst(OP_CELL) orelse continue;
                mk = nodeOf(ci);
                mk.nin = 0;
                mk.w[2] = 0xff000000;
                mk.w[3] = 0xffffffff;
            } else {
                mk = perlinNode(f0, 3, 0.7, @intCast(rndN(256)), 3.0, 0xff000000, 0xffffffff);
                mk.w[8] = wordOf(2.0);
            }
            mk.grey = true;
            c.insert(k + 1, mk);
            c.insert(k + 2, flatNode(0xff000000 | palette[pi]));
            var ms = Node{ .op = OP_MASK, .nin = 3, .nw = 1 };
            ms.in[0] = @intCast(k + 1);
            ms.in[1] = @intCast(k + 2);
            ms.in[2] = @intCast(k);
            ms.w[0] = 0;
            c.insert(k + 3, ms);
            c.rewire(k + 3, k, k + 3);
            cands[n] = .{ .g = c, .first = k + 1, .last = k + 2, .base = k + 3 };
            n += 1;
        }
    }
    return keepBest(g, t, base, cur, opt, cands[0..n]);
}

/// patches and facets: real Cell instances merged over the colour layer
fn stepCell(g: *Graph, t: *Target, base: *usize, cur: *f32, opt: Options) bool {
    const cands = alloc.alloc(Cand, 24) catch die("out of memory", .{});
    defer alloc.free(cands);
    var n: usize = 0;
    const k = base.*;
    const modes = [_]u32{ 2, 0, 1 };
    for (0..8) |_| {
        const ci = randomInst(OP_CELL) orelse break;
        for (modes) |md| {
            var c = g.*;
            var ce = nodeOf(ci);
            ce.nin = 0;
            ce.grey = true;
            ce.w[2] = if (md == 2) 0xff909090 else 0xff000000;
            ce.w[3] = if (md == 2) 0xffffffff else 0xff505050;
            ce.w[4] = ce.w[2];
            c.insert(k + 1, ce);
            var mg = Node{ .op = OP_MERGE, .nin = 2, .nw = 1 };
            mg.in[0] = @intCast(k);
            mg.in[1] = @intCast(k + 1);
            mg.w[0] = md;
            c.insert(k + 2, mg);
            c.rewire(k + 2, k, k + 2);
            cands[n] = .{ .g = c, .first = k + 1, .last = k + 1, .base = k + 2 };
            n += 1;
        }
    }
    return keepBest(g, t, base, cur, opt, cands[0..n]);
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
    if (cost(raw, best.bytes(), g.bytes(), opt) >= cur.* * (1.0 - opt.gain)) return false;
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
    if (opt.read_only) return;
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
    if (rd.nrect > 0) {
        var best: Graph = undefined;
        var best_s: f32 = BAD;
        var best_bond = false;
        inline for (.{ false, true }) |bond| {
            if (!bond or rd.nrect >= 2 or rd.ny % 2 == 0) {
                var c = g;
                const colour = c.root;
                const sh = appendShape(&c, &rd, bond);
                var mg = Node{ .op = OP_MERGE, .nin = 2, .nw = 1 };
                mg.in[0] = @intCast(colour);
                mg.in[1] = @intCast(sh);
                mg.w[0] = 2;
                _ = append(&c, mg);
                _ = tune(&c, &t, colour + 1, c.n - 1, opt.deep * 3, false, 3);
                const s = tune(&c, &t, 0, c.n - 1, opt.deep * 2, true, 2);
                say("  the shape {s}: measure {d:.5}\n", .{ if (bond) "in a bond" else "as read", s });
                if (cost(s, c.bytes(), g.bytes(), opt) < best_s) {
                    best_s = cost(s, c.bytes(), g.bytes(), opt);
                    best = c;
                    best_bond = bond;
                }
            }
        }
        if (best_s < cur * (1.0 - opt.gain)) {
            g = best;
            cur = score(&g, &t);
            rung += 1;
            saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
            say("rung {d}: the repeated shape{s}, {d} operators, {d} bytes, measure {d:.5}\n", .{ rung, if (best_bond) " in a bond" else "", g.n, g.bytes(), cur });
        } else say("the repeated shape did not pay ({d:.5})\n", .{best_s});
    }

    const TOP = 4;
    var size = work;
    var ncand = opt.candidates;
    while (true) {
        if (!has_relief and tryRelief(&g, &t, &cur, opt)) {
            has_relief = true;
            rung += 1;
            saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
            say("rung {d} at {d} px: a lit relief, {d} operators, {d} bytes, measure {d:.5}\n", .{ rung, @as(usize, 1) << @intCast(size), g.n, g.bytes(), cur });
        }
        if (size < full or full == work) {
            const names = [_][]const u8{ "grain (stretch, Distort or Twirl)", "a second material (Mask)", "cells", "tone (Range, HSCB or Blur)" };
            inline for (.{ stepGrain, stepMask, stepCell, stepTone }, 0..) |step, si| {
                // grain is tried only where the picture has one: a swirl pays by the measure on any noise and is wrong to the eye
                if ((si != 0 or rd.aniso >= opt.grain) and g.n + 4 < opt.max_ops and step(&g, &t, &base, &cur, opt)) {
                    rung += 1;
                    saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
                    say("rung {d} at {d} px: {s}, {d} operators, {d} bytes, measure {d:.5}, {d:.0} s\n", .{ rung, @as(usize, 1) << @intCast(size), names[si], g.n, g.bytes(), cur, seconds() - t0 });
                }
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
        // operators that no longer earn their bytes go
        var i: usize = 0;
        while (i < g.n) {
            const nd = g.nodes[i];
            if (i == g.root or nd.nin == 0) {
                i += 1;
                continue;
            }
            var removed = false;
            for (0..nd.nin) |slot| {
                var c = g;
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
};

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
