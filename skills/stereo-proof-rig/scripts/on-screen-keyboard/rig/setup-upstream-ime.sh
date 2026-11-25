#!/bin/bash
# USER_SETUP for the upstream smoke (row 71, Daniel's lead of 2026-11-25): the person chose Plasma Keyboard as the virtual
# keyboard (System Settings' Virtual Keyboard page writes kwinrc [Wayland] InputMethod) and, with UPSTREAM_LOCALE, enabled
# their language on Plasma Keyboard's page (plasmakeyboardrc [General] enabledLocales)
set -eu
kwriteconfig6 --file kwinrc --group Wayland --key InputMethod /usr/share/applications/org.kde.plasma.keyboard.desktop
[ -n "${UPSTREAM_LOCALE:-}" ] && kwriteconfig6 --file plasmakeyboardrc --group General --key enabledLocales "$UPSTREAM_LOCALE"
# with UPSTREAM_LAYOUT: the layout as the page's "enabled layouts" list saves it (master's enabledLocales path fails:
# KeyboardPanel.qml calls layoutIdsForLocales, which no C++ class defines)
[ -n "${UPSTREAM_LAYOUT:-}" ] && kwriteconfig6 --file plasmakeyboardrc --group General --key enabledKeyboardLayoutIds "$UPSTREAM_LAYOUT"
cat "$HOME/.config/kwinrc" "$HOME/.config/plasmakeyboardrc" 2>/dev/null
