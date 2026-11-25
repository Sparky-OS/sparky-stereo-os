#!/bin/bash
# USER_SETUP: the person turned "Show this keyboard when Fcitx 5 is the input method" off, as the settings page writes it
set -eu
kwriteconfig6 --file plasmakeyboardrc --group General --key showWithFcitx false
cat "$HOME/.config/plasmakeyboardrc"
