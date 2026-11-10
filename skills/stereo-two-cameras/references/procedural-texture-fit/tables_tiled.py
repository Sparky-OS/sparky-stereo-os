#!/usr/bin/env python3
"""Print the tiled study's tables from the ladder, foveation and recognition JSON files.

Usage: tables_tiled.py LADDER_DIR BENCH.json
"""
import json
import sys

lad, bench = sys.argv[1], json.load(open(sys.argv[2]))
names = ["concrete_floor_02", "plaster_grey_04", "floor_tiles_06", "red_brick_03", "bark_brown_02", "coast_sand_rocks_02", "control-white"]
N = 2048
cn = [bench["noise_gradient_ns_per_pixel_octave"], bench["noise_value_ns_per_pixel_octave"]]


def cost(r, octaves=None):
    typ = 1 if r["noise"][0]["kind"].startswith("value") else 0
    o = r["noise"][0]["octaves"] if octaves is None else min(octaves, r["noise"][0]["octaves"])
    return N * N * (bench["bilinear_ns_per_pixel"] + r["cells_tiles"] / r["tiles"] * bench["cells_4_ns_per_pixel"] + cn[typ] * o) / 1e6


print("### Table 1: the ladder, rung by rung (hard tiles; every rung includes the ones above it in the table)\n")
print("| Picture | Tile | Bytes so far | PSNR | SSIM | GMSD | Spectrum gap dB | Two octaves only: PSNR | Evaluation ms (full, two octaves) | Seam ratio hard | Seam ratio windowed | PSNR windowed | Same bytes as a small JPEG: size, quality, PSNR, SSIM, GMSD |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for n in names:
    h = json.load(open(f"{lad}/{n}-hard.json"))["rungs"]
    w = json.load(open(f"{lad}/{n}-window.json"))["rungs"]
    full = two = 0.0
    for r, v in zip(h, w):
        full += cost(r)
        two += cost(r, 2)
        s = r.get("same_bytes_picture")
        sb = "%d px, q%d, %.2f, %.3f, %.3f" % (s["size"], s["quality"], s["psnr"], s["ssim"], s["gmsd"]) if s else "none fits"
        print("| %s | %d | %d | %.2f | %.3f | %.3f | %.1f | %.2f | %.0f, %.0f | %.2f | %.2f | %.2f | %s |" % (
            n, r["tile"], r["bytes_so_far"], r["psnr"], r["ssim"], r["gmsd"], r["spectrum_gap_db"], r["two_octaves"]["psnr"],
            full, two, r["seam_ratio"], v["seam_ratio"], v["psnr"], sb))

print("\n### Table 2: the ladder at the picture's lower levels (PSNR dB and SSIM; hard tiles)\n")
print("| Picture | Tile | 2048 | 1024 | 512 | 256 | 128 | 64 |")
print("|---|---|---|---|---|---|---|---|")
for n in names:
    for r in json.load(open(f"{lad}/{n}-hard.json"))["rungs"]:
        print("| %s | %d | %s |" % (n, r["tile"], " | ".join("%.1f, %.3f" % tuple(r["levels"][k]) for k in ("2048", "1024", "512", "256", "128", "64"))))

print("\n### Table 3: where each rung's error went (mean squared error, hard tiles)\n")
print("| Picture | Tile | Before the rung | After the gradient | After cells (tiles that kept them) | After noise |")
print("|---|---|---|---|---|---|")
for n in names:
    for r in json.load(open(f"{lad}/{n}-hard.json"))["rungs"]:
        print("| %s | %d | %.1f | %.1f | %.1f (%d of %d) | %.1f |" % (n, r["tile"], r["mse_before"], r["mse_after_gradient"],
              r["mse_after_gradient_cells"], r["cells_tiles"], r["tiles"], r["mse_after_noise"]))

print("\n### Table 4: one gaze point, the same rings, both schemes (before the last layer arrives)\n")
print("| Picture | Scheme | Bytes on the wire | Texels held | One-time cost ms | Fovea: PSNR, SSIM | Near: PSNR, SSIM | Far: PSNR, SSIM | Against what each ring resolves: fovea, near, far dB |")
print("|---|---|---|---|---|---|---|---|---|")
for n in names[:6]:
    f = json.load(open(f"{lad}/{n}-foveated.json"))
    rows = [("procedural ladder, foveated", f["procedural_foveated"], f["procedural_foveated"]["samples"], f["procedural_foveated"]["evaluation_ms_reference_cpu_one_thread"]),
            ("procedural ladder, finest rung everywhere", f["procedural_uniform_finest"], f["procedural_uniform_finest"]["samples"], f["procedural_uniform_finest"]["evaluation_ms_reference_cpu_one_thread"]),
            ("bitmap pyramid, foveated", f["bitmap_pyramid_foveated"], f["bitmap_pyramid_foveated"]["upload_bytes_rgba8"] // 4, f["bitmap_pyramid_foveated"]["decode_ms_pillow_one_thread"])]
    for label, d, texels, ms in rows:
        c = list(d["closeness"].values())
        print("| %s | %s | %d | %d | %.1f | %s | %s |" % (n, label, d["wire_bytes"], texels, ms,
              " | ".join("%.2f, %.3f" % (x["psnr_against_picture"], x["ssim_against_picture"]) for x in c),
              ", ".join("%.2f" % x["psnr_against_the_level_the_ring_resolves"] for x in c)))

print("\n### Table 5: everything, once the last layer has arrived (bytes, JPEG quality 90)\n")
print("| Picture | Picture | Its lower-resolution copies | Picture plus copies | Tiled pyramid, every page | Picture plus ladder to 32 px tiles | to 8 px tiles | Ladder to 32 against the copies | Ladder to 8 against the copies |")
print("|---|---|---|---|---|---|---|---|---|")
for n in names[:6]:
    t = json.load(open(f"{lad}/{n}-foveated.json"))["totals"]
    base = t["picture_plus_copies"]
    print("| %s | %d | %d (+%.1f %%) | %d | %d | %d (%+.1f %%) | %d (%+.1f %%) | %d against %d | %d against %d |" % (
        n, t["picture_jpeg_q90"], t["lower_resolution_copies"], 100 * t["lower_resolution_copies"] / t["picture_jpeg_q90"], base,
        t["tiled_pyramid_all_pages_and_tail"], t["picture_plus_ladder"]["32"], 100 * (t["picture_plus_ladder"]["32"] - base) / base,
        t["picture_plus_ladder"]["8"], 100 * (t["picture_plus_ladder"]["8"] - base) / base,
        t["ladder_bytes"]["32"], t["lower_resolution_copies"], t["ladder_bytes"]["8"], t["lower_resolution_copies"]))
