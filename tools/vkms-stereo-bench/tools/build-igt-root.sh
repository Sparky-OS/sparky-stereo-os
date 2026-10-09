#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# build-igt-root.sh OUT_DIR [IGT_COMMIT]
#
# Builds IGT GPU Tools' kms_3d in the image of igt/Dockerfile (as your user, 4 CPUs) and turns that image into a
# root file system in OUT_DIR for the igt phase: kms_3d and libigt in /usr/local, its pictures in
# /usr/local/share/igt-gpu-tools. Runs on the host (it needs docker). IGT_COMMIT defaults to the tip of master.
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:?usage: build-igt-root.sh OUT_DIR [IGT_COMMIT]}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
SRC="$OUT.src"
IMAGE=${IGT_IMAGE:-vkms-stereo-bench-igt:1}
docker image inspect "$IMAGE" >/dev/null 2>&1 || docker build -t "$IMAGE" "$HERE/igt"
if [ ! -d "$SRC/igt" ]; then
    mkdir -p "$SRC"
    git clone -q https://gitlab.freedesktop.org/drm/igt-gpu-tools.git "$SRC/igt"
fi
[ -n "${2:-}" ] && git -C "$SRC/igt" checkout -q "$2"
docker run --rm --cpus 4 --user "$(id -u):$(id -g)" -v "$SRC:$SRC" -e HOME=/tmp "$IMAGE" sh -c "
    meson setup --wipe '$SRC/build' '$SRC/igt' -Dprefix=/usr/local -Dtests=enabled -Drunner=disabled \
        -Dchamelium=disabled -Dvalgrind=disabled -Dman=disabled -Ddocs=disabled -Doverlay=disabled \
        -Dtestplan=disabled -Dsphinx=disabled -Dlibdrm_drivers= -Dvmtb=disabled -Doping=disabled \
        -Dlibunwind=enabled -Dxe_driver=disabled >/dev/null &&
    ninja -C '$SRC/build' -j4 tests/kms_3d"
cid=$(docker create "$IMAGE")
docker export "$cid" | tar -x -C "$OUT" 2>/dev/null || true
docker rm "$cid" >/dev/null
mkdir -p "$OUT/usr/local/bin" "$OUT/usr/local/lib" "$OUT/usr/local/share/igt-gpu-tools"
cp "$SRC/build/tests/kms_3d" "$OUT/usr/local/bin/"
cp -L "$SRC/build/lib/libigt.so.0" "$OUT/usr/local/lib/"
cp "$SRC/igt/data/1080p-left.png" "$SRC/igt/data/1080p-right.png" "$OUT/usr/local/share/igt-gpu-tools/"
echo "IGT root: $OUT ($(git -C "$SRC/igt" log -1 --format=%h))"
