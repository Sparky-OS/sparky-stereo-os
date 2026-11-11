# A procedure fitted to a bitmap, and what is left for the image

Written on 2026-11-10 (ORDER 473v), as a study for [Dynamic Procedural Foveated Rendering](../../../docs/dynamic-procedural-foveated-rendering.md), which renders procedures first and the image last and assumes the procedure exists.
Most assets are bitmaps, so this asks the other direction: how much of a bitmap a program can turn into a small procedure by itself, and how many bytes the image must still carry.
It is a measurement method with its numbers from two rounds (one procedure for the whole picture, then tiled procedures as a ladder), not a renderer and not a DPFR implementation.

## The method

1. Fit small procedures to the picture: a flat colour as the floor, a noise operator with a colour gradient, and a structure layer (here a sum of the K strongest cosine waves).
2. Draw each procedure at the picture's size with the real operator, never with the fit's own model alone, and require the two to agree within one level.
3. Measure three things: the bytes of the procedure; how close the procedure alone is (PSNR at every size from the full picture down to 8 pixels, the gap between the power spectra in octave bands, the gap between the histograms); and the bytes of the remainder, the image that restores the picture when added to the procedure, lossless and at a matched lossy quality.
4. Always include controls whose answer is known: a picture made by the operator itself (the fit must return its parameters and an empty remainder), a picture of random bytes (nothing may be found), a picture of known waves (they must come back).
5. Always include a small picture of the same bytes, enlarged, beside the procedure. It is the honest comparison for "a small procedure gives the coarse picture".

## Recipe

The scripts are in [`procedural-texture-fit/`](procedural-texture-fit/); they need Docker, a local image that has g++, and Python with NumPy, SciPy and Pillow.

```sh
git clone --depth 1 https://github.com/farbrausch/fr_public.git WORK/fr_public
# put 2048 x 2048 pictures as WORK/tex/NAME.png (the first run used six CC0 diffuse maps from Poly Haven)
KTG_IMAGE=your-image-with-g++ sh procedural-texture-fit/run.sh WORK WORK/out
python3 procedural-texture-fit/tables.py WORK/out WORK/out/sheet.png > WORK/out/tables.md
python3 procedural-texture-fit/chain_sizes.py WORK/tex/*.png   # the fair baseline: the lower-resolution copies
```

Expect: `ktgtool` built from OpenKTG's unchanged `gentexture.cpp` (public domain, Fabian "ryg" Giesen, 2007); three control pictures; one JSON file per picture; and 16 lines starting with PASS from `check_controls.py`, which exits 1 on any FAIL.
Nine pictures take about 13 minutes, three at a time.
OpenKTG's code runs only inside the container (`--network none`, `--ulimit core=0`).

The noise fit, in OpenKTG's own terms (`Noise(grad, freqX, freqY, oct, fadeoff, seed, mode)`):
- one octave of the operator at base frequency f is the first octave at frequency f + i, so the driver dumps single octaves once and the fit combines them for any `oct` and `fadeoff`;
- the kind of noise, `freq`, `oct` and `fadeoff` are chosen by the energy in eight octave bands of the rank-equalised picture (its main colour axis) against the rank-equalised noise;
- all 4,096 seeds are scanned at 128 x 128; a correlation above 0.5 means the picture is that noise field, and then `oct`, `fadeoff` and the gradient are solved against the pixels (linear least squares for the 16 stops);
- otherwise each gradient stop takes the mean colour the picture has at the same rank.

## What the first run measured

Six pictures (two noise-like, two regular, two photographic), 2048 x 2048, and three controls.

- A picture that is an OpenKTG procedure came back exactly from 57 bytes (1,614,136 bytes as a PNG), with an empty remainder; best seed correlation 0.990, second best 0.464.
- On the six real pictures no procedure made a difference image (the remainder) smaller: procedure plus remainder changed the total by 0.0 to +7.6 % lossless (PNG) and +0.1 to +29.5 % as JPEG at a matched PSNR.
  This compares procedure plus picture with the picture alone, which is not DPFR's comparison; see the next section.
- OpenKTG's noise (57 bytes) brought the power spectrum within 1.1 to 3.8 dB and the histogram within 1.2 to 7.5 levels of the picture, and was 1.3 to 2.4 dB worse than a flat colour pixel by pixel.
- 64 waves (835 bytes) showed the checkerboard and the brick courses (28.3 and 21.1 dB against 20.6 and 18.9 for a flat colour) and beat a 32 pixel picture of the same bytes only on the brick.
- A fitted procedure of a few kilobytes stood for the picture up to about 64 pixels wide (32.6 to 40.0 dB at 32 pixels with 64 waves), and for nothing above that pixel by pixel (23.1 to 33.0 dB at 512 pixels with 1,024 waves).

## The fair baseline: what a traditional asset ships

Daniel's correction of the first reading (2026-11-10): a traditional asset carries the picture in several resolutions, which is where the procedure is meant to act, so procedures plus picture against the picture alone is not a fair comparison.
A traditional asset ships the picture and its lower-resolution copies (a mip chain, or separate versions per device), and streams them as a tiled pyramid.
The design it is compared with (Daniel, the same day) is tiled procedures informed by the high-resolution texture, forming a level-of-detail ladder that the device's power sets, chosen per tile together with foveation, with the high-resolution texture as the last layer.
"One image plus a small procedure" was an oversimplification and is not the design; the numbers of the single procedure below are kept as what they are, the first round's.
Measured on the same six pictures with [`chain_sizes.py`](procedural-texture-fit/chain_sizes.py) (box-averaged levels, JPEG quality 90):

- The lower-resolution copies down to 1 pixel added 31.1 to 41.4 % to the picture's bytes (29.1 to 38.6 % for two device copies at 1024 and 512; 31.0 to 38.1 % lossless as PNG).
- First round, one procedure for the whole picture (57 bytes of OpenKTG noise to 13,315 bytes of 1,024 waves): with the picture, 24 to 29 % smaller than the picture with its copies, and pixel-exact only up to about 64 pixels.
- Second round, the tiled ladder (next section): with the picture, 22.6 to 28.4 % smaller when the ladder stops at 64 pixel tiles, 15.5 to 24.3 % smaller at 32, between 13.1 % smaller and 24.3 % larger at 16, and 39.5 to 193.7 % larger at 8.

No difference image in either round: the asset is the procedures plus the picture.
Not measured: GPU texture formats with their own chains (KTX2, BCn), AVIF and JPEG XL, and how the change from procedures to picture looks.

## The tiled ladder: procedures informed by the tile's own pixels (ORDER 473w)

These are code metrics of a three-term fitter (gradient, cells, seed-chosen noise). Daniel's reading of them, 10 November 2026: the work had not started where it should, from .kkrieger's own tooling and its way of making textures, and the comparison is a visual matter, which a vision-capable model judges better than code metrics do. They stay as that round's record; the artist's way below is the round that answers him.

The direction of werkkzeug3 and .kkrieger run backwards: there operators made the texture; here the texture yields the operators and their parameters, tile by tile.

### Two fitters

