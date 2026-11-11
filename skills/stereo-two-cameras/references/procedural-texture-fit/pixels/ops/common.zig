//! What every modern operator shares (ORDER 508, milestone 2b; our code, BSD 2-clause like Farbrausch's tree).
//!
//! The operators are pure functions of the place they draw and of their parameter words: no state between
//! pixels beyond what one more pass over a picture holds, every loop bounded by a parameter, no maths library
//! call (no sin, cos, pow or exp: plain + - * /, sqrt and floor, which IEEE 754 rounds the same everywhere), so a
//! WGSL twin follows line for line and the WebAssembly build draws the same bytes as the native one.
//!
//! Places are in parts of the whole picture (0 to 1 across and down, repeating), never in pixels: a tile is the
//! same procedure drawn over a window of the picture, so a tile's noise has the picture's frequencies, its light
//! stands where the picture's stands, and neighbouring tiles meet without a seam.
//! Pictures are werkkzeug's: four 15-bit channels per pixel (blue, green, red, alpha; 0 to 0x7fff). A material
//! carries its colour in red, green and blue and its height (the relief) in alpha.
const std = @import("std");

/// Where a picture is drawn: w by h pixels, of which m on each side are a margin that neighbourhood operators read
/// (Shade, Wear) and that is cut away at the end; the inner pixels show the window wx, wy (its top left corner) of
/// side ws, in parts of the whole picture.
pub const Canvas = struct {
    w: usize = 512,
    h: usize = 512,
    m: usize = 0,
    wx: f32 = 0,
    wy: f32 = 0,
    ws: f32 = 1,
    /// the most octaves any noise draws (the level of detail a coarser rung asks for); 99: all
    maxoct: u32 = 99,

    pub fn inner(c: *const Canvas) f32 {
        return @floatFromInt(c.w - 2 * c.m);
    }
    /// the size of one pixel in parts of the picture
    pub fn px(c: *const Canvas) f32 {
        return c.ws / c.inner();
    }
    pub fn u(c: *const Canvas, i: usize) f32 {
        return c.wx + (@as(f32, @floatFromInt(i)) - @as(f32, @floatFromInt(c.m)) + 0.5) * c.px();
    }
    pub fn v(c: *const Canvas, j: usize) f32 {
        return c.wy + (@as(f32, @floatFromInt(j)) - @as(f32, @floatFromInt(c.m)) + 0.5) * c.px();
    }
};

pub var cv: Canvas = .{};

pub const Pix = struct {
    d: [*]u16,
    w: usize,
    h: usize,
};

pub const Kind = enum { int, float, rgba, cycle };

/// One parameter word, in the shape of Stereo Werkkzeug's operator table (lane 514's Param: kind, label, the
/// word it is stored in, its default, its range and step, the choices of a cycle), so that table can take it.
pub const Param = struct {
    kind: Kind,
    label: []const u8,
    offset: u32,
    def: f64,
    min: f64,
    max: f64,
    step: f64 = 0,
    choices: []const u8 = "",
};

pub var err_buf: [300]u8 = undefined;
pub var err_len: usize = 0;
pub fn refuse(comptime fmt: []const u8, args: anytype) error{Refused} {
    const s = std.fmt.bufPrint(&err_buf, fmt, args) catch "an operator refused its values";
    err_len = s.len;
    return error.Refused;
}

pub fn f32of(w: u32) f32 {
    return @bitCast(w);
}
pub fn i32of(w: u32) i32 {
    return @bitCast(w);
}

