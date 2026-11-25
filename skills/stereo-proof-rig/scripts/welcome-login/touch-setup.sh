#!/bin/bash
# touch-setup.sh: USER_SETUP of the touch rows (welcome-login.sh runs it as the person before the first login): the folder
# the rows open, ~/Desktop/TouchTest/Inner, and the click setting of the case as General Behavior writes it
# (CLICK=single: kdeglobals [KDE] SingleClick=true; double: false; unset: nothing written, KDE's own default).
set -eu
mkdir -p "$HOME/Desktop/TouchTest/Inner"
case "${CLICK:-}" in
single) kwriteconfig6 --file kdeglobals --group KDE --key SingleClick true ;;
double) kwriteconfig6 --file kdeglobals --group KDE --key SingleClick false ;;
esac
grep -A3 '^\[KDE\]' "$HOME/.config/kdeglobals" 2>/dev/null || echo "kdeglobals: no [KDE] SingleClick written"
