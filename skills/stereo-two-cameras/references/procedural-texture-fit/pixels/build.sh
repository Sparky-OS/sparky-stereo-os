#!/bin/sh
# Build p2p (the fitter) natively: build.sh OUTDIR FR_PUBLIC_DIR
# OPTMODE=ReleaseSafe gives a checked build (slower), for finding a crash the fast build hides.
# FR_PUBLIC_DIR is an unchanged clone of github.com/farbrausch/fr_public; needs Zig 0.16 in ZIG or ~/.local/bin/zig, and python3.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
FR=${2:?name a clone of fr_public as the second argument}
ZIG=${ZIG:-$HOME/.local/bin/zig}
GEN=$OUT/gen
mkdir -p "$GEN/wz4frlib"
python3 "$HERE/../werkkzeug/patch_wz3.py" "$FR/altona_wz4/wz4/wz4frlib/wz3_bitmap_code.cpp" "$GEN/wz3_bitmap_code.cpp"
cp "$FR/altona_wz4/wz4/wz4frlib/wz3_bitmap_code.hpp" "$GEN/"
cp "$GEN/wz3_bitmap_code.hpp" "$GEN/wz4frlib/"
cd "$HERE"
export ZIG_GLOBAL_CACHE_DIR="$OUT/zigcache" ZIG_LOCAL_CACHE_DIR="$OUT/zigcache/local"
"$ZIG" build-exe p2p.zig -cflags -fno-exceptions -fno-rtti -w -fpermissive -fno-strict-aliasing -O2 -msse2 -DSTEREOTEX_WASM -I "$GEN" -I "$HERE/shim" -- wzbridge.cpp \
  -target x86_64-linux-musl -O "${OPTMODE:-ReleaseFast}" -lc -lc++ -j4 -femit-bin="$OUT/p2p"
