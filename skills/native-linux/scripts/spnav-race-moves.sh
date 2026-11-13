#!/bin/sh
# SPDX-License-Identifier: MIT
# HOOK for the race count: three moves with autofocus on, then whether the program is still there.
D=$1
echo "40 25 0 0 0 0 0" > "$D/trig/go-1"; sleep 2.5
echo "40 0 0 25 0 0 0" > "$D/trig/go-2"; sleep 2.5
echo "50 0 0 0 0 100 0" > "$D/trig/go-3"; sleep 2.5
echo "40 -25 0 -25 0 0 0" > "$D/trig/go-4"; sleep 2.5
grep "camera position" "$D/out/app.stderr" | tail -1 > "$D/out/cam-end.txt"
