#!/usr/bin/python3
# make-fcitx-layouts.py SRC: Plasma Keyboard's layouts for Fcitx 5 mode (src/layouts-fcitx), made from its own
# fallback layout (src/layouts/fallback/main.qml, forked from Qt's): the same QWERTY keys, typing the same Latin keysyms,
# labelled with what Fcitx 5's engine makes of each key.
# - ko_KR: fcitx5-hangul's default keyboard, Dubeolsik (two-set): the jamo of each key, the shifted jamo as small text.
# - zh_TW: fcitx5-chewing's default keyboard, Dachen: a number row and the bopomofo and tones of each key.
# - ja_JP, zh_CN: Mozc and Pinyin read Latin letters (romaji, pinyin): the fallback layout as it is.
# Only the two main.qml are written here: src/CMakeLists.txt makes the other pages' empty .fallback markers, the links for
# ja_JP and zh_CN and the links to Plasma Keyboard's own layouts at install (a Debian source's patch cannot carry an empty
# file or a link).
# - every other locale: Plasma Keyboard's own layout, whose characters reach Fcitx 5 as keysyms (a relative link that
#   src/CMakeLists.txt makes at install: a Debian source's patch cannot carry a link).
import os, re, sys
SRC = sys.argv[1]
LAYOUTS = os.path.join(SRC, "layouts"); OUT = os.path.join(SRC, "layouts-fcitx")
PAGES = ["dialpad", "digits", "handwriting", "numbers", "symbols"]
DUBEOLSIK = dict(zip("qwertyuiopasdfghjklzxcvbnm", "ㅂㅈㄷㄱㅅㅛㅕㅑㅐㅔㅁㄴㅇㄹㅎㅗㅓㅏㅣㅋㅌㅊㅍㅠㅜㅡ"))
DUBEOLSIK_SHIFT = {"q": "ㅃ", "w": "ㅉ", "e": "ㄸ", "r": "ㄲ", "t": "ㅆ", "o": "ㅒ", "p": "ㅖ"}
DACHEN = {"1": "ㄅ", "q": "ㄆ", "a": "ㄇ", "z": "ㄈ", "2": "ㄉ", "w": "ㄊ", "s": "ㄋ", "x": "ㄌ", "e": "ㄍ", "d": "ㄎ", "c": "ㄏ",
          "r": "ㄐ", "f": "ㄑ", "v": "ㄒ", "5": "ㄓ", "t": "ㄔ", "g": "ㄕ", "b": "ㄖ", "y": "ㄗ", "h": "ㄘ", "n": "ㄙ", "u": "ㄧ",
          "j": "ㄨ", "m": "ㄩ", "8": "ㄚ", "i": "ㄛ", "k": "ㄜ", ",": "ㄝ", "9": "ㄞ", "o": "ㄟ", "l": "ㄠ", ".": "ㄡ", "0": "ㄢ",
          "p": "ㄣ", ";": "ㄤ", "/": "ㄥ", "-": "ㄦ", "3": "ˇ", "4": "ˋ", "6": "ˊ", "7": "˙"}
QT_KEY = {",": "Qt.Key_Comma", ".": "Qt.Key_Period", "/": "Qt.Key_Slash", ";": "Qt.Key_Semicolon", "-": "Qt.Key_Minus"}
HEADER = """// Copyright (C) 2021 The Qt Company Ltd.
// SPDX-FileCopyrightText: 2026 Daniel Campos Ramos
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only
//
// Plasma Keyboard as Fcitx 5's keyboard: the keys of the fallback layout (layouts/fallback/main.qml), labelled
// %s. The keys type Latin keysyms; Fcitx 5's engine makes them %s.
// Made by make-fcitx-layouts.py; edit the script, not this file.
"""

def qt_key(c):
    return QT_KEY.get(c, "Qt.Key_" + c.upper())