/// the word's value checked against its table row: a value outside the range is refused with a sentence
pub fn int(comptime P: []const Param, w: []const u32, comptime k: usize) error{Refused}!i32 {
    const v = i32of(w[k]);
    if (@as(f64, @floatFromInt(v)) < P[k].min or @as(f64, @floatFromInt(v)) > P[k].max)
        return refuse("{s} {d} is outside {d}..{d}", .{ P[k].label, v, P[k].min, P[k].max });
    return v;
}
pub fn flt(comptime P: []const Param, w: []const u32, comptime k: usize) error{Refused}!f32 {
    const v = f32of(w[k]);
    if (!(v >= P[k].min and v <= P[k].max)) return refuse("{s} {d} is outside {d}..{d}", .{ P[k].label, v, P[k].min, P[k].max });
    return v;
}
pub fn version(comptime opname: []const u8, w: []const u32, comptime known: u32) error{Refused}!void {
    if (w[0] != known) return refuse("{s} version {d} is not known (this module draws version {d})", .{ opname, w[0], known });
}

/// a colour word (0xAARRGGBB) as three values 0..1
pub fn rgb(word: u32) [3]f32 {
    return .{
        @as(f32, @floatFromInt((word >> 16) & 0xff)) / 255.0,
        @as(f32, @floatFromInt((word >> 8) & 0xff)) / 255.0,
        @as(f32, @floatFromInt(word & 0xff)) / 255.0,
    };
}

pub inline fn getc(p: Pix, i: usize) [4]f32 {
    const q = p.d + 4 * i;
    return .{
        @as(f32, @floatFromInt(q[2])) / 32767.0,
        @as(f32, @floatFromInt(q[1])) / 32767.0,
        @as(f32, @floatFromInt(q[0])) / 32767.0,
        @as(f32, @floatFromInt(q[3])) / 32767.0,
    };
}
pub inline fn q15(x: f32) u16 {
    const c = @min(1.0, @max(0.0, x));
    return @intFromFloat(@floor(c * 32767.0 + 0.5));
}
pub inline fn putc(p: Pix, i: usize, c: [4]f32) void {
    const q = p.d + 4 * i;
    q[2] = q15(c[0]);
    q[1] = q15(c[1]);
    q[0] = q15(c[2]);
    q[3] = q15(c[3]);
}
/// the grey value a field operator reads from its input: the mean of red, green and blue
pub inline fn grey(p: Pix, i: usize) f32 {
    const q = p.d + 4 * i;
    return (@as(f32, @floatFromInt(q[0])) + @as(f32, @floatFromInt(q[1])) + @as(f32, @floatFromInt(q[2]))) / (3.0 * 32767.0);
}

pub inline fn clamp01(x: f32) f32 {
    return @min(1.0, @max(0.0, x));
}
pub inline fn lerp(a: f32, b: f32, t: f32) f32 {
    return a + (b - a) * t;
}
pub inline fn smoothstep(a: f32, b: f32, x: f32) f32 {
    if (b <= a) return if (x >= a) 1.0 else 0.0;
    const t = clamp01((x - a) / (b - a));
    return t * t * (3.0 - 2.0 * t);
}

// ---------------------------------------------------------------- hashing (no state: a function of the place)

/// lowbias32 (Chris Wellons, "Prospecting for Hash Functions", 2018, public domain): one 32-bit word mixed well
pub inline fn hash(x: u32) u32 {
    var h = x;
    h ^= h >> 16;
    h *%= 0x7feb352d;
    h ^= h >> 15;
    h *%= 0x846ca68b;
    h ^= h >> 16;
    return h;
}
pub inline fn hash3(a: i32, b: i32, s: u32) u32 {
    return hash(@as(u32, @bitCast(a)) *% 0x8da6b343 ^ hash(@as(u32, @bitCast(b)) *% 0xd8163841 ^ hash(s +% 0x9e3779b9)));
}
pub inline fn rnd01(h: u32) f32 {
    return @as(f32, @floatFromInt(h >> 8)) * (1.0 / 16777216.0);
}
pub inline fn wrap(i: i32, n: i32) i32 {
    return @mod(i, n);
}

// ---------------------------------------------------------------- gradient noise (Perlin 1985, 2002), repeating

