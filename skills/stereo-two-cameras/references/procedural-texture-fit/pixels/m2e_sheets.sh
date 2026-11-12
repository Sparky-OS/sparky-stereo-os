#!/bin/sh
# The sheets of milestone 2e (Daniel's verdicts on 2d's sheets), from the renders in SCRATCH/m2e:
# m2e_sheets.sh SCRATCH EVIDENCE   (each sheet looked at before a word is written about it)
set -eu
S=$1; E=$2
L=$(cd "$(dirname "$0")" && pwd)/m2d_look.py
R=$(cd "$(dirname "$0")" && pwd)/m2e_relief.py
mkdir -p "$E/sheets"
cd "$S"
X=768,768,512
# 1. bricks: the three versions Daniel named, and the relief in the same order
for f in r01 r02 bricks-h bricks-a50 bricks-a75; do python3 "$R" m2e/st/$f-h.pgm m2e/st/$f-rl.ppm lit; done
python3 "$L" "$E/bricks-three-versions.jpg" "bricks at 1:1: picture | 2d-r01 as is | 2d-r02 as is | r02 over r01 (r02's faces over, r01's straight line in its chips and joints: the default) | r02 over r01 at alpha 0.5 | at 0.75 - then each one's relief, lit" 300 0 \
  picture=m2b/full/red_brick_03.ppm@$X 2d-r01=m2e/st/r01.ppm@$X 2d-r02=m2e/st/r02.ppm@$X r02-over-r01=m2e/st/bricks-h.ppm@$X alpha-0.5=m2e/st/bricks-a50.ppm@$X alpha-0.75=m2e/st/bricks-a75.ppm@$X NEXT \
  picture=m2b/full/red_brick_03.ppm@$X relief-r01=m2e/st/r01-rl.ppm@$X relief-r02=m2e/st/r02-rl.ppm@$X relief-r02-over-r01=m2e/st/bricks-h-rl.ppm@$X relief-0.5=m2e/st/bricks-a50-rl.ppm@$X relief-0.75=m2e/st/bricks-a75-rl.ppm@$X
# 2. rusted metal: 2d-four-5 under, 2d-one and 2d-four-7 over, 2c-7's spots over at a low alpha
python3 "$L" "$E/rusted-metal-laid.jpg" "rusted metal: picture | 2d-four-5 (underneath) | s1: one and four-7 over in thirds, 2c-7 at alpha 0.15 | s3: the same, 2c-7's spots only (its dark) at 0.5 | s5: one and four-7 laid where they are dark (their marks), 2c-7's spots at 0.5: the default | s6: the same at 0.6 - whole, then 1:1" 300 0 \
  picture=m2b/full/rusty_metal_02.ppm 2d-four-5=m2d/rF/rusty_metal_02-simple.ppm s1=m2e/st/rm-s1.ppm s3=m2e/st/rm-s3.ppm s5=m2e/st/rm-s5.ppm s6=m2e/st/rm-s6.ppm NEXT \
  picture=m2b/full/rusty_metal_02.ppm@$X 2d-four-5=m2d/rF/rusty_metal_02-simple.ppm@$X s1=m2e/st/rm-s1.ppm@$X s3=m2e/st/rm-s3.ppm@$X s5=m2e/st/rm-s5.ppm@$X s6=m2e/st/rm-s6.ppm@$X
# 3. metal plate: rust colours mixed in, the bevel, the relief with its shadow
python3 "$L" "$E/metal-plate.jpg" "metal plate: picture | 2d | 2d's pattern over the plate's surface colours (fitted without structure, spots asked for) where its lozenges stand | the same with the bevel's light: the default | relief, light and cast shadow, the surface over at 0.4 | the bevel, the surface over at 0.4 - whole, then 1:1" 300 0 \
  picture=m2b/full/metal_plate.ppm 2d=m2d/rF/metal_plate-one.ppm colours=m2e/st/plate-A.ppm bevel=m2e/st/plate-B.ppm shadow=m2e/st/plate-C.ppm bevel-0.4=m2e/st/plate-D.ppm NEXT \
  picture=m2b/full/metal_plate.ppm@$X 2d=m2d/rF/metal_plate-one.ppm@$X colours=m2e/st/plate-A.ppm@$X bevel=m2e/st/plate-B.ppm@$X shadow=m2e/st/plate-C.ppm@$X bevel-0.4=m2e/st/plate-D.ppm@$X
