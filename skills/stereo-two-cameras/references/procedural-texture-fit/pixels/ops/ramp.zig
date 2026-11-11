//! Ramp (version 1): a gradient map. The grey of its input (the mean of red, green and blue) is mapped through up to
//! eight colour stops, linearly between neighbouring stops; the height (alpha) passes through. werkkzeug's Range maps
//! a grey to two colours; a surface's dark and light parts are seldom one hue apart, and eight stops read from the
//! picture at the same ranks as the drawn field's carry the picture's colours (a histogram match in few bytes).
//! Stops are given in order of their place; places that are not rising are refused with a sentence.
const c = @import("common.zig");

pub const name = "Ramp";
pub const version: u32 = 1;
pub const inputs: u8 = 1;
pub const NSTOP = 8;
pub const params = blk: {
    var p: [2 + 2 * NSTOP]c.Param = undefined;
    p[0] = .{ .kind = .int, .label = "version", .offset = 0, .def = 1, .min = 1, .max = 1 };
    p[1] = .{ .kind = .int, .label = "stops", .offset = 1, .def = 2, .min = 2, .max = NSTOP };
    for (0..NSTOP) |k| {
        p[2 + 2 * k] = .{ .kind = .float, .label = "place " ++ [_]u8{'1' + k}, .offset = 2 + 2 * k, .def = @as(f64, @floatFromInt(k)) / (NSTOP - 1), .min = 0, .max = 1, .step = 0.01 };
        p[3 + 2 * k] = .{ .kind = .rgba, .label = "colour " ++ [_]u8{'1' + k}, .offset = 3 + 2 * k, .def = 0xff808080, .min = 0, .max = 0xffffffff };
    }
    break :blk p;
};

pub fn margin(w: []const u32) f32 {
    _ = w;
    return 0;
}

pub fn draw(out: c.Pix, ins: []const c.Pix, w: []const u32) error{Refused}!void {
    try c.version(name, w, version);
    const n: usize = @intCast(try c.int(&params, w, 1));
    var pos: [NSTOP]f32 = undefined;
    var col: [NSTOP][3]f32 = undefined;
    for (0..n) |k| {
        pos[k] = c.f32of(w[2 + 2 * k]);
        if (!(pos[k] >= 0 and pos[k] <= 1)) return c.refuse("Ramp: place {d} is {d}, outside 0..1", .{ k + 1, pos[k] });
        if (k > 0 and pos[k] < pos[k - 1]) return c.refuse("Ramp: place {d} ({d}) lies before place {d} ({d}); places must rise", .{ k + 1, pos[k], k, pos[k - 1] });
        col[k] = c.rgb(w[3 + 2 * k]);
    }
    const src = ins[0];
    for (0..out.w * out.h) |i| {
        const g = c.grey(src, i);
        const a = c.getc(src, i)[3];
        var rgb = col[0];
        if (g >= pos[n - 1]) {
            rgb = col[n - 1];
        } else if (g > pos[0]) {
            var k: usize = 1;
            while (k < n and g > pos[k]) : (k += 1) {}
            const span = pos[k] - pos[k - 1];
            const t = if (span > 0) (g - pos[k - 1]) / span else 1.0;
            inline for (0..3) |q| rgb[q] = c.lerp(col[k - 1][q], col[k][q], t);
        }
        c.putc(out, i, .{ rgb[0], rgb[1], rgb[2], a });
    }
}
