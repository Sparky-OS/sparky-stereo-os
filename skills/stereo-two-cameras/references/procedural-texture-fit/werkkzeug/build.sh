#!/bin/sh
# Build wzrender from an unchanged clone of fr_public.
# Usage: KTG_IMAGE=image build.sh FR_PUBLIC_DIR BUILD_DIR     (DOCKER_HOST points at your Docker socket)
set -eu
FR=$1; B=$2
HERE=$(cd "$(dirname "$0")" && pwd)
IMAGE=${KTG_IMAGE:?name a local container image that has g++}
mkdir -p "$B"
python3 "$HERE/patch_wz3.py" "$FR/altona_wz4/wz4/wz4frlib/wz3_bitmap_code.cpp" "$B/wz3_bitmap_code.cpp"
rm -rf "$B/shim"; cp -r "$HERE/shim" "$B/shim"
cp "$FR/altona_wz4/wz4/wz4frlib/wz3_bitmap_code.hpp" "$B/shim/wz4frlib/"
cp "$HERE/wzrender.cpp" "$B/"
docker run --rm --name x3d-473x-build --network none --ulimit core=0 --cpus 2 --user "$(id -u):$(id -g)" \
  -v "$B:$B" "$IMAGE" sh -euc "cd '$B' && g++ -O2 -w -fpermissive -msse2 -fno-strict-aliasing -I shim -o wzrender wzrender.cpp"
