#!/bin/sh
# Draw every found procedure of a fit folder and every rung of its tiles (run inside the lane's container):
# m2render.sh BINARY FITDIR OUTDIR
# A tile of level 0 is drawn at 2048 pixels, of level 1 at 1024, of level 2 at 512: each at its window's own size.
set -eu
B=$1; F=$2; O=$3
mkdir -p "$O"
for s in "$F"/L*.script; do
  [ -e "$s" ] || continue
  b=$(basename "$s" .script)
  case "$b" in
    L0-*) e=11 ;;
    L1-*) e=10 ;;
    *) e=9 ;;
  esac
  case "$b" in
    *.r[0-9][0-9]) ;;
    *) [ -e "$O/$b.ppm" ] || "$B" render "$s" "$O/$b.ppm" "$e" > "$O/$b.render.out" 2>&1 || echo "render failed: $b" ;;
  esac
done
for s in "$F"/L2-*.r[0-9][0-9].script; do
  [ -e "$s" ] || continue
  b=$(basename "$s" .script)
  [ -e "$O/$b.ppm" ] || "$B" render "$s" "$O/$b.ppm" 9 > "$O/$b.render.out" 2>&1 || echo "render failed: $b"
done
echo "rendered $(ls "$O"/*.ppm 2>/dev/null | wc -l) pictures in $O"
