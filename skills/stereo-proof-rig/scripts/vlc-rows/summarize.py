#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""summarize.py ROWDIR...: one line per row: kind, the captures with the picture, the notice (first and last second), the volume read through MPRIS
before and after the Up key, whether VLC was still there at the end (state.json) and how it ended (vlc.rc)."""
import json, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
for row in sys.argv[1:]:
    name = os.path.basename(row.rstrip("/"))
    kind = "audio" if "audio" in name else "3d" if ("3d" in name or name.startswith("l-")) else "2d"
    out = subprocess.run([sys.executable, os.path.join(here, "evaluate.py"), row, kind, "--summary"], capture_output=True, text=True).stdout
    try: e = json.loads(out)
    except Exception: e = {"error": out[:80]}
    vols = []
    try:
        for l in open(os.path.join(row, "vol.jsonl")):
            vols.append(round(json.loads(l)["volume"], 3))
    except Exception: pass
    st = ""
    try: st = json.load(open(os.path.join(row, "state.json"))).get("status", json.load(open(os.path.join(row, "state.json"))).get("error", ""))
    except Exception: st = "?"
    rc = ""
    try: rc = open(os.path.join(row, "vlc.rc")).read().split()[-1]
    except Exception: rc = "-"
    print(f"{name:20s} {kind:5s} pic {e.get('with_picture')}/{e.get('captures')} notice {e.get('with_notice')} first {e.get('notice_first_s')} last {e.get('notice_last_s')} maxpx {e.get('max_text_pixels')}  volume {vols}  end: {st}  rc {rc}")
