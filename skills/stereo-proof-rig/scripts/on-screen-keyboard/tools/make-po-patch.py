#!/usr/bin/python3
# make-po-patch.py SRC OUT.patch: the edition's strings of Plasma Keyboard as Fcitx 5's keyboard (row 71) in the nine
# translated languages, appended to the catalogues of a plasma-keyboard 6.7.4 source (po/LANG/plasma-keyboard.po, the
# settings page's po/LANG/kcm_plasmakeyboard.po; Japanese gets a plasma-keyboard catalogue of its own), each checked with
# msgfmt -c, as one patch. A first draft with AI assistance, pending review by native speakers.
import os, shutil, subprocess, sys, tempfile
SRC, OUT = sys.argv[1], sys.argv[2]
LANGS = ["pl", "pt_BR", "fr", "de", "es", "ja", "ko", "zh_CN", "zh_TW"]
KEYBOARD = [
    ("@info:status", "Fcitx 5 does not answer. The keys type plain text, without conversion.", {
        "pl": "Fcitx 5 nie odpowiada. Klawisze wpisują zwykły tekst, bez konwersji.",
        "pt_BR": "O Fcitx 5 não responde. As teclas digitam texto simples, sem conversão.",
        "fr": "Fcitx 5 ne répond pas. Les touches saisissent du texte brut, sans conversion.",
        "de": "Fcitx 5 antwortet nicht. Die Tasten tippen einfachen Text, ohne Umwandlung.",
        "es": "Fcitx 5 no responde. Las teclas escriben texto sin formato, sin conversión.",
        "ja": "Fcitx 5 が応答しません。キーは変換せずにそのまま入力します。",
        "ko": "Fcitx 5가 응답하지 않습니다. 키는 변환 없이 일반 텍스트를 입력합니다.",
        "zh_CN": "Fcitx 5 没有响应。按键将输入纯文本，不进行转换。",
        "zh_TW": "Fcitx 5 沒有回應。按鍵將輸入純文字，不進行轉換。"}),
    ("@info:status", "Another program is already the on-screen keyboard of Fcitx 5.", {
        "pl": "Inny program jest już klawiaturą ekranową Fcitx 5.",
        "pt_BR": "Outro programa já é o teclado virtual do Fcitx 5.",
        "fr": "Un autre programme est déjà le clavier virtuel de Fcitx 5.",
        "de": "Ein anderes Programm ist bereits die Bildschirmtastatur von Fcitx 5.",
        "es": "Otro programa ya es el teclado en pantalla de Fcitx 5.",
        "ja": "別のプログラムがすでに Fcitx 5 のスクリーンキーボードになっています。",
        "ko": "다른 프로그램이 이미 Fcitx 5의 화상 키보드입니다.",
        "zh_CN": "已有其他程序作为 Fcitx 5 的屏幕键盘。",
        "zh_TW": "已有其他程式作為 Fcitx 5 的螢幕鍵盤。"}),
    ("@info:tooltip", "Input method: touch to choose another", {
        "pl": "Metoda wprowadzania: dotknij, aby wybrać inną",
        "pt_BR": "Método de entrada: toque para escolher outro",
        "fr": "Méthode de saisie : touchez pour en choisir une autre",
        "de": "Eingabemethode: Antippen, um eine andere zu wählen",
        "es": "Método de entrada: toque para elegir otro",
        "ja": "入力メソッド：タッチして別のものを選択",
        "ko": "입력기: 다른 입력기를 선택하려면 누르십시오",
        "zh_CN": "输入法：轻触以选择其他输入法",
        "zh_TW": "輸入法：輕觸以選擇其他輸入法"}),
    ("@action:button", "Previous candidates", {
        "pl": "Poprzednie propozycje", "pt_BR": "Candidatos anteriores", "fr": "Candidats précédents", "de": "Vorherige Kandidaten",
        "es": "Candidatos anteriores", "ja": "前の候補", "ko": "이전 후보", "zh_CN": "上一页候选", "zh_TW": "上一頁候選字"}),
    ("@action:button", "Next candidates", {
        "pl": "Następne propozycje", "pt_BR": "Próximos candidatos", "fr": "Candidats suivants", "de": "Nächste Kandidaten",
        "es": "Candidatos siguientes", "ja": "次の候補", "ko": "다음 후보", "zh_CN": "下一页候选", "zh_TW": "下一頁候選字"}),
    ("@info", "Types the keys of the on-screen keyboard while Fcitx 5 does not answer", {
        "pl": "Wpisuje klawisze klawiatury ekranowej, gdy Fcitx 5 nie odpowiada",
        "pt_BR": "Digita as teclas do teclado virtual enquanto o Fcitx 5 não responde",
        "fr": "Saisit les touches du clavier virtuel tant que Fcitx 5 ne répond pas",
        "de": "Tippt die Tasten der Bildschirmtastatur, solange Fcitx 5 nicht antwortet",
        "es": "Escribe las teclas del teclado en pantalla mientras Fcitx 5 no responde",
        "ja": "Fcitx 5 が応答しない間、スクリーンキーボードのキーを入力します",
        "ko": "Fcitx 5가 응답하지 않는 동안 화상 키보드의 키를 입력합니다",
        "zh_CN": "在 Fcitx 5 没有响应时输入屏幕键盘的按键",
        "zh_TW": "在 Fcitx 5 沒有回應時輸入螢幕鍵盤的按鍵"}),
    ("@info:shell", "Run as the on-screen keyboard of Fcitx 5, when Fcitx 5 is KWin's input method", {
        "pl": "Uruchom jako klawiaturę ekranową Fcitx 5, gdy Fcitx 5 jest metodą wprowadzania KWin",
        "pt_BR": "Executar como o teclado virtual do Fcitx 5, quando o Fcitx 5 é o método de entrada do KWin",
        "fr": "Lancer comme clavier virtuel de Fcitx 5, lorsque Fcitx 5 est la méthode de saisie de KWin",
        "de": "Als Bildschirmtastatur von Fcitx 5 starten, wenn Fcitx 5 die Eingabemethode von KWin ist",
        "es": "Ejecutar como el teclado en pantalla de Fcitx 5, cuando Fcitx 5 es el método de entrada de KWin",
        "ja": "Fcitx 5 が KWin の入力メソッドのとき、Fcitx 5 のスクリーンキーボードとして実行します",
        "ko": "Fcitx 5가 KWin의 입력기일 때 Fcitx 5의 화상 키보드로 실행합니다",
        "zh_CN": "当 Fcitx 5 是 KWin 的输入法时，作为 Fcitx 5 的屏幕键盘运行",
        "zh_TW": "當 Fcitx 5 是 KWin 的輸入法時，作為 Fcitx 5 的螢幕鍵盤執行"}),
]
KCM = [
    (None, "Fcitx 5:", {l: "Fcitx 5:" for l in LANGS} | {"fr": "Fcitx 5 :"}),
    (None, "Show this keyboard when Fcitx 5 is the input method", {
        "pl": "Pokazuj tę klawiaturę, gdy Fcitx 5 jest metodą wprowadzania",
        "pt_BR": "Mostrar este teclado quando o Fcitx 5 for o método de entrada",
        "fr": "Afficher ce clavier lorsque Fcitx 5 est la méthode de saisie",
        "de": "Diese Tastatur anzeigen, wenn Fcitx 5 die Eingabemethode ist",
        "es": "Mostrar este teclado cuando Fcitx 5 sea el método de entrada",
        "ja": "Fcitx 5 が入力メソッドのときにこのキーボードを表示",
        "ko": "Fcitx 5가 입력기일 때 이 키보드 표시",
        "zh_CN": "当 Fcitx 5 是输入法时显示此键盘",
        "zh_TW": "當 Fcitx 5 是輸入法時顯示此鍵盤"}),
    (None, "Fcitx 5 converts the keys and shows its candidates above them. Takes effect at the next login.", {
        "pl": "Fcitx 5 konwertuje klawisze i pokazuje propozycje nad nimi. Zmiana działa od następnego logowania.",
        "pt_BR": "O Fcitx 5 converte as teclas e mostra seus candidatos acima delas. Vale a partir do próximo login.",
        "fr": "Fcitx 5 convertit les touches et affiche ses candidats au-dessus d'elles. Prend effet à la prochaine connexion.",
        "de": "Fcitx 5 wandelt die Tasten um und zeigt seine Kandidaten darüber an. Wirkt ab der nächsten Anmeldung.",
        "es": "Fcitx 5 convierte las teclas y muestra sus candidatos encima de ellas. Tendrá efecto en el próximo inicio de sesión.",
        "ja": "Fcitx 5 がキーを変換し、その上に候補を表示します。次回のログインから有効になります。",
        "ko": "Fcitx 5가 키를 변환하고 그 위에 후보를 표시합니다. 다음 로그인부터 적용됩니다.",
        "zh_CN": "Fcitx 5 会转换按键，并在按键上方显示候选字词。下次登录时生效。",
        "zh_TW": "Fcitx 5 會轉換按鍵，並在按鍵上方顯示候選字詞。下次登入時生效。"}),
]
HEADER = '''# Plasma Keyboard's strings in Japanese, begun by Sparky Stereo OS for Plasma Keyboard as Fcitx 5's keyboard (row 71).
# This file is distributed under the same license as the plasma-keyboard package.
msgid ""
msgstr ""
"Project-Id-Version: plasma-keyboard\\n"
"Report-Msgid-Bugs-To: https://bugs.kde.org\\n"
"PO-Revision-Date: 2026-11-25 00:00+0000\\n"
"Last-Translator: Sparky Stereo OS\\n"
"Language-Team: Japanese\\n"
"Language: ja\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=1; plural=0;\\n"
'''
def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
def entries(rows, lang):
    out = "\n# Sparky Stereo OS: Plasma Keyboard as Fcitx 5's keyboard (row 71); a first draft with AI assistance\n"
    for ctx, msgid, tr in rows:
        out += "#, kde-format\n" + ("msgctxt %s\n" % q(ctx) if ctx else "") + "msgid %s\nmsgstr %s\n\n" % (q(msgid), q(tr[lang]))
    return out.rstrip("\n") + "\n"