1. **Recognition** ([`recognise.py`](procedural-texture-fit/recognise.py)): each 256 pixel tile is tried as one OpenKTG operator (a flat colour, `Cells`, a `GlowRect` over a flat colour, `Noise` with a two-colour gradient), the answer is drawn again by the real operator and compared pixel by pixel.
2. **The ladder** ([`tiled.py`](procedural-texture-fit/tiled.py)): seven rungs with tiles of 512 down to 8 pixels. Each rung adds per tile, fitted to what the rungs below left: a gradient (one colour per tile corner, shared, 3 bytes), `Cells` with four sites (20 bytes, kept only where they remove 15 % of the tile's error), and OpenKTG noise whose seed is the one of all 4,096 that follows the tile's pixels best, with one amplitude per channel (8 bytes). A finer rung refines the coarser ones, so any rung can be the last.

### Recipe

```sh
KTG_IMAGE=your-image-with-g++ python3 procedural-texture-fit/make_tiled_controls.py WORK
KTG_IMAGE=... python3 procedural-texture-fit/recognise.py WORK WORK/rec control-tiled-ktg=WORK/tex2/control-tiled-ktg.png control-tiled-mixed=WORK/tex2/control-tiled-mixed.png
KTG_IMAGE=... python3 procedural-texture-fit/recognise.py WORK WORK/rec --gate NAME=WORK/tex/NAME.png ...
KTG_IMAGE=... python3 procedural-texture-fit/tiled.py WORK WORK/lad NAME=WORK/tex/NAME.png ...            # hard tiles
KTG_IMAGE=... python3 procedural-texture-fit/tiled.py WORK WORK/lad --window NAME=WORK/tex/NAME.png ...   # faded borders
python3 procedural-texture-fit/foveate.py WORK/lad bench.json NAME=WORK/tex/NAME.png ...                  # one gaze point, both schemes
python3 procedural-texture-fit/check_tiled.py WORK WORK/rec WORK/lad                                       # exits 1 on any FAIL
python3 procedural-texture-fit/tables_tiled.py WORK/lad bench.json
```

`bench.json` holds the nanoseconds per pixel that `ktgtool bench` prints (keys `noise_gradient_ns_per_pixel_octave`, `noise_value_ns_per_pixel_octave`, `cells_4_ns_per_pixel`, `bilinear_ns_per_pixel`); take medians of several runs.
Expect 27 lines starting with PASS for six pictures, one random-bytes control and the two tiled controls.
Seven pictures take about an hour per ladder variant on a busy machine: the 512 pixel rung alone is 20 minutes, because the fields of 4,096 seeds are drawn at that size for four candidate materials.

### What it measured (six pictures, 2048 x 2048)

- **Controls.** 64 tiled `Noise` procedures came back pixel for pixel in 533 bytes. In a picture of mixed operators every tile's operator was named; every `Noise`, `GlowRect` and flat tile came back exactly; 12 of 16 `Cells` tiles did, the other 4 at 20.7 to 27.0 dB. No real picture was taken for a procedure.
- **The ladder gets closer as tiles shrink:** 18.6 to 27.1 dB at 512 pixel tiles (185 to 505 bytes), 19.7 to 31.4 dB at 32 (64 to 128 KB), 22.8 to 36.9 dB at 8 (1.81 to 2.37 MB); 3.0 to 12.1 dB closer at 32 pixel tiles than one procedure for the whole picture.
- **A tile's procedure stops being smaller than the tile's own picture at 8 pixels** (28 to 36 bytes of procedure against 12 to 33 bytes of JPEG per 8 x 8 tile).
- **Byte for byte a small JPEG copy is closer** than the ladder at every rung, by 0.2 to 5.3 dB.
- **As levels of detail:** the ladder to 32 pixel tiles is 34.0 to 45.7 dB from the picture at 128 pixels; to 8 pixel tiles, 35.8 to 49.6 dB at 512 pixels. Two octaves instead of all cost at most 0.15 dB down to 128 pixel tiles and 0.7 to 4.0 dB at 8.
- **Cost** with OpenKTG's reference code on one CPU thread: 25 ns per pixel and octave of gradient noise, 15 of value noise, 24 for four cells, 1.5 for a bilinear blend; the whole ladder for a 2048 x 2048 picture, 2.3 to 3.0 seconds. No GPU was measured.
- **Seams:** hard tiles show a grid (the jump at borders is 1.6 to 69 times the jump elsewhere); fading each tile's cells and noise to zero at its border with `GlowRect`'s falloff brings that to 0.2 to 1.1 at no cost in PSNR, and leaves a soft grid.
- **One gaze point** (Guenter and others' acuity model, 48 pixels per degree), the ladder against a bitmap pyramid of 128 pixel JPEG pages for the same rings: 19 to 35 KB against 75 to 147 KB on the wire, 64,215 against 278,528 texels, 19 to 28 ms of evaluation against 4 to 13 ms of JPEG decoding, and 26 to 39 dB against 37 to 44 dB from the level each ring resolves. The bitmap scheme costs more bytes and memory; it is closer and, against this reference code, faster.

### Traps of the tiled round

- Symptom: every tile's seed is right and the picture still comes back at 34 dB.
  Cause: octaves and fadeoff were settled with the seed a 32 pixel copy of the first tile chose, and that seed was a wrong one (correlation 0.56 only).
  Fix: take only the kind and the frequency from the small copy, scan the seed again on the tile's own pixels, then settle octaves and fadeoff.
  Found by: comparing the returned operator lines with the ones the control was made with.
- Symptom: a real picture passes the "is it a procedure" gate (seed correlation 0.64 on the small copy, above the true control's 0.56).
  Fix: the gate is the exact redraw by the real operator, never the correlation.
- Symptom: a `Noise` tile comes back one level off in a few pixels.
  Cause: a least-squares colour rounds to a neighbour when the noise barely moves that channel.
  Fix: walk the six colour values one level at a time, drawing each candidate with the real operator, until nothing improves. Two colour sets can draw the same pixels, so compare pictures, not parameters.
- Symptom: `Cells` sites found by moving one site at a time stop with thousands of wrong pixels although every site is within three grid steps of the truth.
  Fix: after trying every grid position per site, move pairs of sites together. Four of sixteen tiles still fail; the exact route (each boundary is the bisector of its two sites) was not built.
- Symptom: tiles show as a grid.
  Cause: each tile's cells and noise are periodic inside the tile and unrelated to the neighbour's.
  Fix: fade each tile's terms to zero at the border with `GlowRect`'s falloff and fit with the fade applied; keep the gradient shared at tile corners.
- Symptom: two ladders and a recogniser run at once, and the timing of the operators doubles from run to run.
  Fix: time the operators (`ktgtool bench`) when nothing else of yours runs, and take the median of five.

## The artist's way: werkkzeug3's own graphs, a vision model as the artist, the eye as the judge (ORDER 473x)

### How .kkrieger made its textures

The project file of the game is in `fr_public` (`werkkzeug3/data/kkrieger.k`, 217 pages, 29,347 operators).
[`werkkzeug/kdoc.py`](procedural-texture-fit/werkkzeug/kdoc.py) reads it, following `WerkDoc::Read`; [`kgraph.py`](procedural-texture-fit/werkkzeug/kgraph.py) rebuilds each texture's graph the way the editor does (an operator takes the operators in the row right above it that overlap it sideways, left to right; `Load` takes a stored operator by name) and prints it in plain words.
854 named bitmaps can be drawn; a graph has 16 operators and 396 bytes of class and parameter words at the median, 173 operators and 3,793 bytes at most.
The operators used most: `HSCB` (hue, saturation, contrast, brightness), `Merge`, `Color`, `Transform`, `Perlin`, `Blur`, `GlowRect`, `Range`, `Flat`, `TransformMul`, `Normals`, `Distort`, `Twirl`, `Bump`, `Cell`, `Mask`, `Gradient`.

The artist's idioms, read from the graphs:
- **A colour layer:** `Perlin` in black and white, `Range` to map it to two colours of the material, `HSCB` to tune it. Several noises at different frequencies are multiplied or added.
- **A shape, repeated:** one soft rectangle (`Flat`, then `GlowRect`), repeated with `TransformMul` or by a `Transform` that scales it down so it tiles. .kkrieger's brick walls and tiles are made this way; the `Bricks` operator exists and the game does not use it.
- **Irregular edges:** `Distort` the shape by a noise.
- **Relief:** the shape and noises as a height, `Normals`, then `Bump` lights the colour layer with it; a brightened copy of the shape is multiplied in for the joints.
- **Two materials on one surface:** `Mask` with a noise as the mask (metal and rust, wood and knots).
- **A mask from a noise:** `Perlin`'s own amplify and gamma (amplify 3, gamma 2 gives patches over about 40 % of the picture).

### Drawing them with Farbrausch's own operator code

werkkzeug3's `genbitmap.cpp` is Visual C++ with x86 MMX assembly and does not compile with g++.
werkkzeug4 carries Farbrausch's own portable C++ version of the same generator (`altona_wz4/wz4/wz4frlib/wz3_bitmap_code.cpp`, BSD).
[`build.sh`](procedural-texture-fit/werkkzeug/build.sh) builds [`wzrender`](procedural-texture-fit/werkkzeug/wzrender.cpp) from an unchanged clone: `patch_wz3.py` removes seven whole functions that need fonts, image files or the vector operator, and one line of `Paste` (a test that belongs to the editor's cache); no other line of a texture operator is changed; `shim/` stands in for the few altona types the file uses, with altona's random generators copied so the operators draw what they draw there.
wzrender's calls follow werkkzeug3's `Bitmap_*` functions parameter for parameter.

```sh
KTG_IMAGE=your-image-with-g++ sh werkkzeug/build.sh FR_PUBLIC BUILD
PYTHONPATH=werkkzeug python3 werkkzeug/kgraph.py FR_PUBLIC/werkkzeug3/data/kkrieger.k              # the 854 names
PYTHONPATH=werkkzeug python3 werkkzeug/kgraph.py FR_PUBLIC/werkkzeug3/data/kkrieger.k t.wall.bricks.01 > g.txt   # a script for wzrender
```

Expect: `t.wall.bricks.01` (24 operators, 644 bytes), `0.fliesen_01` (36, 772), `0.wood.02` (35, 831), `t.bricks.02` (36, 784), `0.wood.crate01` (69, 1,773) and the others draw as a brick wall, stone tiles, wood, a stone wall and a crate, 512 x 512.
They are the game's graphs through werkkzeug4's code: the look is the game's; the random details (which cell is where) need not be, because werkkzeug4 uses other random generators than werkkzeug3. `Text` is passed through undrawn (it needs Windows fonts).

### The reverse direction, as an artist would do it

1. Cut a tile of the high-resolution texture (512 x 512 at full size).
2. A vision-capable model looks at the tile and types a graph in werkkzeug3's operators, in [`wzlang.py`](procedural-texture-fit/werkkzeug/wzlang.py)'s form: one operator per line, name, operator, inputs, values in werkkzeug3's own parameter order. Four typed graphs are in [`werkkzeug/examples/`](procedural-texture-fit/werkkzeug/examples/).
3. [`look.py`](procedural-texture-fit/werkkzeug/look.py) draws it with wzrender and puts it beside the tile at the same size.
4. The model looks at the sheet, says in words what matches and what is wrong, and revises the graph. Three to five rounds.
5. A second, cold vision model that has seen none of this judges the final sheet: what each side is, what matches, what is missing, the same surface at a glance, and close up.
6. The level of detail is the graph's detail: thinner versions of the final graph (fewer operators, fewer octaves, down to one flat colour) are drawn beside it and judged for the distance at which each still reads.
7. The next tile of the same picture starts from the same graph; only seeds and a few values change. The tiles are where the graph changes.

No code metric decides anything. The graph's bytes are written beside each sheet as a fact.

### What the first run found (the vision model's and the second judge's words are in the lane's evidence)

- **Known answers.** Two .kkrieger textures written from the picture alone came back in three rounds as the same surface at a glance for both judges: stone tiles in 12 operators and 296 bytes (the artist's own graph: 36 and 772), stained rusty metal in 9 and 237 (the artist's: 48 and 804). The typed tile graph used the artist's own idiom (one soft rectangle scaled to half) without having read it.
- **Six photographs, one 512 pixel tile each, 3 to 5 rounds:** concrete (9 operators, 221 bytes), plaster (6, 186), floor tiles (13, 337), red brick (7, 227, with werkkzeug3's `Bricks`), coast with moss and stone (8, 248): the same kind of surface at a glance, or nearly, for both judges; none the same surface close up. Tree bark (15, 427): refused by both; it came out as a drawing of bark.
- **What a typed graph gets:** the material's colours, grain, shares of light and dark, and a regular layout. **What it does not get:** things that are objects or events on the surface (stones, chips, a knot, the one orange brick, a crack) and deep relief with light and shadow.
- **Level of detail:** concrete still reads from afar at 108 bytes (4 operators), brick at 57 bytes (`Bricks` alone), the coast at 139 bytes; one or two operators below that are placeholders in the right colours.
- **A second tile** of the same picture needed the same graph with other seeds and one or two changed values.

### Traps of the artist's round

- Symptom: the first compile of werkkzeug3's own texture library stops in `_types.hpp` with `fclex`, `push`, `fldcw` not declared.
  Cause: inline x86 assembly in Visual C++ syntax, 29 blocks, with no C fallback for the merge, blur and filter cores.
  Fix: use werkkzeug4's `wz3_bitmap_code.cpp`, which has no assembly, with a small stand-in for altona's types; altona's own base does not compile with a current g++ either (its `new` macros collide with the standard headers).
  Found by: `grep -c __asm` over both trees.
- Symptom: `grep` finds nothing in files that plainly hold the text.
  Cause: the sources are ISO-8859 and grep takes them for binary.
  Fix: `grep -a`.
- Symptom: a mask hardened with `HSCB` (contrast 3 to 4) comes out nearly black, three rounds in a row.
  Cause: the contrast does not turn around mid-grey as assumed.
  Fix: make masks in `Perlin` itself with amplify and gamma, and look at the mask alone before using it.
  Found by: drawing five masks side by side.
- Symptom: a relief turns the picture into black and white hair, or plaster into sandpaper.
  Cause: `Normals` strength near 1 on a fine noise is ten times too much.
  Fix: 0.08 to 0.4 for a surface's tooth, and a `Bump` ambient colour close to the diffuse.
- Symptom: `Mask` puts the two layers the wrong way round.
  Fix: the first layer shows where the mask is white.
- Symptom: a speckle meant for the mortar lands on the bricks too.
  Cause: a layer added to the whole picture has no notion of the shape under it.
  Fix: mask it with the shape, as the artist's graphs do with a brightened copy of the joints.
- Symptom: the writer of the graph accepts its own result more easily than a cold reader does.
  Fix: always a second judge that has not seen the graph or the rounds; record both verdicts and where they differ.
- Symptom: the local vision model answers 404 and the cloud one 429.
  Fix: record the refusals word for word and use another independent model that can look at pictures; never invent a second opinion.

## Relief the artist's way, and stereo textures that only sink (ORDER 473y)

Daniel's request (10 November 2026): build the relief the traditional way, and make it a stereo texture whose depth is always sunk or at the surface's level, never in front of it, because a popped relief renders wrongly from some points of view; regular rendering shows the relief from one side, while stereo rendering gives it real sunk levels.

### The relief, as werkkzeug3's artists built it

The relief is one grey picture, the height, made of several shapes and noises multiplied together, and it is used three times.
`Merge a,b,c 2` multiplies the parts into the height `h`.
`Color h 1 #ffa0a0a0` lifts it, and a multiply over the colour darkens the hollows.
`Normals h 0.08 to 0.5` then `Bump colour,normals` lights it.
The parts that worked, per kind of surface (the graphs are in `procedural-texture-fit/werkkzeug/examples/relief-*.txt`):

- Bark: two `Cell` layers stretched along the trunk and bent by `Distort` for the furrows, a stretched `Perlin` for the plates, a fine `Perlin` for the fibre and a coarse one for the crust.
- Brick: the `Bricks` joints, a sparse `Perlin` with high gamma for the chips, a fine one for the grain; the lime specks are colour only.
- Plaster: a soft `Perlin` for the lumps and a very sparse one (gamma 9) for the pits.
- Stone tiles: the slabs' joints from thin `GlowRect` lines, a `Cell` crackle only inside the slate slabs through `Mask`.
- Wood for a panel: the game's wood (a stretched `Perlin`), two knots from `GlowRect`, the joint between planks as the only deep line.

```sh
KTG_IMAGE=image PYTHONPATH=werkkzeug python3 werkkzeug/relief_look.py BUILD TILE.png SHEET.jpg GRAPH.txt
# writes GRAPH.png (lit), GRAPH-height.png (the operator named h) and a sheet: tile | lit | height
```

### The height is also the depth: at the surface or behind it

White in the height is the surface and has zero parallax.
Black is the deepest point and lies behind it.
Nothing stands in front of the surface, so a tile's outline, a wall's corner and a panel's edge stay where the flat geometry puts them in both eyes.
A relief that stands in front must show its side past the outline, which a flat tile cannot draw: that is the popping Daniel names.
Relief mapping already works this way: Policarpo, Oliveira and Comba (2005) store depth from 0.0 at the surface to 1.0, and a ray enters the surface and is searched (linear steps, then a refinement) for the first point it meets; Tatarchuk (2006) does the same search with a height field below the polygon.
For stereo the search runs once per eye, with each eye's own ray, and the lit colour is the same in both eyes because the light is baked.

```sh
KTG_IMAGE=image PYTHONPATH=werkkzeug python3 werkkzeug/draw.py BUILD GRAPH.txt     # GRAPH.png, GRAPH-height.png, GRAPH-depth.png at the graph's own size
python3 werkkzeug/stereo_texture.py GRAPH.png GRAPH-depth.png OUT.pns --sunk 10 --pop 3 --black 25 --surface 128 --white 165
python3 werkkzeug/pns.py OUT.pns                     # chunk order, every CRC, the mode, the padding, and that it decodes; exit 1 on a fault
```

The first run stated its numbers for 1920 pixels on a screen 1.21 m wide seen from 2.5 m with eyes 65 mm apart: 10 pixels of parallax are 6.3 mm on the screen and about 0.27 m behind it.
The script tests itself first: a mark on a wide flat floor at the black level, the surface level and the white level must come out with exactly the sunk, zero and popped parallax.

### The size, the mark, the range and the edges (ORDER 473z, after Daniel saw the pictures on his 3D TV)

Daniel, after seeing the pictures on his 3D TV (10 November 2026): sunk stereo textures work, and so did the subtly popped brick, so a texture may also pop by a few pixels; the coast, bark, tiles and plaster can take a little more separation, keeping the edge-cut rule so no strip shows at the edges.

- **The size.** A procedural texture is drawn at the size it is wanted, by setting the size in the graph's generators (`10 10` is 1024 x 1024). The 2D picture and each eye of the 3D picture have that one size. Nothing is resized afterwards: a program never stretches or squeezes an eye, and the compositor scales once at the output. The first pictures had enlarged a 512 tile to 1024 inside a 1920 x 1080 frame, and Daniel asked why the sizes differed.
- **The mark.** Every stereo picture is written as a `.pns`: full side by side, left eye first, with the PNG `sTER` chunk (mode 1) before the first `IDAT`, and the specification's padding between the views when the width is not a multiple of eight. `pns.py` writes it and reads it back. An unmarked side by side PNG is shown flat by the viewers. No red-cyan picture is made: the person has a 3D screen.
- **The range.** Three levels of the height, set as an artist sets levels: the black level is the deepest point, the surface level has no parallax, the white level is the highest point. Mostly sunk, and a few pixels in front at most, inside the desktop's default limits (10 sunk, 4 popped at 1920). The first proposal: bark 10 and 3, coast ground 10 and 4 (the stones stand up), stone tiles 10 and 2, plaster 8 and 2; the brick stayed at 10 and 0 as approved.
- **The depth without the finest grain.** The graph names a second operator, `dep  Blur h 1 0.003 0.003 1`. The light keeps the grain (`h`); the depth takes the form (`dep`). With the grain in the depth, a wall four pixels wide carries ten pixels of parallax and the two eyes see different pictures.
- **The edges.** Each eye is drawn shifted over the tile plus its edge columns, then the same columns are cut from the left and the right of both eyes, half the largest parallax per side, rounded up; top and bottom are untouched; nothing is widened, scaled or filled. A texture that repeats loses nothing by it: the eye comes out at the tile's own size with no strip.
- **A round thing.** On a post the search runs in the cylinder's own shell: walk the ray from where it enters the shell's outer radius to where it leaves, and stop where the ray's radius falls below the relief's. A ray that passes through a furrow at the rim sees what is behind the post, so the post gets a true rough outline and both eyes see the same trunk. Searching the post as if it were a flat sheet gave streaks, which was the one thing Daniel found wrong in the popped control.

### A flat element with a stereo texture: the wood panel

`panel.py WOOD.png WOOD-height.png OUT` draws a desktop bar whose wood is sunk below the bar's plane (4 pixels at the deepest, the lane's choice, which Daniel saw and found working) while the icons and the clock are the same in both eyes, at the bar's plane.
The wood is used at the size it was drawn and repeats along the bar, so the shift uncovers nothing at the screen's edges.
A theme can carry this as three things: the graph of the wood, the name of its depth operator, and its range (sunk by at most N, popped by at most a few).
SVGStereo 0.4 can say one level for an element (`svgstereo:depth="sunk"`), so a filled area sinks as a whole.
It cannot say a depth that varies inside one fill; today that is drawn as separate elements at a few levels.

### A scene to look at, and real stereo photographs

`scene.py TEXDIR OUTDIR` renders a room corner (tile floor, brick wall, plaster wall, bark post) in 2D and as two marked stereo pictures, the relief sunk only and mostly sunk with a little in front: two cameras with parallel axes and off-axis projections, zero parallax at the nearest thing in view.
It is a picture to judge by, not a renderer.
`real_pns.py REAL.jpg cross|parallel OUT.pns` turns a real side by side photograph into a marked `.pns` at its own size, left eye first.

### What the first run found

- A relief built from three to five parts reads as relief and as the right kind of surface for bark, brick, plaster and tiles; it stays more regular than the photograph, and the second judge's words are in the lane's evidence.
- With true sizes the relief's own parallax is small at 1920 pixels and a 50 degree view: about half a pixel for a brick joint 15 mm deep at 2 m and for a tile joint 6 mm deep at 1.3 m, a little over one pixel for bark furrows 25 mm deep at 1.6 m (computed from the cameras, not measured on the pictures). The surfaces' places in the room carry the depth, and the relief shows in the light. The tile pictures at 10 pixels are an exaggeration, said as such.
- A real stereo photograph of bark has flakes that stand tens of pixels in front of the trunk; the sunk-only tile cannot and should not copy that. Such parts are geometry, or a separate element at its own level.
- Open stereo photographs of a single flat surface are rare: for bark and ground Wikimedia Commons had usable pairs (Robbie Sproule, CC BY 2.0); for a brick wall, plaster and stone tiles none was found, and none was substituted.

### Traps of the relief and stereo round

- Symptom: the self-test measures 2 pixels where 10 were set.
  Cause: the test mark sat in a narrow pit, whose walls hide the floor from each eye.
  Fix: test a mark on the floor of a wide pit.
  Found by: widening the pit until the number stopped changing.
- Symptom: a real stereo photograph looks inside out after it is placed left eye first.
  Cause: it was a cross-eyed pair; its left half is the right eye's view.
  Fix: read the page's own words ("cross eyed", "parallel") and swap the halves; check with a near thing against a far one.
- Symptom: chips or pits cover the whole surface like lava.
  Cause: a `Perlin` used as a mask without amplify and gamma.
  Fix: amplify 2 to 3 and gamma 2 to 9 make it sparse; `HSCB` is not a threshold.
- Symptom: the bark looks like pleated cloth.
  Cause: one `Cell` layer, evenly stretched.
  Fix: a second layer at another scale, a `Distort`, and a coarse noise multiplied over all.
- Symptom: the popped control looks the same as the sunk picture on a far wall.
  Cause: at that distance the relief's parallax is under a pixel either way.
  Fix: judge the control on the nearest surface, or on the tile pictures.
- Symptom: a model says a stereo picture "looks deep".
  Cause: it compares two pictures, it does not fuse them.
  Fix: give it the two eyes as separate pictures and ask which way each feature moved; a person on a 3D screen gives the judgement.
- Symptom: a judge reading colour fringes calls a thing popped that the cameras put behind the screen.
  Cause: the usual reading holds for a feature brighter than its surround; for a dark feature on a light ground the colours come out the other way round.
  Fix: do not make red-cyan pictures for judging; compare the two eyes.
  Found by: the second judge read the dark post as popped while the scene's nearest point is the zero-parallax plane.
- Symptom: the viewers show a stereo PNG flat.
  Cause: the file has no `sTER` chunk; Pillow drops it on every save.
  Fix: insert the chunk after `IHDR` in the finished file and read the file back (`pns.py`).
  Found by: Daniel opened the unmarked pictures on his desktop and TV.
- Symptom: the depth picture is plain noise and the eyes show a grainy surface with no furrows.
  Cause: the graph already had an operator named `d` (a noise used by `Distort`), and the depth was read from it.
  Fix: name the depth operator `dep`, and look at the depth picture before using it.
  Found by: three different textures had the same depth percentiles.
- Symptom: `IndexError: index 512 is out of bounds` while sampling a repeating texture.
  Cause: `np.mod` of a tiny negative float32 returns the width itself.
  Fix: take the floor first, then the modulo of the integer.
- Symptom: at the steep side of a furrow one eye sees a wide dark floor and the other a bright wall.
  Cause: a wall a few pixels wide carries the whole range, so one eye sees it stretched and the other hidden.
  Fix: take the depth from the height without its finest grain, and widen the wall or lower the range if a person finds it restless.
- Symptom: the round post's rim sparkles.
  Cause: near the rim one pixel covers many of the bark's.
  Fix: blend to a softened copy of the lit bark as the surface turns away from the eye.

## Procedures from pixels: the artist's order run backwards, by a program (ORDER 508)

Daniel's request, stated plainly: the procedure is made the way .kkrieger's textures were made, in reverse, from the high-resolution texture's own pixels, never from text; no model types a graph.
The typed graphs of the section above are reference only.
[`pixels/p2p.zig`](procedural-texture-fit/pixels/p2p.zig) is the fitter: Zig, with Farbrausch's own operator code as its renderer ([`wzbridge.cpp`](procedural-texture-fit/pixels/wzbridge.cpp) over werkkzeug4's `wz3_bitmap_code.cpp`), so what it finds is a real werkkzeug3 procedure that the playback module of the WebAssembly section draws unchanged.
This first milestone proves the method on known answers: .kkrieger's own textures, drawn from their real graphs, with only the pixels handed to the fitter.

### The method, and why

The published ways to get a procedure from a picture were read first.
MATch (Shi and colleagues, 2020) picks a finished graph from a library and tunes its values by gradient descent through a differentiable copy of every node; its DiffMat library is for noncommercial research only, so it is cited and not used.
MatFormer (Guerrero and colleagues, 2022) and "Generating Procedural Materials from Text or Image Prompts" (Hu and colleagues, 2023) generate graphs with trained networks, which needs thousands of graphs to train on and is a model writing the graph.
Guo, Hašan, Yan and Zhao (2020) sample a fixed procedure's values with Markov chains, discrete ones included.
"An Inverse Procedural Modeling Pipeline for SVBRDF Maps" (Hu, He, Deschaintre, Dorsey and Rushmeier, 2022) needs no artist's graph: it takes the bitmap apart into parts, models each part as noise in several layers, and tunes everything together against the bitmap.
That last order is the one that fits the request, and it is the artist's order backwards, so the fitter follows it with werkkzeug3's operators:

1. **Read the picture** (no search, at the picture's own size):
   - its two colours: the ends of its main colour axis, where 1 % and 99 % of the pixels lie, and the grey picture between them (the reverse of `Perlin`'s two colours, or of `Range`);
   - whether it repeats: the means of the columns and of the rows, compared with themselves one period away and half a period away (a joint adds up along its length, a noise averages out); when the column means show nothing, the picture against itself moved sideways (rows shifted against each other, a wall's bond);
   - the one cell under the repeats, the mean of all of them, and the shapes in it (the reverse of "one shape drawn once and repeated"); a larger cell is kept only when it predicts the repeats it was not made from better;
   - the noise: which octaves and how strong, from the strength of detail per scale of what the cell leaves, against the same strengths measured on `Perlin` itself one octave at a time.
2. **Build the procedure in the artist's idioms from that reading:** a `Perlin` between the two colours; `Flat`, one `GlowRect` per shape and a `Transform` that repeats it, multiplied in; a `Normals` and a `Bump` taken from .kkrieger's own graphs for the relief, the light starting white; more `Perlin` layers merged over the colour layer.
   A part is kept only when it brings the drawing closer to the picture by more than its bytes cost.
3. **Tune every value by direct search**, one value at a time (Hooke and Jeeves, 1961): whole numbers by trying the values .kkrieger's artists used (all 256 seeds for `Perlin`), decimals and colours by steps that halve.
   No derivative is needed, so the renderer is werkkzeug's own integer code and nothing is re-implemented.
   Values read from the picture that must stay whole (the repeat count) are locked.
4. **Coarse to fine:** at 128 pixels, then 256, then the picture's own size; each size adds what only shows there.
5. **Every kept step is saved as a rung:** the procedure up to there is a thinner version of the final one, with its bytes.

The prior is `prior.py`'s reading of `kkrieger.k`: every operator instance and every generator chain with the operator that consumed it.
It gives the ranges and the values to try, and the real `Normals` and `Bump` instances.
The operators of the textures used as known answers are left out of it, so a known answer never meets its own values.

The measure the search steers by is internal and is not the verdict:
- place: one minus the correlation between drawing and picture per level of a pyramid, counted fully on coarse levels and less on fine ones;
- texture: for twelve small random filters with no mean on the six finest levels, the distance between the spread of their answers on the drawing and on the picture (Elnekave and Weiss, 2022: patch distributions along random directions, no trained network);
- spread: the same distance for each colour channel's values.
The verdict is the eye's: a sheet per texture with the original and the drawing, whole and close up, read by the person, by the model that ran the work and by a second model that saw nothing else.

### Recipe

```sh
# FR is an unchanged clone of github.com/farbrausch/fr_public; Zig 0.16; python3 with Pillow
sh pixels/build.sh BUILD FR                                   # BUILD/p2p, native (x86-64, musl, static)
python3 pixels/prior.py FR/werkkzeug3/data/kkrieger.k WORK NAME...   # the prior without the named textures; WORK/scripts/NAME.script are the artists' graphs
BUILD/p2p render WORK/scripts/NAME.script NAME.ppm            # the known answer's pixels
BUILD/p2p fit NAME.ppm WORK/prior.txt OUT/NAME                # OUT/NAME.script, .ppm, .log (the rungs), .rNN.script per rung
python3 pixels/sheet.py NAME.ppm OUT/NAME.ppm OUT/NAME.jpg "caption"   # original and found, whole and close up
python3 pixels/script2text.py OUT/NAME.script > NAME.txt      # the typed form the playback module and wzlang.py take
python3 pixels/table.py OUT WORK/names.txt NAME...            # bytes and time beside the artist's graph
```

Expect a line `read: colours ... repeats N by M ... noise octaves A to B`, then one line per rung, then `done: N operators, B bytes, T s`.
The same picture and prior give the same procedure and the same pixels on every run (checked with `cmp`).
Run every program the build makes in a container; Zig itself only compiles.
`p2p fit ... readonly=1` prints the reading and stops; `grow=N` adds free moves taken at random from the prior after the reading (off by default: see the traps).

### What the first run found (eleven of .kkrieger's textures, 512 x 512, one CPU thread each)

| texture | artist's graph | found | time | at a glance | close up |
|---|---|---|---|---|---|
| concrete wall | 22 operators, 470 B | 7 operators, 211 B | 268 s | yes | nearly |
| camouflage | 22, 470 B | 3, 111 B | 209 s | yes | no |
| rust | 33, 721 B | 11, 311 B | 240 s | nearly | no |
| rusty metal | 48, 804 B | 3, 95 B | 156 s | nearly | no |
| fibrous wall | 24, 540 B | 7, 211 B | 185 s | no | no |
| rock | 80, 1,664 B | 9, 261 B | 307 s | nearly | no |
| stone tiles | 36, 772 B | 11, 307 B | 240 s | nearly | no |
| brick wall | 24, 644 B | 13, 357 B | 299 s | no | no |
| stone-block wall | 36, 784 B | 14, 402 B | 308 s | no | no |
| wood | 35, 831 B | 3, 111 B | 219 s | no | no |
| carved stone | 33, 789 B | 7, 211 B | 196 s | no | no |

The verdicts in the table are the fitting model's own reading of the sheets; the lane's report holds its words and the second model's.
- **What it finds:** the material's colours and the kind and scale of its noise (concrete, camouflage, rust, the metal's grey); a regular repeat and where its joints are (the tiles' two by two, the wall's rows).
- **What it does not find:** hard-edged patches (camouflage's flakes come back as soft clouds); a second material on the surface (the metal's orange rust: no `Mask` is built yet); grain that runs one way or swirls (wood, the fibrous wall: no `Distort`, `Twirl` or stretched noise is built yet); bricks of uneven length and a wall's bond with a bevel on every stone; a drawing (the carved ornament), which is objects, not a material.
- **The relief is the weakest part:** a `Bump` over a noise often comes back as pits or lumps the original does not have.
- **Bytes:** the found procedures are 12 to 55 % of the artists' bytes, because they hold less, not because they are better.
- **Time:** 2.6 to 5.1 minutes per 512 pixel texture on one thread, about 11,000 to 17,000 drawings of the graph; the fitter remembers every operator's result, so a changed value redraws only what lies above it.

### Traps of the reverse

- Symptom: free moves drawn at random from the prior (a real chain, a real operator, joined anywhere) with a measure made of squared pixel differences and the strength of detail give scratches, rotated grids and soft rectangles, never the material.
  Cause: a weak statistic is easy to satisfy with the wrong thing, and the artists' graphs are mostly lamps and sprites, so random real chains are mostly glows.
  Fix: read the picture first and build from the reading; keep random moves as an option.
  Found by: looking at the first three sheets instead of the falling measure.
- Symptom: a patchy texture comes back as one flat colour.
  Cause: with squared pixel differences a right texture in the wrong place scores worse than no texture at all.
  Fix: the place part is one minus the correlation, never below none, so flat and misplaced score the same and the texture part decides.
  Found by: drawing the reading's own first `Perlin` beside the flat result; the eye preferred the one the measure refused.
- Symptom: the whole picture is chosen as the repeating cell and "explains 100 %".
  Cause: a larger cell always fits its own pixels better.
  Fix: make the cell from every second repeat and judge it on the others.
- Symptom: tiles with thin joints read as not repeating.
  Cause: a thin joint is a few per cent of the contrast, less than the noise of a cell made from two repeats; at 128 pixels it is gone.
  Fix: read at the picture's own size and find joints in the column and row means with the peak test (agree one period away, not half a period away), which a smooth noise does not pass.
- Symptom: a brick wall reads as rows only.
  Cause: rows shifted against each other put their upright joints at different columns, so the column means show nothing; bricks of uneven length have no period at all.
  Fix: for the first, compare the picture with itself moved sideways; the second is not a repeat and stays with the image.
- Symptom: joints found at the right place come out as ten slanted or crowded lines.
  Cause: the tuner changed the `Transform`'s scale, a repeat count read from the pixels, by a fraction.
  Fix: lock what was read as a whole number.
- Symptom: purple, green and blue patches on a grey material.
  Cause: .kkrieger's `Bump` instances carry the game's coloured lamps, and colours of added layers were tuned freely.
  Fix: a light starts white over grey with no shine, and lights and added noises are tuned as greys.
- Symptom: nothing is written for minutes and one thread is busy.
  Cause: `var sh: u5 = 0; while (sh <= 24) : (sh += 8)` wraps in a fast build and never ends.
  Fix: loop over a list of the four shifts.
  Found by: no rung file after the first tuning.
- Symptom: a rerun gives the same numbers to the last digit after a change.
  Cause: the build failed (an unused capture is an error in Zig) behind a pipe that hid the exit status, and the old program ran.
  Fix: write the build's output to a file, test its exit status, and check the program's date before believing a run.
- Symptom: leaving the known answers out halves the prior (737 of 1,484 instances).
  Cause: every graph that shares one stored operator with a known answer was dropped.
  Fix: drop the shared operators, keep the graphs.
- Symptom: a run stalls on one candidate.
  Cause: an operator with a large count (`Cell`, `TransformMul`) takes seconds.
  Fix: a drawing slower than a bound is refused: the device must draw it too.
- Symptom: the operator code stops the program on a check.
  Cause: the fitter tries values no artist typed.
  Fix: the bridge returns from a failed check with `longjmp` and the candidate is refused; the bitmaps of that one call are lost.

### The second round: more of the artists' operators, and what the eye said (milestone 1b)

The build step gained steps over the colour layer, each from .kkrieger's real instances: grain (the layer stretched one way, `Distort` by a noise, `Twirl`), a second material (`Mask` through a `Perlin` with amplify and gamma or through a `Cell`), `Cell` merged in, tone (`Range`, `HSCB`, `Blur`), the bond (the shape on every second row moved half a cell), the bevel (`Blur` of the shape before `Normals`), and the joints' colour taken from the dark end of the picture's own colours.
Which generators the artists started from, counted in the 742 drawable graphs: `Perlin` 1,519 times in 511 graphs, `Flat` 908 in 459, `Cell` 243 in 145, `Gradient` 192 in 104, `Bricks` never.
- **Better, by eye:** the stone tiles (dark grooves with a lit edge, a whole tile with its border in the close-up); the dark pinpoints are gone; wood has a grain direction.
- **Worse, by eye:** `Cell` and `Mask` through cells were kept on nine of eleven textures and drew a web of cell edges over rust, metal, rock and both walls; they paid by the inner measure and are wrong to the eye.
- **The rule this leaves:** "kept if it pays by the measure" is not enough for an operator that adds structure. Grain is now tried only where the reading finds one (detail stronger one way than the other by 1.2 or more: wood 2.13, the fibrous wall 1.38, the others 1.01 to 1.07); cells, a mask and a twirl need a reading of their own before they are tried.

More traps:
- Symptom: dark pinpoint specks on a smooth surface.
  Cause: a `Perlin` gamma tuned below zero (the range was the artists' lowest value minus one spread), which turns the noise's zeros into spikes.
  Fix: a value the artists never took below zero stays at or above zero.
  Found by: every specked result had a `Perlin` with a negative gamma; setting it to 1 removed the specks on the fibrous wall (317 to 0 counted pinpoints).
- Symptom: the joints are found, but a close-up shows a cross of lines where the original shows one whole tile.
  Cause: the tuner moved the shape's centre, which was read from the picture.
  Fix: lock the centre as well as the repeat count.
- Symptom: one large swirl on a concrete wall.
  Cause: a `Twirl` pays by the measure on any noise.
  Fix: try grain only where the reading finds a direction.
- Symptom: the playback module draws a found graph with a few hundred pixels different.
  Cause: the typed text printed decimals with six digits.
  Fix: nine digits (`%.9g`); then 0 of 262,144 pixels differ on four graphs.

### The third round: every structure needs its own reading, and the eye chooses (milestone 1c)

The second round left one rule: an operator that adds structure is never tried because the inner measure likes it.
Each one now has a reading of its own, measured on the picture and never searched, and the fitter refuses a structure whose reading does not allow it (`structure NAME is refused`).

| structure | operator | the reading, and how it is measured | allowed when | what the pictures gave |
|---|---|---|---|---|
| patches | `Cell` as a `Mask` | flat patches: at a quarter of the side, the share of places whose 5 by 5 surroundings differ by less than 0.08; hard edges: the share of the picture's change that sits in the 5 % of places that change most | flat 0.03 or more and edges 0.35 or more | camouflage 0.05 and 0.39; every other picture 0.00 to 0.02 flat |
| second | `Mask` | a colour off the main colour axis: the share of pixels further than 0.10 from the line between the two colours, and how alike their offsets are (1 is one colour) | share 0.01 or more and alike 0.8 or more | rusted metal photograph 0.018 and 0.94; the noises 0.000 to 0.003 |
| grain | `Transform` | the change from a pixel to its neighbour across against the change to the one below; the larger says which way the fibres run | 1.2 or more | wood 2.13, fibrous wall 1.38, rusted metal 1.36; the others 1.03 to 1.11 |
| rings | `Twirl` | at half the side, for every centre on a grid of 4 pixels and a disc of a tenth of the side: the share of the change that runs along the radius (0.5 for lines in no order, 1 for rings), taken as the smaller of the disc's inner and outer half, so one round blob does not count | 0.74 or more; up to three centres | wood 0.89, 0.83, 0.82; carved stone 0.85, 0.81, 0.75; the others 0.54 to 0.66 |
| mirror | `Transform` with a negative scale | two ring centres that lie level (within one radius), and how much better the way the lines run around one agrees with the other turned left to right than as it lies | 0.10 or more | carved stone 0.55 turned against 0.40 as it lies; wood has no level pair |
| shape | `GlowRect`, `Transform` | the repeat of the first round (column and row means, the peak test, the cell) | a cell with a shape | tiles 2 by 2; the walls |
| bond | `TransformMul` | the picture cut into its rows; every row's mean across against the next row's, as it lies and moved sideways; the bricks per row from a row against itself | the moved row agrees better by 0.2 or more | brick wall 0.44 at 0.58 of a brick, 16 rows of 8; block wall 0.61 at 0.59, 8 rows of 4; the tiles 0.00 |

A repeat is read first, and where one is found the other structures are not tried: a grid is its own mirror picture, and a wall's rows read as grain (1.25 on the brick wall).
The thresholds sit in the gaps these fourteen pictures leave; the narrow ones are the patches (0.05 against 0.02) and the mirror (0.14).

**The outline trick.**
.kkrieger's artists made outlines by blurring a shape, subtracting the shape and setting the brightness.
`appendOutline` builds the joints that way: the shape in white on black, repeated; `Blur` as wide as the joint read from the picture; `Merge` in mode 1 (the first input minus the second), which leaves what the blur carried out of the shapes; `HSCB` with the brightness set so the outline's brightest place becomes full (the fitter draws the outline once to find it); `Range` from white to the joints' colour; `Merge` in mode 2 into the surface.
The joints' colour is measured, not searched: the cell's darkest line over the shape's own brightness, both on the picture's colour axis, so the mortar is the darker shade of the bricks' own colour.
The blurred shape is the height for `Normals` and `Bump`, which lights the edge of every brick.
No thin drawn joints are built any more.

**The bond the artists' way.**
`TransformMul` is `GenBitmap::RotateMul`.
Read in `wz3_bitmap_code.cpp` and checked with drawings: with mode 16 it merges the picture with a moved copy of itself `count` times, each move twice the last, so `count` 4 lays 16 rows; the first move is (t - 0.5) / (2^count - 1); without mode 16 it adds `count` copies of the first picture, the i-th moved i times (t - 0.5) / count; and a move of t - 0.5 carries the picture by minus that.
One brick is drawn, a `Transform` repeats it across, and a `TransformMul` lays the rows, each one row down and the measured part of a brick sideways.
.kkrieger's own walls are built the same way, and the measured 0.58 of a brick is what their graphs hold (0.583).

**The mirror and the spiral.**
A `GlowRect` at the ring's centre, a `Twirl` there and a second one, a `Transform` with scale -1 across about the mirror line, both merged (`Merge` 0), and that drawing as the height of a lit relief.
The centres, the radius and the mirror line are read; only the turn is tried (four values).

**The visual check.**
One run builds one structure (`structure=plain|shape|patches|second|grain|rings|mirror`); its best candidate is kept without the pay test, and what a reading built is not removed or faded by the tuning.
`choices.py` puts the finished drawing of every allowed structure beside the original, at most four, whole and close up, with bytes and the inner measure, and marks the lowest measure as the program's choice.
The person or the model looking chooses by eye and writes why; a few values are set the same way, by looking (`stretch=8`, `relief=0`, `surface2=1`, `blur=0.002`, `jointw=1`).

```sh
BUILD/p2p fit NAME.ppm WORK/prior.txt OUT/x readonly=1          # the readings, then: allowed by the readings: plain shape ...
BUILD/p2p fit NAME.ppm WORK/prior.txt OUT/shape/NAME structure=shape
python3 pixels/choices.py REF OUT sheet.jpg NAME plain shape    # original | plain | shape, whole and close up
printf 'v0 Flat - 8 8 #ff000000\nv1 GlowRect v0 0.3 0.3 0.01 0.01 0.15 0.05 #ffffffff 1 0.5 1 0\n' | python3 pixels/text2script.py > t.script   # a test graph, to see what an operator does
```

What the eye chose on the eleven pictures (eight of .kkrieger's, and three CC0 photographs from Poly Haven reduced to 512 pixels, which replaced .kkrieger's rust, rusty metal and rock after Daniel asked for better sources):

| picture | allowed | the program's choice | chosen by eye | found |
|---|---|---|---|---|
| concrete wall | plain | plain | plain | 3 operators, 111 B |
| camouflage | plain, patches | patches | patches | 8, 212 B |
| rust (photograph) | plain | plain | plain | 5, 141 B |
| rusted metal (photograph) | plain, second, grain | second | second without the relief | 7, 171 B |
| fibrous wall | plain, grain | plain | grain | 5, 161 B |
| rock (photograph) | plain | plain | plain | 3, 111 B |
| stone tiles | plain, shape | shape | shape, the surface 2 by 2, no relief | 9, 193 B |
| brick wall | plain, shape | shape | shape | 14, 330 B |
| stone-block wall | plain, shape | shape | shape | 15, 347 B |
| wood | plain, grain, rings | rings | rings with stretch 8 and no relief | 5, 165 B |
| carved stone | plain, rings, mirror | mirror | mirror | 11, 295 B |

- **Now right at a glance, by the fitting model's eye:** the brick wall and the block wall (a wall in its bond, mortar in the darker shade of the bricks), the tiles (thin dark joints with no shine, finer granules), the concrete.
- **Recognisable, not right:** wood (long fibres with three spiral knots where the original has its rings; no rings, and the fibres repeat as regular stripes); the carved stone (two lit spirals, mirror twins, at the right places; wound too tight, and the arcs above them are not built); camouflage (flat patches in the picture's greens, with straight polygon edges where the original has ragged flakes); the fibrous wall (fibres running down; soft, with a regular rhythm).
- **The photographs:** the colours and the kind of surface come back (a warm brown rust, orange over grey, a sand-coloured granular stone); the speckles and drips of the rusted metal, the rust's stains and the rock's cracks and pits do not. That is where the image stays the last layer.
- **Program against eye:** they differ on three of the eleven. On the wood the inner measure prefers 0.47 (sideways smears) to 0.80 (the fibres and knots the eye takes); on the fibrous wall 0.21 (lit worm shapes) to 0.51 (fibres).
- **The readings run on the fitter's own drawings** (a test that can fail): the found brick wall reads 16 rows of 8 in a bond at 0.58, as the original does; the found wood reads rings at the same three places; the found tiles do not read as a repeat (the joints are fainter than the original's); the found carved stone reads one ring and no mirror pair; the found camouflage reads a false ring at 0.76.
- **Against the fair baseline:** the three photographs' lower-resolution copies are 390,825, 414,440 and 591,032 bytes (31.6, 40.7 and 34.6 % of the 2048 pixel JPEG); the found procedures are 111 to 171 bytes and hold only the material's look.

Traps of the third round:
- Symptom: the program ends at once after `rung 0` with no message, and a checked build reports `integer overflow` at a line of unrelated older code.
  Cause: `const m = @min(n, 256)` gives the smallest type that holds the bound (a 9-bit number), so `m * m` overflows; the fast build has no check, and the checked build's line number is wrong because the reading is inlined.
  Fix: `const m: usize = @min(n, 256)`.
  Found by: a build with `-O ReleaseSafe` and a line printed before and after each new reading.
- Symptom: a carving does not read as a mirror picture (0.11 to 0.27, the same as wood and rust).
  Cause: brightness, and edge strength too, follow the light: a flank facing the light is bright, its mirror twin faces away; and the ornament is a small part of the picture.
  Fix: compare only which way the lines run (the change across squared minus the change down squared, and twice their product, each made the same length), around a level pair of ring centres, turned against as it lies; rings alone are their own mirror picture, so the difference of the two is the reading.
  Found by: four versions printed on the wood and the carved stone side by side.
- Symptom: a cloud reads as "repeats 1 by 2" and gets a shape.
  Cause: joints seen in the row means were trusted even when the cell predicted the other repeats far worse than no cell (-78 %).
  Fix: trust them only above -10 % (thin joints give about -3 %); the refusal is printed.
- Symptom: with a full search the brick wall has no bricks, though a quick run had them.
  Cause: the tuning lowered the outline `Blur`'s strength to 0.23 and set `HSCB`'s brightness to 0, and the cleaning removed operators that "did not earn their bytes".
  Fix: what a reading built is marked kept and its values locked; the brightness is set from the outline's own drawing.
  Found by: printing the found graph; the operators were there with the values changed.
- Symptom: a noise is merged into the shape instead of the surface.
  Cause: the cleaning removed an operator below the surface layer's top and the index kept pointing one further.
  Fix: the top is marked before the cleaning and found again after it.
- Symptom: patches are allowed and built, and the drawing shows clouds; or it shows a web of lines.
  Cause: the tuning turned every cell white; and `Cell` draws edges in modes 1, 3 and 7.
  Fix: `Cell` in mode 2 (every cell one flat shade, read in `GenBitmap::Cell` and drawn), its shades, the `Flat` and the `Mask` locked; only the count and the seed are tried.
- Symptom: a `Blur` of 0.006 over the patches smears them away.
  Cause: the value is the operator's own radius, far wider than it looks; the artists' camouflage uses 0.0024.
  Fix: 0.002; 0.004 looked the same.
- Symptom: one knot becomes a swirl half the picture wide, or a disc turned as one plate with a visible rim.
  Cause: the `Twirl`'s radius and its fall were tuned by the inner measure (the fall went to 0).
  Fix: the centre and the radius are the reading's, the fall is one of two tried values; only the turn is tuned.
- Symptom: wood fibres come out as worms at a slant, or as sideways smears.
  Cause: `Distort` by a noise, and the relief's own `Blur` over a stretched noise.
  Fix: grain is a `Transform` that repeats the layer across the fibres, in the direction the reading gives; how long the fibres are is set by eye (`stretch=8`), and the relief is left off for wood (`relief=0`).
- Symptom: with the surface repeated 2 by 2, a white line runs beside every joint.
  Cause: the relief lights the blurred shape's edge, and the finer surface shows it.
  Fix: no relief for that choice; the `Bump`'s shine colour is locked at black in every relief, since a glossy groove is wrong to the eye.
- Symptom: `p2p render` of a rung script fails.
  Cause: rung scripts carry no size.
  Fix: give the size as the last argument (`render SCRIPT OUT.ppm 8` for 256 pixels).
- Symptom: two launches of the same job list at once: `Conflict. The container name ... is already in use`.
  Cause: a wait loop that started the jobs was thought to have ended without starting them.
  Fix: one launcher; check the container list by name before starting another.

### Where the procedures stop (so far)

On .kkrieger's own textures, which are procedures, the reverse now gets the material at a glance for the plain noises, the regular repeats and the walls in a bond, and a recognisable drawing for the wood and the carved ornament; nothing is right close up.
On photographs it gets the colours and the kind of surface, and none of the marks that make the photograph that surface (speckles, drips, stains, cracks): those stay with the image, the last layer.
Not built yet: a `Distort` for ragged patch edges and for stones of uneven length, the rounded bevel of a stone, text (font glyphs used as shapes), rings (as against spirals), and the same method tile by tile on photographs.

## Where it fails

- Photographic and scanned detail: nothing small predicts it.
- A statistics match is another sample of a similar material, not the picture; no number here says how different it looks.
- Regular textures are regular only in outline; each brick's own colour and chips stay in the image.
- A sum of cosines rings at edges and is not what an artist's graph is; fitting shapes (`GlowRect`, `Cells`, werkkzeug3's `Bricks`) is what the published methods do with networks and gradient descent; the reverse section above fits `GlowRect` shapes from the picture's repeats by direct search.
- Not covered: normal, roughness and height maps; AVIF, JPEG XL and GPU texture formats; a perceptual measure or a person's judgement; the cost of evaluating the procedure; magnification beyond the picture's size.

## Traps

- Symptom: the operator draws one constant colour while the fit's model shows noise.
  Cause: OpenKTG's normalised `Noise` computes `(fadeoff - 1) / (fadeoff^oct - 1)`, which is 0/0 at `fadeoff` 1.
  Fix: never fit `fadeoff` exactly 1, and compare the real operator with the model on every picture.
  Found by: a spectrum gap equal to the flat colour's, to the last digit.
- Symptom: subtracting an unrelated noise makes the lossless remainder smaller than the picture.
  Cause: lossless WebP on a difference stored modulo 256; an unrelated smooth field gave 5.8 % fewer bytes, where PNG gave 1.3 % more.
  Fix: measure lossless sizes with PNG, and compare against the flat colour's remainder, which is stored the same way.
  Found by: repeating the measurement with a field that cannot be related to the picture.
- Symptom: `OSError: broken data stream when writing image file` from Pillow on the random-bytes control.
  Cause: a JPEG of pure noise is larger than Pillow's encoder buffer when `optimize` is on.
  Fix: `ImageFile.MAXBLOCK = width * height * 4` before saving.
- Symptom: the control's parameters come back nearly right (8 octaves for 7, fadeoff 0.548 for 0.55) and its remainder is almost as large as the picture.
  Cause: the parameters were refined on a reduced copy; a box-averaged picture is not the operator drawn at a smaller size, and a remainder of plus or minus one level is noise that does not compress.
  Fix: once the seed locks, settle octaves, fadeoff and colours against a sample of the full-size pixels, and prefer the rounder value when it fits as well.
- Symptom: the lossy remainder of a flat colour costs up to 13 % more than the picture alone on a control at 50 dB.
  Cause: JPEG qualities are steps; near 50 dB one step is many bytes.
  Fix: interpolate the bytes between the two nearest qualities, and report the flat colour's row as the method's own error (0.0 to +1.2 % on the six real pictures).
- Symptom: a research library that fits artists' graphs looks like the tool to carry.
  Cause: its licence was not read: DiffMat is under a research licence "solely for noncommercial research purposes" and needs a proprietary toolkit.
  Fix: read the licence file before planning on any fitter; OpenKTG (public domain), werkkzeug3 (BSD two-clause) and MaterialX (Apache-2.0) are the open ground.

## Perks of this part

- OpenKTG has 4,096 seeds, so a picture made by it can be recognised by scanning them all.
- OpenKTG's `Noise` and MaterialX's `fractal2d` are the same idea under two sets of names (`oct` and `octaves`, `fadeoff` and `diminish`), so a fit made on the open base can be written as a graph for glTF's `KHR_texture_procedurals` draft.
- werkkzeug3's project files in `fr_public` are pictures with known procedures: a ready test set for a fitter.

## Credits

OpenKTG: Fabian "ryg" Giesen. werkkzeug3: Dierk Ohlerich, Fabian Giesen, Thomas Mahlke, Christoph Muetze, Tammo Hinrichs and Bastian Zuehlke, as its licence names them. The pictures of the first run: Poly Haven, CC0. Relief mapping: Fábio Policarpo, Manuel M. Oliveira and João L. D. Comba (2005). Parallax occlusion mapping: Natalya Tatarchuk (2006). The stereo photographs of bark and ground: Robbie Sproule, CC BY 2.0, on Wikimedia Commons. MaterialX: the Academy Software Foundation's project, its standard nodes document by Doug Smythe and Jonathan Stone. The reverse from pixels: Yiwei Hu, Chengan He, Valentin Deschaintre, Julie Dorsey and Holly Rushmeier (2022) for the order (parts, layered noise, tuning together); Ariel Elnekave and Yair Weiss (2022) for comparing textures by their patches along random directions; Robert Hooke and T. A. Jeeves (1961) for direct search; the bridge to the operators started as lane 503's, from lane 473x's renderer.