# 4. terracotta: very fine grain, the stain of the upper right corner
python3 "$L" "$E/terracotta.jpg" "terracotta: the upper right corner at 1:1 (picture | 2d | 2e the finest grain and each piece's stain | 2e with the second colour asked too: the default, by the second judge), then the whole" 300 0 \
  picture=m2b/full/patterned_terracotta_tiling.ppm@1536,0,512 2d=m2d/rF/patterned_terracotta_tiling-one.ppm@1536,0,512 2e-fine=m2e/fit/terra-fine.ppm@1536,0,512 2e-fine-second=m2e/fit/terra-stain.ppm@1536,0,512 NEXT \
  picture=m2b/full/patterned_terracotta_tiling.ppm 2d=m2d/rF/patterned_terracotta_tiling-one.ppm 2e-fine=m2e/fit/terra-fine.ppm 2e-fine-second=m2e/fit/terra-stain.ppm
# 5. floor tiles: the thin adjustment, four internal tiles
python3 "$L" "$E/floor-tiles.jpg" "floor tiles: picture | 2d | 2e one (the joint's darkest line, its warp and the pieces' jitter under a quarter of it, edges filtered: the default) | 2e four internal tiles on the whole's structure - whole, 1:1 at the centre, 192 pixels around a crossing" 300 0 \
  picture=m2b/full/floor_tiles_06.ppm 2d=m2d/rF/floor_tiles_06-one.ppm 2e-one=m2e/fit/floor-dark.ppm 2e-four=m2e/fitq/floor-four.ppm NEXT \
  picture=m2b/full/floor_tiles_06.ppm@$X 2d=m2d/rF/floor_tiles_06-one.ppm@$X 2e-one=m2e/fit/floor-dark.ppm@$X 2e-four=m2e/fitq/floor-four.ppm@$X NEXT \
  picture=m2b/full/floor_tiles_06.ppm@930,930,192 2d=m2d/rF/floor_tiles_06-one.ppm@930,930,192 2e-one=m2e/fit/floor-dark.ppm@930,930,192 2e-four=m2e/fitq/floor-four.ppm@930,930,192
# 6. more tiles: four (every band read), eight both ways, sixteen; whole and 1:1
a=""; b=""
for n in rock_05 concrete_floor_02 coast_sand_rocks_02 bark_brown_02 rusty_metal_02; do
  a="$a picture=m2b/full/$n.ppm 2d-four=m2d/rF/$n-simple.ppm 2e-four=m2e/grid/$n-2x2.ppm eight-4x2=m2e/grid/$n-4x2.ppm eight-2x4=m2e/grid/$n-2x4.ppm sixteen=m2e/grid/$n-4x4.ppm NEXT"
  b="$b picture=m2b/full/$n.ppm@$X 2d-four=m2d/rF/$n-simple.ppm@$X 2e-four=m2e/grid/$n-2x2.ppm@$X eight-4x2=m2e/grid/$n-4x2.ppm@$X eight-2x4=m2e/grid/$n-2x4.ppm@$X sixteen=m2e/grid/$n-4x4.ppm@$X NEXT"
done
python3 "$L" "$E/more-tiles-whole.jpg" "the five where four failed, at 2048: picture | 2d four (seven bands read) | 2e four (every band read) | eight, 4 across by 2 down | eight, 2 by 4 | sixteen" 240 0 $a
python3 "$L" "$E/more-tiles-1to1.jpg" "the same at 1:1 around the centre" 240 0 $b
# 7. how eight tiles lie on a square picture: a tall tile and a wide one with their mirror images, as the fitter reads them
python3 "$L" "$E/eight-tiles-laid.jpg" "eight tiles on a square picture: a tall tile of 4 by 2 (512 by 1024 of the 2048 picture) and a wide tile of 2 by 4, each laid with its mirror image into a square the fitter reads; the drawing shows only the tile's part" 300 0 \
  4x2-tile-and-mirror=m2e/tiles/rusty_metal_02/4x2/t0-1.full.ppm 2x4-tile-and-mirror=m2e/tiles/rusty_metal_02/2x4/t1-0.full.ppm 4x2-drawn=m2e/grid/rusty_metal_02-4x2.ppm 2x4-drawn=m2e/grid/rusty_metal_02-2x4.ppm
