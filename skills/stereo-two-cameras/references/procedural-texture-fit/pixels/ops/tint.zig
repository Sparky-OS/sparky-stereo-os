//! Tint (version 1): a tile's own correction, laid only where the picture differs from the whole picture's
//! procedure. Its weight is a tent over the tile: 1 at the tile's centre, falling linearly to 0 at the centres of
//! the tiles around it, so neighbouring tints add up to a smooth field and no border shows. It changes brightness
//! and saturation only (every channel scaled alike; every channel moved toward or away from their mean), so the
//! hue stays the whole picture's (milestone 2's purple and green tiles came from colours retuned channel by
//! channel). The values are measured on the tile, never searched. The picture repeats, so the tent does too.
const c = @import("common.zig");

pub const name = "Tint";
pub const version: u32 = 1;
pub const inputs: u8 = 1;
pub const params = [_]c.Param{
    .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 },
    .{ .kind = .float, .label = "tile left", .offset = 1, .def = 0, .min = 0, .max = 1, .step = 0.0625 },
    .{ .kind = .float, .label = "tile top", .offset = 2, .def = 0, .min = 0, .max = 1, .step = 0.0625 },
    .{ .kind = .float, .label = "tile side", .offset = 3, .def = 0.25, .min = 0.001, .max = 1, .step = 0.0625 },
    .{ .kind = .float, .label = "brightness", .offset = 4, .def = 0, .min = -0.9, .max = 4, .step = 0.01 },
    .{ .kind = .float, .label = "saturation", .offset = 5, .def = 0, .min = -1, .max = 4, .step = 0.01 },
};

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 0;
}

inline fn tent(d_in: f32, s: f32) f32 {
    var d = d_in - @floor(d_in + 0.5); // the nearest repeat
    d = @abs(d);
    return c.clamp01(1.0 - d / s);
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    try c.version(name, w, version);
    const x = try c.flt(&params, w, 1);
    const y = try c.flt(&params, w, 2);
    const s = try c.flt(&params, w, 3);
    const gb = try c.flt(&params, w, 4);
    const gs = try c.flt(&params, w, 5);
    const cx = x + 0.5 * s;
    const cy = y + 0.5 * s;
    for (0..out.h) |j| {
        const ty = tent(c.cv.v(j) - cy, s);
        for (0..out.w) |i| {
            const k = j * out.w + i;
            const o = c.getc(ins[0], k);
            const wt = ty * tent(c.cv.u(i) - cx, s);
            if (wt == 0) {
                c.putc(out, k, o);
                continue;
            }
            const b = 1.0 + gb * wt;
            const sa = 1.0 + gs * wt;
            const m = (o[0] + o[1] + o[2]) / 3.0;
            c.putc(out, k, .{ (m + (o[0] - m) * sa) * b, (m + (o[1] - m) * sa) * b, (m + (o[2] - m) * sa) * b, o[3] });
        }
    }
}
