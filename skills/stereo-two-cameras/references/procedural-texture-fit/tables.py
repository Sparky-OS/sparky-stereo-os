#!/usr/bin/env python3
"""Print the study's tables from the fit's JSON files, and make one contact sheet.

Usage: tables.py RESULTS_DIR [SHEET.png]
"""
import glob
import json
import sys

out = sys.argv[1]
order = ["concrete_floor_02", "plaster_grey_04", "floor_tiles_06", "red_brick_03", "bark_brown_02",
         "coast_sand_rocks_02", "control-ktg", "control-lattice", "control-white"]
res = {r["name"]: r for r in (json.load(open(f)) for f in glob.glob(out + "/*.json"))}
names = [n for n in order if n in res]


def kb(n):
    return "%.1f" % (n / 1024.0)


def pick(r, start):
    return next(p for p in r["procedures"] if p["procedure"].startswith(start))


print("### Table 1: what the picture costs alone, and what the procedure plus its remainder costs (KiB)\n")
print("| Picture | Alone, lossless | Alone, JPEG q90 (dB) | Procedure | Bytes | Remainder, lossless | Remainder, JPEG at the same dB | Lossless: change against the flat colour | JPEG: change against alone |")
print("|---|---|---|---|---|---|---|---|---|")
for n in names:
    r = res[n]
    flat = pick(r, "flat")
    for p in r["procedures"]:
        if p["procedure"].startswith(("16 ", "256 ", "16x16", "64x64")):
            continue
        dl = 100.0 * (p["remainder_png"] + p["procedure_bytes"] - flat["remainder_png"] - 3) / (flat["remainder_png"] + 3)
        rj = p["remainder_jpeg"]  # None when no JPEG quality reaches the target
        dj = "%+.1f %%" % (100.0 * (rj["bytes"] + p["procedure_bytes"] - r["direct_jpeg_q90"]["bytes"]) / r["direct_jpeg_q90"]["bytes"]) if rj else "not reached"
        print("| %s | %s | %s (%.2f) | %s | %d | %s | %s | %+.1f %% | %s |" % (
            n, kb(r["direct_png"]), kb(r["direct_jpeg_q90"]["bytes"]), r["direct_jpeg_q90"]["psnr"],
            p["procedure"], p["procedure_bytes"], kb(p["remainder_png"]), kb(rj["bytes"]) if rj else "not reached", dl, dj))

print("\n### Table 2: how close the procedure alone is (PSNR in dB, per size of the picture)\n")
print("| Picture | Procedure | Bytes | 2048 | 1024 | 512 | 256 | 128 | 64 | 32 | 16 | 8 | Spectrum gap (dB) | Histogram gap (levels) |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for n in names:
    for p in res[n]["procedures"]:
        print("| %s | %s | %d | %s | %.1f | %.1f |" % (n, p["procedure"], p["procedure_bytes"],
              " | ".join("%.1f" % v for v in p["psnr_per_level"]), p["spectrum_gap_db"], p["histogram_gap_levels"]))

print("\n### Table 3: what the fit chose for OpenKTG's Noise\n")
print("| Picture | freq | octaves | fadeoff | noise | abs | seed | best seed correlation | second best | locked | operator against model (levels) |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for n in names:
    q = pick(res[n], "OpenKTG")["params"]
    print("| %s | %d | %d | %.4g | %s | %s | %d | %.3f | %.3f | %s | %.2f |" % (
        n, q["freq"], q["oct"], q["fadeoff"], q["noise"], "yes" if q["abs"] else "no", q["seed"],
        q["seed_correlation"], q["second_best_seed_correlation"], "yes" if q["seed_locked"] else "no",
        q["operator_against_model_levels"]))

if len(sys.argv) > 2:
    from PIL import Image
    sheet = Image.new("RGB", (len(names) * 260, 3 * 260), "white")
    for i, n in enumerate(names):
        for j, tag in enumerate(("picture", "ktg", "cos64")):
            sheet.paste(Image.open(f"{out}/{n}-{tag}.png").resize((256, 256), Image.BOX), (i * 260 + 2, j * 260 + 2))
    sheet.save(sys.argv[2])
