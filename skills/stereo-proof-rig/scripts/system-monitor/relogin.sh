#!/bin/bash
# relogin.sh: what a next login runs (the autostart entry's command), on the same machine as the session.
if [ "${MACHINE:-live}" = live ]; then $HOOK_CMD; else umockdev-run --device "$MACHINE" -- $HOOK_CMD; fi
echo "relogin hook exit $?"
cp "$HOME/.config/systemmonitorrc" "$CASE/after-relogin.rc" 2>/dev/null
