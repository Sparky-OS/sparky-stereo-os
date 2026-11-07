#!/usr/bin/env python3
# pwctl.py card ADDR | profile ADDR NAME-PART | nodes ADDR : small helpers over pw-dump (JSON), no PipeWire library needed.
import json, subprocess, sys

def dump():
    return json.loads(subprocess.run(["pw-dump"], capture_output=True, text=True, timeout=15).stdout or "[]")

def key(addr):
    return addr.upper().replace(":", "_")

def card(addr):
    for o in dump():
        p = (o.get("info") or {}).get("props") or {}
        if o.get("type") == "PipeWire:Interface:Device" and key(addr) in (p.get("device.name") or "") and "bluez" in (p.get("device.name") or ""):
            return o
    return None

def profiles(c):
    out = []
    for e in (c["info"]["params"].get("EnumProfile") or []):
        out.append((e["index"], e["name"], e.get("available", "?")))
    return out

def nodes(addr):
    res = []
    for o in dump():
        p = (o.get("info") or {}).get("props") or {}
        if o.get("type") == "PipeWire:Interface:Node" and key(addr) in (p.get("node.name") or ""):
            res.append((o["id"], p.get("node.name"), p.get("media.class")))
    return res

cmd = sys.argv[1]
if cmd == "card":
    c = card(sys.argv[2])
    if not c:
        sys.exit(1)
    cur = [e["name"] for e in (c["info"]["params"].get("Profile") or [])]
    print(c["id"], "current=", cur)
    for i, n, a in profiles(c):
        print("  profile", i, n, "available=" + str(a))
elif cmd == "profile":
    c = card(sys.argv[2])
    if not c:
        sys.exit(1)
    want = sys.argv[3]
    # exact name first, then the first name that contains the part
    cand = [x for x in profiles(c) if x[1] == want] or [x for x in profiles(c) if want in x[1]]
    if not cand:
        print("no profile like", want, [x[1] for x in profiles(c)]); sys.exit(2)
    idx, name, _ = cand[0]
    r = subprocess.run(["pw-cli", "s", str(c["id"]), "Profile", "{ index: %d, save: false }" % idx], capture_output=True, text=True)
    print("set profile", idx, name, r.stdout.strip(), r.stderr.strip())
elif cmd == "nodes":
    n = nodes(sys.argv[2])
    for x in n:
        print(*x)
    sys.exit(0 if n else 1)
