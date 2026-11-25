# The on-screen keyboard: Plasma Keyboard, KWin's input method and Fcitx 5

**For** whoever changes how text is typed by touch on the edition: how KWin, the input method and the keyboard fit together, Plasma Keyboard as the keyboard of Fcitx 5 (the bridge) and how to see it working, typing each required language in the session rig, and the traps met (row 71, November 2026).

Daniel, 2026-10-14: "we should also revamp the best (integrated with kde) virtual keyboard - as a measure for VR", "multilanguage is required".
The accessibility study's answer, accepted: Plasma Keyboard is the keyboard, Fcitx 5 does the conversion for Japanese, Korean and Chinese.

## How the pieces fit

- **KWin runs one input method.** `kwinrc [Wayland] InputMethod` names a desktop entry; KWin starts its program with a private Wayland connection (`WAYLAND_SOCKET`) and talks `zwp_input_method_v1` with it (`src/inputmethod.cpp`, `startInputMethod()`). Text fields reach it through text-input v1, v2 or v3.
- **Plasma Keyboard as the input method** (Latin sessions on a computer with a touch screen of its own, row 567): Qt Virtual Keyboard runs inside it, its commits and preedit go to the field through `zwp_input_method_context_v1`, and its window is a `zwp_input_panel_surface_v1` that KWin shows as an `InputPanelV1Window` (`inputMethod` true in KWin's window list). KWin shows it when the last input came from a touch screen or a pen and, with the edition's KWin, only in tablet mode (`InputMethod::shouldShowOnActive()`, `[Wayland] InputMethodTabletOnly`).
- **Fcitx 5 as the input method** (Japanese, Korean and Chinese sessions: `sparky-stereo-look`'s `first-login-input-method` writes `org.fcitx.Fcitx5.desktop` into the person's `kwinrc` at the first login): Fcitx 5 converts the keys of a hardware keyboard, and until row 71 no on-screen keyboard showed at all.
- **Fcitx 5's keyboard bridge** (`fcitx5 src/ui/virtualkeyboard`, the addon "DBus Virtual Keyboard" in Debian's `fcitx5-modules`): Fcitx 5 draws no keyboard. In its on-screen keyboard mode it owns `org.fcitx.Fcitx5.VirtualKeyboardBackend` (`/virtualkeyboard`, interface `org.fcitx.Fcitx5.VirtualKeyboardBackend1`: `ProcessKeyEvent(uuubu)`, `SelectCandidate(i)`, `PrevPage`, `NextPage`, `SetVirtualKeyboardFunctionMode(u)`) and calls the keyboard that owns `org.fcitx.Fcitx5.VirtualKeyboard` (`/org/fcitx/virtualkeyboard/impanel`, interface `org.fcitx.Fcitx5.VirtualKeyboard1`): `ShowVirtualKeyboard`, `HideVirtualKeyboard`, `UpdatePreeditArea(s)`, `UpdatePreeditCaret(i)`, `UpdateCandidateArea(asbbii)`, `NotifyIMActivated(s)`, `NotifyIMDeactivated(s)`, `NotifyIMListChanged`. Its keyboard mode starts with `ShowVirtualKeyboard` on `org.fcitx.Fcitx5` `/virtualkeyboard` (`org.fcitx.Fcitx.VirtualKeyboard1`) and ends at the first physical key, which hands back to its own candidate window.

## Plasma Keyboard as Fcitx 5's keyboard (the edition's plasma-keyboard 6.7.4-2+stereo3d1)

`plasma-keyboard --fcitx` is that keyboard. It is a second process beside KWin's input method, so it is not an input method itself:

