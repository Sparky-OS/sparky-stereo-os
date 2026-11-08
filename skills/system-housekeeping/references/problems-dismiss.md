# Kept problems: Dismiss, Bring back and the Problems page

The edition's one failure engine, `sparky-stereo-problems`, keeps every problem the computer has until it is repaired, and tells the person.
Since engine 0.2.0 and `sparky-stereo-problems-plasma` 0.2.0 the person can also stop seeing one, and finds all of them, current and dismissed, on the Problems page of System Settings (System Administration).
Work on a package that raises a problem needs none of this: it hands its failure to the engine, and Dismiss and the page come with it.

## Recipe

1. **The engine's verbs are `hide` and `show`; the person's words are Dismiss and Bring back.** One dismissal exists, the engine's. The notifier's Dismiss, the summary's Dismiss all and the page's Dismiss all call `ssp_hide`; Bring back calls `ssp_show`. Never write a second store, a second command or a dismissal of a package's own.
2. **The mark is the person's.** `$XDG_STATE_HOME/sparky-stereo-problems/.hidden/SCOPE_PACKAGE_KEY` holds a copy of the record (its id and generation are what the mark holds to), its fingerprint (the message and its arguments) and when it was dismissed. Another person, and root, still see the problem.
3. **What a dismissal ends on:** the problem's message or arguments change (a different message is a different problem), or a repair fails (the record becomes a new generation). A machine problem or a person's own problem that is kept again with the same message keeps its dismissal.
4. **A failed service is a problem of this boot, new at every boot.** `/run` is empty after a reboot, so the record gets a new id. For this boot scope only, a mark whose fingerprint equals the new record's, with no repair failed since, moves its dismissal to the new record: the same unit failing the same way (the same exit status, signal or result) stays dismissed; another exit status shows again. The mark of a boot problem is kept when the problem is not happening, so the first failure after a reboot is already dismissed when the person's session reads it. Marks of machine and person problems that are over go with them, as before.
5. **List them for the page:** `sparky-stereo-problems list --json --over` (C: `ssp_list_over_json`) adds the dismissed problems of this boot's kind that are not happening now, with `"over": true` and `"hidden": true`, their text rendered from the copy in the mark. Without `--over` nothing changes for any caller (the Python module, the Graphics page, the Memory page and the notifier read `ssp_list_json`).
6. **Bring back is `show`:** for a problem that is not happening now it removes the mark and the entry disappears; for one that is happening it lists it as current and the notifier tells it again.
7. **The notifier and the page agree through the stores.** Both watch the three stores and the person's `.hidden` folder (`QFileSystemWatcher` on directories, re-added when they appear) and systemd's `ActiveState` changes; a dismissal made on the page closes the notification at once, and a problem brought back there is told again (the notifier remembers which problems it saw dismissed and notifies one again when it is no longer dismissed).
8. **Dismissing is told, never silent:** a short notice says where the problem stays listed (Problems in System Settings) and has Open Problems. An unreadable record cannot be dismissed (the engine cannot name it) and is shown with its file and reason.

## The page (a KCM in the Plasma package)

- `kcm_sparkystereo_problems` is a `kcmutils_add_qml_kcm` plugin in `sparky-stereo-problems-plasma`, linked to the engine's private library with the same `INSTALL_RPATH` as the notifier. A KCM's QML takes its strings from the domain named like the plugin, so the page has its own `po` folder (`kcm_sparkystereo_problems`) beside the notifier's.
- Each card: icon by severity, title, text, severity and "Since", the last failed repair, Repair where there is one, the record's own actions, Dismiss or Bring back. The empty state is one placeholder in plain words.

## Traps

- Symptom: the page shows "Dismiss" and the plugin's name in Portuguese but every other string in English. Cause: a QML KCM looks its strings up in the domain named like the plugin, and `TRANSLATION_DOMAIN` of the package was the notifier's. Fix: `remove_definitions` and `add_definitions` of the plugin's domain in its own folder, its own `ki18n_install(po)`. Found by: capturing with the real `LANG` and `LANGUAGE`, since the engine's text and the plugin's metadata were already translated.
- Symptom: the page and the buttons render with empty icon squares. Cause: the capture image lacks Qt's SVG icon-engine plugin (`qt6-svg-plugins`) and a platform theme. Fix: install both, run with `QT_QPA_PLATFORMTHEME=kde` and a `kdeglobals` that names Breeze.
- Symptom: `no match for operator=` between `QVariant` and `QStringBuilder` in a KCM. Cause: KDE's compiler settings turn on string builders. Fix: wrap the concatenation in `QString(...)`.
- Symptom: a dismissed failed service appears again after a reboot. Cause: the dismissal was keyed to the record's id, which is new at every boot. Fix: the fingerprint carry for the boot scope (item 4); the test is a real unit under systemd that fails with the same status twice and once with another.
- Symptom: a test checks a QML page and finds no button although it is drawn. Cause: `findChildren<QQuickItem*>()` follows QObject parents, not visual children. Fix: walk `childItems()`.
- Symptom: a page test passes with the page's strings in English although the language is Portuguese. Cause: `LANG=C.UTF-8`, where gettext translates nothing. Fix: run with a generated real locale (`LANG=pt_BR.UTF-8`) and require the text to differ from the English.
- Symptom: a boot problem is dismissed, then removed by a test with `rm`, and a waiting check passes at once. Cause: the page has not refreshed yet, so the old entry still satisfies the check. Fix: wait for the state that only the new entry has (`over` true), not for the count.

## Proving it

- Engine: `tests/run-tests.sh` (dismiss across the three scopes, a simulated reboot by emptying `/run/sparky-stereo-problems`, bring back, the package filter, another person) and `tests/systemd-tests.sh` (a real failing service under systemd as PID 1: the same exit status twice stays dismissed, another one shows). Red with the previous engine; a mutant that drops the fingerprint carry fails exactly the carry checks.
- Page: the plugin's autotest loads the plugin as System Settings does, against the real library, with the stores under a fixture, and checks lists, dismiss, bring back, live changes, the reboot case, an unreadable record, repairs and the page's buttons in English and Portuguese; captures at 1920x1080 in Xvfb with `kcmshell6`, one fresh session per language.
- Notifier: the session suite under a real user manager with a stand-in notification server clicks Dismiss, Dismiss all, and dismisses and brings back through the engine as the page does.
