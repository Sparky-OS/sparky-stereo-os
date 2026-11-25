#!/bin/bash
# m9-setup.sh: USER_SETUP of the three pages' click rows. With VARIETY_RAN=1 the account has started Stereo Variety before:
# its first-run mark (~/.config/variety/.firstrun, VarietyWindow's fr_file) is there, so "variety --preferences" opens
# its Preferences instead of its welcome and privacy questions.
set -eu
if [ "${VARIETY_RAN:-0}" = 1 ]; then
	mkdir -p "$HOME/.config/variety"
	date '+%Y-%m-%d %H:%M:%S' > "$HOME/.config/variety/.firstrun"
	echo "variety first-run mark: $HOME/.config/variety/.firstrun"
fi
