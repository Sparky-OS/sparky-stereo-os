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
# the output's scale (SCALE, as kb-login.sh set it): KWin's geometry is logical, captures are in device pixels
SCALE = float(os.environ.get("SCALE", "1") or 1)
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
    # the same sentence with its diacritic, by the keyboard's own long press: "n" held, the finger slides to "ń" (the key's
    # alternativeKeys "nń"), one key's width to the right
    "pl-long": {"layout": STD + "/pl_PL/main.qml", "keys": "dzień dobry", "expect": "Dzień dobry", "long": {"ń": ["n", "m"]}},
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
    # upstream's reworked keyboard as KWin's input method, converting by itself (the smoke for Daniel's lead of 2026-11-25);
    # the key finder reads key positions from a 6.7 layout of the same rows (mounted at /hint)
    "ja-upstream": {"layout": "/hint/fallback.qml", "keys": "nihongo  ", "finish": ["candidate", "enter"], "expect": "日本語"},
    "zh_CN-upstream": {"layout": "/hint/fallback.qml", "keys": "zhongwen", "finish": ["candidate"], "expect": "中文"},
    "ko-upstream": {"layout": "/hint/ko.qml", "keys": "gksrnrdj", "finish": ["enter"], "expect": "한국어"},
    "show-only": {"layout": "/hint/fallback.qml", "keys": "", "expect": ""},
    # the candidate pages by touch: Mozc hands a page at a time (the bar's "›" turns it), Pinyin all candidates at once (the
    # bar's row is swiped); the candidate touched is read from the bridge's log of what Fcitx 5 handed over
    "ja-pages": {"layout": FCX + "/fallback/main.qml", "im": "mozc", "keys": "nihongo  ", "finish": ["nextpage", "page-first", "enter"], "expect": None},
    "zh_CN-swipe": {"layout": FCX + "/fallback/main.qml", "im": "pinyin", "keys": "zhongwen", "finish": ["swipe", "visible-first", "rest-first"], "expect": None},
    # the same with upstream's own layout files as the key finder's hint, and the first candidate of upstream's strip touched
    "ja-upstream2": {"layout": "/usr/share/plasma/keyboard/keyboardpackages/org.kde.plasma.keyboard.ja_JP/contents/layouts/Romaji.qml",
                     "keys": "nihongo ", "finish": ["touch:35,730", "enter"], "expect": "日本語"},
    "zh_CN-upstream2": {"layout": "/hint/fallback.qml", "keys": "zhongwen", "finish": ["touch:35,730"], "expect": "中文"},
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
    x, y, w, h = [int(v * SCALE) for v in cg]
    return int((np.abs(a[y:y + h, x:x + w] - np.array([247, 159, 82])).max(axis=2) <= 12).sum())