# 8. snowflakes and poinsettias
python3 "$L" "$E/snowflakes.jpg" "snowflakes: picture | 2c (Symbola) | 2d (an outlined hexagram) | 2e tabler-icons snowflake (MIT; the seed reading's choice) | 2e bootstrap-icons snow3 (MIT; the default, by the eye and the second judge) | 2e two glyphs: snow3 with 2d's hexagram laid over it - whole, then one motif at 1:1" 300 0 \
  picture=m2b/full/ornament_snowflakes.ppm 2c=m2c/renderF/ornament_snowflakes.ppm 2d=m2d/rF/ornament_snowflakes-glyph.ppm 2e-tabler=m2e/fit/snow-tabler.ppm 2e-bootstrap=m2e/fit/snow-bootstrap.ppm 2e-two=m2e/st/snow-two.ppm NEXT \
  picture=m2b/full/ornament_snowflakes.ppm@0,600,700 2c=m2c/renderF/ornament_snowflakes.ppm@0,600,700 2d=m2d/rF/ornament_snowflakes-glyph.ppm@0,600,700 2e-tabler=m2e/fit/snow-tabler.ppm@0,600,700 2e-bootstrap=m2e/fit/snow-bootstrap.ppm@0,600,700 2e-two=m2e/st/snow-two.ppm@0,600,700
cp m2e/look-glyph.jpg "$E/poinsettia-themed-fonts-pixels.jpg"
cp m2e/look-glyph-names-poin.jpg "$E/poinsettia-themed-fonts-named.jpg"
cp m2e/look-glyph-snow.jpg "$E/snowflake-themed-fonts-pixels.jpg"
cp m2e/look-glyph-names-snow.jpg "$E/snowflake-themed-fonts-named.jpg"
cp m2e/look-snow2.jpg "$E/snowflake-two-glyphs.jpg"
python3 -c "from PIL import Image; Image.open('m2e/carr-chart.png').convert('RGB').save('$E/carr-xmas-dingbats-chart.jpg', quality=88)"
echo sheets done
# 9. the overviews and each texture's own sheet: picture, 2b, 2c, 2d, 2e (each one's default), whole and at 1:1
two() { case $1 in
  bark_brown_02|coast_sand_rocks_02|concrete_floor_02|rock_05) echo m2e/grid/$1-2x2.ppm ;;
  rusty_metal_02) echo m2e/st/rm-s5.ppm ;; red_brick_03) echo m2e/st/bricks-h.ppm ;; floor_tiles_06) echo m2e/fit/floor-dark.ppm ;;
  metal_plate) echo m2e/st/plate-B.ppm ;; patterned_terracotta_tiling) echo m2e/fit/terra-stain.ppm ;; ornament_snowflakes) echo m2e/fit/snow-bootstrap.ppm ;;
  *) echo "" ;; esac; }
twod() { case $1 in plaster_grey_04|rust_coarse_01) echo m2d/rF/$1-simple.ppm ;; ornament_*) echo m2d/rF/$1-glyph.ppm ;; *) echo m2d/rF/$1-one.ppm ;; esac; }
a=""
for n in bark_brown_02 coast_sand_rocks_02 concrete_floor_02 plaster_grey_04 rock_05 rust_coarse_01 rusty_metal_02; do
  e=$(two $n); a="$a picture=m2b/full/$n.ppm 2b=m2c/reg2b-all/$n.ppm 2c=m2c/renderF/$n.ppm 2d=$(twod $n)"; [ -n "$e" ] && a="$a 2e=$e"; a="$a NEXT"
done
python3 "$L" "$E/overview-photos.jpg" "photographs at 2048: picture | 2b | 2c | 2d (the eye's default) | 2e (the default; none where this milestone did not touch it)" 300 0 $a
a=""
for n in floor_tiles_06 metal_plate patterned_terracotta_tiling red_brick_03 ornament_snowflakes ornament_poinsettias; do
  e=$(two $n); a="$a picture=m2b/full/$n.ppm 2b=m2c/reg2b-all/$n.ppm 2c=m2c/renderF/$n.ppm 2d=$(twod $n)"; [ -n "$e" ] && a="$a 2e=$e"; a="$a NEXT"
done
python3 "$L" "$E/overview-motifs.jpg" "laid structures and motifs at 2048: picture | 2b | 2c | 2d | 2e (the default; none for the poinsettias: no font draws one)" 300 0 $a
for n in bark_brown_02 coast_sand_rocks_02 concrete_floor_02 rock_05 rusty_metal_02 floor_tiles_06 metal_plate patterned_terracotta_tiling red_brick_03; do
  e=$(two $n)
  python3 "$L" "$E/sheets/$n.jpg" "$n: whole (picture, 2b, 2c, 2d, 2e) | at 1:1 around the centre" 380 0 \
    picture=m2b/full/$n.ppm 2b=m2c/reg2b-all/$n.ppm 2c=m2c/renderF/$n.ppm 2d=$(twod $n) 2e=$e NEXT \
    1:1-picture=m2b/full/$n.ppm@$X 1:1-2b=m2c/reg2b-all/$n.ppm@$X 1:1-2c=m2c/renderF/$n.ppm@$X 1:1-2d=$(twod $n)@$X 1:1-2e=$e@$X > /dev/null
done
echo overview done
