# Paper depth: the desk and the page

Learned from queue row 121 (November 2026): Okular's page view and every Qt program's print preview paint the desk and the pages in one widget, so no style could give them their own depth.
Daniel's design (2026-10-15): "1px background sink and on top of this -1, +1px to the paper"; "so it all stays leveled".

## The design

- The desk (the background around the pages) lies one element step behind the window.
- The paper lies one step above that: the window's own plane, level with the toolbars and the frame.
- Nothing pops out of the window, so a page scrolled under a toolbar is cut at its own level.
- The page's text, pictures, annotations and selection ride with the page; the page's shadow lies on the desk, where a shadow falls.
- The step is the person's element limit, set in one place and handed out by the compositor: no program and no library rescales it by a window, a view or a page ([one separation, one place](../../native-linux/references/one-separation-one-place.md)).
- A window lying behind the active one is flat, like every other element inside it; a 2D screen shows the program as it always was.

## The chain, from the setting to the eyes

1. **The setting:** `ElementLimit` in kwinrc's `[StereoDepth]` group, 1 pixel of a view 1920 wide by default. Stereo KWin reads it with the other depth limits (`Options::stereoElementLimit()`), applies no display factor to it (none is designed for a window's insides), and tells it to every surface that follows its depth: version 7 of `kde_stereo_content_v1`, the event `element_limit`, sent before `output_width` and `depth_limits`, which ends the group (KWin +stereo3d69, plasma-wayland-protocols +stereo3d13).
2. **The declaration:** the widget that paints the desk and the pages sets a dynamic property, `_q_stereo_depth_rects`: a list of maps, each with a `rect` (QRect or QRectF, in the widget's coordinates) and a `depth` (a fraction of one step, -1 to 1, relative to what the rectangle lies on). A document viewer gives the whole view at -1 and each page at 0. A rectangle lies on the last one before it in the list that holds it whole, else on the widget; the widget's children lie on the widget's own plane.
3. **The wake:** declaring makes Qt Widgets ask the platform to follow the window's depth (`_q_stereo_follow_depth`, through the native interface). Qt's Wayland plugin makes a `kde_stereo_depth_v1` object of its own for the window's surface, on every surface the window gets, and sets two properties on the `QWindow`: `_q_stereo_awake` from `depth_state` and `_q_stereo_element_limit` from `element_limit`. A window is then painted once per eye while it is awake and one step is at least half a device pixel, whatever style draws it; a style that shows depth itself (Stereo Union's `_q_stereo_depth`) still does as before.
4. **The step in pixels:** the element limit times the window's screen width in device pixels, over 1920 (`qt_widget_stereo_element_step()`), the way the stereo layer gives a Qt Quick window its limits; a rectangle's parallax is its depth times the step, rounded to whole device pixels, as everything in Qt Widgets is.
5. **The drawing:** `QWidgetPrivate::paintStereoDepthRects()` draws the declaring widget a rectangle at a time in each eye, each moved by its own eye shift by the rule widgets are moved by (`paintSiblingsRecursive()`, Stereo KWin's split of a parallax): nearer than what it lies on, drawn whole; deeper, seen through its own rectangle and cut to it.

## How a program uses it

```cpp
// the pages moved (scroll, relayout, resize): say where they lie before they are painted
QVariantList rects;
rects.append(QVariantMap{{u"rect"_s, viewport()->rect()}, {u"depth"_s, -1.0}});   // the desk
for (const QRect &page : visiblePagesInViewportCoordinates)
    rects.append(QVariantMap{{u"rect"_s, page}, {u"depth"_s, 0.0}});              // the paper
viewport()->setProperty("_q_stereo_depth_rects", rects);
```

- Say it again wherever the pages move, before the paint: Okular calls it at the end of `PageView::slotRelayoutPages()`, at the start of `PageView::scrollContentsBy()` and at the end of `PageView::resizeEvent()`; Qt's print preview from `scrollContentsBy()`, `resizeEvent()` and after every transform or layout change (`_q_fit`, `zoom`, `setZoomFactor`, `layoutPages`, `setViewMode`).
- Declare the paper with its outline (Okular draws a one-device-pixel outline just outside the page: the page's rectangle grown by one), never with its shadow.
- Setting an unchanged value sends no event (`QObject::setProperty()` compares a dynamic property's value), and a changed one repaints only while the window is awake, so declaring on every scroll costs a 2D screen nothing.

## Recipe: Okular and the print preview

- Okular: `part/pageview.cpp`, one function, `updateStereoPaperDepth()`, and the three calls above; the edition's `okular` package depends on the Qt that draws the rectangles.
- The print preview: `src/printsupport/widgets/qprintpreviewwidget.cpp`, `GraphicsView::updatePaperDepth()`; the paper is `PageItem::paperRect()` mapped through the view's `viewportTransform()`, aligned outward.
- Presentation mode in Okular is a window of its own and declares nothing: it stays at its window's level.

## The study: Calligra Words and LibreOffice (built in milestone 2)

- **Calligra Words** (Debian testing 1:26.08.0+dfsg-1): `KWCanvas` is a `QWidget`; `KWCanvas::paintEvent()` erases with the widget's own background (the desk) and `KWCanvasBase::paint()` fills each exposed page's clip rectangle white (`m_viewMode->mapExposedRects(...)`, translated by `-m_documentOffset`). It draws no page shadow (`paintPageDecorations()` says so). The smallest change: one function in `KWCanvas` that declares `rect()` at -1 and each `ViewMap::clipRect` of `mapExposedRects(QRectF(rect()).translated(m_documentOffset), viewConverter())`, translated back, at 0, called from `setDocumentOffset()`, `updateSize()` and the canvas's resize.
- **LibreOffice** (Debian testing 4:26.8.3.1-3), its KF6 VCL plugin: the whole frame is one `QtWidget`, painted in `QtFrame::handlePaintEvent()` from the frame's image (toolbars, rulers and the document alike), so the rectangles have to come from Writer's layout through VCL. The smallest change in three layers: a `SalFrame` virtual with an empty default (as `SetRepresentedURL` has), which `QtFrame` turns into the property on `m_pQWidget` in widget coordinates; a `vcl::Window` call that maps a window's output pixels into its frame; and in Writer, after `SwViewShell::VisPortChgd()` and after a paint or a zoom, the edit window's rectangle at -1 and each visible `SwPageFrame::getFrameArea()` (twips, `LogicToPixel`) at 0. Writer paints the page's shadow with `SwPageFrame::PaintBorderAndShadow()` outside the page rectangle and the desk with `SwViewShell::PaintDesktop()`, so the shadow lies on the desk by itself.

## The proof

The stereo proof rig ([the rig](../../stereo-proof-rig/SKILL.md)): Stereo KWin's virtual output in a 3D mode, 1920 wide, a fresh session per case, the published round plus the stage installed by apt.

- The desk's shift against the page's, from colour-keyed marks: a desk mark and a page mark measured in each eye; the page's own content moves with the page.
- A page scrolled under the toolbar: the page's edge at the toolbar in both eyes at the same column.
- Presentation mode, a page filling the output: equal eyes.
- A background window: equal eyes.
- Red rows: the published packages show no step; `ElementLimit=0` gives equal eyes; a 2D output gives the same pixels as the published build.
- A second, measuring scale (a larger `ElementLimit`) makes every share whole pixels; it is a measuring scale only, never a default.

Measured in row 121 (KWin's virtual output in its 3D twin mode, 1920 wide, the NVIDIA card through CDI; left eye minus right eye, in pixels of one view; every match exact):

| Case | Published round | Qt +25, KWin +69, Okular +1 |
|---|---|---|
| Okular, two pages, `ElementLimit=1` | paper 0, desk 0 | paper 0, desk -1, title bar 0 |
| Print preview, two pages | paper 0, desk 0 | paper 0, desk -1, title bar 0 |
| Both at `ElementLimit=12` (measuring scale) | desk 0 | desk -12, paper 0 |
| `ElementLimit=0` | equal eyes | equal eyes |
| A page scrolled under the toolbar | cut at the window's plane | cut at the window's plane, its edge on the same column in both eyes |
| Okular presentation mode | equal eyes | equal eyes |
| A window behind the active one | flat inside (the whole window at -2) | flat inside (paper, desk and title bar at -2) |
| A 2D output | baseline | the same pixels as the published build |

The client's `WAYLAND_DEBUG` log carries the chain: `kde_stereo_depth_v1.depth_state(1, 0)` and `element_limit(1.00000000)` (12 and 0 at those settings); the window behind the active one hears `depth_state(0, 0)`.

## Traps

- **Symptom:** the page's left edge looks a step deeper than its right edge in one eye (the paper one column wider on one side). **Cause:** the desk is drawn moved with everything the widget paints, the paper too; where the paper's shift differs from the desk's, a strip beside the page shows paper at the desk's depth, a part of the desk the program never drew because the paper covered it. **Fix:** after the desk and before the paper, the strip continues the desk from the column just outside the page (one extra pass per column of the strip, the column shifted into place), so the page's edge is at the page's depth in both eyes. **Found by:** the unit test `paintRectsAtTheirDepth` (the column beside the page white instead of grey).
- **Symptom:** a window followed for a pair (s8-0001's depth object) never heard it was awake once the widget declared rectangles. **Cause:** the compositor sends `depth_state` when an object is made and on changes only; the object made earlier had heard its state before anyone listened. **Fix:** following gets a `kde_stereo_depth_v1` object of its own. **Found by:** reading `StereoDepthSurfaceV1::sendState()` (it sends only what changed).
- **Symptom:** a build script stopped right after installing the build dependencies, exit status 2, nothing in its log. **Cause:** `build_user=$(getent passwd 1000 | cut -d: -f1)` under `set -e` and `pipefail`: `getent` exits 2 in an image with no user of uid 1000. **Fix:** `|| true` on the lookup, then `useradd`. **Found by:** the last log written (`build-versions.txt`) and the exit status.
- **Symptom:** a build stopped at `apt-get update` (exit 100) with `The repository 'file:/repo mashtabba InRelease' is not signed` and `Failed to parse keyring /etc/apt/trusted.gpg.d/sparky-stereo-repo.asc`. **Cause:** the recipe's inner script names the edition's key in `signed-by` and expects the builder image to carry it; another lane's builder did, the shared base image does not. **Fix:** the script copies the published tree's own key (`/repo/sparky-stereo-repo.asc`) into place before the update. **Found by:** `apt-update.log` in the work folder.
- **Symptom:** a qt6-base or KWin build compiles to the end and stops in `override_dh_builddeb` with `conflicting supplied package: kwin-common; provide one authoritative edition snapshot`. **Cause:** the sibling list given to the Lean Code gate held the published round's packages, among them the source's own published binaries, while the build supplies its new ones. **Fix:** the list carries only edition packages the build needs that are not published yet (KWin +69: the new plasma-wayland-protocols; qt6-base: none, an empty file); published packages already reach the gate through the archive configuration. A program built against an unpublished library (Okular against qt6-base +25) may take the published list with that library's packages replaced, since its own packages are not in it. **Found by:** the last line of the build log; KWin's recipe notes had it since +65.
- **Symptom:** a build against an unpublished qt6-base stops after installing it with `The following packages will be DOWNGRADED: libqt6core6t64 ...` and `E: Packages were downgraded and -y was used without --allow-downgrades` (apt exit 100). **Cause:** the build container pins the edition's published tree at 1001, so a later `apt-get install` that names `qt6-base-dev` takes the published Qt back over the one just installed from the folder of new packages; `apt-get build-dep` keeps an installed version that satisfies it and does not hit this. **Fix:** `apt-mark hold` the new packages right after installing them, and name a package the install line lists explicitly at the version just installed (`qt6-base-dev=VERSION`): the solver takes the pinned candidate of a named package even over a hold (`Reached two conflicting assignments ... selected as a downgrade`). **Found by:** the end of `build-dep.log`, twice.
- **Symptom (caught before a run):** a recipe whose container script is one single-quoted `bash -c '...'` gets a comment such as "apt's solver"; `bash -n` passes. **Cause:** the apostrophe ends the quoted script and the rest becomes separate words, so the container runs a truncated script. **Fix:** no apostrophes inside such a script (write "the apt solver"), and escape a format string as `"\${Version}"`. **Found by:** counting single quotes between `bash -c '` and the closing quote.
- **Symptom:** after stopping a build container, its work folder cannot be removed (`Permission denied`). **Cause:** the script's `trap ... chown` runs on exit, not when the container is killed. **Fix:** remove it from a throwaway container as root, by name. 
- **Symptom:** in the rig every window has Qt's own title bar (minimise, maximise and close drawn by Qt), and KWin's log says `Could not locate decoration plugin "org.kde.breeze"`. **Cause:** an image with `kwin-wayland` alone has no decoration plugin, so KWin offers no server-side frame and Qt draws its own (bradient); a window whose frame the client draws is painted once on the processor store, so its elements would show no depth for a reason that is not the program's. **Fix:** install a KWin decoration in the rig image (`kwin-style-breeze`), as every session has one. **Found by:** looking at the left eye of the first capture, then KWin's log.
- **Symptom:** Okular's desk kept the palette's dark grey although the rig set a custom background. **Cause:** `UseCustomBackgroundColor` and `BackgroundColor` belong to okularpartrc's `[PageView]` group (`conf/okular.kcfg`), not `[General]`. **Fix:** write them under `[PageView]` (magenta, 255,0,255, so no page content can be taken for the desk); the measuring script keys the desk by that colour and the print preview's by Qt's own grey (160,160,164). **Found by:** the group names in `conf/okular.kcfg`.
- **Symptom:** Okular's presentation case shows different eyes where a full-screen page should give equal ones. **Cause:** Okular's notice "There are two ways of exiting presentation mode" (`PresentationWidget`, `KMessageBox::information` with the name `presentationInfo`) is a dialog over the presentation, and a dialog is at its own depth. `[Notification Messages] presentationInfo=false` in okularrc did not stop it in the rig (the client still sets the title `Information — Okular`); in that image only KIOWidgets carries the group's name, and nothing showed that the dialog's storage reads it. **Fix:** the rig closes the notice through KWin's scripting, by its caption, as a person closes it, and captures after. **Found by:** the left eye of the capture, then `set_title` in the client's `WAYLAND_DEBUG` log.
- **Symptom:** the measuring script finds a third "page" left of the pages, or a page split in two. **Cause:** Okular's thumbnail sidebar shows small pages, and paper-coloured toolbar fields are white too. **Fix:** the rig starts Okular with its sidebar and bottom bar hidden (okularrc `[General] ShowSidebar=false`, `ShowBottomBar=false`); the script takes a page as a white or pure-coloured run wider than 150 pixels with more than 60 rows of its own, and drops pages under any window stacked above the program. **Found by:** the page list in `measure.json` against the left eye.
- **Symptom:** the desk's disparity comes out as a large number such as -20. **Cause:** the desk is a flat colour; matching a block of it along a row ties at every offset. **Fix:** match the desk in the strip just below a page, where the page's shadow gives texture, and report a tie as "no measurement" rather than its first offset.
- **Symptom:** plasma-wayland-protocols' build fails at `virtual-stereo-contract.py`, `'7' != '6'`. **Cause:** the package's contract test pins the interface versions and events. **Fix:** the protocol change updates the test: version 7, the new event's form, and the events' order, which is their wire opcodes.
- **Symptom:** KWin's stereo test runner (`test-in-container.sh`) prints `BUILD FAILED` and runs no test; the link of `bin/testQuickStereo` reports `undefined reference to KWin::LayerShellV1Window::staticMetaObject`. **Cause:** the test compiles `src/scene/stereodepth.cpp` into itself, and that file casts to `LayerShellV1Window` (the overlay layer-shell check of an earlier change, in +68 already), whose metaobject libkwin does not export. **Fix, for a run now:** a copy of the runner without `testQuickStereo` runs the other 44 (row 121: 43 pass; `testXdgShellWindow` fails 3 rows that need an icon theme's `wayland` icon and the frozen-window helper process). **Found by:** the tail of `ninja.log`.
- **Symptom:** every function of KWin's `testStereoDepthExchange` fails at `init()`. **Cause:** `init()` compared the manager's version with 5 after the protocol went to 6. **Fix:** compare with the protocol's version (7 now).
