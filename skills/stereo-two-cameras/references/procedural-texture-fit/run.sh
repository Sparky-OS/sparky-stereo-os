#!/bin/sh
# Build the driver, make the controls, fit every picture, check the controls.
# Usage: KTG_IMAGE=image run.sh WORKDIR OUTDIR
# WORKDIR holds fr_public/ (a clone of github.com/farbrausch/fr_public) and tex/*.png
# (2048 x 2048 pictures); DOCKER_HOST points at your Docker socket.
set -eu
WORK=$1; OUT=$2
HERE=$(cd "$(dirname "$0")" && pwd)
IMAGE=${KTG_IMAGE:?name a local container image that has g++}
mkdir -p "$WORK/bin" "$WORK/oct" "$OUT"
docker run --rm --network none --ulimit core=0 --cpus 4 --user "$(id -u):$(id -g)" \
  -v "$WORK:$WORK" -v "$HERE:/src:ro" "$IMAGE" sh -euc "
    cd '$WORK'
    g++ -O2 -w -I fr_public/ktg -o bin/ktgtool /src/ktgtool.cpp
    for t in 0 1; do for F in 0 1 2 3 4 5 6 7 8 9; do bin/ktgtool octave 9 \$F \$t 1 > oct/o_\${t}_\${F}.f32; done; done"
python3 "$HERE/make_controls.py" "$WORK"
# three pictures at a time (one process each)
for f in "$WORK"/tex/*.png; do printf '%s=%s\n' "$(basename "$f" .png)" "$f"; done |
  xargs -P 3 -n 1 python3 "$HERE/fit.py" "$WORK" "$OUT"
python3 "$HERE/check_controls.py" "$WORK" "$OUT"
