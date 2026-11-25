#!/usr/bin/env python3
# proof-pair.py CAPTURE WINDOWS.json OUT.pns [MARK_PNS STEREO_VERIFY]: the Welcome window cut from both eyes of a 3D
# output's capture (the same frame in each eye, nothing resized), saved full side by side, left eye first, marked with
# PNG's sTER chunk by the proof rig's mark_pns.py and read back by the pictures skill's stereo_verify.py.
import json
import subprocess
import sys
import tempfile

from PIL import Image

capture, windows, out = sys.argv[1:4]
mark = sys.argv[4] if len(sys.argv) > 4 else None
verify = sys.argv[5] if len(sys.argv) > 5 else None
data = json.load(open(windows))
frame = next(w["fg"] for w in data["windows"] if w["cls"] in ("org.kde.plasma-welcome", "plasma-welcome"))
x, y, w, h = frame
w -= w % 8
im = Image.open(capture).convert("RGB")
half = im.width // 2
pair = Image.new("RGB", (2 * w, h))
pair.paste(im.crop((x, y, x + w, y + h)), (0, 0))
pair.paste(im.crop((half + x, y, half + x + w, y + h)), (w, 0))
with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
    pair.save(tmp.name)
    subprocess.run([sys.executable, "-I", mark, tmp.name, out], check=True)
if verify:
    subprocess.run([sys.executable, "-I", verify, "pns", out], check=True)
