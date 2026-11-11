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
const modern = @import("modern.zig");
const mfit = @import("mfit.zig");

extern "c" fn wzb_init() void;
extern "c" fn wzb_set_limit(bytes: usize) void;
extern "c" fn wzb_apply(name: [*:0]const u8, w: [*]const u32, nin: c_int, inp: [*]?*anyopaque, out: *?*anyopaque, err: [*]u8, errlen: c_int) c_int;
extern "c" fn wzb_strings(text: [*:0]const u8, font: [*:0]const u8) void;
extern "c" fn wzb_strings3(text: [*:0]const u8, font: [*:0]const u8, axes: [*:0]const u8) void;
extern "c" fn wzb_notes() [*:0]const u8;
extern "c" fn wzb_glyph_mask(font: [*:0]const u8, c: c_int, side: c_int, out: [*]u8, v: [*]f32) c_int;
extern "c" fn wzb_free(p: ?*anyopaque) void;
extern "c" fn fi_index(nsrc: c_int, srcs: [*]const [*:0]const u8) c_int;
extern "c" fn gi_build(out: [*:0]const u8, shard: c_int, nshard: c_int) c_int;
extern "c" fn wzb_width(p: ?*anyopaque) c_int;
extern "c" fn wzb_height(p: ?*anyopaque) c_int;
extern "c" fn wzb_rgba(p: ?*anyopaque, dst: [*]u8) void;
extern "c" fn fopen(path: [*:0]const u8, mode: [*:0]const u8) ?*anyopaque;
extern "c" fn fclose(f: ?*anyopaque) c_int;
extern "c" fn fread(p: [*]u8, s: usize, n: usize, f: ?*anyopaque) usize;
extern "c" fn fwrite(p: [*]const u8, s: usize, n: usize, f: ?*anyopaque) usize;
extern "c" fn write(fd: c_int, p: [*]const u8, n: usize) isize;
extern "c" fn clock() i64; // clock_t: long on x86-64, long long in wasi-libc
extern "c" fn exit(code: c_int) noreturn;

pub const alloc = std.heap.c_allocator;

pub fn say(comptime fmt: []const u8, args: anytype) void {
    var buf: [4096]u8 = undefined;
    const s = std.fmt.bufPrint(&buf, fmt, args) catch return;
    _ = write(2, s.ptr, s.len);
}

pub fn die(comptime fmt: []const u8, args: anytype) noreturn {
    say(fmt ++ "\n", args);
    exit(1);
}

/// what the font renderer noted about the texts drawn: the font that stood in, characters without a glyph
fn sayNotes() void {
    var it = std.mem.tokenizeScalar(u8, std.mem.span(wzb_notes()), '\n');
    while (it.next()) |line| say("text: {s}\n", .{line});
}

pub fn seconds() f64 {
    return @as(f64, @floatFromInt(clock())) / 1000000.0;
}

// ---------------------------------------------------------------- operators

const NW = 28; // werkkzeug3 stores at most 14 words; the modern Ramp 18, Tiles version 2 24
const MAXIN = 16; // a Grid of 4 by 4 procedures (milestone 2e); werkkzeug3 takes at most 8
pub const MAXN = 220;

const OpInfo = struct { name: [:0]const u8, kinds: []const u8, nin: u8 };
// i = whole number, f = decimal, c = colour: the packing of werkkzeug3's operator table (lane 473x's wzlang.py)
const werk_ops = [_]OpInfo{
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
    // x, y, the font's height, the character width (0: the font's own), colour, flags, space around a font page's
    // letters (whole pixels, then parts of the picture), line height; and two strings: the text and the font's name
    .{ .name = "Text", .kinds = "ffffciiff", .nin = 1 },
};
/// milestone 2b: the modern operators follow werkkzeug3's (ops/*.zig, each with its table; modern.zig lists them)
pub const OP_MODERN = werk_ops.len;
pub const ops = blk: {
    var a: [werk_ops.len + modern.count]OpInfo = undefined;
    for (werk_ops, 0..) |o, i| a[i] = o;
    for (0..modern.count) |k| {
        const P = modern.paramsOf(k);
        a[werk_ops.len + k] = .{ .name = modern.nameOf(k), .kinds = modern.kindsOf(P), .nin = modern.inputsOf(k) };
    }
    break :blk a;
};
fn isModern(op: u8) bool {
    return op >= OP_MODERN;
}
const OP_TEXT = 28;
pub const OP_FLAT = 0;
const OP_NORMALS = 16;
const OP_TRANSFORM = 13;
const OP_MERGE = 21;
const OP_BUMP = 23;
const OP_MASK = 25;

/// Text version 2 (our extension: UTF-8, any font of the font index, axis values, palette, form) says so in its
/// tenth word; werkkzeug3's own Text has nine words and two strings, and reads unchanged.
const TEXT2_WORDS = 12;
fn isText2(nd: *const Node) bool {
    return nd.op == OP_TEXT and nd.nw >= 10 and nd.w[9] == 2;
}
/// the words an operator stores: werkkzeug3's count, or version 2 Text's twelve
fn wordsOf(nd: *const Node) usize {
    if (isModern(nd.op)) return modern.wordsFor(nd.op - OP_MODERN, nd.w[0]);
    return if (isText2(nd)) TEXT2_WORDS else ops[nd.op].kinds.len;
}

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

pub const Node = struct {
    op: u8 = 0,
    nin: u8 = 0,
    in: [MAXIN]u8 = [_]u8{0} ** MAXIN,
    nw: u8 = 0,
    w: [NW]u32 = [_]u32{0} ** NW,
    lock: bool = false, // values read from the picture that the tuning must keep (a repeat count)
    lockw: u32 = 0, // single values the tuning must keep (where a shape's centre was read)
    shape: bool = false, // the Transform that repeats the read shape: the relief's height
    is_base: bool = false, // the top of the surface layer, marked while the cleaning moves operators
    keep: bool = false, // built from a reading: the cleaning by the inner measure does not remove it
    grey: bool = false, // its colours are tuned as greys: a light or an added noise changes shade, not hue
    hue: bool = false, // milestone 2b: its colours are retuned by brightness and saturation only, so a tile keeps the whole picture's hue
    s: [3]u16 = .{ 0, 0, 0 }, // Text: its text and its font's name, as places in the string pool (0 is the empty string); version 2 adds the axis values
};

// The strings of Text operators: 8-bit, Windows code page 1252, kept once each.
var spool: [512][:0]const u8 = undefined;
var spool_n: usize = 0;

pub fn intern(bytes: []const u8) u16 {
    if (spool_n == 0) {
        spool[0] = "";
        spool_n = 1;
    }
    for (spool[0..spool_n], 0..) |x, i| {
        if (std.mem.eql(u8, x, bytes)) return @intCast(i);
    }
    if (spool_n >= spool.len) die("more than {d} different strings", .{spool.len});
    const m = alloc.allocSentinel(u8, bytes.len, 0) catch die("out of memory", .{});
    @memcpy(m, bytes);
    spool[spool_n] = m;
    spool_n += 1;
    return @intCast(spool_n - 1);
}

fn strOf(i: u16) [:0]const u8 {
    if (spool_n == 0) return "";
    return spool[i];
}

/// a string as werkkzeug3 stores it: a length word, then the bytes and their end mark, filled to whole words
fn stringBytes(i: u16) usize {
    return 4 + 4 * ((strOf(i).len + 1 + 3) / 4);
}

