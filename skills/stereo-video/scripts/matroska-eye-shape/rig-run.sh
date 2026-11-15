#!/bin/bash
# Runs rig-case.sh for each "PLAYER FIXTURE" line of a list, one fresh session each.
# Usage (as uid 1000 with the render group, in the rig container): rig-run.sh LIST FIXTURES OUTROOT [WAIT]
set -u
while read -r player fixture; do
	[ -z "$player" ] && continue
	out="$3/$player/$fixture"
	rm -rf "$out"; mkdir -p "$out"
	env HOME=/home/tester timeout 60 bash /scripts/rig-case.sh "$player" "$2/$fixture.mkv" "$out" "${4:-8}"
	python3 /scripts/analyze-capture.py "$out/capture.png" 1920 > "$out/result.json" 2> "$out/analyze.err" || echo '{}' > "$out/result.json"
	echo "$player $fixture $(cat "$out/declarations" 2>/dev/null) $(cat "$out/result.json")"
done < "$1"
