#!/bin/bash
# switch.sh OUT: the person's switch to KDE's Overview, as a person does it in System Monitor 6.7.4 (maximised window,
# 1920x1200): the sidebar toolbar's overflow button, Edit or Remove pages… (AT-SPI press on the menu item), then in
# Edit Pages (a popup AT-SPI does not show) by pointer and keys: tick KDE's Overview, Start with: the next entry
# (KDE's Overview, the list's third entry after Last Visited Page and the preset), untick the computer's preset, OK. A capture after each step.
# Positions (logical pixels) read from the capture of the dialog: OVERFLOW_AT, STOCK_BOX_AT, START_AT, START_ITEM_AT, OURS_BOX_AT, OK_AT.
OUT=$1
export WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-sm}
FI=${FAKEINPUT:-/rig/bin/fakeinput}
RIG=${RIG_DIR:-/rig}; RIGS=${RIGS_DIR:-/rigs}
shot() { python3 "$RIGS/capture.py" "$OUT/switch-$1.png" > /dev/null 2>&1; }
$FI m:${OVERFLOW_AT:-160,58} s:300 b:272 s:1200 > "$OUT/fi-switch.txt" 2>&1
shot 1-menu
python3 "$RIG/switch_to_stock.py" "$OUT" "${STOCK_TITLE:-Overview}" "${EDIT_PAGES:-Edit or Remove pages…}" > "$OUT/switch-press.txt" 2>&1
sleep 1; shot 2-dialog
$FI m:${STOCK_BOX_AT:-526,443} s:300 b:272 s:800 >> "$OUT/fi-switch.txt" 2>&1; shot 3-stock-ticked
$FI m:${START_AT:-690,884} s:300 b:272 s:1000 m:${START_ITEM_AT:-640,987} s:300 b:272 s:800 >> "$OUT/fi-switch.txt" 2>&1; shot 4-start-with
$FI m:${OURS_BOX_AT:-526,396} s:300 b:272 s:800 >> "$OUT/fi-switch.txt" 2>&1; shot 5-ours-unticked
$FI m:${OK_AT:-1300,884} s:300 b:272 s:1500 >> "$OUT/fi-switch.txt" 2>&1; shot 6-after-ok
