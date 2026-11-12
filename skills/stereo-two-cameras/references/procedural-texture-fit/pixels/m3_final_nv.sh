#!/bin/sh
# Milestone 3, phase E: the RTX's dial-up runs again with the final page (in phase A, on the old page, jobs still in
# flight when a picture came kept submitting after their texture stopped: the starved browser drew its tiles for
# minutes). m3_final_nv.sh OUTBASE
set -eu
OUT=$1
R=/K3D/partners/queue/procedures-from-pixels-508/src/tester/run-proof.sh
run() { gpu=$1; tag=$2; q=$3; t=$4; sh "$R" "$gpu" "$OUT/$tag" "$tag" "$q" "$t" > "$OUT/$tag.out" 2>&1; }
mkdir -p "$OUT"
for c in 1 2 6; do run nvidia final-nv-d144-c$c "speed=d144&conns=$c&fps=5" 4600 & sleep 120; done
for c in 1 2 6; do run nvidia final-nv-d56-c$c "speed=d56&conns=$c&fps=5" 1900 & sleep 120; done
wait
echo "phase E finished"