/// sixteen unit directions, k times 22.5 degrees, written out (no trigonometry at run time)
const grads = [16][2]f32{
    .{ 1, 0 },                        .{ 0.92387953, 0.38268343 },   .{ 0.70710678, 0.70710678 },   .{ 0.38268343, 0.92387953 },
    .{ 0, 1 },                        .{ -0.38268343, 0.92387953 },  .{ -0.70710678, 0.70710678 },  .{ -0.92387953, 0.38268343 },
    .{ -1, 0 },                       .{ -0.92387953, -0.38268343 }, .{ -0.70710678, -0.70710678 }, .{ -0.38268343, -0.92387953 },
    .{ 0, -1 },                       .{ 0.38268343, -0.92387953 },  .{ 0.70710678, -0.70710678 },  .{ 0.92387953, -0.38268343 },
};

inline fn fade(t: f32) f32 {
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0);
}

/// Perlin's gradient noise at x, y on a lattice that repeats every px cells across and py down; about -1 to 1.
/// The fade is Perlin's improved one (2002), 6t^5 - 15t^4 + 10t^3.
pub fn gnoise(x: f32, y: f32, px: i32, py: i32, seed: u32) f32 {
    const x0 = @floor(x);
    const y0 = @floor(y);
    const ix: i32 = @intFromFloat(x0);
    const iy: i32 = @intFromFloat(y0);
    const dx = x - x0;
    const dy = y - y0;
    const a0 = wrap(ix, px);
    const a1 = wrap(ix + 1, px);
    const b0 = wrap(iy, py);
    const b1 = wrap(iy + 1, py);
    const g00 = grads[hash3(a0, b0, seed) & 15];
    const g10 = grads[hash3(a1, b0, seed) & 15];
    const g01 = grads[hash3(a0, b1, seed) & 15];
    const g11 = grads[hash3(a1, b1, seed) & 15];
    const n00 = g00[0] * dx + g00[1] * dy;
    const n10 = g10[0] * (dx - 1) + g10[1] * dy;
    const n01 = g01[0] * dx + g01[1] * (dy - 1);
    const n11 = g11[0] * (dx - 1) + g11[1] * (dy - 1);
    const u = fade(dx);
    const v = fade(dy);
    return 1.41421356 * lerp(lerp(n00, n10, u), lerp(n01, n11, u), v);
}

pub const NoiseKind = enum(u32) { fbm = 0, ridged = 1, billow = 2 };

/// Fractal sum of octaves (Musgrave's fBm, with ridged and billowed variants after Musgrave 1994): fx and fy cells
/// across and down the whole picture for the first octave, each next octave twice as many, its weight gain times
/// the last. Octaves whose cells are under two pixels of the canvas are left out (they would only alias), and so
/// are octaves past the canvas's level of detail; the sum is divided by the weights of all octaves, so leaving
/// fine octaves out does not move the overall level.
pub fn fbm(u: f32, v: f32, fx: i32, fy: i32, oct: u32, gain: f32, seed: u32, kind: NoiseKind) f32 {
    var sum: f32 = 0;
    var amp: f32 = 1;
    var norm: f32 = 0;
    const pxs = cv.px();
    var k: u32 = 0;
    while (k < oct) : (k += 1) {
        const m: i32 = @as(i32, 1) << @intCast(@min(k, 20));
        const cx = fx * m;
        const cy = fy * m;
        norm += amp;
        const cell = 1.0 / @as(f32, @floatFromInt(@max(cx, cy)));
        if (k < cv.maxoct and cell >= 2.0 * pxs) {
            var n = gnoise(u * @as(f32, @floatFromInt(cx)), v * @as(f32, @floatFromInt(cy)), cx, cy, seed +% k *% 1013);
            switch (kind) {
                .fbm => {},
                .ridged => {
                    const r = 1.0 - @abs(n);
                    n = r * r;
                },
                .billow => n = @abs(n),
            }
            sum += amp * n;
        } else if (kind != .fbm) {
            // the mean a left-out ridged or billowed octave would have added
            sum += amp * (if (kind == .ridged) @as(f32, 0.55) else @as(f32, 0.3));
        }
        amp *= gain;
    }
    return sum / norm;
}