pub const Graph = struct {
    n: usize = 0,
    root: usize = 0,
    nodes: [MAXN]Node = undefined,

    /// werkkzeug3's storage: one class byte and the parameter words of every operator
    pub fn bytes(g: *const Graph) usize {
        var b: usize = 0;
        for (g.nodes[0..g.n]) |nd| {
            b += 1 + 4 * @as(usize, wordsOf(&nd));
            if (nd.op == OP_TEXT) b += stringBytes(nd.s[0]) + stringBytes(nd.s[1]);
            if (isText2(&nd)) b += stringBytes(nd.s[2]);
        }
        return b;
    }

    /// put a node at position pos; the nodes from pos on move up by one
    pub fn insert(g: *Graph, pos: usize, nd: Node) void {
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
    pub fn rewire(g: *Graph, from: usize, old: usize, new: usize) void {
        for (g.nodes[from + 1 .. g.n]) |*x| {
            for (x.in[0..x.nin]) |*v| {
                if (v.* == old) v.* = @intCast(new);
            }
        }
        if (g.root == old) g.root = new;
    }

    /// drop the operators the result does not use
    pub fn prune(g: *Graph) void {
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

pub fn readFile(path: [*:0]const u8) []u8 {
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

pub fn writeFile(path: []const u8, data: []const u8) void {
    var pz: [1024]u8 = undefined;
    const p = std.fmt.bufPrintZ(&pz, "{s}", .{path}) catch die("path too long", .{});
    const f = fopen(p.ptr, "wb") orelse die("cannot write {s}", .{path});
    if (fwrite(data.ptr, 1, data.len, f) != data.len) die("short write to {s}", .{path});
    _ = fclose(f);
}

pub const Image = struct { w: usize, h: usize, rgb: []f32 };

pub fn readPpm(path: [*:0]const u8) Image {
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

pub fn writePpm(path: []const u8, rgba: []const u8, w: usize, h: usize) void {
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

pub fn parseScript(text: []const u8) Graph {
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
        var ns: usize = 0;
        while (t.next()) |hx| {
            if (std.mem.startsWith(u8, hx, "s=")) {
                // a string: s= and its bytes as hex digits
                const hd = hx[2..];
                if (ns >= 3 or hd.len % 2 != 0) die("{s}: bad string {s}", .{ id, hx });
                var tmp: [600]u8 = undefined;
                if (hd.len / 2 > tmp.len) die("{s}: a string longer than {d} bytes", .{ id, tmp.len });
                for (0..hd.len / 2) |k| tmp[k] = std.fmt.parseInt(u8, hd[2 * k .. 2 * k + 2], 16) catch die("{s}: bad string {s}", .{ id, hx });
                nd.s[ns] = intern(tmp[0 .. hd.len / 2]);
                ns += 1;
                continue;
            }
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

pub fn scriptText(g: *const Graph, buf: []u8) []u8 {
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
        for (0..wordsOf(&nd)) |p| {
            n += (std.fmt.bufPrint(buf[n..], " {x}", .{nd.w[p]}) catch die("script too long", .{})).len;
        }
        if (nd.op == OP_TEXT) {
            for (nd.s[0..if (isText2(&nd)) 3 else 2]) |si| {
                n += (std.fmt.bufPrint(buf[n..], " s=", .{}) catch die("script too long", .{})).len;
                for (strOf(si)) |ch| n += (std.fmt.bufPrint(buf[n..], "{x:0>2}", .{ch}) catch die("script too long", .{})).len;
            }
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
pub var say_refusals: bool = false; // render says why an operator refused; the fitter tries values in silence

pub fn cacheClear() void {
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
pub fn draw(g: *const Graph, size: u32) ?*anyopaque {
    n_eval += 1;
    if (cache_count > cache_cap) cacheClear();
    var hs: [MAXN]u64 = undefined;
    var bm: [MAXN]?*anyopaque = undefined;
    for (0..g.root + 1) |i| {
        const nd = &g.nodes[i];
        var w: [32]u32 = [_]u32{0} ** 32;
        const nk = wordsOf(nd);
        for (0..nk) |p| w[p] = nd.w[p];
        if (size != 0 and !isModern(nd.op)) {
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
        if (isModern(nd.op)) {
            // a modern operator draws on the canvas: its size, margin, window and level of detail are part of its key
            const cv = modern.c.cv;
            h = mix(h, cv.w);
            h = mix(h, cv.h);
            h = mix(h, cv.m);
            h = mix(h, @as(u32, @bitCast(cv.wx)));
            h = mix(h, @as(u32, @bitCast(cv.wy)));
            h = mix(h, @as(u32, @bitCast(cv.ws)));
            h = mix(h, cv.maxoct);
        }
        for (0..nk) |p| h = mix(h, w[p]);
        if (nd.op == OP_TEXT) {
            for (nd.s) |si| {
                h = mix(h, 0x7e87);
                for (strOf(si)) |ch| h = mix(h, ch);
            }
        }
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
        var err: [300]u8 = [_]u8{0} ** 300;
        if (nd.op == OP_TEXT) wzb_strings3(strOf(nd.s[0]).ptr, strOf(nd.s[1]).ptr, strOf(nd.s[2]).ptr);
        const r = if (isModern(nd.op))
            modern.apply(nd.op - OP_MODERN, w[0..nk], inp[0..nd.nin], &out, &err)
        else
            wzb_apply(ops[nd.op].name.ptr, &w, nd.nin, &inp, &out, &err, 300);
        n_draw += 1;
        if (r != 0) {
            if (say_refusals) say("refused: v{d} {s}: {s}\n", .{ i, ops[nd.op].name, std.mem.sliceTo(&err, 0) });
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

pub const Target = struct {
    size: u32, // exponent of the side
    pyr: Pyr,
    scratch: Pyr,
    rgba: []u8,
    slow: f64, // a drawing that takes longer than this is refused: the device must draw it
};

pub fn makeTarget(img: Image, size: u32) Target {
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

pub fn freeTarget(t: *Target) void {
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
                        if (g.nodes[i].hue) {
                            // milestone 2b: brightness (every channel scaled alike) and saturation (every channel moved
                            // toward or away from their mean); the ratios between the channels' departures stay, so
                            // the hue stays the whole picture's and a grey stays grey
                            const fs = [_]f32{ 1, -1 };
                            for (0..2) |kind| {
                                for (fs) |sgn| {
                                    var k: usize = 0;
                                    while (k < 3) : (k += 1) {
                                        const cur = g.nodes[i].w[p];
                                        var c: [3]f32 = undefined;
                                        inline for (0..3) |q| c[q] = @floatFromInt((cur >> (16 - 8 * q)) & 0xff);
                                        const d = sgn * @as(f32, @floatFromInt(step)) / 255.0;
                                        const m = (c[0] + c[1] + c[2]) / 3.0;
                                        var v = cur & 0xff000000;
                                        inline for (0..3) |q| {
                                            const nvf = if (kind == 0) c[q] * (1.0 + d) else m + (c[q] - m) * (1.0 + 2.0 * d);
                                            const nv: u32 = @intFromFloat(@min(255.0, @max(0.0, nvf + 0.5)));
                                            v |= nv << (16 - 8 * q);
                                        }
                                        if (!tryWord(g, t, i, p, v, &best, &budget)) break;
                                        improved = true;
                                    }
                                }
                            }
                            continue;
                        }
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

pub const Reading = struct {
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
    fig: Figure = .{}, // a figure on a ground, and its pieces read as glyphs (the reading behind Text)
    // milestone 2: the mean cell along the colour axis (its first pixel lies at the picture's first), and a tile's
    // view of the whole picture's repeat
    cell: []f32 = &.{},
    cw: usize = 0,
    ch: usize = 0,
    win: bool = false,
    ax: Axis = .{},
    ay: Axis = .{},
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

pub fn readPicture(t: *Target) Reading {
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
            r.cell = cell;
            r.cw = cw;
            r.ch = ch;
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

// ---------------------------------------------------------------- a glyph shape: the reading behind Text
//
// What in the pixels says "a glyph shape is here": the picture is a figure in one flat shade on a ground in
// another, and its pieces, each stretched to its own box, lie over the same picture of a glyph of one of the
// fonts, drawn from that font's outlines, and stand on one line at one size. The letter is found by laying
// the font's own outlines over the ink; nobody names it. A box or a disc is not a glyph: GlowRect draws those.

const GS = 24; // the side of a shape's picture, stretched to its own box
const NFONT = 3;
/// the font names .kkrieger's Text operators hold ("" is werkkzeug3's "arial"); the font map says which file draws each
const font_names = [NFONT][:0]const u8{ "", "times new roman", "verdana" };
const Templ = struct { font: u16, ch: u32, m: [GS * GS]bool, aspect: f32, inkh: f32, top: f32, adv: f32, lsb: f32, plain: bool, parts: u8, rich: bool };
var templs: std.ArrayList(Templ) = .empty;
/// The candidate fonts of the figure being read. Without a glyph index (milestone 1d's reading) they are the
/// three names .kkrieger holds, drawn by werkkzeug3's own Text; with one (WZ_GLYPHINDEX), the fonts of the whole
/// index whose glyphs lie closest over the figure's pieces, chosen per figure.
const MAXCF = 40;
var cf_n: usize = 0;
var cf_key: [MAXCF][:0]const u8 = undefined; // werkkzeug3's name, or the font index's key
var cf_label: [MAXCF][]const u8 = undefined;
var cf_v1: [MAXCF]bool = undefined; // written as werkkzeug3's own Text (8-bit, by name)
var cf_v1name: [MAXCF][:0]const u8 = undefined;
var font_space = [_]f32{0} ** MAXCF;
var font_avg = [_]f32{0} ** MAXCF;
var font_have = [_]bool{false} ** MAXCF;
var templs_loaded = false;
/// the reading over the whole index is switched off while the Twirl is run backwards (thousands of readings of
/// bent shapes); the figure is read over the whole index once the twirls are out
var wide_off = false;
var wide_now = false; // the figure in hand was read over the whole index: its texts are UTF-8

/// how much of a shape must lie over a glyph, and the glyph over it (their common part over their union).
/// Measured: the letters of .kkrieger's plain texts give 0.86 to 1.00 against their own font, letters bent by a
/// Distort 0.74 and more; the best glyph for the pieces of a noise, a patch or a swirl gives 0.35 to 0.66.
var glyph_t: f32 = 0.70;
/// a line is started by a shape that reaches glyph_t; once a line stands, a shape that fits the line's size and
/// top is taken with this much less (a letter bent by a Distort still stands on its line)
const MEMBER_SLACK: f32 = 0.12;
/// a figure: at least this share of the picture lies in the two flat shades
const TWO_T: f32 = 0.80;

/// a box, or a disc stretched to its box: what GlowRect draws
fn plainShape(m: *const [GS * GS]bool) bool {
    var ink: usize = 0;
    var both: usize = 0;
    var either: usize = 0;
    for (0..GS) |y| {
        for (0..GS) |x| {
            const dx = (@as(f32, @floatFromInt(x)) + 0.5) / GS * 2.0 - 1.0;
            const dy = (@as(f32, @floatFromInt(y)) + 0.5) / GS * 2.0 - 1.0;
            const in = dx * dx + dy * dy <= 1.0;
            const v = m[y * GS + x];
            if (v) ink += 1;
            if (v and in) both += 1;
            if (v or in) either += 1;
        }
    }
    return ink * 100 >= GS * GS * 88 or both * 100 >= either * 85;
}

/// A shape with enough form to say "glyph" on its own: in a quarter or more of its rows, or of its columns, a
/// line through it crosses ink twice or more (o, e, a, g, k, h, n, s, c, A, 8). A comma, a dash, a bar, a slash,
/// an r or a t are single strokes that a blob or a bent box also gives: they are read on a line that such a
/// shape started, never as the start of one.
fn richShape(m: *const [GS * GS]bool) bool {
    var rows: usize = 0;
    var cols: usize = 0;
    for (0..GS) |a| {
        var runs_r: usize = 0;
        var runs_c: usize = 0;
        var pr = false;
        var pc = false;
        for (0..GS) |b| {
            const vr = m[a * GS + b];
            const vc = m[b * GS + a];
            if (vr and !pr) runs_r += 1;
            if (vc and !pc) runs_c += 1;
            pr = vr;
            pc = vc;
        }
        if (runs_r >= 2) rows += 1;
        if (runs_c >= 2) cols += 1;
    }
    return rows * 4 >= GS or cols * 4 >= GS;
}

/// how many separate pieces of ink a small picture holds
fn partsOf(m: *const [GS * GS]bool) u8 {
    var seen = [_]bool{false} ** (GS * GS);
    var stack: [GS * GS]u16 = undefined;
    var parts: u8 = 0;
    for (0..GS * GS) |s| {
        if (!m[s] or seen[s]) continue;
        parts += 1;
        var sp: usize = 0;
        stack[sp] = @intCast(s);
        sp += 1;
        seen[s] = true;
        while (sp > 0) {
            sp -= 1;
            const p: usize = stack[sp];
            const x = p % GS;
            const y = p / GS;
            const nb = [4][2]i32{ .{ -1, 0 }, .{ 1, 0 }, .{ 0, -1 }, .{ 0, 1 } };
            for (nb) |d| {
                const xx = @as(i32, @intCast(x)) + d[0];
                const yy = @as(i32, @intCast(y)) + d[1];
                if (xx < 0 or yy < 0 or xx >= GS or yy >= GS) continue;
                const q: usize = @intCast(yy * GS + xx);
                if (m[q] and !seen[q]) {
                    seen[q] = true;
                    stack[sp] = @intCast(q);
                    sp += 1;
                }
            }
        }
    }
    return parts;
}

fn loadTemplates() void {
    if (templs_loaded and !wide_now) return;
    if (wide_now) templs.clearRetainingCapacity();
    templs_loaded = true;
    wide_now = false;
    cf_n = NFONT;
    for (font_names, 0..) |fname, fi| {
        cf_key[fi] = fname;
        cf_label[fi] = if (fname.len == 0) "arial (the empty name)" else fname;
        cf_v1[fi] = true;
        cf_v1name[fi] = fname;
        font_have[fi] = false;
    }
    var buf: [GS * GS]u8 = undefined;
    for (font_names, 0..) |fname, fi| {
        var v: [6]f32 = undefined;
        var c: c_int = 32;
        while (c < 256) : (c += 1) {
            if (c >= 127 and c < 161) continue;
            const r = wzb_glyph_mask(fname.ptr, c, GS, &buf, &v);
            if (r == 1) continue;
            font_have[fi] = true;
            font_avg[fi] = v[5];
            if (c == 32) {
                font_space[fi] = v[3];
                continue;
            }
            if (r != 0) continue;
            var tp = Templ{ .font = @intCast(fi), .ch = @intCast(c), .m = undefined, .aspect = v[0], .inkh = v[1], .top = v[2], .adv = v[3], .lsb = v[4], .plain = false, .parts = 1, .rich = false };
            for (0..GS * GS) |i| tp.m[i] = buf[i] >= 128;
            tp.plain = plainShape(&tp.m);
            tp.parts = partsOf(&tp.m);
            tp.rich = richShape(&tp.m);
            templs.append(alloc, tp) catch die("out of memory", .{});
        }
    }
}

const MAXSHAPE = 300;
const MAXC = 12;
const Shape = struct {
    x0: usize = 0,
    y0: usize = 0,
    x1: usize = 0,
    y1: usize = 0,
    area: usize = 0,
    ids: [6]u32 = .{ 0, 0, 0, 0, 0, 0 }, // the pieces it is made of (a glyph of several pieces: i, j, a hieroglyph, a CJK character)
    m: [GS * GS]bool = undefined,
    plain: bool = false,
    rich: bool = false,
    nc: usize = 0, // the glyphs of the font in hand that lie over it well enough
    c: [MAXC]u16 = undefined,
    ci: [MAXC]f32 = undefined,
    best: f32 = 0, // the best any non-plain glyph does
    used: bool = false,
    dead: bool = false,
};

fn owns(sh: *const Shape, l: u32) bool {
    if (l == 0) return false;
    for (sh.ids) |i| if (i == l) return true;
    return false;
}

fn shapeMask(labels: []const u32, n: usize, sh: *Shape) void {
    const w = sh.x1 - sh.x0;
    const h = sh.y1 - sh.y0;
    for (0..GS) |gy| {
        const ya = sh.y0 + gy * h / GS;
        const yb = @max(ya + 1, sh.y0 + (gy + 1) * h / GS);
        for (0..GS) |gx| {
            const xa = sh.x0 + gx * w / GS;
            const xb = @max(xa + 1, sh.x0 + (gx + 1) * w / GS);
            var cnt: usize = 0;
            var tot: usize = 0;
            for (ya..@min(yb, n)) |y| {
                for (xa..@min(xb, n)) |x| {
                    tot += 1;
                    const l = labels[y * n + x];
                    if (owns(sh, l)) cnt += 1;
                }
            }
            sh.m[gy * GS + gx] = tot > 0 and 2 * cnt >= tot;
        }
    }
    sh.plain = plainShape(&sh.m);
    sh.rich = !sh.plain and richShape(&sh.m);
}

fn iou(a: *const [GS * GS]bool, b: *const [GS * GS]bool) f32 {
    var both: usize = 0;
    var either: usize = 0;
    for (a, b) |x, y| {
        if (x and y) both += 1;
        if (x or y) either += 1;
    }
    return if (either == 0) 0 else @as(f32, @floatFromInt(both)) / @as(f32, @floatFromInt(either));
}

// ---------------------------------------------------------------- the reading over every font of the index
//
// The glyph index (p2p glyphindex) holds, for every font of the font index and every character its cmap maps, the
// glyph's ink stretched to its own box as 16 by 16 bits, and the ink's proportions. A piece of ink is laid over all
// of them first at that coarse size (the bits that differ), the fonts whose glyphs lie closest over the figure's
// pieces become its candidates, and each candidate is then read exactly as milestone 1d read its three fonts:
// its glyphs drawn from the font at 24 by 24 and laid over the pieces, on lines, by the font's own advances.

extern "c" fn getenv(name: [*:0]const u8) ?[*:0]const u8;
extern "c" fn wzb_glyph_mask2(key: [*:0]const u8, cp: c_uint, side: c_int, out: [*]u8, v: [*]f32, form: *c_int, rgba: ?[*]u8) c_int;
extern "c" fn wzb_font_spacing(key: [*:0]const u8, space: *f32, avg: *f32) c_int;
extern "c" fn uc_class(cp: u32) c_int;
/// a letter of a specialist block (IPA, phonetic, Latin Extended-D and later) is taken only when it lies this much closer
const SPECIAL_PENALTY: f32 = 0.10;

const GIEnt = extern struct { font: u32, cp: u32, aspect: f32, form: u8, parts: u8, pad: [2]u8, bits: [4]u64 };
var gi: []const GIEnt = &.{};
var gi_la: []f32 = &.{}; // the log of each entry's proportions
var gi_tried = false;
var fx_key: std.ArrayList([:0]const u8) = .empty;
var fx_family: std.ArrayList([]const u8) = .empty;
var fx_source: std.ArrayList([]const u8) = .empty;
var fx_label: std.ArrayList([]const u8) = .empty;
var fx_lo: []u32 = &.{};
var fx_hi: []u32 = &.{};

fn giLoad() bool {
    if (gi_tried) return gi.len > 0;
    gi_tried = true;
    const p = getenv("WZ_GLYPHINDEX") orelse return false;
    if (p[0] == 0) return false; // set and empty: no glyph index, the reading of milestone 1d
    const ip = getenv("WZ_FONTINDEX") orelse die("WZ_GLYPHINDEX is set and WZ_FONTINDEX is not: the glyph index's fonts are named by the font index", .{});
    const data = readFile(p);
    if (data.len % @sizeOf(GIEnt) != 0) die("the glyph index {s} is not a whole number of entries", .{std.mem.span(p)});
    gi = @alignCast(std.mem.bytesAsSlice(GIEnt, data));
    const text = readFile(ip);
    var lines = std.mem.tokenizeScalar(u8, text, '\n');
    while (lines.next()) |line| {
        if (std.mem.startsWith(u8, line, "key\t")) continue;
        var f = std.mem.splitScalar(u8, line, '\t');
        const key = f.next() orelse continue;
        _ = f.next(); // file
        _ = f.next(); // face
        const source = f.next() orelse "";
        const family = f.next() orelse "";
        const style = f.next() orelse "";
        const version = f.next() orelse "";
        const k = alloc.allocSentinel(u8, key.len, 0) catch die("out of memory", .{});
        @memcpy(k, key);
        fx_key.append(alloc, k) catch die("out of memory", .{});
        fx_family.append(alloc, family) catch die("out of memory", .{});
        fx_source.append(alloc, source) catch die("out of memory", .{});
        const ver = version[0 .. std.mem.indexOfScalar(u8, version, ';') orelse version.len];
        const lb = std.fmt.allocPrint(alloc, "{s} {s} {s} ({s})", .{ family, style, ver, source }) catch die("out of memory", .{});
        fx_label.append(alloc, lb) catch die("out of memory", .{});
    }
    const nf = fx_key.items.len;
    fx_lo = alloc.alloc(u32, nf) catch die("out of memory", .{});
    fx_hi = alloc.alloc(u32, nf) catch die("out of memory", .{});
    @memset(fx_lo, 0);
    @memset(fx_hi, 0);
    gi_la = alloc.alloc(f32, gi.len) catch die("out of memory", .{});
    var prev: u32 = std.math.maxInt(u32);
    for (gi, 0..) |e, i| {
        if (e.font >= nf) die("the glyph index names font {d} and the font index has {d}", .{ e.font, nf });
        if (e.font != prev) {
            if (prev != std.math.maxInt(u32) and e.font < prev) die("the glyph index is not sorted by font", .{});
            fx_lo[e.font] = @intCast(i);
            prev = e.font;
        }
        fx_hi[e.font] = @intCast(i + 1);
        gi_la[i] = @log(@max(e.aspect, 1e-4));
    }
    say("glyph index: {d} glyphs of {d} fonts\n", .{ gi.len, nf });
    return gi.len > 0;
}

const Desc = struct { bits: [4]u64, la: f32, plain: bool, rich: bool, area: usize, vote: bool };

/// a piece (or two pieces one above the other) as 16 by 16 bits stretched to its box, by majority
fn descOf(labels: []const u32, n: usize, sh: *const Shape) Desc {
    var d = Desc{ .bits = .{ 0, 0, 0, 0 }, .la = 0, .plain = sh.plain, .rich = sh.rich, .area = sh.area, .vote = true };
    const w = sh.x1 - sh.x0;
    const h = sh.y1 - sh.y0;
    for (0..16) |gy| {
        const ya = sh.y0 + gy * h / 16;
        const yb = @max(ya + 1, sh.y0 + (gy + 1) * h / 16);
        for (0..16) |gx| {
            const xa = sh.x0 + gx * w / 16;
            const xb = @max(xa + 1, sh.x0 + (gx + 1) * w / 16);
            var cnt: usize = 0;
            var tot: usize = 0;
            for (ya..@min(yb, n)) |y| {
                for (xa..@min(xb, n)) |x| {
                    tot += 1;
                    const l = labels[y * n + x];
                    if (owns(sh, l)) cnt += 1;
                }
            }
            if (tot > 0 and 2 * cnt >= tot) {
                const i = gy * 16 + gx;
                d.bits[i >> 6] |= @as(u64, 1) << @intCast(i & 63);
            }
        }
    }
    d.la = @log(@as(f32, @floatFromInt(w)) / @as(f32, @floatFromInt(@max(1, h))));
    return d;
}

fn ham(a: *const [4]u64, b: *const [4]u64) u32 {
    // each @popCount of a u64 is a 7-bit number: widen before adding, or 128 differing bits wrap to 0
    return @as(u32, @popCount(a[0] ^ b[0])) + @as(u32, @popCount(a[1] ^ b[1])) + @as(u32, @popCount(a[2] ^ b[2])) + @as(u32, @popCount(a[3] ^ b[3]));
}

/// how far apart, at the coarse size, a glyph may be to make its font a candidate, and to be read as a template
/// Pieces that may be one glyph together (a CJK character's radicals, a hieroglyph's parts, an i's dot): around each
/// piece, the pieces whose centres lie within a margin of its box, the union no larger than a glyph would be.
const MAXGROUP = 600;
var groups: [MAXGROUP]Shape = undefined;
var ngroups: usize = 0;

fn makeGroups(shapes: []const Shape) void {
    ngroups = 0;
    for (shapes) |*si| {
        for ([_]f32{ 0.35, 0.7 }) |fac| {
            const side: f32 = @floatFromInt(@max(si.x1 - si.x0, si.y1 - si.y0));
            const ex = fac * side;
            var g = Shape{ .x0 = si.x0, .y0 = si.y0, .x1 = si.x1, .y1 = si.y1, .area = 0, .rich = true };
            var nid: usize = 0;
            var ok = true;
            for (shapes) |*sj| {
                const cx = @as(f32, @floatFromInt(sj.x0 + sj.x1)) / 2.0;
                const cy = @as(f32, @floatFromInt(sj.y0 + sj.y1)) / 2.0;
                if (cx < @as(f32, @floatFromInt(si.x0)) - ex or cx > @as(f32, @floatFromInt(si.x1)) + ex) continue;
                if (cy < @as(f32, @floatFromInt(si.y0)) - ex or cy > @as(f32, @floatFromInt(si.y1)) + ex) continue;
                if (nid >= 6) {
                    ok = false;
                    break;
                }
                g.ids[nid] = sj.ids[0];
                nid += 1;
                g.x0 = @min(g.x0, sj.x0);
                g.y0 = @min(g.y0, sj.y0);
                g.x1 = @max(g.x1, sj.x1);
                g.y1 = @max(g.y1, sj.y1);
                g.area += sj.area;
            }
            if (!ok or nid < 2) continue;
            const ub: f32 = @floatFromInt(@max(g.x1 - g.x0, g.y1 - g.y0));
            if (ub > 1.8 * side) continue;
            std.mem.sort(u32, g.ids[0..nid], {}, std.sort.asc(u32));
            var dup = false;
            for (groups[0..ngroups]) |*o| if (std.mem.eql(u32, &o.ids, &g.ids)) {
                dup = true;
            };
            if (dup or ngroups >= MAXGROUP) continue;
            groups[ngroups] = g;
            ngroups += 1;
        }
    }
    // the larger groups are tried first, so a whole glyph is taken before a part of it
    std.mem.sort(Shape, groups[0..ngroups], {}, struct {
        fn lt(_: void, a: Shape, b: Shape) bool {
            return a.area > b.area;
        }
    }.lt);
}

const COARSE_SEL: u32 = 56;
const COARSE_TPL: u32 = 72;
const NCAND = 32;
const MAXTPL = 600; // templates drawn per candidate font, the closest first

/// Choose the figure's candidate fonts from the whole glyph index and draw their nearest glyphs as templates.
fn wideCandidates(shapes: []Shape, labels: []const u32, n: usize) void {
    templs.clearRetainingCapacity();
    templs_loaded = false;
    wide_now = true;
    cf_n = 0;
    const nf = fx_key.items.len;
    // the pieces, and every pair one above the other (an i, a j, a colon): their coarse pictures
    var descs: std.ArrayList(Desc) = .empty;
    defer descs.deinit(alloc);
    for (shapes) |*sh| descs.append(alloc, descOf(labels, n, sh)) catch die("out of memory", .{});
    for (shapes) |*sa| {
        for (shapes) |*sb| {
            if (sa == sb or sa.y1 > sb.y0) continue;
            const ov = @as(i64, @intCast(@min(sa.x1, sb.x1))) - @as(i64, @intCast(@max(sa.x0, sb.x0)));
            const wmin: i64 = @intCast(@min(sa.x1 - sa.x0, sb.x1 - sb.x0));
            if (ov * 2 < wmin) continue;
            const hmax = @max(sa.y1 - sa.y0, sb.y1 - sb.y0);
            if (sb.y0 - sa.y1 > hmax + hmax / 4) continue;
            const mg = Shape{ .x0 = @min(sa.x0, sb.x0), .y0 = sa.y0, .x1 = @max(sa.x1, sb.x1), .y1 = sb.y1, .area = sa.area + sb.area, .ids = .{ sa.ids[0], sb.ids[0], 0, 0, 0, 0 }, .rich = true };
            var d = descOf(labels, n, &mg);
            d.vote = false;
            descs.append(alloc, d) catch die("out of memory", .{});
        }
    }
    makeGroups(shapes);
    for (groups[0..ngroups]) |*g| {
        var d = descOf(labels, n, g);
        d.vote = false;
        descs.append(alloc, d) catch die("out of memory", .{});
    }
    const nd = descs.items.len;
    if (nd == 0) return;
    // the closest glyph of every font to every piece
    const best = alloc.alloc(u16, nd * nf) catch die("out of memory", .{});
    defer alloc.free(best);
    @memset(best, 0xffff);
    for (gi, gi_la) |*e, la| {
        for (descs.items, 0..) |*d, k| {
            const tol: f32 = if (d.plain) 0.5 else 0.27;
            if (@abs(la - d.la) > tol) continue;
            const h = ham(&e.bits, &d.bits);
            const at = k * nf + e.font;
            if (h < best[at]) best[at] = @intCast(h);
        }
    }
    // a font's worth: the ink of the pieces with form that its glyphs lie close over
    const worth = alloc.alloc(f32, nf) catch die("out of memory", .{});
    defer alloc.free(worth);
    @memset(worth, 0);
    for (descs.items, 0..) |*d, k| {
        if (!d.vote or !d.rich) continue;
        for (0..nf) |f| {
            const h = best[k * nf + f];
            if (h <= COARSE_SEL) worth[f] += @as(f32, @floatFromInt(d.area)) * (1.0 - @as(f32, @floatFromInt(h)) / @as(f32, @floatFromInt(COARSE_SEL + 1)));
        }
    }
    var pick: [NCAND]usize = undefined;
    var np: usize = 0;
    for (0..nf) |f| {
        if (worth[f] <= 0) continue;
        var at = np;
        while (at > 0 and worth[pick[at - 1]] < worth[f]) at -= 1;
        if (at >= NCAND) continue;
        var j = @min(np, NCAND - 1);
        while (j > at) : (j -= 1) pick[j] = pick[j - 1];
        pick[at] = f;
        if (np < NCAND) np += 1;
    }
    if (getenv("WZ_READDEBUG") != null) {
        for (pick[0..np]) |f| say("  candidate {s}: worth {d:.1}\n", .{ fx_label.items[f], worth[f] });
        if (getenv("WZ_READDEBUG_FONT")) |want| {
            for (0..nf) |f| {
                if (!std.mem.eql(u8, fx_key.items[f], std.mem.span(want))) continue;
                say("  {s}: worth {d:.1}; closest per piece:", .{ fx_label.items[f], worth[f] });
                for (0..nd) |k| say(" {d}", .{best[k * nf + f]});
                say("\n", .{});
            }
        }
    }
    // each candidate's glyphs that lie close over some piece, drawn from the font at 24 by 24
    var buf: [GS * GS]u8 = undefined;
    for (pick[0..np]) |f| {
        const ci = cf_n;
        const key = fx_key.items[f];
        cf_key[ci] = key;
        cf_label[ci] = fx_label.items[f];
        // the fonts werkkzeug3's artists named, installed on this machine: written as werkkzeug3's own Text
        const fam = fx_family.items[f];
        cf_v1[ci] = false;
        cf_v1name[ci] = "";
        if (std.mem.eql(u8, fx_source.items[f], "machine")) {
            if (std.ascii.eqlIgnoreCase(fam, "arial") and std.mem.endsWith(u8, key, "/Regular")) {
                cf_v1[ci] = true;
                cf_v1name[ci] = "";
            } else if (std.ascii.eqlIgnoreCase(fam, "times new roman") and std.mem.endsWith(u8, key, "/Regular")) {
                cf_v1[ci] = true;
                cf_v1name[ci] = "times new roman";
            } else if (std.ascii.eqlIgnoreCase(fam, "verdana") and std.mem.endsWith(u8, key, "/Regular")) {
                cf_v1[ci] = true;
                cf_v1name[ci] = "verdana";
            }
        }
        var sp: f32 = 0;
        var av: f32 = 0;
        if (wzb_font_spacing(key.ptr, &sp, &av) != 0) continue;
        font_space[ci] = sp;
        font_avg[ci] = av;
        font_have[ci] = false;
        // the glyphs, closest first
        var near: std.ArrayList([2]u32) = .empty;
        defer near.deinit(alloc);
        var i: usize = fx_lo[f];
        while (i < fx_hi[f]) : (i += 1) {
            const e = &gi[i];
            var bh: u32 = 999;
            for (descs.items) |*d| {
                const tol: f32 = if (d.plain) 0.5 else 0.27;
                if (@abs(gi_la[i] - d.la) > tol) continue;
                bh = @min(bh, ham(&e.bits, &d.bits));
            }
            if (bh <= COARSE_TPL) near.append(alloc, .{ bh, @intCast(i) }) catch die("out of memory", .{});
        }
        std.mem.sort([2]u32, near.items, {}, struct {
            fn lt(_: void, a: [2]u32, b: [2]u32) bool {
                return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1]);
            }
        }.lt);
        for (near.items[0..@min(near.items.len, MAXTPL)]) |nb| {
            const e = &gi[nb[1]];
            // a presentation variant (a superscript, a fullwidth or mathematical letter, a combining mark) is the same
            // shape as its plain character stretched to its box: the plain character is the reading
            if (uc_class(e.cp) == 2) continue;
            var v: [6]f32 = undefined;
            var form: c_int = 0;
            if (wzb_glyph_mask2(key.ptr, e.cp, GS, &buf, &v, &form, null) != 0) continue;
            font_have[ci] = true;
            var tp = Templ{ .font = @intCast(ci), .ch = e.cp, .m = undefined, .aspect = v[0], .inkh = v[1], .top = v[2], .adv = v[3], .lsb = v[4], .plain = false, .parts = 1, .rich = false };
            for (0..GS * GS) |q| tp.m[q] = buf[q] >= 128;
            tp.plain = plainShape(&tp.m);
            tp.parts = partsOf(&tp.m);
            tp.rich = richShape(&tp.m);
            templs.append(alloc, tp) catch die("out of memory", .{});
        }
        if (font_have[ci]) cf_n += 1;
    }
}

/// A text read over the whole index, as werkkzeug3's own Text when its font is one the artists named and is
/// installed here and every letter is in code page 1252; otherwise as version 2 (UTF-8, the index's key).
fn textNode2(tr: *const TextRead, col: u32) Node {
    var nd = Node{ .op = OP_TEXT, .nw = 9, .keep = true };
    nd.w[0] = wordOf(tr.x);
    nd.w[1] = wordOf(tr.y);
    nd.w[2] = wordOf(tr.size);
    nd.w[3] = wordOf(tr.wide);
    nd.w[4] = col;
    nd.w[5] = 0;
    nd.w[6] = 2;
    nd.w[7] = wordOf(0.0);
    nd.w[8] = wordOf(1.0);
    if (cf_v1[tr.font]) {
        var b: [200]u8 = undefined;
        var l: usize = 0;
        var ok = true;
        var it = std.unicode.Utf8View.initUnchecked(tr.str[0..tr.len]).iterator();
        while (it.nextCodepoint()) |c| {
            const byte = cp1252Of(c) orelse {
                ok = false;
                break;
            };
            b[l] = byte;
            l += 1;
        }
        if (ok) {
            nd.s[0] = intern(b[0..l]);
            nd.s[1] = intern(cf_v1name[tr.font]);
            return nd;
        }
    }
    nd.nw = TEXT2_WORDS;
    nd.w[9] = 2;
    nd.w[10] = 0; // the palette
    nd.w[11] = 0; // the form: auto
    nd.s[0] = intern(tr.str[0..tr.len]);
    nd.s[1] = intern(cf_key[tr.font]);
    nd.s[2] = 0;
    return nd;
}

/// A line is read left to right, as it stands on the picture. A text in a right-to-left script (Hebrew, Arabic, Syriac,
/// Thaana, N'Ko and the others UAX #9 gives the classes R and AL) is stored in logical order, so its characters are
/// turned around: the text then draws through UAX #9 (rule L2) as it was read. Lines that mix directions stay as read.
fn logicalOrder(tr: *TextRead) void {
    var cps: [200]u21 = undefined;
    var n: usize = 0;
    var rtl: usize = 0;
    var ltr: usize = 0;
    var it = std.unicode.Utf8View.initUnchecked(tr.str[0..tr.len]).iterator();
    while (it.nextCodepoint()) |c| {
        if (n >= cps.len) return;
        cps[n] = c;
        n += 1;
        const r = (c >= 0x0590 and c <= 0x08FF) or (c >= 0xFB1D and c <= 0xFDFF) or (c >= 0xFE70 and c <= 0xFEFF) or (c >= 0x10800 and c <= 0x10FFF) or (c >= 0x1E800 and c <= 0x1EFFF);
        if (r) rtl += 1 else if (c > 0x40 and c != 0x20) ltr += 1;
    }
    if (rtl == 0 or ltr > 0) return;
    var out: [200]u8 = undefined;
    var l: usize = 0;
    var i = n;
    while (i > 0) {
        i -= 1;
        const k = std.unicode.utf8Encode(cps[i], out[l..]) catch return;
        l += k;
    }
    @memcpy(tr.str[0..l], out[0..l]);
    tr.len = l;
}

/// Latin, Greek and Cyrillic share letters drawn by one glyph in many fonts (A, Α, А): the shape cannot tell them apart.
/// A letter of one of these scripts in a line of another is turned into that script's own letter when the font draws
/// both alike (their glyphs lie over each other by 0.97 or more at 24 by 24, with the same advance).
const homoglyphs = [_][3]u21{
    .{ 'A', 0x391, 0x410 }, .{ 'B', 0x392, 0x412 }, .{ 'C', 0, 0x421 },     .{ 'E', 0x395, 0x415 }, .{ 'H', 0x397, 0x41D },
    .{ 'I', 0x399, 0x406 }, .{ 'J', 0, 0x408 },     .{ 'K', 0x39A, 0x41A }, .{ 'M', 0x39C, 0x41C }, .{ 'N', 0x39D, 0 },
    .{ 'O', 0x39F, 0x41E }, .{ 'P', 0x3A1, 0x420 }, .{ 'S', 0, 0x405 },     .{ 'T', 0x3A4, 0x422 }, .{ 'X', 0x3A7, 0x425 },
    .{ 'Y', 0x3A5, 0x4AE }, .{ 'Z', 0x396, 0 },     .{ 'a', 0, 0x430 },     .{ 'c', 0, 0x441 },     .{ 'e', 0, 0x435 },
    .{ 'i', 0, 0x456 },     .{ 'j', 0, 0x458 },     .{ 'o', 0x3BF, 0x43E }, .{ 'p', 0, 0x440 },     .{ 's', 0, 0x455 },
    .{ 'x', 0, 0x445 },     .{ 'y', 0, 0x443 },
};

fn scriptOf(c: u21) u8 {
    if ((c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z') or (c >= 0xC0 and c <= 0x24F)) return 0;
    if ((c >= 0x370 and c <= 0x3FF) or (c >= 0x1F00 and c <= 0x1FFF)) return 1;
    if (c >= 0x400 and c <= 0x52F) return 2;
    return 3;
}

fn sameGlyph(key: [:0]const u8, a: u21, b: u21) bool {
    var ma: [GS * GS]u8 = undefined;
    var mb: [GS * GS]u8 = undefined;
    var va: [6]f32 = undefined;
    var vb: [6]f32 = undefined;
    var fa: c_int = 0;
    var fb: c_int = 0;
    if (wzb_glyph_mask2(key.ptr, a, GS, &ma, &va, &fa, null) != 0) return false;
    if (wzb_glyph_mask2(key.ptr, b, GS, &mb, &vb, &fb, null) != 0) return false;
    var both: usize = 0;
    var either: usize = 0;
    for (ma, mb) |x, y| {
        if (x >= 128 and y >= 128) both += 1;
        if (x >= 128 or y >= 128) either += 1;
    }
    if (either == 0) return false;
    const io = @as(f32, @floatFromInt(both)) / @as(f32, @floatFromInt(either));
    return io >= 0.97 and @abs(va[3] - vb[3]) <= 0.02 and @abs(va[1] - vb[1]) <= 0.02;
}

fn oneScript(tr: *TextRead, key: [:0]const u8) void {
    var cps: [200]u21 = undefined;
    var n: usize = 0;
    var count = [4]usize{ 0, 0, 0, 0 };
    var it = std.unicode.Utf8View.initUnchecked(tr.str[0..tr.len]).iterator();
    while (it.nextCodepoint()) |c| {
        if (n >= cps.len) return;
        cps[n] = c;
        n += 1;
        // only letters no other of the three scripts draws alike say which script the line is in
        var ambiguous = false;
        for (homoglyphs) |h| {
            if (h[0] == c or h[1] == c or h[2] == c) ambiguous = true;
        }
        if (!ambiguous) count[scriptOf(c)] += 1;
    }
    var major: u8 = 0;
    for (0..3) |k| if (count[k] > count[major]) {
        major = @intCast(k);
    };
    if (count[major] == 0) return;
    var changed = false;
    for (cps[0..n]) |*c| {
        const sc = scriptOf(c.*);
        if (sc == major or sc == 3) continue;
        for (homoglyphs) |h| {
            if (h[sc] != c.* or h[major] == 0) continue;
            if (sameGlyph(key, c.*, h[major])) {
                c.* = h[major];
                changed = true;
            }
            break;
        }
    }
    if (!changed) return;
    var out: [200]u8 = undefined;
    var l: usize = 0;
    for (cps[0..n]) |c| l += std.unicode.utf8Encode(c, out[l..]) catch return;
    @memcpy(tr.str[0..l], out[0..l]);
    tr.len = l;
}

/// the byte of Windows code page 1252 for a character, or null
fn cp1252Of(c: u21) ?u8 {
    const high = [32]u16{ 0x20AC, 0x0081, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x02C6, 0x2030, 0x0160, 0x2039, 0x0152, 0x008D, 0x017D, 0x008F, 0x0090, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0x009D, 0x017E, 0x0178 };
    if (c < 0x80 or (c >= 0xA0 and c <= 0xFF)) return @intCast(c);
    for (high, 0..) |h, i| if (h == c) return @intCast(0x80 + i);
    return null;
}

/// the connected pieces of the ink, each with its box; returns how many, or MAXSHAPE + 1 when there are more
fn pieces(ink: []const bool, n: usize, labels: []u32, out: []Shape) usize {
    @memset(labels, 0);
    const stack = alloc.alloc(u32, n * n) catch die("out of memory", .{});
    defer alloc.free(stack);
    var count: usize = 0;
    for (0..n * n) |s| {
        if (!ink[s] or labels[s] != 0) continue;
        if (count >= MAXSHAPE) return MAXSHAPE + 1;
        const id: u32 = @intCast(count + 1);
        var sh = Shape{ .x0 = n, .y0 = n, .x1 = 0, .y1 = 0, .ids = .{ id, 0, 0, 0, 0, 0 } };
        var sp: usize = 0;
        stack[sp] = @intCast(s);
        sp += 1;
        labels[s] = id;
        while (sp > 0) {
            sp -= 1;
            const p: usize = stack[sp];
            const x = p % n;
            const y = p / n;
            sh.area += 1;
            sh.x0 = @min(sh.x0, x);
            sh.y0 = @min(sh.y0, y);
            sh.x1 = @max(sh.x1, x + 1);
            sh.y1 = @max(sh.y1, y + 1);
            if (x > 0 and ink[p - 1] and labels[p - 1] == 0) {
                labels[p - 1] = id;
                stack[sp] = @intCast(p - 1);
                sp += 1;
            }
            if (x + 1 < n and ink[p + 1] and labels[p + 1] == 0) {
                labels[p + 1] = id;
                stack[sp] = @intCast(p + 1);
                sp += 1;
            }
            if (y > 0 and ink[p - n] and labels[p - n] == 0) {
                labels[p - n] = id;
                stack[sp] = @intCast(p - n);
                sp += 1;
            }
            if (y + 1 < n and ink[p + n] and labels[p + n] == 0) {
                labels[p + n] = id;
                stack[sp] = @intCast(p + n);
                sp += 1;
            }
        }
        out[count] = sh;
        count += 1;
    }
    return count;
}

const TextRead = struct {
    font: u16 = 0,
    x: f32 = 0,
    y: f32 = 0,
    size: f32 = 0,
    wide: f32 = 0,
    len: usize = 0,
    str: [200]u8 = undefined,
    nm: usize = 0, // its letters: the piece and the glyph each was read as (for the closer look that tells fonts apart)
    mshape: [48]u16 = undefined,
    mtpl: [48]u16 = undefined,
};
const MAXTEXT = 24;
const Figure = struct {
    two: f32 = 0, // the share of the picture in the two flat shades
    ink: f32 = 0, // the smaller shade's share: the ink
    ink_high: bool = true,
    nshape: usize = 0,
    nrich: usize = 0, // pieces with enough form to be a glyph on their own
    font: u16 = 0,
    explained: f32 = 0, // the share of the ink that lies in shapes read as glyphs on a line
    like: f32 = 0, // how well those shapes lie over their glyphs (1: exactly)
    best_single: f32 = 0, // how well each piece lies over its best glyph, weighted by the pieces' ink, line or no line
    ntext: usize = 0,
    texts: [MAXTEXT]TextRead = undefined,
    nun: usize = 0, // twirls taken out of the picture before the glyphs were read: strength, gamma, radius, centre x, y
    un: [3][5]f32 = undefined,
    colour: bool = false, // read as colour glyphs on a flat ground of any colour (not two flat shades)
    ground: u32 = 0, // that ground's colour
};

/// the glyphs of one font that lie over a shape well enough, the best first
fn shapeCands(sh: *Shape, font: u16, parts_min: u8) void {
    sh.nc = 0;
    sh.best = 0;
    const asp = @as(f32, @floatFromInt(sh.x1 - sh.x0)) / @as(f32, @floatFromInt(@max(1, sh.y1 - sh.y0)));
    for (templs.items, 0..) |*tp, ti| {
        if (tp.font != font or tp.parts < parts_min) continue;
        if (sh.plain != tp.plain) continue;
        // the shape's own proportions must be the glyph's (a stretched text keeps them within this)
        const ra = @abs(@log(asp / tp.aspect));
        if (ra > @as(f32, if (sh.plain) 0.5 else 0.27)) continue;
        const v = iou(&sh.m, &tp.m) - (if (wide_now and uc_class(tp.ch) == 1) SPECIAL_PENALTY else 0);
        if (sh.rich and tp.rich) sh.best = @max(sh.best, v);
        if (v < glyph_t - MEMBER_SLACK) continue;
        var at = sh.nc;
        while (at > 0 and sh.ci[at - 1] < v) at -= 1;
        if (at >= MAXC) continue;
        var j = @min(sh.nc, MAXC - 1);
        while (j > at) : (j -= 1) {
            sh.c[j] = sh.c[j - 1];
            sh.ci[j] = sh.ci[j - 1];
        }
        sh.c[at] = @intCast(ti);
        sh.ci[at] = v;
        if (sh.nc < MAXC) sh.nc += 1;
    }
}

/// the labels of the figure in hand, for a closer look at a piece
var cur_labels: []const u32 = &.{};
var cur_n: usize = 0;
const GL = 48;

/// Glyphs that lie almost equally well over a piece at 24 by 24 (1 and l, O and 0 in a serif face) are compared again
/// at 48 by 48, drawn from the font, and the closer one is taken.
fn closerLook(sh: *const Shape, chosen: u16, chosen_worth: f32, em: f32, top: f32) u16 {
    var near: [8]u16 = undefined;
    var nn: usize = 0;
    const tol2 = 2.0 * @max(1.6, 0.06 * em);
    for (sh.c[0..sh.nc], sh.ci[0..sh.nc]) |tj, vj| {
        const e = fitsLine(sh, &templs.items[tj], em, top);
        if (e < 0) continue;
        if (vj - 0.1 * e / tol2 >= chosen_worth - 0.06 and nn < near.len) {
            near[nn] = tj;
            nn += 1;
        }
    }
    if (nn < 2 or cur_n == 0) return chosen;
    // the piece at 48 by 48
    var pm: [GL * GL]bool = undefined;
    const w = sh.x1 - sh.x0;
    const h = sh.y1 - sh.y0;
    for (0..GL) |gy| for (0..GL) |gx| {
        const ya = sh.y0 + gy * h / GL;
        const yb = @max(ya + 1, sh.y0 + (gy + 1) * h / GL);
        const xa = sh.x0 + gx * w / GL;
        const xb = @max(xa + 1, sh.x0 + (gx + 1) * w / GL);
        var cnt: usize = 0;
        var tot: usize = 0;
        for (ya..@min(yb, cur_n)) |y| for (xa..@min(xb, cur_n)) |x| {
            tot += 1;
            if (owns(sh, cur_labels[y * cur_n + x])) cnt += 1;
        };
        pm[gy * GL + gx] = tot > 0 and 2 * cnt >= tot;
    };
    var best = chosen;
    var best_v: f32 = -1;
    for (near[0..nn]) |tj| {
        const tp = &templs.items[tj];
        var m: [GL * GL]u8 = undefined;
        var v: [6]f32 = undefined;
        var form: c_int = 0;
        if (wzb_glyph_mask2(cf_key[tp.font].ptr, tp.ch, GL, &m, &v, &form, null) != 0) continue;
        var both: usize = 0;
        var either: usize = 0;
        for (0..GL * GL) |q| {
            const a = m[q] >= 128;
            if (a and pm[q]) both += 1;
            if (a or pm[q]) either += 1;
        }
        const io = if (either > 0) @as(f32, @floatFromInt(both)) / @as(f32, @floatFromInt(either)) else 0;
        if (io > best_v) {
            best_v = io;
            best = tj;
        }
    }
    return best;
}

/// the script of a letter, by its block (0 none: digits, punctuation, symbols and the scripts not listed)
fn letterScript(c: u32) u8 {
    if ((c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z') or (c >= 0xC0 and c <= 0x24F) or (c >= 0x1E00 and c <= 0x1EFF)) return 1;
    if ((c >= 0x370 and c <= 0x3FF) or (c >= 0x1F00 and c <= 0x1FFF)) return 2;
    if (c >= 0x400 and c <= 0x52F) return 3;
    if (c >= 0x530 and c <= 0x58F) return 4;
    if (c >= 0x590 and c <= 0x5FF) return 5;
    if ((c >= 0x600 and c <= 0x8FF) or (c >= 0xFB50 and c <= 0xFEFF)) return 6;
    if ((c >= 0x13A0 and c <= 0x13FF) or (c >= 0xAB70 and c <= 0xABBF)) return 7;
    if (c >= 0x10A0 and c <= 0x10FF) return 8;
    if (c >= 0x900 and c <= 0xDFF) return 9;
    if (c >= 0xE00 and c <= 0xEFF) return 10;
    if ((c >= 0x1100 and c <= 0x11FF) or (c >= 0x3130 and c <= 0x318F) or (c >= 0xAC00 and c <= 0xD7AF)) return 11;
    if ((c >= 0x2E80 and c <= 0x9FFF) or (c >= 0xF900 and c <= 0xFAFF) or (c >= 0x20000 and c <= 0x3FFFF)) return 12;
    if (c >= 0x1200 and c <= 0x139F) return 13;
    return 0;
}

/// One script per line: the script most of a line's ink is read in is its script, and a letter read in another script
/// is read again as that script's best letter when one lies almost as well over it (within 0.12): Cherokee Ꭵ for i,
/// Armenian ո for n, Cyrillic р for p in a Latin line are the same shapes, not the plainer reading.
fn oneScriptLine(shapes: []Shape, members: []const usize, pick: []u16, em: f32, top: f32) void {
    var ink = [_]usize{0} ** 14;
    for (members) |j| ink[letterScript(templs.items[pick[j]].ch)] += shapes[j].area;
    var major: usize = 1;
    for (1..14) |k| if (ink[k] > ink[major]) {
        major = k;
    };
    if (ink[major] == 0) return;
    const tol2 = 2.0 * @max(1.6, 0.06 * em);
    for (members) |j| {
        const sc = letterScript(templs.items[pick[j]].ch);
        if (sc == 0 or sc == major) continue;
        const sh = &shapes[j];
        var chosen_v: f32 = 0;
        for (sh.c[0..sh.nc], sh.ci[0..sh.nc]) |tj, vj| if (tj == pick[j]) {
            chosen_v = vj;
        };
        var best: ?u16 = null;
        var bv: f32 = -1;
        for (sh.c[0..sh.nc], sh.ci[0..sh.nc]) |tj, vj| {
            if (letterScript(templs.items[tj].ch) != major) continue;
            const e = fitsLine(sh, &templs.items[tj], em, top);
            if (e < 0) continue;
            const w = vj - 0.1 * e / tol2;
            if (w > bv) {
                bv = w;
                best = tj;
            }
        }
        if (best) |b| {
            if (bv >= chosen_v - 0.12) pick[j] = b;
        }
    }
}

fn fitsLine(sh: *const Shape, tp: *const Templ, em: f32, top: f32) f32 {
    const tol = @max(1.6, 0.06 * em);
    const h: f32 = @floatFromInt(sh.y1 - sh.y0);
    const e1 = @abs(h - tp.inkh * em);
    const e2 = @abs(@as(f32, @floatFromInt(sh.y0)) - (top + tp.top * em));
    if (e1 > tol or e2 > tol) return -1;
    return e1 + e2;
}

/// Read the shapes as lines of one font's glyphs. Returns the ink explained (pixels) and adds the texts to fig.
fn readLines(shapes: []Shape, font: u16, n: usize, fig: *Figure, like_sum: *f64) usize {
    var explained: usize = 0;
    for (shapes) |*sh| {
        sh.used = false;
        if (!sh.dead) shapeCands(sh, font, 1);
    }
    const order = alloc.alloc(usize, shapes.len) catch die("out of memory", .{});
    defer alloc.free(order);
    const pick = alloc.alloc(u16, shapes.len) catch die("out of memory", .{});
    defer alloc.free(pick);
    var lines: usize = 0;
    while (lines < MAXTEXT) : (lines += 1) {
        // the line (size and top) most shapes agree on; a line needs one shape that is no box and no disc
        var best_n: usize = 0;
        var best_s: f32 = 0;
        var best_em: f32 = 0;
        var best_top: f32 = 0;
        for (shapes) |*si| {
            if (si.used or si.dead or !si.rich) continue;
            for (si.c[0..si.nc], si.ci[0..si.nc]) |ti, vi| {
                if (vi < glyph_t) continue;
                const tp = &templs.items[ti];
                if (!tp.rich) continue;
                const em = @as(f32, @floatFromInt(si.y1 - si.y0)) / tp.inkh;
                const top = @as(f32, @floatFromInt(si.y0)) - tp.top * em;
                var cnt: usize = 0;
                var sum: f32 = 0;
                for (shapes) |*sj| {
                    if (sj.used or sj.dead) continue;
                    for (sj.c[0..sj.nc], sj.ci[0..sj.nc]) |tj, vj| {
                        if (fitsLine(sj, &templs.items[tj], em, top) >= 0) {
                            cnt += 1;
                            sum += vj;
                            break;
                        }
                    }
                }
                if (cnt > best_n or (cnt == best_n and sum > best_s)) {
                    best_n = cnt;
                    best_s = sum;
                    best_em = em;
                    best_top = top;
                }
            }
        }
        if (best_n == 0) break;
        // its members, left to right, each with the glyph whose box fits best
        var m: usize = 0;
        for (shapes, 0..) |*sj, j| {
            if (sj.used or sj.dead) continue;
            // of the glyphs that fit the line, the one that lies best over the shape; how well its box fits the line
            // counts for a tenth at most, enough to tell o from O and not enough to take an n for an o
            var bt: ?u16 = null;
            var be: f32 = -1e9;
            const tol2 = 2.0 * @max(1.6, 0.06 * best_em);
            for (sj.c[0..sj.nc], sj.ci[0..sj.nc]) |tj, vj| {
                const e = fitsLine(sj, &templs.items[tj], best_em, best_top);
                if (e < 0) continue;
                const worth = vj - 0.1 * e / tol2;
                if (worth > be) {
                    be = worth;
                    bt = tj;
                }
            }
            if (bt) |tj| {
                order[m] = j;
                pick[j] = if (wide_now) closerLook(sj, tj, be, best_em, best_top) else tj;
                m += 1;
            }
        }
        var a: usize = 1;
        while (a < m) : (a += 1) {
            const v = order[a];
            var b = a;
            while (b > 0 and shapes[order[b - 1]].x0 > shapes[v].x0) : (b -= 1) order[b] = order[b - 1];
            order[b] = v;
        }
        if (wide_now and m > 1) oneScriptLine(shapes, order[0..m], pick, best_em, best_top);
        // a text stretched sideways: the middle value of the letters' own stretch
        var sx: f32 = 1;
        {
            var rs: [MAXSHAPE]f32 = undefined;
            var nr: usize = 0;
            for (order[0..m]) |j| {
                const sh = &shapes[j];
                if (sh.plain) continue;
                rs[nr] = (@as(f32, @floatFromInt(sh.x1 - sh.x0)) / @as(f32, @floatFromInt(sh.y1 - sh.y0))) / templs.items[pick[j]].aspect;
                nr += 1;
            }
            if (nr > 0) {
                std.mem.sort(f32, rs[0..nr], {}, std.sort.asc(f32));
                sx = rs[nr / 2];
                if (@abs(sx - 1.0) < 0.06) sx = 1;
            }
        }
        const fn_: f32 = @floatFromInt(n);
        const space = font_space[font] * best_em * sx;
        var k: usize = 0;
        while (k < m) {
            // one Text operator: the letters that follow each other by the font's own advances, spaces between
            if (fig.ntext >= MAXTEXT) break;
            var tr = TextRead{ .font = font };
            const s0 = &shapes[order[k]];
            const t0 = &templs.items[pick[order[k]]];
            const pen0 = @as(f32, @floatFromInt(s0.x0)) - t0.lsb * best_em * sx;
            // werkkzeug3 draws a plain text (space + 2) pixels right and down of where its values say; the space
            // around letters is 2 in every plain text of .kkrieger (the operator's own default), so 4 pixels
            tr.x = (pen0 - 4.0) / fn_;
            tr.y = (best_top - 4.0) / fn_;
            tr.size = best_em / fn_;
            tr.wide = if (sx == 1) 0 else sx * font_avg[font] * best_em / fn_;
            var expect = pen0;
            while (k < m and tr.len + 42 < tr.str.len) {
                const sh = &shapes[order[k]];
                const tp = &templs.items[pick[order[k]]];
                const pen = @as(f32, @floatFromInt(sh.x0)) - tp.lsb * best_em * sx;
                const gap = pen - expect;
                const nsp_f = if (space > 0) @round(gap / space) else 0;
                const tol = @max(1.6, 0.08 * best_em);
                if (nsp_f < 0 or nsp_f > 40 or @abs(gap - nsp_f * space) > tol) break;
                var q: usize = 0;
                while (q < @as(usize, @intFromFloat(nsp_f))) : (q += 1) {
                    tr.str[tr.len] = ' ';
                    tr.len += 1;
                }
                if (wide_now) {
                    // the glyph's character as UTF-8 (version 2 Text)
                    var u8b: [4]u8 = undefined;
                    const ul = std.unicode.utf8Encode(@intCast(tp.ch), &u8b) catch 1;
                    if (ul == 1 and tp.ch > 127) u8b[0] = '?';
                    @memcpy(tr.str[tr.len .. tr.len + ul], u8b[0..ul]);
                    tr.len += ul;
                } else {
                    tr.str[tr.len] = @intCast(tp.ch);
                    tr.len += 1;
                }
                expect += nsp_f * space + @round(tp.adv * best_em * sx);
                sh.used = true;
                if (tr.nm < tr.mshape.len) {
                    tr.mshape[tr.nm] = @intCast(order[k]);
                    tr.mtpl[tr.nm] = pick[order[k]];
                    tr.nm += 1;
                }
                explained += sh.area;
                var vv: f32 = 0;
                for (sh.c[0..sh.nc], sh.ci[0..sh.nc]) |tc, vc| {
                    if (tc == pick[order[k]]) vv = vc;
                }
                like_sum.* += @as(f64, vv) * @as(f64, @floatFromInt(sh.area));
                k += 1;
            }
            if (tr.len == 0) {
                // a shape that does not follow: it starts a text of its own on the next turn
                shapes[order[k]].used = true;
                k += 1;
                continue;
            }
            if (wide_now) {
                oneScript(&tr, cf_key[font]);
                logicalOrder(&tr);
            }
            fig.texts[fig.ntext] = tr;
            fig.ntext += 1;
        }
        // members that were not placed stay out of further lines
        for (order[0..m]) |j| shapes[j].used = true;
    }
    return explained;
}

/// The figure reading, on the picture along its colour axis (0..1, n by n).
fn readFigure(t: []const f32, n: usize, fig: *Figure) void {
    if (!giLoad() or wide_off) loadTemplates();
    fig.ntext = 0;
    fig.explained = 0;
    fig.like = 0;
    fig.best_single = 0;
    var lo: usize = 0;
    var hi: usize = 0;
    for (t) |v| {
        if (v < 0.25) lo += 1;
        if (v > 0.75) hi += 1;
    }
    const tot: f32 = @floatFromInt(n * n);
    fig.two = @as(f32, @floatFromInt(lo + hi)) / tot;
    fig.ink_high = hi <= lo;
    fig.ink = @as(f32, @floatFromInt(@min(lo, hi))) / tot;
    fig.nshape = 0;
    if (fig.two < TWO_T or fig.ink < 0.0005) return;
    const ink = alloc.alloc(bool, n * n) catch die("out of memory", .{});
    defer alloc.free(ink);
    var ink_px: usize = 0;
    for (t, ink) |v, *b| {
        b.* = if (fig.ink_high) v > 0.5 else v < 0.5;
        if (b.*) ink_px += 1;
    }
    const labels = alloc.alloc(u32, n * n) catch die("out of memory", .{});
    defer alloc.free(labels);
    const shapes = alloc.alloc(Shape, MAXSHAPE * 2) catch die("out of memory", .{});
    defer alloc.free(shapes);
    const ns = pieces(ink, n, labels, shapes);
    fig.nshape = ns;
    if (ns > MAXSHAPE or ns == 0) return;
    fig.nrich = 0;
    for (shapes[0..ns]) |*sh| {
        shapeMask(labels, n, sh);
        if (sh.rich) fig.nrich += 1;
    }
    if (giLoad() and !wide_off) wideCandidates(shapes[0..ns], labels, n);
    cur_labels = labels;
    cur_n = n;
    defer cur_n = 0;
    var best_font: u16 = 0;
    var best_val: f64 = -1;
    var best_fig = Figure{};
    const WRead = struct { fig: Figure, val: f64, font: u16 };
    var wread: [MAXCF]WRead = undefined;
    var nwr: usize = 0;
    for (0..cf_n) |fi| {
        if (!font_have[fi]) continue;
        const font: u16 = @intCast(fi);
        // two pieces one above the other that together are a glyph of two pieces (i, j, !, ?, :, ;, =)
        var nn = ns;
        for (shapes[0..ns]) |*sh| sh.dead = false;
        if (wide_now) {
            // groups of pieces that lie over one glyph of several pieces, the largest first
            for (groups[0..ngroups]) |*gr| {
                if (nn >= MAXSHAPE * 2) break;
                var free = true;
                for (shapes[0..ns]) |*sh| {
                    if (sh.dead and owns(gr, sh.ids[0])) free = false;
                }
                if (!free) continue;
                var mg = gr.*;
                shapeMask(labels, n, &mg);
                mg.plain = false;
                mg.rich = true;
                shapeCands(&mg, font, 2);
                // a group is one glyph only when it lies over a glyph better than its pieces lie over theirs (a CJK
                // character's radicals are no glyphs of the font on their own; a t beside an i are)
                var mbest: f64 = 0;
                var marea: f64 = 0;
                for (shapes[0..ns]) |*sh| {
                    if (!owns(gr, sh.ids[0])) continue;
                    var one = sh.*;
                    shapeCands(&one, font, 1);
                    mbest += @as(f64, if (one.nc > 0) one.ci[0] else 0) * @as(f64, @floatFromInt(sh.area));
                    marea += @floatFromInt(sh.area);
                }
                const pieces_like: f32 = if (marea > 0) @floatCast(mbest / marea) else 0;
                if (wide_now and getenv("WZ_READDEBUG2") != null and mg.nc > 0) say("    group of {s} at {d},{d}: U+{X} {d:.3} against its pieces {d:.3}\n", .{ cf_label[fi], mg.x0, mg.y0, templs.items[mg.c[0]].ch, mg.ci[0], pieces_like });
                if (mg.nc > 0 and mg.ci[0] >= glyph_t and mg.ci[0] > pieces_like + 0.05) {
                    for (shapes[0..ns]) |*sh| {
                        if (owns(gr, sh.ids[0])) sh.dead = true;
                    }
                    shapes[nn] = mg;
                    nn += 1;
                }
            }
        }
        for (0..ns) |a| {
            for (0..ns) |b| {
                if (a == b or shapes[a].dead or shapes[b].dead or nn >= MAXSHAPE * 2) continue;
                const sa = &shapes[a];
                const sb = &shapes[b];
                if (sa.y1 > sb.y0) continue; // a lies above b
                const ov = @as(i64, @intCast(@min(sa.x1, sb.x1))) - @as(i64, @intCast(@max(sa.x0, sb.x0)));
                const wmin: i64 = @intCast(@min(sa.x1 - sa.x0, sb.x1 - sb.x0));
                if (ov * 2 < wmin) continue;
                const hmax = @max(sa.y1 - sa.y0, sb.y1 - sb.y0);
                if (sb.y0 - sa.y1 > hmax + hmax / 4) continue;
                var mg = Shape{ .x0 = @min(sa.x0, sb.x0), .y0 = sa.y0, .x1 = @max(sa.x1, sb.x1), .y1 = sb.y1, .area = sa.area + sb.area, .ids = .{ sa.ids[0], sb.ids[0], 0, 0, 0, 0 } };
                if (sa.ids[1] != 0 or sb.ids[1] != 0) continue;
                shapeMask(labels, n, &mg);
                mg.plain = false;
                mg.rich = true; // two pieces that are one glyph (i, j, ?, !): crossed twice by every line through both
                shapeCands(&mg, font, 2);
                if (wide_now and getenv("WZ_READDEBUG2") != null) say("    pair {d},{d} of {s}: {d} glyphs, best {d:.3} U+{X}\n", .{ a, b, cf_label[fi], mg.nc, if (mg.nc > 0) mg.ci[0] else 0, if (mg.nc > 0) templs.items[mg.c[0]].ch else 0 });
                if (mg.nc > 0 and mg.ci[0] >= glyph_t + (if (wide_now) @as(f32, 0.0) else @as(f32, 0.08))) {
                    shapes[a].dead = true;
                    shapes[b].dead = true;
                    shapes[nn] = mg;
                    nn += 1;
                }
            }
        }
        var f2 = Figure{};
        var like_sum: f64 = 0;
        const ex = readLines(shapes[0..nn], font, n, &f2, &like_sum);
        // every piece's best glyph, weighted by the piece's ink: one small piece that happens to look like a
        // letter does not make a shredded figure a text
        var single: f32 = 0;
        for (shapes[0..nn]) |*sh| {
            if (!sh.dead) single += sh.best * @as(f32, @floatFromInt(sh.area));
        }
        single /= @as(f32, @floatFromInt(@max(1, ink_px)));
        f2.explained = @as(f32, @floatFromInt(ex)) / @as(f32, @floatFromInt(@max(1, ink_px)));
        f2.like = if (ex > 0) @floatCast(like_sum / @as(f64, @floatFromInt(ex))) else 0;
        f2.best_single = single;
        // over every font, a reading that mixes scripts (Armenian n, Cherokee i and IPA letters in a Latin line) is
        // not the plainer one: the share of its letters' ink in its main script weighs it
        const val = @as(f64, f2.explained) * f2.like * (if (wide_now) plainness(&f2, shapes) else 1.0);
        if (wide_now and getenv("WZ_READDEBUG") != null) {
            say("  as lines of {s}: {d:.3} of the ink, likeness {d:.3}, {d} text(s):", .{ cf_label[fi], f2.explained, f2.like, f2.ntext });
            for (f2.texts[0..f2.ntext]) |*tq| say(" \"{s}\"", .{tq.str[0..tq.len]});
            say("\n", .{});
        }
        if (wide_now) {
            if (nwr < wread.len) {
                wread[nwr] = .{ .fig = f2, .val = val, .font = font };
                wread[nwr].fig.best_single = single;
                nwr += 1;
            }
        }
        if (val > best_val or (val == best_val and single > best_fig.best_single)) {
            best_val = val;
            best_font = font;
            best_fig = f2;
        }
    }
    if (wide_now and nwr > 1 and best_fig.ntext > 0) {
        // Fonts whose readings lie almost as well over the pieces (clones of one design, a font and the one it was
        // made from) are told apart by drawing: each one's texts drawn by werkkzeug's Text, in white on black at the
        // picture's size, laid over the figure's ink; the font whose drawing differs from the ink in the fewest pixels
        // is taken (the place and size are tuned around it later).
        // Fonts whose readings lie almost as well over the pieces (clones of one design, a font and the one it was made
        // from) are told apart by a closer look: every letter's piece against its glyph at 48 by 48, drawn from the font
        // (each aligned to its own box, so an error of a pixel in the read place or size does not count); of the sixteen
        // best readings the one whose letters lie closest is taken.
        var top: [16]usize = undefined;
        var nt: usize = 0;
        for (0..nwr) |i| {
            var at = nt;
            while (at > 0 and wread[top[at - 1]].val < wread[i].val) at -= 1;
            if (at >= top.len) continue;
            var j = @min(nt, top.len - 1);
            while (j > at) : (j -= 1) top[j] = top[j - 1];
            top[at] = i;
            if (nt < top.len) nt += 1;
        }
        // only readings that explain the ink as well (within 0.01) take part, and of those the ones with the fewest
        // texts (a line read whole is the plainer reading than the same line in pieces)
        var fewest: usize = std.math.maxInt(usize);
        for (top[0..nt]) |ti| {
            const wr = &wread[ti];
            if (wr.val >= best_val - 0.01 and wr.fig.ntext > 0) fewest = @min(fewest, wr.fig.ntext);
        }
        var bfine: f32 = -1;
        for (top[0..nt]) |ti| {
            const wr = &wread[ti];
            if (wr.val < best_val - 0.01 or wr.fig.ntext == 0 or wr.fig.ntext > fewest) continue;
            const fine = fineLikeness(&wr.fig, shapes);
            if (getenv("WZ_READDEBUG") != null) say("  closer look, {s}: {d:.4}\n", .{ cf_label[wr.font], fine });
            if (fine > bfine) {
                bfine = fine;
                best_font = wr.font;
                best_fig = wr.fig;
            }
        }
    }
    fig.font = best_font;
    fig.explained = best_fig.explained;
    fig.like = best_fig.like;
    fig.best_single = best_fig.best_single;
    fig.ntext = best_fig.ntext;
    fig.texts = best_fig.texts;
}

/// the share of a reading's letter ink that is in its main script (letters only: digits and signs count for every script)
fn plainness(fig: *const Figure, shapes: []const Shape) f64 {
    var ink = [_]f64{0} ** 14;
    for (fig.texts[0..fig.ntext]) |*tr| {
        for (tr.mshape[0..tr.nm], tr.mtpl[0..tr.nm]) |si, ti| ink[letterScript(templs.items[ti].ch)] += @floatFromInt(shapes[si].area);
    }
    var tot: f64 = 0;
    var top: f64 = 0;
    for (ink[1..]) |v| {
        tot += v;
        top = @max(top, v);
    }
    return if (tot > 0) top / tot else 1.0;
}

/// how well a reading's letters lie over their glyphs at 48 by 48, weighted by their ink
fn fineLikeness(fig: *const Figure, shapes: []const Shape) f32 {
    var sum: f64 = 0;
    var area: f64 = 0;
    for (fig.texts[0..fig.ntext]) |*tr| {
        for (tr.mshape[0..tr.nm], tr.mtpl[0..tr.nm]) |si, ti| {
            const sh = &shapes[si];
            const io = iou48(sh, &templs.items[ti]);
            sum += @as(f64, io) * @as(f64, @floatFromInt(sh.area));
            area += @floatFromInt(sh.area);
        }
    }
    return if (area > 0) @floatCast(sum / area) else 0;
}

fn iou48(sh: *const Shape, tp: *const Templ) f32 {
    var pm: [GL * GL]bool = undefined;
    const w = sh.x1 - sh.x0;
    const h = sh.y1 - sh.y0;
    for (0..GL) |gy| for (0..GL) |gx| {
        const ya = sh.y0 + gy * h / GL;
        const yb = @max(ya + 1, sh.y0 + (gy + 1) * h / GL);
        const xa = sh.x0 + gx * w / GL;
        const xb = @max(xa + 1, sh.x0 + (gx + 1) * w / GL);
        var cnt: usize = 0;
        var tot: usize = 0;
        for (ya..@min(yb, cur_n)) |y| for (xa..@min(xb, cur_n)) |x| {
            tot += 1;
            if (owns(sh, cur_labels[y * cur_n + x])) cnt += 1;
        };
        pm[gy * GL + gx] = tot > 0 and 2 * cnt >= tot;
    };
    var m: [GL * GL]u8 = undefined;
    var v: [6]f32 = undefined;
    var form: c_int = 0;
    if (wzb_glyph_mask2(cf_key[tp.font].ptr, tp.ch, GL, &m, &v, &form, null) != 0) return 0;
    var both: usize = 0;
    var either: usize = 0;
    for (0..GL * GL) |q| {
        const a2 = m[q] >= 128;
        if (a2 and pm[q]) both += 1;
        if (a2 or pm[q]) either += 1;
    }
    return if (either > 0) @as(f32, @floatFromInt(both)) / @as(f32, @floatFromInt(either)) else 0;
}

/// after twirls were taken out, the figure must be the glyph itself: a true Twirl run backwards gives the glyph
/// back (0.99 on .kkrieger's g), while the search can also bend a bar into a tilde or a hook into an e (0.75 to 0.77)
const UNTWIRL_T: f32 = 0.90;
const UNTWIRL_T_WIDE: f32 = 0.95;

fn figureIsText(fig: *const Figure) bool {
    if (fig.colour) return fig.ntext > 0 and fig.explained >= 0.85 and fig.like >= COLOUR_IOU_T;
    // over every font a bent stroke finds a glyph more easily (a twirled bar comes back as a tilde at 0.90): read over
    // the whole index, a figure with its twirls taken out must lie over its glyph by 0.95 (.kkrieger's g gives 0.99)
    const need: f32 = if (fig.nun > 0) (if (wide_now) UNTWIRL_T_WIDE else UNTWIRL_T) else glyph_t;
    return fig.two >= TWO_T and fig.ntext > 0 and fig.explained >= 0.85 and fig.like >= need;
}

// ---------------------------------------------------------------- colour glyphs: the reading by silhouette and colour
//
// A figure that is not two flat shades may be colour glyphs (COLR layers and paint graphs, SVG, colour bitmaps) on a
// flat ground. The ground is the commonest colour of the picture's border; the ink is what differs from it. Each piece's
// silhouette is laid over the silhouettes of every colour glyph of the index, as for letters; the closest are drawn in
// their own colours at 24 by 24 and compared with the piece's colours, so the glyph is found by its own layers' colours.
const COLOUR_IOU_T: f32 = 0.70;
const COLOUR_LIKE_T: f32 = 0.80;

fn readColourFigure(img: *const Image, fig: *Figure) void {
    if (!giLoad()) return;
    const n = img.w;
    if (img.h != n) return;
    // the ground: the commonest colour on the border, 32 levels per channel
    var counts = std.AutoHashMap(u32, u32).init(alloc);
    defer counts.deinit();
    for (0..n) |i| {
        for ([_][2]usize{ .{ i, 0 }, .{ i, n - 1 }, .{ 0, i }, .{ n - 1, i } }) |xy| {
            const o = (xy[1] * n + xy[0]) * 3;
            var key: u32 = 0;
            for (0..3) |c| key = key * 32 + @as(u32, @intFromFloat(@min(31.0, img.rgb[o + c] * 31.0 + 0.5)));
            const g = counts.getOrPut(key) catch die("out of memory", .{});
            if (!g.found_existing) g.value_ptr.* = 0;
            g.value_ptr.* += 1;
        }
    }
    var gk: u32 = 0;
    var gn: u32 = 0;
    var cit = counts.iterator();
    while (cit.next()) |e| if (e.value_ptr.* > gn) {
        gn = e.value_ptr.*;
        gk = e.key_ptr.*;
    };
    const gc = [3]f32{ @as(f32, @floatFromInt((gk >> 10) & 31)) / 31.0, @as(f32, @floatFromInt((gk >> 5) & 31)) / 31.0, @as(f32, @floatFromInt(gk & 31)) / 31.0 };
    const ink = alloc.alloc(bool, n * n) catch die("out of memory", .{});
    defer alloc.free(ink);
    var nink: usize = 0;
    for (0..n * n) |i| {
        var d: f32 = 0;
        for (0..3) |c| d = @max(d, @abs(img.rgb[i * 3 + c] - gc[c]));
        ink[i] = d > 0.12;
        if (ink[i]) nink += 1;
    }
    const share_ground = 1.0 - @as(f32, @floatFromInt(nink)) / @as(f32, @floatFromInt(n * n));
    if (share_ground < 0.5 or nink < 16) return;
    const labels = alloc.alloc(u32, n * n) catch die("out of memory", .{});
    defer alloc.free(labels);
    const shapes = alloc.alloc(Shape, MAXSHAPE * 2) catch die("out of memory", .{});
    defer alloc.free(shapes);
    const ns = pieces(ink, n, labels, shapes);
    if (ns == 0 or ns > 40) return;
    fig.colour = true;
    fig.two = share_ground;
    fig.ink = 1.0 - share_ground;
    fig.nshape = ns;
    fig.ground = 0xff000000 | rgbWord(gc);
    fig.ntext = 0;
    const Found = struct { font: u32, cp: u32, v: [6]f32, iou: f32, like: f32, sh: usize };
    var found: [40]Found = undefined;
    var nfound: usize = 0;
    var explained: usize = 0;
    var like_sum: f64 = 0;
    for (shapes[0..ns], 0..) |*sh, si| {
        if (sh.area < 12) continue;
        const d = descOf(labels, n, sh);
        // the piece's colours at 24 by 24: the mean of its ink in each cell
        var pc: [GS * GS][3]f32 = undefined;
        var pm: [GS * GS]bool = undefined;
        const w = sh.x1 - sh.x0;
        const h = sh.y1 - sh.y0;
        for (0..GS) |gy| for (0..GS) |gx| {
            const ya = sh.y0 + gy * h / GS;
            const yb = @max(ya + 1, sh.y0 + (gy + 1) * h / GS);
            const xa = sh.x0 + gx * w / GS;
            const xb = @max(xa + 1, sh.x0 + (gx + 1) * w / GS);
            var sum = [3]f32{ 0, 0, 0 };
            var cnt: usize = 0;
            var tot: usize = 0;
            for (ya..@min(yb, n)) |y| for (xa..@min(xb, n)) |x| {
                tot += 1;
                if (labels[y * n + x] == sh.ids[0]) {
                    cnt += 1;
                    for (0..3) |c| sum[c] += img.rgb[(y * n + x) * 3 + c];
                }
            };
            pm[gy * GS + gx] = tot > 0 and 2 * cnt >= tot;
            for (0..3) |c| pc[gy * GS + gx][c] = if (cnt > 0) sum[c] / @as(f32, @floatFromInt(cnt)) else 0;
        };
        // the closest colour silhouettes
        const NTOP = 400; // many colour glyphs share one silhouette (every round face): the colours decide among them
        var top: [NTOP][2]u32 = undefined;
        var nt: usize = 0;
        for (gi, gi_la, 0..) |*e, la, i| {
            if (e.form < 2 or e.form > 5) continue;
            if (@abs(la - d.la) > 0.2) continue;
            const hh = ham(&e.bits, &d.bits);
            if (hh > 72) continue;
            var at = nt;
            while (at > 0 and top[at - 1][0] > hh) at -= 1;
            if (at >= NTOP) continue;
            var j = @min(nt, NTOP - 1);
            while (j > at) : (j -= 1) top[j] = top[j - 1];
            top[at] = .{ hh, @intCast(i) };
            if (nt < NTOP) nt += 1;
        }
        var best: ?Found = null;
        var best_v: f32 = -1;
        for (top[0..nt]) |tb| {
            const e = &gi[tb[1]];
            var m: [GS * GS]u8 = undefined;
            var rgba: [GS * GS * 4]u8 = undefined;
            var v: [6]f32 = undefined;
            var form: c_int = 0;
            if (wzb_glyph_mask2(fx_key.items[e.font].ptr, e.cp, GS, &m, &v, &form, &rgba) != 0) continue;
            var both: usize = 0;
            var either: usize = 0;
            var cd: f32 = 0;
            for (0..GS * GS) |q| {
                const a = m[q] >= 128;
                if (a and pm[q]) {
                    both += 1;
                    // the glyph's colour in the cell (premultiplied blue, green, red, alpha), against the piece's
                    const al: f32 = @max(1.0, @as(f32, @floatFromInt(rgba[q * 4 + 3])));
                    const gr = [3]f32{ @as(f32, @floatFromInt(rgba[q * 4 + 2])) / al, @as(f32, @floatFromInt(rgba[q * 4 + 1])) / al, @as(f32, @floatFromInt(rgba[q * 4])) / al };
                    for (0..3) |c| cd += @abs(gr[c] - pc[q][c]) / 3.0;
                }
                if (a or pm[q]) either += 1;
            }
            if (either == 0 or both == 0) continue;
            const io = @as(f32, @floatFromInt(both)) / @as(f32, @floatFromInt(either));
            const lk = 1.0 - cd / @as(f32, @floatFromInt(both));
            if (io * lk > best_v) {
                best_v = io * lk;
                best = .{ .font = e.font, .cp = e.cp, .v = v, .iou = io, .like = lk, .sh = si };
            }
        }
        if (best) |b| {
            if (b.iou >= COLOUR_IOU_T and b.like >= COLOUR_LIKE_T and nfound < found.len) {
                found[nfound] = b;
                nfound += 1;
                explained += sh.area;
                like_sum += @as(f64, b.iou) * @as(f64, @floatFromInt(sh.area));
            }
            say("  colour piece {d}: U+{X:0>4} of {s}: silhouette {d:.2}, colours {d:.2}\n", .{ si, b.cp, fx_label.items[b.font], b.iou, b.like });
        } else say("  colour piece {d}: no colour glyph lies close over it\n", .{si});
    }
    fig.explained = @as(f32, @floatFromInt(explained)) / @as(f32, @floatFromInt(@max(1, nink)));
    fig.like = if (explained > 0) @floatCast(like_sum / @as(f64, @floatFromInt(explained))) else 0;
    // the glyphs left to right; one text per run of one font at one size whose places follow by the font's advances
    std.mem.sort(Found, found[0..nfound], shapes, struct {
        fn lt(sh: []Shape, a: Found, b: Found) bool {
            return sh[a.sh].x0 < sh[b.sh].x0;
        }
    }.lt);
    wide_now = true;
    cf_n = 0;
    const fnn: f32 = @floatFromInt(n);
    var k: usize = 0;
    while (k < nfound and fig.ntext < MAXTEXT) {
        const f0 = found[k];
        const s0 = &shapes[f0.sh];
        const em = @as(f32, @floatFromInt(s0.y1 - s0.y0)) / f0.v[1];
        const top = @as(f32, @floatFromInt(s0.y0)) - f0.v[2] * em;
        var ci: usize = 0;
        while (ci < cf_n and !std.mem.eql(u8, cf_key[ci], fx_key.items[f0.font])) ci += 1;
        if (ci == cf_n and cf_n < MAXCF) {
            cf_key[ci] = fx_key.items[f0.font];
            cf_label[ci] = fx_label.items[f0.font];
            cf_v1[ci] = false;
            cf_v1name[ci] = "";
            var sp: f32 = 0;
            var av: f32 = 0;
            _ = wzb_font_spacing(cf_key[ci].ptr, &sp, &av);
            font_space[ci] = sp;
            font_avg[ci] = av;
            font_have[ci] = true;
            cf_n += 1;
        }
        var tr = TextRead{ .font = @intCast(ci) };
        const pen0 = @as(f32, @floatFromInt(s0.x0)) - f0.v[4] * em;
        tr.x = (pen0 - 4.0) / fnn;
        tr.y = (top - 4.0) / fnn;
        tr.size = em / fnn;
        var expect = pen0;
        while (k < nfound) {
            const fk = found[k];
            const sk = &shapes[fk.sh];
            const emk = @as(f32, @floatFromInt(sk.y1 - sk.y0)) / fk.v[1];
            const topk = @as(f32, @floatFromInt(sk.y0)) - fk.v[2] * emk;
            const pen = @as(f32, @floatFromInt(sk.x0)) - fk.v[4] * emk;
            const space = font_space[ci] * em;
            const gap = pen - expect;
            const nsp = if (space > 0) @round(gap / space) else 0;
            const tol = @max(2.0, 0.08 * em);
            if (tr.len > 0 and (fk.font != f0.font or @abs(emk - em) > 0.06 * em or @abs(topk - top) > tol or nsp < 0 or nsp > 8 or @abs(gap - nsp * space) > tol)) break;
            var q: usize = 0;
            while (tr.len > 0 and q < @as(usize, @intFromFloat(nsp))) : (q += 1) {
                tr.str[tr.len] = ' ';
                tr.len += 1;
            }
            var u8b: [4]u8 = undefined;
            const ul = std.unicode.utf8Encode(@intCast(fk.cp), &u8b) catch 0;
            if (tr.len + ul + 8 > tr.str.len) break;
            @memcpy(tr.str[tr.len .. tr.len + ul], u8b[0..ul]);
            tr.len += ul;
            expect = pen + fk.v[3] * emk;
            k += 1;
        }
        fig.texts[fig.ntext] = tr;
        fig.ntext += 1;
    }
}

/// how far a figure is a text: the share of its ink read as glyphs on lines times how well they lie over their
/// glyphs; while no line stands, the best one glyph does over one piece, kept below what a line gives
fn figureWorth(fig: *const Figure) f32 {
    if (fig.ntext > 0) return @max(fig.explained * fig.like, 0.6 * fig.best_single);
    return 0.6 * fig.best_single;
}

fn fontSaid(font: u16) []const u8 {
    return cf_label[font];
}

fn sayFigure(fig: *const Figure) void {
    if (fig.colour) {
        say("figure: colour glyphs on a flat ground: the ground is {d:.2} of the picture, the ink in {d} pieces; read as colour glyphs: {d:.2} of the ink, silhouettes {d:.2}, {d} text(s)\n", .{ fig.two, fig.nshape, fig.explained, fig.like, fig.ntext });
        for (fig.texts[0..fig.ntext]) |*tr| say("  text \"{s}\" of {s} at {d:.4}, {d:.4}, height {d:.4}\n", .{ tr.str[0..tr.len], cf_label[tr.font], tr.x, tr.y, tr.size });
        return;
    }
    say("figure: {d:.2} of the picture lies in two flat shades, the ink is {d:.3} of it in {d} pieces, {d} with form enough for a glyph; ", .{ fig.two, fig.ink, fig.nshape, fig.nrich });
    if (fig.two < TWO_T) {
        say("no figure on a ground\n", .{});
        return;
    }
    if (fig.nshape > MAXSHAPE) {
        say("more than {d} pieces of ink: not read as glyphs\n", .{MAXSHAPE});
        return;
    }
    say("each piece over its best glyph {d:.2}; as lines of {s}: {d:.2} of the ink, likeness {d:.2}, {d} text(s)\n", .{ fig.best_single, fontSaid(fig.font), fig.explained, fig.like, fig.ntext });
    for (fig.un[0..fig.nun]) |u| say("  a twirl taken out first: strength {d:.3}, gamma {d:.0}, radius {d:.3}, centre {d:.3}, {d:.3}\n", .{ -u[0], u[1], u[2], u[3], u[4] });
    for (fig.texts[0..fig.ntext]) |*tr| {
        var shown: [220]u8 = undefined;
        var l: usize = 0;
        for (tr.str[0..tr.len]) |ch| {
            shown[l] = if ((ch >= 32 and ch < 127) or (wide_now and ch >= 128)) ch else '?';
            l += 1;
        }
        say("  text \"{s}\" at {d:.4}, {d:.4}, height {d:.4}, width {d:.4}\n", .{ shown[0..l], tr.x, tr.y, tr.size, tr.wide });
    }
}

extern "c" fn wzb_from_rgba(xs: c_int, ys: c_int, rgba: [*]const u8) ?*anyopaque;

/// one Twirl of werkkzeug's own code run on a grey picture (n by n, 0..1)
fn twirlPicture(src: ?*anyopaque, n: usize, u: [5]f32, out: []f32, rgba: []u8) bool {
    var w: [32]u32 = [_]u32{0} ** 32;
    w[0] = wordOf(u[0]);
    w[1] = wordOf(u[1]);
    w[2] = wordOf(u[2]);
    w[3] = wordOf(u[2]);
    w[4] = wordOf(u[3]);
    w[5] = wordOf(u[4]);
    var inp = [1]?*anyopaque{src};
    var res: ?*anyopaque = null;
    var err: [200]u8 = undefined;
    if (wzb_apply("Twirl", &w, 1, &inp, &res, &err, 200) != 0) return false;
    wzb_rgba(res, rgba.ptr);
    wzb_free(res);
    for (0..n * n) |i| out[i] = @as(f32, @floatFromInt(rgba[4 * i])) / 255.0;
    return true;
}

fn greyBitmap(t: []const f32, n: usize, rgba: []u8) ?*anyopaque {
    for (0..n * n) |i| {
        const b: u8 = @intFromFloat(@min(255.0, @max(0.0, t[i] * 255.0 + 0.5)));
        rgba[4 * i] = b;
        rgba[4 * i + 1] = b;
        rgba[4 * i + 2] = b;
        rgba[4 * i + 3] = 255;
    }
    return wzb_from_rgba(@intCast(n), @intCast(n), rgba.ptr);
}

/// A figure that is no glyph, in a picture where the ring reading found a swirl: the Twirl run backwards.
/// Each candidate twirl (centres on eighths of the side, three radii, three gammas, strengths in eighths of a
/// turn: the fitter's own grid) is taken out of the picture with werkkzeug's own Twirl at minus its strength,
/// and the figure is read again; the one after which the pieces lie best over a glyph is kept, up to three.
/// What steers it is the glyph reading, not the inner measure.
fn untwirl(t_full: []const f32, n_full: usize, fig: *Figure) void {
    const m: usize = 128;
    const small = shrink(t_full, n_full, m);
    defer alloc.free(small);
    const cur = alloc.alloc(f32, m * m) catch die("out of memory", .{});
    defer alloc.free(cur);
    const trial = alloc.alloc(f32, m * m) catch die("out of memory", .{});
    defer alloc.free(trial);
    const rgba = alloc.alloc(u8, n_full * n_full * 4) catch die("out of memory", .{});
    defer alloc.free(rgba);
    @memcpy(cur, small);
    wide_off = true;
    defer wide_off = false;
    var f0 = Figure{};
    readFigure(cur, m, &f0);
    var have: f32 = figureWorth(&f0);
    fig.nun = 0;
    const radii = [_]f32{ 0.25, 0.5, 0.75 };
    const gammas = [_]f32{ 2, 16, 48 };
    while (fig.nun < 3) {
        const src = greyBitmap(cur, m, rgba);
        defer wzb_free(src);
        var best: [5]f32 = undefined;
        var best_v: f32 = have;
        for (1..8) |cy| {
            for (1..8) |cx| {
                for (radii) |rad| {
                    for (gammas) |ga| {
                        var si: i32 = -6;
                        while (si <= 6) : (si += 1) {
                            if (si == 0) continue;
                            const u = [5]f32{ @as(f32, @floatFromInt(si)) * 0.25, ga, rad, @as(f32, @floatFromInt(cx)) / 8.0, @as(f32, @floatFromInt(cy)) / 8.0 };
                            if (!twirlPicture(src, m, u, trial, rgba)) continue;
                            var f2 = Figure{};
                            readFigure(trial, m, &f2);
                            const v2 = figureWorth(&f2);
                            if (v2 > best_v + 0.0001) {
                                best_v = v2;
                                best = u;
                            }
                        }
                    }
                }
            }
        }
        if (best_v < have + 0.03) break;
        // the strength once more, in eighths, around the best quarter
        for ([_]f32{ -0.125, 0.125 }) |d| {
            var u = best;
            u[0] += d;
            if (u[0] == 0 or !twirlPicture(src, m, u, trial, rgba)) continue;
            var f2 = Figure{};
            readFigure(trial, m, &f2);
            const v2 = figureWorth(&f2);
            if (v2 > best_v + 0.0001) {
                best_v = v2;
                best = u;
            }
        }
        _ = twirlPicture(src, m, best, trial, rgba);
        @memcpy(cur, trial);
        have = best_v;
        fig.un[fig.nun] = best;
        fig.nun += 1;
        say("  twirl backwards {d}: strength {d:.3}, gamma {d:.0}, radius {d:.2}, centre {d:.3}, {d:.3}: the figure's worth as text now {d:.2}\n", .{ fig.nun, best[0], best[1], best[2], best[3], best[4], have });
    }
    if (fig.nun == 0) return;
    // the same twirls taken out of the picture at its own size, and the figure read there
    const a = alloc.alloc(f32, n_full * n_full) catch die("out of memory", .{});
    defer alloc.free(a);
    const b = alloc.alloc(f32, n_full * n_full) catch die("out of memory", .{});
    defer alloc.free(b);
    @memcpy(a, t_full);
    for (fig.un[0..fig.nun]) |u| {
        const src = greyBitmap(a, n_full, rgba);
        defer wzb_free(src);
        if (!twirlPicture(src, n_full, u, b, rgba)) return;
        @memcpy(a, b);
    }
    const keep_n = fig.nun;
    const keep_u = fig.un;
    wide_off = false;
    readFigure(a, n_full, fig);
    fig.nun = keep_n;
    fig.un = keep_u;
}

fn textNode(tr: *const TextRead, col: u32) Node {
    if (wide_now) return textNode2(tr, col);
    var nd = Node{ .op = OP_TEXT, .nw = 9, .keep = true };
    nd.w[0] = wordOf(tr.x);
    nd.w[1] = wordOf(tr.y);
    nd.w[2] = wordOf(tr.size);
    nd.w[3] = wordOf(tr.wide);
    nd.w[4] = col;
    nd.w[5] = 0;
    nd.w[6] = 2;
    nd.w[7] = wordOf(0.0);
    nd.w[8] = wordOf(1.0);
    nd.s[0] = intern(tr.str[0..tr.len]);
    nd.s[1] = intern(font_names[tr.font]);
    return nd;
}

/// a few values tried around what was read, each by steps that halve: the place and size of a text
fn nudge(g: *Graph, t: *Target, items: []const [2]usize, steps: []const f32, rounds: usize) f32 {
    var best = score(g, t);
    var scale: f32 = 1;
    for (0..rounds) |_| {
        var improved = false;
        for (items, steps) |it, st| {
            const old = g.nodes[it[0]].w[it[1]];
            for ([_]f32{ st * scale, -st * scale }) |d| {
                g.nodes[it[0]].w[it[1]] = wordOf(f32of(old) + d);
                const s = score(g, t);
                if (s < best - 1e-6) {
                    best = s;
                    improved = true;
                    break;
                }
                g.nodes[it[0]].w[it[1]] = old;
            }
        }
        if (!improved) scale *= 0.5;
    }
    return best;
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

// ---------------------------------------------------------------- milestone 2: tiles, and glyphs as seeds
//
// A tile is fitted from its own pixels. The whole picture's repeat (its cell, where the cell starts, its shapes, and a
// seed: a glyph that lies over the cell's motif) is read once on the whole picture and drawn in every tile at its own
// place, so the joints and the motifs of neighbouring tiles meet at their borders (the seams).

/// One axis of the whole picture's repeat as a tile sees it: the cell repeats f times across the tile, and the cell
/// coordinate of a point u of the tile is u * f - o. Periodic when one cell or more lies across the tile: one cell is
/// drawn in a picture of its own and Transform repeats it. Direct when less than one does: the tile itself is the
/// picture, and every instance that reaches the tile is drawn at its own place, so nothing is magnified.
const Axis = struct { f: f32 = 1, o: f32 = 0, direct: bool = false };

fn axisOf(n: f32, o: f32, w0: f32, ws: f32) Axis {
    const f = ws * n;
    return .{ .f = f, .o = o - w0 * n, .direct = f < 0.999 };
}

/// A shape of the cell: its centre and half sizes, in cells.
const CellItem = struct { cx: f32 = 0.5, cy: f32 = 0.5, hw: f32 = 0.25, hh: f32 = 0.25, seed: ?*const Seed = null };

/// A seed: a glyph of a font that lies over the motif of the cell, called by its key and its character.
pub const Seed = struct {
    have: bool = false,
    key: [:0]const u8 = "",
    label: []const u8 = "",
    cp: u32 = 0,
    // the glyph's ink in em squares: width over height, height, top below the line's top, advance, left edge after the
    // pen, and the font's average character width
    gv: [6]f32 = .{ 1, 1, 0, 1, 0, 0.5 },
    box: CellItem = .{},
    nx: f32 = 1,
    ny: f32 = 1,
    ox: f32 = 0,
    oy: f32 = 0,
    bonded: bool = false,
    bond_shift: f32 = 0,
    ink: u32 = 0xffffffff,
    ground: u32 = 0xff000000,
    like: f32 = 0,
    box_like: f32 = 0,
    drawing: bool = false,
    bytes: usize = 0,
};
/// the seeds of a seed file: one glyph over the whole motif, or one per piece of it (a flower and its leaves); they
/// share the whole picture's repeat
const MAXSEED = 12;
pub var seeds: [MAXSEED]Seed = undefined;
pub var nseeds: usize = 0;

/// The window of the whole picture a tile is: its left, its top and its side, in shares of the whole picture.
pub const Win = struct { x: f32 = 0, y: f32 = 0, s: f32 = 1 };

/// The tile's reading takes the repeat from the whole picture's: what repeats is a property of the whole surface, and a
/// tile holds too few repeats to read it (a 512 pixel tile of a 2048 pixel brick wall holds one and a half bricks).
fn mapWhole(rd: *Reading, rw: *const Reading, w: Win) void {
    rd.nx = rw.nx;
    rd.ny = rw.ny;
    rd.ox = rw.ox;
    rd.oy = rw.oy;
    rd.nrect = rw.nrect;
    rd.rect = rw.rect;
    rd.bonded = rw.bonded;
    rd.bond_shift = rw.bond_shift;
    rd.bond = rw.bond;
    rd.rows = rw.rows;
    rd.bricks = rw.bricks;
    rd.row0 = rw.row0;
    rd.jw = rw.jw;
    rd.jmul = rw.jmul;
    rd.dark = rw.dark;
    rd.share = rw.share;
    rd.win = true;
    rd.ax = axisOf(@floatFromInt(rw.nx), rw.ox, w.x, w.s);
    rd.ay = axisOf(@floatFromInt(rw.ny), rw.oy, w.y, w.s);
    say("the tile's window: {d:.4}, {d:.4}, side {d:.4} of the whole; the whole repeats {d} by {d} ({d} shape(s){s}), so {d:.3} by {d:.3} cells lie across the tile ({s} across, {s} down)\n", .{ w.x, w.y, w.s, rw.nx, rw.ny, rw.nrect, if (rw.bonded) ", in a bond" else "", rd.ax.f, rd.ay.f, if (rd.ax.direct) "each drawn at its place" else "repeated", if (rd.ay.direct) "each drawn at its place" else "repeated" });
}

/// The edge of a drawn shape: two pixels of the tile, in the units of the picture the shape is drawn in
fn edgeOf(a: Axis, side: f32) f32 {
    return if (a.direct) 2.0 / side else 2.0 * a.f / side;
}

/// The instances of a cell coordinate c (half size h, cells) along an axis, in the units of the picture they are drawn
/// in: one at c on a periodic axis; on a direct axis every one that reaches the tile, at (c + o + k) / f.
fn instances(a: Axis, c: f32, h: f32, out: *[8][2]f32) usize {
    if (!a.direct) {
        out[0] = .{ c, h };
        return 1;
    }
    var nout: usize = 0;
    const reach = 0.5 + h / a.f + 0.002;
    var k: f32 = @floor(-(c + a.o) - 1.0);
    const k_end = @ceil(a.f - (c + a.o) + 1.0);
    while (k <= k_end and nout < out.len) : (k += 1) {
        const u = (c + a.o + k) / a.f;
        if (@abs(u - 0.5) <= reach) {
            out[nout] = .{ u, h / a.f };
            nout += 1;
        }
    }
    return nout;
}

/// A seed's glyph drawn white into the box (centre and half sizes, in the units of a picture of side pixels); the
/// glyph's own ink is stretched to the box, so a picture whose two axes have other scales gets the glyph right
/// once Transform has repeated it. Always Text version 2 (the font's key), in its outline form.
pub fn seedText(sd: *const Seed, cx: f32, cy: f32, hw: f32, hh: f32, side: f32) Node {
    const bw = 2.0 * hw * side;
    const bh = 2.0 * hh * side;
    const em = bh / @max(sd.gv[1], 1e-4);
    var sx = (bw / @max(bh, 1e-4)) / @max(sd.gv[0], 1e-4);
    if (@abs(sx - 1.0) < 0.01) sx = 1.0;
    const pen0 = (cx - hw) * side - sd.gv[4] * em * sx;
    const top = (cy - hh) * side - sd.gv[2] * em;
    var nd = Node{ .op = OP_TEXT, .nw = TEXT2_WORDS, .lock = true, .keep = true };
    // the text starts (space + 2) pixels right and down of its x and y; the space around letters is 0 here
    nd.w[0] = wordOf((pen0 - 2.0) / side);
    nd.w[1] = wordOf((top - 2.0) / side);
    nd.w[2] = wordOf(em / side);
    nd.w[3] = wordOf(if (sx == 1.0) 0.0 else sx * sd.gv[5] * em / side);
    nd.w[4] = 0xffffffff;
    nd.w[5] = 0;
    nd.w[6] = 0;
    nd.w[7] = wordOf(0.0);
    nd.w[8] = wordOf(1.0);
    nd.w[9] = 2;
    nd.w[10] = 0;
    nd.w[11] = 1; // the outline form: the seed is a shape, white on black
    var b: [8]u8 = undefined;
    const l = std.unicode.utf8Encode(@intCast(sd.cp), &b) catch die("character U+{X} cannot be written as UTF-8", .{sd.cp});
    nd.s[0] = intern(b[0..l]);
    nd.s[1] = intern(sd.key);
    nd.s[2] = 0;
    return nd;
}

/// The cell's shapes (GlowRects, or the seed's glyph) white on black in the tile's own frame: drawn once in a cell
/// picture and repeated by Transform on periodic axes, drawn at each instance's place on direct ones. Rows in a bond
/// make a cell one brick wide and two rows tall, the second row moved sideways by TransformMul. Returns the last
/// operator: the shape picture, marked as the relief's height.
fn appendCellShapes(g: *Graph, ax_in: Axis, ay_in: Axis, items: []const CellItem, bonded_in: bool, bshift: f32, side: f32) usize {
    var bonded = bonded_in;
    var ay = ay_in;
    const ax = ax_in;
    if (bonded and (ax.direct or ay.f < 2.0)) {
        say("the bond is not drawn in this tile: {d:.2} bricks and {d:.2} rows lie across it, and the bond's two-row cell needs a brick and two rows; the rows are drawn without it\n", .{ ax.f, ay.f });
        bonded = false;
    }
    if (bonded) ay = .{ .f = ay.f / 2.0, .o = ay.o / 2.0, .direct = false };
    var fl = flatNode(0xff000000);
    fl.lock = true;
    fl.keep = true;
    _ = append(g, fl);
    const ex = edgeOf(ax, side);
    const ey = edgeOf(ay, side);
    for (items) |it| {
        const cy = if (bonded) it.cy / 2.0 else it.cy;
        const hh = if (bonded) it.hh / 2.0 else it.hh;
        var xs: [8][2]f32 = undefined;
        var ys: [8][2]f32 = undefined;
        const nxs = instances(ax, it.cx, it.hw, &xs);
        const nys = instances(ay, cy, hh, &ys);
        for (ys[0..nys]) |yi| {
            for (xs[0..nxs]) |xi| {
                var nd: Node = undefined;
                if (it.seed) |s| {
                    nd = seedText(s, xi[0], yi[0], xi[1], yi[1], side);
                } else {
                    nd = Node{ .op = OP_GLOWRECT, .nin = 1, .nw = 11, .lock = true, .keep = true };
                    nd.w[0] = wordOf(xi[0]);
                    nd.w[1] = wordOf(yi[0]);
                    nd.w[2] = wordOf(ex);
                    nd.w[3] = wordOf(ey);
                    nd.w[4] = wordOf(@max(0.002, xi[1] - ex));
                    nd.w[5] = wordOf(@max(0.002, yi[1] - ey));
                    nd.w[6] = 0xffffffff;
                    nd.w[7] = wordOf(1.0);
                    nd.w[8] = wordOf(0.5);
                    nd.w[9] = if (ax.direct or ay.direct) 0 else 1; // wrapped round the cell only where the cell repeats
                    nd.w[10] = 0;
                }
                nd.nin = 1;
                nd.in[0] = @intCast(g.n - 1);
                _ = append(g, nd);
            }
        }
    }
    if (bonded) {
        // RotateMul, mode 16, count 1: the picture merged with itself carried by minus (t - 0.5): the second row,
        // half the cell down and the bond's part of a brick sideways
        var mul = Node{ .op = OP_TRANSFORMMUL, .nin = 1, .nw = 10, .lock = true, .keep = true };
        mul.in[0] = @intCast(g.n - 1);
        mul.w[0] = wordOf(0.0);
        mul.w[1] = wordOf(1.0);
        mul.w[2] = wordOf(1.0);
        mul.w[3] = wordOf(0.5 - bshift);
        mul.w[4] = wordOf(0.0);
        mul.w[5] = 0;
        mul.w[6] = 0xffffffff;
        mul.w[7] = 16;
        mul.w[8] = 1;
        mul.w[9] = 0xffffffff;
        _ = append(g, mul);
    }
    if (!ax.direct or !ay.direct) {
        // Transform: a point u of the tile reads the cell picture at (u - 0.5) / s + t, so s = 1 / f and
        // t = 0.5 f - o give u f - o; on a direct axis s = 1 and t = 0.5 leave the picture as it is
        var tr = Node{ .op = OP_TRANSFORM, .nin = 1, .nw = 8, .lock = true, .keep = true };
        tr.in[0] = @intCast(g.n - 1);
        tr.w[0] = wordOf(0.0);
        tr.w[1] = wordOf(if (ax.direct) 1.0 else 1.0 / ax.f);
        tr.w[2] = wordOf(if (ay.direct) 1.0 else 1.0 / ay.f);
        tr.w[3] = wordOf(if (ax.direct) 0.5 else @mod(0.5 * ax.f - ax.o, 1.0));
        tr.w[4] = wordOf(if (ay.direct) 0.5 else @mod(0.5 * ay.f - ay.o, 1.0));
        tr.w[5] = 0;
        _ = append(g, tr);
    }
    g.nodes[g.n - 1].shape = true;
    return g.n - 1;
}

/// The repeated shape of a tile, its joints by the outline trick (milestone 1c), with the whole picture's repeat
/// drawn at the tile's place.
fn appendOutlineWin(g: *Graph, r: *const Reading, colour: usize, opt: Options, side: f32) Outline {
    const first = g.n;
    var items: [3]CellItem = undefined;
    for (0..r.nrect) |i| items[i] = .{ .cx = r.rect[i][0], .cy = r.rect[i][1], .hw = r.rect[i][2], .hh = r.rect[i][3] };
    // the existing build draws one shape per cell (the first); so does this one
    const shape = appendCellShapes(g, r.ax, r.ay, items[0..@min(r.nrect, 1)], r.bonded, r.bond_shift, side);
    g.nodes[shape].shape = false;
    var bl = Node{ .op = OP_BLUR, .nin = 1, .nw = 4, .lock = true, .shape = true, .keep = true };
    bl.in[0] = @intCast(shape);
    bl.w[0] = 1;
    bl.w[1] = wordOf(@max(0.001, opt.jointw * r.jw[0] / r.ax.f));
    bl.w[2] = wordOf(@max(0.001, opt.jointw * r.jw[1] / r.ay.f));
    bl.w[3] = wordOf(1.0);
    const blurred = append(g, bl);
    var sub = Node{ .op = OP_MERGE, .nin = 2, .nw = 1, .lock = true };
    sub.in[0] = @intCast(blurred);
    sub.in[1] = @intCast(shape);
    sub.w[0] = 1;
    const subi = append(g, sub);
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

/// The seed over the surface: its glyph, white on black, at every instance of the motif, is the mask through which
/// the motif's own colour lies over the surface (Mask: the first layer where the mask is white).
fn appendSeed(g: *Graph, sds: []const Seed, w: Win, colour: usize, side: f32) usize {
    const first = g.n;
    const sd = &sds[0];
    const ax = axisOf(sd.nx, sd.ox, w.x, w.s);
    const ay = axisOf(sd.ny, sd.oy, w.y, w.s);
    var items: [MAXSEED]CellItem = undefined;
    for (sds, 0..) |*x, i| {
        say("the seed: U+{X:0>4} of {s}, over {d:.3} by {d:.3} cells of the tile ({s} across, {s} down)\n", .{ x.cp, x.label, ax.f, ay.f, if (ax.direct) "each drawn at its place" else "repeated", if (ay.direct) "each drawn at its place" else "repeated" });
        items[i] = x.box;
        // a seed with no character is the box GlowRect draws: the motif is a box, and the box costs the fewest bytes
        items[i].seed = if (x.cp == 0) null else x;
    }
    const shape = appendCellShapes(g, ax, ay, items[0..sds.len], sd.bonded, sd.bond_shift, side);
    var ink = flatNode(sd.ink);
    ink.lock = true;
    ink.keep = true;
    const inki = append(g, ink);
    var ms = Node{ .op = OP_MASK, .nin = 3, .nw = 1, .lock = true, .keep = true };
    ms.in[0] = @intCast(shape);
    ms.in[1] = @intCast(inki);
    ms.in[2] = @intCast(colour);
    ms.w[0] = 0;
    const root = append(g, ms);
    for (g.nodes[first..g.n]) |*x| x.keep = true;
    return root;
}

fn parseF(tok: ?[]const u8) f32 {
    return std.fmt.parseFloat(f32, tok orelse die("the seed file is cut short", .{})) catch die("the seed file holds a number that is none", .{});
}

/// The seed file `p2p seed` writes: one name and its values per line; `cand` lines are the record of the search.
pub fn loadSeed(path: [*:0]const u8) void {
    const text = readFile(path);
    var lines = std.mem.splitScalar(u8, text, '\n');
    while (lines.next()) |line| {
        var it = std.mem.tokenizeScalar(u8, line, ' ');
        const k = it.next() orelse continue;
        if (std.mem.eql(u8, k, "seed")) {
            if (std.mem.eql(u8, it.next() orelse "0", "1")) {
                if (nseeds >= MAXSEED) die("the seed file holds more than {d} seeds", .{MAXSEED});
                seeds[nseeds] = .{ .have = true };
                nseeds += 1;
            }
            continue;
        }
        if (nseeds == 0) continue;
        const the_seed = &seeds[nseeds - 1];
        if (false) {
        } else if (std.mem.eql(u8, k, "key")) {
            const rest = std.mem.trim(u8, line[3..], " ");
            the_seed.key = alloc.dupeZ(u8, rest) catch die("out of memory", .{});
        } else if (std.mem.eql(u8, k, "label")) {
            the_seed.label = alloc.dupe(u8, std.mem.trim(u8, line[5..], " ")) catch die("out of memory", .{});
        } else if (std.mem.eql(u8, k, "cp")) {
            the_seed.cp = std.fmt.parseInt(u32, it.next() orelse "0", 16) catch die("the seed's character is not a number", .{});
        } else if (std.mem.eql(u8, k, "gv")) {
            for (0..6) |i| the_seed.gv[i] = parseF(it.next());
        } else if (std.mem.eql(u8, k, "box")) {
            the_seed.box = .{ .cx = parseF(it.next()), .cy = parseF(it.next()), .hw = parseF(it.next()), .hh = parseF(it.next()) };
        } else if (std.mem.eql(u8, k, "repeat")) {
            the_seed.nx = parseF(it.next());
            the_seed.ny = parseF(it.next());
            the_seed.ox = parseF(it.next());
            the_seed.oy = parseF(it.next());
            the_seed.bonded = parseF(it.next()) > 0.5;
            the_seed.bond_shift = parseF(it.next());
        } else if (std.mem.eql(u8, k, "colour")) {
            the_seed.ink = std.fmt.parseInt(u32, it.next() orelse "0", 16) catch die("the seed's colour is not a number", .{});
            the_seed.ground = std.fmt.parseInt(u32, it.next() orelse "0", 16) catch die("the seed's colour is not a number", .{});
        } else if (std.mem.eql(u8, k, "like")) {
            the_seed.like = parseF(it.next());
            the_seed.box_like = parseF(it.next());
        }
    }
    for (seeds[0..nseeds]) |x| {
        if (x.key.len == 0) die("the seed file says seed 1 and names no font", .{});
    }
}

extern "c" fn uc_drawing(cp: u32) c_int;

/// The motif's picture as 16 by 16 bits and as GS by GS, each stretched to the ink's own box
const Sil = struct { bits: [4]u64, la: f32, m: [GS * GS]bool, x0: usize, y0: usize, x1: usize, y1: usize, area: usize };

fn silOf(mask: []const bool, w: usize, x0: usize, y0: usize, x1: usize, y1: usize) Sil {
    var s = Sil{ .bits = .{ 0, 0, 0, 0 }, .la = 0, .m = undefined, .x0 = x0, .y0 = y0, .x1 = x1, .y1 = y1, .area = 0 };
    const bw = x1 - x0;
    const bh = y1 - y0;
    for (y0..y1) |y| {
        for (x0..x1) |x| {
            if (mask[y * w + x]) s.area += 1;
        }
    }
    inline for (.{ 16, GS }) |side| {
        for (0..side) |gy| {
            const ya = y0 + gy * bh / side;
            const yb = @max(ya + 1, y0 + (gy + 1) * bh / side);
            for (0..side) |gx| {
                const xa = x0 + gx * bw / side;
                const xb = @max(xa + 1, x0 + (gx + 1) * bw / side);
                var cnt: usize = 0;
                var tot: usize = 0;
                for (ya..@min(yb, y1)) |y| {
                    for (xa..@min(xb, x1)) |x| {
                        tot += 1;
                        if (mask[y * w + x]) cnt += 1;
                    }
                }
                const on = tot > 0 and 2 * cnt >= tot;
                if (side == 16) {
                    if (on) {
                        const i = gy * 16 + gx;
                        s.bits[i >> 6] |= @as(u64, 1) << @intCast(i & 63);
                    }
                } else s.m[gy * GS + gx] = on;
            }
        }
    }
    s.la = @log(@as(f32, @floatFromInt(bw)) / @as(f32, @floatFromInt(@max(1, bh))));
    return s;
}

/// how well a glyph must lie over a motif to be offered as a seed (the eye then decides). The likeness is the soft one
/// below: a drawing of thin strokes (a snowflake) and its look-alikes lie over each other badly pixel for pixel, while
/// the eye takes them for the same thing; blurring both first lets strokes that run close count.
const SEED_T: f32 = 0.70;

/// 16 by 16 bits as one number, bit gy * 16 + gx; grown by one cell in the four directions
fn bits256(b: *const [4]u64) u256 {
    return @as(u256, b[0]) | (@as(u256, b[1]) << 64) | (@as(u256, b[2]) << 128) | (@as(u256, b[3]) << 192);
}
fn grow256(x: u256) u256 {
    var col0: u256 = 0;
    var col15: u256 = 0;
    for (0..16) |r| {
        col0 |= @as(u256, 1) << @intCast(16 * r);
        col15 |= @as(u256, 1) << @intCast(16 * r + 15);
    }
    return x | ((x << 1) & ~col0) | ((x >> 1) & ~col15) | (x << 16) | (x >> 16);
}
fn iou256(a: u256, b: u256) f32 {
    const u: u32 = @popCount(a | b);
    return if (u == 0) 0 else @as(f32, @floatFromInt(@as(u32, @popCount(a & b)))) / @as(f32, @floatFromInt(u));
}
/// a GS by GS picture blurred by a box of five cells, twice (close to a Gaussian of 1.6 cells)
fn softOf(m: *const [GS * GS]bool) [GS * GS]f32 {
    var a: [GS * GS]f32 = undefined;
    for (m, 0..) |v, i| a[i] = if (v) 1 else 0;
    var b: [GS * GS]f32 = undefined;
    for (0..2) |_| {
        for (0..GS) |y| {
            for (0..GS) |x| {
                var s: f32 = 0;
                var k: i32 = -2;
                while (k <= 2) : (k += 1) {
                    const xx = @as(i32, @intCast(x)) + k;
                    if (xx >= 0 and xx < GS) s += a[y * GS + @as(usize, @intCast(xx))];
                }
                b[y * GS + x] = s / 5.0;
            }
        }
        for (0..GS) |y| {
            for (0..GS) |x| {
                var s: f32 = 0;
                var k: i32 = -2;
                while (k <= 2) : (k += 1) {
                    const yy = @as(i32, @intCast(y)) + k;
                    if (yy >= 0 and yy < GS) s += b[@as(usize, @intCast(yy)) * GS + x];
                }
                a[y * GS + x] = s / 5.0;
            }
        }
    }
    return a;
}
fn softLike(a: *const [GS * GS]f32, b: *const [GS * GS]f32) f32 {
    var mn: f32 = 0;
    var mx: f32 = 0;
    for (a, b) |x, y| {
        mn += @min(x, y);
        mx += @max(x, y);
    }
    return if (mx <= 0) 0 else mn / mx;
}

const SeedCand = struct { gi: u32, like: f32, score: f32, drawing: bool, bytes: usize, v: [6]f32 };

/// p2p seed WHOLE.ppm OUT.seed: the whole picture's repeat, the mean cell's motif (the minority of its two shades),
/// and the glyph of every font of the index that lies over it best, the pure drawings and the fewest bytes preferred.
fn seedRead(path: [*:0]const u8, out_path: []const u8) void {
    const img = readPpm(path);
    var full: u32 = 0;
    while ((@as(usize, 1) << @intCast(full)) < img.w) full += 1;
    var t = makeTarget(img, full);
    const rd = readPicture(&t);
    var rec: std.ArrayList(u8) = .empty;
    var line: [600]u8 = undefined;
    const W = struct {
        fn put(r: *std.ArrayList(u8), buf: []u8, comptime fmt: []const u8, args: anytype) void {
            const l = std.fmt.bufPrint(buf, fmt, args) catch die("seed record line too long", .{});
            r.appendSlice(alloc, l) catch die("out of memory", .{});
        }
    };
    if (rd.cw == 0 or rd.nx * rd.ny < 2) {
        say("no seed: the picture does not repeat, so it has no cell and no motif to lay a glyph over\n", .{});
        W.put(&rec, &line, "seed 0\nwhy the picture does not repeat\n", .{});
        writeFile(out_path, rec.items);
        return;
    }
    if (!giLoad()) die("the seed reading needs the glyph index: set WZ_GLYPHINDEX and WZ_FONTINDEX", .{});
    const cw = rd.cw;
    const ch = rd.ch;
    const cell = rd.cell;
    // two shades by Otsu's threshold over the cell (between-class variance over total); the ink is the smaller shade
    var lo: f32 = 1e9;
    var hi: f32 = -1e9;
    for (cell) |c| {
        lo = @min(lo, c);
        hi = @max(hi, c);
    }
    var hist = [_]f64{0} ** 64;
    const span = @max(hi - lo, 1e-6);
    for (cell) |c| hist[@min(63, @as(usize, @intFromFloat((c - lo) / span * 64.0)))] += 1;
    const total: f64 = @floatFromInt(cw * ch);
    var mu: f64 = 0;
    for (hist, 0..) |hcount, b| mu += hcount * @as(f64, @floatFromInt(b));
    mu /= total;
    var vt: f64 = 0;
    for (hist, 0..) |hcount, b| vt += hcount * (@as(f64, @floatFromInt(b)) - mu) * (@as(f64, @floatFromInt(b)) - mu);
    vt /= total;
    var w0: f64 = 0;
    var m0: f64 = 0;
    var best_b: usize = 0;
    var best_v: f64 = -1;
    for (0..63) |b| {
        w0 += hist[b] / total;
        m0 += hist[b] * @as(f64, @floatFromInt(b)) / total;
        if (w0 <= 0 or w0 >= 1) continue;
        const mb = (mu * w0 - m0);
        const vb = mb * mb / (w0 * (1 - w0));
        if (vb > best_v) {
            best_v = vb;
            best_b = b;
        }
    }
    const eta: f32 = @floatCast(if (vt > 0) best_v / vt else 0);
    const th = lo + span * (@as(f32, @floatFromInt(best_b)) + 1.0) / 64.0;
    var nhigh: usize = 0;
    for (cell) |c| {
        if (c > th) nhigh += 1;
    }
    const ink_high = 2 * nhigh < cw * ch;
    const ink = alloc.alloc(bool, cw * ch) catch die("out of memory", .{});
    var nink: usize = 0;
    for (cell, 0..) |c, i| {
        ink[i] = (c > th) == ink_high;
        if (ink[i]) nink += 1;
    }
    const share = @as(f32, @floatFromInt(nink)) / @as(f32, @floatFromInt(cw * ch));
    say("seed reading: the whole repeats {d} by {d}{s}; its mean cell is {d} by {d} pixels; two shades by Otsu: separation {d:.2}; the ink is the {s} shade, {d:.3} of the cell\n", .{ rd.nx, rd.ny, if (rd.bonded) " in a bond" else "", cw, ch, eta, if (ink_high) "lighter" else "darker", share });
    W.put(&rec, &line, "# seed reading: repeats {d} by {d}{s}; mean cell {d} by {d}; Otsu separation {d:.3}; ink the {s} shade, {d:.3} of the cell\n", .{ rd.nx, rd.ny, if (rd.bonded) " in a bond" else "", cw, ch, eta, if (ink_high) "lighter" else "darker", share });
    if (eta < 0.60 or share < 0.005) {
        say("no seed: the cell is no figure on a ground (separation {d:.2}, under 0.60, or no ink)\n", .{eta});
        W.put(&rec, &line, "seed 0\nwhy the cell is no figure on a ground (Otsu separation {d:.3}, ink {d:.3})\n", .{ eta, share });
        writeFile(out_path, rec.items);
        return;
    }
    // the cell turned round so its first row and column hold the least ink: the motif is not cut by the cell's border
    var rx: usize = 0;
    var ry: usize = 0;
    {
        var bestc: usize = std.math.maxInt(usize);
        for (0..cw) |x| {
            var c: usize = 0;
            for (0..ch) |y| c += @intFromBool(ink[y * cw + x]);
            if (c < bestc) {
                bestc = c;
                rx = x;
            }
        }
        bestc = std.math.maxInt(usize);
        for (0..ch) |y| {
            var c: usize = 0;
            for (0..cw) |x| c += @intFromBool(ink[y * cw + x]);
            if (c < bestc) {
                bestc = c;
                ry = y;
            }
        }
    }
    const m = alloc.alloc(bool, cw * ch) catch die("out of memory", .{});
    for (0..ch) |y| {
        for (0..cw) |x| m[y * cw + x] = ink[((y + ry) % ch) * cw + (x + rx) % cw];
    }
    {
        // the turned cell and its ink, for the sheet: OUT.cell.pgm, OUT.ink.pgm
        var nb: [1024]u8 = undefined;
        const pg = alloc.alloc(u8, cw * ch + 64) catch die("out of memory", .{});
        inline for (.{ "cell", "ink" }) |what| {
            const head = std.fmt.bufPrint(pg[0..64], "P5\n{d} {d}\n255\n", .{ cw, ch }) catch unreachable;
            const hl = head.len;
            for (0..ch) |y| {
                for (0..cw) |x| {
                    const src = ((y + ry) % ch) * cw + (x + rx) % cw;
                    const v: f32 = if (std.mem.eql(u8, what, "cell")) (cell[src] - lo) / span else if (ink[src]) 1.0 else 0.0;
                    pg[hl + y * cw + x] = @intFromFloat(@min(255.0, @max(0.0, v * 255.0)));
                }
            }
            writeFile(std.fmt.bufPrint(&nb, "{s}.{s}.pgm", .{ out_path, what }) catch unreachable, pg[0 .. hl + cw * ch]);
        }
    }
    // the motif: all the ink of the turned cell; and each of its larger pieces on its own (a flower and its leaves)
    var sils: std.ArrayList(Sil) = .empty;
    {
        var x0: usize = cw;
        var y0: usize = ch;
        var x1: usize = 0;
        var y1: usize = 0;
        for (0..ch) |y| {
            for (0..cw) |x| {
                if (!m[y * cw + x]) continue;
                x0 = @min(x0, x);
                y0 = @min(y0, y);
                x1 = @max(x1, x + 1);
                y1 = @max(y1, y + 1);
            }
        }
        sils.append(alloc, silOf(m, cw, x0, y0, x1, y1)) catch die("out of memory", .{});
        // the pieces (8-connected), each with its box
        const lab = alloc.alloc(u32, cw * ch) catch die("out of memory", .{});
        @memset(lab, 0);
        const stack = alloc.alloc(usize, cw * ch) catch die("out of memory", .{});
        const Piece = struct { l: u32, area: usize, b: [4]usize };
        var pcs: std.ArrayList(Piece) = .empty;
        var nl: u32 = 0;
        for (0..cw * ch) |s0| {
            if (!m[s0] or lab[s0] != 0) continue;
            nl += 1;
            var sp: usize = 1;
            stack[0] = s0;
            lab[s0] = nl;
            var area: usize = 0;
            var b = [4]usize{ cw, ch, 0, 0 };
            while (sp > 0) {
                sp -= 1;
                const p = stack[sp];
                const px = p % cw;
                const py = p / cw;
                area += 1;
                b = .{ @min(b[0], px), @min(b[1], py), @max(b[2], px + 1), @max(b[3], py + 1) };
                var dy: i32 = -1;
                while (dy <= 1) : (dy += 1) {
                    var dx: i32 = -1;
                    while (dx <= 1) : (dx += 1) {
                        const qx = @as(i32, @intCast(px)) + dx;
                        const qy = @as(i32, @intCast(py)) + dy;
                        if (qx < 0 or qy < 0 or qx >= @as(i32, @intCast(cw)) or qy >= @as(i32, @intCast(ch))) continue;
                        const q: usize = @intCast(qy * @as(i32, @intCast(cw)) + qx);
                        if (!m[q] or lab[q] != 0) continue;
                        lab[q] = nl;
                        stack[sp] = q;
                        sp += 1;
                    }
                }
            }
            pcs.append(alloc, .{ .l = nl, .area = area, .b = b }) catch die("out of memory", .{});
        }
        std.mem.sort(Piece, pcs.items, {}, struct {
            fn lt(_: void, a: Piece, b: Piece) bool {
                return a.area > b.area;
            }
        }.lt);
        var kept: usize = 0;
        if (pcs.items.len > 1) {
            for (pcs.items) |pc| {
                if (kept >= MAXSEED - 1 or pc.area * 100 < nink * 3) break;
                const only = alloc.alloc(bool, cw * ch) catch die("out of memory", .{});
                for (lab, 0..) |l, i| only[i] = l == pc.l;
                sils.append(alloc, silOf(only, cw, pc.b[0], pc.b[1], pc.b[2], pc.b[3])) catch die("out of memory", .{});
                kept += 1;
            }
        }
        say("  the cell's ink: {d} piece(s); {d} hold 3 % of the ink or more and are read on their own too\n", .{ nl, kept });
    }
    var found: [MAXSEED]SeedCand = undefined;
    var found_ok: [MAXSEED]bool = undefined;
    var found_box: [MAXSEED]f32 = undefined;
    var buf: [GS * GS]u8 = undefined;
    for (sils.items, 0..) |*sl, si| {
        // what GlowRect draws: a box, or a disc stretched to its box
        var boxm: [GS * GS]bool = undefined;
        var discm: [GS * GS]bool = undefined;
        for (0..GS) |gy| {
            for (0..GS) |gx| {
                boxm[gy * GS + gx] = true;
                const u = (@as(f32, @floatFromInt(gx)) + 0.5) / GS * 2.0 - 1.0;
                const v = (@as(f32, @floatFromInt(gy)) + 0.5) / GS * 2.0 - 1.0;
                discm[gy * GS + gx] = u * u + v * v <= 1.0;
            }
        }
        const ms = softOf(&sl.m);
        const bs = softOf(&boxm);
        const ds = softOf(&discm);
        const bl = @max(softLike(&ms, &bs), softLike(&ms, &ds));
        // the coarse pass, with both pictures grown by one cell, so strokes that run close count (a thin drawing and
        // its look-alikes lie far apart bit for bit)
        const mg = grow256(bits256(&sl.bits));
        var hcount = [_]u32{0} ** 101;
        for (gi, gi_la) |*e, la| {
            if (e.form != 1 or @abs(la - sl.la) > 0.27) continue;
            hcount[@intFromFloat(@round(100.0 * iou256(mg, grow256(bits256(&e.bits)))))] += 1;
        }
        const K: u32 = 4000;
        var hmin: usize = 100;
        var acc: u32 = hcount[100];
        while (hmin > 0 and acc + hcount[hmin - 1] < K) {
            hmin -= 1;
            acc += hcount[hmin];
        }
        var near: std.ArrayList(u32) = .empty;
        defer near.deinit(alloc);
        for (gi, gi_la, 0..) |*e, la, i| {
            if (e.form != 1 or @abs(la - sl.la) > 0.27) continue;
            if (@as(usize, @intFromFloat(@round(100.0 * iou256(mg, grow256(bits256(&e.bits)))))) >= hmin) near.append(alloc, @intCast(i)) catch die("out of memory", .{});
            if (near.items.len >= 6000) break;
        }
        say("  motif {d} ({s}, {d} by {d} pixels of the cell): a box or a disc lies over it by {d:.2}; {d} glyphs of the index lie over it by {d} hundredths or more, grown by one cell\n", .{ si, if (si == 0) "all the ink" else "one piece", sl.x1 - sl.x0, sl.y1 - sl.y0, bl, near.items.len, hmin });
        var cands: std.ArrayList(SeedCand) = .empty;
        defer cands.deinit(alloc);
        for (near.items) |ii| {
            const e = &gi[ii];
            if (uc_class(e.cp) == 2) continue; // a presentation variant: the plain character draws the same shape
            var v: [6]f32 = undefined;
            var form: c_int = 0;
            const key = fx_key.items[e.font];
            if (wzb_glyph_mask2(key.ptr, e.cp, GS, &buf, &v, &form, null) != 0) continue;
            var tm: [GS * GS]bool = undefined;
            for (0..GS * GS) |q| tm[q] = buf[q] >= 128;
            const ts = softOf(&tm);
            const like = softLike(&ms, &ts);
            const drawing = uc_drawing(e.cp) != 0;
            var u8b: [8]u8 = undefined;
            const ul = std.unicode.utf8Encode(@intCast(e.cp), &u8b) catch continue;
            const bytes: usize = 1 + 4 * @as(usize, TEXT2_WORDS) + (@as(usize, ul) + 1) + (key.len + 1) + 1;
            // a drawing is preferred by 0.03 of likeness; among glyphs that lie as well, the fewer bytes
            const sc = like + (if (drawing) @as(f32, 0.03) else 0.0) - 0.0005 * @as(f32, @floatFromInt(bytes));
            cands.append(alloc, .{ .gi = ii, .like = like, .score = sc, .drawing = drawing, .bytes = bytes, .v = v }) catch die("out of memory", .{});
        }
        std.mem.sort(SeedCand, cands.items, {}, struct {
            fn lt(_: void, a: SeedCand, b: SeedCand) bool {
                return a.score > b.score;
            }
        }.lt);
        for (cands.items[0..@min(if (si == 0) @as(usize, 12) else 4, cands.items.len)]) |c| {
            const e = &gi[c.gi];
            say("    U+{X:0>4} of {s}: lies over it by {d:.3}{s}, {d} bytes\n", .{ e.cp, fx_label.items[e.font], c.like, if (c.drawing) ", a drawing" else "", c.bytes });
            W.put(&rec, &line, "cand {d} U+{X:0>4} like {d:.3} drawing {d} bytes {d} gv {d:.5} {d:.5} {d:.5} {d:.5} {d:.5} {d:.5} box {d} {d} {d} {d} {d} {d}\t{s}\t{s}\n", .{ si, e.cp, c.like, @intFromBool(c.drawing), c.bytes, c.v[0], c.v[1], c.v[2], c.v[3], c.v[4], c.v[5], cw, ch, sl.x0, sl.y0, sl.x1, sl.y1, fx_key.items[e.font], fx_label.items[e.font] });
        }
        found_box[si] = bl;
        found_ok[si] = cands.items.len > 0 and cands.items[0].like >= SEED_T and cands.items[0].like >= bl + 0.05;
        if (cands.items.len > 0) found[si] = cands.items[0];
        if (cands.items.len == 0) found[si] = .{ .gi = 0, .like = 0, .score = -1, .drawing = false, .bytes = 0, .v = undefined };
    }
    // the motif's and the ground's colours: the picture's own pixels on each side of the threshold
    var sums = [2][3]f64{ .{ 0, 0, 0 }, .{ 0, 0, 0 } };
    var cnts = [2]f64{ 0, 0 };
    {
        const n = rd.n;
        const px = t.pyr.lev[0];
        for (0..n * n) |i| {
            const s = (rd.t[i] > th) == ink_high;
            const k: usize = if (s) 0 else 1;
            inline for (0..3) |c| sums[k][c] += px[3 * i + c];
            cnts[k] += 1;
        }
    }
    var cols: [2]u32 = undefined;
    for (0..2) |k| {
        const c3 = [3]f32{ @floatCast(sums[k][0] / @max(cnts[k], 1)), @floatCast(sums[k][1] / @max(cnts[k], 1)), @floatCast(sums[k][2] / @max(cnts[k], 1)) };
        cols[k] = 0xff000000 | rgbWord(c3);
    }
    // the phase the seeds are placed with (the cell turned by rx, ry)
    const fcw: f32 = @floatFromInt(cw);
    const fch: f32 = @floatFromInt(ch);
    var ox = @as(f32, @floatFromInt(rx)) / fcw;
    const oy = @as(f32, @floatFromInt(ry)) / fch;
    if (rd.bonded) {
        // the mean cell of a wall in a bond lies in the frame where every row is moved back by its place in the
        // bond: the seed's first row is the bond's row m, which lies m bond shifts to the right
        const n = rd.n;
        const period = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(rd.ny));
        const ymid = (@as(f32, @floatFromInt(ry)) + 0.5 * fch);
        const y0 = rd.row0 * @as(f32, @floatFromInt(n));
        const mrow = @floor(@mod(ymid - y0, @as(f32, @floatFromInt(n))) / period);
        ox += mrow * rd.bond_shift;
    }
    const Put = struct {
        fn seedBlock(r: *std.ArrayList(u8), lb: []u8, c: *const SeedCand, sl: *const Sil, fw: f32, fh: f32, nx: usize, ny: usize, pox: f32, poy: f32, bonded: bool, bshift: f32, ink_c: u32, ground_c: u32, boxl: f32) void {
            const e = &gi[c.gi];
            const bx = CellItem{
                .cx = 0.5 * @as(f32, @floatFromInt(sl.x0 + sl.x1)) / fw,
                .cy = 0.5 * @as(f32, @floatFromInt(sl.y0 + sl.y1)) / fh,
                .hw = 0.5 * @as(f32, @floatFromInt(sl.x1 - sl.x0)) / fw,
                .hh = 0.5 * @as(f32, @floatFromInt(sl.y1 - sl.y0)) / fh,
            };
            W.put(r, lb, "seed 1\nlabel {s}\ncp {X}\ngv {d:.6} {d:.6} {d:.6} {d:.6} {d:.6} {d:.6}\nbox {d:.6} {d:.6} {d:.6} {d:.6}\nrepeat {d} {d} {d:.6} {d:.6} {d} {d:.6}\ncolour {x:0>8} {x:0>8}\nlike {d:.4} {d:.4}\ndrawing {d} bytes {d}\n", .{ fx_label.items[e.font], e.cp, c.v[0], c.v[1], c.v[2], c.v[3], c.v[4], c.v[5], bx.cx, bx.cy, bx.hw, bx.hh, nx, ny, pox, poy, @intFromBool(bonded), bshift, ink_c, ground_c, c.like, boxl, @intFromBool(c.drawing), c.bytes });
            W.put(r, lb, "key {s}\n", .{fx_key.items[e.font]});
        }
    };
    // OUT: one glyph over the whole motif
    if (found_ok[0]) {
        const e = &gi[found[0].gi];
        say("seed: U+{X:0>4} of {s}, lying over the motif by {d:.3} (a box or a disc {d:.3}){s}; {d} bytes; ink {x:0>6} on {x:0>6}\n", .{ e.cp, fx_label.items[e.font], found[0].like, found_box[0], if (found[0].drawing) ", a drawing" else "", found[0].bytes, cols[0] & 0xffffff, cols[1] & 0xffffff });
        Put.seedBlock(&rec, &line, &found[0], &sils.items[0], fcw, fch, rd.nx, rd.ny, ox, oy, rd.bonded, rd.bond_shift, cols[0], cols[1], found_box[0]);
    } else if (found_box[0] >= SEED_T and found[0].score >= 0 and found[0].like < found_box[0] + 0.05) {
        // the motif is a box: GlowRect draws it in fewer bytes than any glyph, through the same mask
        say("seed: the box GlowRect draws (it lies over the motif by {d:.3}, the best glyph by {d:.3}); 45 bytes; ink {x:0>6} on {x:0>6}\n", .{ found_box[0], found[0].like, cols[0] & 0xffffff, cols[1] & 0xffffff });
        const sl = &sils.items[0];
        W.put(&rec, &line, "seed 1\nlabel GlowRect (a box)\ncp 0\ngv 1 1 0 1 0 0.5\nbox {d:.6} {d:.6} {d:.6} {d:.6}\nrepeat {d} {d} {d:.6} {d:.6} {d} {d:.6}\ncolour {x:0>8} {x:0>8}\nlike {d:.4} {d:.4}\ndrawing 0 bytes 45\nkey -\n", .{ 0.5 * @as(f32, @floatFromInt(sl.x0 + sl.x1)) / fcw, 0.5 * @as(f32, @floatFromInt(sl.y0 + sl.y1)) / fch, 0.5 * @as(f32, @floatFromInt(sl.x1 - sl.x0)) / fcw, 0.5 * @as(f32, @floatFromInt(sl.y1 - sl.y0)) / fch, rd.nx, rd.ny, ox, oy, @intFromBool(rd.bonded), rd.bond_shift, cols[0], cols[1], found_box[0], found_box[0] });
    } else {
        const why = if (found[0].score < 0) "no glyph of the index lies over the motif" else "no glyph lies over the motif by 0.70 (soft)";
        say("no seed: {s} (best {d:.3}, a box or a disc {d:.3})\n", .{ why, if (found[0].score < 0) 0 else found[0].like, found_box[0] });
        W.put(&rec, &line, "seed 0\nwhy {s} (best {d:.3}, box or disc {d:.3})\n", .{ why, if (found[0].score < 0) 0 else found[0].like, found_box[0] });
    }
    writeFile(out_path, rec.items);
    // OUT.pieces: one glyph per piece, for the pieces a glyph lies over
    if (sils.items.len > 2) {
        var pr: std.ArrayList(u8) = .empty;
        var npc: usize = 0;
        for (sils.items[1..], 1..) |*sl, si| {
            if (!found_ok[si]) {
                W.put(&pr, &line, "# piece {d}: no seed (best {d:.3}, a box or a disc {d:.3}); left out\n", .{ si, found[si].like, found_box[si] });
                continue;
            }
            Put.seedBlock(&pr, &line, &found[si], sl, fcw, fch, rd.nx, rd.ny, ox, oy, rd.bonded, rd.bond_shift, cols[0], cols[1], found_box[si]);
            npc += 1;
        }
        say("seeds per piece: {d} of {d} pieces have a glyph\n", .{ npc, sils.items.len - 1 });
        var nb: [1024]u8 = undefined;
        writeFile(std.fmt.bufPrint(&nb, "{s}.pieces", .{out_path}) catch unreachable, pr.items);
    }
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
    var rd = readPicture(&tread);
    freeTarget(&tread);
    if (opt.whole) |wp| {
        say("the whole picture, read for the repeat every tile draws at its own place:\n", .{});
        const wimg = readPpm(wp);
        var wf: u32 = 0;
        while ((@as(usize, 1) << @intCast(wf)) < wimg.w) wf += 1;
        var wt = makeTarget(wimg, wf);
        const rw = readPicture(&wt);
        freeTarget(&wt);
        mapWhole(&rd, &rw, opt.win);
    }
    if (opt.seedfile) |sp| loadSeed(sp);
    // a figure on a ground, and whether its pieces are glyphs of a font (the reading behind Text)
    readFigure(rd.t, rd.n, &rd.fig);
    if (!figureIsText(&rd.fig) and giLoad()) {
        // not two flat shades read as text: colour glyphs on a flat ground (a picture of emoji has a light ground and
        // colourful ink, which may also count as two shades)
        const keep = .{ cf_n, cf_key, cf_label, cf_v1, cf_v1name, font_space, font_avg, font_have, wide_now };
        var cfig = Figure{};
        readColourFigure(&img, &cfig);
        if (figureIsText(&cfig)) rd.fig = cfig else {
            // the two-shade reading stands: its candidate fonts are put back for what is said about it
            cf_n = keep[0];
            cf_key = keep[1];
            cf_label = keep[2];
            cf_v1 = keep[3];
            cf_v1name = keep[4];
            font_space = keep[5];
            font_avg = keep[6];
            font_have = keep[7];
            wide_now = keep[8];
        }
    }
    if (!figureIsText(&rd.fig) and !rd.fig.colour and rd.fig.two >= TWO_T and rd.fig.nshape > 0 and rd.fig.nshape <= 3 and rd.fig.nrich > 0 and rd.fig.ink >= 0.02 and rd.nring > 0) {
        say("a figure of {d} piece(s) that is no glyph (best {d:.2}), and the ring reading found a swirl: the Twirl is run backwards\n", .{ rd.fig.nshape, rd.fig.best_single });
        untwirl(rd.t, rd.n, &rd.fig);
    }
    sayFigure(&rd.fig);
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
    if (opt.from) |fp| {
        // The tile keeps the whole picture's procedure (the same operators, so neighbouring tiles are the same kind of
        // surface) and retunes their values on its own pixels, coarse to fine. What places a shape, repeats it or
        // draws a glyph stays as found on the whole picture.
        g = parseScript(readFile(fp));
        for (g.nodes[0..g.n]) |*x| {
            x.keep = true;
            x.lock = x.op == OP_GLOWRECT or x.op == OP_TRANSFORM or x.op == OP_TRANSFORMMUL or x.op == OP_TEXT or x.op == OP_TWIRL;
            // the kind of surface stays the whole picture's: the whole-number values (a noise's frequency and octaves,
            // modes, passes) are kept, so neighbouring tiles do not turn into other surfaces; a noise's seed may change,
            // or every tile would repeat the same field (Daniel's 473x note: "only seeds and a few values change")
            if (!opt.from_free) {
                for (ops[x.op].kinds, 0..) |kd, wi| {
                    if (kd == 'i' and !(x.op == OP_PERLIN and wi == 5)) x.lockw |= @as(u32, 1) << @intCast(wi);
                }
            }
        }
        if (opt.fix) fixTileFaults(&g, opt.win);
        if (opt.structure == .seed) {
            // the seeds at the tile's own place over the retuned surface; they are locked (placed, never tuned)
            const colour = g.root;
            _ = appendSeed(&g, seeds[0..nseeds], opt.win, colour, @floatFromInt(@as(usize, 1) << @intCast(full)));
        }
        var size = work;
        while (true) {
            cur = tune(&g, &t, 0, g.n - 1, if (size >= full) opt.final else opt.deep * 2, true, 2);
            if (cur >= BAD) die("the whole picture's procedure does not draw on this tile: {s}", .{std.mem.span(wzb_notes())});
            rung += 1;
            saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
            say("the whole picture's procedure, retuned at {d} px: {d} operators, {d} bytes, measure {d:.5}, {d:.0} s\n", .{ @as(usize, 1) << @intCast(size), g.n, g.bytes(), cur, seconds() - t0 });
            if (size >= full) break;
            size += 1;
            cacheClear();
            cache_cap = if (size >= 9) 500 else 1500;
            freeTarget(&t);
            t = makeTarget(img, size);
        }
        finish(&g, img, full, prefix, &log, t0);
        return;
    }
    if (opt.structure == .text) {
        // The text read from the figure, drawn by werkkzeug's Text operator on a flat ground. Everything here was
        // read: the ground and the ink are the picture's two colours, each text's letters, font, place and size come
        // from the glyph reading, the twirls from running Twirl backwards. Only each text's place and size (by pixels
        // and less, around what was read) and a Blur for soft edges are tried by the inner measure.
        freeTarget(&t);
        cacheClear();
        cache_cap = 500;
        t = makeTarget(img, full);
        const ground = if (rd.fig.colour) rd.fig.ground else if (rd.fig.ink_high) rd.c0 else rd.c1;
        // colour glyphs draw in their own colours; the operator's colour is only their foreground (CPAL 0xFFFF)
        const inkc = if (rd.fig.colour) 0xff000000 else if (rd.fig.ink_high) rd.c1 else rd.c0;
        g = Graph{};
        g.nodes[0] = flatNode(ground);
        g.nodes[0].nw = 3;
        g.nodes[0].lock = true;
        g.n = 1;
        g.root = 0;
        var items: [MAXTEXT * 3 + 8][2]usize = undefined;
        var steps: [MAXTEXT * 3 + 8]f32 = undefined;
        var ni: usize = 0;
        const px = 1.0 / @as(f32, @floatFromInt(rd.n));
        for (rd.fig.texts[0..rd.fig.ntext]) |*tr| {
            var nd = textNode(tr, inkc);
            nd.nin = 1;
            nd.in[0] = @intCast(g.n - 1);
            const k = append(&g, nd);
            for (0..3) |w| {
                items[ni] = .{ k, w };
                steps[ni] = px;
                ni += 1;
            }
        }
        const last_text = g.n - 1;
        var iu = rd.fig.nun;
        while (iu > 0) {
            iu -= 1;
            const u = rd.fig.un[iu];
            var tw = Node{ .op = OP_TWIRL, .nw = 7, .nin = 1, .keep = true };
            tw.in[0] = @intCast(g.n - 1);
            tw.w[0] = wordOf(-u[0]);
            tw.w[1] = wordOf(u[1]);
            tw.w[2] = wordOf(u[2]);
            tw.w[3] = wordOf(u[2]);
            tw.w[4] = wordOf(u[3]);
            tw.w[5] = wordOf(u[4]);
            tw.w[6] = 0;
            // a twirl stays as it was read: only the very strength that was taken out gives the glyph back
            _ = append(&g, tw);
        }
        cur = score(&g, &t);
        if (cur >= BAD) die("the text read from the picture does not draw: {s}", .{std.mem.span(wzb_notes())});
        rung += 1;
        saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
        say("rung {d}: structure text, as read: {d} text(s), {d} twirl(s), {d} operators, {d} bytes, measure {d:.5}\n", .{ rung, rd.fig.ntext, rd.fig.nun, g.n, g.bytes(), cur });
        {
            // soft edges: a Blur right after the texts, as wide as pays (the artists blurred the glyph before twirling it)
            const widths = [_]f32{ 0.002, 0.003, 0.004, 0.006, 0.008, 0.009, 0.011, 0.013, 0.016, 0.02 };
            const passes = [_]u32{ 0x11, 0x12, 0x13 }; // one to three passes, as .kkrieger's artists set them (0x12 most often)
            var best_g = g;
            var best_s = cur;
            for (passes) |pc| {
                for (widths) |bw| {
                    var c = g;
                    var bl = Node{ .op = OP_BLUR, .nw = 4, .keep = true };
                    bl.w[0] = pc;
                    bl.w[1] = wordOf(bw);
                    bl.w[2] = wordOf(bw);
                    bl.w[3] = wordOf(1.0);
                    wrapOne(&c, last_text, bl);
                    const sc = score(&c, &t);
                    // the best of them, if it pays for its 17 bytes
                    if (sc < cur * (1.0 - opt.byte_cost * 17.0) and sc < best_s) {
                        best_s = sc;
                        best_g = c;
                    }
                }
            }
            if (best_g.n != g.n) {
                g = best_g;
                cur = best_s;
                for (items[0..ni]) |*it| {
                    if (it[0] > last_text) it[0] += 1;
                }
                rung += 1;
                saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
                say("rung {d}: soft edges, a Blur of {d:.4} after the text, {d} operators, {d} bytes, measure {d:.5}\n", .{ rung, f32of(g.nodes[last_text + 1].w[1]), g.n, g.bytes(), cur });
            }
        }
        cur = nudge(&g, &t, items[0..ni], steps[0..ni], 6);
        rung += 1;
        saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
        say("cleaned and tuned at {d} px: {d} operators, {d} bytes, measure {d:.5}, {d:.0} s\n", .{ rd.n, g.n, g.bytes(), cur, seconds() - t0 });
        finish(&g, img, full, prefix, &log, t0);
        return;
    }
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
    if (opt.structure == .seed) {
        const colour = g.root;
        _ = appendSeed(&g, seeds[0..nseeds], opt.win, colour, @floatFromInt(@as(usize, 1) << @intCast(full)));
        cur = tune(&g, &t, 0, colour, opt.deep * 2, true, 2);
        if (cur >= BAD) die("the seed does not draw: {s}", .{std.mem.span(wzb_notes())});
        rung += 1;
        saveRung(prefix, rung, &g, &t, cur, &log, seconds() - t0);
        say("rung {d}: {d} seed(s), {d} operators, {d} bytes, measure {d:.5}\n", .{ rung, nseeds, g.n, g.bytes(), cur });
    }
    if (opt.structure == .shape) {
        const colour = g.root;
        const ol = if (rd.win) appendOutlineWin(&g, &rd, colour, opt, @floatFromInt(@as(usize, 1) << @intCast(full))) else appendOutline(&g, &rd, colour, opt);
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
    var structure_done = opt.structure == .shape or opt.structure == .plain or opt.structure == .seed;

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
    finish(&g, img, full, prefix, &log, t0);
}

/// write the found procedure, its drawing and the rungs' record
fn finish(g: *const Graph, img: Image, full: u32, prefix: []const u8, log: *std.ArrayList(u8), t0: f64) void {
    var buf: [1 << 16]u8 = undefined;
    var name: [1024]u8 = undefined;
    writeFile(std.fmt.bufPrint(&name, "{s}.script", .{prefix}) catch unreachable, scriptText(g, &buf));
    const bm = draw(g, full) orelse die("the final procedure does not draw", .{});
    const rgba = alloc.alloc(u8, img.w * img.w * 4) catch die("out of memory", .{});
    wzb_rgba(bm, rgba.ptr);
    writePpm(std.fmt.bufPrint(&name, "{s}.ppm", .{prefix}) catch unreachable, rgba, img.w, img.w);
    const tail = std.fmt.bufPrint(&buf, "# rung operators bytes measure seconds\n# total {d:.1} s, {d} graphs asked, {d} operators drawn, {d} refused, {d} too slow\n", .{ seconds() - t0, n_eval, n_draw, n_refused, n_slow }) catch unreachable;
    log.appendSlice(alloc, tail) catch {};
    writeFile(std.fmt.bufPrint(&name, "{s}.log", .{prefix}) catch unreachable, log.items);
    sayNotes();
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
    whole: ?[*:0]const u8 = null, // milestone 2: the whole picture (at the tile's size), whose repeat the tile draws
    win: Win = .{}, // where the tile lies in the whole picture
    seedfile: ?[*:0]const u8 = null, // the seed `p2p seed` found on the whole picture
    from: ?[*:0]const u8 = null, // a procedure found on the whole picture: the tile keeps its operators and retunes their values
    from_free: bool = false, // with from: the whole-number values are retuned too (the first try; the tiles drift apart)
    fix: bool = true, // milestone 2b: with from and window, the three faults of milestone 2 fixed (fix=0 gives milestone 2's tiles)
};

/// Milestone 2b, the three faults of milestone 2's tiles (the whole picture's procedure retuned on a tile):
///  1. a noise's frequency follows the window: werkkzeug's Perlin draws 2^freq cells across whatever it is drawn on,
///     so on a tile a quarter of the picture wide the same words draw the whole picture's octaves four times finer;
///     the tile takes freq + log2(side), and octaves coarser than one cell across the tile are dropped (said);
///  2. a light stands at the whole picture's place: Bump's light position (in parts of the picture it is drawn on)
///     is moved by the window, its height scaled with it, and locked, so every tile is lit from the same lamp;
///  3. the colour retune keeps hue: every colour is retuned by brightness and saturation only.
fn fixTileFaults(g: *Graph, w: Win) void {
    var sh: i32 = 0;
    var s = w.s;
    while (s < 0.999 and sh < 12) : (sh += 1) s *= 2;
    if (@abs(s - 1.0) > 0.001) die("window side {d} is not a power of two of the picture (1, 1/2, 1/4, ...)", .{w.s});
    for (g.nodes[0..g.n], 0..) |*x, i| {
        x.hue = true;
        if (x.op == OP_PERLIN and sh > 0) {
            var f: i32 = @bitCast(x.w[2]);
            var o: i32 = @bitCast(x.w[3]);
            f -= sh;
            if (f < 0) {
                say("v{d} Perlin: {d} octave(s) coarser than one cell across this tile are dropped (the tile's own colours carry them)\n", .{ i, -f });
                o += f;
                f = 0;
            }
            if (o < 1) o = 1;
            x.w[2] = @bitCast(f);
            x.w[3] = @bitCast(o);
            x.lockw |= (1 << 2) | (1 << 3);
        }
        if (x.op == OP_BUMP) {
            if (x.w[0] != 2) {
                const px = f32of(x.w[1]);
                const py = f32of(x.w[2]);
                const pz = f32of(x.w[3]);
                x.w[1] = wordOf((px - w.x) / w.s);
                x.w[2] = wordOf((py - w.y) / w.s);
                x.w[3] = wordOf(pz / w.s);
            }
            x.lockw |= (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5);
        }
    }
}

/// What adds structure. Each needs its own reading; the inner measure accepts any of them on almost any
/// picture, so none is tried without one, and the choice between the allowed ones is the eye's.
const Structure = enum { plain, shape, patches, second, grain, rings, mirror, text, seed };

fn allowed(rd: *const Reading, st: Structure, opt: Options) bool {
    return switch (st) {
        .plain => true,
        .shape => rd.nrect > 0,
        .patches => rd.nrect == 0 and rd.flat >= 0.03 and rd.edge >= 0.35,
        .second => rd.nrect == 0 and rd.off >= 0.01 and rd.off_coh >= 0.8,
        .grain => rd.nrect == 0 and rd.aniso >= opt.grain,
        .rings => rd.nrect == 0 and rd.nring > 0,
        .mirror => rd.nrect == 0 and rd.nring >= 2 and rd.mirror >= 0.10,
        .text => figureIsText(&rd.fig),
        .seed => nseeds > 0,
    };
}

pub fn hasModern(g: *const Graph) bool {
    for (g.nodes[0..g.n]) |nd| {
        if (isModern(nd.op)) return true;
    }
    return false;
}

/// Draw a graph of modern operators on a canvas of side pixels showing window win of the picture: the margin is the
/// widest neighbourhood any node reads (Shade one pixel, Wear its radius or length), cut away by cropRgba.
pub fn drawCanvas(g: *const Graph, side: usize, win: Win, maxoct: u32) ?*anyopaque {
    if (isQuad(g.nodes[g.root].op)) return drawQuad(g, side, win, maxoct);
    if (isGrid(g.nodes[g.root].op)) return drawGrid(g, side, win, maxoct);
    if (isStack(g.nodes[g.root].op)) return drawStack(g, side, win, maxoct);
    for (g.nodes[0..g.root]) |nd| {
        if (isQuad(nd.op) or isGrid(nd.op) or isStack(nd.op)) {
            say("refused: a {s} is the procedure's last operator (it draws whole procedures, each on its own canvas)\n", .{ops[nd.op].name});
            return null;
        }
    }
    var reach: f32 = 0;
    var any = false;
    for (g.nodes[0 .. g.root + 1]) |nd| {
        if (!isModern(nd.op)) continue;
        const r = modern.marginOf(nd.op - OP_MODERN, nd.w[0..wordsOf(&nd)]);
        if (r > 0) any = true;
        reach += r; // neighbourhoods chained one after another add up
    }
    const pxs = win.s / @as(f32, @floatFromInt(side));
    var m: usize = if (any) @as(usize, @intFromFloat(@ceil(reach / pxs))) + 2 else 0;
    m = (m + 1) & ~@as(usize, 1); // even, so a canvas of a power-of-two side stays a multiple of four pixels
    modern.c.cv = .{ .w = side + 2 * m, .h = side + 2 * m, .m = m, .wx = win.x, .wy = win.y, .ws = win.s, .maxoct = maxoct };
    return draw(g, 0);
}

pub fn isQuad(op: u8) bool {
    return op == OP_MODERN + modern.K_QUAD;
}

extern "c" fn wzb_new(xs: c_int, ys: c_int) ?*anyopaque;

/// one input of a Quad as a procedure of its own: the graph up to that input's root, what it does not use dropped
pub fn quadPart(g: *const Graph, q: usize) Graph {
    var sub = g.*;
    sub.root = g.nodes[g.root].in[q];
    sub.prune();
    return sub;
}

/// Four procedures per picture (milestone 2d): the Quad's four inputs, each drawn on its own canvas (input q at the
/// place 2x - column, 2y - row of the window's place x, y), every canvas of one side and margin so the Quad reads
/// pixel k of each under its own pixel k; then the Quad lays them together with its seam.
fn drawQuad(g: *const Graph, side: usize, win: Win, maxoct: u32) ?*anyopaque {
    const rt = g.nodes[g.root];
    if (rt.nin != 4) {
        say("refused: a Quad takes four procedures, the graph gives {d}\n", .{rt.nin});
        return null;
    }
    const subs = alloc.alloc(Graph, 4) catch die("out of memory", .{});
    defer alloc.free(subs);
    const pxs = 2.0 * win.s / @as(f32, @floatFromInt(side));
    var m: usize = 0;
    for (0..4) |q| {
        subs[q] = quadPart(g, q);
        var reach: f32 = 0;
        var any = false;
        for (subs[q].nodes[0 .. subs[q].root + 1]) |nd| {
            if (isQuad(nd.op) or isGrid(nd.op) or isStack(nd.op)) {
                say("refused: a Quad's inputs hold a {s} (one Quad per procedure, its last operator; a Stack may lay Quads)\n", .{ops[nd.op].name});
                return null;
            }
            if (!isModern(nd.op)) continue;
            const r = modern.marginOf(nd.op - OP_MODERN, nd.w[0..wordsOf(&nd)]);
            if (r > 0) any = true;
            reach += r;
        }
        const mq: usize = if (any) @as(usize, @intFromFloat(@ceil(reach / pxs))) + 2 else 0;
        m = @max(m, mq);
    }
    m = (m + 1) & ~@as(usize, 1);
    const cw = side + 2 * m;
    var parts: [4]?*anyopaque = .{ null, null, null, null };
    defer for (parts) |p| {
        if (p != null) wzb_free(p);
    };
    for (0..4) |q| {
        const col: f32 = @floatFromInt(q % 2);
        const row: f32 = @floatFromInt(q / 2);
        modern.c.cv = .{ .w = cw, .h = cw, .m = m, .wx = 2.0 * win.x - col, .wy = 2.0 * win.y - row, .ws = 2.0 * win.s, .maxoct = maxoct };
        const bm = draw(&subs[q], 0) orelse {
            say("refused: the Quad's procedure {d} does not draw\n", .{q + 1});
            return null;
        };
        // a copy of its own: the memory of drawn pictures may be cleared by the next procedure's drawing
        const cp = wzb_new(@intCast(cw), @intCast(cw)) orelse die("out of memory", .{});
        @memcpy(wzb_data(cp)[0 .. cw * cw * 4], wzb_data(bm)[0 .. cw * cw * 4]);
        parts[q] = cp;
    }
    modern.c.cv = .{ .w = cw, .h = cw, .m = m, .wx = win.x, .wy = win.y, .ws = win.s, .maxoct = maxoct };
    var out: ?*anyopaque = null;
    var err: [300]u8 = [_]u8{0} ** 300;
    var w: [32]u32 = [_]u32{0} ** 32;
    const nk = wordsOf(&rt);
    for (0..nk) |p| w[p] = rt.w[p];
    const r = modern.apply(modern.K_QUAD, w[0..nk], parts[0..4], &out, &err);
    if (r != 0) {
        say("refused: Quad: {s}\n", .{std.mem.sliceTo(&err, 0)});
        return null;
    }
    // into the memory of drawn pictures, so it is freed with them
    quad_serial += 1;
    cachePut(mix(0x51ad0001, quad_serial), out);
    return out;
}
var quad_serial: u64 = 0;

pub fn isGrid(op: u8) bool {
    return op == OP_MODERN + modern.K_GRID;
}
pub fn isStack(op: u8) bool {
    return op == OP_MODERN + modern.K_STACK;
}

/// the widest margin any of the given procedures needs on a canvas whose pixels are pxs parts of their own picture
fn marginFor(sub: *const Graph, pxs: f32) usize {
    var reach: f32 = 0;
    var any = false;
    for (sub.nodes[0 .. sub.root + 1]) |nd| {
        if (!isModern(nd.op)) continue;
        const r = modern.marginOf(nd.op - OP_MODERN, nd.w[0..wordsOf(&nd)]);
        if (r > 0) any = true;
        reach += r;
    }
    return if (any) @as(usize, @intFromFloat(@ceil(reach / pxs))) + 2 else 0;
}

/// More procedures per picture (milestone 2e): a Grid's cols * rows inputs, input q (row q / cols, column q % cols)
/// drawn on its own canvas at the places s (x - col / cols), s (y - row / rows), s the smaller of cols and rows, every
/// canvas of one side and margin; then the Grid lays them together with its seam (Quad's rule for any count).
fn drawGrid(g: *const Graph, side: usize, win: Win, maxoct: u32) ?*anyopaque {
    const rt = g.nodes[g.root];
    const cols: usize = @intCast(rt.w[1]);
    const rows: usize = @intCast(rt.w[2]);
    const nt = cols * rows;
    if (cols < 1 or rows < 1 or cols > 4 or rows > 4 or rt.nin != nt) {
        say("refused: a Grid of {d} by {d} tiles takes {d} procedures, the graph gives {d}\n", .{ cols, rows, nt, rt.nin });
        return null;
    }
    const sc = modern.grid.scaleOf(cols, rows);
    const subs = alloc.alloc(Graph, nt) catch die("out of memory", .{});
    defer alloc.free(subs);
    const pxs = sc * win.s / @as(f32, @floatFromInt(side));
    var m: usize = 0;
    for (0..nt) |q| {
        subs[q] = quadPart(g, q);
        for (subs[q].nodes[0 .. subs[q].root + 1]) |nd| {
            if (isQuad(nd.op) or isGrid(nd.op) or isStack(nd.op)) {
                say("refused: a Grid's inputs hold a {s} (one Grid per procedure, its last operator; a Stack may lay Grids)\n", .{ops[nd.op].name});
                return null;
            }
        }
        m = @max(m, marginFor(&subs[q], pxs));
    }
    m = (m + 1) & ~@as(usize, 1);
    const cw = side + 2 * m;
    var parts: [modern.grid.MAXT]?*anyopaque = [_]?*anyopaque{null} ** modern.grid.MAXT;
    defer for (parts) |p| {
        if (p != null) wzb_free(p);
    };
    for (0..nt) |q| {
        const col: f32 = @floatFromInt(q % cols);
        const row: f32 = @floatFromInt(q / cols);
        const fc: f32 = @floatFromInt(cols);
        const fr: f32 = @floatFromInt(rows);
        modern.c.cv = .{ .w = cw, .h = cw, .m = m, .wx = sc * (win.x - col / fc), .wy = sc * (win.y - row / fr), .ws = sc * win.s, .maxoct = maxoct };
        const bm = draw(&subs[q], 0) orelse {
            say("refused: the Grid's procedure {d} does not draw\n", .{q + 1});
            return null;
        };
        const cp = wzb_new(@intCast(cw), @intCast(cw)) orelse die("out of memory", .{});
        @memcpy(wzb_data(cp)[0 .. cw * cw * 4], wzb_data(bm)[0 .. cw * cw * 4]);
        parts[q] = cp;
        // the tile's own pictures are not needed again: up to sixteen procedures' worth would fill the memory of
        // drawn pictures (a 2 by 4 Grid at 2048 ran out of WebAssembly's memory)
        cacheClear();
    }
    modern.c.cv = .{ .w = cw, .h = cw, .m = m, .wx = win.x, .wy = win.y, .ws = win.s, .maxoct = maxoct };
    var out: ?*anyopaque = null;
    var err: [300]u8 = [_]u8{0} ** 300;
    var w: [32]u32 = [_]u32{0} ** 32;
    const nk = wordsOf(&rt);
    for (0..nk) |p| w[p] = rt.w[p];
    const r = modern.apply(modern.K_GRID, w[0..nk], parts[0..nt], &out, &err);
    if (r != 0) {
        say("refused: Grid: {s}\n", .{std.mem.sliceTo(&err, 0)});
        return null;
    }
    quad_serial += 1;
    cachePut(mix(0x51ad0002, quad_serial), out);
    return out;
}

/// Results laid over each other (milestone 2e): a Stack's inputs, each a whole procedure (a Quad or a Grid among
/// them), drawn over the same window, their inner pixels copied to canvases without a margin; then the Stack lays
/// them, the bottom one first. The Stack's own canvas has no margin.
fn drawStack(g: *const Graph, side: usize, win: Win, maxoct: u32) ?*anyopaque {
    const rt = g.nodes[g.root];
    if (rt.nin < 2 or rt.nin > modern.stack.MAXL) {
        say("refused: a Stack lays two to four procedures, the graph gives {d}\n", .{rt.nin});
        return null;
    }
    var parts: [modern.stack.MAXL]?*anyopaque = [_]?*anyopaque{null} ** modern.stack.MAXL;
    defer for (parts) |p| {
        if (p != null) wzb_free(p);
    };
    for (0..rt.nin) |q| {
        var sub = quadPart(g, q);
        for (sub.nodes[0..sub.root]) |nd| {
            if (isStack(nd.op)) {
                say("refused: a Stack's procedure {d} holds another Stack (one Stack per procedure, its last operator)\n", .{q + 1});
                return null;
            }
        }
        if (isStack(sub.nodes[sub.root].op)) {
            say("refused: a Stack's procedure {d} is another Stack\n", .{q + 1});
            return null;
        }
        const bm = drawCanvas(&sub, side, win, maxoct) orelse {
            say("refused: the Stack's procedure {d} does not draw\n", .{q + 1});
            return null;
        };
        const cv = modern.c.cv;
        const cp = wzb_new(@intCast(side), @intCast(side)) orelse die("out of memory", .{});
        const src = wzb_data(bm);
        const dst = wzb_data(cp);
        for (0..side) |j| {
            const a = ((j + cv.m) * cv.w + cv.m) * 4;
            @memcpy(dst[j * side * 4 .. (j + 1) * side * 4], src[a .. a + side * 4]);
        }
        parts[q] = cp;
        cacheClear();
    }
    modern.c.cv = .{ .w = side, .h = side, .m = 0, .wx = win.x, .wy = win.y, .ws = win.s, .maxoct = maxoct };
    var out: ?*anyopaque = null;
    var err: [300]u8 = [_]u8{0} ** 300;
    var w: [32]u32 = [_]u32{0} ** 32;
    const nk = wordsOf(&rt);
    for (0..nk) |p| w[p] = rt.w[p];
    const r = modern.apply(modern.K_STACK, w[0..nk], parts[0..rt.nin], &out, &err);
    if (r != 0) {
        say("refused: Stack: {s}\n", .{std.mem.sliceTo(&err, 0)});
        return null;
    }
    quad_serial += 1;
    cachePut(mix(0x51ad0003, quad_serial), out);
    return out;
}

/// a procedure's mean colour, drawn alone on its own canvas at 256 pixels (the smooth seam's field passes through it)
fn meanWord(sub: *const Graph, what: []const u8) u32 {
    const side: usize = 256;
    const rgba = alloc.alloc(u8, side * side * 4) catch die("out of memory", .{});
    defer alloc.free(rgba);
    const bm = drawCanvas(sub, side, .{}, 99) orelse die("{s} does not draw", .{what});
    cropRgba(bm, rgba);
    var s = [3]f64{ 0, 0, 0 };
    for (0..side * side) |k| {
        inline for (0..3) |ch| s[ch] += @floatFromInt(rgba[4 * k + ch]);
    }
    var word: u32 = 0xff000000;
    inline for (0..3) |ch| {
        const v: u32 = @intFromFloat(@floor(s[ch] / @as(f64, @floatFromInt(side * side)) + 0.5));
        word |= @as(u32, @min(v, 255)) << (16 - 8 * ch);
    }
    return word;
}

fn sameNode(a: *const Node, b: *const Node) bool {
    if (a.op != b.op or a.nin != b.nin) return false;
    if (!std.mem.eql(u8, a.in[0..a.nin], b.in[0..b.nin])) return false;
    const na = wordsOf(a);
    if (na != wordsOf(b) or !std.mem.eql(u32, a.w[0..na], b.w[0..na])) return false;
    return std.mem.eql(u16, &a.s, &b.s);
}

/// copy a procedure's nodes into g after its own; the root's new place. A node equal to one already in g (the same
/// operator, words and inputs: two layers built on one structure share it) is stored once (milestone 2e).
fn appendGraph(g: *Graph, sub: *const Graph, what: []const u8) usize {
    var map: [MAXN]u8 = undefined;
    for (sub.nodes[0..sub.n], 0..) |nd0, i| {
        var nd = nd0;
        for (nd.in[0..nd.nin]) |*v| v.* = map[v.*];
        var found: ?usize = null;
        for (g.nodes[0..g.n], 0..) |*x, k| {
            if (sameNode(x, &nd)) {
                found = k;
                break;
            }
        }
        if (found) |k| {
            map[i] = @intCast(k);
            continue;
        }
        if (g.n + 2 > MAXN) die("{s}: the procedures hold more than {d} operators", .{ what, MAXN - 1 });
        g.nodes[g.n] = nd;
        map[i] = @intCast(g.n);
        g.n += 1;
    }
    return map[sub.root];
}

/// p2p grid: cols * rows tiles' procedures (row by row from the top left) joined under a Grid, each one's mean
/// colour measured on its own canvas
fn gridJoin(out: []const u8, cols: usize, rows: usize, paths: []const [*:0]const u8, seam: u32, band: f32) void {
    const nt = cols * rows;
    if (paths.len != nt) die("grid: {d} by {d} tiles take {d} procedures, {d} given", .{ cols, rows, nt, paths.len });
    var g = alloc.create(Graph) catch die("out of memory", .{});
    g.* = Graph{};
    var gn = Node{ .op = @intCast(OP_MODERN + modern.K_GRID), .nin = @intCast(nt), .nw = @intCast(modern.grid.params.len) };
    gn.w[0] = 1;
    gn.w[1] = @intCast(cols);
    gn.w[2] = @intCast(rows);
    gn.w[3] = seam;
    gn.w[4] = @bitCast(band);
    for (5..modern.grid.params.len) |k| gn.w[k] = 0xff808080;
    for (0..nt) |q| {
        var sub = parseScript(readFile(paths[q]));
        sub.prune();
        if (isQuad(sub.nodes[sub.root].op) or isGrid(sub.nodes[sub.root].op) or isStack(sub.nodes[sub.root].op)) die("grid: {s} is already a {s}", .{ paths[q], ops[sub.nodes[sub.root].op].name });
        gn.w[5 + q] = meanWord(&sub, "grid: a tile's procedure");
        gn.in[q] = @intCast(appendGraph(g, &sub, "grid"));
        say("tile {d} (row {d}, column {d}): {d} operators, {d} bytes, mean colour {x:0>6}\n", .{ q + 1, q / cols, q % cols, sub.n, sub.bytes(), gn.w[5 + q] & 0xffffff });
    }
    g.nodes[g.n] = gn;
    g.root = g.n;
    g.n += 1;
    var buf: [1 << 18]u8 = undefined;
    writeFile(out, scriptText(g, &buf));
    say("grid: {d} by {d}, {d} operators, {d} bytes (seam {s}, band {d:.3})\n", .{ cols, rows, g.n, g.bytes(), ([_][]const u8{ "cut", "mix", "keep", "smooth" })[seam], band });
}

pub const StackLayer = struct { mode: u32 = 0, amount: f32 = 0.5, lo: f32 = 0.4, hi: f32 = 0.6 };

/// p2p stack: two to four whole procedures (the bottom one first) joined under a Stack with each upper layer's mask
fn stackJoin(out: []const u8, paths: []const [*:0]const u8, lay: []const StackLayer) void {
    if (paths.len < 2 or paths.len > modern.stack.MAXL) die("stack: two to four procedures, {d} given", .{paths.len});
    var g = alloc.create(Graph) catch die("out of memory", .{});
    g.* = Graph{};
    var sn = Node{ .op = @intCast(OP_MODERN + modern.K_STACK), .nin = @intCast(paths.len), .nw = @intCast(modern.stack.params.len) };
    sn.w[0] = 1;
    for (1..modern.stack.MAXL) |l| {
        const L = if (l < lay.len) lay[l] else StackLayer{};
        sn.w[1 + 4 * (l - 1)] = L.mode;
        sn.w[2 + 4 * (l - 1)] = @bitCast(L.amount);
        sn.w[3 + 4 * (l - 1)] = @bitCast(L.lo);
        sn.w[4 + 4 * (l - 1)] = @bitCast(L.hi);
    }
    const mn = [_][]const u8{ "alpha", "height", "dark", "light" };
    for (paths, 0..) |p, q| {
        var sub = parseScript(readFile(p));
        sub.prune();
        if (isStack(sub.nodes[sub.root].op)) die("stack: {s} is already a Stack", .{p});
        sn.in[q] = @intCast(appendGraph(g, &sub, "stack"));
        if (q == 0) {
            say("layer 1 (bottom): {s}, {d} operators, {d} bytes\n", .{ p, sub.n, sub.bytes() });
        } else say("layer {d}: {s}, {d} operators, {d} bytes; laid by {s}, amount {d:.2}, from {d:.3} to {d:.3}\n", .{ q + 1, p, sub.n, sub.bytes(), mn[lay[q].mode], lay[q].amount, lay[q].lo, lay[q].hi });
    }
    g.nodes[g.n] = sn;
    g.root = g.n;
    g.n += 1;
    var buf: [1 << 18]u8 = undefined;
    writeFile(out, scriptText(g, &buf));
    say("stack: {d} layers, {d} operators, {d} bytes\n", .{ paths.len, g.n, g.bytes() });
}

/// p2p quad: the four quarters' procedures joined into one graph under a Quad, each input's mean colour measured
/// on its own canvas (at 256 pixels) for the seam that keeps the contrast
fn quadJoin(out: []const u8, paths: [4][*:0]const u8, seam: u32, band: f32) void {
    var g = alloc.create(Graph) catch die("out of memory", .{});
    g.* = Graph{};
    var roots: [4]usize = undefined;
    var means: [4]u32 = undefined;
    const names = [_][]const u8{ "top left", "top right", "bottom left", "bottom right" };
    const side: usize = 256;
    const rgba = alloc.alloc(u8, side * side * 4) catch die("out of memory", .{});
    defer alloc.free(rgba);
    for (0..4) |q| {
        var sub = parseScript(readFile(paths[q]));
        sub.prune();
        if (isQuad(sub.nodes[sub.root].op)) die("quad: {s} is already a Quad", .{paths[q]});
        const bm = drawCanvas(&sub, side, .{}, 99) orelse die("quad: the {s} procedure ({s}) does not draw", .{ names[q], paths[q] });
        cropRgba(bm, rgba);
        var s = [3]f64{ 0, 0, 0 };
        for (0..side * side) |k| {
            inline for (0..3) |ch| s[ch] += @floatFromInt(rgba[4 * k + ch]);
        }
        var word: u32 = 0xff000000;
        inline for (0..3) |ch| {
            const v: u32 = @intFromFloat(@floor(s[ch] / @as(f64, @floatFromInt(side * side)) + 0.5));
            word |= @as(u32, @min(v, 255)) << (16 - 8 * ch);
        }
        means[q] = word;
        const off = g.n;
        if (off + sub.n + 1 > MAXN) die("quad: the four procedures hold more than {d} operators", .{MAXN - 1});
        for (sub.nodes[0..sub.n]) |nd0| {
            var nd = nd0;
            for (nd.in[0..nd.nin]) |*v| v.* = @intCast(@as(usize, v.*) + off);
            g.nodes[g.n] = nd;
            g.n += 1;
        }
        roots[q] = off + sub.root;
        say("{s}: {d} operators, {d} bytes, mean colour {x:0>6}\n", .{ names[q], sub.n, sub.bytes(), word & 0xffffff });
    }
    var qn = Node{ .op = @intCast(OP_MODERN + modern.K_QUAD), .nin = 4, .nw = 7 };
    qn.w[0] = 1;
    qn.w[1] = seam;
    qn.w[2] = @bitCast(band);
    for (0..4) |q| {
        qn.w[3 + q] = means[q];
        qn.in[q] = @intCast(roots[q]);
    }
    g.nodes[g.n] = qn;
    g.root = g.n;
    g.n += 1;
    var buf: [1 << 17]u8 = undefined;
    writeFile(out, scriptText(g, &buf));
    say("quad: {d} operators, {d} bytes (seam {s}, band {d:.3})\n", .{ g.n, g.bytes(), ([_][]const u8{ "cut", "mix", "keep", "smooth" })[seam], band });
}

pub fn cropRgba(bm: ?*anyopaque, rgba: []u8) void {
    const cv = modern.c.cv;
    const full = alloc.alloc(u8, cv.w * cv.h * 4) catch die("out of memory", .{});
    defer alloc.free(full);
    wzb_rgba(bm, full.ptr);
    const side = cv.w - 2 * cv.m;
    for (0..side) |j| {
        const a = ((j + cv.m) * cv.w + cv.m) * 4;
        @memcpy(rgba[j * side * 4 .. (j + 1) * side * 4], full[a .. a + side * 4]);
    }
}

/// the material's height (alpha), 16 bits per pixel as a PGM (the 15-bit value times two): the relief milestone 3's
/// stereo reads, at the drawing's own size
fn writeHeight(path: []const u8, bm: ?*anyopaque) void {
    const cv = modern.c.cv;
    const side = cv.w - 2 * cv.m;
    const d = modern.c.Pix{ .d = wzb_data16(bm), .w = cv.w, .h = cv.h };
    var out = alloc.alloc(u8, 32 + side * side * 2) catch die("out of memory", .{});
    defer alloc.free(out);
    const hd = std.fmt.bufPrint(out[0..32], "P5\n{d} {d}\n65535\n", .{ side, side }) catch unreachable;
    for (0..side) |j| {
        for (0..side) |i| {
            const v: u32 = @as(u32, d.d[4 * ((j + cv.m) * cv.w + i + cv.m) + 3]) * 2;
            const o = hd.len + 2 * (j * side + i);
            out[o] = @intCast(v >> 8);
            out[o + 1] = @intCast(v & 0xff);
        }
    }
    writeFile(path, out[0 .. hd.len + side * side * 2]);
}
extern "c" fn wzb_data(p: ?*anyopaque) [*]u16;
fn wzb_data16(p: ?*anyopaque) [*]u16 {
    return wzb_data(p);
}

fn argStr(argv: [*]const [*:0]const u8, i: usize) []const u8 {
    return std.mem.span(argv[i]);
}

// The entry: the C library's start calls main natively; for WebAssembly, p2p_wasm.zig is the root and gives the same
// function the name WASI's start (wasi-libc's crt1-command) calls, __main_argc_argv (lane 514's finding).
pub export fn main(argc: c_int, argv: [*]const [*:0]const u8) c_int {
    return mainC(argc, argv);
}

pub fn mainC(argc: c_int, argv: [*]const [*:0]const u8) callconv(.c) c_int {
    const n: usize = @intCast(argc);
    wzb_init();
    makeFilters();
    wzb_set_limit(@as(usize, 3) << 30);
    cache = alloc.alloc(Slot, CACHE) catch die("out of memory", .{});
    for (cache) |*s| s.* = .{};
    if (n >= 2 and std.mem.eql(u8, argStr(argv, 1), "kinds")) {
        // p2p kinds: every operator's packing (i whole number, f decimal, c colour), werkkzeug3's then the modern ones
        for (ops) |o| say("{s} {s}\n", .{ o.name, o.kinds });
        return 0;
    }
    if (n >= 3 and std.mem.eql(u8, argStr(argv, 1), "fontindex")) {
        // p2p fontindex SOURCE=FOLDER ... > index.tsv   (sources in the order their copies are preferred)
        return fi_index(@intCast(n - 2), @constCast(argv + 2));
    }
    if (n >= 3 and std.mem.eql(u8, argStr(argv, 1), "glyphindex")) {
        // p2p glyphindex OUT.bin [k n]   (the fonts of WZ_FONTINDEX; with k n, every n-th font from the k-th)
        const k: c_int = if (n >= 5) std.fmt.parseInt(c_int, argStr(argv, 3), 10) catch die("bad shard", .{}) else 0;
        const m: c_int = if (n >= 5) std.fmt.parseInt(c_int, argStr(argv, 4), 10) catch die("bad shard count", .{}) else 1;
        return gi_build(argv[2], k, m);
    }
    if (n >= 4 and std.mem.eql(u8, argStr(argv, 1), "mfit")) {
        // p2p mfit WHOLE.ppm OUT-PREFIX [full=FULL.ppm] [tile=512] [close=0] [off=grain,...]   (milestone 2b: the modern operators,
        // the whole first; milestone 2c: the close-up layers, read on the full-size picture)
        var mo = mfit.MOpt{};
        for (4..n) |i| {
            const a = argStr(argv, i);
            if (std.mem.startsWith(u8, a, "full=")) {
                mo.full = argv[i] + 5;
            } else if (std.mem.startsWith(u8, a, "tile=")) {
                mo.tile = std.fmt.parseInt(usize, a[5..], 10) catch die("bad {s}", .{a});
            } else if (std.mem.startsWith(u8, a, "seeds=")) {
                mo.seeds = argv[i] + 6;
            } else if (std.mem.startsWith(u8, a, "light=")) {
                mo.light = a[6] == '1';
            } else if (std.mem.startsWith(u8, a, "close=")) {
                mo.close = a[6] == '1';
            } else if (std.mem.startsWith(u8, a, "off=")) {
                mo.off = a[4..];
            } else if (std.mem.eql(u8, a, "grainat=field")) {
                mo.grain_in_field = true;
            } else if (std.mem.eql(u8, a, "grainat=colour")) {
                mo.grain_in_field = false;
            } else if (std.mem.startsWith(u8, a, "seed=")) {
                mo.seed = std.fmt.parseInt(i32, a[5..], 10) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, a, "joints=scan")) {
                mo.joints_full = false;
            } else if (std.mem.eql(u8, a, "joints=full")) {
                mo.joints_full = true;
            } else if (std.mem.startsWith(u8, a, "pairs=")) {
                mo.pairs = a[6] == '1';
            } else if (std.mem.startsWith(u8, a, "framed=")) {
                mo.framed = a[7] == '1';
            } else if (std.mem.startsWith(u8, a, "on=")) {
                mo.on = a[3..];
            } else if (std.mem.eql(u8, a, "marks=fixed")) {
                mo.marks_soft = false;
            } else if (std.mem.eql(u8, a, "marks=read")) {
                mo.marks_soft = true;
            } else if (std.mem.eql(u8, a, "grainfit=closest")) {
                mo.grain_cap = false;
            } else if (std.mem.eql(u8, a, "struct=none")) {
                mo.struct_none = true;
            } else if (std.mem.startsWith(u8, a, "struct=")) {
                // struct=WHOLE.script,COLS,ROWS,COL,ROW: the tile's structure is the whole picture's (milestone 2e)
                var it = std.mem.tokenizeScalar(u8, a[7..], ',');
                const path = it.next() orelse die("struct=WHOLE.script,COLS,ROWS,COL,ROW", .{});
                mo.struct_cols = std.fmt.parseInt(usize, it.next() orelse die("struct=WHOLE.script,COLS,ROWS,COL,ROW", .{}), 10) catch die("bad {s}", .{a});
                mo.struct_rows = std.fmt.parseInt(usize, it.next() orelse die("struct=WHOLE.script,COLS,ROWS,COL,ROW", .{}), 10) catch die("bad {s}", .{a});
                mo.struct_col = std.fmt.parseInt(usize, it.next() orelse die("struct=WHOLE.script,COLS,ROWS,COL,ROW", .{}), 10) catch die("bad {s}", .{a});
                mo.struct_row = std.fmt.parseInt(usize, it.next() orelse die("struct=WHOLE.script,COLS,ROWS,COL,ROW", .{}), 10) catch die("bad {s}", .{a});
                const z = alloc.allocSentinel(u8, path.len, 0) catch die("out of memory", .{});
                @memcpy(z, path);
                mo.struct_from = z.ptr;
            } else if (std.mem.eql(u8, a, "jointwarp=keep")) {
                mo.joint_wobble = false;
            } else if (std.mem.eql(u8, a, "jointwarp=quarter")) {
                mo.joint_wobble = true;
            } else if (std.mem.eql(u8, a, "bands=7")) {
                mo.bands_all = false;
            } else if (std.mem.eql(u8, a, "bands=all")) {
                mo.bands_all = true;
            } else if (std.mem.eql(u8, a, "grainfit=cap")) {
                mo.grain_cap = true;
            } else die("mfit: {s} is not known (full=FULL.ppm, tile=SIDE, seeds=CHOSEN, light=0|1, close=0|1, off=LAYER,..., grainat=colour|field, seed=N, joints=full|scan, pairs=0|1, framed=0|1, grainfit=cap|closest, on=LAYER,..., marks=read|fixed, bands=all|7, struct=WHOLE.script,COLS,ROWS,COL,ROW, jointwarp=quarter|keep)", .{a});
        }
        mfit.run(argv[2], argStr(argv, 3), mo);
        return 0;
    }
    if (n >= 7 and std.mem.eql(u8, argStr(argv, 1), "quad")) {
        // p2p quad OUT.script TL.script TR.script BL.script BR.script [seam=cut|mix|keep] [band=B]   (milestone 2d: four
        // procedures, each fitted to one quarter of the picture as a picture of its own, laid together by a Quad)
        var seam: u32 = 3;
        var band: f32 = 0.03;
        for (7..n) |i| {
            const a = argStr(argv, i);
            if (std.mem.eql(u8, a, "seam=cut")) {
                seam = 0;
            } else if (std.mem.eql(u8, a, "seam=mix")) {
                seam = 1;
            } else if (std.mem.eql(u8, a, "seam=keep")) {
                seam = 2;
            } else if (std.mem.eql(u8, a, "seam=smooth")) {
                seam = 3;
            } else if (std.mem.startsWith(u8, a, "band=")) {
                band = std.fmt.parseFloat(f32, a[5..]) catch die("bad {s}", .{a});
            } else die("quad: {s} is not known (seam=cut|mix|keep|smooth, band=PARTS-OF-THE-PICTURE)", .{a});
        }
        say_refusals = true;
        quadJoin(argStr(argv, 2), .{ argv[3], argv[4], argv[5], argv[6] }, seam, band);
        return 0;
    }
    if (n >= 6 and std.mem.eql(u8, argStr(argv, 1), "grid")) {
        // p2p grid OUT.script COLS ROWS TILE.script... [seam=cut|mix|keep|smooth] [band=B]   (milestone 2e: cols by rows
        // procedures, each fitted to one tile of the picture, row by row from the top left)
        const cols = std.fmt.parseInt(usize, argStr(argv, 3), 10) catch die("grid: COLS is a whole number", .{});
        const rows = std.fmt.parseInt(usize, argStr(argv, 4), 10) catch die("grid: ROWS is a whole number", .{});
        if (cols < 1 or cols > 4 or rows < 1 or rows > 4) die("grid: 1 to 4 columns and rows", .{});
        var seam: u32 = 3;
        var band: f32 = 0.03;
        var paths: [16][*:0]const u8 = undefined;
        var np: usize = 0;
        for (5..n) |i| {
            const a = argStr(argv, i);
            if (std.mem.eql(u8, a, "seam=cut")) {
                seam = 0;
            } else if (std.mem.eql(u8, a, "seam=mix")) {
                seam = 1;
            } else if (std.mem.eql(u8, a, "seam=keep")) {
                seam = 2;
            } else if (std.mem.eql(u8, a, "seam=smooth")) {
                seam = 3;
            } else if (std.mem.startsWith(u8, a, "band=")) {
                band = std.fmt.parseFloat(f32, a[5..]) catch die("bad {s}", .{a});
            } else if (std.mem.indexOfScalar(u8, a, '=') != null) {
                die("grid: {s} is not known (seam=cut|mix|keep|smooth, band=PARTS-OF-THE-PICTURE)", .{a});
            } else {
                if (np >= 16) die("grid: more than 16 procedures", .{});
                paths[np] = argv[i];
                np += 1;
            }
        }
        say_refusals = true;
        gridJoin(argStr(argv, 2), cols, rows, paths[0..np], seam, band);
        return 0;
    }
    if (n >= 5 and std.mem.eql(u8, argStr(argv, 1), "stack")) {
        // p2p stack OUT.script BOTTOM.script [mask=alpha|height|dark|light amount=A lo=L hi=H] LAYER.script ...
        // (milestone 2e: whole procedures laid over each other; the options before a layer's script are that layer's)
        var paths: [4][*:0]const u8 = undefined;
        var lay: [4]StackLayer = [_]StackLayer{.{}} ** 4;
        var cur = StackLayer{};
        var np: usize = 0;
        for (3..n) |i| {
            const a = argStr(argv, i);
            if (std.mem.startsWith(u8, a, "mask=")) {
                const v = a[5..];
                cur.mode = if (std.mem.eql(u8, v, "alpha")) 0 else if (std.mem.eql(u8, v, "height")) 1 else if (std.mem.eql(u8, v, "dark")) 2 else if (std.mem.eql(u8, v, "light")) 3 else die("stack: mask={s} is not known (alpha, height, dark, light)", .{v});
            } else if (std.mem.startsWith(u8, a, "amount=")) {
                cur.amount = std.fmt.parseFloat(f32, a[7..]) catch die("bad {s}", .{a});
            } else if (std.mem.startsWith(u8, a, "lo=")) {
                cur.lo = std.fmt.parseFloat(f32, a[3..]) catch die("bad {s}", .{a});
            } else if (std.mem.startsWith(u8, a, "hi=")) {
                cur.hi = std.fmt.parseFloat(f32, a[3..]) catch die("bad {s}", .{a});
            } else if (std.mem.indexOfScalar(u8, a, '=') != null) {
                die("stack: {s} is not known (mask=alpha|height|dark|light, amount=A, lo=L, hi=H before a layer's script)", .{a});
            } else {
                if (np >= 4) die("stack: more than four procedures", .{});
                if (np == 0 and (cur.mode != 0 or cur.amount != 0.5)) die("stack: the bottom procedure is laid on nothing; give a layer's mask and amount before the layer's own script", .{});
                paths[np] = argv[i];
                lay[np] = cur;
                cur = StackLayer{};
                np += 1;
            }
        }
        say_refusals = true;
        stackJoin(argStr(argv, 2), paths[0..np], lay[0..np]);
        return 0;
    }
    if (n >= 4 and std.mem.eql(u8, argStr(argv, 1), "seed")) {
        // p2p seed WHOLE.ppm OUT.seed   (the glyph index of WZ_GLYPHINDEX and WZ_FONTINDEX)
        seedRead(argv[2], argStr(argv, 3));
        return 0;
    }
    if (n >= 4 and std.mem.eql(u8, argStr(argv, 1), "render")) {
        // p2p render SCRIPT OUT.ppm [SIZE-EXPONENT] [window=X,Y,SIDE] [lod=OCTAVES] [height=OUT.pgm]
        const g = parseScript(readFile(argv[2]));
        const size: u32 = if (n > 4) std.fmt.parseInt(u32, argStr(argv, 4), 10) catch 0 else 0;
        say_refusals = true;
        if (hasModern(&g)) {
            var win = Win{};
            var lod: u32 = 99;
            var hpath: ?[]const u8 = null;
            for (5..n) |i| {
                const a = argStr(argv, i);
                if (std.mem.startsWith(u8, a, "window=")) {
                    var it = std.mem.tokenizeScalar(u8, a[7..], ',');
                    win.x = std.fmt.parseFloat(f32, it.next() orelse die("window=X,Y,SIDE", .{})) catch die("bad {s}", .{a});
                    win.y = std.fmt.parseFloat(f32, it.next() orelse die("window=X,Y,SIDE", .{})) catch die("bad {s}", .{a});
                    win.s = std.fmt.parseFloat(f32, it.next() orelse die("window=X,Y,SIDE", .{})) catch die("bad {s}", .{a});
                } else if (std.mem.startsWith(u8, a, "lod=")) {
                    lod = std.fmt.parseInt(u32, a[4..], 10) catch die("bad {s}", .{a});
                } else if (std.mem.startsWith(u8, a, "height=")) {
                    hpath = a[7..];
                } else die("render: {s} is not known (window=X,Y,SIDE, lod=OCTAVES, height=OUT.pgm)", .{a});
            }
            if (size == 0) die("render: a procedure of modern operators is drawn at the size asked for: give the size exponent (9 is 512 pixels)", .{});
            const side = @as(usize, 1) << @intCast(size);
            const bm = drawCanvas(&g, side, win, lod) orelse die("the procedure does not draw", .{});
            const rgba = alloc.alloc(u8, side * side * 4) catch die("out of memory", .{});
            cropRgba(bm, rgba);
            writePpm(argStr(argv, 3), rgba, side, side);
            if (hpath) |hp| writeHeight(hp, bm);
            sayNotes();
            say("{d} operators, {d} bytes, {d}x{d}, window {d},{d} side {d}, margin {d}\n", .{ g.n, g.bytes(), side, side, win.x, win.y, win.s, modern.c.cv.m });
            return 0;
        }
        const bm = draw(&g, size) orelse die("the procedure does not draw", .{});
        const w: usize = @intCast(wzb_width(bm));
        const h: usize = @intCast(wzb_height(bm));
        const rgba = alloc.alloc(u8, w * h * 4) catch die("out of memory", .{});
        wzb_rgba(bm, rgba.ptr);
        writePpm(argStr(argv, 3), rgba, w, h);
        sayNotes();
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
                opt.structure = std.meta.stringToEnum(Structure, v) orelse die("structure {s} is not known (plain, shape, patches, second, grain, rings, mirror, text, seed)", .{v});
            } else if (std.mem.eql(u8, k, "surface2")) {
                opt.surface2 = v[0] == '1';
            } else if (std.mem.eql(u8, k, "blur")) {
                opt.blur = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "stretch")) {
                opt.stretch = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "jointw")) {
                opt.jointw = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "whole")) {
                opt.whole = argv[i] + eq + 1;
            } else if (std.mem.eql(u8, k, "window")) {
                var it = std.mem.tokenizeScalar(u8, v, ',');
                opt.win.x = std.fmt.parseFloat(f32, it.next() orelse die("window=X,Y,SIDE", .{})) catch die("bad {s}", .{a});
                opt.win.y = std.fmt.parseFloat(f32, it.next() orelse die("window=X,Y,SIDE", .{})) catch die("bad {s}", .{a});
                opt.win.s = std.fmt.parseFloat(f32, it.next() orelse die("window=X,Y,SIDE", .{})) catch die("bad {s}", .{a});
            } else if (std.mem.eql(u8, k, "fix")) {
                opt.fix = v[0] == '1';
            } else if (std.mem.eql(u8, k, "fromfree")) {
                opt.from_free = v[0] == '1';
            } else if (std.mem.eql(u8, k, "from")) {
                opt.from = argv[i] + eq + 1;
            } else if (std.mem.eql(u8, k, "seeds")) {
                opt.seedfile = argv[i] + eq + 1;
            } else if (std.mem.eql(u8, k, "glyph")) {
                glyph_t = std.fmt.parseFloat(f32, v) catch die("bad {s}", .{a});
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
