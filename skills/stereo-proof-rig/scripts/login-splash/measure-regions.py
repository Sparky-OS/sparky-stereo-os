#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Measure named image regions against a plain capture, in both eyes.

Usage: measure-regions.py PAIR.pns PLAIN.png REGIONS.json
Regions name a box [x0,y0,x1,y1] and predicted right-minus-left disparity.
The gradient mask follows boundaries rather than a uniform box interior.
"""
import json
import sys
import numpy as np
from PIL import Image


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


pair, plain = map(load, sys.argv[1:3])
height, width = plain.shape[:2]
if pair.shape != (height, 2 * width, 3):
    raise SystemExit("capture is not two views of the reference size")
results = {}
failed = False
for region in json.load(open(sys.argv[3])):
    if region.get("method") == "boundary":
        measured = {}
        for name, eye in (("reference", plain), ("left", pair[:, :width]), ("right", pair[:, width:])):
            positions = {}
            for axis, key in ((1, "x_edge"), (0, "y_edge")):
                x0, y0, x1, y1 = region[key]
                patch = eye[y0:y1, x0:x1].mean(axis=2)
                profile = patch.mean(axis=0 if axis == 1 else 1)
                derivative = np.abs(np.diff(profile))
                peak = int(derivative.argmax())
                if derivative[peak] < 5:
                    raise SystemExit("boundary lacks sufficient contrast: " + region["name"])
                positions["x" if axis == 1 else "y"] = peak + (x0 if axis == 1 else y0)
            measured[name] = positions
        disparity = measured["right"]["x"] - measured["left"]["x"]
        vertical = measured["right"]["y"] - measured["left"]["y"]
        centre = (measured["right"]["x"] + measured["left"]["x"]) / 2 - measured["reference"]["x"]
        passed = disparity == region["predicted"] and vertical == 0 and centre == 0
        failed |= not passed
        results[region["name"]] = {"method": "boundary derivative peak", "predicted": region["predicted"],
                                   "observed": disparity, "vertical_predicted": 0, "vertical_observed": vertical,
                                   "centre_shift": centre, "pass": passed, **measured}
        continue
    x0, y0, x1, y1 = region["box"]
    reference = plain[y0:y1, x0:x1]
    gray = reference.mean(axis=2)
    gradient = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1])) + np.abs(np.diff(gray, axis=0, prepend=gray[:1]))
    mask = gradient >= max(1, np.percentile(gradient, 90))
    if mask.sum() < 10:
        raise SystemExit("region lacks enough visible boundaries: " + region["name"])
    measured = {}
    for name, eye in (("left", pair[:, :width]), ("right", pair[:, width:])):
        scores = []
        for dy in range(-3, 4):
            for dx in range(-24, 25):
                observed = eye[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
                if region.get("normalize_mean"):
                    delta = (observed - observed.mean()) - (reference - reference.mean())
                else:
                    delta = observed - reference
                scores.append((float(np.abs(delta)[mask].mean()), dx, dy))
        scores.sort()
        error, dx, dy = scores[0]
        measured[name] = {"x": dx, "y": dy, "error": round(error, 4), "next_error": round(scores[1][0], 4)}
    disparity = measured["right"]["x"] - measured["left"]["x"]
    vertical = measured["right"]["y"] - measured["left"]["y"]
    passed = disparity == region["predicted"] and vertical == 0 and (measured["left"]["x"] + measured["right"]["x"]) == 0
    failed |= not passed
    results[region["name"]] = {"predicted": region["predicted"], "observed": disparity,
                               "vertical_predicted": 0, "vertical_observed": vertical,
                               "centre_shift": (measured["left"]["x"] + measured["right"]["x"]) / 2,
                               "mask_pixels": int(mask.sum()), "pass": passed, **measured}
print(json.dumps(results, indent=2))
raise SystemExit(int(failed))