| Part | What it does | Why this way |
| --- | --- | --- |
| Start | an autostart entry, `/etc/xdg/autostart/org.kde.plasma.keyboard.fcitx.desktop`; the program ends at once, with one line, unless KWin's `InputMethod` names Fcitx 5 and `plasmakeyboardrc [General] showWithFcitx` is true | KWin starts only one program; the setting is off in the package and on where the hardware layer finds a touch screen of the computer's own (its folder in front of `XDG_CONFIG_DIRS`), so existing accounts get it with no file of theirs touched |
| When it shows | KWin's `org.kde.kwin.VirtualKeyboard` on `/VirtualKeyboard`: on `activeChanged` it reads `active` and calls `willShowOnActive()`; when KWin would show a keyboard it asks Fcitx 5 to show, and shows when Fcitx 5 calls it | the touch, pen and tablet-mode rule stays KWin's, no KWin change |
| Its window | a layer-shell surface (LayerShellQt) at the bottom, `KeyboardInteractivityNone`, made Qt's focus window on the client side | KWin never gives it the keyboard focus, so the text field keeps it and Fcitx 5 keeps its input context |
| Its keys | Qt Virtual Keyboard types into a focus item of its own; each commit and key becomes an X keysym with Fcitx 5's key states, sent by `ProcessKeyEvent` | Fcitx 5's engine converts them as it converts a physical keyboard's; with `keyboard-us` Fcitx 5 forwards them unchanged |
| The bar | the preedit Fcitx 5 hands over, the candidates (a touch calls `SelectCandidate`), the pages, the input method (a touch, or the layout's language key, lists the group's input methods from `org.fcitx.Fcitx.Controller1` and switches with `SetCurrentIM`) | |
| Layouts | `layouts-fcitx`: Korean keys labelled with Dubeolsik jamo, Chinese (Taiwan) keys with Dachen bopomofo and tones; Japanese and Chinese (China) the QWERTY of the fallback layout; every other locale Plasma Keyboard's own | the engines read QWERTY positions (romaji, pinyin, Dubeolsik, Dachen) |
| When Fcitx 5 does not answer | the bar says so ("Fcitx 5 does not answer. The keys type plain text, without conversion.") and the keys go through KWin's fake input (`keyboard_keysym`, version 6) | no silent fallback; KWin grants the protocol to the entry `org.kde.plasma.keyboard.fcitx.desktop`, whose `Exec` is the absolute path |

How to see it working, in a session: `busctl --user tree org.fcitx.Fcitx5.VirtualKeyboard` shows the keyboard's object; after a touch on a field, `busctl --user status org.fcitx.Fcitx5.VirtualKeyboardBackend` answers (Fcitx 5 is in its keyboard mode); the keyboard's debug lines are `QT_LOGGING_RULES=org.kde.plasma.keyboard.debug=true` ("KWin: text field active, show the keyboard: true", "Fcitx 5 keyboard backend registered", "Fcitx 5 keyboard visible: true"); KWin's window list shows a window of class `plasma-keyboard` with `inputMethod` false.

## Known gaps (row 71)

- **A touch on a field that already has the keyboard focus** (from the pointer, with the edition's focus following the mouse) shows KWin's own keyboard but not the keyboard for Fcitx 5. The field asks for the panel (text-input `show_input_panel`), KWin calls `InputMethod::show()` (`src/inputmethod.cpp`), which acts on KWin's own panel or input method only and emits nothing; `activeChanged` comes only when a field becomes active or inactive. The smallest change is KWin's: `InputMethod::show()` emits a signal that `VirtualKeyboardDBus` relays on D-Bus beside `activeChanged`, and the bridge treats it as it treats `activeChanged`. Until then: touch elsewhere, then the field.
- **Windows are not moved clear of the keys.** KWin's own input panel tells the focused text field the rectangle it covers (text-input's `input_panel_state`); a layer surface does not, and an exclusive zone would resize maximized windows (and stereo windows with them), so the keyboard covers the bottom of the screen and a field there stays behind it (no design yet for this).
- **Plasma Keyboard's long-press accents** (its diacritics overlay) belong to its input-method mode and are not offered in Fcitx 5 mode, where Fcitx 5's engine decides what a key gives.

## The defaults, and where each one lives

| Default | Where | Why there |
| --- | --- | --- |
| The keyboard for Fcitx 5 starts at login | `plasma-keyboard`: `/etc/xdg/autostart/org.kde.plasma.keyboard.fcitx.desktop` (`X-KDE-autostart-phase=1`, `NoDisplay`, `OnlyShowIn=KDE`) | the package owns the program; the program itself decides whether it is needed and ends at once otherwise, with one line in the journal |
| `showWithFcitx` is off | `plasma-keyboard`: `plasmakeyboardrc [General] showWithFcitx`, default false in the kcfg | a computer without a touch screen of its own gets nothing new |
| `showWithFcitx` is on for a computer with a touch screen of its own | `sparky-stereo-hardware` 0.1.42: `share/tablet-mode/xdg/plasmakeyboardrc`, in the folder its session script puts in front of `XDG_CONFIG_DIRS` when `has-tablet-mode` says yes (row 567) | the same detection that makes Plasma Keyboard KWin's keyboard on such a computer; the person's own file wins, and the settings page's switch ("Show this keyboard when Fcitx 5 is the input method") writes it |
| Shown only in tablet mode | KWin's own rule (`[Wayland] InputMethodTabletOnly`, row 567), read through `willShowOnActive()` | the keyboard asks KWin instead of deciding itself, so Latin and CJK sessions behave the same |
| Fcitx 5 stays KWin's input method | `sparky-stereo-look`'s `first-login-input-method`, unchanged | a hardware keyboard types through Fcitx 5 as before; Fcitx 5's first physical key ends its keyboard mode and hides the on-screen keyboard |

