#!/bin/bash
# USER_SETUP: Fcitx 5 without its keyboard addon ("DBus Virtual Keyboard"), as Fcitx 5's global configuration writes it
set -eu
mkdir -p "$HOME/.config/fcitx5"
printf '[Behavior/DisabledAddons]\n0=virtualkeyboard\n' > "$HOME/.config/fcitx5/config"
cat "$HOME/.config/fcitx5/config"
