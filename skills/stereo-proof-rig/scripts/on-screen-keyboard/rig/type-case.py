#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""type-case.py: inside a rig session (row 71), touch Kate's text and type the language's sentence on the on-screen keyboard.

Env: CASE (results), LANE (this folder), RIG (the skill's stereo-proof-rig/scripts), FAKEINPUT, LANG_CASE (en, pt_BR, es, fr,
de, pl, ja, ko, zh_CN, zh_TW), SESSION_LOG (startplasma's log, where KWin's script output lands), TOUCH_KATE (0: click
Kate's text with the mouse instead, the control for "only on touch").

What it does, each step recorded in CASE/steps.jsonl and the result in CASE/result.json:
1. Kate opens CASE/typed.txt (auto save every 2 s, as set in katerc before the login).
2. One fake input connection for the whole case (fakeinput --serve): a touch on the empty desktop, then on Kate's text.
3. KWin's windows: is there a keyboard, which one (an input panel of KWin's input method, or Plasma Keyboard's layer for
   Fcitx 5), and where.
4. Its keys from the layout's QML and the capture (keys.py); for Fcitx 5 mode the bar above them.
5. For Fcitx 5 mode, the input method of the language chosen on the keyboard's own bar (a touch on the input method, a touch
   on the one wanted); the keys of the sentence; for Japanese and Chinese (China) a candidate chosen by a touch.
