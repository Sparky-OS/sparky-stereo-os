//! The readings of milestone 2b: what the pixels say, measured, never searched, each one the way an operator enters
//! the fit. A parameter that a reading cannot give directly is chosen so the drawing's reading equals the
//! picture's (the drawing is read by the same function): the operator is never chosen by the inner measure.
//! Every function takes a grey picture (n by n values, 0 to 1) and gives numbers; nothing here draws.
const std = @import("std");
const alloc = std.heap.c_allocator;

pub fn blur(src: []const f32, n: usize, r: usize) []f32 {
    const tmp = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(tmp);
    const out = alloc.alloc(f32, n * n) catch unreachable;
    if (r == 0) {
        @memcpy(out, src);
        return out;
    }
    const k: f32 = @floatFromInt(2 * r + 1);
    for (0..n) |y| {
        for (0..n) |x| {
            var s: f32 = 0;
            for (0..2 * r + 1) |d| s += src[y * n + (x + n + d - r) % n];
            tmp[y * n + x] = s / k;
        }
    }
    for (0..n) |y| {
        for (0..n) |x| {
            var s: f32 = 0;
            for (0..2 * r + 1) |d| s += tmp[((y + n + d - r) % n) * n + x];
            out[y * n + x] = s / k;
        }
    }
    return out;
}

/// how much stronger the change is across than down, after a blur of r (a grain that runs down gives more than 1)
pub fn aniso(t: []const f32, n: usize, r: usize) f32 {
    const b = blur(t, n, r);
    defer alloc.free(b);
    var ax: f64 = 0;
    var ay: f64 = 0;
    const st = @max(1, r);
    for (0..n) |y| {
        for (0..n) |x| {
            ax += @abs(b[y * n + (x + st) % n] - b[y * n + x]);
            ay += @abs(b[((y + st) % n) * n + x] - b[y * n + x]);
        }
    }
    return @floatCast((ax + 1e-9) / (ay + 1e-9));
}

/// the skew of the detail (the picture less its blur of r): thin dark lines on a lighter ground give a negative skew,
/// thin light lines a positive one, a blotchy noise near zero
pub fn hpSkew(t: []const f32, n: usize, r: usize) f32 {
    const b = blur(t, n, r);
    defer alloc.free(b);
    var m2: f64 = 0;
    var m3: f64 = 0;
    for (0..n * n) |i| {
        const d: f64 = t[i] - b[i];
        m2 += d * d;
        m3 += d * d * d;
    }
    m2 /= @floatFromInt(n * n);
    m3 /= @floatFromInt(n * n);
    return @floatCast(m3 / (std.math.pow(f64, m2, 1.5) + 1e-12));
}

/// How the way the lines run bends: the structure tensor (Bigun and Granlund 1987; Kass and Witkin 1987) of the picture
/// blurred by r, smoothed over 2r, as a doubled angle; the mean change of that angle between places 2r apart,
/// weighed by how clearly lines run there. Straight grain gives little; furrows that wander, much.
pub fn wiggle(t: []const f32, n: usize, r: usize) f32 {
    const b = blur(t, n, r);
    defer alloc.free(b);
    const jx = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(jx);
    const jy = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(jy);
    const jz = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(jz);
    for (0..n) |y| {
        for (0..n) |x| {
            const gx = b[y * n + (x + 1) % n] - b[y * n + (x + n - 1) % n];
            const gy = b[((y + 1) % n) * n + x] - b[((y + n - 1) % n) * n + x];
            jx[y * n + x] = gx * gx - gy * gy;
            jy[y * n + x] = 2 * gx * gy;
            jz[y * n + x] = gx * gx + gy * gy;
        }
    }
    const sx = blur(jx, n, 2 * r);
    defer alloc.free(sx);
    const sy = blur(jy, n, 2 * r);
    defer alloc.free(sy);
    const sz = blur(jz, n, 2 * r);
    defer alloc.free(sz);
    var num: f64 = 0;
    var den: f64 = 0;
    const d = 2 * r;
    var y: usize = 0;
    while (y < n) : (y += 2) {
        var x: usize = 0;
        while (x < n) : (x += 2) {
            const a = y * n + x;
            const c = ((y + d) % n) * n + x;
            const e = y * n + (x + d) % n;
            const la = @sqrt(sx[a] * sx[a] + sy[a] * sy[a]);
            const lc = @sqrt(sx[c] * sx[c] + sy[c] * sy[c]);
            const le = @sqrt(sx[e] * sx[e] + sy[e] * sy[e]);
            const coh = la / (sz[a] + 1e-9);
            if (la < 1e-9) continue;
            const dot_c = (sx[a] * sx[c] + sy[a] * sy[c]) / (la * lc + 1e-12);
            const dot_e = (sx[a] * sx[e] + sy[a] * sy[e]) / (la * le + 1e-12);
            num += coh * (2.0 - dot_c - dot_e);
            den += coh;
        }
    }
    return @floatCast(num / (den + 1e-12));
}

