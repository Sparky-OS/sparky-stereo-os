#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# probe.py COMMAND ...: one step of the translucency probe inside a running Plasma session of the rig.
#   wall PATH [MODE]     set every desktop's wallpaper (org.kde.image, FillMode 2) and wait until a capture shows it
#   panel SPEC           set panel properties ("floating=true;opacity=translucent;height=36"), print them back
#   panels               print every panel's location, height, floating and opacity
#   windows TAG          print KWin's windows (kind and frame) as JSON, read back from the session log
#   waitwin TAG KEY [N]  poll KWin until a window with KEY true (dock, notification, popup, dialog ...) exists and its
#                        frame is the same in two reads; prints the windows
#   shot NAME            capture Virtual-0 into $CASE/NAME.png (both eyes side by side on a 3D output)
#   notify               show a lasting notification; prints its id
#   unnotify ID          close it
#   launcher             open (or close) the panel's application launcher
# Every wait polls what it reads, with a deadline; a step that cannot do its job exits non-zero and says why.
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, "/rig-scripts")
import numpy as np
from capture import capture
from gi.repository import Gio, GLib
from PIL import Image

CASE = os.environ["CASE"]
LOG = os.path.join(CASE, "session.log")
HERE = os.path.dirname(os.path.abspath(__file__))
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)


def call(dest, path, iface, method, args=None, sig=None, reply="()", timeout=30000):
    params = GLib.Variant(sig, args) if sig else None
    r = bus.call_sync(dest, path, iface, method, params, GLib.VariantType(reply), Gio.DBusCallFlags.NONE, timeout, None)
    return r.unpack()


def evaluate(js):
    return call("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell", "evaluateScript", (js,), "(s)", "(s)")[0]


def grab(name=None):
    info, px = capture("CaptureScreen", ("Virtual-0",))
    if name:
        Image.fromarray(px).save(os.path.join(CASE, name + ".png"))
        with open(os.path.join(CASE, name + ".json"), "w") as f:
            json.dump({k: (v if isinstance(v, (int, float, str, bool)) else str(v)) for k, v in info.items()}, f)
    return px


