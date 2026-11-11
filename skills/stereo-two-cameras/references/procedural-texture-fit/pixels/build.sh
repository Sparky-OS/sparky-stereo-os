#!/bin/sh
# Build p2p (the fitter) natively: build.sh OUTDIR FR_PUBLIC_DIR FREETYPE_DIR
# OPTMODE=ReleaseSafe gives a checked build (slower), for finding a crash the fast build hides.
# FR_PUBLIC_DIR is an unchanged clone of github.com/farbrausch/fr_public; FREETYPE_DIR is FreeType's unpacked
# source (2.14.3 was used; the Text operator draws through it); needs Zig 0.16 in ZIG or ~/.local/bin/zig, and python3.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
FR=${2:?name a clone of fr_public as the second argument}
FT=${3:?name the unpacked FreeType source as the third argument}
[ -f "$FT/src/base/ftbase.c" ] || { echo "no FreeType source in $FT" >&2; exit 1; }
ZIG=${ZIG:-$HOME/.local/bin/zig}
GEN=$OUT/gen
mkdir -p "$GEN/wz4frlib"
python3 "$HERE/../werkkzeug/patch_wz3.py" --keep-text "$FR/altona_wz4/wz4/wz4frlib/wz3_bitmap_code.cpp" "$GEN/wz3_bitmap_code.cpp"
cp "$FR/altona_wz4/wz4/wz4frlib/wz3_bitmap_code.hpp" "$GEN/"
cp "$GEN/wz3_bitmap_code.hpp" "$GEN/wz4frlib/"
# FreeType with only what reads outlines: TrueType and CFF fonts, and the anti-aliasing rasteriser
cat > "$GEN/ftmodule-p2p.h" <<'MOD'
FT_USE_MODULE( FT_Driver_ClassRec, tt_driver_class )
FT_USE_MODULE( FT_Driver_ClassRec, cff_driver_class )
FT_USE_MODULE( FT_Module_Class, psaux_module_class )
FT_USE_MODULE( FT_Module_Class, psnames_module_class )
FT_USE_MODULE( FT_Module_Class, pshinter_module_class )
FT_USE_MODULE( FT_Module_Class, sfnt_module_class )
FT_USE_MODULE( FT_Renderer_Class, ft_smooth_renderer_class )
MOD
FTC="-O2 -w -DFT2_BUILD_LIBRARY -DFT_CONFIG_MODULES_H=<ftmodule-p2p.h> -I $GEN -I $FT/include"
cd "$HERE"
export ZIG_GLOBAL_CACHE_DIR="$OUT/zigcache" ZIG_LOCAL_CACHE_DIR="$OUT/zigcache/local"
# shellcheck disable=SC2086
"$ZIG" build-exe p2p.zig -cflags -fno-exceptions -fno-rtti -w -fpermissive -fno-strict-aliasing -O2 -msse2 -DSTEREOTEX_WASM -I "$GEN" -I "$HERE/shim" -- wzbridge.cpp \
  -cflags $FTC -- wzfont.c \
  "$FT/src/base/ftsystem.c" "$FT/src/base/ftinit.c" "$FT/src/base/ftdebug.c" "$FT/src/base/ftbase.c" "$FT/src/base/ftbbox.c" \
  "$FT/src/base/ftbitmap.c" "$FT/src/base/ftglyph.c" "$FT/src/base/ftmm.c" "$FT/src/truetype/truetype.c" "$FT/src/sfnt/sfnt.c" \
  "$FT/src/smooth/smooth.c" "$FT/src/cff/cff.c" "$FT/src/psaux/psaux.c" "$FT/src/pshinter/pshinter.c" "$FT/src/psnames/psnames.c" \
  "$FT/src/gzip/ftgzip.c" \
  -target x86_64-linux-musl -O "${OPTMODE:-ReleaseFast}" -lc -lc++ -j4 -femit-bin="$OUT/p2p"
