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

### The sixth round: high-resolution pictures, tile by tile, and glyphs as seeds (milestone 2)

Daniel (11 November 2026), on the fifth round: "the objective of leveraging other letters is not to be a copy of kkriger, but instead, expand what's possible - we aim small, but small today is not like the demo scene - we want a modern small, and with plenty of fonts as procedure seeds, we can do a lot ... letters are drawings with meanings, and when fonts are pure drawing, it's even better"; and "extend to reproduce advanced hi res textures, even if multiple tiles are needed".
The design it follows (his words of 10 November): the procedural part is tiled, each tile's procedure informed by the high-resolution texture's own pixels and its neighbours for the seams; the tiles are also the levels of detail; the image stays the last layer.

#### Tiles

**The tile size, and why.**
Tiles of 512 pixels at the picture's full size: 16 tiles for a 2048 pixel map.
- The fitter searches coarse to fine at 128, 256 and 512 pixels, and its readings were set and judged by eye at 512 (the third round, which Daniel passed), so a 512 tile is fitted at its own size and drawn at its own size, never resampled.
- A 512 pixel tile at full size holds a photograph's grain and pits at the size the person sees them close up.
- A repeat is often larger than a tile (a brick wall's 512 pixel tile holds one and a half bricks per row), so a tile never reads its own repeat: the repeat is read once on the whole picture and drawn at the tile's place (below).

**Three ways of drawing a photograph's tiles.**
Each gives the person another texture, so all three are kept as options.
1. **A procedure per tile**: the fitter of the earlier rounds on each tile on its own. Each tile finds its own operators, and neighbouring tiles become different kinds of surface (a lit relief of scales on one, plain noise on the next, stripes on the third): the eye sees the grid at once, blended seams or not. Four to six minutes per tile on one thread.
2. **One procedure, every value retuned per tile** (`from=WHOLE.script fromfree=1`): the procedure found on the whole picture (reduced to the tile's size) keeps its operators, and every value is retuned on the tile's own pixels, coarse to fine. Neighbouring tiles are mostly the same surface, but some drift: one tile of the rust lets its noise fall to the lowest frequency and draws one large drop, a tile of the floor turns to stripes.
3. **One procedure, its kind kept, retuned per tile** (`from=WHOLE.script`, the default proposed): as the second, but the whole-number values stay the whole picture's (a noise's frequency and octaves, the modes, a blur's passes), except a noise's seed, which may change, or every tile would repeat the same noise field. 8 to 20 seconds per tile.
What places, repeats or draws a shape (`GlowRect`, `Transform`, `TransformMul`, `Text`, `Twirl`) stays as found in the second and the third.

**The whole picture's repeat, drawn at a tile's place.**
`fit TILE.ppm PRIOR OUT structure=shape whole=WHOLE.ppm window=X,Y,SIDE` reads the tile as usual and takes the repeat (cells across and down, where the cell starts, its shapes, the bond, the joints) from the whole picture's reading; a seed file (`seeds=`) carries its own repeat.
For an axis where the whole repeats n times, a tile of side SIDE at X sees f = SIDE × n cells, and its point u lies at the cell coordinate u × f − o, with o = o_whole − X × n.
- **Periodic axis** (f of one or more): one cell is drawn in a picture of its own and `Transform` repeats it, with scale 1 / f and offset 0.5 f − o (werkkzeug's `Rotate` reads its input at (u − 0.5) / scale + offset).
- **Direct axis** (f under one): less than a cell lies across the tile, so the tile itself is the picture and every instance that reaches the tile is drawn at its own place, at (c + o + k) / f; through `Transform` a cell picture would be magnified (four times for an ornament's cell of 683 by 2048 pixels seen from a 512 pixel tile) and soft.
- **A bond**: the cell is one brick wide and two rows tall, the second row carried half the cell down and the bond's part of a brick sideways by `TransformMul` (mode 16, count 1); where a tile has less than a brick across or two rows down, the rows are drawn without the bond and the program says so.

**The rungs of a tile (the levels of detail).**
Each rung of a tile is a thinner version of the same tile's procedure, and each rung of the whole texture is every tile at that rung.
With one procedure retuned per tile, the rungs are the whole picture's own rungs, each retuned on the tile: one flat colour (13 bytes a tile), the noise between two colours (45), the procedure as found at 128 pixels, the whole procedure.
With a procedure per tile they are the fitter's own rungs: the flat colour, the noise, the procedure as found at 128 and at 256 pixels, the final one.

**The seams.**
A werkkzeug picture repeats, so a tile's procedure drawn past the tile's border continues itself, not its neighbour.
The composition (ours, with one value for the whole texture: the band's width) has two modes, each giving another result:
- **mixed** (for surfaces of noise): every tile is drawn 32 pixels past each border, and neighbours are mixed across the 64 pixel band with weights that rise and fall linearly and sum to one, keeping the texture's contrast: the weighted sum of each tile's departure from its own mean colour is divided by the root of the sum of the squared weights (the variance-preserving blend of Heitz and Neyret, 2018), where a plain average leaves a softer, greyer band;
- **colour-matched** (for shapes and seeds drawn at their place, which already meet at the border): every pixel keeps its own tile, and only the tiles' mean colours are mixed across the band; mixed drawings would lay a ghost of each tile's own repeat over its neighbour's shapes.
The sheets show the corner where four tiles meet, at 1:1, hard and composed.

```sh
python3 pixels/m2cut.py PICTURE.png TILES                                   # TILES/L0-0-0.ppm (the whole at 512), L1-*, L2-r-c.ppm (512 at full size), tiles.txt
BUILD/p2p fit TILES/L0-0-0.ppm PRIOR W/plain/L0-0-0                          # the whole picture's procedure and its rungs
BUILD/p2p fit TILES/L2-1-2.ppm PRIOR W/kc3/L2-1-2 from=W/plain/L0-0-0.script # one tile: the whole's procedure, its kind kept, retuned
BUILD/p2p fit TILES/L2-1-2.ppm PRIOR W/kc1/L2-1-2 from=W/plain/L0-0-0.r01.script   # the same tile's rung 1
BUILD/p2p fit TILES/L2-1-2.ppm PRIOR W/shape/L2-1-2 structure=shape whole=TILES/L0-0-0.ppm window=0.5,0.25,0.25
python3 pixels/m2run.py BUILD/p2p JOBS.txt 8                                 # many jobs, each in its own container; waits for all of them
sh pixels/m2render.sh BUILD/p2p W/kc3 RENDERS/kc3                            # level 0 at 2048, level 2 at 512, every rung at 512
python3 pixels/m2compose.py SCRATCH NAME kc FONT OUT 64 full                 # NAME-sheet.jpg, NAME-ladder.jpg, NAME-tiled.jpg, NAME.json
```

#### Glyphs as seeds

A glyph is a seed: a small, exact drawing a procedure calls by a few bytes (the font's key, the character, a place and a size), then repeats, masks, blurs and lights like any other shape.
Which font a seed comes from is not the measure: any glyph of any free or installed font that lies over the motif is a good seed, a look-alike as good as the original.
.kkrieger's own `Text` stays as it was.

**What triggers a seed.**
A seed is tried where the picture repeats (the repeat reading of the first round, on the whole picture) and the mean cell is a figure on a ground: repeating motifs, ornaments, rosettes, tiles' patterns, rivets, perforations, weave, scales, leaves and stars all arrive as a mean cell with ink.
- The mean cell, along the picture's colour axis, is split into two shades by Otsu's threshold; the separation (the variance between the two shades over the whole variance) must be 0.60 or more, and the smaller shade is the ink.
- The cell is turned so its first row and column hold the least ink, so the motif is not cut by the cell's border.
- The motif is all the ink of the turned cell; each piece holding 3 % of the ink or more is also read on its own (a flower and its leaves).

**The search** (`p2p seed WHOLE.ppm OUT.seed`, with the glyph index of the fifth round).
1. A coarse pass over every glyph of the index (17,166,578 silhouettes of 12,845 faces, 16 by 16 bits, outline forms): both pictures grown by one cell in the four directions and laid over each other; glyphs of other proportions (more than 0.27 apart in the logarithm of width over height) are left out; the 4,000 closest go on.
2. Each is drawn from its font at 24 by 24, stretched to its own box, and laid over the motif with the soft likeness: both pictures blurred by a box of five cells, twice, then the sum of the smaller of the two over the sum of the larger.
3. Drawings are preferred (Unicode general categories So and Sm, and private use, where icon fonts put their pictures): 0.03 of likeness; among glyphs that lie as well, the fewer bytes (0.0005 of likeness a byte).
4. The box and the disc `GlowRect` draws are laid over the motif the same way; a seed is offered when its glyph lies over the motif by 0.70 or more, and better than the box or the disc by 0.05.
5. The program's choice and its runners-up go into the seed file and are drawn by the engine, each stretched to the motif's box, on a candidates sheet (`m2seedsheet.py`); the person or the model looking chooses by eye (`m2seedpick.py`), as the visual check of the third round chooses a structure, and both choices are recorded.

**The build.**
A black `Flat`; the glyph drawn white by `Text` version 2 in its outline form, stretched to the motif's box, once per cell on periodic axes and once per instance on direct ones; the repeat's `Transform`; a `Flat` in the motif's colour; `Mask` lays it over the surface where the glyph is white.
The motif's and the ground's colours are the means of the picture's pixels on each side of the threshold.
A seed file may hold several seeds (one per piece); they share the repeat and are drawn into the same shape picture.
With `from=`, the seeds are laid at the tile's place over the whole picture's surface procedure, retuned on the tile.

**What a seed costs, and what the font's presence means.**
In the procedure a seed costs its key, not its outline: a version 2 `Text` operator is 12 words and three strings, 64 to 86 bytes with the font's key (`Symbola/Regular`, 15 bytes) and the character (one to four bytes).
The font must be present where the procedure is drawn: installed on the machine (the font index reads fontconfig's folders in place) or in the free collection the index was built from; a key the index does not hold is refused with a sentence, never replaced.
If the font had to travel with the procedure, the whole file weighs 27 KB to 5.2 MB; cut to the one glyph the seed calls (fontTools' subsetter: the glyph, its cmap entry and the tables a renderer needs), 300 to 720 bytes as WOFF2 (`m2fontweight.py`).

```sh
WZ_FONTINDEX=IX/candidates.tsv WZ_GLYPHINDEX=IX/glyphs.bin BUILD/p2p seed TILES/L0-0-0.ppm S/NAME.seed   # NAME.seed, NAME.seed.pieces, the cell and ink as PGM
python3 pixels/m2seedsheet.py prep S NAME && sh S/cands/render.sh BUILD/p2p && python3 pixels/m2seedsheet.py sheet S cands.jpg FONT NAME
python3 pixels/m2seedpick.py S/NAME.seed K S/NAME.chosen "why the eye took candidate K"
BUILD/p2p fit TILES/L2-1-1.ppm PRIOR W/kcs3/L2-1-1 from=W/plain/L0-0-0.script structure=seed seeds=S/NAME.chosen window=0.25,0.25,0.25
python3 pixels/m2fontweight.py IX/candidates.tsv "Symbola/Regular" 2745   # the font whole, and cut to the one glyph
```

#### What the sixth round found

Nine photographs at full size (2048 by 2048, CC0 from Poly Haven: the six of the earlier study and the rust, rusted metal and rock of the third round) and six textures with motifs (a patterned terracotta floor and a tread plate from Poly Haven, two ornament prints from ambientCG, and the floor of slabs and the brick wall again, with seeds); every sheet looked at before a word was written about it.

- **Repeats need the whole picture.** The brick wall reads its repeat on the whole picture and on its quarters and on one of its sixteen 512 pixel tiles; the floor of slabs and the two ornaments only on the whole picture (their tiles read patches and rings instead); the terracotta's cell (293 pixels) fits a tile and reads everywhere.
- **A procedure per tile is a patchwork.** On the first row of tiles of all nine photographs, neighbouring tiles are other surfaces (scales, stripes, lumps, plain noise side by side).
- **One procedure, its kind kept, retuned per tile, reads as one surface** on the coast, the concrete, the plaster, the rock and the rusted metal, with each tile's own colour; the bark keeps its colours (grey, the green of the moss) and loses its furrows, which the whole picture's procedure never had. Three faults remain and are not fixed: a relief's light stands over every tile at the same place, so a lit procedure (the rust) shows each tile as a cushion; a few tiles drift in hue (a purple and a green tint on the floor and on the concrete), because a noise's two colours are retuned channel by channel; and a tile draws the whole picture's octaves at its own scale, four times finer in the picture than on the whole (the frequencies are kept as numbers; shifting them by the window's scale is not built).
- **Seams.** A 64 pixel band shows the border at 1:1 as a change of grain; a 256 pixel band (half a tile) hides it at 1:1. At a glance a faint grid of tiles remains on some pictures, from each tile's own colour: the picture's local colour, in steps of a tile.
- **The ladder, for 16 tiles of a 2048 pixel photograph:** one flat colour per tile 208 bytes, the noise between two colours 720, the whole's procedure at 128 pixels 1.0 to 2.3 KB, the whole procedure 1.8 to 3.6 KB.
- **Against the fair baseline:** the picture's lower-resolution copies add 31 to 41 % to the photographs' JPEG (60 to 66 % to the flat ornament prints); the tiled procedures with the picture are 23.7 to 29.2 % smaller than the picture with its copies for the photographs, 23.6 to 39.3 % for the textures with seeds.
- **The second judge** (a model that saw only the four sheets, none of this text): of the three ways of drawing a row of tiles, the per-tile procedures were never the continuous one except on the coarse rust, where it also had the truest grain; every value retuned won on the coast, the concrete and the rock; the kind kept won on the floor, the plaster, the brick and the rusted metal; on the bark none was continuous. So the three stay options, and the kind kept is proposed as the default for the tiles where the eye judged both, with the free retune as the other choice.
- **Time, one CPU thread:** a tile retuned from the whole picture's procedure 8 to 20 seconds; a tile fitted on its own 4 to 6 minutes; the seed reading of a picture over the whole glyph index 2 to 4 seconds.

What the seeds made possible (the same tile without a seed and with one, on a sheet in the lane's evidence):

| texture | the seed | without a seed | with it |
|---|---|---|---|
| snowflakes on red | ❅ U+2745 of Symbola, chosen by eye (the measure put the helm ⎈ U+2388 of STIX Two Math first, 0.88 against 0.86) | white blobs of noise | the three snowflakes at their places, the arms thicker and without the branched tips; one procedure for the whole picture, 277 bytes, draws them |
| floor of slabs in two shades | ▞ U+259E of Murecho Thin, 1.00 | a cloud: one shape per cell and darker joints cannot draw a checker | the checker of slabs; the light slabs flat, the dark ones noise |
| brick wall, light mortar | ᆍ U+118D of Gothic A1 (two bars and an upright), chosen by eye over two harpoons | brick-coloured noise: the outline trick only darkens | rows of bricks with light mortar, too wide and too regular; the bond stays with the image |
| terracotta floor with black inserts | the box `GlowRect` draws (every glyph that lies as well costs more bytes) | joints, no inserts | the black inserts at their places |
| tread plate | ↘ U+2198 of Inconsolata UltraExpanded Black | dark noise | a patterned plate at a glance; arrows, not raised lozenges |
| poinsettias | refused by eye: a not-equal sign for the whole flower, a hand, a pig, a seedling and leaves for its pieces | white blobs | no seed |

Traps of the sixth round:
- Symptom: every 512 pixel tile of a brick wall and of a floor of slabs reads "repeats 1 by 1", plain only.
  Cause: a tile holds one and a half bricks per row, one slab: too few repeats for the repeat reading.
  Fix: read the repeat on the whole picture and draw it at the tile's place (`whole=`, `window=`).
  Found by: the readings of all 21 windows of the nine pictures (`readonly=1`): the brick wall reads its repeat at 2048 and 1024 pixels, never at 512.
- Symptom: the tiles of one photograph are different surfaces side by side (scales, stripes, lumps), and blended seams do not hide it.
  Cause: each tile's fit chooses its own operators (a relief kept on one, extra noises on another).
  Fix: one procedure for the whole picture, retuned per tile (`from=`).
  Found by: the first row of tiles of the nine pictures drawn side by side.
- Symptom: retuned per tile, one tile of the rust draws a single large drop, a tile of the floor turns to stripes.
  Cause: the tuning also moved the whole-number values (a noise's frequency fell to its lowest, a mode changed).
  Fix: keep the whole-number values as found on the whole picture, except a noise's seed; with the seed kept too, every tile would repeat the same noise field.
  Found by: the same first row, drawn for the freely retuned tiles.
- Symptom: a cell larger than the tile (an ornament's cell is 683 by 2048 pixels, a tile 512) would come out magnified and soft.
  Cause: `Transform` reads a cell picture of the tile's own size; a quarter of a cell across means four times the scale.
  Fix: on an axis with less than one cell across the tile, draw every instance at its own place.
  Found by: the arithmetic of the window before the first run (0.75 by 0.25 cells across the tile).
- Symptom: a blended seam lays a ghost of a snowflake's arm, or a strip of the slabs' joint, across the band.
  Cause: a tile drawn past its border continues its own repeat, not its neighbour; shapes drawn at their place already meet at the border.
  Fix: the colour-matched seam for shapes and seeds; the mixed seam only for surfaces of noise.
  Found by: the close-up at the corner of four tiles, hard and blended side by side.
- Symptom: the tiled rust looks like quilted panels, each tile brighter in its middle and darker at its border, and a 256 pixel band does not hide it.
  Cause: the whole picture's procedure lights its relief with `Bump`'s light at a place in the picture; drawn on a tile, the same light stands over every tile, so every tile is lit as a cushion of its own.
  Fix: not built: a tile's light must stand at the whole picture's place (moved by the window like a repeat) or come from a direction.
  Found by: the rust's sheet, and the second judge's words for it ("the 4x4 grid is plain, like quilted panels").
- Symptom: background jobs started with `( ... ) &` by a shell that then exits leave their output files empty, and the containers go on running.
  Cause: the docker client dies with the shell; the container does not.
  Fix: a runner that starts every job in its own container and waits for all of them (`m2run.py`); stop leftovers by your own container name prefix only.
  Found by: `docker ps` after the task said it had finished.
- Symptom: a sheet shows a black tile.
  Cause: the sheet was drawn while that tile's fit still ran.
  Fix: compose only when every tile's script exists; the composer lists what is missing.
- Symptom: the mortar of a photographed brick wall comes out darker than the bricks, where the photograph's is light.
  Cause: the outline trick of the third round multiplies, and a multiply only darkens; the bricks are of uneven length, so no bricks per row are read either, only rows.
  Fix: a seed whose ink is the light mortar (two bed joints and a head joint, a Hangul jamo here), laid by `Mask` in the mortar's own colour; the bond stays with the image.

Traps of the seeds:
- Symptom: for a snowflake the search offers a sun icon and a starfish, while the snowflake glyphs (❄ ❅ ❆) lie over it by only 0.29 to 0.47.
  Cause: the overlap pixel for pixel punishes thin strokes that run close but not on top of each other.
  Fix: the soft likeness (both pictures blurred, twice, by a box of five cells at 24 by 24); the snowflakes then lie over it by 0.79 to 0.89.
  Found by: laying ❄ ❅ ❆ ✶ of four fonts over the motif outside the program, then drawing the engine's candidates on a sheet.
- Symptom: the true look-alikes never reach the fine pass.
  Cause: the coarse pass took the 500 glyphs closest bit for bit; the snowflake glyphs are 65 to 108 of 256 bits away.
  Fix: grow both 16 by 16 pictures by one cell before laying them over each other, and take 4,000.
- Symptom: the mean cell of a tread plate is a soft diagonal band, and the seed is an arrow.
  Cause: the plate's lozenges lie in two directions; the repeat reading takes a cell of one lozenge and averages both directions into it.
  Fix: not built (a cell of two motifs, or a motif turned per row); the plate's raised lozenges stay with the image.
- Symptom: a flower with leaves gets a not-equal sign, or, one glyph per piece, a hand, a seedling and an arrow.
  Cause: no glyph of the index lies over a poinsettia's silhouette, and its leaves alone lie closest over letters and icons.
  Fix: none: the eye refuses both, and the flower stays with the image.
- Symptom: the motif is a box (the black squares between octagonal tiles), and a seed would draw it.
  Cause: a box glyph lies over it as well as `GlowRect` does.
  Fix: a seed must beat the box or the disc by 0.05; here `GlowRect` keeps it, in fewer bytes.
- Symptom: `fit ... seed=FILE` stops with "bad seed=".
  Cause: `seed` is the fitter's random seed already.
  Fix: the seed file is given as `seeds=`.
- Symptom: `type 'u3' cannot represent integer value '49'` at a sum of byte counts.
  Cause: `std.unicode.utf8Encode` returns a `u3`, and the sum takes the type of its first runtime operand.
  Fix: widen to `usize` before adding.
- Symptom: `function parameter shadows declaration of 'seed'`, `local constant shadows declaration of 'score'`.
  Cause: Zig refuses a name that hides a declaration of the file.
  Fix: give the file's own globals names no function uses (`seeds`, `nseeds`).

### The seventh round: modern operators, the whole picture first (milestone 2b)

Daniel (11 November 2026): "Opus was having a hard time understanding the goal moved from - let's make it work like they did - to - let's modernize and expand what's possible"; "many many effects are now regular and we have more to include into it"; "for now we are aiming the web, so, web gpu, web assembler you name it - all that my 3060 and amd igpu can do and up, starting also from a10 gpus"; on GPUs rounding differently: "it's ok, this is not a dataset, but a graphics thing".
The sixth round measured where werkkzeug's 2004 operators stop: at 111 to 224 bytes a tile the bark is a flat noise, the brick wall has no bricks, the checker needs a glyph to exist, the rust is quilted.
The method stays (pixels in, procedures out, tiles, ladder, seeds, the eye as judge); the operator set and the budget change: "modern small", kilobytes where they buy the surface, the bytes stated beside the picture's.

#### The three faults of the sixth round, fixed

The tile path of the sixth round (the whole picture's procedure retuned on each tile, `from=`) now takes the tile's window (`window=X,Y,SIDE`) and fixes three faults (`fix=0` gives the sixth round's tiles):
1. **A tile's noise has the picture's frequencies.** werkkzeug's `Perlin` draws 2^freq cells across whatever it is drawn on, so on a tile a quarter of the picture wide the same words drew the whole's octaves four times finer. The tile takes freq + log2(side); octaves coarser than one cell across the tile are dropped and said (`v0 Perlin: 2 octave(s) coarser than one cell across this tile are dropped`).
2. **The light stands at the whole picture's place.** `Bump`'s light position is in parts of the picture it is drawn on; it is moved by the window, its height scaled with it, and locked, so every tile is lit from the one lamp (the quilted rust is gone).
3. **The colour retune keeps hue.** Colours are retuned by brightness (every channel scaled alike) and saturation (every channel moved toward or away from their mean), never channel by channel; a grey stays grey (the purple and green tiles are gone).

#### The modern operators

Nine operators, each in its own file under [`pixels/ops/`](procedural-texture-fit/pixels/ops/) with its parameter table in the shape of Stereo Werkkzeug's operator table (kind, label, word, default, range, step, choices), so that table can take them; [`modern.zig`](procedural-texture-fit/pixels/modern.zig) lists them.
Every one carries a version word first (1 today): a drawing refuses a version it does not know, with a sentence.
They join werkkzeug3's operators in the same graph and the same script (`p2p kinds` prints every operator's packing), and the playback is the same `p2p render`.

| operator | what it draws | its parameters | how the fitter reads it from the pixels | bytes | source |
|---|---|---|---|---|---|
| `Noise` | fractal gradient noise over the whole picture: fbm, ridged, billowed; another frequency across than down (grain); the place warped by noise | kind, cells across, cells down, octaves, gain, warp, warp cells, seed, contrast | the kind by the skew of the detail (thin dark or light lines) after the drawing is put in the picture's order of values; ridged and billowed only where the picture's lines run clearly (structure-tensor coherence 0.65 or more); the first octave and the gain by the whole row of octave strengths (a Laplacian pyramid) made to agree; the stretch by the change across against down; the warp by how the lines bend | 41 | Perlin 1985 and 2002 (gradient noise, the improved fade); Musgrave in Ebert et al. (fbm, ridged); Quilez, "domain warping" |
| `Cells` | cellular noise: cracks (F2 - F1), stones and pebbles (a dome per cell with a gap), patches or scales (a shade per cell), optionally warped | kind, cells across, down, jitter, width, warp, warp cells, seed, variation | long thin dark pieces of the detail (6 times as long as wide, 24 pixels or more) over 0.015 of the picture: their spacing gives the cells, their width the crack width | 41 | Worley 1996 |
| `Tiles` | structure by distance: grid, bond, checker, hexagons, lozenges turned per cell, studs, octagons with diamond inserts, planks of uneven length, square tiles with upright inserts; joint, bevel, rounded corners, per-piece shade and jitter, warped edges; grey 0 in the joints, the piece's shade on its face, inserts at 1; the height in alpha | layout, pieces across, down, bond, joint, bevel, round, jitter, variation, seed, warp, warp cells, floor, size, phase across, down | the repeat of the first round, then every layout's mean cell laid over the picture's mean cell at every shift (the best correlation gives the layout, the pieces per cell and the place of the joints); lozenges only where the cell's edges run on the diagonals (0.12 or more: the tread plate 0.185, the others 0.04 to 0.08); the joint's width and bevel (and an insert's size) by the same laying, with at least 0.3 of the picture left as faces | 69 | Quilez's 2D distance functions (rounded box, rhombus); the hexagons as F2 - F1 on a lattice |
| `Ramp` | a gradient map of up to eight stops | stops, eight places and colours | the field's values at eight ranks and the picture's mean colour at the same ranks of its main colour axis (a histogram match); a structure's joints take their own measured colour first | 73 | the rank match of histogram specification |
| `Layer` | one material over another by a mask's soft threshold: mix, multiply, add, or the detail mode (the top's departure from mid grey added, for texture in a structure's faces); the height kept, mixed, raised, lowered or multiplied | colour mode, lo, hi, amount, height mode, height amount | a second material where the first round's reading finds colours off the main axis as one cluster; its patches by their size (the mask's correlation length), raggedness (edge per pixel inside) and coverage | 29 | werkkzeug's `Mask`, with the height carried |
| `Shade` | a material lit from a direction by its own height (Lambert), the slope in parts of the picture | direction across, down, up, depth, strength | on a structure, the picture's brightness regressed on the drawn relief's slopes (a fit share of 0.01 or more); else the light and dark sides of pits or stones; the depth by making the drawing's reading agree | 25 | Lambert's cosine law |
| `Scatter` | a seed placed many times on a jittered grid: a glyph drawn by `Text` (any font) or a soft disc stretched by an aspect; size, turn and shade each its own | cells across, down, density, size, size variation, turn, jitter, colour, colour variation, seed, height, softness, aspect, opacity, phase across, down | pits and specks: compact dark or light pieces of the detail, 8 or more of 2.5 pixels or more at 512 (read on a structure's faces only); stones: light pieces of 5 pixels or more at a coarser scale; a motif: the seed the eye chose in the sixth round | 69 | ours |
| `Wear` | cavity dirt, worn edges, drips running down from a source, growth from points, read from the relief or a mask | kind, radius, length, lo, hi, amount, colour, noise cells, noise amount, seed, gain | drips: the second material's mask runs 1.5 times longer down than across | 49 | ours |
| `Tint` | a tile's own brightness and saturation, weighted by a tent over the tile so neighbouring tints add up to a smooth field | tile left, top, side, brightness, saturation | measured: the tile's mean brightness and saturation against the whole procedure's drawing at the tile's window; laid where they differ by 3 % or 8 % | 25 | ours |

The rules every operator keeps, so a WGSL twin follows line for line and WebAssembly draws the same bytes:
- **A pure function of the place.** Places are parts of the whole picture (0 to 1, repeating); a drawing is a canvas showing a window of it (`render ... window=X,Y,SIDE`), so a tile is the same procedure drawn over a quarter of the picture. Integer frequencies repeat over the picture.
- **No maths library.** Only + - * /, sqrt and floor, which IEEE 754 rounds the same everywhere; the sixteen gradient directions are written out; a turn uses a polynomial sine and cosine; the hash is lowbias32 (Chris Wellons).
- **Bounded loops.** A cell search looks at 3 by 3 cells, a scatter at most 7 by 7, a drip at most its length.
- **Neighbourhoods on a margin.** `Shade` reads one pixel each way, `Wear` its radius or length; the canvas is drawn that much wider and cut, and the blur sums whole numbers (the 15-bit values), so a pixel's answer does not depend on where the canvas starts.
- **The proof:** for each of the thirteen pictures, the sixteen tiles of 512 drawn each through its own window and put together are the whole drawn at 2048, byte for byte (0 pixels differ), with `Shade`, `Scatter` and a glyph's `Text` inside.

#### The fit, the whole picture first

`p2p mfit WHOLE.ppm OUT [full=FULL.ppm] [seeds=CHOSEN] [light=0]` reads the whole picture at 512, builds the procedure layer by layer, each layer only where its reading allows it, and prints every reading with what it decided:
1. the surface's `Noise` and its `Ramp` (the colours at the same ranks);
2. a structure (`Tiles`, the noise laid into the faces by `Layer` in the detail mode, the amount chosen so the share of the faces' variation that lies between pieces agrees with the picture's), or a motif (`Scatter` of the seed's glyph drawn by `Text` on a 128 pixel stamp, the ground's colours read from the ground's pixels only);
3. a second material, drips, cracks, stones, pits, specks, the light, each by its reading;
4. with `full=`, the tiles: the whole procedure drawn at each tile's window at full size, and a `Tint` only where the tile's brightness or saturation differs from it.
Every layer is a rung (`OUT.rNN.script`): the procedure up to there, a thinner version of the final one. `OUT.whole.script` is the whole picture's procedure without the tiles' Tints.
No choice is made by the inner measure: where a reading cannot give a value directly, candidates are drawn and the one whose reading equals the picture's is taken.
What the eye refuses is an option: `light=0` leaves a read light off (the terracotta's light raised its joints into crosses on the sheet of the rungs).

```sh
sh pixels/build.sh BUILD FR FREETYPE LIBS                              # BUILD/p2p
BUILD/p2p mfit TILES/L0-0-0.ppm OUT/NAME full=FULL/NAME.ppm            # OUT/NAME.script, .whole.script, .rNN.script, .log
BUILD/p2p mfit TILES/L0-0-0.ppm OUT/NAME full=FULL/NAME.ppm seeds=NAME.chosen   # a figure on a ground: the sixth round's seed
BUILD/p2p render OUT/NAME.script NAME.ppm 11 height=NAME-h.pgm         # the whole at 2048 and its relief in 16 bits
BUILD/p2p render OUT/NAME.script NAME-t-1-2.ppm 9 window=0.5,0.25,0.25 # the tile of row 1, column 2 at 512: the same pixels
python3 pixels/m2b_renderset.py OUT NAME DRAWN native BUILD/p2p > set.sh   # the whole, its 16 tiles and its rungs
python3 pixels/m2b_sheets.py SCRATCH EVIDENCE FONT                     # overviews, sheets at 1:1, what each operator bought, the table
```

#### The WebAssembly build of the drawing path

`P2P_TARGET=wasm32-wasi sh pixels/build.sh BUILD-WASM FR FREETYPE LIBS` builds the same program (`p2p.wasm`, 21 MB) from the same source: Farbrausch's operators with the SSE2 stand-in of lanes 503 and 514 (`shim/portable/emmintrin.h`), the first WebAssembly processor with SIMD and without the saturating float-to-integer conversions (`-mcpu=mvp+simd128`, lane 514's finding), FreeType, HarfBuzz, plutosvg, libpng, zlib and Brotli for `Text`, and the modern operators.
It runs in wasmtime 50.0.1 with the font folders mapped: `wasmtime run --dir SCRATCH::SCRATCH --dir /usr/share/fonts::/usr/share/fonts --env WZ_FONTINDEX=... p2p.wasm render ...` (precompiled once with `wasmtime compile`).
The thirteen final procedures drawn natively and in WebAssembly, 262 pictures (the wholes at 2048 and their 16-bit heights, 208 tiles, 28 rungs), are the same bytes (`evidence/m2b/checksums.tsv` in the lane, SHA-256 beside SHA-256).
The maths: both builds take Zig's own (compiler-rt and musl's) for every function the operator code calls, linked into each program, and the modern operators call none; lane 514 carries musl 1.2.6's functions under names of its own, which a glibc build needs too.

#### What the fifteen gave (the seventh round's sheets, looked at before these words)

- **Now the surface at a glance:** the brick wall (bricks in a running bond, light mortar measured from its own pixels, each brick its own shade), the floor of slabs (the checker of two shades with its joints, no glyph needed), the terracotta (black upright inserts where four tiles meet, at their places, the joints between), the snowflakes (the seed's glyph three times, on a clean ground), the plaster, the concrete and the rust (multi-scale clouds in their colours, no quilting).
- **Nearly:** the coast (moss and sand in patches; no stones), the rock (mottled; no pits or wet patches), the bark (dark furrows running down, ridged and stretched; too regular, no moss, no knots), the tread plate (lozenges turned per cell at their places; too dark and flat, the lit edges missing).
- **Not the surface:** the rusted metal (marbled swirls where the picture has rust spots and drips), the poinsettias (the ground only: the eye refused every seed in the sixth round, so the flowers stay with the image).
- **Close up, nothing is the picture:** the brick faces are marbled instead of grained, joints are uniform, and every mark of the photographs (stains, pits, chips, moss, knots, drips, veins) stays with the image, the last layer.
- **Bytes:** the whole picture's procedure 114 to 383 bytes, the tiles' Tints 0 to 400 more (114 to 562 bytes in all, against milestone 2's 1,776 to 4,257); with the picture, 23.7 to 39.7 % smaller than the picture with its lower-resolution copies.
- **What each operator bought** (the sheet of the rungs): `Tiles` with `Ramp` made the bond, the checker and the inserts; `Scatter` with `Text` made the snowflakes; `Layer` laid the rusted metal's second colour; `Tint` evened tiles' brightness where they differed; the light (`Shade`) was read on the terracotta only and the eye left it off. `Cells` (cracks), `Wear` (drips), stones and the other `Tiles` layouts were read on none of the fifteen: their readings stayed under their thresholds, said in each log.

Traps of the seventh round:
- Symptom: every candidate layout reports that the cells agree -2.000 and the first is chosen.
  Cause: the search for the best shift started at -2 and, for an unsigned match, compared against the absolute value of the best so far (2), so nothing beat it.
  Fix: keep the best key apart from the best correlation. Found by: the candidates printed with their numbers.
- Symptom: a fitted structure does not draw ("a step of the procedure does not draw").
  Cause: the phase read from the shift was -1.8 pieces, outside the parameter's range.
  Fix: take the phase within the layout's period (a bond and a checker repeat every two pieces). Found by: turning on `say_refusals` in the fitter.
- Symptom: the typed form of a graph turns the modern light into werkkzeug's `Light` (11 values asked for 6 given).
  Cause: one name in two families; the converters and `opIndex` take the first.
  Fix: the modern light is `Shade`; no modern name repeats one of werkkzeug3's.
- Symptom: every photograph comes back as a uniform fine grain.
  Cause: the frequency was matched by crossings of a band of detail, which the finest octaves fill whatever the first octave is.
  Fix: match the whole row of octave strengths (the Laplacian pyramid) over the first octave and the gain together. Found by: the first octave chosen at 16 for every picture.
- Symptom: rusted metal comes back as orange worms.
  Cause: a ridged kind is closer by the detail's skew alone; spots and lines both skew.
  Fix: ridged and billowed are tried only where the picture's lines run clearly (coherence 0.65: bark 0.708; rusted metal 0.558, rock 0.413).
- Symptom: the terracotta's square inserts are drawn as lozenges.
  Cause: a large lozenge's ground lies over a dark square as well as an insert does, either sign.
  Fix: lozenges only where the cell's edges run on the diagonals; inserts laid by their grey, signed (read as darker than the tiles; a light insert is not read yet).
- Symptom: inserts dark brown with a dark ring around every joint.
  Cause: the inserts' value lay between the joints' and the faces', so every bevel passed through the insert colour, and the faces' texture moved the inserts' values.
  Fix: inserts at 1, above every piece, coloured by a `Layer` whose mask is the structure itself.
- Symptom: the joint scan makes the joints a quarter of a piece wide, or leaves no faces at all.
  Cause: a wide joint stands in for a larger insert; a layout of joints alone still correlates with dark squares.
  Fix: the insert's size is read with the joints, and a candidate must leave at least 0.3 of the picture as faces.
- Symptom: the poinsettias' ground gets bright green blotches from the tiles' Tints.
  Cause: the tile's brightness included the white flowers the procedure does not draw.
  Fix: where a motif stays with the image, a tile is measured on its ground only (0 of 16 tiles then differ).
- Symptom: hundreds of pits of one and a half pixels on every photograph.
  Cause: the detail's own grain passes a blob test.
  Fix: pits and specks need 2.5 pixels or more at 512; on a structure they are read on its faces only, and their colour among the faces.
- Symptom: the WebAssembly build stops in FreeType's and libpng's headers ("Setjmp/longjmp support requires Exception handling support").
  Cause: wasi-libc refuses `setjmp.h` without the exception extension.
  Fix: `wasm/setjmp.h` for that build only: `setjmp` returns 0, `longjmp` (a real function, since libpng takes its address) says which library jumped and stops; the bridge's own refusal by `longjmp` is left out there.
- Symptom: `WASI lacks a true mmap` in plutovg.
  Fix: `-D_WASI_EMULATED_MMAN` and `-lwasi-emulated-mman` (and the process-clock and signal emulations).
- Symptom: wasmtime refuses the module: "type mismatch: expected i32, found i64".
  Cause: `clock()` declared in Zig as returning `c_long`; wasi-libc's `clock_t` is `long long`.
  Fix: declare it as `i64` (the same on x86-64). Found by: listing the module's C functions declared by hand in Zig.
- Symptom: Zig's start code wants `root.main` natively, and exports `__main_argc_argv` itself for WASI when it finds one.
  Fix: the native root keeps `pub export fn main`; the WebAssembly root is `p2p_wasm.zig`, which has no `main` and exports the same function as `__main_argc_argv`.
- Symptom: the joints of the brick wall and the tread plate stay at the starting width, and the log says "the cells agree -1.000".
  Cause: the joint scan accepts only a shift under an eighth of the cell, and a shift of -1 pixel was counted as cw - 1; when nothing passed, the starting width stayed without a word.
  Fix: the shift's distance is taken either way (the brick wall's joints are then read: 0.02 of a brick, bevel 0.14), and where still no width agrees (the tread plate) the log says the starting width is kept, said and not chosen.
- Symptom: a render set draws nothing and every line says "No such file or directory".
  Cause: the native set was written with the arguments in the WebAssembly order.
  Fix: `m2b_renderset.py FITDIR NAME OUTDIR native|wasm BINARY`.

### The eighth round: close up with the budget, and the WebGPU path (milestone 2c)

Daniel agreed the seventh round ("milestone 2b - agreed") with its reading: a clear step, but the bark too regular, the rusted metal marbled where the picture is spotted with drips, nothing holding close up, and the budget not used.
This round lays what the eye misses at 1:1 as layers, each by its own reading, each a rung above the seventh round's whole-picture procedure, and draws every procedure in a browser on WebGPU.

#### Two views of the full-size picture, and a drawing read the same way

`p2p mfit ... full=FULL.ppm` now reads the full-size picture twice ([`close.zig`](procedural-texture-fit/pixels/close.zig)): C, its central half at 1:1 (grain, chipped edges, mortar, the run of furrows), and H, the whole at half size (spots and how they gather, stones, pits, patches).
Each view has its own main colour axis; a drawing's colours are put on the same axis, and the drawing is drawn in the same window (`drawWin`), so a value no reading gives directly is chosen where the drawing's reading equals the picture's.
`close=0` gives the seventh round's procedure; `off=grain,chips,mortar,patches,spots,halo,drips,furrows,knots,stones,pits` leaves out what the eye refused; `grainat=field` lays the grain before the Ramp instead of over the colours (each a different picture, so both paths stay).

| layer | what it draws | its reading (the threshold) | where it fired on the thirteen |
|---|---|---|---|
| grain | the surface's own noise continued one or two octaves finer, or a grain `Noise` of 128 cells and 4 octaves laid by `Layer` (detail) over the colours, its strength 0.1 to 2 (beyond an amount of 1, the noise's contrast) and its fall | the picture's 2, 4 and 8 pixel bands (a Laplacian pyramid) 0.70 or more stronger in log variance than the drawing's; the candidate whose bands and across-against-down ratio come closest; on a figure on a ground, the ground's own detail (values near the median) 1.4 times the drawn | bark, coast, concrete, plaster, rock, rust; not on the two ornaments (their grounds are flat); refused by eye on the floor of slabs |
| chips, each piece's grain and stain | `Tiles` version 2: a noise eats into the pieces' edges, and every piece reads the noise at its own offset, so no pattern crosses a joint | the joints' outline per pixel inside (the joints' side of a threshold 0.35 of the way from joints to faces, both blurred by 3) 1.2 times the drawn; grain and stain by the faces' detail at 1, 3 and 12 pixels | brick (chips 0.15, grain 1.0), terracotta (chips 0.15), metal plate (grain 0.5) |
| mortar | a `Noise` laid into the joints, and light specks (`Scatter` laid by `Layer` with the joints as its mask) | the joints hold 0.03 of the picture at 1:1 and stand half a spread of the faces apart; their spread twice the drawn; specks: 6 or more light marks of 10 pixels or more in the joints | brick |
| patches | a second colour through a ragged `Noise` | colours off the main axis by 0.05, grouped by the way they lean (three groups, fixed starting directions); a group of 0.03 of the whole whose mask, blurred by 2, lies in patches of 5 pixels or more | bark (the moss), coast, rock |
| wet | the surface multiplied by the wet patches' colour against the dry, through a `Noise` | over blocks of 32 pixels, brightness and detail agree 0.50 or more | concrete |
| spots, halo, runs | `Scatter` version 2 (clustered, rough, a darker core) in the spot's colour; `Wear` grow for the stain around them; `Wear` drips down; the surface's `Ramp` read again on the lighter half; the seventh round's marbled second material taken out | the darkest fifth of the whole, its granules joined (blurred by 2): 0.45 of it in 30 or more compact marks of 5 pixels or more, 2.2 spreads darker than the rest; how they gather (variance over mean of the counts on an 8 by 8 grid); the ring beside them stained 1.5 times as often as far from them; at 1:1 the darkest fifth alike 1.3 times further down than across | rusted metal |
| stones | `Scatter` version 2 of rough raised discs in the marks' colour, lit by `Shade` where their sides are | the lightest fifth, joined, with the spots' thresholds | coast |
| pits | `Scatter` version 2 of rough sunk discs, lit by `Shade` | in the whole, 3 or more dark compact marks of 40 pixels or more, 2.5 spreads darker, twice the drawn | bark, coast, brick, rock, terracotta; refused by eye on the floor |
| furrows | `Cells` version 2 cracks stretched the way the lines run, their width wandering | dark lines (blurred by 5, less their blur of 32, 0.8 of a spread darker) whose runs are 1.5 times longer one way (bark 1.78; the six other photographs 1.01 to 1.31) | bark, and refused by eye: thin wandering cracks, not furrows |
| knots | `Scatter` version 2 of rough dark ellipses | 3 to 40 dark compact marks of 300 pixels or more in the whole, 2.2 spreads darker | none in the end (rock at 1.6 spreads was a false one) |

The operators that changed carry version 2, and version 1 draws byte for byte as before (the seventh round's thirteen procedures redrawn: the same SHA-256): `Tiles` (chip, chip cells, grain, grain cells, grain octaves, stain, stain cells), `Scatter` (cluster cells, cluster, rough, rough cells, core), `Cells` (width variation, width cells), `Layer` (lo above hi: a falling mask).
A word count now follows the version word (`wordCount` in the operator's file, `modern.wordsFor`), so a version 1 node keeps its 17 words and its bytes.

What the thirteen gave (the sheets in the lane's evidence, looked at before these words, and a second judge who saw only the sheets): close up, 2c is closer than 2b on every photograph that took grain (the brick faces grainy instead of marbled, the bark, rock and rust rough instead of blurred, the mortar light and rough with specks); at a glance the grain is often too contrasty (concrete, plaster), the brick wall loses some of its bricks' colour variation and its mortar is too white, the coast's stones are flat cut-outs, the rusted metal has spots with a stain and runs where 2b had marbling but a yellow cast over the metal, the bark has no furrows or knots of its own and its moss is small flat blobs, and the terracotta's chips are faint.
The procedures stay small: 114 to 555 bytes for the whole picture, 114 to 892 with the tiles' Tints; the readings add what they find, and the budget of a few kilobytes was not needed by any of them.
What changes when the picture replaces its procedure (`m2c_blend.py`): the coarse look agrees (blocks of 256 pixels within 1.4 to 8.3 levels of 255 for the twelve but the poinsettias, whose flowers the procedure does not draw), the detail does not sit where the picture's does (10 to 38 levels per pixel on the photographs): a procedure is the same kind of surface, not the same marks.

#### The WebGPU path

Every modern operator has a WGSL twin beside its Zig file: [`ops/NAME.wgsl`](procedural-texture-fit/pixels/ops/), each appended to [`ops/common.wgsl`](procedural-texture-fit/pixels/ops/common.wgsl), which is `common.zig` line for line (the hash, the gradient table, the improved fade, the fractal sums with their octave cut, the warp, the polynomial sine, the canvas's places).
Kept in step by shape: the same parameter words in the same order (a uniform holds the canvas, the window, the level of detail and the 32 words), the same branches in the same order, a pixel held as werkkzeug's four 15-bit channels in two words and quantised exactly where the native operator quantises; `Wear`'s box blur is two passes (rows into a buffer, then columns and the drawing), its drips one.
A change to an operator's Zig file is a change to its WGSL file in the same commit; the check is the page's difference table against the native drawing (below).
The page ([`web/`](procedural-texture-fit/pixels/web/): `index.html`, `app.js`, `wasi.js`) parses the fitter's script, works out the canvas and its margin as `drawCanvas` does (in single precision), encodes every needed operator into one submission, reuses a buffer once its last reader is encoded, and draws the whole at 2048 and the sixteen 512 pixel tiles each through its own window.
A werkkzeug3 node (a seed's `Flat` and `Text`) is drawn by the WebAssembly build of the same program, run in the page through a WASI of seventeen calls over files held in memory, and handed to the GPU as the `Scatter`'s stamp; the same module draws every procedure on the processor beside the GPU.

```sh
python3 pixels/m2c_page.py FITDIR p2p.wasm PAGE            # the page, the procedures, the module, the seed's font cut
XVFB=1 FLAGS="--enable-features=Vulkan --use-angle=vulkan" sh pixels/web/run-browser.sh nvidia PAGE OUT "index.html?tag=rtx"
FLAGS="--enable-features=Vulkan --use-angle=vulkan" sh pixels/web/run-browser.sh amd PAGE OUT "index.html?tag=amd&wasm=0"
python3 pixels/m2c_gpudiff.py NATIVE OUT rtx               # largest difference, mean, share of pixels that differ
python3 pixels/m2c_gpusheet.py NATIVE EVIDENCE OUT:rtx OUT:amd   # the sheet at 1:1 and the timings table
```

Measured on the station (Debian chromium 156, Mesa's radv, NVIDIA 615.71.09): WebGPU against the native drawing, at most 1 level of 255 on 0.000 to 0.5 % of the pixels, on both GPUs, whole and tiles; the WebAssembly module in the page, the same bytes as the native program (221 of 221 SHA-256: 13 wholes and 208 tiles).
A whole at 2048 (median of three after a warm-up): RTX 3060 12 to 108 ms, the AMD iGPU (Renoir, 7 Vega units) 30 to 717 ms, the WebAssembly module on one processor thread 1.2 to 26 seconds; the heaviest everywhere is the rusted metal (drips read up to their length per pixel, and a `Scatter` that looks at 7 by 7 cells).
For a lighter GPU (the A10's Carrizo and Hainan, the floor Daniel set): draw only the tiles a view needs, at the rung it needs (the tiles are the levels of detail), with fewer octaves (`lod=`), and keep the drips short; the kit runs both GPUs at 2048 and at 1024 with six octaves.

The WGSL clauses the twins rely on (WGSL, W3C Candidate Recommendation Draft of 6 November 2026; WebGPU, of 15 September 2026):
- 6.2.3: "Expressions on concrete integer types that overflow produce a result that is modulo 2^bitwidth": the hash's products wrap as Zig's `*%`.
- 8.8, the remainder of a signed integer: "e1 - truncate(e1 ÷ e2) × e2 ... the result has the same sign as e1": Zig's `@mod` floors, so the twin's `wrapi` adds the divisor and takes the remainder again.
- 15.7.4.1: `x + y`, `x - y`, `x * y` "Correctly rounded"; `x / y` "2.5 ULP"; `sqrt(x)` "Inherited from 1.0 / inverseSqrt(x)", `inverseSqrt` "2 ULP"; and 15.7.5: "An implementation may fuse operations if the transformed expression is at least as accurate": the reasons a GPU's drawing may differ by a level where the native one rounds a division or a root otherwise, judged by eye (Daniel: "this is not a dataset, but a graphics thing").
- 16.2, Reserved Words: `'pass'` and `'layout'` are among them (a uniform's member and a local had to be renamed).
- WebGPU 3.4.4: "In a compute pass, each dispatch command ... is one usage scope": one operator's writes are seen by the next dispatch, so the whole procedure goes in one submission; 3.6.2: `maxStorageBufferBindingSize` defaults to 134217728 bytes (128 MiB), and a 2048 canvas with its margin is 34 MB in this layout (a 4096 one would pass the default).

Traps of the eighth round:
- Symptom: `vkCreateInstance` fails in a container with the RTX ("Could not get 'vkCreateInstance' via 'vk_icdGetInstanceProcAddr' for ICD libGLX_nvidia.so.0"), although CDI mounts every NVIDIA library.
  Cause: NVIDIA's Vulkan driver opens `libEGL.so.1` (glvnd) at run time, and a minimal image has none.
  Fix: install `libegl1`. Found by: `LD_DEBUG=files vulkaninfo`: `libEGL.so.1` is "dynamically loaded by libGLX_nvidia.so.0" with no "opening file" line after it.
- Symptom: headless Chromium (`--headless=new`) on the RTX offers WebGPU, but the adapter is SwiftShader (vendor google), while the Vulkan loader's log says it created a device on the RTX.
  Cause: NVIDIA's instance extensions have no `VK_EXT_headless_surface` (vulkaninfo's list), which the headless platform asks for.
  Fix: an Xvfb inside the container (its own display number, never the person's) with `--ozone-platform=x11 --enable-features=Vulkan --use-angle=vulkan`: the adapter is nvidia, ampere.
- Symptom: on the AMD iGPU the same Xvfb route gives no adapter ("No DRI3 support detected - required for presentation", "GrContext creation failed").
  Fix: on Mesa, headless with `--use-angle=vulkan --enable-features=Vulkan` (radv has the headless surface); the adapter is amd, gcn-5. Forky's Mesa names the manifest `radeon_icd.json`, not `radeon_icd.x86_64.json`.
- Symptom: "The profile appears to be in use by another Chromium process". Fix: a fresh `--user-data-dir` from `mktemp -d` for every run.
- Symptom: the snowflake drawn on WebGPU is narrower than the native one (253 levels on 12 % of the pixels), every other texture within one level.
  Cause: the page cut the seed's font to its one glyph, and werkkzeug3's `Text` works out a font's average width from the advances of the space and a to z (the older weighted rule of the fourth round).
  Fix: keep the space and a to z in the cut font (37 KB for Symbola). Found by: the native and WebGPU crops side by side.
- Symptom: a reading's "gathered" value is `nan` on every picture.
  Cause: `const B = @min(blocks, 16)` gives `B` the type `u5` (the smallest that holds 16), and `B * B` wraps to 0 in a fast build: no blocks, 0 / 0.
  Fix: `const B: usize = @min(blocks, 16)`. Found by: the function alone under `zig run` (a debug build), which panics "integer overflow" at `B * B`.
- Symptom: grain laid before the Ramp at the strength the bands ask for evens out the whole picture's coarse look (the concrete turned an even speckle) and puts white blotches in the ornaments' grounds.
  Cause: the Ramp maps ranks, and strong grain mixes the ranks of the coarse field; on a figure on a ground the motif's colours are among the Ramp's.
  Fix: the grain over the colours (detail) by default, `grainat=field` as the other path; on a figure on a ground, read the ground alone.
- Symptom: the faces' grain of `Tiles` shows as a dark rim along every piece and black joint lines.
  Cause: grain pulled a face below the floor value, into the range the Ramp gives the bevel.
  Fix: a face stays at or above the floor.
- Symptom: the spots' base comes out yellow, and the tiles' Tints push it further.
  Cause: the spots carry less of the picture's colour than its stains do, so a tile's saturation falls short and its Tint raises it over the metal too.
  Fix (partial): the base read on the lighter half, the stain reaching three spot radii at the ring's own share; the yellow cast is less, not gone.
- Symptom: a structure's mortar reading finds a spread of 0.23 and lays specks over half the bricks.
  Cause: the joints were read on the chipped structure, whose bitten corners count as mortar.
  Fix: read the joints on the structure as the seventh round drew it.
- Symptom: wet patches, moss or stones fire on the wrong pictures (a brick wall's second colour, a concrete's darker mottles as stones).
  Fix: patches, spots, stones, furrows and knots are not read on a laid structure; marks are counted only from a size up (`marks`: 10, 40, 80 or 300 pixels), never the grain between them.

### The ninth round: four procedures per picture, and the eye's verdicts on the eighth (milestone 2d)

Daniel, on the eighth round's sheets (11 November 2026), for plaster, rock, rust and rusted metal: "this is where one single tile is not enought - it's to fine grain detail - this means what? the current procedure canvas become one quarter of the final image, not more operations on top, but four different operations per quadrant, meaning, 4 simple procedures maped to one hi res image"; "each part can focus on completing the other".
And, per texture: the floor's joints "are gigantic, on the original they are very thin lines"; the tread plate's two seeds "are forming a line"; the terracotta needs "one tiny centralized square with surrounding trapezoids, larger side to the outside border"; the bricks have "too much mortar", are "too much granulated", and "mortar usually has a "u" shape to it in a depression"; the poinsettias: "there must be a font that has this type of drawing"; the snowflakes: "the inner losangles are nice, the lines crossing not nice".

#### Four procedures per picture: the `Quad`

[`ops/quad.zig`](procedural-texture-fit/pixels/ops/quad.zig) (and its WGSL twin) takes four whole procedures, each fitted to one quarter of the picture as a picture of its own (`mfit` on the quarter reduced to 512, `full=` the quarter at full size), and lays them together.
Each input is drawn on its own canvas: where the `Quad` shows the place x, y of the picture, input q is drawn at 2x - column, 2y - row, every canvas of one side and margin, so the `Quad` reads pixel k of each input under its own pixel k (`drawQuad` in `p2p.zig`, `drawQuadGpu` in the page).
A `Quad` is a procedure's last operator; one is allowed, its inputs hold none.
The four meet at the cross in the middle and at the picture's own edges (it repeats), across a band each side of the border (0.03 of the picture by default), by one of four seams, all kept as the person's choice:
- `cut`: each quarter alone up to its border (the cross shows as four squares);
- `mix`: the two (four at the corner) mixed linearly; the detail washes out in the band;
- `keep`: Eric Heitz and Fabrice Neyret's variance-preserving blend (2018); with four procedures whose noises are correlated it overshoots: a bright and dark blotch at the centre;
- `smooth` (the default, the best or equal best on every picture by the lane's eye and a second judge's): the coarse colour laid as one smooth field through the four quarters' mean colours (each at its quarter's centre, a smoothstep between them), and each quarter's departure from its own mean mixed linearly across the band; a quarter darker than its neighbour shades into it over the whole distance between their centres.

```sh
python3 pixels/m2d_quarters.py FULLDIR QUARTERS NAME...                          # QUARTERS/NAME/qR-C.full.ppm
BUILD/p2p mfit QUARTER512.ppm OUT/qR-C full=QUARTERS/NAME/qR-C.full.ppm seed=1000*(2R+C) close=0   # four simple procedures
BUILD/p2p quad NAME.script OUT/q0-0.whole.script OUT/q0-1.whole.script OUT/q1-0.whole.script OUT/q1-1.whole.script seam=smooth band=0.03
BUILD/p2p render NAME.script NAME.ppm 11                                          # the whole; window= draws any tile, the same pixels
```

`seed=N` moves every word labelled "seed" in the operators' tables by N as the fitter writes it (`mk` in `mfit.zig`); the default 0 writes what the eighth round wrote.
What it costs: four simple procedures are 485 to 1,449 bytes against 184 to 708 for one (the `Quad` itself 29 bytes); against the picture with its lower-resolution copies the gain does not move (23.7 to 29.2 % smaller either way, `evidence/m2d/table.md` in the lane).
What the eye saw (the second judge agreeing): rust coarse and plaster are nearer the picture as four (each quarter its own colours: the rust's dark upper half and lighter patches; the plaster's larger, softer patches), rock is not (a finer, even mottling), the rusted metal is not (four times the eighth round's marbling, or pale dots), the bark gets a quarter of another colour.
Laid structures and motifs do not split into quarters: a wall five bricks wide or three snowflakes across holds two and a half bricks or one and a half snowflakes a quarter, the quarters read different brick sizes or none, and the four lose the checker, the inserts and the bond: for them one procedure stays the default and the four are not drawn for the motifs (said in the table).
The seam is not where four procedures fail: the quarters differ in tone and scale, which a band cannot hide; "each part can focus on completing the other" is not yet built (a quarter does not read its neighbours).

#### The joints read again at 1:1

The scan at 512 cannot see a joint of one or two pixels at 2048: it starts at 0.02 of a piece (ten pixels on the floor's slabs).
`mfit ... full=` now reads the joints on the full-size picture (`jointsAtFull`): every pixel's signed distance to the nearest joint line, as the structure's words place it (the bond's rows moved as `Tiles` moves them, a quarter of a piece around every crossing left out), the grey summed per pixel of distance, horizontal and upright joints apart; then the profile's centre (which moves the joints' phase), its width at half depth (the joint), from half to a quarter depth (the bevel, never more than half the joint: a shadow or a stain beside a joint reaches further than the pieces' rounded edge), and the joints' colour in their core (from a direction whose place was read).
Floor tiles: 1.0 pixel at half depth (the joint 0.002 of a slab); terracotta 3.0 pixels, lighter than the tiles; bricks 20.6 pixels.
`joints=scan` keeps the scan's width.
A thinner joint grows the inserts (their visible half side is half their size less half the joint), so their size is moved by the joint's change; a corner is rounded at most twice the joint.

#### Tiles version 3: the hollow, pairs, framed tiles

- `hollow`: inside the joint the height rises as the square of the distance from its centre line to half the hollow at the pieces' edges (a "u" in a depression); the colour stays the joint's, so a light (`Shade`) shows it. Read by drawing hollows with a light from above and below and correlating the drawn profile across the horizontal joints with the picture's; on the bricks the flat joint agreed best (0.480 against 0.465 for the smallest hollow), so the hollow is the eye's: `on=hollow` takes the hollow whose profile agrees best and lays its light at the depth it was compared with, unless a light is read on the relief.
- `pairs` (layout 9): two lozenges in every cell, the second turned the other way and moved by its own offset; the tread plate's cell is one pair (13 across, 11 down where the repeat read 24 rows), the second lozenge half a cell across and down; read over the picture's mean cell of one pair, where the checker of the eighth round agrees 0.199 and the pair 0.833.
- `framed` (layout 10): the inserts layout's square tile cut into a small central square and four trapezoids by joints along the square's edges and the diagonals from its corners to the tile's corners. At 512 its inner joints are under a pixel and at full size they are thin and lighter than the tiles, so the inserts layout correlates better (0.831 against 0.822 for framed tiles at 1:1): `on=framed` is the eye's choice, the central square's size read (0.33 of the tile, where the picture's is 95 of 292 pixels).
Version 1 and 2 graphs draw byte for byte as before.

#### Grain, chips and the mortar's colours

- The faces' grain may not raise a band of the drawn faces above the picture's (or above the faces without grain, where they are above it already), with grain cells of 256, 512 and 1024 tried: the bricks took 0.75 of 1024 cells where the eighth round took 1.0 of 256 (Daniel: "too much granulated"); `grainfit=closest` gives the eighth round's choice.
- Chips are tried with finer noise cells too, and with joints read at 1:1 bite at most half the joint's width.
- The mortar's own colours: a `Ramp` along the joints' own main colour axis (their pixels' covariance, its first eigenvector), at the ranks of that axis, mixed into the joints by the amount whose middle-half spread agrees with the picture's (the tread plate's green and rust, the mortar's greys); on the tread plate, the terracotta and the bricks it took the largest amount tried, 1.00, and the bricks' mortar came out white and blotchy by eye: the picture's joints hold the shadow under each brick as well as the mortar's own colours.
- `on=spots` asks for the spots below their reading's thresholds (the rusted metal's quarters read 0.34 to 0.39 of the darkest fifth in marks, under 0.45); `marks=read` (default) reads the second material's and the spots' softness and how much they are laid from the darkest fifth's edge slope over its contrast; the rusted metal came out washed out (Daniel had asked for "more blur and blend on the more disperse darker areas"), `marks=fixed` gives the eighth round's.

#### The glyph index searched for a flower and a snowflake's parts

[`m2d_glyphsearch.py`](procedural-texture-fit/pixels/m2d_glyphsearch.py) reads every entry of the glyph index (17,166,578 glyphs of 48 bytes: font, character, width over height, form, pieces, and the ink on 16 by 16 cells) against the motif laid on the same cells, in about 7 seconds with numpy's `bitwise_count`: the cells both hold over the cells either holds, less a tenth of how far the widths over heights differ; `rotations=N` turns the motif; `part=ring` or `part=centre` compare only the cells outside or inside a disc (a snowflake's tips, its middle); `crop=` takes a part of the motif (one arm's tip); `tolerant=1` counts cells a cell apart as meeting; `drawings=1` keeps the characters that are drawings (Unicode's So and Sm, private use); `names=REGEX` keeps those whose Unicode name matches, ranked by the pixels alone.
[`m2d_glyphsheet.py`](procedural-texture-fit/pixels/m2d_glyphsheet.py) draws the nearest characters with the engine's own `Text` beside the motif; [`m2d_miniindex.py`](procedural-texture-fit/pixels/m2d_miniindex.py) makes a glyph index of the characters the eye picked, so `p2p seed` lays them over the motif and writes their drawing's words; [`m2d_seedbelow.py`](procedural-texture-fit/pixels/m2d_seedbelow.py) writes the eye's choice where the reading found none above its threshold, saying so.
What the free fonts and the machine's fonts hold: no poinsettia; among drawings named as flowers, leaves and rosettes the nearest are a rosette of petals in a ring (U+1F3F6, Noto Sans Symbols 2), a florette (U+273F) and a maple leaf (U+1F341, Symbola): the rosette drawn as the motif is the first flower the procedure draws, round where the picture's bracts are pointed.
For the snowflake: whole, its middle and its rim bring six-pointed stars, outlined hexagrams, the dharma wheel and asterisks; one arm's tip brings arrows and crosses, none with the barbed tip. The outlined hexagram the seed reading laid best (U+F0ACA of Material Design Icons) has no lines crossing the middle, and no arms or tips either: by the second judge less of a snowflake than the eighth round's, so the eighth round's seed stays the default and the hexagram is the other path.

Traps of the ninth round:
- Symptom: four procedures per picture show a two by two repetition at a glance.
  Cause: the four quarters' procedures were fitted with the same seed words, so each draws the same noise instance at its own scale.
  Fix: `seed=` per quarter (0, 1000, 2000, 3000). Found by: the sheet of the four, where the same blotch stood in every quarter.
- Symptom: a bright and dark blotch where the four quarters meet with `seam=keep`.
  Cause: the variance-preserving blend divides by the root of the sum of the squared weights (one half at the corner), which assumes uncorrelated inputs; the four noises are correlated (similar frequencies, and the same seeds before the fix above).
  Fix: `seam=smooth`. Found by: the 1:1 sheet of the cross, seam by seam.
- Symptom: a Tiles bond drawn through a window beyond 0 to 1 shows other shades a picture's height lower (162 levels of 255).
  Cause: the bond's rows shift by bond times the row, and the piece's hash wraps the column by the pieces across; after a whole picture of rows the shift is not a multiple of them.
  Fix: a `Quad` draws each quarter on its own canvas (2x - column), never on the repeat. Found by: drawing a procedure at window=0,0,2 and comparing its quarters with window=0,0,1.
- Symptom: `refused: v12 Shade: Shade: no memory for a 520x520 picture` late in a fit.
  Cause: the joints' reading at 1:1 draws ten candidates at 2048, and the memory of drawn pictures (3 GB) keeps them.
  Fix: empty that memory when the reading ends (`P.cacheClear()`). Found by: the fit's last lines.
- Symptom: after the joints were read at 1:1 the terracotta's inserts came out brown and larger (98 pixels became 125).
  Cause: an insert's visible half side is half its size less half the joint; a thinner joint grew it over the tiles.
  Fix: the size moved by the joint's change. Found by: measuring the drawn inserts' runs of columns against the picture's.
- Symptom: the terracotta's joints at 1:1 read brown, though they are light grey lines.
  Cause: the horizontal joints' place was not read (no extremum stood out of the faces), and their pixels, off the line, joined the joints' colour.
  Fix: the colour from the directions whose place was read. Found by: a profile across the drawn horizontal joints, flat where the picture has a line.
- Symptom: on a structure with narrow edges, the pits' light draws black outlines round every brick.
  Cause: the light's depth read on the pits is steep on a bevel of a few pixels.
  Fix: on a structure whose joints were read at 1:1 the pits stay colour only; the hollow's light keeps its compared depth. The bricks still show black at chipped edges under the hollow's light: not fixed.
- Symptom: `type 'u3' cannot represent integer value '16'`.
  Cause: `@min(v, 255)` has the type u8, and a u8 shifted takes a u3 shift.
  Fix: `@as(u32, @min(v, 255)) << 16`.
- Symptom: `expected ';' or 'else' after statement` at a nested loop.
  Cause: `for (a) |x| for (b) |y| { ... }` is an expression statement.
  Fix: end it with `;`.
- Symptom: the glyph search by strict cells finds CJK characters for a snowflake's middle and bells for a poinsettia.
  Cause: 16 by 16 cells of dense ink match any dense character; a thin line drawn a cell apart never meets.
  Fix: `drawings=1`, `tolerant=1`, and for a flower `names=`; the ranking stays the pixels'.
- Symptom: `ValueError: chr() arg not in range(0x110000)` with `names=`.
  Cause: glyphs a font maps to no character carry their glyph number past Unicode's range.
  Fix: such entries are not characters: skipped.

### Where the procedures stop (so far)

On .kkrieger's own textures, which are procedures, the reverse now gets the material at a glance for the plain noises, the regular repeats and the walls in a bond, and a recognisable drawing for the wood and the carved ornament; nothing is right close up.
On photographs it gets the colours and the kind of surface, and none of the marks that make the photograph that surface (speckles, drips, stains, cracks): those stay with the image, the last layer.
A glyph used as a shape is found where it stands as a figure on a flat ground: plain, or under up to three twirls that the search can take out one at a time; then the found procedure can be the artists' own.
Over every free and open font and the machine's own, any character is found the same way: Latin, Greek, Cyrillic, Hebrew, CJK characters of several pieces, ornaments, icons, bitmap fonts and colour emoji, with the font, the place and the size.
It stops at letters bent by a `Distort` (found clean, often whole, in another design), at four twirls and more, at letters under about 20 pixels, at a text stretched by more than a third, at a single stroke standing alone (an r, a t), at letters that touch (rt), at a word that is one piece of ink (joined Arabic, a Devanagari word under its headline), at thin line drawings (hieroglyphs), at a text over a material, and at telling clones of one design apart (Times, Helvetica and Arial copies draw the same letters within a pixel).
On photographs at full size, tile by tile, one procedure retuned per tile gives each part of the picture its own colours and grain, and the whole stays one surface where the second judge and the eye agree (coast, concrete, plaster, rock, rusted metal); the bark's furrows and knots, the coast's stones, the rock's pits and cracks, the rust's stains, the rusted metal's drips, a wall's bond and a slab's veins stay with the image, the last layer.
Where a picture repeats a motif, a glyph found over the whole index draws it at every place in a few bytes (snowflakes, a checker of slabs, a wall's mortar), and the box `GlowRect` draws where the motif is a box; a motif no glyph lies over (a poinsettia), or a cell that averages two motifs (a tread plate's lozenges in two directions), stays with the image.
With the modern operators of the seventh round, one procedure for the whole picture draws any tile at its own window with no seam (the tiles put together are the whole, byte for byte, natively and in WebAssembly), and the laid surfaces come back from their pixels in their layout: bricks in a bond with their mortar's colour, a checker of slabs, square inserts where four tiles meet, lozenges turned per cell, and a motif scattered from its glyph; noise-like photographs come back as their colours in clouds of the right scales, a grain that runs one way as ridged and stretched noise.
They stop at the marks: stains, pits, chips, moss, knots, drips, veins and the grain inside a brick stay with the image; rust spots come back as swirls; a motif no glyph lies over (the poinsettias) stays with the image whole.
Close up (the eighth round), each photograph takes the grain its pictures' bands ask for, a laid surface its chips, its pieces' own grain and its mortar's specks, the rusted metal its spots with a stain and runs, the coast its stones, and the procedure is drawn on WebGPU within a level of the native drawing; the marks themselves (where a furrow, a knot, a stain or a stone is) stay with the image: the procedure gives the same kind of surface, and the image, arriving, puts its marks in their places.
Four procedures per picture (the ninth round) give each quarter its own colours and scales and meet without a seam at 1:1 (`seam=smooth`); they help where a picture's coarse colour changes across it (rust, plaster), not where its quarters differ in kind or where a structure's repeat does not divide into quarters; laid structures now read their joints at 1:1 (thin joints, framed tiles, a tread plate's two seeds apart), while the bricks' mortar, lit hollow and chipped edges are not yet right by eye, and no free font holds a poinsettia.
Not built yet: a `Distort` for bent letters, a text read over a material, a font page, rings (as against spirals), a cell of two motifs, a light insert, and readings for the operators no picture of the fifteen took (cracks, drips, stones, hexagons, studs, planks).

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

OpenKTG: Fabian "ryg" Giesen. werkkzeug3: Dierk Ohlerich, Fabian Giesen, Thomas Mahlke, Christoph Muetze, Tammo Hinrichs and Bastian Zuehlke, as its licence names them. The pictures of the first run: Poly Haven, CC0. Relief mapping: Fábio Policarpo, Manuel M. Oliveira and João L. D. Comba (2005). Parallax occlusion mapping: Natalya Tatarchuk (2006). The stereo photographs of bark and ground: Robbie Sproule, CC BY 2.0, on Wikimedia Commons. MaterialX: the Academy Software Foundation's project, its standard nodes document by Doug Smythe and Jonathan Stone. The reverse from pixels: Yiwei Hu, Chengan He, Valentin Deschaintre, Julie Dorsey and Holly Rushmeier (2022) for the order (parts, layered noise, tuning together); Ariel Elnekave and Yair Weiss (2022) for comparing textures by their patches along random directions; Robert Hooke and T. A. Jeeves (1961) for direct search; the bridge to the operators started as lane 503's, from lane 473x's renderer. Text: the FreeType Project (David Turner, Robert Wilhelm, Werner Lemberg) for the font renderer; Liberation Fonts (SIL Open Font License 1.1) and DejaVu Fonts (Bitstream Vera licence) as the stand-ins named in the font map; .theprodukkt's capture of the title screen on Wikimedia Commons (BSD licence). Any font, any character: HarfBuzz (Behdad Esfahbod and the contributors its AUTHORS file names) for shaping and COLR painting; SheenBidi (Muhammad Tayyab Akram) for UAX #9 and the script runs; plutosvg and plutovg (Samuel Ugochukwu) for SVG glyphs; libpng, zlib (Jean-loup Gailly and Mark Adler) and Brotli for colour bitmaps, WOFF and WOFF2; the Unicode Consortium's UAX #9, UAX #24 and Blocks.txt; the Google Fonts repository and Debian's font packages (the Debian Fonts Team and each package's maintainers), every font credited from its own name table in the lane's evidence; Microsoft's core fonts read where the person installed them, never shipped. Tiles and seeds: the variance-preserving blend of Eric Heitz and Fabrice Neyret (2018); Otsu's threshold (Nobuyuki Otsu, 1979); fontTools (MIT licence, copyright Just van Rossum, as its LICENSE states) for cutting a font to one glyph; the pictures of the sixth round from Poly Haven (Rob Tuytel; Dimitrios Savva and Rico Cilliers; Amal Kumar) and ambientCG, all CC0; the seeds' fonts as their own name tables credit them: Symbola (George Douros), Murecho (Neil Summerour), Gothic A1 (HanYang I&C), Inconsolata (Raph Levien, Cyreal, Brenton Simpson). Modern operators (seventh round, written from the texts, no code copied): Ken Perlin, "An Image Synthesizer" (SIGGRAPH 1985) and "Improving Noise" (SIGGRAPH 2002); F. Kenton Musgrave in Ebert, Musgrave, Peachey, Perlin and Worley, "Texturing and Modeling: A Procedural Approach" (fractal sums, ridged multifractals); Steven Worley, "A Cellular Texture Basis Function" (SIGGRAPH 1996); Inigo Quilez's articles on domain warping and 2D distance functions (iquilezles.org); Chris Wellons's lowbias32 hash ("Prospecting for Hash Functions", public domain); Peter Burt and Edward Adelson's Laplacian pyramid (1983) for the strength per octave; Josef Bigun and Gösta Granlund (1987) and Michael Kass and Andrew Witkin (1987) for the structure tensor. The WebAssembly build: the SSE2 stand-in written for lane 503 and carried by lane 514 (Daniel Campos Ramos with Claude), lane 514's findings on the saturating conversion and WASI's entry; wasi-libc's emulations (the WebAssembly project); wasmtime 50.0.1 (the Bytecode Alliance, Apache-2.0 with the LLVM exception) to run it, not shipped. The close-up layers and the WebGPU path (eighth round): the W3C GPU for the Web Working Group's WGSL and WebGPU specifications (the clauses quoted above); Debian's Chromium (the Chromium project) and Mesa's radv in the test container; NVIDIA's driver through the NVIDIA Container Toolkit's CDI; fontTools again to cut the seed's font. Four procedures per picture (ninth round): Eric Heitz and Fabrice Neyret's variance-preserving blend (2018), and Brent Burley's paper on it (2019), as OpenImageIO's maketx documentation cites them (the corpus's lead); the glyphs drawn as motifs, as their own name tables or Debian's copyright files credit them: Noto Sans Symbols 2 (the Monotype Design Team, the Noto Project Authors, SIL Open Font License 1.1), Material Design Icons (the Pictogrammers Icon Group, Debian's fonts-materialdesignicons-legacy, read where the machine has it), Diphylleia (Minha Hyung, the Diphylleia Project Authors, OFL 1.1), Symbola (George Douros); the Unicode Consortium's character names and categories (Python's unicodedata).
