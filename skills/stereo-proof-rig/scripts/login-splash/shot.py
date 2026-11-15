#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# shot.py OUTPUT_NAME OUT.png: one ScreenShot2 CaptureScreen of an output (both eyes side by side on a 3D output)
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from capture import capture
from PIL import Image
info, px = capture("CaptureScreen", (sys.argv[1],))
Image.fromarray(px).save(sys.argv[2])
print(json.dumps({k: (v if isinstance(v, (int, float, str, bool)) else str(v)) for k, v in info.items()}))
