//! Layer (version 1): one material laid over another where a mask says, colour and relief together. The mask's grey
//! is taken through a soft threshold (from lo to hi) and times an amount; the top's colour is mixed in, multiplied
//! in, or added; the height is the base's, mixed with the top's, or raised or lowered by the top's height.
//! This is how a second material (rust on metal, moss on bark), dirt and stains are laid: the order of the artists'
//! werkkzeug graphs (Mask), with the height carried along so the relief stays one with the colour.
//! The detail mode adds the top's departure from mid grey (signed) to the base: a texture laid into the faces of a
//! structure before one Ramp colours both (so a brick's own shade and its grain follow the same colours).
const c = @import("common.zig");

pub const name = "Layer";
pub const version: u32 = 1;
pub const inputs: u8 = 3;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .cycle, .label = "colour", .offset = 1, .def = 0, .min = 0, .max = 3, .choices = "mix|multiply|add|detail" },
    .{ .kind = .float, .label = "lo", .offset = 2, .def = 0.4, .min = -1, .max = 2, .step = 0.01 },
    .{ .kind = .float, .label = "hi", .offset = 3, .def = 0.6, .min = -1, .max = 2, .step = 0.01 },
    .{ .kind = .float, .label = "amount", .offset = 4, .def = 1, .min = 0, .max = 1, .step = 0.02 },
    .{ .kind = .cycle, .label = "height", .offset = 5, .def = 0, .min = 0, .max = 4, .choices = "base|mix|raise|lower|multiply" },
    .{ .kind = .float, .label = "height amount", .offset = 6, .def = 0.2, .min = 0, .max = 1, .step = 0.02 },
};

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 0;
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    try c.version(name, w, version);
    const mode = try c.int(&params, w, 1);
    const lo = try c.flt(&params, w, 2);
    const hi = try c.flt(&params, w, 3);
    const amt = try c.flt(&params, w, 4);
    const hm = try c.int(&params, w, 5);
    const hk = try c.flt(&params, w, 6);
    for (0..out.w * out.h) |i| {
        const b = c.getc(ins[0], i);
        const t = c.getc(ins[1], i);
        const m = c.smoothstep(lo, hi, c.grey(ins[2], i)) * amt;
        var o: [4]f32 = undefined;
        inline for (0..3) |q| {
            o[q] = switch (mode) {
                0 => c.lerp(b[q], t[q], m),
                1 => b[q] * c.lerp(1.0, t[q], m),
                2 => b[q] + t[q] * m,
                else => b[q] + (t[q] - 0.5) * 2.0 * m,
            };
        }
        o[3] = switch (hm) {
            0 => b[3],
            1 => c.lerp(b[3], t[3], m),
            2 => b[3] + hk * t[3] * m,
            3 => b[3] - hk * t[3] * m,
            else => b[3] * c.lerp(1.0, t[3], hk * m),
        };
        c.putc(out, i, o);
    }
}