def read_doc():
    if TARGET in ("konsole", "zenity"):
        # the line ends the program's read (a second Enter after the commit); zenity prints the entry when OK is taken
        if not os.path.exists(APP_OUT) or os.path.getsize(APP_OUT) == 0:
            touch.run("t:%d,%d s:2500" % keys_enter()) if keys_enter() else None
        try:
            with open(APP_OUT, encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
    if TARGET in ("systemsettings", "browser"):
        return None
    try:
        with open(DOC, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

LAST_KEYS = {}
def keys_enter():
    return LAST_KEYS.get("EnterKey")

def find_keys(win, tag, bar, layout=None):
    # the keyboard fades in and its keys light up when touched: capture again until every row of keys matches the layout
    x, y, w, h = [int(round(v * SCALE)) for v in win["fg"]]
    for attempt in range(8):
        time.sleep(1.0)
        pic = shot(tag)
        out = subprocess.run(["python3", os.path.join(LANE, "keys.py"), layout or plan["layout"], pic, "%d,%d,%d,%d" % (x, y, w, h)] + (["--bar"] if bar else []),
                             capture_output=True, text=True, timeout=60)
        with open(os.path.join(CASE, "keys-%s.json" % tag), "w") as f:
            f.write(out.stdout or out.stderr)
        found = json.loads(out.stdout)
        if SCALE != 1:
            # back to logical coordinates, where touches land
            for r in found.get("rows", []):
                for k in r.get("keys", []):
                    k["x"], k["y"] = k["x"] / SCALE, k["y"] / SCALE
            for b in found.get("bar", []) or []:
                b["x"], b["y"] = b["x"] / SCALE, b["y"] / SCALE
        if found["rows"] and not any("mismatch" in r for r in found["rows"]):
            break
    step("keys", tag=tag, attempts=attempt + 1, rows=[r.get("runs") for r in found["rows"]])
    return found

def logged_candidates():
    # the last list the bridge logged: "Fcitx 5 candidates: QList("日本語", ...) page ... previous ... next ..."
    import re
    last = None
    try:
        for line in open(LOG, errors="replace"):
            if "Fcitx 5 candidates:" in line:
                last = line
    except FileNotFoundError:
        return None
    if last is None:
        return None
    body = last.split("Fcitx 5 candidates:", 1)[1].split(") page", 1)[0]
    return [re.sub(r"\\(.)", r"\1", m) for m in re.findall(r'"((?:[^"\\]|\\.)*)"', body)]

def without_comment(text):
    # Fcitx 5 appends a candidate's comment in brackets after a space ("ニホンゴ [カタカナ]", and nested:
    # "Ｎｉｈｏｎｇｏ [[全] アルファベット]"); the text committed is the candidate itself
    import re
    return re.sub(r"\s+\[.*\]$", "", text)

def keymap(found):
    m = {}
    for row in found["rows"]:
        for k in row.get("keys", []):
            label = k["text"] if k["name"] == "Key" else k["name"]
            if label is not None and label not in m:
                m[label] = (k["x"], k["y"])
    return m

result = {"lang": LANGC, "expect": plan["expect"], "touch": TOUCH}
# INVIEW (max, lower or full): the field is at the bottom of a window that is maximized, in the lower half of the screen or
# full screen; the document has 90 lines so that a touch near the window's bottom puts the cursor there. Kate's Wayland
# connection logs its text-input traffic (what the client is told about the keyboard) to kate-wl.log.
INVIEW = os.environ.get("INVIEW", "")
with open(DOC, "w") as f:
    if INVIEW:
        f.write("".join("%02d\n" % i for i in range(1, 91)))
# TARGET: the program typed into (Kate by default): konsole (a line read by bash into a file), zenity (GTK 4: its entry,
# printed on OK), systemsettings (its search field), browser (the Stereo Browser's address field). The field is placed
# relative to the window's client area (calibrated on captures); read back where the program allows it.
TARGET = os.environ.get("TARGET", "kate")
APP_OUT = os.path.join(CASE, "app.txt")
TARGETS = {
    "konsole": {"cmd": ["konsole", "--separate", "--hide-menubar", "-e", "bash", "-c", 'IFS= read -r line; printf "%s" "$line" > "$1"; sleep 3', "bash", APP_OUT],
                "cls": "org.kde.konsole", "field": (0.5, 0.5)},
    "zenity": {"cmd": ["bash", "-c", 'zenity --entry --title=Row71 --text=Type > "$1"', "bash", APP_OUT], "cls": "zenity", "field": (0.5, 0.53)},
    "systemsettings": {"cmd": ["systemsettings"], "cls": "systemsettings", "field": (0.10, 0.06)},
    "browser": {"cmd": ["sparky-stereo-browser", "--new-instance", "about:blank"], "cls": "sparky-stereo-browser", "field": (0.45, 0.06)},
}
WL_LOG = os.path.join(CASE, "kate-wl.log")
if TARGET == "zenity" and INVIEW:
    # the GTK 4 dialog's Wayland connection logs its text-input traffic, as Kate's does
    kate = subprocess.Popen(["bash", "-c", 'WAYLAND_DEBUG=client zenity --entry --title=Row71 --text=Type > "$1" 2> >(grep --line-buffered -E "text_input|input_panel|input_method" > "$2")',
                             "bash", APP_OUT, WL_LOG], stdout=open(os.path.join(CASE, "app.log"), "w"))
elif TARGET != "kate":
    t = TARGETS[TARGET]
    kate = subprocess.Popen(t["cmd"], stdout=open(os.path.join(CASE, "app.log"), "w"), stderr=subprocess.STDOUT)
elif INVIEW:
    kate = subprocess.Popen(["bash", "-c", 'WAYLAND_DEBUG=client exec kate -n "$1" 2> >(grep --line-buffered -E "text_input|input_panel|input_method" > "$2")', "kate",
                             DOC, os.path.join(CASE, "kate-wl.log")], stdout=open(os.path.join(CASE, "kate.log"), "w"))
else:
    kate = subprocess.Popen(["kate", "-n", DOC], stdout=open(os.path.join(CASE, "kate.log"), "w"), stderr=subprocess.STDOUT)
kw = None
want_cls = TARGETS[TARGET]["cls"] if TARGET != "kate" else "org.kde.kate"
for _ in range(90 if TARGET == "browser" else 60):
    time.sleep(0.5)
    ws = windows("kate")
    kw = next((w for w in ws if want_cls.lower() in (w.get("cls") or "").lower() and w.get("normal")), None)
    if kw:
        break
step("kate", window=kw)
if not kw:
    result.update(ok=False, why="Kate's window did not appear")
    json.dump(result, open(os.path.join(CASE, "result.json"), "w"), ensure_ascii=False, indent=1)
    sys.exit(1)
time.sleep(3)
if INVIEW:
    js = {"max": "w.setMaximize(true, true);",
          "lower": "w.setMaximize(false, false); w.frameGeometry = {x: 360, y: 540, width: 1200, height: 520};",
          "full": "w.fullScreen = true;"}[INVIEW]
    if TARGET != "kate" and INVIEW == "lower":
        # a dialog keeps its own size, its bottom edge 10 px above the screen's
        js = "w.frameGeometry = {x: 960 - Math.round(w.frameGeometry.width / 2), y: 1070 - w.frameGeometry.height, width: w.frameGeometry.width, height: w.frameGeometry.height};"
    subprocess.run(["python3", os.path.join(RIG, "kwin_script.py"), LOG,
                    'var ws = workspace.stackingOrder; for (var i = 0; i < ws.length; i++) { var w = ws[i]; '
                    'if (String(w.resourceClass).toLowerCase().indexOf("%s") >= 0 && w.normalWindow) { %s workspace.activeWindow = w; } }' % (want_cls.lower(), js)],
                   capture_output=True, timeout=30)
    time.sleep(3)
    first = kw["fg"]
    kw = next((w for w in windows("inview-placed") if want_cls.lower() in (w.get("cls") or "").lower() and w.get("normal")), kw)
    # KWin's scripting says nothing when a property name is wrong: the placement is checked, not assumed
    want = {"max": lambda g: g[2] >= 1900, "lower": lambda g: abs(g[1] - 540) <= 2 and abs(g[3] - 520) <= 2,
            "full": lambda g: g[2] >= 1920 and g[3] >= 1080}[INVIEW]
    if TARGET != "kate" and INVIEW == "lower":
        want = lambda g: g[1] + g[3] >= 1060
    result["inview"] = {"mode": INVIEW, "kate_first": first, "kate_before": kw["fg"], "placed": bool(want(kw["fg"]))}
touch = Touch()
cx, cy, cw, ch = kw["cg"]
tx, ty = int(cx + cw / 2), int(cy + ch / 3)
if TARGET != "kate":
    fx, fy = TARGETS[TARGET]["field"]
    tx, ty = int(cx + cw * fx), int(cy + ch * fy)
    shot("app-window")
if INVIEW:
    if TARGET == "kate":
        # the field at the bottom: a line just above Kate's status bar
        ty = int(cy + ch - 90)
    result["inview"]["touch"] = [tx, ty]
if INVIEW == "lower":
    # the desktop above the window takes the first touch (where it has no icon), so that the touch on the field at the
    # bottom activates the window
    touch.run("t:1700,150 s:1500")
elif INVIEW:
    # a maximized or full-screen window is already active, as a person meets it: the touches land on its field, which
    # already has the focus (the re-touch case), first at its top line
    touch.run("t:%d,%d s:1500" % (tx, int(cy + 40)))
else:
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
if INVIEW and win is not None:
    time.sleep(2)
    kafter = next((w for w in windows("inview-shown") if want_cls.lower() in (w.get("cls") or "").lower() and w.get("normal")), None)
    kbw, _ = keyboard_window(windows("inview-keyboard"))
    result["inview"].update(kate_after=kafter and kafter["fg"], keyboard=kbw and kbw["fg"])
    shot("inview-before")
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
    LAST_KEYS.update(keys)
    result["key_rows"] = [r.get("runs") for r in found["rows"]]
    result["mismatched_rows"] = [r["mismatch"] for r in found["rows"] if "mismatch" in r]
    seq = []
    for ch in plan["keys"]:
        if ch in plan.get("long", {}):
            base, beside = plan["long"][ch]
            seq.append(("long:" + ch, (keys.get(base), keys.get(beside)) if keys.get(base) and keys.get(beside) else None))
            continue
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
        for n, pos in seq:
            if n.startswith("long:"):
                (bx, by), (nx, ny) = pos
                touch.run("td:%d,%d s:1300 tm:%d,%d s:400 tu s:500" % (bx, by, bx + (nx - bx), by))
                continue
            x, y = pos
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
            elif action == "nextpage":
                bar_now = find_keys(win, "page1", True)
                buttons = sorted([b for b in bar_now["bar"] if b["button"]], key=lambda b: b["x"])
                result["page1"] = logged_candidates()
                step("page1", buttons=buttons, candidates=result["page1"])
                # the bar: the input method, the candidates, then "›" at its right end
                touch.run("t:%d,%d s:1800" % (buttons[-1]["x"], buttons[-1]["y"]))
                result["page2"] = logged_candidates()
                shot("page2")
            elif action == "page-first":
                bar_now = find_keys(win, "page2-bar", True)
                buttons = sorted([b for b in bar_now["bar"] if b["button"]], key=lambda b: b["x"])
                step("page2", buttons=buttons, candidates=result.get("page2"))
                # the bar on a later page: the input method, "‹", then the candidates
                if len(buttons) >= 3 and result.get("page2"):
                    plan["expect"] = without_comment(result["page2"][0])
                    touch.run("t:%d,%d s:1500" % (buttons[2]["x"], buttons[2]["y"]))
            elif action == "swipe":
                bar_now = find_keys(win, "list1", True)
                buttons = sorted([b for b in bar_now["bar"] if b["button"]], key=lambda b: b["x"])
                result["all_candidates"] = logged_candidates()
                result["visible_before"] = len(buttons) - 1
                y = buttons[1]["y"] if len(buttons) > 1 else buttons[0]["y"]
                touch.run("sw:1700,%d,250,%d,700 s:1500" % (y, y))
                shot("swiped")
            elif action == "visible-first":
                bar_now = find_keys(win, "list2", True)
                buttons = sorted([b for b in bar_now["bar"] if b["button"]], key=lambda b: b["x"])
                step("swiped", buttons=buttons)
                if len(buttons) >= 2:
                    touch.run("t:%d,%d s:1500" % (buttons[1]["x"], buttons[1]["y"]))
            elif action == "rest-first":
                # a candidate for part of the syllables (Pinyin's single characters) leaves the rest composing, and the
                # bar then shows the rest's candidates: the first is touched, as a person finishes the word
                time.sleep(1.0)
                bar_now = find_keys(win, "rest", True)
                buttons = sorted([b for b in bar_now["bar"] if b["button"]], key=lambda b: b["x"])
                result["rest_candidates"] = logged_candidates()
                step("rest", buttons=buttons, candidates=result["rest_candidates"])
                if len(buttons) >= 2:
                    touch.run("t:%d,%d s:1500" % (buttons[1]["x"], buttons[1]["y"]))
                    shot("rest-touched")
            elif action.startswith("touch:"):
                # a fixed place read from an earlier capture (upstream's candidate strip, which the bar finder does not read)
                touch.run("t:%s s:1500" % action.split(":", 1)[1])
                shot("touched")
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
if TARGET in ("systemsettings", "browser") and os.path.exists(os.path.join(CASE, "after-touch.png")) and os.path.exists(os.path.join(CASE, "committed.png")):
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(CASE, "after-touch.png")).convert("RGB")).astype(int)
    b = np.asarray(Image.open(os.path.join(CASE, "committed.png")).convert("RGB")).astype(int)
    # the field where the window is in each capture (KWin may have moved it clear of the keys): the touch point relative
    # to the window as it stood when touched, then that place in the window's frame after the touch and after typing
    pick = lambda ws: next((w for w in ws if want_cls.lower() in (w.get("cls") or "").lower() and w.get("normal")), None)
    wa_, wb_ = pick(ws), pick(windows("committed"))
    rx, ry = tx - kw["fg"][0], ty - kw["fg"][1]
    def strip(img, w):
        x0, y0 = max(int((w["fg"][0] + rx - 220) * SCALE), 0), max(int((w["fg"][1] + ry - 22) * SCALE), 0)
        return img[y0:y0 + int(44 * SCALE), x0:x0 + int(440 * SCALE)]
    if wa_ and wb_:
        sa, sb = strip(a, wa_), strip(b, wb_)
        h_, w_ = min(sa.shape[0], sb.shape[0]), min(sa.shape[1], sb.shape[1])
        result["field_change_px"] = int((np.abs(sb[:h_, :w_] - sa[:h_, :w_]).max(axis=2) > 24).sum())
        result["field_window"] = {"touched": kw["fg"], "after_touch": wa_["fg"], "after_typing": wb_["fg"]}