## Proving it: the session rig

The rig is [the welcome-login rig](first-run-welcome.md#the-session-proof) adapted: one fresh container and one new account's login per case, KWin on a virtual 1920x1080 output on the NVIDIA card (CDI), a sysfs fixture that the hardware layer reads as a computer with a touch screen of its own (`SPARKY_STEREO_SYSFS`), `KWIN_VIRTUAL_TOUCH_SCREEN=1` so that KWin has a touch device, tablet mode set as General Behavior writes it, and touches sent through KWin's fake input (`t:X,Y`, the rig's `fakeinput`, granted by its desktop entry's `X-KDE-Wayland-Interfaces`). Scripts: [`stereo-proof-rig/scripts/on-screen-keyboard/`](../../stereo-proof-rig/scripts/on-screen-keyboard/).

1. Images: `mkrig.sh` builds the published set (Debian testing pinned by digest, the edition's signed tree, deb-multimedia, SparkyLinux's repository, Kate, Plasma Keyboard, Fcitx 5 with the four engines, every locale); `mklayer.sh` adds one layer installed by apt (Gwenview for the 3D case, then the staged packages for green), keeping apt's plan.
2. A typing case (`type-case.py`): Kate opens an empty file and saves it every 2 seconds; a touch elsewhere, then a touch on the text; KWin's window list says which keyboard showed (`inputMethod` true: KWin's input panel; class `plasma-keyboard`: the keyboard for Fcitx 5); the keys are found in a capture from the layout's own `main.qml` (`keys.py`: background from the top rows, key runs on each row's middle line, the bar above the first row); in a CJK session the input method is chosen first on the keyboard's bar; then the word's keys and its engine's finish are touched and the saved file is read back.
3. The other cases are step scripts run in the same login (`STEP=`): `hw-type.sh` (a hardware keyboard through Fcitx 5, then a touch and a physical key), `retouch.sh` (a field focused by the pointer, then touched), `kcm-page.sh` (the settings page), `step6-3d.sh` (the keyboard over a stereo picture on a 3D output, both eyes captured, measured by `measure-3d.py`).
4. `prove.sh OUT` runs every case red (the published set) and green (the staged packages) and writes one row per claim; it exits 1 when a row is not as expected.

### Measured (row 71, 2026-11-25)

A touch on Kate's text in tablet mode, on a computer with a touch screen of its own; the sentence typed on the on-screen keys and read back from the saved file. Red: the published set (Plasma Keyboard 6.7.4-2+b1 from Debian, sparky-stereo-hardware 0.1.32); green: plasma-keyboard 6.7.4-2+stereo3d1 and sparky-stereo-hardware 0.1.42.

| Language | Red | Green | How it is typed |
| --- | --- | --- | --- |
| en, pt_BR, es, fr, de, pl | KWin's input panel, the sentence typed | the same | Plasma Keyboard as KWin's input method, the session's layout |
| ja | no keyboard | 日本語 | `nihongo`, Space twice (Mozc's 8 candidates on the bar), the first touched, Enter |
| ko | no keyboard | 한국어 | Dubeolsik keys `gksrnrdj`, Enter |
| zh_CN | no keyboard | 中文 | `zhongwen` (27 candidates on the bar), the first touched |
| zh_TW | no keyboard | 中文 | Dachen keys `5j/ jp6` (zhong1 wen2), Enter |

In each converted language the input method is chosen on the keyboard's own bar (Fcitx 5's group is `keyboard-us` first), and the commit is checked by the preedit's highlight as well as the file.

The other rows of the same run (29 rows, red and green, all as expected):

