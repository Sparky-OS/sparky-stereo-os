//! The modern operators of milestone 2b, as one family beside werkkzeug3's: each in its own file under ops/ with its
//! parameter table (the shape of Stereo Werkkzeug's table, so lane 514 can take them), each with a version word
//! first. This file lists them, gives the fitter their tables, and draws one of them on werkkzeug's bitmaps.
const std = @import("std");
pub const c = @import("ops/common.zig");

pub const noise = @import("ops/noise.zig");
pub const cells = @import("ops/cells.zig");
pub const tiles = @import("ops/tiles.zig");
pub const ramp = @import("ops/ramp.zig");
pub const layer = @import("ops/layer.zig");
pub const shade = @import("ops/shade.zig");
pub const scatter = @import("ops/scatter.zig");
pub const wear = @import("ops/wear.zig");
pub const tint = @import("ops/tint.zig");

pub const list = .{ noise, cells, tiles, ramp, layer, shade, scatter, wear, tint };
pub const count = list.len;

/// i whole number, f decimal, c colour: the packing p2p's operator table uses
pub fn kindsOf(comptime P: []const c.Param) []const u8 {
    comptime {
        var s: [P.len]u8 = undefined;
        for (P, 0..) |p, k| s[k] = switch (p.kind) {
            .int, .cycle => 'i',
            .float => 'f',
            .rgba => 'c',
        };
        const out = s;
        return &out;
    }
}

pub fn paramsOf(k: usize) []const c.Param {
    inline for (list, 0..) |m, i| {
        if (i == k) return &m.params;
    }
    unreachable;
}

pub fn inputsOf(k: usize) u8 {
    inline for (list, 0..) |m, i| {
        if (i == k) return m.inputs;
    }
    unreachable;
}

pub fn nameOf(k: usize) [:0]const u8 {
    inline for (list, 0..) |m, i| {
        if (i == k) return m.name;
    }
    unreachable;
}

/// the reach of a node's neighbourhood in parts of the picture (0 for an operator that reads only its own place)
pub fn marginOf(k: usize, w: []const u32) f32 {
    inline for (list, 0..) |m, i| {
        if (i == k) return m.margin(w);
    }
    unreachable;
}

extern "c" fn wzb_new(xs: c_int, ys: c_int) ?*anyopaque;
extern "c" fn wzb_data(p: ?*anyopaque) [*]u16;
extern "c" fn wzb_width(p: ?*anyopaque) c_int;
extern "c" fn wzb_height(p: ?*anyopaque) c_int;
extern "c" fn wzb_free(p: ?*anyopaque) void;

fn pixOf(p: ?*anyopaque) c.Pix {
    return .{ .d = wzb_data(p), .w = @intCast(wzb_width(p)), .h = @intCast(wzb_height(p)) };
}

/// Draw modern operator k on the canvas c.cv. 0 and the new bitmap in out, or 1 and a sentence in err.
pub fn apply(k: usize, w: []const u32, inp: []const ?*anyopaque, out: *?*anyopaque, err: []u8) c_int {
    var pins: [8]c.Pix = undefined;
    for (inp, 0..) |p, i| {
        pins[i] = pixOf(p);
        // every input is drawn on the canvas, except a Scatter's seed (its second input), which is a small picture
        const is_seed = (k == 6 and i == 1);
        if (!is_seed and (pins[i].w != c.cv.w or pins[i].h != c.cv.h)) {
            const s = std.fmt.bufPrint(err, "{s}: input {d} is {d}x{d}, the canvas {d}x{d}", .{ nameOf(k), i + 1, pins[i].w, pins[i].h, c.cv.w, c.cv.h }) catch "";
            if (s.len < err.len) err[s.len] = 0;
            return 1;
        }
    }
    var need: usize = 0;
    inline for (list, 0..) |m, i| {
        if (i == k) need = m.inputs;
    }
    if (inp.len < need) {
        const s = std.fmt.bufPrint(err, "{s} takes {d} input(s), the graph gives {d}", .{ nameOf(k), need, inp.len }) catch "";
        if (s.len < err.len) err[s.len] = 0;
        return 1;
    }
    if (w[0] == 0) {
        const s = std.fmt.bufPrint(err, "{s} has no version word (the first word must say the version)", .{nameOf(k)}) catch "";
        if (s.len < err.len) err[s.len] = 0;
        return 1;
    }
    const o = wzb_new(@intCast(c.cv.w), @intCast(c.cv.h)) orelse {
        const s = std.fmt.bufPrint(err, "{s}: no memory for a {d}x{d} picture", .{ nameOf(k), c.cv.w, c.cv.h }) catch "";
        if (s.len < err.len) err[s.len] = 0;
        return 1;
    };
    const po = pixOf(o);
    var r: error{Refused}!void = {};
    inline for (list, 0..) |m, i| {
        if (i == k) r = m.draw(po, pins[0..inp.len], w);
    }
    r catch {
        wzb_free(o);
        const s = std.fmt.bufPrint(err, "{s}", .{c.err_buf[0..c.err_len]}) catch "";
        if (s.len < err.len) err[s.len] = 0;
        return 1;
    };
    out.* = o;
    return 0;
}
