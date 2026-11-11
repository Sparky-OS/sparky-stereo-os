#!/bin/sh
# Build p2p (the fitter) natively: build.sh OUTDIR FR_PUBLIC_DIR FREETYPE_DIR LIBS_DIR
# FR_PUBLIC_DIR is an unchanged clone of github.com/farbrausch/fr_public; FREETYPE_DIR is FreeType's unpacked
# source (2.14.3 was used). LIBS_DIR holds the unpacked sources of the libraries Text version 2 draws with
# (Debian forky's source packages): harfbuzz-14.4.0, sheenbidi-3.0.0, the plutovg and plutosvg folders,
# libpng-1.6.59, zlib, brotli, and Unicode's Blocks.txt. Needs Zig 0.16 in ZIG or ~/.local/bin/zig, and python3.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
FR=${2:?name a clone of fr_public as the second argument}
FT=${3:?name the unpacked FreeType source as the third argument}
L=${4:?name the folder of the libraries Text version 2 needs as the fourth argument}
[ -f "$FT/src/base/ftbase.c" ] || { echo "no FreeType source in $FT" >&2; exit 1; }
one() { set -- $1; [ -e "$1" ] || { echo "not found: $1" >&2; exit 1; }; echo "$1"; }
HB=$(one "$L/harfbuzz-*"); SB=$(one "$L/sheenbidi-*"); PVG=$(one "$L/*plutovg-*"); PSVG=$(one "$L/*plutosvg-*")
PNG=$(one "$L/libpng-*"); ZL=$(one "$L/zlib-*"); BR=$(one "$L/*brotli-*")
[ -f "$L/Blocks.txt" ] || { echo "no Blocks.txt in $L" >&2; exit 1; }
ZIG=${ZIG:-$HOME/.local/bin/zig}
GEN=$OUT/gen
mkdir -p "$GEN/wz4frlib"
python3 "$HERE/farbrausch/patch_wz3.py" "$FR/altona_wz4/wz4/wz4frlib/wz3_bitmap_code.cpp" "$GEN/wz3_bitmap_code.cpp"
cp "$FR/altona_wz4/wz4/wz4frlib/wz3_bitmap_code.hpp" "$GEN/"
cp "$GEN/wz3_bitmap_code.hpp" "$GEN/wz4frlib/"
# Unicode's blocks, for the font index's coverage column
python3 - "$L/Blocks.txt" "$GEN/ublocks.h" <<'PY'
import sys, re
rows = []
for line in open(sys.argv[1], encoding='utf-8'):
    m = re.match(r'^([0-9A-F]+)\.\.([0-9A-F]+); (.+)$', line.strip())
    if m:
        rows.append((int(m.group(1), 16), int(m.group(2), 16), m.group(3)))
with open(sys.argv[2], 'w') as f:
    f.write('static const struct { unsigned lo, hi; const char *name; } ublocks[] = {\n')
    for lo, hi, n in rows:
        f.write('  { 0x%X, 0x%X, "%s" },\n' % (lo, hi, n))
    f.write('};\n')
PY
# Which characters are presentation variants of others (the reading takes the plain character): combining and
# modifier marks and letters (general categories Mn, Me, Lm, Sk) and every character whose compatibility normalisation
# (NFKC) is another (fullwidth, superscript, mathematical, ligature and compatibility forms), from this Python's
# Unicode data; and the specialist letter blocks (Latin Extended-B, IPA and phonetic extensions, Latin Extended-D to -G, Cyrillic
# Extended-B to -D), which the reading takes only when they lie clearly closer than any plain letter
python3 - "$GEN/uvariant.h" <<'PY'
import sys, unicodedata
ranges = []
start = None
for c in range(0x110000):
    ch = chr(c)
    cat = unicodedata.category(ch)
    v = cat in ('Mn', 'Me', 'Lm', 'Sk') or (cat not in ('Cn', 'Cs', 'Co') and unicodedata.normalize('NFKC', ch) != ch)
    if v and start is None:
        start = c
    if not v and start is not None:
        ranges.append((start, c - 1)); start = None
if start is not None:
    ranges.append((start, 0x10FFFF))