def korean():
    with open(os.path.join(LAYOUTS, "fallback", "main.qml"), encoding="utf-8") as f:
        qml = f.read()
    body = qml.split("\n", 2)[2]  # drop Qt's two header lines, the new header carries them
    def label(m):
        letter = m.group(2)
        extra = '\n%sdisplayText: "%s"' % (m.group(3), DUBEOLSIK[letter])
        if letter in DUBEOLSIK_SHIFT:
            extra += '\n%ssmallText: "%s"\n%ssmallTextVisible: true' % (m.group(3), DUBEOLSIK_SHIFT[letter], m.group(3))
        return m.group(1) + extra
    out, n = re.subn(r'(text: "([a-z])"\n(\s*)alternativeKeys: "[^"]*"\n\s*smallText: "[^"]*"\n\s*smallTextVisible: true)',
                     lambda m: m.group(0).split("\n")[0] + "\n%sdisplayText: \"%s\"" % (m.group(3), DUBEOLSIK[m.group(2)])
                     + ("\n%ssmallText: \"%s\"\n%ssmallTextVisible: true" % (m.group(3), DUBEOLSIK_SHIFT[m.group(2)], m.group(3)) if m.group(2) in DUBEOLSIK_SHIFT else ""), body)
    # the remaining letter keys: text "x" with or without alternativeKeys
    def plain(m):
        letter = m.group(2)
        if "displayText" in m.group(0):
            return m.group(0)
        return '%stext: "%s"\n%sdisplayText: "%s"' % (m.group(1), letter, m.group(1), DUBEOLSIK[letter])
    out = re.sub(r'(\n\s*)text: "([a-z])"(?!\n\s*displayText)', lambda m: '%stext: "%s"%sdisplayText: "%s"' % (m.group(1), m.group(2), m.group(1), DUBEOLSIK[m.group(2)]), out)
    # drop the Latin alternatives and digits: they would type Latin characters Fcitx 5's Hangul engine does not compose
    out = re.sub(r'\n\s*alternativeKeys: "[^"]*"', "", out)
    out = re.sub(r'(displayText: "[^"]*")\n(\s*)smallText: "[0-9]"\n\s*smallTextVisible: true', r"\1", out)
    return HEADER % ("with the jamo of Fcitx 5's Hangul engine (Dubeolsik, its default keyboard)", "Hangul") + out

def key(c, weight=None):
    w = "\n            weight: %s\n            Layout.fillWidth: false" % weight if weight else ""
    return '        Key {\n            key: %s\n            text: "%s"\n            displayText: "%s"%s\n        }\n' % (qt_key(c), c, DACHEN[c], w)

def taiwanese():
    rows = ["1234567890-", "qwertyuiop", "asdfghjkl;", "zxcvbnm,./"]
    out = HEADER % ("with the bopomofo and tones of Fcitx 5's Chewing engine (Dachen, its default keyboard)", "Zhuyin and convert it")
    out += """
import QtQuick
import QtQuick.VirtualKeyboard
import QtQuick.VirtualKeyboard.Components
import QtQuick.Layouts

KeyboardLayout {
    inputMode: InputEngine.InputMode.Latin
    keyWeight: 160
"""
    for i, r in enumerate(rows):
        out += "    KeyboardRow {\n"
        for c in r:
            out += key(c).replace("\n", "\n    ").rstrip(" ") if False else key(c)
        if i == 2:
            out += "        BackspaceKey {\n        }\n"
        out += "    }\n"
    out += """    KeyboardRow {
        SymbolModeKey {
        }
        ChangeLanguageKey {
        }
        SpaceKey {
        }
        HideKeyboardKey {
        }
        EnterKey {
        }
    }
}
"""
    return out

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

for loc, main in (("ko_KR", korean()), ("zh_TW", taiwanese())):
    write(os.path.join(OUT, loc, "main.qml"), main)
print("layouts-fcitx:", sorted(os.listdir(OUT)))
