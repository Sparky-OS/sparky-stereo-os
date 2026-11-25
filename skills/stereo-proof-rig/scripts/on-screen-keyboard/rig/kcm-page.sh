#!/bin/bash
# kcm-page.sh: inside a rig session (kb-login.sh STEP=kcm-page.sh): Plasma Keyboard's settings page, captured, with KWin's
# window list. Env: CASE, LANE, RIG, SESSION_LOG.
set -u
# the session's configuration path (the hardware layer's folder in front of XDG_CONFIG_DIRS), as System Settings started
# from the session has it; the rig's own shell does not
XDG_CONFIG_DIRS=$(sed -n 's/^XDG_CONFIG_DIRS=//p' "$CASE/session-env.txt") kcmshell6 kcm_plasmakeyboard > "$CASE/kcm.log" 2>&1 &
sleep 12
python3 "$LANE/kwin-windows.py" "$SESSION_LOG" > "$CASE/windows-kcm.json"
python3 "$RIG/kwin_script.py" "$SESSION_LOG" 'var ws = workspace.stackingOrder; for (var i = 0; i < ws.length; i++) { var w = ws[i]; if (String(w.resourceClass).indexOf("kcmshell") >= 0) { w.setMaximize(true, true); workspace.activeWindow = w; } }'
sleep 3
python3 "$RIG/login-splash/shot.py" Virtual-0 "$CASE/kcm-page.png" > /dev/null
for p in $(pgrep -x kcmshell6); do kill -TERM "$p"; done
