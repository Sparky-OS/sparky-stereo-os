# A procedure fitted to a bitmap, and what is left for the image

Written on 2026-11-10 (ORDER 473v), as a study for [Dynamic Procedural Foveated Rendering](../../../docs/dynamic-procedural-foveated-rendering.md), which renders procedures first and the image last and assumes the procedure exists.
Most assets are bitmaps, so this asks the other direction: how much of a bitmap a program can turn into a small procedure by itself, and how many bytes the image must still carry.
It is a measurement method with its first numbers, not a renderer and not a DPFR implementation.

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

Daniel's correction of the first reading (2026-11-10): a traditional asset carries the picture in several resolutions, which is where the procedure is meant to act, so procedure plus picture against the picture alone is not a fair comparison.
A traditional asset ships the picture and its lower-resolution copies (a mip chain, or separate versions per device); DPFR ships a small procedure and the single picture, and the procedure stands where those copies were.
Measured on the same six pictures with [`chain_sizes.py`](procedural-texture-fit/chain_sizes.py) (box-averaged levels, JPEG quality 90):

- The lower-resolution copies down to 1 pixel added 31.1 to 41.4 % to the picture's bytes (29.1 to 38.6 % for two device copies at 1024 and 512; 31.0 to 38.1 % lossless as PNG).
- The procedure costs 57 bytes (OpenKTG noise) to 13,315 bytes (1,024 waves), under 1 % of the picture.
- So the procedure and the one picture were 24 to 29 % smaller than the picture with its full chain.

What the person sees differs in one place: before the picture arrives, a traditional asset shows a blurred copy of the picture, and DPFR shows the procedure, which is the material (its spectrum and colours) and is pixel-exact only up to about 64 pixels for a fitted photo (exact at every size for content authored as a procedure).
Once the picture arrives, the device makes its lower levels from it.
The asset is the procedure plus the single picture, never a difference image.
Not measured: GPU texture formats with their own chains (KTX2, BCn), AVIF and JPEG XL, and how the change from material to picture looks.

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

OpenKTG: Fabian "ryg" Giesen. werkkzeug3: Dierk Ohlerich, Fabian Giesen, Thomas Mahlke, Christoph Muetze, Tammo Hinrichs and Bastian Zuehlke, as its licence names them. The pictures of the first run: Poly Haven, CC0. MaterialX: the Academy Software Foundation's project, its standard nodes document by Doug Smythe and Jonathan Stone.
