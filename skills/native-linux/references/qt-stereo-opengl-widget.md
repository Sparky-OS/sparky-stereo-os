# A stereo QOpenGLWidget in an ordinary Qt Widgets window

**For** anyone whose program shows a stereo `QOpenGLWidget` inside a 2D Qt Widgets window on the edition (a 3D view in a scroll area, a dock, a graphics view's viewport, an item view's cell), or who changes the edition's qt6-base patch that gives such a widget a window of its own.
Learned on queue row 863 (November 2026), on qt6-base 6.11.2+dfsg-5+stereo3d23 and +stereo3d24 (the fix), Stereo KWin 6.7.4 +stereo3d64, Mesa 26.1.6 +stereo3d29; part A ran the published programs on both (Kubrick, KAlgebra, Kalzium, Fraqtive, VLC Stereo, Krita, the installer's slideshow, Octave).

## What the edition's Qt does

- A `QOpenGLWidget` whose format asks for stereo (its own format, or the default format) gets a native window of its own on Wayland (a subsurface), with a stereo format; Mesa declares that surface as full side by side; the top level and every other widget stay one picture (qt6-base patch `stereo3d-native-stereo-opengl-widget.patch`, the platform capability `StereoNativeWindows`).
- The widget's ancestors stay alien (no native window): the patch sets `Qt::WA_DontCreateNativeAncestors`, so the window's parent is the nearest native ancestor, usually the top level.
- `paintGL()` is called once per eye (`currentTargetBuffer()`); a widget used as a `QGraphicsView` viewport never gets `paintGL()` and draws both buffers itself with `makeCurrent(TargetBuffer)` ([the FreeCAD page](../../stereo-two-cameras/references/coin-quarter-view-freecad.md)).

## Keeping the window where its widget is

Qt moves a native window only when its own widget moves (`QWidgetPrivate::setGeometry_sys()` places it at `mapTo(nativeParentWidget())`), and at `show_sys()`.
When an alien ancestor moves (a scroll area scrolls, a layout gives a dock more room, an item view scrolls its cells with `QWidget::scroll()`), nothing tells the stereo window, and it stays at its old place over moved 2D content.
Qt's own answer for the same shape, a window container under alien ancestors, is `QWindowContainer`: the container marks every widget from it up to its window (`markParentChain()`, the `hasWindowContainer` bit of `QWExtra`), and `QWidget::move()` and `QWidget::setGeometry()` of a marked widget call `QWindowContainer::parentWasMoved()`, which walks the marked children and places the contained window; `setParent()` calls `parentWasChanged()`.
In a scroll area or MDI area Qt makes the whole parent chain native instead (qwidget.html, createWindowContainer).

## The trap: a stereo window moved during a flush reads a freed texture list

- **Symptom:** nothing on screen, no crash seen; under memcheck (`valgrind --tool=memcheck`), reads of a freed `QPlatformTextureList` (`count`, `flags`, `clipRect`, `geometry`, `texture`, `textureExtra`) inside `QPlatformBackingStore::rhiFlush()`, called from `QWidgetRepaintManager::flush(QWidget *, const QRegion &, QPlatformTextureList *)`; the free is in `QWidgetRepaintManager::paintAndFlush()` reached from `QWaylandWindow::setGeometry_helper()`, `sendExposeEvent()`, under `QWindow::setPosition()` inside that same `flush()`. FreeCAD's stress row showed 31 such error contexts with its 3D view in stereo and none with Enable 3D off or on Debian's build.
- **Cause:** up to qt6-base +stereo3d23 the patch placed the stereo window inside `flush()` of that window (the flush of a native child). On Wayland a subsurface's move sent a synchronous expose to its parent (`setGeometry_helper()`, since Qt's Wayland plugin delivers its window system events synchronously from 6.9, QTBUG-121731); the nested `sync()` repainted the top level and rebuilt `topData()->widgetTextures` (a vector of `unique_ptr<QPlatformTextureList>`), destroying the list the outer flush held, and `rhiFlush()` then read it. The nested sync paints only when the window is dirty at that moment: FreeCAD's two 3D views of one document are (Quarter processes Coin's delay queue in its paint event, and "processing the sensors might trigger a redraw in another context"), a lone animated `QOpenGLWidget` is not (its `update()` comes after the flush).
- **Fix (qt6-base +stereo3d24):** the window is placed where the geometry of an ancestor changes, with `QWindowContainer`'s technique: the widgets from a stereo window up to its window carry the `QWExtra` bit `hasStereoWindow` (beside `hasWindowContainer`), and `move()`, `setGeometry()`, `setParent()` and `QWidget::scroll()` (`scrollChildren()`, `setWSGeometry()`) of a marked widget place the stereo windows below it (patch `o863-0002`). With it, upstream's commit d6d2a75cdbfe by David Edmundson (Qt's dev branch, not in 6.11.3 or 6.12.1): a subsurface that moves asks for its parent's next frame (`requestForcedUpdate()`) instead of exposing it synchronously (patch `o863-0001`).
- **Why that place, measured** (the small test below; every number is commits of the parent over 60 steps that showed a stereo window away from its widget, and steps after which a visible window was not placed):

  | Qt | freed-list reads (scroll, viewport, item view) | misplaced on screen: scroll, viewport, item view | stale steps under memcheck: scroll, item view; at full speed: item view |
  |---|---|---|---|
  | +stereo3d23, the move inside the flush | 31, 31, 31 | 60, 60, 62 | 0, 10; 0 |
  | the move queued until the flush returns | 0 | 60, 60, 67 | 23, 16; 2 |
  | the same with d6d2a75 | 0 | 78, 33, 128 | 12, 16; 7 |
  | upstream's d6d2a75 alone (the move left in the flush) | 0 | 0, 38, 102 | 0, 10; 0 |
  | the move where the ancestors move | 0 | 60, 60, 0 | 0, 0; 0 |
  | **the same with d6d2a75 (shipped)** | 0 | **0, 42, 0** | **0, 0; 0** |

  (The 10 are the second table cell, scrolled out of the table's view but still visible to Qt: a build that moves a stereo window only when that window is flushed leaves it behind while it is not flushed, as under Valgrind's slow frames; at full speed it was flushed within the step. That series counted hidden widgets too; the test now counts visible widgets only, and the published build's rerun with that check has the same 10.)

  A move queued after the flush waits for the next flush to notice the window is out of place, so under load a window stays behind for a whole step. Placing each window where its ancestors move repaints the parent once per window while the expose is synchronous (Mesa's swap waits for the frame callback, so each is a frame of its own, the second window one frame behind); with upstream's commit the moves wait for the parent's next frame and arrive together. The viewport shape keeps some misplaced frames in every build: the views are resized as well as moved there, and the published build has them too.
- **How it was found:** FreeCAD's memcheck row against the same run on Debian's build and with Enable 3D off; the free's stack named `QWindow::setPosition()` inside `flush()`, and the patch's hunk in `qwidgetrepaintmanager.cpp` is the one that calls it. Qt's painting log (`QT_LOGGING_RULES=qt.widgets.painting=true`) then showed why a first small test stayed clean: its nested sync printed `Syncing` and `Flushing QRegion(null)`, no `Painting and flushing dirty`.

## The small test

`sparky-os/packages/qt6-base/tests/stereo-widget-move/` in the build repository: `run.sh IMAGE RESULTS [LIBDIR]` compiles `stereo-widget-move.cpp` in IMAGE against the Qt it holds and runs it in one fresh Stereo KWin session per case (virtual output 1920 x 1080, KWin on the NVIDIA card through CDI with `GPU=nvidia` since every case is a loop, the program on llvmpipe), under memcheck and with `WAYLAND_DEBUG=client`, in four shapes:

- `scroll`: a scroll area's alien content holds a stereo `QOpenGLWidget` and a graphics view with a stereo viewport; 37 px a step.
- `viewport`: two graphics views of one scene with stereo viewports (FreeCAD's two 3D views) beside a dock hidden and shown each step.
- `itemview`: the two as cell widgets of a `QTableWidget`, scrolled 23 px a step (`QWidget::scroll()` moves cell widgets without `move()`).
- `float`: the two in a dock floated and docked again each step (a new native parent).

Each view of the shared scene asks the other for a frame from its paint (as FreeCAD's views do), and a small mono `QOpenGLWidget` animates in the status bar: that keeps the window dirty while it flushes.
Rows: `memcheck-MODE` (no error block naming `QPlatformTextureList`, the run ended by itself, every step placed) and `lag-MODE` (every step placed; `lag.py` reads the wire log and counts the top level's commits that carried a stereo window elsewhere than its widget, and how many of those reached the screen: their frame callback came before the next commit). LIBDIR lays a development build's `libQt6Widgets`, `libQt6WaylandClient` and `libQt6OpenGLWidgets` over the image's Qt (same version, so the private ABI matches).

Results, the published +stereo3d23 against +stereo3d24: see the table above; the package rows are in the row 863 hand-back.

At a fractional scale (`OUTPUT_SCALE=1.25` in `case.sh`, `ROW863_OUTPUT_SCALE` in `run.sh`: kscreen-doctor sets the virtual output's scale in a setup KWin before the case's own, as Display Settings does; the image needs `libkscreen-bin`), on +stereo3d24 through zink, 2026-11-25: memcheck clean in all four shapes (0 errors), every step placed; `lag-scroll` and `lag-itemview` place every commit (0 misplaced of 124 and 147); `lag-viewport` 58 misplaced commits of 316 (41 of 329 at 100 %). `lag-float`'s count (379 of 390) is not a placement measure: the floated dock's two stereo windows get new subsurfaces at every float, each a child of the floating window's surface, and `lag.py` pairs them with the wrong widget (its most common offsets are the distance between the two widgets, 2,208 and -1,-207), while the first commit places each one exactly at its widget; reading the float shape at a fractional scale needs `lag.py` to follow a subsurface to its new parent.

## The published programs on +stereo3d24 (row 863, part A)

`sparky-os/packages/qt6-base/tests/stereo-programs-on-qt/` in the build repository, `rerun-part-a.sh`: each published program that shows a subsurface inside a Qt window, on the published set and on the same image with +stereo3d24, one fresh Stereo KWin session per case. A probe preloaded through QtCore's `qt_startup_hook` (exported by Qt 6 and by Qt 5, so one source builds for both) logs where each 3D widget belongs and the window's frame margins at every update request and expose, drives the steps and waits for each capture; `lag.py` reads the wire log; each program's own proof measure runs on the captures.

| Program | Its stereo surface | On +24, against the published set |
|---|---|---|
| Kubrick | a stereo `QOpenGLWidget`'s native window | placed at every step (resize, full screen and back); disparity error median 0.39 to 0.47 px (1.0 at full screen) by the Qt rig's `an-kub.py`, the same on both |
| KAlgebra | Analitza's `PlotsView3DES` | placed through tab changes and resizes; each eye pixel-identical but for its random parts; `an-ka.py` median 0.26 to 0.82 px |
| Kalzium | `KalziumGLWidget` in the molecule dialog | placed; pixel-identical; `an-kz.py` median 0.06 to 0.07 px |
| Fraqtive | `MeshView` | placed through dock changes and resizes; pixel-identical; `measure.py`'s rule |
| VLC Stereo | its own desynchronized subsurface (its patch 3d-0049); a Qt 5 program | no `libQt6` in the process; placed at every step (resize, playlist, full screen); `check-embedded.py`'s rule passes |
| Krita | `KisStereoCanvasLayer`, a child `QWindow` it moves itself | placed through docker and window changes |
| Qt's own frame | none | frame and content agree in every capture of a corner and an edge drag, the button held |
| The installer's slideshow | the stereo layer's `StereoPicture`: its own subsurface | pairs on a 3D output; one commit after a resize a frame late, on both |
| Octave on Xvfb | none | one view, nothing said, on both |

Upstream's commit (patch `o863-0001`) reaches only the subsurfaces QtWayland makes for a `QWindow` (a native widget's window, Krita's layer): their move asks for the parent's next frame instead of a synchronous expose. A subsurface a program makes itself on Qt's `wl_surface` (VLC Stereo's video, the stereo layer's pictures) is placed by that program, and its `set_position` waits for the parent's next commit whichever the Qt: those were the same on both.

### Traps of part A

- **Every full-screen commit looked misplaced.** **Cause:** `lag.py` took one constant offset (Qt's frame, 3, 30), and Qt hides its frame in full screen. **Fix:** the probe logs `QWindow::frameMargins()` with each flush line; at a commit between two lines that differ, the next line's layout counts too, and that commit is listed with the parent's buffer size (1920x1080 without the frame, 1168x404 with it). **How found:** listing the commits: the window stood at 0,49, the widget's own place.
- **A Qt 5 program's layout changes were not logged.** **Cause:** Qt 5 posts a widget window's update request to the top level `QWidget`, Qt 6 to its `QWindow`; a probe watching only the `QWindow` sees only exposes in Qt 5. **Fix:** log both. **How found:** VLC's "misplaced" commits stood at the next layout's place with the previous frame.
- **108 misplaced commits in VLC on one run, 35 on the other.** **Cause:** VLC destroys its video surface's subsurface role when the widget is hidden and makes a new one when shown; places kept per `wl_subsurface` id kept the destroyed roles. **Fix:** keep places per declared `wl_surface`, drop one at `wl_subsurface.destroy`, start a new role at 0,0. **How found:** the misplaced commits listed five roles at once.
- **Moving a native widget's window is no known bad case.** **Cause:** `QWidgetWindow` moves the widget with its window (the probe's widget place followed to 51,94). **Fix:** move a window the program places itself (Krita's layer), and change a real wire log three ways (`lag-selftest.py`). **How found:** 0 misplaced commits on +24 after the "displacement".
- **A capture showed the next step.** **Cause:** under a load of 13 to 20 the capture and KWin's window list took more than the probe's fixed 2.5 s, and its step 0 did not wait at all. **Fix:** a handshake: the probe writes `step-K.ready`, the case script `step-K.captured` with content. **How found:** Kalzium's step 0 picture held the grown dialog of step 1.
- **Every pixel "differed" between the eyes.** **Cause:** with nothing declared on screen KWin returns one 1920-wide picture (`"stereo": false`). **Fix:** read the capture's own flag. **How found:** a 481,239-pixel "pair" on KAlgebra's 2D tab.
- **The installer's slideshow stayed flat with nothing said.** **Cause:** `StereoPicture` draws two eyes only on a screen that shows two eyes (`showsTwoEyes()`: a stereo or anaglyph output), and asks for an alpha channel only for a window not made yet (`PictureItem::prepareWindow()`), so in a QML window made before it loads it stays flat with `stereoFailure` empty. **Fix in the rig:** `qml --transparent`, and the virtual output in its 3D twin mode as Display Settings sets it (a setup KWin with `KWIN_VIRTUAL_STEREO_MODES=1`, `kscreen-doctor`, `otherStereoFormats` in the saved `kwinoutputconfig.json`). **How found:** `stereoActive=0` in the wrapper's log, then the layer's `updatePolish()`.
- **Two runs of one program differ where nothing moved.** **Cause:** the program's own randomness: Kubrick's shuffle (not taken from the shim's deterministic `getrandom`), KAlgebra's function colour (`randomFunctionColor()`, a random hue) and its variables list (hash order per process), Fraqtive's progressive 2D render, a film's frame, a hovered scroll arrow. **Fix:** compare those by their own measure, and crop every difference before calling it. **How found:** the crops.
- **Kubrick's measure failed before the click.** **Cause:** its demo animates and the shim records still frames only, so the record analysed is not the captured frame. **Fix:** a click stops the demo; the frame before it is listed, not judged.
- **Never edit a script a batch is running:** bash reads a script while it runs it, and an edited `run-prog.sh` resumes at its old byte offset.
- **The Qt rig's `an-kub.py` ray-casts every pixel in Python:** minutes per step at full screen; give the batch the time.

### Found on both Qts (the published set), not from +24

- KAlgebra with Stereo 3D on: after the first switch to the 3D graph the window's interface is black around the view until the window is resized; with Stereo 3D off it is drawn.
- The stereo layer's `StereoPicture` is placed one frame late after its window is resized (7 to 9 ms).
- The stereo layer's `StereoPicture` in a window made before it loads stays flat and says nothing.

## Traps of the test and the rig

- **A first test stayed clean on the published Qt.** A lone stereo `QOpenGLWidget` that calls `update()` from `paintGL()` marks itself dirty after the flushes, so the nested sync only flushed. Found by Qt's painting log; fixed by giving the window something dirty during the flush (a second view of a shared scene whose paint asks the first for a frame).
- **Every commit looked misplaced.** Qt draws its own frame in the rig (client-side decorations), so `wl_subsurface.set_position` carries the frame's margins (3, 30 here) over the widget's place; and the wire log's time stamps are `[HH:MM:SS.micro]`, and Mesa declares with `kde_stereo_content_manager_v1.create(new id, wl_surface)`. `lag.py` takes each window's constant offset as the one its positions follow most often, and matches each stereo subsurface to one widget.
- **Frame callback ids are reused** (`wl_callback#N` comes back): bind each `done` to the commit that asked for it, never to the id alone.
- **Never switch the branch of a tree a build is reading:** a `git checkout` during `ninja` can compile a file from another variant; switch only between builds and let ninja rebuild what the checkout touched.