if LANGC == "zh_CN-swipe":
    # a later candidate than the visible ones, reached by the swipe: the longest candidate of Fcitx 5's list the typed text
    # starts with (a whole word, or a character for the first syllables with the rest converted after it), converted to
    # the end (no Latin letters left)
    got = (typed or "").strip()
    allc = [without_comment(c) for c in (result.get("all_candidates") or [])]
    hits = sorted((i for i, c in enumerate(allc) if c and got.startswith(c)), key=lambda i: -len(allc[i]))
    result["swiped_index"] = hits[0] if hits else None
    result["swiped_candidate"] = allc[hits[0]] if hits else None
    done = bool(got) and not any("a" <= ch.lower() <= "z" for ch in got)
    plan["expect"] = got if (result["swiped_index"] or 0) >= (result.get("visible_before") or 1) and done else "(a candidate past the visible ones, converted to the end)"
result["expect"] = plan["expect"]
# Kate ends a saved file with a newline
result["ok"] = typed is not None and (typed[:-1] if typed.endswith("\n") else typed) == plan["expect"] and result.get("preedit_px", 0) <= 20
if TARGET in ("systemsettings", "browser"):
    # not read back: the keyboard showed, the keys reached Fcitx 5 (its preedit came and went) and the field changed
    result["ok"] = bool(result.get("keyboard", {}).get("shown")) and result.get("field_change_px", 0) > 150
