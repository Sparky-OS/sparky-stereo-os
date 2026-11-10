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

## Where it fails

- Photographic and scanned detail: nothing small predicts it.
- A statistics match is another sample of a similar material, not the picture; no number here says how different it looks.
- Regular textures are regular only in outline; each brick's own colour and chips stay in the image.
- A sum of cosines rings at edges and is not what an artist's graph is; fitting shapes (`GlowRect`, `Cells`, werkkzeug3's `Bricks`) is what the published methods do with networks and gradient descent, and was not tried.
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

OpenKTG: Fabian "ryg" Giesen. werkkzeug3: Dierk Ohlerich, Fabian Giesen, Thomas Mahlke, Christoph Muetze, Tammo Hinrichs and Bastian Zuehlke, as its licence names them. The pictures of the first run: Poly Haven, CC0. Relief mapping: Fábio Policarpo, Manuel M. Oliveira and João L. D. Comba (2005). Parallax occlusion mapping: Natalya Tatarchuk (2006). The stereo photographs of bark and ground: Robbie Sproule, CC BY 2.0, on Wikimedia Commons. MaterialX: the Academy Software Foundation's project, its standard nodes document by Doug Smythe and Jonathan Stone.
