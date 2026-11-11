#!/bin/sh
# Milestone 3, phase F: the fibre runs again after the link's bucket was bounded to five chunks' time above
# 25.6 Mbit/s (0.1 s had been more than half of the 0.17 s a 300 Mbit/s transfer of the pictures lasts).
# m3_fibre.sh OUTBASE
set -eu
OUT=$1
R=/K3D/partners/queue/procedures-from-pixels-508/src/tester/run-proof.sh
run() { gpu=$1; tag=$2; q=$3; t=$4; sh "$R" "$gpu" "$OUT/$tag" "$tag" "$q" "$t" > "$OUT/$tag.out" 2>&1; }
mkdir -p "$OUT"
for c in 1 2 6; do
  run nvidia f-nv-fibre300-c$c "speed=fibre300&conns=$c&fps=10" 240
  run amd f-amd-fibre300-c$c "speed=fibre300&conns=$c&fps=10" 240
  run nvidia f-wa-fibre300-c$c "speed=fibre300&conns=$c&fps=10&player=wasm" 400
done
# the negative control again on the AMD iGPU (the RTX's browser, starved by the machine's load, had drawn almost
# nothing before its pictures came), watched 20 s after every picture is in
run amd nostop-amd-dsl15 "speed=dsl15&conns=6&fps=10&nostop=1" 200
echo "phase F finished"