6. The document read back from the file Kate saved.
"""
import json, os, subprocess, sys, time

CASE = os.environ["CASE"]
LANE = os.environ.get("LANE", "/lane")
RIG = os.environ.get("RIG", "/rig")
FAKEINPUT = os.environ.get("FAKEINPUT", "/tools/fakeinput")
LANGC = os.environ["LANG_CASE"]
LOG = os.environ["SESSION_LOG"]
TOUCH = os.environ.get("TOUCH_KATE", "1") == "1"
DOC = os.path.join(CASE, "typed.txt")
STD = "/usr/share/plasma/keyboard/layouts"
FCX = "/usr/share/plasma/keyboard/layouts-fcitx"

# the sentence of each language, its layout, and for Fcitx 5 mode the engine, the keys, and how the text is finished; Plasma
# Keyboard's own auto-capitalisation (on by default) starts a document with a capital in the Latin languages
PLANS = {
    "en": {"layout": STD + "/fallback/main.qml", "keys": "the quick brown fox", "expect": "The quick brown fox"},
    "pt_BR": {"layout": STD + "/pt_BR/main.qml", "keys": "cabeça", "expect": "Cabeça"},
    "es": {"layout": STD + "/es_ES/main.qml", "keys": "el niño", "expect": "El niño"},
    "fr": {"layout": STD + "/fr_FR/main.qml", "keys": "aujourd'hui", "expect": "Aujourd'hui"},
    "de": {"layout": STD + "/de_DE/main.qml", "keys": "über äpfel und öl", "expect": "Über äpfel und öl"},
    "pl": {"layout": STD + "/pl_PL/main.qml", "keys": "dzien dobry", "expect": "Dzien dobry"},
    # Mozc converts at the first Space and lists its candidates at the second; a touch chooses one, Enter commits it. Pinyin
# commits the candidate touched. Chewing converts as the keys come and Enter commits. Hangul composes as the keys come and
# Enter commits the last syllable (a final space would be dropped by Kate's "remove trailing spaces" on save).
    "ja": {"layout": FCX + "/fallback/main.qml", "im": "mozc", "keys": "nihongo  ", "finish": ["candidate", "enter"], "expect": "日本語"},
    "ko": {"layout": FCX + "/ko_KR/main.qml", "im": "hangul", "keys": "gksrnrdj", "finish": ["enter"], "expect": "한국어"},
    "zh_CN": {"layout": FCX + "/fallback/main.qml", "im": "pinyin", "keys": "zhongwen", "finish": ["candidate"], "expect": "中文"},
    "zh_TW": {"layout": FCX + "/zh_TW/main.qml", "im": "chewing", "keys": "5j/ jp6", "finish": ["enter"], "expect": "中文"},
    # a Japanese session whose Fcitx 5 does not answer (its keyboard addon off, or the program gone): the keyboard says so
    # and its keys type plain text through KWin's fake input
    "ja-plain": {"layout": FCX + "/fallback/main.qml", "keys": "abc", "expect": "abc"},
}
plan = PLANS[LANGC]

def step(name, **kw):
    kw.update(step=name, t=round(time.time(), 3))
    with open(os.path.join(CASE, "steps.jsonl"), "a") as f:
        f.write(json.dumps(kw, ensure_ascii=False) + "\n")

def windows(tag):
    out = subprocess.run(["python3", os.path.join(LANE, "kwin-windows.py"), LOG], capture_output=True, text=True, timeout=20)
    path = os.path.join(CASE, "windows-%s.json" % tag)
    with open(path, "w") as f:
        f.write(out.stdout)
    try:
        return json.loads(out.stdout)["windows"] or []
    except Exception:
        return []

def shot(tag):
    path = os.path.join(CASE, "%s.png" % tag)
    subprocess.run(["python3", os.path.join(RIG, "login-splash", "shot.py"), "Virtual-0", path], capture_output=True, timeout=30)
    return path

def dbus(dest, path, iface, method, sig="", args=None, reply="", timeout=3000):
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    try:
        # never start a service by asking it something: a Fcitx 5 started by D-Bus activation in a session whose input
        # method is Plasma Keyboard binds KWin's input method too and takes its input panel (found by this rig)
        v = bus.call_sync(dest, path, iface, method, GLib.Variant(sig, args) if sig else None,
                          GLib.VariantType(reply) if reply else None, Gio.DBusCallFlags.NO_AUTO_START, timeout, None)
        return v.unpack() if v is not None else None
    except Exception as e:
        return "error: %s" % e

def kwin_keyboard_state():
    props = {}
    for p in ("available", "enabled", "active", "visible", "activeClientSupportsTextInput"):
        r = dbus("org.kde.KWin", "/VirtualKeyboard", "org.freedesktop.DBus.Properties", "Get", "(ss)",
                 ("org.kde.kwin.VirtualKeyboard", p), "(v)")
        props[p] = r[0] if isinstance(r, tuple) else r
    r = dbus("org.kde.KWin", "/VirtualKeyboard", "org.kde.kwin.VirtualKeyboard", "willShowOnActive", reply="(b)")
    props["willShowOnActive"] = r[0] if isinstance(r, tuple) else r
    r = dbus("org.kde.KWin", "/org/kde/KWin", "org.freedesktop.DBus.Properties", "Get", "(ss)",
             ("org.kde.KWin.TabletModeManager", "tabletMode"), "(v)")
    props["tabletMode"] = r[0] if isinstance(r, tuple) else r
    return props

def fcitx_state():
    cur = dbus("org.fcitx.Fcitx5", "/controller", "org.fcitx.Fcitx.Controller1", "CurrentInputMethod", reply="(s)")
    grp = dbus("org.fcitx.Fcitx5", "/controller", "org.fcitx.Fcitx.Controller1", "CurrentInputMethodGroup", reply="(s)")
    info = None
    if isinstance(grp, tuple):
        info = dbus("org.fcitx.Fcitx5", "/controller", "org.fcitx.Fcitx.Controller1", "InputMethodGroupInfo", "(s)", (grp[0],), "(sa(ss))")
    return {"current": cur[0] if isinstance(cur, tuple) else cur, "group": grp[0] if isinstance(grp, tuple) else grp,
            "items": [i[0] for i in info[1]] if isinstance(info, tuple) else info}

class Touch:
    """One fake input connection for the whole case (the seat's touch capability lives with it)."""
    def __init__(self):
        self.inp = os.path.join(os.environ["XDG_RUNTIME_DIR"], "fi-in")
        self.ack = os.path.join(os.environ["XDG_RUNTIME_DIR"], "fi-ack")
        for p in (self.inp, self.ack):
            if os.path.exists(p):
                os.unlink(p)
            os.mkfifo(p)
        self.proc = subprocess.Popen([FAKEINPUT, "--serve", self.inp, self.ack], stdout=open(os.path.join(CASE, "fakeinput.log"), "a"),
                                     stderr=subprocess.STDOUT)
        self.w = open(self.inp, "w")
        self.r = open(self.ack)

    def run(self, steps):
        self.w.write(steps + "\n")
        self.w.flush()
        answer = self.r.readline().strip()
        step("input", steps=steps, answer=answer)
        return answer

    def close(self):
        self.w.close()
        self.proc.wait(timeout=10)

def keyboard_window(ws):
    for w in ws:
        if w.get("deleted") or w.get("hidden"):
            continue
        if w.get("inputMethod"):
            return w, "input-panel"
        if "plasma-keyboard" in (w.get("cls") or "") or "plasma.keyboard" in (w.get("cls") or ""):
            return w, "layer"
    return None, None

def highlight_px(pic, cg):
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(pic).convert("RGB")).astype(int)
    x, y, w, h = [int(v) for v in cg]
    return int((np.abs(a[y:y + h, x:x + w] - np.array([247, 159, 82])).max(axis=2) <= 12).sum())

