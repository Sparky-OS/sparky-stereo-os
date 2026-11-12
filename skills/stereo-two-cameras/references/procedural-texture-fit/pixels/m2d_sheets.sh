#!/bin/sh
# The sheets of milestone 2d (four procedures per picture, and Daniel's verdicts on 2c's sheets), from the renders in
# SCRATCH/m2d: m2d_sheets.sh SCRATCH EVIDENCE   (each sheet looked at before a word is written about it)
set -eu
S=$1; E=$2
L=$(cd "$(dirname "$0")" && pwd)/m2d_look.py
mkdir -p "$E/sheets"
cd "$S"
X=768,768,512   # the 512 pixels at 1:1 around the centre, where the four quarters meet
PH="bark_brown_02 coast_sand_rocks_02 concrete_floor_02 plaster_grey_04 rock_05 rust_coarse_01 rusty_metal_02"
four() { [ -f "m2d/rF/$1-simple.ppm" ] && echo "2d-four=m2d/rF/$1-simple.ppm" || true; }
fourx() { [ -f "m2d/rF/$1-simple.ppm" ] && echo "1:1-2d-four=m2d/rF/$1-simple.ppm@$X" || true; }
# 1. the photographs: picture, 2b, 2c, 2d one procedure, 2d four procedures (simple), and four with close-up layers
a=""
for n in $PH; do
  a="$a picture=m2b/full/$n.ppm 2b=m2c/reg2b-all/$n.ppm 2c=m2c/renderF/$n.ppm 2d-one=m2d/rF/$n-one.ppm $(four $n)"
  [ -f "m2d/rF/$n-close.ppm" ] && a="$a 2d-four-close=m2d/rF/$n-close.ppm"
  a="$a NEXT"
done
python3 "$L" "$E/overview-photos.jpg" "photographs at 2048: picture | 2b | 2c | 2d one procedure | 2d four procedures per picture (each quarter's simple procedure, seam smooth) | four with close-up layers" 300 0 $a
# 2. laid structures and motifs
a=""
for n in floor_tiles_06 metal_plate patterned_terracotta_tiling red_brick_03; do
  a="$a picture=m2b/full/$n.ppm 2b=m2c/reg2b-all/$n.ppm 2c=m2c/renderF/$n.ppm 2d-one=m2d/rF/$n-one.ppm $(four $n) NEXT"
done
for n in ornament_snowflakes ornament_poinsettias; do
  a="$a picture=m2b/full/$n.ppm 2b=m2c/reg2b-all/$n.ppm 2c=m2c/renderF/$n.ppm 2d-glyph-picked=m2d/rF/$n-glyph.ppm NEXT"
done
python3 "$L" "$E/overview-motifs.jpg" "laid structures and motifs at 2048: picture | 2b | 2c | 2d one procedure | 2d four (structures) or the glyph the eye picked (motifs)" 300 0 $a
# 3. per texture: whole and 1:1
for n in $PH floor_tiles_06 metal_plate patterned_terracotta_tiling red_brick_03; do
  python3 "$L" "$E/sheets/$n.jpg" "$n: whole (picture, 2c, 2d one, 2d four) | at 1:1 around the centre where the quarters meet" 380 0 \
    picture=m2b/full/$n.ppm 2c=m2c/renderF/$n.ppm 2d-one=m2d/rF/$n-one.ppm $(four $n) NEXT \
    1:1-picture=m2b/full/$n.ppm@$X 1:1-2c=m2c/renderF/$n.ppm@$X 1:1-2d-one=m2d/rF/$n-one.ppm@$X $(fourx $n) > /dev/null
done
for n in ornament_snowflakes ornament_poinsettias; do
  python3 "$L" "$E/sheets/$n.jpg" "$n: whole (picture, 2c, 2d with the glyph the eye picked) | one motif at 1:1" 380 0 \
    picture=m2b/full/$n.ppm 2c=m2c/renderF/$n.ppm 2d=m2d/rF/$n-glyph.ppm NEXT \
    1:1-picture=m2b/full/$n.ppm@0,600,700 1:1-2c=m2c/renderF/$n.ppm@0,600,700 1:1-2d=m2d/rF/$n-glyph.ppm@0,600,700 > /dev/null
done
# 4. how the four meet: the cross at 1:1, every seam
a=""
for n in plaster_grey_04 rock_05 rust_coarse_01 rusty_metal_02; do
  a="$a picture=m2b/full/$n.ppm@$X cut=m2d/rF/$n-simple-cut.ppm@$X mix=m2d/rF/$n-simple-mix.ppm@$X keep=m2d/rF/$n-simple-keep.ppm@$X smooth=m2d/rF/$n-simple.ppm@$X NEXT"