elif TARGET in ("konsole", "zenity"):
    # a terminal's line and a dialog's entry get no automatic capital from the keyboard (it follows the field's hints)
    result["ok"] = typed is not None and typed.strip().lower() == plan["expect"].lower()
if INVIEW and result.get("inview", {}).get("keyboard") and os.path.exists(os.path.join(CASE, "inview-before.png")):
    import numpy as np
    from PIL import Image
    iv = result["inview"]
    a = np.asarray(Image.open(os.path.join(CASE, "inview-before.png")).convert("RGB")).astype(int)
    b = np.asarray(Image.open(os.path.join(CASE, "committed.png")).convert("RGB")).astype(int)
    kx, ky, kw_, kh = [int(round(v)) for v in iv["keyboard"]]
    fx, fy, fw, fh = [int(round(v)) for v in (iv.get("kate_after") or iv["kate_before"])]
    top = max(fy, 0); bottom = min(fy + fh, ky)
    changed = (np.abs(b - a).max(axis=2) > 24)
    iv["visible_change_px"] = int(changed[top:bottom, max(fx, 0):fx + fw].sum()) if bottom > top else 0
    iv["hidden_change_px"] = int(changed[ky:ky + kh, kx:kx + kw_].sum())
    ov_h = max(0, min(fy + fh, ky + kh) - max(fy, ky)); ov_w = max(0, min(fx + fw, kx + kw_) - max(fx, kx))
    iv["overlap_px"] = int(ov_h * ov_w)
    # KWin's rule for its own panel: the focused window ends where the keys begin (full-screen windows excepted)
    iv["clear_of_keyboard"] = fy + fh <= ky + 1
    words = plan["expect"].replace(" ", "")
    iv["typed_in_file"] = typed is not None and words.lower() in typed.replace(" ", "").replace("\n", "").lower()
    try:
        # libwayland's log: "[time] {Default Queue} zwp_text_input_v2#28.input_panel_state(1, 0, 0, 0, 0)"; "->" marks
        # the client's requests. The events the client was told, by name, and the globals it was offered
        import re
        lines = list(open(os.path.join(CASE, "kate-wl.log"), errors="replace"))
        iv["text_input_events"] = sorted(set("%s.%s" % m.groups() for l in lines if "->" not in l
                                             for m in [re.search(r"(zwp_text_input_v\d)#\d+\.(\w+)\(", l)] if m))
        iv["input_panel_states"] = [l.split("input_panel_state", 1)[1].strip() for l in lines if "->" not in l and "input_panel_state(" in l][:6]
        iv["offered_input_method_globals"] = sorted(set(m.group(1) for l in lines for m in [re.search(r'global\(\d+, "(zwp_input_(?:method|panel)_v1)"', l)] if m))
    except Exception as e:
        iv["text_input_events"] = str(e)
    # the field is in view when the text typed into it can be seen: changed pixels above the keyboard (glyphs), not only
    # under it
    result["ok"] = bool(iv["typed_in_file"]) and bool(iv.get("placed"))
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
