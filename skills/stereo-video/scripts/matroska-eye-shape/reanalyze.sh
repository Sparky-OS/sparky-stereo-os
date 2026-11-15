#!/bin/sh
# Measures every capture of a rig run again: ROOT/PLAYER/FIXTURE/capture.png -> result.json, one line each to stdout
set -u
for d in "$1"/*/*/; do
	[ -f "$d/capture.png" ] || continue
	p=$(basename "$(dirname "$d")"); f=$(basename "$d")
	python3 /scripts/analyze-capture.py "$d/capture.png" 1920 > "$d/result.json" 2>/dev/null || echo '{}' > "$d/result.json"
	echo "$p $f $(cat "$d/declarations" 2>/dev/null) $(cat "$d/result.json")"
done
