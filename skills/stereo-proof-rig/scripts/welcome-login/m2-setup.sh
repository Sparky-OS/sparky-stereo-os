#!/bin/bash
# m2-setup.sh: USER_SETUP of the click rows: a stand-in web browser, the default for http and https, that writes each address it
# is given to $CASE/urls.txt (the address a page's button or link opens), as a desktop entry of the person's own.
set -eu
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/url-recorder.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=URL recorder
Exec=sh -c 'printf "%s\\\\n" "\$1" >> $CASE/urls.txt' url-recorder %u
MimeType=x-scheme-handler/http;x-scheme-handler/https;text/html;
NoDisplay=true
DESKTOP
cat > "$HOME/.config/mimeapps.list" <<LIST
[Default Applications]
x-scheme-handler/http=url-recorder.desktop
x-scheme-handler/https=url-recorder.desktop
text/html=url-recorder.desktop
LIST
cat "$HOME/.local/share/applications/url-recorder.desktop"