def read_doc():
    try:
        with open(DOC, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

def find_keys(win, tag, bar, layout=None):
    # the keyboard fades in and its keys light up when touched: capture again until every row of keys matches the layout
    x, y, w, h = [int(round(v)) for v in win["fg"]]
    for attempt in range(8):
        time.sleep(1.0)
        pic = shot(tag)
        out = subprocess.run(["python3", os.path.join(LANE, "keys.py"), layout or plan["layout"], pic, "%d,%d,%d,%d" % (x, y, w, h)] + (["--bar"] if bar else []),
                             capture_output=True, text=True, timeout=60)
        with open(os.path.join(CASE, "keys-%s.json" % tag), "w") as f:
            f.write(out.stdout or out.stderr)
        found = json.loads(out.stdout)
        if found["rows"] and not any("mismatch" in r for r in found["rows"]):
            break
    step("keys", tag=tag, attempts=attempt + 1, rows=[r.get("runs") for r in found["rows"]])
    return found

def keymap(found):
    m = {}
    for row in found["rows"]:
        for k in row.get("keys", []):
            label = k["text"] if k["name"] == "Key" else k["name"]
            if label is not None and label not in m:
                m[label] = (k["x"], k["y"])
    return m

result = {"lang": LANGC, "expect": plan["expect"], "touch": TOUCH}
open(DOC, "w").close()
kate = subprocess.Popen(["kate", "-n", DOC], stdout=open(os.path.join(CASE, "kate.log"), "w"), stderr=subprocess.STDOUT)
kw = None
for _ in range(60):
    time.sleep(0.5)
    ws = windows("kate")
    kw = next((w for w in ws if w.get("cls") == "org.kde.kate" and w.get("normal")), None)
    if kw:
        break
step("kate", window=kw)
if not kw:
    result.update(ok=False, why="Kate's window did not appear")
    json.dump(result, open(os.path.join(CASE, "result.json"), "w"), ensure_ascii=False, indent=1)
    sys.exit(1)
time.sleep(3)
touch = Touch()
cx, cy, cw, ch = kw["cg"]
tx, ty = int(cx + cw / 2), int(cy + ch / 3)
touch.run("t:%d,%d s:900" % (int(cx + cw + 40) if cx + cw + 40 < 1900 else 5, 5))
if TOUCH:
    touch.run("t:%d,%d s:2500" % (tx, ty))
else:
    touch.run("m:%d,%d s:300 b:272 s:2500" % (tx, ty))
result["kwin_after_touch"] = kwin_keyboard_state()
ws = windows("after-touch")
shot("after-touch")
win, kind = keyboard_window(ws)
result["keyboard"] = {"shown": win is not None, "kind": kind, "window": win}
result["fcitx"] = fcitx_state()
step("keyboard", shown=win is not None, kind=kind, kwin=result["kwin_after_touch"], fcitx=result["fcitx"])

typed = ""
if win is not None:
    bar = kind == "layer"
    if "im" in plan and bar:
        # the input method of the language, chosen on the keyboard's own bar; until then the keys are the layout of the
        # current input method, so the bar is found with the fallback layout
        first = find_keys(win, "before-im", True, os.path.join(FCX, "fallback", "main.qml"))
        st = fcitx_state()
        items = st.get("items") or []
        if st.get("current") != plan["im"] and plan["im"] in items and first.get("bar"):
            imb = first["bar"][0]
            touch.run("t:%d,%d s:1500" % (imb["x"], imb["y"]))
            listing = find_keys(win, "im-list", True, os.path.join(FCX, "fallback", "main.qml"))
            buttons = sorted([b for b in listing["bar"] if b["button"]], key=lambda b: b["x"])
            # the bar: the input method button, then one button per input method of the group, in order
            target = 1 + items.index(plan["im"])
            step("im-list", buttons=buttons, items=items, target=target)
            if target < len(buttons):
                touch.run("t:%d,%d s:1500" % (buttons[target]["x"], buttons[target]["y"]))
        result["fcitx_before_typing"] = fcitx_state()
    found = find_keys(win, "keys", bar)
    keys = keymap(found)
    result["key_rows"] = [r.get("runs") for r in found["rows"]]
    result["mismatched_rows"] = [r["mismatch"] for r in found["rows"] if "mismatch" in r]
    seq = []
    for ch in plan["keys"]:
        if ch == " ":
            name = "SpaceKey"
        elif ch in keys:
            name = ch
        elif ch.lower() in keys:
            seq.append(("ShiftKey", keys.get("ShiftKey")))
            name = ch.lower()
        else:
            name = None
        seq.append((name, keys.get(name) if name else None))
    missing = [n for n, p in seq if p is None]
    result["missing_keys"] = missing
    if not missing:
        for n, (x, y) in seq:
            touch.run("t:%d,%d s:350" % (x, y))
        time.sleep(1.5)
        shot("typed")
        for action in plan.get("finish", []):
            if action == "candidate":
                cand = find_keys(win, "candidates", True)
                buttons = sorted([b for b in cand["bar"] if b["button"]], key=lambda b: b["x"])
                step("candidates", buttons=buttons)
                result["candidates_shown"] = max(len(buttons) - 1, 0)
                # the bar: the input method button, then the candidates; the first is Fcitx 5's own first choice
                if len(buttons) >= 2:
                    touch.run("t:%d,%d s:1500" % (buttons[1]["x"], buttons[1]["y"]))
            elif action == "enter":
                touch.run("t:%d,%d s:1500" % keys["EnterKey"])
        shot("finished")
    time.sleep(3)
    typed = read_doc()
    # KTextEditor keeps a pending conversion (the preedit) in its buffer, so the saved file alone cannot tell committed
    # text from a conversion still open. The preedit is drawn with the highlight (247,159,82), which Kate's own tab bar
    # also uses: the measure is how many more such pixels Kate's window has than right after the touch, before any key
    # (proved: a pending conversion adds 410 to 723, committed text 2)
    result["preedit_px"] = highlight_px(shot("committed"), kw["cg"]) - highlight_px(os.path.join(CASE, "after-touch.png"), kw["cg"])
else:
    time.sleep(3)
    typed = read_doc()

result["typed"] = typed
# Kate ends a saved file with a newline
result["ok"] = typed is not None and (typed[:-1] if typed.endswith("\n") else typed) == plan["expect"] and result.get("preedit_px", 0) <= 20
result["kwin_end"] = kwin_keyboard_state()
result["fcitx_end"] = fcitx_state()
json.dump(result, open(os.path.join(CASE, "result.json"), "w"), ensure_ascii=False, indent=1)
touch.close()
kate.terminate()
try:
    kate.wait(timeout=10)
except subprocess.TimeoutExpired:
    kate.kill()
print(json.dumps({k: result[k] for k in ("lang", "keyboard", "typed", "ok") if k in result}, ensure_ascii=False))