/// the picture's values sorted (for rank matching)
pub fn sorted(t: []const f32) []f32 {
    const s = alloc.alloc(f32, t.len) catch unreachable;
    @memcpy(s, t);
    std.mem.sort(f32, s, {}, std.sort.asc(f32));
    return s;
}

/// t mapped so its values have the histogram of ref (both sorted lists of the same length or not): rank matching
pub fn rankMap(t: []const f32, ref_sorted: []const f32) []f32 {
    const idx = alloc.alloc(u32, t.len) catch unreachable;
    defer alloc.free(idx);
    for (idx, 0..) |*v, i| v.* = @intCast(i);
    const Ctx = struct {
        t: []const f32,
        fn lt(ctx: @This(), a: u32, b: u32) bool {
            return ctx.t[a] < ctx.t[b];
        }
    };
    std.mem.sort(u32, idx, Ctx{ .t = t }, Ctx.lt);
    const out = alloc.alloc(f32, t.len) catch unreachable;
    for (idx, 0..) |v, r| out[v] = ref_sorted[r * ref_sorted.len / t.len];
    return out;
}

pub const Blobs = struct {
    count: usize = 0, // compact blobs found
    radius: f32 = 0, // their mean radius in pixels
    share: f32 = 0, // the share of the picture they cover
    dark: bool = true,
    down: f32 = 1, // how much longer down than across (drips and streaks)
    up_light: f32 = 0, // the detail on the blobs' upper half minus their lower half, over the detail's spread
    left_light: f32 = 0, // the same left against right
    lines: f32 = 0, // the share of the picture in long thin pieces (cracks)
    line_spacing: f32 = 0, // the mean distance between those lines, in pixels
    line_width: f32 = 0,
};

