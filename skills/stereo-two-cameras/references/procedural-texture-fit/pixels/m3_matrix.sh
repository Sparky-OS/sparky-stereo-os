#!/bin/sh
# The milestone 3 proofs (ORDER 508): the scene tester at 14.4 and 56 kbit/s, DSL 8 Mbit/s and fibre 300 Mbit/s, with
# 1, 2 and 6 connections, on the RTX 3060 (WebGPU), the AMD iGPU (WebGPU) and with the WebAssembly player.
# m3_matrix.sh OUTBASE A|B|C   (A: the dial-up runs side by side, started 90 s apart; B: the fast runs one by one;
# C: the extra runs: the negative control, a browser without WebGPU, a broken scene, the blend strips, the player
# against the native drawings on both GPUs, the scene in a viewer that ignores the mixed texture)
set -eu
OUT=$1; PH=$2
R=/K3D/partners/queue/procedures-from-pixels-508/src/tester/run-proof.sh
run() { gpu=$1; tag=$2; q=$3; t=$4; sh "$R" "$gpu" "$OUT/$tag" "$tag" "$q" "$t" > "$OUT/$tag.out" 2>&1; }
mkdir -p "$OUT"
case $PH in
A)
  for sp in d144 d56; do
    [ $sp = d144 ] && T=4300 || T=1600
    for c in 1 2 6; do
      run nvidia nv-$sp-c$c "speed=$sp&conns=$c&fps=5" $T & sleep 90
      run amd amd-$sp-c$c "speed=$sp&conns=$c&fps=5" $T & sleep 90
      run nvidia wa-$sp-c$c "speed=$sp&conns=$c&fps=5&player=wasm" $T & sleep 90
    done
  done
  run nvidia nv-d144-c6-everything "speed=d144&conns=6&fps=5&limit=everything" 4400 &
  wait ;;
B)
  for sp in dsl8 fibre300; do
    for c in 1 2 6; do
      run nvidia nv-$sp-c$c "speed=$sp&conns=$c&fps=10" 240
      run amd amd-$sp-c$c "speed=$sp&conns=$c&fps=10" 240
      run nvidia wa-$sp-c$c "speed=$sp&conns=$c&fps=10&player=wasm" 400
    done
  done ;;
C)
  run nvidia nostop-dsl15 "speed=dsl15&conns=6&fps=10&nostop=1" 90
  run cpu nogpu-dsl8 "speed=dsl8&conns=6&fps=5" 600
  SCENE=/var/tmp/procedures-from-pixels-508/m3/broken-scene run nvidia broken-dsl8 "speed=dsl8&conns=6&fps=10" 120
  for tx in 0 1 4 6; do PAGE=strip.html run nvidia strip-$tx "tex=$tx" 300; done
  PAGE=twins.html run nvidia twins-nv "" 900
  PAGE=twins.html run amd twins-amd "" 900
  NPM=/var/tmp/procedures-from-pixels-508/m3/npm PAGE=ignore.html run nvidia ignore "" 120 ;;
esac
echo "phase $PH finished"
