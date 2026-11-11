#!/bin/sh
# Milestone 3, phase D: the final page at dial-up (the dial-up matrix ran the page before three changes: a job stops at
# its next operator once its picture is in, passes timed by GPU timestamps, the panel's headline and legend).
# m3_final.sh OUTBASE
set -eu
OUT=$1
R=/K3D/partners/queue/procedures-from-pixels-508/src/tester/run-proof.sh
run() { gpu=$1; tag=$2; q=$3; t=$4; sh "$R" "$gpu" "$OUT/$tag" "$tag" "$q" "$t" > "$OUT/$tag.out" 2>&1; }
mkdir -p "$OUT"
run amd final-amd-d56-c6 "speed=d56&conns=6&fps=5" 1700 &
sleep 120
run nvidia final-wa-d56-c2 "speed=d56&conns=2&fps=5&player=wasm" 1700 &
sleep 120
run nvidia final-nv-d144-c6 "speed=d144&conns=6&fps=5" 600 &
wait
echo "phase D finished"