/// Blobs and lines in the detail (the picture less its blur of r), darker (dark) or lighter than k spreads:
/// compact pieces (filling at least 0.35 of their box, at most 3 times as long as wide, under max_area pixels) are
/// pits, specks or stones; long thin pieces (at least 6 times as long as their mean width, and 24 pixels) are
/// cracks. Connected pieces by an iterative fill with its own stack (bounded by the picture).
pub fn blobs(t: []const f32, n: usize, r: usize, k: f32, dark: bool, max_area: usize) Blobs {
    const b = blur(t, n, r);
    defer alloc.free(b);
    var sd: f64 = 0;
    for (0..n * n) |i| sd += (t[i] - b[i]) * (t[i] - b[i]);
    const sdev: f32 = @floatCast(@sqrt(sd / @as(f64, @floatFromInt(n * n))));
    const m = alloc.alloc(u8, n * n) catch unreachable;
    defer alloc.free(m);
    for (0..n * n) |i| {
        const d = t[i] - b[i];
        m[i] = if ((dark and d < -k * sdev) or (!dark and d > k * sdev)) 1 else 0;
    }
    const stack = alloc.alloc(u32, n * n) catch unreachable;
    defer alloc.free(stack);
    var out = Blobs{ .dark = dark };
    var rsum: f64 = 0;
    var area_all: usize = 0;
    var dsum: f64 = 0;
    var upl: f64 = 0;
    var lfl: f64 = 0;
    var lines_area: usize = 0;
    var lines_len: f64 = 0;
    var lines_w: f64 = 0;
    for (0..n * n) |s0| {
        if (m[s0] != 1) continue;
        var sp: usize = 0;
        stack[sp] = @intCast(s0);
        sp += 1;
        m[s0] = 2;
        var area: usize = 0;
        var x0: usize = n;
        var x1: usize = 0;
        var y0: usize = n;
        var y1: usize = 0;
        var cxs: f64 = 0;
        var cys: f64 = 0;
        while (sp > 0) {
            sp -= 1;
            const p = stack[sp];
            const x = p % n;
            const y = p / n;
            area += 1;
            cxs += @floatFromInt(x);
            cys += @floatFromInt(y);
            x0 = @min(x0, x);
            x1 = @max(x1, x);
            y0 = @min(y0, y);
            y1 = @max(y1, y);
            const nb = [4]u32{ @intCast(y * n + (x + 1) % n), @intCast(y * n + (x + n - 1) % n), @intCast(((y + 1) % n) * n + x), @intCast(((y + n - 1) % n) * n + x) };
            for (nb) |q| {
                if (m[q] == 1) {
                    m[q] = 2;
                    stack[sp] = q;
                    sp += 1;
                }
            }
        }
        if (area < 4) continue;
        const bw: f32 = @floatFromInt(x1 - x0 + 1);
        const bh: f32 = @floatFromInt(y1 - y0 + 1);
        const fa: f32 = @floatFromInt(area);
        const long = @max(bw, bh);
        const width = fa / long;
        if (long >= 24 and long >= 6 * width and bw < @as(f32, @floatFromInt(n / 2)) and bh < @as(f32, @floatFromInt(n / 2))) {
            lines_area += area;
            lines_len += long;
            lines_w += width * long;
            continue;
        }
        if (area > max_area) continue;
        if (fa < 0.35 * bw * bh or long > 3 * @min(bw, bh)) continue;
        out.count += 1;
        area_all += area;
        rsum += @sqrt(fa / std.math.pi);
        dsum += bh / bw;
        // light on the blob's sides: the detail just above it against just below it, and left against right
        const cx: usize = @intFromFloat(cxs / fa);
        const cy: usize = @intFromFloat(cys / fa);
        const rr: usize = @intFromFloat(@max(2.0, @sqrt(fa / std.math.pi)));
        const ya = (cy + n - rr) % n;
        const yb = (cy + rr) % n;
        const xa = (cx + n - rr) % n;
        const xb = (cx + rr) % n;
        upl += (t[ya * n + cx] - b[ya * n + cx]) - (t[yb * n + cx] - b[yb * n + cx]);
        lfl += (t[cy * n + xa] - b[cy * n + xa]) - (t[cy * n + xb] - b[cy * n + xb]);
    }
    if (out.count > 0) {
        const fc: f64 = @floatFromInt(out.count);
        out.radius = @floatCast(rsum / fc);
        out.down = @floatCast(dsum / fc);
        out.up_light = @floatCast(upl / fc / (sdev + 1e-9));
        out.left_light = @floatCast(lfl / fc / (sdev + 1e-9));
    }
    out.share = @as(f32, @floatFromInt(area_all)) / @as(f32, @floatFromInt(n * n));
    out.lines = @as(f32, @floatFromInt(lines_area)) / @as(f32, @floatFromInt(n * n));
    if (lines_len > 0) {
        // lines of total length L over an area A lie about A / L apart
        out.line_spacing = @floatCast(@as(f64, @floatFromInt(n * n)) / lines_len);
        out.line_width = @floatCast(lines_w / lines_len);
    }
    return out;
}

/// The mean cell of a picture that repeats nx by ny times (cw by ch pixels, its first pixel at the picture's first)
pub fn meanCell(t: []const f32, n: usize, nx: usize, ny: usize, cw_out: *usize, ch_out: *usize) []f32 {
    const cw = n / nx;
    const ch = n / ny;
    cw_out.* = cw;
    ch_out.* = ch;
    const cell = alloc.alloc(f32, cw * ch) catch unreachable;
    @memset(cell, 0);
    const fx: f32 = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(nx));
    const fy: f32 = @as(f32, @floatFromInt(n)) / @as(f32, @floatFromInt(ny));
    for (0..ny) |j| {
        for (0..nx) |i| {
            const ox: usize = @intFromFloat(@floor(@as(f32, @floatFromInt(i)) * fx + 0.5));
            const oy: usize = @intFromFloat(@floor(@as(f32, @floatFromInt(j)) * fy + 0.5));
            for (0..ch) |y| {
                for (0..cw) |x| cell[y * cw + x] += t[((oy + y) % n) * n + (ox + x) % n];
            }
        }
    }
    const k: f32 = @floatFromInt(nx * ny);
    for (cell) |*v| v.* /= k;
    return cell;
}

pub const Align = struct { corr: f32 = -2, sx: usize = 0, sy: usize = 0 };