done
python3 "$L" "$E/four-procedures-the-cross.jpg" "where the four quarters meet, 512 pixels at 1:1 around the centre: picture | seam cut | mix | keep (Heitz and Neyret) | smooth (the default) - band 0.03 of the picture each side" 380 0 $a
# 5. the trap of shared seeds: four quarters drawing one noise instance (first run) against their own seeds
python3 "$L" "$E/four-procedures-own-seeds.jpg" "four quarters with one seed (a 2 by 2 repetition at a glance) | each quarter with its own seeds" 380 0 \
  plaster-shared=m2d/qr/plaster_grey_04-simple-whole-smooth-0.03.ppm plaster-own=m2d/rF/plaster_grey_04-simple.ppm \
  rust-shared=m2d/qr/rust_coarse_01-simple-whole-smooth-0.03.ppm rust-own=m2d/rF/rust_coarse_01-simple.ppm
# 6. Daniel's verdicts, one sheet each
python3 "$L" "$E/floor-tiles-joints.jpg" "floor tiles: \"the tile joints are gigantic, on the original they are very thin lines\" - at 1:1, and 192 pixels around a crossing enlarged" 380 0 \
  picture=m2b/full/floor_tiles_06.ppm@$X 2c=m2c/renderF/floor_tiles_06.ppm@$X 2d=m2d/rF/floor_tiles_06-one.ppm@$X NEXT \
  picture=m2b/full/floor_tiles_06.ppm@930,930,192 2c=m2c/renderF/floor_tiles_06.ppm@930,930,192 2d=m2d/rF/floor_tiles_06-one.ppm@930,930,192
python3 "$L" "$E/metal-plate-seeds-apart.jpg" "metal plate: \"shift the two seeds in space, they are forming a line\" - whole, then at 1:1" 380 0 \
  picture=m2b/full/metal_plate.ppm 2c=m2c/renderF/metal_plate.ppm 2d=m2d/rF/metal_plate-one.ppm NEXT \
  picture=m2b/full/metal_plate.ppm@$X 2c=m2c/renderF/metal_plate.ppm@$X 2d=m2d/rF/metal_plate-one.ppm@$X
python3 "$L" "$E/terracotta-framed.jpg" "terracotta: \"one tiny centralized square with surrounding trapezoids\" - whole, then at 1:1" 380 0 \
  picture=m2b/full/patterned_terracotta_tiling.ppm 2c=m2c/renderF/patterned_terracotta_tiling.ppm 2d=m2d/rF/patterned_terracotta_tiling-one.ppm NEXT \
  picture=m2b/full/patterned_terracotta_tiling.ppm@$X 2c=m2c/renderF/patterned_terracotta_tiling.ppm@$X 2d=m2d/rF/patterned_terracotta_tiling-one.ppm@$X
a="picture=m2b/full/red_brick_03.ppm@$X 2c-6-operators=m2c/renderF/red_brick_03.r02-c.ppm"
for r in m2d/rF/red_brick_03.r0*.ppm; do b=$(basename "$r" .ppm); a="$a 2d-${b#red_brick_03.}=$r@$X"; done
python3 "$L" "$E/bricks-rungs.jpg" "bricks at 1:1: picture | 2c's rung of 6 operators (the one Daniel called almost perfect) | 2d's rungs (r00 structure with the joints read at 1:1; r01 the hollow's light; r02 chips and grain; r03 mortar colours; r04 specks; r05 pits; r06 Tints)" 300 0 $a
python3 "$L" "$E/rusted-metal.jpg" "rusted metal: picture | 2c's 5 and 7 operator rungs | 2d one procedure (softer marks) | four simple (5 operators a quarter) | four with spots asked for (7 a quarter) - whole, then 1:1" 300 0 \
  picture=m2b/full/rusty_metal_02.ppm 2c-5=m2c/renderF/rusty_metal_02.r01-w.ppm 2c-7=m2c/renderF/rusty_metal_02.r02-w.ppm 2d-one=m2d/rF/rusty_metal_02-one.ppm 2d-four-5=m2d/rF/rusty_metal_02-simple.ppm 2d-four-7=m2d/rF/rusty_metal_02-close.ppm NEXT \
  picture=m2b/full/rusty_metal_02.ppm@$X 2c-5=m2c/renderF/rusty_metal_02.r01-c.ppm 2c-7=m2c/renderF/rusty_metal_02.r02-c.ppm 2d-one=m2d/rF/rusty_metal_02-one.ppm@$X 2d-four-5=m2d/rF/rusty_metal_02-simple.ppm@$X 2d-four-7=m2d/rF/rusty_metal_02-close.ppm@$X
echo sheets done
