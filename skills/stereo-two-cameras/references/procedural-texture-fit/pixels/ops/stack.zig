//! Stack (version 1, milestone 2e): results laid over each other. Daniel, 11 November 2026, on the bricks: "2d-r02,
//! but put 2d-r01 underneath it, so the black brick contour that's straight, is underneath the cracked parts - in the
//! 3D map, obay this layering as well, with the line underneath"; on the rusted metal: "should be mixed on top of
//! 2-four-5 (same idea as bricks) and if mixed, 2c-7 as well just slightly "alpha" on it".
//! Its inputs are two to four whole procedures (each may be a Quad or a Grid), the bottom one first; each is drawn on
//! its own canvas over the same window (p2p.zig's drawStack and the page's drawStackGpu do that). Every layer above
//! the bottom is laid over what lies below it with its own amount and mask: alpha (the amount everywhere), height
//! (where the layer itself stands high: its height through a soft threshold from lo to hi), dark (where the layer is
//! dark: its grey below the threshold), light (where it is light). With lo above hi the threshold falls instead of
//! rising (as Layer version 2's). Colour and height are laid with the same weight, so the relief keeps the order of
//! the layers: what lies underneath in the picture lies underneath in the relief.
//! Pure function of the place, no maths library: only + - * /.
const c = @import("common.zig");

pub const name = "Stack";
pub const version: u32 = 1;
pub const inputs: u8 = 2;
pub const MAXL = 4;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .cycle, .label = "mask 2", .offset = 1, .def = 0, .min = 0, .max = 3, .choices = "alpha|height|dark|light" },
    .{ .kind = .float, .label = "amount 2", .offset = 2, .def = 0.5, .min = 0, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "lo 2", .offset = 3, .def = 0.4, .min = -1, .max = 2, .step = 0.01 },
    .{ .kind = .float, .label = "hi 2", .offset = 4, .def = 0.6, .min = -1, .max = 2, .step = 0.01 },
    .{ .kind = .cycle, .label = "mask 3", .offset = 5, .def = 0, .min = 0, .max = 3, .choices = "alpha|height|dark|light" },
    .{ .kind = .float, .label = "amount 3", .offset = 6, .def = 0.5, .min = 0, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "lo 3", .offset = 7, .def = 0.4, .min = -1, .max = 2, .step = 0.01 },
    .{ .kind = .float, .label = "hi 3", .offset = 8, .def = 0.6, .min = -1, .max = 2, .step = 0.01 },
    .{ .kind = .cycle, .label = "mask 4", .offset = 9, .def = 0, .min = 0, .max = 3, .choices = "alpha|height|dark|light" },
    .{ .kind = .float, .label = "amount 4", .offset = 10, .def = 0.5, .min = 0, .max = 1, .step = 0.05 },
    .{ .kind = .float, .label = "lo 4", .offset = 11, .def = 0.4, .min = -1, .max = 2, .step = 0.01 },
    .{ .kind = .float, .label = "hi 4", .offset = 12, .def = 0.6, .min = -1, .max = 2, .step = 0.01 },
};

pub fn wordCount(ver: u32) usize {
    _ = ver;
    return params.len;
}

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 0;
}

/// a soft threshold from lo to hi, falling when lo lies above hi
pub fn thr(lo: f32, hi: f32, x: f32) f32 {
    if (lo > hi) return 1.0 - c.smoothstep(hi, lo, x);
    return c.smoothstep(lo, hi, x);
}

/// the weight a layer is laid with at a pixel of colour p (p[3] its height)
pub fn weightOf(mode: i32, amount: f32, lo: f32, hi: f32, p: [4]f32) f32 {
    const g = (p[0] + p[1] + p[2]) / 3.0;
    const f: f32 = switch (mode) {
        0 => 1.0,
        1 => thr(lo, hi, p[3]),
        2 => 1.0 - thr(lo, hi, g),
        else => thr(lo, hi, g),
    };
    return f * amount;
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    try c.version(name, w, version);
    if (ins.len < 2 or ins.len > MAXL) return c.refuse("Stack lays two to four procedures, the graph gives {d}", .{ins.len});
    var mode: [MAXL]i32 = undefined;
    var amt: [MAXL]f32 = undefined;
    var lo: [MAXL]f32 = undefined;
    var hi: [MAXL]f32 = undefined;
    inline for (1..MAXL) |l| {
        mode[l] = try c.int(&params, w, 1 + 4 * (l - 1));
        amt[l] = try c.flt(&params, w, 2 + 4 * (l - 1));
        lo[l] = try c.flt(&params, w, 3 + 4 * (l - 1));
        hi[l] = try c.flt(&params, w, 4 + 4 * (l - 1));
    }
    for (0..out.w * out.h) |i| {
        var o = c.getc(ins[0], i);
        for (1..ins.len) |l| {
            const t = c.getc(ins[l], i);
            const m = weightOf(mode[l], amt[l], lo[l], hi[l], t);
            inline for (0..4) |ch| o[ch] = c.lerp(o[ch], t[ch], m);
        }
        c.putc(out, i, o);
    }
}