/// The correlation of cell a with cell b moved by every shift (both cw by ch, repeating); the best shift.
/// signed: the largest correlation; else the largest in size (a light mortar against drawn dark joints).
pub fn alignCells(a: []const f32, b: []const f32, cw: usize, ch: usize, signed: bool) Align {
    var ma: f64 = 0;
    var mb: f64 = 0;
    for (a, b) |x, y| {
        ma += x;
        mb += y;
    }
    const N: f64 = @floatFromInt(cw * ch);
    ma /= N;
    mb /= N;
    var va: f64 = 0;
    var vb: f64 = 0;
    for (a, b) |x, y| {
        va += (x - ma) * (x - ma);
        vb += (y - mb) * (y - mb);
    }
    var best = Align{};
    var bk: f32 = -1e9;
    const step: usize = if (cw * ch > 40000) 2 else 1;
    var sy: usize = 0;
    while (sy < ch) : (sy += step) {
        var sx: usize = 0;
        while (sx < cw) : (sx += step) {
            var s: f64 = 0;
            for (0..ch) |y| {
                const yb = ((y + sy) % ch) * cw;
                for (0..cw) |x| s += (a[y * cw + x] - ma) * (b[yb + (x + sx) % cw] - mb);
            }
            const cr: f32 = @floatCast(s / (@sqrt(va * vb) + 1e-12));
            const key = if (signed) cr else @abs(cr);
            if (key > bk) {
                bk = key;
                best = .{ .corr = cr, .sx = sx, .sy = sy };
            }
        }
    }
    return best;
}

/// the share of pixels a mask holds above its threshold, and its edge (pixels whose neighbour across or down is on the
/// other side) per pixel inside: a ragged, broken mask has more edge for the same share
pub fn edgePerArea(mask: []const f32, n: usize, thr: f32) f32 {
    var inside: usize = 0;
    var edge: usize = 0;
    for (0..n) |y| {
        for (0..n) |x| {
            const a = mask[y * n + x] > thr;
            if (a) inside += 1;
            const b = mask[y * n + (x + 1) % n] > thr;
            const c = mask[((y + 1) % n) * n + x] > thr;
            if (a != b) edge += 1;
            if (a != c) edge += 1;
        }
    }
    return @as(f32, @floatFromInt(edge)) / @as(f32, @floatFromInt(@max(1, inside)));
}

/// the value a mask has at the given share from the top (its threshold for that coverage)
pub fn quantile(t: []const f32, q: f32) f32 {
    const s = sorted(t);
    defer alloc.free(s);
    const i: usize = @intFromFloat(@min(@as(f32, @floatFromInt(s.len - 1)), @max(0.0, q * @as(f32, @floatFromInt(s.len - 1)))));
    return s[i];
}

/// how far apart along one axis the mask's values stay alike: the lag (in pixels, up to n/4) where the mask's
/// correlation with itself moved that far falls under one half
pub fn corrLength(mask: []const f32, n: usize, down: bool) f32 {
    var m: f64 = 0;
    for (mask) |v| m += v;
    m /= @floatFromInt(n * n);
    var v0: f64 = 0;
    for (mask) |v| v0 += (v - m) * (v - m);
    if (v0 <= 0) return 0;
    var lag: usize = 1;
    while (lag < n / 4) : (lag += 1) {
        var s: f64 = 0;
        var y: usize = 0;
        while (y < n) : (y += 2) {
            var x: usize = 0;
            while (x < n) : (x += 2) {
                const a = mask[y * n + x];
                const b = if (down) mask[((y + lag) % n) * n + x] else mask[y * n + (x + lag) % n];
                s += (a - m) * (b - m);
            }
        }
        if (4.0 * s / v0 < 0.5) return @floatFromInt(lag);
    }
    return @floatFromInt(n / 4);
}

/// How often the band of detail between blurs r1 and r2 changes sign along the rows (across) or the columns (down),
/// per 100 pixels: how many features of that band lie across a line of the picture (the noise's frequency).
pub fn bandCross(t: []const f32, n: usize, r1: usize, r2: usize, across: bool) f32 {
    const a = blur(t, n, r1);
    defer alloc.free(a);
    const b = blur(t, n, r2);
    defer alloc.free(b);
    var cnt: usize = 0;
    for (0..n) |k| {
        var prev: f32 = 0;
        for (0..n) |m| {
            const i = if (across) k * n + m else m * n + k;
            const d = a[i] - b[i];
            if (m > 0 and ((d > 0) != (prev > 0))) cnt += 1;
            prev = d;
        }
    }
    return 100.0 * @as(f32, @floatFromInt(cnt)) / @as(f32, @floatFromInt(n * n));
}

/// the fine detail's spread over the coarse detail's: the picture less its blur of 1, against the blur of 1 less the
/// blur of 8 (how strong the finest octaves are against the coarse ones: the fall of the octaves)
pub fn detailRatio(t: []const f32, n: usize) f32 {
    const a = blur(t, n, 1);
    defer alloc.free(a);
    const b = blur(t, n, 8);
    defer alloc.free(b);
    var f: f64 = 0;
    var c: f64 = 0;
    for (0..n * n) |i| {
        f += (t[i] - a[i]) * (t[i] - a[i]);
        c += (a[i] - b[i]) * (a[i] - b[i]);
    }
    return @floatCast(@sqrt(f / (c + 1e-12)));
}

