#!/bin/bash
# show-all-presets.sh: every preset visible in the sidebar (KDE's Overview stays hidden), for the title measurement.
kwriteconfig6 --file systemmonitorrc --group General --key hiddenPages overview.page
