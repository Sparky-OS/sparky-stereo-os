#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""FFmpeg's own reading of the ORDER 577 fixtures.

For each fixture: ffprobe's stream sample and display aspect ratios; the first frame decoded at its coded size, each
eye cut out by the fixture's packing and its circle measured with the sample aspect ratio applied (what any program
that takes FFmpeg's SAR shows); and for side by side and top and bottom the left eye rendered by ffmpeg itself
(crop, then scale by the SAR to square pixels) and measured. A right shape reads 1.0.

Usage: probe-ffmpeg.py FIXTURE_DIR [--ffmpeg PATH] [--ffprobe PATH] [--label NAME] > results.jsonl
"""
import argparse, json, os, subprocess, sys, tempfile
from fractions import Fraction
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure import shapes, eyes_from_frame

CROP = {("sbs", "lr"): "iw/2:ih:0:0", ("sbs", "rl"): "iw/2:ih:iw/2:0",
        ("tab", "lr"): "iw:ih/2:0:0", ("tab", "rl"): "iw:ih/2:0:ih/2"}


def ratio(text):
    try:
        n, d = text.split(":")
        n, d = int(n), int(d)
        return Fraction(n, d) if n > 0 and d > 0 else None
    except (ValueError, AttributeError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fixtures")
    ap.add_argument("--ffmpeg", default="ffmpeg")
    ap.add_argument("--ffprobe", default="ffprobe")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    cases = json.load(open(os.path.join(a.fixtures, "cases.json")))
    tmp = tempfile.mkdtemp()
    for name in sorted(cases):
        c = cases[name]
        path = os.path.join(a.fixtures, name + ".mkv")
        st = json.loads(subprocess.run([a.ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
                                        "stream=width,height,sample_aspect_ratio,display_aspect_ratio", "-of", "json",
                                        path], check=True, capture_output=True, text=True).stdout)["streams"][0]
        w, h = st["width"], st["height"]
        sar = ratio(st.get("sample_aspect_ratio")) or Fraction(1)
        raw = subprocess.run([a.ffmpeg, "-v", "error", "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt",
                              "rgb24", "-"], check=True, capture_output=True).stdout
        frame = np.frombuffer(raw[: w * h * 3], np.uint8).reshape(h, w, 3)
        left, right = eyes_from_frame(frame, c["packing"], c["order"])
        sx = float(sar)
        ml, mr = shapes(left, sx), shapes(right, sx)
        rendered = None
        key = (c["packing"], c["order"])
        if key in CROP:
            png = os.path.join(tmp, "eye.png")
            subprocess.run([a.ffmpeg, "-v", "error", "-y", "-i", path, "-frames:v", "1", "-vf",
                            "crop=%s,scale=w='trunc(iw*sar/2)*2':h=ih:flags=neighbor,setsar=1" % CROP[key], png],
                           check=True)
            rendered = shapes(np.asarray(Image.open(png).convert("RGB")))["circle"]
        rec = {"label": a.label, "fixture": name, "packing": c["packing"], "order": c["order"],
               "coded": [w, h], "sar": st.get("sample_aspect_ratio"), "dar": st.get("display_aspect_ratio"),
               "left_colour": ml["colour"], "right_colour": mr["colour"],
               "left_circle": ml["circle"], "left_square": ml["square"], "right_circle": mr["circle"],
               "rendered_left_circle": rendered}
        print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    main()