/// How clearly lines run (the structure tensor's coherence, Bigun and Granlund 1987): the mean over the picture of
/// the tensor's anisotropy (0 for spots and blotches, 1 for parallel lines), the tensor smoothed over 2r after a blur of r.
pub fn coherence(t: []const f32, n: usize, r: usize) f32 {
    const b = blur(t, n, r);
    defer alloc.free(b);
    const jx = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(jx);
    const jy = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(jy);
    const jz = alloc.alloc(f32, n * n) catch unreachable;
    defer alloc.free(jz);
    for (0..n) |y| {
        for (0..n) |x| {
            const gx = b[y * n + (x + 1) % n] - b[y * n + (x + n - 1) % n];
            const gy = b[((y + 1) % n) * n + x] - b[((y + n - 1) % n) * n + x];
            jx[y * n + x] = gx * gx - gy * gy;
            jy[y * n + x] = 2 * gx * gy;
            jz[y * n + x] = gx * gx + gy * gy;
        }
    }
    const sx = blur(jx, n, 2 * r);
    defer alloc.free(sx);
    const sy = blur(jy, n, 2 * r);
    defer alloc.free(sy);
    const sz = blur(jz, n, 2 * r);
    defer alloc.free(sz);
    var num: f64 = 0;
    var den: f64 = 0;
    for (0..n * n) |i| {
        num += @sqrt(sx[i] * sx[i] + sy[i] * sy[i]);
        den += sz[i];
    }
    return @floatCast(num / (den + 1e-12));
}

pub const NBAND = 7;
/// The detail's strength per octave: the picture halved again and again (means of 2 by 2), and in each octave the
/// spread of what the halving lost (the Laplacian pyramid of Burt and Adelson 1983); the log of each. Milestone 1's
/// noise reading measured the same per octave; here the whole row of octaves is what a noise must give back.
pub fn octaves(t: []const f32, n: usize) [NBAND]f32 {
    var out = [_]f32{0} ** NBAND;
    var cur = alloc.alloc(f32, n * n) catch unreachable;
    @memcpy(cur, t);
    var m = n;
    var k: usize = 0;
    while (k < NBAND and m >= 4) : (k += 1) {
        const h = m / 2;
        const nxt = alloc.alloc(f32, h * h) catch unreachable;
        for (0..h) |y| {
            for (0..h) |x| nxt[y * h + x] = 0.25 * (cur[2 * y * m + 2 * x] + cur[2 * y * m + 2 * x + 1] + cur[(2 * y + 1) * m + 2 * x] + cur[(2 * y + 1) * m + 2 * x + 1]);
        }
        var v: f64 = 0;
        for (0..m) |y| {
            for (0..m) |x| {
                const d = cur[y * m + x] - nxt[(y / 2) * h + x / 2];
                v += d * d;
            }
        }
        out[k] = @floatCast(@log(v / @as(f64, @floatFromInt(m * m)) + 1e-12));
        alloc.free(cur);
        cur = nxt;
        m = h;
    }
    alloc.free(cur);
    return out;
}

pub fn octDist(a: [NBAND]f32, b: [NBAND]f32) f32 {
    var s: f32 = 0;
    for (a, b) |x, y| s += (x - y) * (x - y);
    return s;
}

/// How much of the cell's edges run on the diagonals: the structure tensor's off-diagonal part over its trace,
/// |sum gx gy| over sum (gx^2 + gy^2) / 2, the largest of the cell's four quarters (a lozenge turned one way in one
/// quarter and the other way in the next still counts). Upright shapes (squares, bricks, slabs) give near 0.
pub fn diagonal(cell: []const f32, cw: usize, ch: usize) f32 {
    var best: f32 = 0;
    for (0..2) |qy| {
        for (0..2) |qx| {
            var sxy: f64 = 0;
            var sxx: f64 = 0;
            for (qy * ch / 2..(qy + 1) * ch / 2) |y| {
                for (qx * cw / 2..(qx + 1) * cw / 2) |x| {
                    const gx: f64 = cell[y * cw + (x + 1) % cw] - cell[y * cw + (x + cw - 1) % cw];
                    const gy: f64 = cell[((y + 1) % ch) * cw + x] - cell[((y + ch - 1) % ch) * cw + x];
                    sxy += gx * gy;
                    sxx += gx * gx + gy * gy;
                }
            }
            const d: f32 = @floatCast(2.0 * @abs(sxy) / (sxx + 1e-12));
            best = @max(best, d);
        }
    }
    return best;
}
