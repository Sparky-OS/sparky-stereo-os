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

### The fourth round: Text, a font glyph used as a shape (milestone 1d)

.kkrieger's artists used letters as shapes: `kkrieger.k` holds 99 `Text` operators, and 112 of its drawable named textures contain one.
The title logo is seven of them: each letter of "kkrieger" is one glyph, blurred, twisted by three to thirteen `Twirl`s and lit as a relief (`r.kkrieger.g` is `Flat`, `Text` "g", `Blur`, three `Twirl`s: 6 operators, 170 bytes).
The others are the title and credits screens, the menu, two font pages, and words on a crate, a sign, a blade and the weapons.

**The font renderer.**
werkkzeug3 drew text with Windows GDI (`sSystem_::FontBegin`, `FontPrint`, `FontWidth` and `FontCharWidth` in `_start.cpp`); werkkzeug4's portable copy (`GenBitmap::Text`) draws through altona's `sFont2D`.
`pixels/wzfont.c` gives those calls on FreeType, reading the font's own outlines and nothing else: no bitmap strike, no hinting program, no pre-rendered glyph.
`shim/font2d.hpp` is the `sFont2D` stand-in over it, so `GenBitmap::Text` itself draws a plain text; a font page (flags 0x10 to 0x70: every letter of a game font, one after the other) exists only in werkkzeug3, and its loop is taken over line by line in `wzbridge.cpp`.
What the renderer follows, each tied to its source:

| what | the rule | where it is written |
|---|---|---|
| the outline | TrueType outlines are quadratic curves, CFF outlines cubic; both are filled by the non-zero winding rule | OpenType 1.9.1, "glyf" and "CFF"; FreeType Glyph Conventions, VI "FreeType Outlines" |
| character to glyph | the font's `cmap`; a character with no entry gets glyph 0, the missing glyph | OpenType 1.9.1, "cmap" ("mapped to glyph index 0 (missing glyph)") |
| the size | werkkzeug3 calls `CreateFont(-h, w, ...)`: an em square `h` pixels high, so the scale is `h` over `unitsPerEm` | werkkzeug3 `_start.cpp`; OpenType "head" |
| the line's top and height | GDI's `tmAscent` and `tmHeight`, from `usWinAscent` and `usWinDescent` | OpenType "OS/2" ("In the Windows GDI implementation, the usWinAscent and usWinDescent values have been used to determine the size of the bitmap surface") |
| the advance | `advanceWidth`, rounded to whole pixels; no kerning (GDI's `ExtTextOut` adds none) | OpenType "hmtx" |
| a set character width | `w` is the average character width asked for; the outlines are stretched by `w` over the font's own average | OpenType "OS/2", `xAvgCharWidth`; see the trap below |
| the text's bytes | Windows code page 1252 | the project file stores 8-bit strings |
| an empty font name | "arial" | werkkzeug3 `_start.cpp`: `if(name[0]==0) name = "arial";` |
| the two size values | the operator's third value is the font's height and its fourth the character width, although werkkzeug3's code names them `width` and `height` | `FontBegin(xs,ys,font,xs*height,ys*width,4)` in `genbitmap.cpp` |
| where a plain text starts | (the space around letters + 2) pixels right and down of its x and y; every plain text of .kkrieger has space 2 | `es = extspace*alias + 2*alias` in `genbitmap.cpp` |

**The fonts, and what stands in for them.**
`kkrieger.k` names "times new roman" 15 times, "verdana" twice, and no font 82 times (so 82 are Arial).
Those are Microsoft's fonts and are not in Debian, so a font map says which file draws each name, and nothing is chosen in the code:

```
# werkkzeug's font name = font file | the sentence said in every caption
arial = LiberationSans-Regular.ttf | Liberation Sans 2.1.5 stands in for Arial (metric-compatible)
times new roman = LiberationSerif-Regular.ttf | Liberation Serif 2.1.5 stands in for Times New Roman (metric-compatible)
verdana = DejaVuSans.ttf | DejaVu Sans 2.37 stands in for Verdana (not metric-compatible: its letters are a different width)
```

`WZ_FONTMAP` names that file.
Without it, with a name it does not hold, with a file that is no outline font, or with werkkzeug4's bold and italic flags, `Text` is refused with a sentence that says which; every font used and every character without a glyph is printed as a `text:` line by `p2p render` and `p2p fit`, and the sheets carry those lines.
Liberation Sans and Liberation Serif are the stand-ins fontconfig's own `30-metric-aliases.conf` binds to Arial and Times New Roman.
Measured against the Microsoft fonts of 2000 (versions 2.82) over code page 1252: 217 of 218 advances are equal (the middle dot differs), and `usWinAscent` and `usWinDescent` are equal, so the same letters stand at the same places.
The letter shapes inside those widths differ: 1.35 % of the pixels (the middle value over the 112 textures) differ by more than 24 of 255, 7 to 9 % on the logo's big twirled letters.
Verdana has no metric-compatible free font: DejaVu Sans has 35 of 218 advances equal, letters 0.65 to 1.06 times as wide and a different line height, and 32 % of the pixels of the one Verdana font page differ.
A person who has the named fonts points the map at them; the fitter and the renderer do not care which files they are.

**The known answers.**
All 112 textures with a `Text` draw (14 seconds for all of them at 512 pixels).
The shipped game's title screen (a capture on Wikimedia Commons) shows the same four texts in the same places at the same sizes as the drawing of `flat.credits.kk01`.

**The reading: what in the pixels says a glyph shape is here.**
Like every structure of the third round, `Text` is tried only where its own reading allows it, and a letter is found by laying the font's own outlines over the ink, never named by a person or a model.

1. A figure on a ground: at least 0.80 of the picture lies in two flat shades (within a quarter of either end of the picture's colour axis); the smaller shade is the ink.
   The fourteen pictures of the earlier rounds give 0.16 to 0.51, the text pictures 0.94 to 1.00.
2. The ink's connected pieces, each stretched to its own box as a 24 by 24 picture.
   A box or a disc is not a glyph: `GlowRect` draws those.
3. Each piece against every glyph of the map's fonts (code page 1252), drawn from the outlines and stretched the same way: their common part over their union, where the piece's own proportions are the glyph's.
   Two pieces one above the other are tried together against the glyphs that have two pieces (i, j, !, ?).
4. A line: the size and top most pieces agree on, each piece taken with the glyph whose box fits the line best, which also tells o from O and s from S.
   A line is started only by a piece with enough form to say "glyph" on its own (a line through it crosses ink twice in a quarter of its rows or columns: o, e, a, g, k, not a comma, a dash, an r or a t) that reaches 0.70; pieces that fit a standing line are taken from 0.58.
5. The letters of a line that follow each other by the font's own advances, with spaces where the gap is whole spaces, become one `Text` operator: its text, font, place and size are all read.
6. Allowed when the lines hold 0.85 of the ink or more and the pieces lie over their glyphs by 0.70 or more.
   Why 0.70: the menu's plain texts lie over their glyphs by 0.90 and a twirled glyph given back by 0.99; texts bent by a `Distort` give 0.66 to 0.76, so the threshold cuts through them; the pieces of figures that are no text (two-shade noise, veins, one blob) give 0.27 to 0.34, a box and a disc are no glyph at all, and a square ring gives 0.66, the nearest thing to a letter that is none.

**A twirled glyph: the Twirl run backwards.**
Where the figure is one to three pieces that are no glyph and the ring reading of the third round finds a swirl, werkkzeug's own `Twirl` is run on the picture at minus its strength.
`Twirl` turns every point about the centre by an angle that depends only on its distance from the centre, so the same twirl with the opposite strength undoes it exactly.
The candidates are the fitter's own grid (centres on eighths of the side, radii 0.25, 0.5 and 0.75, gamma 2, 16 and 48, strengths in eighths up to 1.5); the one after which the pieces lie best over a glyph is kept, up to three, and what steers it is the glyph reading, not the inner measure.
After twirls were taken out the figure must lie over its glyph by 0.90 or more: a true `Twirl` run backwards gives the glyph back (0.99 on the logo's g), while the search can also bend a bar into a tilde or a hook into an e (0.75 to 0.77).
The found procedure is `Flat`, the `Text`, a `Blur` for the soft edges (the artists' one to three passes and ten widths are drawn, the best is kept if it pays for its 17 bytes), and the twirls forwards, with the strengths as read.
Each text's place and size are then tried by pixels and less around what was read; nothing else is searched.

```sh
export WZ_FONTMAP=FONTS/fonts.map                               # name = file | sentence; nothing draws a Text without it
python3 pixels/textset.py FR/werkkzeug3/data/kkrieger.k WORK/text    # the 112 graphs with Text, their strings as s=HEX
BUILD/p2p render WORK/text/r.kkrieger.g.script g.ppm            # prints: text: Liberation Sans 2.1.5 stands in for Arial (metric-compatible)
BUILD/p2p fit g.ppm WORK/prior.txt OUT/x readonly=1             # figure: ... as lines of arial ...: 1.00 of the ink, likeness 0.99 / text "g" at 0.2510, -0.2495, height 1.0000
BUILD/p2p fit g.ppm WORK/prior.txt OUT/g structure=text         # the found procedure
python3 pixels/script2text.py OUT/g.script                      # ... Text v0 0.25 -0.25 1 0 #ffffffff 0 2 0 1 "g" ""
sh pixels/build.sh BUILD FR FREETYPE                            # the build now takes FreeType's unpacked source as its third argument
```

What the fourth round found (512 pixels, one thread):

| picture | the artists' graph | found from the pixels | time | at a glance | close up |
|---|---|---|---|---|---|
| the logo's g | 6 operators, 170 B: `Flat`, `Text` "g", `Blur`, three `Twirl`s | the same six operators, 170 B: the `Text` and the three `Twirl`s value for value, `Blur` 0.0090 for 0.0092 | 19 s | yes | yes |
| the menu | 5, 201 B: three `Text`s and an `HSCB` | 4, 184 B: the three texts "start", "options", "info" within a pixel, in the picture's grey | 5 s | yes | yes |
| "chaos" (bent by a `Distort`) | 4, 124 B | 3, 123 B: "chao" and "s", clean | 4 s | yes | no |
| "kb", "ryg" (bent) | 4, 120 B each | 2 and 3 operators, 66 and 83 B | 2 s | yes | no |
| "giZMo" (bent) | 4, 124 B | 4, 172 B: "g Z", "Mo" and an inverted exclamation mark where the i is | 4 s | nearly | no |
| ".hund" (bent, over drips) | 13, 385 B | 4, 144 B: "hu" and "nd" in the font named verdana, where the artists' graph has Arial | 4 s | nearly | no |

- **Wrong, and seen by eye:** the reading allowed seven of the thirty text pictures it was run on; on two of them the letters bent by the `Distort` misled it (another glyph for giZMo's i; the wider font for ".hund", whose dot and drips are also missing).
- **Read back:** the reading run on the fitter's own seven drawings gives the same texts ("chaos" as one), and "g!ZMo" for the sixth: the mark standing for the i is no i.
- **Refused, and said so:** the logo's other letters (four to thirteen twirls: the search takes out three at most, one at a time, and does not get the glyph back); eight of the twelve credits' texts tried (bent too far: 0.66 to 0.75, or under 0.85 of the ink read); texts 9 to 20 pixels high; a font page (more than 300 pieces); a text over a material (no flat ground: a crate, a sign, a blade).
- **The eleven of the third round:** rerun with this fitter, every found procedure and every drawing is byte for byte the third round's.

Traps of the fourth round:
- Symptom: small captions overlap the names beside them, and every text with a set character width is a quarter too narrow.
  Cause: GDI stretches a font by the width asked over the font's average width; Arial 2.82 states 904 units (OS/2 version 1: the weighted average of the lower-case letters and the space), Liberation Sans 2.1.5 states 1187 for the same letter widths (version 3 and later: "the arithmetic average of the escapement (width) of all non-zero width glyphs").
  Fix: for an OS/2 table of version 3 or later, work out the average by the older rule from the font's own advances (904.46 for both fonts).
  Found by: the two fonts' tables side by side, and the caption row of the intro's credits, which overlapped before and fits after.
- Symptom: letters would come out about a tenth too small, and shifted.
  Cause: werkkzeug4's `sFont2D` on Windows hands the size to GDI as a positive height (the whole line's height); werkkzeug3 handed it over negative (the em square's height), and its plain texts start (space + 2) pixels in, which werkkzeug4's copy dropped.
  Fix: the stand-in takes the size as the em square's height, and the bridge adds the offset to the position.
  Found by: reading `FontBegin` in werkkzeug3's `_start.cpp` beside `sFont2D::Init` in altona's `windows.cpp`; the game's title screen then showed the texts where the drawing has them.
- Symptom: every place read from the pixels is two pixels off the artists' value.
  Cause: the space around letters is 2 in every plain text of .kkrieger, so the text starts four pixels in, not two.
  Fix: the found `Text` carries space 2 and its place is the pen minus four pixels; the menu's texts then read 0.0006, 0.1746 and 0.3759 where the artists typed 0, 0.175 and 0.375.
- Symptom: the Twirl run backwards turns a box and a disc into a dash and a comma, and a twirled bar into a tilde, and calls them text.
  Cause: a single stroke or a blob is easy to reach by bending, and any shape may start a line.
  Fix: only a shape with form starts a line (see the reading), and after twirls the figure must be the glyph itself (0.90).
  Found by: seven control figures that are no text (two-shade noise, veins, cells, one blob, a box and a disc, a ring, a twirled bar), read before any text picture was trusted.
- Symptom: the first twirl taken out shreds the figure into fourteen pieces and the search stops there.
  Cause: the search was steered by the best glyph over any one piece, and one small piece looked like a letter.
  Fix: every piece's best glyph is weighted by the piece's ink.
- Symptom: the fitter's own drawing of the g is refused by the reading that allowed the original (0.89 against 0.99).
  Cause: the inner measure had moved a twirl's strength off the value that was read (0.390625 for 0.375) and kept a `Blur` of two passes where the artists used three.
  Fix: a twirl stays as read, and the `Blur` tries one to three passes; the found graph is then the artists' graph and its drawing reads as "g" at 0.99.
  Found by: running the reading on the fitter's own drawings, which is a test that can fail.
- Symptom: the fitter's own drawing of "info" reads "infn".
  Cause: on a line, the glyph whose box fitted best was taken, and n and o have the same box.
  Fix: the glyph that lies best over the shape is taken; how well its box fits counts for a tenth at most, which still tells o from O.
- Symptom: with the stand-in, a font page holds one letter more in its first row than with Times New Roman.
  Cause: a font page wraps where a letter's ink ends, and the stand-in's letters have the same advances but not the same ink.
  Fix: none in the code; the caption says which font drew, and a person who has the named font points the map at it.
- Symptom: one list of readings gives two answers for the same kind of picture.
  Cause: the fitter was rebuilt while a container was still working through the list; each picture starts the program anew, so the list was read half by the old program and half by the new.
  Fix: never rebuild while jobs run, and keep the program's SHA-256 beside its results.
- Symptom: a row of 108 boxes in a sign's text.
  Cause: the artists typed character 0x12, which no font has; Windows draws the font's missing-glyph box, and they used it as a row of boxes.
  Fix: the missing glyph is drawn, and the `text:` line says so (`no glyph for character 0x12`).

### The fifth round: any font, any character (milestone 1e)

Daniel's request (11 November 2026): the engine uses any font and any character, graphical fonts included, and the reading takes every free and open font into account.
werkkzeug3's own `Text` stays exactly as it was (version 1: 8-bit strings, a Windows font name, the font map of the fourth round); everything below is our extension of the operator, version 2, recorded as ours.

**Text version 2.**
A tenth word in the operator's data says the version; werkkzeug3's graphs have nine and read unchanged.
Version 2 has twelve words (the nine of werkkzeug3, then the version 2, the CPAL palette and the form) and three strings (the text as UTF-8, the font's key in the font index, the axis values).
It keeps version 1's geometry: the em square's height, the line's top at the font's Windows ascent, the space around letters, the two centring flags, the line skip; the line breaks only at a line feed.
`pixels/wztext2.c` draws it; what each part follows:

| what | the rule | where it is written |
|---|---|---|
| the font files | every format FreeType reads: TrueType (`glyf`, quadratic) and CFF or CFF2 (cubic) in OpenType files and collections (TTC, OTC), Type 1, CID, Type 42, PFR, Windows FNT, PCF, BDF, and the WOFF (zlib) and WOFF2 (Brotli) wrappers | OpenType 1.9.1 "OpenType font file" ("Font Collections"); "glyf" ("Bezier control points", on- and off-curve points; the curves are quadratic by FreeType Glyph Conventions, VI); "CFF2" ("sequences of cubic (3rd-order) Bézier curves"); FreeType's driver list |
| variable fonts | the operator's axis values (`wght=650 wdth=90`) set the instance through FreeType (outlines) and HarfBuzz (shaping, paint, metrics); an axis the font lacks, or a value outside the axis's range, is refused with a sentence | "fvar", VariationAxisRecord minValue, defaultValue, maxValue; "gvar" (outline deltas); "avar" (the normalisation); the specification has an application clamp an out-of-range value, the operator refuses it instead, so nothing is changed behind the person's back |
| colour | COLR version 0 layers and version 1 paint graphs with CPAL palettes, painted by HarfBuzz's raster library; the operator's colour is the foreground (palette index 0xFFFF), its palette word the CPAL palette (palette 0 the default; a palette the font lacks is refused) | "COLR" ("Version 1 supports ... gradient fills ... affine transformations and various blending modes"; "A palette entry index value of 0xFFFF ... the text foreground color"); "CPAL" ("The first palette, palette index 0, is the default palette") |
| SVG glyphs | drawn by plutosvg through FreeType's SVG hooks, at the em size, y down from the baseline | "SVG " ("the positive y-axis points downward ... y = 0 is the default horizontal baseline"; "Implementations must also support the currentColor keyword"); plutosvg's hooks pass no foreground colour, so currentColor is black, and the caption says so |
| colour bitmaps | CBDT (PNG formats 17, 18, 19) and sbix (PNG, JPEG, TIFF) decoded by FreeType with libpng, per strike | "CBDT", "CBLC" ("Each strike is defined by a BitmapSize record"), "sbix" |
| bitmap strikes | EBDT, PCF, BDF: the smallest strike at least as large as the em asked for, else the largest, each pixel laid as a block (nearest neighbour), so no pixel is invented; the caption names the strike and the size it was laid at | "EBDT", "EBLC" ("monochrome or grayscale bitmap glyph data"; "A set of bitmaps for a face at a given size is called a strike") |
| which form | the one the operator asks for (outline, COLR, SVG, colour bitmap, strike) or, in auto, the richest the glyph has: COLR, then SVG, then a colour bitmap, then the outline, then a strike; a form asked for that a glyph lacks is refused, never replaced | our rule |
| shaping | HarfBuzz 14.4 on the font's own tables (GSUB, GPOS; the shapers for Arabic, Indic, Thai and the others), FreeType's functions behind it for formats without OpenType tables; no language is set, so the result does not depend on the machine's locale | HarfBuzz's manual (`hb_buffer_set_script`: "Script is crucial for choosing the proper shaping behaviour") |
| direction | the Unicode Bidirectional Algorithm, SheenBidi 3.0.0: the paragraph level from the first strong character, the levels, the runs in visual order; HarfBuzz mirrors brackets in right-to-left runs | UAX #9 (Unicode 18.0.0, revision 52): P2, P3, X1 to X10, W1 to W7, N0 to N2, I1, I2, L1, L2 ("reverse any contiguous sequence of characters that are at that level or higher"), L4 |
| script runs | each bidirectional run split by script, Common and Inherited taking the surrounding script | UAX #24 (revision 41), 5.1 ("programs must resolve any of the special Script property values, such as Common, based on the context of the surrounding characters") |
| a missing glyph | a character the font's cmap does not map is drawn as the font's own missing glyph (glyph 0), and every such character is said with its code point | "cmap" ("should be mapped to glyph index 0 ... commonly known as .notdef") |

**The fonts: the machine's first, then every free and open font.**
`p2p fontindex SOURCE=FOLDER ...` writes one line per face of every font file under the folders: its key (family/style, `#2`, `#3` for later copies), file, face, source, family, style, version, format, outline kind, colour tables, axes, named instances, glyphs, characters and the Unicode blocks they fall in (Blocks.txt), designer, copyright, licence text and URL from the font's own `name` table (IDs 9, 0, 13, 14), and `fsType`.
The machine's own fonts come first: fontconfig's folders (`/usr/share/fonts`, `/usr/local/share/fonts`, `/usr/share/texmf`) are read in place and never copied; Microsoft's core fonts are installed on the person's machine by the font installer, so werkkzeug3's Arial, Times New Roman and Verdana draw with the real fonts where they are installed.
Without a font map, a werkkzeug3 name resolves to the machine's font of that family; only when it is not installed does a free font stand in (fontconfig's metric aliases: Liberation Sans for Arial, Liberation Serif for Times New Roman, Liberation Mono for Courier New; DejaVu Sans for Verdana, not metric-compatible), and the caption says so.
A font map (`WZ_FONTMAP`) still decides alone when it is given, which is how the fourth round's drawings are reproduced byte for byte.

The free collection (`src/fonts/`): Google Fonts' `ofl`, `apache` and `ufl` folders, fetched file by file at one commit and each checked against the git blob hash the repository's own tree states (`fetch_gf.py`); Debian's font packages in main, fetched by apt in a container (which checks each package against the signed index), unpacked one at a time, every font file kept only when its licence is on the list and its bytes are not already in the collection (`fetch_debian.py`, which reads the package's machine-readable copyright file and records every file either way).
The licence list: SIL Open Font License, Apache 2.0, Ubuntu Font Licence, the Bitstream Vera and DejaVu licences, GPL with the font exception, MIT, CC0, public domain (`licence.py`).
`classify.py` gives every face its class (the font's own name table first, the source's record beside it, disagreements written down) and writes the candidates: the machine's fonts whatever their licence, and the collection's fonts on the list; a face with the same family, style and version as an earlier source's is left out of the candidates and listed.

**The reading over every font.**
`p2p glyphindex` draws every candidate's every mapped character once, as its ink stretched to its own box at 16 by 16 bits, with the ink's proportions (outlines straight from the font units; colour glyphs and strikes as the renderer draws them, their silhouette).
For a figure, each piece and each group of pieces is laid over all of them at that coarse size (the bits that differ, glyphs of other proportions left out), the fonts whose glyphs lie closest over the pieces with form become the figure's candidates (32 of them), and each candidate is then read exactly as the fourth round read its three fonts: its nearest glyphs drawn from the font at 24 by 24, laid over the pieces, on lines, by the font's own advances.
Each reading is weighed as before (the share of the ink read, times how well its letters lie over their glyphs) and once more by its plainness: the share of its letter ink in its main script.
Of the readings that lie as well (within 0.01), the ones with the fewest texts take part (a line read whole is plainer than the same line in pieces), their letters are compared again at 48 by 48, each aligned to its own box, and the closest font is taken.
- **Groups.** A glyph of several pieces (an i, a CJK character's radicals, a hieroglyph's parts) is found by trying, around every piece, the pieces whose centres lie within a margin of its box (0.35 and 0.7 of its side), largest group first; a group is taken when it lies over one glyph of the font by 0.70 or more.
- **Plain characters.** A presentation variant is the same shape as its plain character stretched to its box, so it is never read: combining marks and modifier letters (general categories Mn, Me, Lm, Sk) and every character whose compatibility form (NFKC) is another (superscripts, fullwidth, mathematical letters, ligatures), from Unicode's data at build time. Letters of specialist blocks (Latin Extended-B, IPA and phonetic extensions, Latin Extended-D to -G, Cyrillic Extended-B to -D) are read only when they lie 0.10 closer than any plain letter.
- **One script.** A line's script is the one most of its letter ink is read in; a letter read in another script is read again as that script's best letter when one lies within 0.12 (Cherokee Ꭵ for i, Armenian ո for n). Latin, Greek and Cyrillic also share letters one glyph draws (A, Α, А): there only the letters no other of the three draws alike say which script a text is in, and the others are turned into that script's own letters when the font draws both alike (0.97 or more at 24 by 24, the same advance).
- **Close glyphs.** Glyphs that lie within 0.06 of the best over a piece (1 and l in a serif face) are compared again at 48 by 48.
- **Right to left.** A line read in a right-to-left script (UAX #9 classes R and AL) is stored in logical order, so the text draws through UAX #9 as it was read.
- **Colour glyphs.** When the two-shade reading finds no text, the figure is tried as colour glyphs on a flat ground: the ground is the border's commonest colour, the ink what differs from it; each piece's silhouette is laid over every colour glyph's (up to 400 of the closest, since every round face has the same silhouette), those are drawn in their own colours at 24 by 24, and the glyph whose silhouette (0.70) and colours (0.80) lie closest is taken.
- **Written back.** A text found in Arial, Times New Roman or Verdana as installed here, every letter in code page 1252, is written as werkkzeug3's own `Text` with the artists' name (an empty name for Arial); every other text as version 2 with the font's key.
- **Twirls.** The Twirl run backwards (fourth round) reads with the three names, since it tries thousands of bent pictures; the figure is read over every font once the twirls are out, and asks 0.95 there (a bent bar comes back as a tilde at 0.90 from some font).

```sh
sh pixels/build.sh BUILD FR FREETYPE LIBS        # LIBS: the unpacked sources of harfbuzz, sheenbidi, plutovg, plutosvg, libpng, zlib, brotli, and Blocks.txt
BUILD/p2p fontindex machine=/usr/share/fonts machine=/usr/local/share/fonts machine=/usr/share/texmf google=GF debian=DEB > index.tsv
python3 fonts/classify.py index.tsv GF DEB IX                         # IX/index-classified.tsv, IX/candidates.tsv, IX/summary.txt
WZ_FONTINDEX=IX/candidates.tsv BUILD/p2p glyphindex gi.0.bin 0 8      # eight of these side by side, then joined in the candidates' order
export WZ_FONTINDEX=IX/candidates.tsv WZ_GLYPHINDEX=IX/glyphs.bin WZ_FONTMAP=
BUILD/p2p render GRAPH.script OUT.ppm                                  # text: Noto Color Emoji Regular Version 2.055 (google): 5 from COLR (5 of them version 1 paint graphs)
BUILD/p2p fit PICTURE.ppm PRIOR OUT/x structure=text                  # glyph index: ... figure: ... as lines of FONT ... text "..." at x, y, height h
```

A typed version 2 `Text` (the form `text2script.py` and `script2text.py` take): `v1 Text v0 X Y HEIGHT WIDTH #COLOUR FLAGS SPACE INSPACE LINESKIP 2 PALETTE FORM "text" "Family/Style" "wght=650"`.

Traps of the fifth round:
- Symptom: every font of the index is a candidate with the same, largest worth, and the reading picks fonts that look nothing like the picture.
  Cause: `@popCount` of a `u64` is a 7-bit number in Zig; four of them added stay 7-bit and wrap in a fast build, so 128 differing bits count as none.
  Fix: widen each count to `u32` before adding.
  Found by: printing the candidates with their worth (all equal to the sum of the pieces' ink).
- Symptom: the reading stops with "cannot open" and nothing else, and a script that greps its output shows nothing at all.
  Cause: the container is given `WZ_GLYPHINDEX=` (set and empty); `getenv` returns an empty string, not null, and the empty path is opened.
  Fix: an empty setting means none (the fourth round's reading).
  Found by: running one reading directly instead of through the grep.
- Symptom: colour emoji from the CBDT font are stacked on one spot, a seventh of their width apart.
  Cause: an OpenType font with bitmaps only is not "scalable" for FreeType, and was given FreeType's own advance functions at a strike size.
  Fix: every OpenType font takes its advances from its own `hmtx` through HarfBuzz; FreeType's functions only for formats without OpenType tables (Type 1, PCF, BDF and the like).
- Symptom: the CBDT build of Noto Color Emoji sits about one em lower than the COLR build at the same place.
  Cause: none of ours: that build states a much taller Windows ascent, and the line's top is the Windows ascent (werkkzeug3's geometry); HarfBuzz's raster library and FreeType place the bitmap the same way.
  Found by: drawing both builds on one line.
- Symptom: a twirled bar is read as a tilde, "allowed as text".
  Cause: over every font a bent stroke finds a glyph that lies over it by 0.90, the fourth round's threshold after twirls.
  Fix: read over every font, a figure with its twirls out must reach 0.95 (the logo's g gives 0.99).
- Symptom: the plain menu text "options" is read as "opons".
  Cause: the group around the t took the i beside it, and "ti" lay over some glyph by 0.70.
  Fix: a group is one glyph only when it lies over a glyph better than its pieces lie over theirs (by 0.05).
  Found by: printing every group tried with its glyph and its pieces' own likeness.
- Symptom: bent credit texts come back as combining letters, superscripts, mathematical and fullwidth letters (ͨ ͪ ͣ ͦ, ᶸᵃ, 𝖙, ｉ).
  Cause: a glyph stretched to its own box has the same shape as its plain character, and among 17 million glyphs a presentation variant may lie a little closer over a bent letter.
  Fix: presentation variants are not read (general categories Mn, Me, Lm, Sk, and every character whose NFKC form is another, from Python's Unicode data at build time); letters of the specialist blocks (IPA, phonetic, Latin Extended-D and later, Cyrillic Extended) must lie 0.10 closer.
- Symptom: "Москва" comes back as "Mocквa".
  Cause: М, о, с and а are drawn by the same glyphs as M, o, c and a, and the shape decides nothing; counting all letters made Latin the majority.
  Fix: only letters no other of the three scripts draws alike decide the line's script.
- Symptom: "Nimbus 1951" comes back as "Nı", "˙mbus l95l".
  Cause: a narrow serif i lies over its glyph by 0.74 at 24 by 24, under the fourth round's 0.78 for two pieces, so the stem and the dot were read as a dotless i and a dot; 1 and l lie almost equally well.
  Fix: read over every font, two pieces are one glyph from 0.70; glyphs within 0.06 of the best are compared again at 48 by 48.
- Symptom: the true font of a picture loses to another by 0.01.
  Cause: clones of one design (Times, Helvetica and Arial) draw the same letters within a pixel at text sizes; at 48 by 48 the difference between them is under the noise of the picture's own pixels.
  Fix: none: the reading names a font of the right design, and says so; Arial and BPG Sans lie over the menu at 0.892 and 0.894.
- Symptom: in the real Arial, "start" is read as "sta".
  Cause: the r's arm and the t's bar touch at that size, so "rt" is one piece, and two letters are no glyph (the stand-in's letters did not touch).
  Fix: not built: splitting a piece into two glyphs.
- Symptom: the library and Docker image the earlier rounds ran in is gone ("pull access denied"), and the local `debian:forky` tag is an i386 image.
  Fix: tag the amd64 base by its digest under the lane's own name and use that.
- Symptom: `duplicate symbol: FT_Get_Font_Format` when FreeType's `ftfntfmt.c` is added to the build.
  Cause: `ftbase.c` already includes it.
- Symptom: SheenBidi's single-file build stops at `'API/SBAlgorithm.c' file not found`.
  Fix: `-DSB_CONFIG_UNITY -I Source` for that file alone.
- Symptom: Debian font packages whose files are free are kept out (`GPL-2+FE`, `SIL-1.1`, `BSD3|SIL`, `Hanazono-Font-License or Open-Font-License`), and cm-super's 368 fonts have "no copyright file".
  Cause: machine-readable copyright files name licences in many ways, and cm-super's documentation folder is a link to cm-super-minimal's.
  Fix: read choices (`or`, `|`) and both parts of an `and`; follow a documentation folder's link to the other package's copyright; fetch again what changed.
- Symptom: filigran_messing_font.tex draws differently from run to run, in the fourth round's program as in this one, while every operator up to its v50 draws the same.
  Cause: werkkzeug4's `HSCB` looks up `gammaTable[value >> 5]` and `[+1]` for channels above 0x7fff, past the 1,025 entries on the stack; its input holds such values after an `HSCB` with brightness 16.
  Fix: not ours to change in Farbrausch's code here; the regression compares that texture up to v50.

What the fifth round found (pictures of 512 by 512, one CPU thread each; the glyph index of 17,166,578 glyphs of 12,845 faces is 824 MB, built by eight processes in about four minutes):

- **The collection.** Google Fonts at one commit: 3,914 font files, 2.4 GB, every one matching the repository's own blob hash. Debian's font packages in main (667 of the 669 in section fonts, texlive's two left out for their size and their per-font licences): 8,064 font files kept from 369 packages, 3.1 GB; 7,462 files left out for their licence (X11's own licence wording, the GUST and LaTeX licences, plain GPL without the font exception, CC-BY, a package's own terms); 425 already in the collection. The index: 16,642 faces in 16,546 files, 3 files FreeType does not read. Candidates: the machine's 4,640 faces, 3,822 of Google Fonts and 4,383 of Debian; 3,797 faces left out as the same family, style and version as an earlier source's.
- **Formats met:** TrueType 10,718 faces, CFF 1,935, Type 1 473, PCF 2,226, BDF 30, TrueType in WOFF 581 and WOFF2 647, CFF in WOFF and WOFF2 32, CFF2 outlines 2, COLR version 1 18, COLR version 0 8, SVG 8 (all with COLR too), CBDT 3, EBDT 27, variable 835, faces of collections 120. No free font in the collection holds `sbix`, CID, PFR, Type 42 or Windows FNT, so those paths are read through FreeType and not yet drawn here.
- **Drawn by the engine** (the gallery): ornaments, icons by private-use characters from a WOFF2 file and by ligatures (Material Icons turns "home" into the house), Webdings' symbol cmap; one emoji text as COLR version 1, as the same font's SVG documents (a dark arc beside the smiling face that the COLR drawing lacks: plutosvg's), as a CBDT strike, and COLR version 0 (Bungee Color); Nabla in CPAL palettes 0, 3 and 6; Roboto Flex at nine instances of weight and width, Honk's paint graph moved by its axis, Cantarell's CFF2 outlines by weight; Arabic joined right to left, Devanagari conjuncts, Thai, Bengali, Tamil, Khmer, Myanmar, a Hebrew line with a number and an English word in UAX #9's order; Egyptian and Anatolian hieroglyphs, Japanese and Korean from one face of an OpenType collection, Chinese; Type 1, CFF, WOFF, a PCF and a BDF bitmap font and an EBDT strike laid pixel for pixel.
- **Found from the pixels alone** (thirteen pictures drawn from free fonts the fitter was not told about): the text, the font, the place and the size come back for ten: "Pixels" in Abril Fatface, "Αθήνα Σπάρτη" in GFS Didot, "Москва" in PT Serif (as two texts, "Москв" and "а"), four ornaments of Noto Sans Symbols 2 (the machine's older build), two Material Icons by their private-use characters, "漢字" in LXGW WenKai at 0.0991, 0.2498, height 0.2805 (drawn at 0.10, 0.25, 0.28), "שלום עולם" in logical order, two colour emoji in Noto Color Emoji's COLR build, "Nimbus 1951" in a Times design (Roman Uralic, not the Nimbus Roman it was drawn with), "Fixed 10x20" in the PCF font it was drawn with. Refused: Egyptian hieroglyphs (thin line drawings lie over their glyphs by 0.58 at 24 by 24), a joined Arabic word and a Devanagari word (each word is one piece of ink, and no single glyph of the font is that shape).
- **The thirty Text pictures of the fourth round**, drawn again with the machine's Arial, Times New Roman and Verdana: eleven read (the fourth round, three fonts: seven): chaos, code by, fiver2, giZMo, kb, ryg, sound by, wayfnder, kkrieger and part of "chapter", hund, and the menu's "options", "info" and "sta". The letters bent by a `Distort` come back clean, and now mostly whole: "giZ" and "Mo" (the fourth round had a stretched ¡ for the i), "hund" as one text. The font is never Arial: bent letters lie a little closer over other designs (Andika for giZMo, Red Rose for hund), and the plain menu is read in BPG Sans, whose Latin lies over Arial's within 0.002 at 48 by 48. The logo's g is refused here: with the real Arial the Twirl run backwards stops at another third twirl (strength 1.25 where the artists' was -0.375) and reaches 0.91, under the 0.95 asked over every font. "start" loses "rt": in the real Arial the r touches the t.
- **Controls:** eleven of twelve figures that are no text are refused, the fourth round's seven and five more. The square ring is read: U+FE12 of Chokokutai is exactly a square ring (likeness 1.00); with every character, it is a glyph.
- **Known answers with the real fonts:** the 112 Text textures draw with the machine's Arial 2.82, Times New Roman 2.82 and Verdana 2.35; against the stand-ins, 1.22 % of the pixels differ by more than 24 of 255 at the median, 17 textures not at all, the Verdana font page 32 %; the game's title screen shows the same four texts at the same places.
- **Nothing of the fourth round moved:** with its font map and no glyph index, the 112 drawings are byte for byte the fourth round's (one texture, filigran_messing_font.tex, draws differently from run to run in both programs: see the traps), the thirty readings and the seven found procedures are byte for byte, and the eleven of the third round too.

### Where the procedures stop (so far)

On .kkrieger's own textures, which are procedures, the reverse now gets the material at a glance for the plain noises, the regular repeats and the walls in a bond, and a recognisable drawing for the wood and the carved ornament; nothing is right close up.
On photographs it gets the colours and the kind of surface, and none of the marks that make the photograph that surface (speckles, drips, stains, cracks): those stay with the image, the last layer.
A glyph used as a shape is found where it stands as a figure on a flat ground: plain, or under up to three twirls that the search can take out one at a time; then the found procedure can be the artists' own.
Over every free and open font and the machine's own, any character is found the same way: Latin, Greek, Cyrillic, Hebrew, CJK characters of several pieces, ornaments, icons, bitmap fonts and colour emoji, with the font, the place and the size.
It stops at letters bent by a `Distort` (found clean, often whole, in another design), at four twirls and more, at letters under about 20 pixels, at a text stretched by more than a third, at a single stroke standing alone (an r, a t), at letters that touch (rt), at a word that is one piece of ink (joined Arabic, a Devanagari word under its headline), at thin line drawings (hieroglyphs), at a text over a material, and at telling clones of one design apart (Times, Helvetica and Arial copies draw the same letters within a pixel).
Not built yet: a `Distort` for ragged patch edges, for bent letters and for stones of uneven length, the rounded bevel of a stone, a text read over a material (its ink is a second colour, which the second-material reading already finds), a font page, rings (as against spirals), and the same method tile by tile on photographs.

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

OpenKTG: Fabian "ryg" Giesen. werkkzeug3: Dierk Ohlerich, Fabian Giesen, Thomas Mahlke, Christoph Muetze, Tammo Hinrichs and Bastian Zuehlke, as its licence names them. The pictures of the first run: Poly Haven, CC0. Relief mapping: Fábio Policarpo, Manuel M. Oliveira and João L. D. Comba (2005). Parallax occlusion mapping: Natalya Tatarchuk (2006). The stereo photographs of bark and ground: Robbie Sproule, CC BY 2.0, on Wikimedia Commons. MaterialX: the Academy Software Foundation's project, its standard nodes document by Doug Smythe and Jonathan Stone. The reverse from pixels: Yiwei Hu, Chengan He, Valentin Deschaintre, Julie Dorsey and Holly Rushmeier (2022) for the order (parts, layered noise, tuning together); Ariel Elnekave and Yair Weiss (2022) for comparing textures by their patches along random directions; Robert Hooke and T. A. Jeeves (1961) for direct search; the bridge to the operators started as lane 503's, from lane 473x's renderer. Text: the FreeType Project (David Turner, Robert Wilhelm, Werner Lemberg) for the font renderer; Liberation Fonts (SIL Open Font License 1.1) and DejaVu Fonts (Bitstream Vera licence) as the stand-ins named in the font map; .theprodukkt's capture of the title screen on Wikimedia Commons (BSD licence). Any font, any character: HarfBuzz (Behdad Esfahbod and the contributors its AUTHORS file names) for shaping and COLR painting; SheenBidi (Muhammad Tayyab Akram) for UAX #9 and the script runs; plutosvg and plutovg (Samuel Ugochukwu) for SVG glyphs; libpng, zlib (Jean-loup Gailly and Mark Adler) and Brotli for colour bitmaps, WOFF and WOFF2; the Unicode Consortium's UAX #9, UAX #24 and Blocks.txt; the Google Fonts repository and Debian's font packages (the Debian Fonts Team and each package's maintainers), every font credited from its own name table in the lane's evidence; Microsoft's core fonts read where the person installed them, never shipped.
