#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# build-test-kernel.sh SRC_DIR OUT_DIR [FRAGMENT...]
#
# Builds a kernel for the bench: `make tinyconfig` (or $BASE, e.g. BASE=x86_64_defconfig for the kwin phase's
# kernel), the fragments given (default kconfig/vkms-stereo-x86_64.fragment), olddefconfig, then bzImage.
# SRC_DIR is a kernel tree with the VKMS stereo patches (README.md) and is not written to; the build goes to
# OUT_DIR (kbuild's O=). Needs gcc, make, bc, bison, flex, libssl-dev, libelf-dev (the Docker image has them).
set -eu
SRC=$(cd "${1:?usage: build-test-kernel.sh SRC_DIR OUT_DIR [FRAGMENT...]}" && pwd)
OUT=${2:?out dir}
shift 2
HERE=$(cd "$(dirname "$0")/.." && pwd)
[ $# -gt 0 ] || set -- "$HERE/kconfig/vkms-stereo-x86_64.fragment"
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
cd "$SRC"
make O="$OUT" "${BASE:-tinyconfig}" >/dev/null
# merge_config.sh makes its temporary file in the current directory: run it from OUT, so SRC can be read-only
frags=""
for f in "$@"; do frags="$frags $(cd "$(dirname "$f")" && pwd)/$(basename "$f")"; done
# shellcheck disable=SC2086
(cd "$OUT" && KCONFIG_CONFIG="$OUT/.config" "$SRC/scripts/kconfig/merge_config.sh" -m -O "$OUT" "$OUT/.config" $frags) >"$OUT/merge.log" 2>&1
make O="$OUT" olddefconfig >/dev/null
for opt in CONFIG_DRM_VKMS CONFIG_CONFIGFS_FS CONFIG_9P_FS; do
    grep -q "^$opt=y" "$OUT/.config" || { echo "build-test-kernel.sh: $opt is not built in, see $OUT/merge.log" >&2; exit 1; }
done
make O="$OUT" -j"${JOBS:-$(nproc)}" bzImage
echo "kernel: $OUT/arch/x86/boot/bzImage"
