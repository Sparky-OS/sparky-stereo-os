# Trash and Home on the desktop, once

Use KDE's own Trash entry and KDE's own name for the home place.
The look package's pre-Plasma environment hook invokes `/usr/lib/sparky-stereo-look/first-login-desktop-shortcuts`.
It runs xdg-user-dirs-update and asks xdg-user-dir for the configured desktop, including localized directory names.

## Recipe

1. Reproduce an account whose Desktop already exists before KIO starts.
   KDE's `/usr/share/kio_desktop/directory.trash`, owned by plasma-workspace, is otherwise copied only when KIO creates that directory itself.
2. Inspect existing link targets before seeding anything.
   Preserve personal labels, icons and filenames; recognize links to trash:/ and the person's file: home URL.
3. Copy KDE's Trash template if absent.
   For Home use Type=Link, Icon=user-home and the current account's escaped file URL.
   Obtain Name and the nine translated Name keys from the installed kio6 gettext catalogue, context `KFile System Bookmarks`, message `Home`.
   Check all ten against native KFilePlacesModel, the same name shown by Dolphin's Places.
4. Create files exclusively, using a numbered filename on collision.
   Never overwrite an unrelated personal entry named home.desktop or trash.desktop.
5. Record `$XDG_STATE_HOME/sparky-stereo-look/desktop-shortcuts-v1` only after successful seeding; the default state root is ~/.local/state.
   An existing account without links gets them at its next login.
   Later logins and upgrades keep the marker, so deleting either link stays a choice.
   If Desktop is disabled by pointing it at home, record the pass without filling the home directory with desktop links.
6. Prove fresh and existing accounts, custom links, filename collisions and removals.
   Capture the actual desktop and compare the links' targets and labels.

## Traps

- **Symptom:** a fresh installed account has no Trash icon, although KDE supplies its template.
  **Cause:** xdg-user-dirs created Desktop first, bypassing KIO's create-directory branch.
  **Fix:** seed the native template once before Plasma reads the desktop.
  **Found by:** the fresh predecessor login and KIO source's directory-exists condition.
- **Symptom:** the home shortcut differs from Dolphin in Portuguese or French.
  **Cause:** translating the generic word Home by hand instead of using the Places catalogue context.
  **Fix:** use kio6's catalogue and compare against KFilePlacesModel in every edition language.
  **Found by:** native Places returned Início and Dossier Personnel; the complete ten-entry table is produced by home-labels.cpp.
- **Symptom:** a removed shortcut reappears after an upgrade.
  **Cause:** seeding every time a link is missing, without remembering the first pass.
  **Fix:** keep account state outside package-owned configuration and test removal followed by another invocation/login.
  **Found by:** requirement analysis and the explicit removal negative controls.