work = tempfile.mkdtemp()
a, b = os.path.join(work, "a"), os.path.join(work, "b")
shutil.copytree(os.path.join(SRC, "po"), os.path.join(a, "po"))
shutil.copytree(os.path.join(SRC, "po"), os.path.join(b, "po"))
for lang in LANGS:
    for domain, rows in (("plasma-keyboard", KEYBOARD), ("kcm_plasmakeyboard", KCM)):
        path = os.path.join(b, "po", lang, domain + ".po")
        if os.path.exists(path):
            text = open(path, encoding="utf-8").read().rstrip("\n") + "\n" + entries(rows, lang)
        else:
            text = HEADER + entries(rows, lang)
        open(path, "w", encoding="utf-8").write(text)
        subprocess.run(["msgfmt", "-c", "-o", "/dev/null", path], check=True)
# a git-style diff, as the edition's other translation patches and sparky-os/tests/validate-po-patches.py read them
diff = subprocess.run(["git", "diff", "--no-index", "--no-prefix", "--src-prefix=a/", "--dst-prefix=b/", "a", "b"], cwd=work,
                      capture_output=True, text=True).stdout.replace("a/a/", "a/").replace("b/b/", "b/").replace("diff --git a/b/", "diff --git a/")
open(OUT, "w", encoding="utf-8").write(diff)
shutil.rmtree(work)
print("patch:", OUT, diff.count("\n+msgid"), "msgids added")
