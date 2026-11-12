//! Wear (version 1): what time does to a surface, read from its own relief. Four kinds:
//!   cavity  dirt in the hollows: where the height lies below its surroundings' mean;
//!   edges   worn edges: where the height stands above it;
//!   drips   stains that run down from features: below every place the source marks, a streak that fades over a
//!           length, stronger or weaker by a noise along the picture's width (each run of its own strength);
//!   grow    rust or moss that grows from points: the source spread over a radius and cut by a noise.
//! The source is the second input's grey when there is one, else the material's height. The worn places take the
//! wear's colour; the height is kept. Radii and lengths are parts of the picture, so a tile wears as the whole does.
//! Bounded: one box blur (exact sums over whole numbers, see common.zig) or a run of at most the length in pixels.
//! The drawing gives it a margin of its radius or length.
const std = @import("std");
const c = @import("common.zig");

pub const name = "Wear";
pub const version: u32 = 1;
pub const inputs: u8 = 1; // the material; a second input is the source
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .cycle, .label = "kind", .offset = 1, .def = 0, .min = 0, .max = 3, .choices = "cavity|edges|drips|grow" },
    .{ .kind = .float, .label = "radius", .offset = 2, .def = 0.01, .min = 0, .max = 0.1, .step = 0.001 },
    .{ .kind = .float, .label = "length", .offset = 3, .def = 0.05, .min = 0, .max = 0.25, .step = 0.005 },
    .{ .kind = .float, .label = "lo", .offset = 4, .def = 0.02, .min = -1, .max = 2, .step = 0.01 },
    .{ .kind = .float, .label = "hi", .offset = 5, .def = 0.2, .min = -1, .max = 2, .step = 0.01 },
    .{ .kind = .float, .label = "amount", .offset = 6, .def = 0.6, .min = 0, .max = 1, .step = 0.02 },
    .{ .kind = .rgba, .label = "colour", .offset = 7, .def = 0xff302820, .min = 0, .max = 0xffffffff },
    .{ .kind = .int, .label = "noise cells", .offset = 8, .def = 32, .min = 1, .max = 4096 },
    .{ .kind = .float, .label = "noise amount", .offset = 9, .def = 0.3, .min = 0, .max = 2, .step = 0.02 },
    .{ .kind = .int, .label = "seed", .offset = 10, .def = 0, .min = 0, .max = 65535 },
    .{ .kind = .float, .label = "gain", .offset = 11, .def = 4, .min = 0, .max = 64, .step = 0.25 },
};

pub fn margin(w: []const u32) f32 {
    const kind = w[1];
    return if (kind == 2) c.f32of(w[3]) else c.f32of(w[2]);
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    try c.version(name, w, version);
    const kind = try c.int(&params, w, 1);
    const radius = try c.flt(&params, w, 2);
    const length = try c.flt(&params, w, 3);
    const lo = try c.flt(&params, w, 4);
    const hi = try c.flt(&params, w, 5);
    const amt = try c.flt(&params, w, 6);
    const col = c.rgb(w[7]);
    const ncells = try c.int(&params, w, 8);
    const namt = try c.flt(&params, w, 9);
    const seed: u32 = @intCast(try c.int(&params, w, 10));
    const gain = try c.flt(&params, w, 11);
    const W = out.w;
    const H = out.h;
    const n = W * H;
    const alloc = std.heap.c_allocator;
    const src = alloc.alloc(i32, n) catch return c.refuse("Wear: out of memory", .{});
    defer alloc.free(src);
    const has_src = ins.len >= 2;
    for (0..n) |i| {
        src[i] = if (has_src) @intFromFloat(@floor(c.grey(ins[1], i) * 32767.0 + 0.5)) else ins[0].d[4 * i + 3];
    }
    const t = alloc.alloc(f32, n) catch return c.refuse("Wear: out of memory", .{});
    defer alloc.free(t);
    const pxs = c.cv.px();
    if (kind == 2) {
        const L: usize = @intFromFloat(@floor(length / pxs + 0.5));
        if (L > 4096) return c.refuse("Wear: drips {d} pixels long; at most 4096", .{L});
        for (0..H) |j| {
            for (0..W) |i| {
                var best: f32 = 0;
                var k: usize = 0;
                while (k <= L and k <= j) : (k += 1) {
                    const s = @as(f32, @floatFromInt(src[(j - k) * W + i])) / 32767.0;
                    const f = s * (1.0 - @as(f32, @floatFromInt(k)) / @as(f32, @floatFromInt(L + 1)));
                    if (f > best) best = f;
                }
                const colf = 1.0 + namt * c.gnoise(c.cv.u(i) * @as(f32, @floatFromInt(ncells)), 0.5, ncells, 1, seed);
                t[j * W + i] = best * colf * gain;
            }
        }
    } else {
        const r: usize = @intFromFloat(@floor(radius / pxs + 0.5));
        if (r > 2048) return c.refuse("Wear: a radius of {d} pixels; at most 2048", .{r});
        const bl = alloc.alloc(f32, n) catch return c.refuse("Wear: out of memory", .{});
        defer alloc.free(bl);
        const tmp = alloc.alloc(i64, n) catch return c.refuse("Wear: out of memory", .{});
        defer alloc.free(tmp);
        c.boxBlur(src, bl, tmp, W, H, r);
        for (0..H) |j| {
            for (0..W) |i| {
                const k = j * W + i;
                const s = @as(f32, @floatFromInt(src[k]));
                const b = bl[k];
                const nz = namt * c.fbm(c.cv.u(i), c.cv.v(j), ncells, ncells, 3, 0.5, seed, .fbm);
                t[k] = switch (kind) {
                    0 => (b - s) / 32767.0 * gain + nz,
                    1 => (s - b) / 32767.0 * gain + nz,
                    else => b / 32767.0 * gain + nz,
                };
            }
        }
    }
    for (0..n) |k| {
        const m = c.smoothstep(lo, hi, t[k]) * amt;
        const o = c.getc(ins[0], k);
        c.putc(out, k, .{ c.lerp(o[0], col[0], m), c.lerp(o[1], col[1], m), c.lerp(o[2], col[2], m), o[3] });
    }
}
