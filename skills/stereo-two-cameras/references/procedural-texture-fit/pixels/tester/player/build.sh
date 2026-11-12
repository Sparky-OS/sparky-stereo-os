#!/bin/sh
# Build the WebAssembly procedure player (the modern operators only): build.sh OUT.wasm
# Needs Zig 0.16 in ZIG (default: zig on the PATH). OPS: the folder of the operators' own files (NAME.zig and
# common.zig; default: ops/ beside this script, or ../../ops where this script lies in the skill's tree).
# OPTMODE: ReleaseSmall (default, about 85 KB) or ReleaseFast (about 217 KB, about a quarter faster; the same bytes
# drawn). The same processor as ORDER 508's player (the first WebAssembly processor with SIMD, without the
# saturating float-to-integer conversions), so the operators draw the same bytes. A reactor (no entry, no imports):
# the C library is linked only for its allocator.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:?name the output file}
case $OUT in /*) ;; *) OUT=$PWD/$OUT ;; esac
ZIG=${ZIG:-zig}
if [ -n "${OPS:-}" ]; then :; elif [ -d "$HERE/ops" ]; then OPS=$HERE/ops; else OPS=$HERE/../../ops; fi
[ -f "$OPS/common.zig" ] || { echo "no operators in $OPS" >&2; exit 1; }
B=$(mktemp -d)
trap 'rm -rf "$B"' EXIT
mkdir "$B/ops"
cp "$HERE/ptr_player.zig" "$B/"
cp "$OPS"/*.zig "$B/ops/"
cd "$B"
"$ZIG" build-exe ptr_player.zig -target wasm32-wasi -mcpu=mvp+simd128 -O "${OPTMODE:-ReleaseSmall}" -lc \
  -mexec-model=reactor -rdynamic -fstrip -femit-bin="$OUT"
