#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""verdict.py OUT CASE: compare the player's state before and after the input; exit 0 only when it changed as the case expects."""
import json, sys
out, case = sys.argv[1:3]
def load(n):
    try:
        return json.load(open("%s/%s.json" % (out, n)))
    except Exception as e:
        return {"error": str(e)}
b, a = load("state1"), load("state2")
def kwin_fs():
    try:
        w = [w for w in (load("win2")["windows"] or []) if w["normal"] and not w["popup"] and "xev" not in w["caption"].lower() and "event tester" not in w["caption"].lower()]
        return any(x["fs"] for x in w)
    except Exception:
        return None
kfs = kwin_fs()
if case in ("dbl", "f"):
    ok = b.get("fullscreen") is False and a.get("fullscreen") is True and kfs is True
elif case == "esc":
    ok = b.get("fullscreen") is True and a.get("fullscreen") is False and kfs is False
elif case == "space":
    ok = b.get("status") == "Playing" and a.get("status") == "Paused"
elif case == "neg":
    try:
        got = "KeyPress" in open(out + "/xev.log", errors="replace").read()
    except OSError:
        got = False
    ok = b.get("status") == "Playing" and a.get("status") == "Playing" and got
    print(json.dumps({"case": case, "pass": ok, "xev_saw_key": got, "before": b, "after": a})); sys.exit(0 if ok else 1)
else:
    ok = False
print(json.dumps({"case": case, "pass": ok, "kwin_window_fullscreen": kfs, "before": b, "after": a}))
sys.exit(0 if ok else 1)
