# Trash and My Documents on the desktop, once

Use KDE's own Trash entry and the classic Windows My Documents term for the shortcut that opens the home folder.
The label does not change its target: the current person's home, not the Documents subfolder.
The icon is user-home.
The look package's pre-Plasma hook invokes `/usr/lib/sparky-stereo-look/first-login-desktop-shortcuts`.
It runs xdg-user-dirs-update and asks xdg-user-dir for the configured desktop, including localized directory names.

## Recipe

1. Reproduce an account whose Desktop exists before KIO starts.
   KDE's `/usr/share/kio_desktop/directory.trash`, owned by plasma-workspace, is otherwise copied only when KIO creates that directory itself.
2. Inspect existing link targets before seeding anything.
   Preserve personal labels, icons and filenames; recognize links to trash:/ and the person's file: home URL.
3. Copy KDE's Trash template if absent.
   For the home shortcut use Type=Link, Icon=user-home and the current account's escaped file URL.
   Read Name and the nine translated Name keys from the look's own `/usr/share/sparky-stereo-look/desktop-shortcuts.json`.
   Its ten classic Microsoft terms are sourced individually, with date read, in the look recipe's TERMINOLOGY.md.
   Keep the Windows 2000/XP forms where newer Windows uses a different name; German is Eigene Dateien.
   Never derive this label from KDE's catalogue or from recall.
4. Create files exclusively, using a numbered filename on collision.
   Never overwrite an unrelated personal entry named home.desktop or trash.desktop.
5. Record `$XDG_STATE_HOME/sparky-stereo-look/desktop-shortcuts-v1` only after successful seeding; the default state root is ~/.local/state.
   An existing account without links gets them at its next login.
   Later logins and upgrades keep the marker, so deleting either link stays a choice.
   If Desktop is disabled by pointing it at home, record the pass without filling home with desktop links.
6. Prove a pt_BR, English and one more fresh login, inspecting the displayed labels and targets.
   Repeat existing-account, custom-link, filename-collision and removal controls.
   The older test-only Home/Início label was never published; no migration or relabeling of personal entries is authorized.

## Traps

- **Symptom:** a fresh installed account has no Trash icon although KDE supplies its template.
  **Cause:** xdg-user-dirs created Desktop first, bypassing KIO's create-directory branch.
  **Fix:** seed the native template once before Plasma reads the desktop.
  **Found by:** the fresh predecessor login and KIO's directory-exists condition.
- **Symptom:** the Portuguese home link says Início, which a person associates with the Start menu.
  **Cause:** the previous test build used KDE Places' Home name instead of the familiar documents-place term requested by Daniel.
  **Fix:** ship the ten classic Microsoft terms in the look's own catalogue; pt_BR is Meus Documentos and English is My Documents.
  **Found by:** Daniel's 18 November 2026 review and Microsoft's published terminology, recorded in TERMINOLOGY.md.
- **Symptom:** a German source appears to offer several different translations of My Documents.
  **Cause:** modern translated API prose mixes names from different Windows generations.
  **Fix:** take the classic Windows XP term from Microsoft's XP support documentation and record the version choice.
  **Found by:** comparing the modern Learn page with Microsoft's MS06-015 Windows XP article.
- **Symptom:** a removed shortcut reappears after an upgrade.
  **Cause:** seeding every time a link is missing without remembering the first pass.
  **Fix:** keep account state outside package-owned configuration and test removal followed by another invocation/login.
  **Found by:** requirement analysis and explicit removal negative controls.