| Claim | Red | Green |
| --- | --- | --- |
| Fcitx 5 without its keyboard addon (`[Behavior/DisabledAddons] 0=virtualkeyboard`) | no keyboard | the bar says so in the session's language, `abc` typed through KWin's fake input |
| Fcitx 5 chosen but its program ends at once | no keyboard | the same ("Name org.fcitx.Fcitx5 does not exist" in the log) |
| A hardware keyboard in a Japanese session (Ctrl+Space, `nihongo`, Space, Enter) | 日本語 | 日本語; a touch shows the keyboard, the first physical key hides it (Fcitx 5's own popup takes over) |
| Outside tablet mode, ja and en | no keyboard | no keyboard |
| A computer without a touch screen of its own | no keyboard | no keyboard; `plasma-keyboard --fcitx` ends at once |
| The person's switch off | | no keyboard |
| On a 3D output, over a stereo picture in Gwenview | KWin's panel: shift 0, 0 differing pixels; the picture behind unchanged in each eye | the keyboard for Fcitx 5: the same |
| A touch on a field focused by the pointer | KWin's own keyboard shows (en) | the keyboard for Fcitx 5 does not (ja): the gap above |

## Traps met (row 71)

- **Symptom:** in a Latin session (Plasma Keyboard as KWin's input method) the keyboard vanished after a test merely asked Fcitx 5 something over D-Bus. **Cause:** the call started Fcitx 5 by D-Bus activation; a Fcitx 5 started that way binds KWin's input-method protocols too (KWin's Wayland filter does not keep them to the program it started) and its popup surface takes KWin's only input panel (`InputPanelV1Window`, one at a time), so Plasma Keyboard's keys were no longer drawn. **Fix:** every call to Fcitx 5, in the keyboard and in a rig, goes without auto-start (`QDBusMessage::setAutoStartService(false)`, `busctl --auto-start=no`, `NO_AUTO_START` in GDBus): an absent Fcitx 5 then answers "no such service". **Found by:** KWin's log at the moment Fcitx 5 drew its popup (`kwin_virtualkeyboard: Replacing input panel KWin::InputPanelV1Window(... surface=A ...) with KWin::InputPanelV1Window(... surface=B ...)`), after which the rig found no rows of keys and nothing was typed. In KWin's window list Plasma Keyboard's panel has the class `kwin_wayland`, because KWin starts it on a private socket.
- **Symptom:** the saved document already holds the Japanese, Korean or Chinese text while the conversion is still open, so a check that reads the file passes too early. **Cause:** KTextEditor (Kate) keeps a pending conversion (the preedit) in its buffer and saves it. **Fix:** besides the file, measure how many more pixels of the preedit's highlight (247,159,82) Kate's window has than right after the touch: a pending conversion adds 410 to 723, committed text 2. **Found by:** a run that "typed" 日本語 with Mozc's candidate list still open.
- **Symptom:** a converted word never commits. **Cause:** each engine commits differently: Mozc converts at the first Space, lists candidates at the second, and commits with Enter; Pinyin commits when a candidate is chosen; Chewing and Hangul commit with Enter. Kate also drops trailing spaces when it saves. **Fix:** finish each language's word its engine's way; end a Korean word with Enter, not a space.
- **Symptom:** the bar's input method button is empty. **Cause:** Fcitx 5 reports the current input method to its keyboard only while it is in keyboard mode, and not again after `SetCurrentIM`. **Fix:** read `CurrentInputMethod` from `org.fcitx.Fcitx.Controller1` when the keyboard is shown and after every switch.
- **Symptom:** `dpkg-source` refuses the code patch, or the installed `layouts-fcitx` lacks the Japanese layout. **Cause:** a 3.0 (quilt) patch cannot carry a symbolic link or an empty file (Qt Virtual Keyboard's `*.fallback` markers are empty). **Fix:** the source holds only the two `main.qml`; CMake writes the markers (`file(TOUCH)`) and the links (`file(CREATE_LINK ... SYMBOLIC)`) in `install(CODE)`.
- **Symptom:** on a 3D output the keyboard sat 2 px behind the screen, and a maximized stereo window shrank when it opened. **Cause:** LayerShellQt's default scope makes a layer KWin treats as an ordinary window (sunk by the depth rules), and an exclusive zone resizes maximized windows. **Fix:** scope `dock` (KWin's `Dock` type stays at the screen's plane) and exclusive zone 0, as KWin's own input panel neither moves nor resizes windows. **Found by:** `measure-3d`: disparity 2 and 154 185 changed pixels behind the keyboard, then 0 and 0.
- **Symptom:** in the rig, Kate disappears behind another window before the touch. **Cause:** the edition's focus follows the mouse with automatic raise, and the fake pointer rests over the other window. **Fix:** keep Kate above, move the pointer away from it, then touch.
- **Symptom:** the package's link gate cannot install it: `libavcodec63 ... Depends libaom3 (>= 1:3.15.3) but none of the choices are installable`. **Cause:** `qml6-module-qtquick-virtualkeyboard` pulls Qt Multimedia, which the edition builds against deb-multimedia's FFmpeg; a gate archive list without deb-multimedia cannot resolve it. **Fix:** the gate's `sources.json` names deb-multimedia beside Debian and the edition's tree.
- **Symptom:** `validate-po-patches.py` says "no file section" for a translation patch. **Cause:** it reads git-style diffs only (`diff --git`, `index`). **Fix:** make the patch with `git diff --no-index`, and give a new catalogue's header `a/` and `b/` paths of the same file.
