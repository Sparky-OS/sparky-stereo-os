# A stereo QOpenGLWidget in an ordinary Qt Widgets window

**For** anyone whose program shows a stereo `QOpenGLWidget` inside a 2D Qt Widgets window on the edition (a 3D view in a scroll area, a dock, a graphics view's viewport, an item view's cell), or who changes the edition's qt6-base patch that gives such a widget a window of its own.
Learned on queue row 863 (November 2026), on qt6-base 6.11.2+dfsg-5+stereo3d23 and +stereo3d24 (the fix), Stereo KWin 6.7.4 +stereo3d64, Mesa 26.1.6 +stereo3d29.

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

## Traps of the test and the rig

- **A first test stayed clean on the published Qt.** A lone stereo `QOpenGLWidget` that calls `update()` from `paintGL()` marks itself dirty after the flushes, so the nested sync only flushed. Found by Qt's painting log; fixed by giving the window something dirty during the flush (a second view of a shared scene whose paint asks the first for a frame).
- **Every commit looked misplaced.** Qt draws its own frame in the rig (client-side decorations), so `wl_subsurface.set_position` carries the frame's margins (3, 30 here) over the widget's place; and the wire log's time stamps are `[HH:MM:SS.micro]`, and Mesa declares with `kde_stereo_content_manager_v1.create(new id, wl_surface)`. `lag.py` takes each window's constant offset as the one its positions follow most often, and matches each stereo subsurface to one widget.
- **Frame callback ids are reused** (`wl_callback#N` comes back): bind each `done` to the commit that asked for it, never to the id alone.
- **Never switch the branch of a tree a build is reading:** a `git checkout` during `ninja` can compile a file from another variant; switch only between builds and let ninja rebuild what the checkout touched.