def windows(tag):
    src = open(os.path.join(HERE, "winlog/contents/code/main.js")).read().replace("TAGVALUE", tag)
    path = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), f"probewin-{tag}.js")
    open(path, "w").write(src)
    name = "probewin-" + tag
    sid = call("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "loadScript", (path, name), "(ss)", "(i)")[0]
    call("org.kde.KWin", f"/Scripting/Script{sid}", "org.kde.kwin.Script", "run")
    deadline = time.time() + 20
    out = []
    while time.time() < deadline:
        lines = [l for l in open(LOG, errors="replace") if f"PROBEWIN {tag} " in l]
        if any(l.rstrip().endswith(f"PROBEWIN {tag} END") or f"PROBEWIN {tag} END" in l for l in lines):
            for l in lines:
                j = l.split(f"PROBEWIN {tag} ", 1)[1].strip()
                if j.startswith("{"):
                    out.append(json.loads(j))
            break
        time.sleep(0.2)
    call("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "unloadScript", (name,), "(s)", "(b)")
    if not out:
        sys.exit(f"windows {tag}: KWin printed nothing within 20 s")
    return out


def waitwin(tag, key, n=1, timeout=45):
    deadline = time.time() + timeout
    last = None
    i = 0
    while time.time() < deadline:
        i += 1
        ws = windows(f"{tag}{i}")
        if key.startswith("type:"):
            hits = [w for w in ws if w.get("type") == int(key[5:])]  # KWin's window types, 18 = an applet's pop-up
        else:
            hits = [w for w in ws if w.get(key)]
        frames = sorted((w["x"], w["y"], w["w"], w["h"]) for w in hits)
        if len(hits) >= n and frames == last:
            return ws
        last = frames
        time.sleep(0.5)
    sys.exit(f"waitwin {tag}: no {n} stable window(s) with {key} within {timeout} s")


def wall(path, mode=2):
    js = ("var ds = desktops(); for (var i = 0; i < ds.length; i++) { var d = ds[i]; d.wallpaperPlugin = 'org.kde.image';"
          " d.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General']; d.writeConfig('Image', 'file://%s');"
          " d.writeConfig('FillMode', %d); }" % (path, mode))
    evaluate(js)
    target = None
    img = Image.open(path).convert("RGB")
    # the expected picture of the rows above the panel area: the wallpaper scaled to the output (FillMode 2 on a
    # 16:9 picture is a plain scale); compare a band of the top rows, away from every window the probe opens
    deadline = time.time() + 40
    prev = None
    while time.time() < deadline:
        px = grab()
        h, w = px.shape[0], px.shape[1]
        if target is None or target.shape[1] != w:
            ew = w // 2 if w > 2 * h else w  # one eye of a 3D output
            target = np.asarray(img.resize((ew, h), Image.BILINEAR)).astype(int)
        ew = target.shape[1]
        # the screen above the panel's band, per pixel; the median ignores what stands on the desktop (icons,
        # widgets: a minority of it). A 3D output sinks the wallpaper: each eye is shifted and its edge columns cut,
        # so the left eye is matched over horizontal shifts of up to 12 px
        top = h * 3 // 4
        band = px[10:top:4, 40:ew - 40:4].astype(int)
        diff = min(float(np.median(np.abs(band - target[10:top:4, 40 + dx:ew - 40 + dx:4]).max(axis=2)))
                   for dx in range(-12, 13, 2))
        same = prev is not None and np.array_equal(prev, px)
        if diff < 6 and same:
            print(json.dumps({"wall": path, "band_diff": round(float(diff), 2)}))
            return
        prev = px
        time.sleep(0.4)
    sys.exit(f"wall {path}: the capture did not show it within 40 s (band difference {diff:.1f})")


def panel(spec):
    sets = []
    for kv in spec.split(";"):
        if not kv:
            continue
        k, v = kv.split("=", 1)
        v = v if v in ("true", "false") or v.lstrip("-").isdigit() else json.dumps(v)
        sets.append(f"p[i].{k} = {v};")
    js = "var p = panels(); for (var i = 0; i < p.length; i++) { %s }" % " ".join(sets)
    evaluate(js)


def panels():
    js = ("var p = panels(); var o = []; for (var i = 0; i < p.length; i++) o.push({location: p[i].location, height: p[i].height,"
          " floating: p[i].floating, opacity: p[i].opacity, alignment: p[i].alignment}); print(JSON.stringify(o));")
    return json.loads(evaluate(js).strip() or "[]")


def main():
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "wall":
        wall(args[0], int(args[1]) if len(args) > 1 else 2)
    elif cmd == "panel":
        panel(args[0])
        time.sleep(0.5)
        print(json.dumps(panels()))
    elif cmd == "panels":
        print(json.dumps(panels()))
    elif cmd == "windows":
        print(json.dumps(windows(args[0])))
    elif cmd == "waitwin":
        print(json.dumps(waitwin(args[0], args[1], int(args[2]) if len(args) > 2 else 1)))
    elif cmd == "shot":
        grab(args[0])
    elif cmd == "notify":
        r = subprocess.run(["notify-send", "-p", "-t", "0", "-a", "Kubabbar probe", "Translucency probe",
                            "The quick brown fox jumps over the lazy dog"], capture_output=True, text=True, check=True)
        print(r.stdout.strip())
    elif cmd == "unnotify":
        call("org.freedesktop.Notifications", "/org/freedesktop/Notifications", "org.freedesktop.Notifications",
             "CloseNotification", (int(args[0]),), "(u)")
    elif cmd == "place":
        # place CAPTION X Y W H: KWin sets the window's frame (a client cannot place itself on Wayland)
        cap, x, y, w, h = args[0], *map(int, args[1:5])
        js = ("var ws = workspace.stackingOrder; for (var i = 0; i < ws.length; i++) { if (ws[i].caption == %s) {"
              " ws[i].frameGeometry = {x: %d, y: %d, width: %d, height: %d}; } }" % (json.dumps(cap), x, y, w, h))
        path = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "probeplace.js")
        open(path, "w").write(js)
        sid = call("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "loadScript", (path, "probeplace"), "(ss)", "(i)")[0]
        call("org.kde.KWin", f"/Scripting/Script{sid}", "org.kde.kwin.Script", "run")
        time.sleep(0.3)
        call("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "unloadScript", ("probeplace",), "(s)", "(b)")
    elif cmd == "activate":
        js = ("var ws = workspace.stackingOrder; for (var i = 0; i < ws.length; i++) { if (ws[i].caption == %s)"
              " workspace.activeWindow = ws[i]; }" % json.dumps(args[0]))
        path = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "probeactivate.js")
        open(path, "w").write(js)
        sid = call("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "loadScript", (path, "probeactivate"), "(ss)", "(i)")[0]
        call("org.kde.KWin", f"/Scripting/Script{sid}", "org.kde.kwin.Script", "run")
        time.sleep(0.3)
        call("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "unloadScript", ("probeactivate",), "(s)", "(b)")
    elif cmd == "launcher":
        call("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell", "activateLauncherMenu")
    else:
        sys.exit(f"unknown command {cmd}")


main()