special = [(0x180, 0x24F), (0x250, 0x2AF), (0x1D00, 0x1DBF), (0xA720, 0xA7FF), (0xAB30, 0xAB6F), (0x10780, 0x107BF), (0x1DF00, 0x1DFFF),
           (0xA640, 0xA69F), (0x1C80, 0x1C8F), (0x1E030, 0x1E08F)]
with open(sys.argv[1], 'w') as f:
    f.write('/* generated from Python %s unicodedata (Unicode %s) */\n' % (sys.version.split()[0], unicodedata.unidata_version))
    f.write('static const unsigned uvariant_ranges[][2] = {\n')
    for a, b in ranges:
        f.write('  { 0x%X, 0x%X },\n' % (a, b))
    f.write('};\nstatic const unsigned uspecial_ranges[][2] = {\n')
    for a, b in special:
        f.write('  { 0x%X, 0x%X },\n' % (a, b))
    # characters that are drawings rather than letters (general categories So and Sm, and private use, where icon
    # fonts put their pictures): the seeds of milestone 2 prefer them
    draw = []
    start = None
    for c in range(0x110000):
        d = unicodedata.category(chr(c)) in ('So', 'Sm', 'Co')
        if d and start is None:
            start = c
        if not d and start is not None:
            draw.append((start, c - 1)); start = None
    if start is not None:
        draw.append((start, 0x10FFFF))
    f.write('};\nstatic const unsigned udrawing_ranges[][2] = {\n')
    for a, b in draw:
        f.write('  { 0x%X, 0x%X },\n' % (a, b))
    f.write('};\n')
PY
# FreeType with every font driver (TrueType, CFF and CFF2, Type 1, CID, Type 42, PFR, Windows FNT, PCF, BDF),
# the SVG module for plutosvg's hooks, PNG for colour bitmaps, zlib and Brotli for WOFF and WOFF2
cat > "$GEN/ftmodule-p2p.h" <<'MOD'
FT_USE_MODULE( FT_Driver_ClassRec, tt_driver_class )
FT_USE_MODULE( FT_Driver_ClassRec, t1_driver_class )
FT_USE_MODULE( FT_Driver_ClassRec, cff_driver_class )
FT_USE_MODULE( FT_Driver_ClassRec, t1cid_driver_class )
FT_USE_MODULE( FT_Driver_ClassRec, pfr_driver_class )
FT_USE_MODULE( FT_Driver_ClassRec, t42_driver_class )
FT_USE_MODULE( FT_Driver_ClassRec, winfnt_driver_class )
FT_USE_MODULE( FT_Driver_ClassRec, pcf_driver_class )
FT_USE_MODULE( FT_Driver_ClassRec, bdf_driver_class )
FT_USE_MODULE( FT_Module_Class, psaux_module_class )
FT_USE_MODULE( FT_Module_Class, psnames_module_class )
FT_USE_MODULE( FT_Module_Class, pshinter_module_class )
FT_USE_MODULE( FT_Module_Class, sfnt_module_class )
FT_USE_MODULE( FT_Renderer_Class, ft_smooth_renderer_class )
FT_USE_MODULE( FT_Renderer_Class, ft_svg_renderer_class )
MOD
sed -e 's|^/\* #define FT_CONFIG_OPTION_SYSTEM_ZLIB \*/|#define FT_CONFIG_OPTION_SYSTEM_ZLIB|' \
    -e 's|^/\* #define FT_CONFIG_OPTION_USE_PNG \*/|#define FT_CONFIG_OPTION_USE_PNG|' \
    -e 's|^/\* #define FT_CONFIG_OPTION_USE_BROTLI \*/|#define FT_CONFIG_OPTION_USE_BROTLI|' \
    "$FT/include/freetype/config/ftoption.h" > "$GEN/ftoption-p2p.h"
