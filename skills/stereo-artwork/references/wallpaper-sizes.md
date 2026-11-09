# Wallpaper sizes for Plasma's Image wallpaper

Recipe (ORDER 456): ship each wallpaper package's picture in the sizes Plasma chooses from, as downscales of the one source.

## How Plasma picks (plasma-workspace 6.7.4, wallpapers/image/plugin/finder/packagefinder.cpp)

`WallpaperPackage::findPreferredImageInPackage` reads each file name in `contents/images` as `WIDTHxHEIGHT` and takes the lowest score:

```
distance = |candidateAspect - screenAspect| * 25000 + delta
delta    = width - screenWidth, or (screenWidth - width) * 2 when the candidate is smaller (penalty for scaling up)
```

The screen size is the primary screen's size times its device pixel ratio; an empty size means 1920x1080.
A file name that is not `WxH` is skipped.
With one picture only, every screen decodes that picture whole: QML's `Image` with `sourceSize` still reads the full PNG, because the PNG handler cannot scale while reading (QImageReader scales after the read).

## What KDE ships

Debian testing plasma-workspace-wallpapers 4:6.7.4-1: the new Plasma 6 wallpapers carry one 5120x2880 picture (PNG or JPG) and a portrait one; only the older ones (Autumn and the like) have 1280x800 to 2560x1440 names as symlinks to one file.
So KDE does not ship real per-size pictures; this edition's sizes are our own choice.

## Make

`sparky-os/packages/sparkyos-artwork/wallpaper-sizes.py SOURCE IMAGES_DIR` makes 1280x720, 1366x768, 1600x900, 1920x1080, 2560x1440 with Pillow Lanczos, never an upscale, same 16:9 (1366x768 is 0.05 % off 16:9, a squeeze of under one pixel), PNG optimised.
It reads each output back and checks it against an area-average (BOX) reduction of the source: the mean absolute difference stayed under 0.4 of 255 on all 19 pictures except the Oxygen lockup (about 1.0).
The 3840x2160 stays; for SparkyOSOxygen it stays a symlink to /opt/artwork.
Results: the package grew from 36 MB to 58 MB; the five sizes of the 19 packages are 23 MB (1280x720 2.6, 1366x768 3.1, 1600x900 4.0, 1920x1080 5.3, 2560x1440 8.4).

## Measure

`wallpaper-decode-bench.cpp` (g++ with Qt6Gui, `QT_QPA_PLATFORM=offscreen`): copies Plasma's selection, then times `QImageReader::read()` and read with `setScaledSize`, median of 9 rounds after a warm-up.
Medians over the 19 packages, 12-thread station at load 17 to 20 (CONTENDED), ms per picture:

| screen | one 3840x2160 | picked size |
|---|---|---|
| 1366x768 | 93 | 12 |
| 1920x1080 | 90 | 21 |
| 2560x1440 | 98 | 35 |
| 3840x2160 | 84 | 82 |

SparkyOSOxygen alone at 1920x1080: 107 ms to 28 ms.

## Traps

- Symptom: `cp -r` of an installed wallpaper tree into a bench shows a dangling `3840x2160.png`. Cause: SparkyOSOxygen links to /opt/artwork. Fix: replace the link with the real file before benchmarking.
- Symptom: `lean.release check-debs` prints "build record NOT complete, unrecorded: buildinfo". Cause: the script-package builder makes no .buildinfo. Fix: none in this recipe; the check itself ("verified 2 packages") passes.
- Symptom: the build stops with "no source date". Cause: the authoring copy is in no git repository. Fix: export SOURCE_DATE_EPOCH, or call `sparky_provenance_init IMAGE` as the container build scripts do.
- Symptom: `docker run` of a Qt program prints fontconfig cache errors for every start. Cause: no writable HOME. Fix: `-e HOME=/tmp` or send stderr away; the timing is unaffected.
- `git clone --local` of a repository onto another disk fails on hard links: use `--no-hardlinks`.
