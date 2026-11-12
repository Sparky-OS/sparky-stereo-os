#!/bin/sh
# The comparison matrix (ORDER 537): the link simulated in the page against the local server's, in the cells of
# milestone 3's table: 14.4 and 56 kbit/s and DSL 8 Mbit/s; 1, 2 and 6 connections with the limit on the pictures,
# and 6 connections with the limit on everything; the WebGPU player on the AMD iGPU and the WebAssembly player in a
# browser without WebGPU (no GPU device: Mesa's lavapipe draws the scene). Every cell runs twice: link=page and
# link=server, side by side at dial-up, one after the other at DSL.
# matrix.sh OUTBASE PHASE...   phases, in the order given, each waited for before the next:
#   A  14.4 kbit/s, all sixteen runs side by side (an hour)
#   B  56 kbit/s without a GPU, eight runs side by side (a quarter of an hour)
#   C  56 kbit/s on the GPU, eight runs side by side
#   D  DSL 8 Mbit/s, sixteen runs one after another
# At most eight browsers use the GPU at once when A and C are not run together (it also drives the person's screens).
# Run it from a frozen copy of the tree (TREE=COPY sh COPY/tools/matrix.sh ...), so an edit never reaches a run.
set -u
OUT=$1; shift
R=$(cd "$(dirname "$0")" && pwd)/run-proof.sh
run() { gpu=$1; tag=$2; q=$3; t=$4; sh "$R" "$gpu" "$OUT/$tag" "$tag" "$q" "$t" > "$OUT/$tag.out" 2>&1; }
runcpu() { WINDOW=1100,900 run cpu "$@"; }
mkdir -p "$OUT"
# the cells: "SUFFIX QUERY"
CELLS='c1 conns=1
c2 conns=2
c6 conns=6
c6-everything conns=6&limit=everything'
for PH in "$@"; do
  pids=""
  # no pipe into this loop: the runs it starts must be this shell's children, or `wait` returns at once
  IFS='
'
  for cell in $CELLS; do
    unset IFS
    sfx=${cell%% *}; q=${cell#* }
    for link in page server; do
      [ "$link" = server ] && lq="&link=server" || lq=""
      case $PH in
        A) run amd "amd-d144-$sfx-$link" "speed=d144&$q&fps=5$lq" 4600 & pids="$pids $!"; sleep 20
           runcpu "wa-d144-$sfx-$link" "speed=d144&$q&fps=2$lq" 4600 & pids="$pids $!"; sleep 40 ;;
        B) runcpu "wa-d56-$sfx-$link" "speed=d56&$q&fps=2$lq" 1700 & pids="$pids $!"; sleep 45 ;;
        C) run amd "amd-d56-$sfx-$link" "speed=d56&$q&fps=5$lq" 1700 & pids="$pids $!"; sleep 30 ;;
        D) run amd "amd-dsl8-$sfx-$link" "speed=dsl8&$q&fps=10$lq" 240
           runcpu "wa-dsl8-$sfx-$link" "speed=dsl8&$q&fps=5$lq" 400 ;;
        *) echo "phase must be A, B, C or D" >&2; exit 2 ;;
      esac
    done
  done
  unset IFS
  # shellcheck disable=SC2086
  [ -n "$pids" ] && wait $pids
  echo "phase $PH finished $(date -u +%H:%M:%S)"
done