/// The domain warp (Quilez, "domain warping", 2002): the place moved by two noises of its own before it is read.
pub fn warped(u: f32, v: f32, amount: f32, wf: i32, seed: u32) [2]f32 {
    if (amount == 0) return .{ u, v };
    const a = fbm(u, v, wf, wf, 3, 0.5, seed ^ 0x51a7, .fbm);
    const b = fbm(u, v, wf, wf, 3, 0.5, seed ^ 0x9e37, .fbm);
    return .{ u + amount * a, v + amount * b };
}

/// sine and cosine of an angle in turns (one turn is a full circle), by a polynomial: the same arithmetic on every
/// processor (Taylor terms to the 11th power after reducing to an eighth of a turn's neighbourhood)
pub fn sincosTurns(t_in: f32) [2]f32 {
    const t = t_in - @floor(t_in + 0.5); // -0.5 .. 0.5
    const x = t * 6.28318531;
    const x2 = x * x;
    // sin and cos on -pi..pi: reduce by symmetry to -pi/2..pi/2
    var s: f32 = undefined;
    var c: f32 = undefined;
    var y = x;
    var flip = false;
    if (y > 1.57079633) {
        y = 3.14159265 - y;
        flip = true;
    } else if (y < -1.57079633) {
        y = -3.14159265 - y;
        flip = true;
    }
    _ = x2;
    const y2 = y * y;
    s = y * (1.0 - y2 / 6.0 * (1.0 - y2 / 20.0 * (1.0 - y2 / 42.0 * (1.0 - y2 / 72.0 * (1.0 - y2 / 110.0)))));
    c = 1.0 - y2 / 2.0 * (1.0 - y2 / 12.0 * (1.0 - y2 / 30.0 * (1.0 - y2 / 56.0 * (1.0 - y2 / 90.0))));
    if (flip) c = -c;
    return .{ s, c };
}

/// Box blur of one channel over r pixels each way, across then down, on whole numbers (the channel's 15-bit values):
/// the sums are exact, so a pixel's answer does not depend on where the canvas starts, and a tile drawn with its
/// margin gives the same bytes as the whole picture at that place. Every loop is bounded by the canvas.
pub fn boxBlur(src: []const i32, dst: []f32, tmp: []i64, w: usize, h: usize, r: usize) void {
    const n: f64 = @floatFromInt((2 * r + 1) * (2 * r + 1));
    for (0..h) |j| {
        // running sum along the row, exact in whole numbers, clamped at the canvas's edge
        var s: i64 = 0;
        const ri: isize = @intCast(r);
        var k: isize = -ri;
        while (k <= ri) : (k += 1) s += src[j * w + clampi(k, w)];
        for (0..w) |i| {
            tmp[j * w + i] = s;
            const ii: isize = @intCast(i);
            s += src[j * w + clampi(ii + ri + 1, w)];
            s -= src[j * w + clampi(ii - ri, w)];
        }
    }
    for (0..w) |i| {
        var s: i64 = 0;
        const ri: isize = @intCast(r);
        var k: isize = -ri;
        while (k <= ri) : (k += 1) s += tmp[clampi(k, h) * w + i];
        for (0..h) |j| {
            dst[j * w + i] = @floatCast(@as(f64, @floatFromInt(s)) / n);
            const jj: isize = @intCast(j);
            s += tmp[clampi(jj + ri + 1, h) * w + i];
            s -= tmp[clampi(jj - ri, h) * w + i];
        }
    }
}

inline fn clampi(x: isize, n: usize) usize {
    return @intCast(@min(@as(isize, @intCast(n - 1)), @max(0, x)));
}
