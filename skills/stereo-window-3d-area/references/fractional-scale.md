# A 3D area at a fractional scale

Learned from ORDER 576 (November 2026): on a 13.3 inch full HD notebook at 125 %, a file manager's 3D thumbnails showed a strip of each picture and the desktop wallpaper through the rest of the cell; at 100 % they were right.
A 3D area is a declared subsurface under a hole in the window ([the pattern](../SKILL.md#the-pattern-that-works-on-wayland)).
At a scale that is not whole (125 %, 150 %, 175 %) three different roundings meet in it, and each one can put the hole and the picture out of step.

## The rule, in device pixels

The hole and the picture cover the same device pixels at every scale.
Where that cannot be had, the area is drawn flat by the program, never as a hole with something else under it.

Three facts decide how:

1. **A window paints an edge at the nearest whole device pixel, counted from the corner of its content.**
   A widget at `x` in the window's own pixels starts at `round(x * scale)`; with Qt the widget's own origin is not rounded first, so a rectangle at `r` inside a widget at `o` starts at `round((o + r) * scale)`, not `round(o * scale) + round(r * scale)`.
2. **A compositor places a subsurface in the window's own whole pixels and rounds it to device pixels by a rule the protocol does not define.**
   `wp_fractional_scale_v1` says how a toplevel's size is rounded and nothing about subsurfaces ([wayland-protocols issue 132](https://gitlab.freedesktop.org/wayland/wayland-protocols/-/issues/132), [KDE bug 491725](https://bugs.kde.org/show_bug.cgi?id=491725)).
   KWin 6.7 rounds a subsurface's corner from its parent's corner and its size on its own: the far edge is `round(p * scale) + round(w * scale)`.
   Other compositors round both edges from the parent: `round((p + w) * scale)`.
   The two differ by a device pixel whenever the two fractions add up past a half.
3. **An image carries a device pixel ratio, and Qt draws by it.**
   `QPainter::drawImage(point, image, sourceRect)` draws an image at its size divided by its ratio (QPainter, "Drawing High Resolution Versions of Pixmaps and Images").
   Code that copies samples must give the target rectangle too, or the copy is a resize.

## The recipe (stereo-layer 1.18.1)

- **A picture the compositor resizes into the area** (a viewer: `WidgetLayer::setSource()`, `setPicture()`, the Qt Quick `StereoPicture`): nothing to do in the program.
  The layer places the surface so that its device pixels, under either rounding, hold every device pixel of the hole (`Surface::covering()`): the same rectangle where that works, one pixel of the window more where it does not, and what is over lies under the window.
- **An area the program draws once per eye** (a view of many items with a few stereo pictures, a preview with its frame): draw on the window's own device pixels.
  ```
  QImage eye = layer->eyeCanvas();                       // clear, from the window's corner to the area's far corner, the window's ratio
  area->render(&eye, layer->eyeOffset(), QRegion(), QWidget::DrawChildren);   // or a QPainter translated by eyeOffset()
  layer->setEyes(left, right);
  ```
  The canvas starts at the corner of the window's content, so the area is drawn in it exactly where the window draws it, and every edge falls on the same pixel as in the window.
  The layer places that surface on whole device pixels from corner to corner (`Surface::onWholePixels()`: grown outward to the step at which the scale is whole, 4 window pixels at 125 % and 175 %, 2 at 150 %, since a compositor gives scales in 120ths) and shows the pixels one to one: no resize anywhere, whatever rounding the compositor uses.
  The eyes are good for the place, size and scale the area had when `setEyes()` was called.
  When one changes, the layer goes flat before the window paints again (`isActive()` false) and asks for new eyes (`eyesWanted()`): connect it to the function that draws them.
- **Cut the holes with the code that paints the window.**
  For a view that keeps only its stereo pictures in the eyes, render the window's own pass (the one that clears the holes) over an opaque ground into a third canvas: the pixels left clear are the holes, to the pixel, and the eyes keep exactly those.
  Working the rectangles out a second time, in the window's own pixels, gives another rounding.
- **A hole is the pixels the picture is drawn on.**
  A pixmap drawn at 125 % has a whole number of device pixels, which is not its size in the window's pixels times the scale; clear the hole with the pixmap's device size divided by the ratio, not with the logical size.

## The rig command

One fresh session a row: Stereo KWin on its virtual output at the scale, a magenta backdrop, the program on a folder of generated marked pairs, then moves, resizes, a scroll and a panel hidden.
After each step the screen is captured in a 3D mode (both eyes) and in the output's 2D mode, where the program draws every picture itself: that flat capture is the reference.
```
rig/case.sh NAME SCALE MODE X Y W H [geom:X,Y,W,H | keys:STEPS | places]...
rig/case.sh row-125 1.25 4 101 53 1003 701 geom:60.8,40.8,1101,643 keys:k:109_s:1200 places
```
The row passes when no backdrop pixel shows inside the window in either eye, the left eye equals the flat capture pixel for pixel, the right eye equals it outside the pictures and inside a pair whose two views are the same, every picture's four edges are where the flat capture has them in both eyes, and the two eyes do differ.
Set the scale with `kscreen-doctor output.Virtual-0.scale.1.25`, the 3D mode with `output.Virtual-0.mode.N` (`KWIN_VIRTUAL_STEREO_MODES=1` lists the twins), and the desktop's depth limits to 0 so that the eyes can be compared pixel for pixel.
Place the window with a KWin script (`workspace.stackingOrder`, `frameGeometry`), also at a part of a pixel: at 125 % a window dragged by hand lies on device pixels, which are 0.8 of the window's own.

## Traps

- **Symptom:** at 125 % every cell shows a strip or corner of the pictures, at four fifths of their size, and the wallpaper through the rest; right at 100 %.
  **Cause:** the eyes were copied into the surface's buffer with `drawImage(point, image, sourceRect)`, and the program's eye images carried the window's device pixel ratio, so each eye was drawn at 1/1.25 of its size from the buffer's corner; the buffer was never cleared, so the rest held old memory.
  **Fix:** give the target rectangle (`drawImage(QRect(0, 0, w, h), image, source)`) and clear the buffer first.
  **Found by:** the buffer recorder (`stereo-proof-rig/scripts/wlrec.c`): the committed buffer was 1476x601 for a destination of 590x481, and a red body in it was 81 px wide where the window draws it 101 px wide: 0.80.
- **Symptom:** with that fixed, no wallpaper shows, but at some window sizes the pictures are one device pixel off, more toward the right and the bottom of the view.
  **Cause:** the surface was one device pixel wider or narrower than what the window paints there (fact 2), so the compositor resized the eyes by one pixel across the view.
  **Fix:** the surface on whole device pixels at both corners (the recipe above).
  **Found by:** the per-cell edge offsets of the rig: 0 at the left of the view and -1 toward the right is a resize, not a shift.
- **Symptom:** one row of a thumbnail's lower edge shows the window's background in 3D and the picture in 2D (118 pixels in a row).
  **Cause:** the hole was cleared with the pixmap's logical size, a whole number of the window's pixels, and at 125 % that is a device row short of the pixmap.
  **Fix:** the hole from the pixmap's device size.
  **Found by:** the left eye against the flat capture: every picture exact and one row differing, a little lighter (the window's white where the pixmap's frame is 252).
- **Trap of the measurement:** compare an eye with the same window drawn flat by the program on the output's 2D mode, not with a prediction: Qt's own rounding is then part of the reference.
  Use a pair whose two views are the same picture: its right eye must equal the flat capture too, which no pair with different views can show.
- **Trap of the rig:** without a decoration plugin KWin leaves the frame to Qt, and the window then has frame margins inside its surface; install the edition's decoration in the rig image and set it in `kwinrc` before KWin starts (`[org.kde.kdecoration2] library=`), or the row measures another case than the desktop's.
- **Trap of the build:** ECM installs a git hook into a source tree that has `.git`; a development build from a read-only mount stops with "Could not open file for write in copy operation .../.git/hooks/pre-commit.tmp". Build from a copy without `.git`.

- **Symptom:** a viewer's picture has a line of wallpaper one device pixel wide along its right or lower edge at some window sizes (a paint program at 125 %: 819 backdrop pixels in one of four window sizes one pixel apart).
  **Cause:** fact 2: the compositor's surface was one device pixel shorter than the hole.
  **Fix:** `Surface::covering()`, for every program on the layer.
  **Found by:** four window sizes one pixel apart in one session, counting backdrop pixels in the 40 pixels around where the eyes differ.
- **Trap of the measurement:** a viewer keeps its declared pair on the output's 2D mode (the output shows the left eye there), and the capture then still holds two eyes: the 2D mode is a flat reference only for a program that draws flat on a 2D screen, as the file manager does.
- **Trap of the measurement:** a picture's body is searched near its place in the flat capture; with eight kinds of picture in a view eight columns wide the same picture stands straight above and below, and a wide search box reports the neighbour as an offset of 70 pixels. Keep the box to a dozen pixels.
- **Trap of the measurement:** the status bar's free-space bar moves while other work fills the disk, between two captures of one step (77 to 147 pixels, the same in both eyes). Leave the status bar out of the comparison and say so.
- **Trap of the rig:** a key sent through fake input goes to the focused widget, and after a window is placed by a script that may not be the view: Page Down did not scroll. Start the file manager with `--select FILE` on a file near the end of the folder for a scrolled view with a selected cell.

## What is not settled here

- Measured at 125 %, the same before and after this work: an image editor's canvas (Showfoto) leaves one device row of its area clear at two of four window sizes, and a Qt Quick viewer (Koko) one device column beside its picture area at one of four. Neither is the surface's placement (painting the whole window background under the area changed nothing in the editor); each is in the program's own painting of its area and is the next thing to find.

- The window and the surface are committed separately, so while a view scrolls the holes move one frame before the pictures under them, at every scale.
  A synchronised subsurface committed before the window's own commit would make the two one frame; it is not built.