for o in SYSTEM_ZLIB USE_PNG USE_BROTLI SVG; do grep -q "^#define FT_CONFIG_OPTION_$o" "$GEN/ftoption-p2p.h" || { echo "FreeType option $o not set" >&2; exit 1; }; done
cp "$PNG/scripts/pnglibconf.h.prebuilt" "$GEN/pnglibconf.h"
INC="-I $GEN -I $FT/include -I $ZL -I $PNG -I $BR/c/include -I $HB/src -I $SB/Headers -I $PVG/include -I $PSVG/source"
FTC="-O2 -w -DFT2_BUILD_LIBRARY -DFT_CONFIG_MODULES_H=<ftmodule-p2p.h> -DFT_CONFIG_OPTIONS_H=<ftoption-p2p.h> $INC"
FTD="-DFT_CONFIG_MODULES_H=<ftmodule-p2p.h> -DFT_CONFIG_OPTIONS_H=<ftoption-p2p.h>"
HBC="-O2 -w -fno-exceptions -fno-rtti $FTD -DHAVE_FREETYPE=1 -DHAVE_PNG=1 -DHB_NO_MT -DHAVE_FT_GET_VAR_BLEND_COORDINATES -DHAVE_FT_SET_VAR_BLEND_COORDINATES -DHAVE_FT_DONE_MM_VAR -DHAVE_FT_GET_TRANSFORM $INC"
CC="-O2 -w $FTD -DSB_CONFIG_UNITY -DPLUTOVG_BUILD -DPLUTOVG_BUILD_STATIC -DPLUTOSVG_BUILD -DPLUTOSVG_BUILD_STATIC -DPLUTOSVG_HAS_FREETYPE -DPNG_ARM_NEON_OPT=0 -DPNG_INTEL_SSE_OPT=0 -DPNG_POWERPC_VSX_OPT=0 -DPNG_LOONGARCH_LSX_OPT=0 -DPNG_RISCV_RVV_OPT=0 -DPNG_MIPS_MSA_OPT=0 -DPNG_MIPS_MMI_OPT=0 $INC"
cd "$HERE"
export ZIG_GLOBAL_CACHE_DIR="$OUT/zigcache" ZIG_LOCAL_CACHE_DIR="$OUT/zigcache/local"
FTSRC="$FT/src/base/ftsystem.c $FT/src/base/ftinit.c $FT/src/base/ftdebug.c $FT/src/base/ftbase.c $FT/src/base/ftbbox.c
  $FT/src/base/ftbitmap.c $FT/src/base/ftglyph.c $FT/src/base/ftmm.c $FT/src/base/fttype1.c
  $FT/src/truetype/truetype.c $FT/src/sfnt/sfnt.c $FT/src/smooth/smooth.c $FT/src/cff/cff.c $FT/src/cid/type1cid.c
  $FT/src/type1/type1.c $FT/src/type42/type42.c $FT/src/pfr/pfr.c $FT/src/winfonts/winfnt.c $FT/src/pcf/pcf.c $FT/src/bdf/bdf.c
  $FT/src/psaux/psaux.c $FT/src/pshinter/pshinter.c $FT/src/psnames/psnames.c $FT/src/svg/svg.c
  $FT/src/gzip/ftgzip.c $FT/src/lzw/ftlzw.c"
ZLSRC=$(for f in adler32 compress crc32 deflate infback inffast inflate inftrees trees uncompr zutil; do printf '%s ' "$ZL/$f.c"; done)
PNGSRC=$(for f in png pngerror pngget pngmem pngpread pngread pngrio pngrtran pngrutil pngset pngtrans pngwio pngwrite pngwtran pngwutil; do printf '%s ' "$PNG/$f.c"; done)
BRSRC=$(ls "$BR"/c/common/*.c "$BR"/c/dec/*.c | tr '\n' ' ')
PVGSRC=$(ls "$PVG"/source/*.c | tr '\n' ' ')
# shellcheck disable=SC2086
"$ZIG" build-exe p2p.zig -cflags -fno-exceptions -fno-rtti -w -fpermissive -fno-strict-aliasing -O2 -msse2 -DSTEREOTEX_WASM -I "$GEN" -I "$HERE/farbrausch/shim" -- wzbridge.cpp \
  -cflags $HBC -- "$HB/src/harfbuzz.cc" "$HB/src/hb-raster-image.cc" "$HB/src/hb-raster-draw.cc" "$HB/src/hb-raster-paint.cc" \
  -cflags $FTC -- wzfont.c wztext2.c wzfontindex.c $FTSRC \
  -cflags $CC -I "$SB/Source" -- "$SB/Source/SheenBidi.c" \
  -cflags $CC -- $PVGSRC "$PSVG/source/plutosvg.c" $ZLSRC $PNGSRC $BRSRC \
  -target x86_64-linux-musl -O "${OPTMODE:-ReleaseFast}" -lc -lc++ -j4 -femit-bin="$OUT/p2p"
