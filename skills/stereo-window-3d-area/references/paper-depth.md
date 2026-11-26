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

1. **The setting.** The 3D Depth page writes `ElementLimit` in kwinrc's `[StereoDepth]` group. It defaults to 1 pixel of a view 1920 wide. Zero keeps the parts inside a window flat.
2. **The selected display.** `StereoDepth::elementLimit(output)` multiplies the setting by the selected output's sunk and popped factors. These are the factors KWin uses for desktop depth, from libstereo-policy. A directional reference override in `[StereoDepth][<output UUID>]` uses `SunkLimit` or `PoppedLimit`. An absent or zero entry uses the display policy for that direction.
3. **The group.** Version 7 of `kde_stereo_content_v1` sends `element_limit(behind, in_front)`, followed by `output_width` and `depth_limits`. The last event closes the group. Selecting another output or changing the setting or the display's depth updates the group for every surface following the window's depth. The staged single-argument event from milestone 1 was amended before publication.
4. **The declaration and wake.** A widget sets `_q_stereo_depth_rects` to a list of maps containing `rect` (`QRect` or `QRectF` in widget coordinates) and `depth` (from -1 to 1). The engine takes its plane relative to the widget and clips according to the last earlier rectangle that contains it. The whole desk is -1 and the page is 0. The toolkit follows the surface's depth and publishes `_q_stereo_awake` and `_q_stereo_element_steps` on the window.
5. **The pixels.** Qt Widgets converts the compositor's two distances using the width carried in the same group. A negative level takes the behind step and a positive level takes the in-front step. It rounds the final parallax to device pixels. An awake window can paint per eye once either step reaches half a device pixel.
6. **The package boundary.** `libqt6waylandclient6` from qt6-base +stereo3d26 breaks `kwin-wayland` and `libkwin6` older than KWin +stereo3d70. Upgrade the Graphics page with Qt because Graphics has exact Qt dependencies. Qt retains its diagnostic on an awake surface from an earlier implementation of the protocol.

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

## Recipe: Calligra Words

Calligra Words `1:26.08.0+dfsg-1+stereo3d1+lc1` declares its desk and pages from `KWCanvas::setDocumentOffset()`, `updateSize()` and `resizeEvent()`. The desk covers the canvas. `mapExposedRects()` receives the viewport translated by the document offset. Intersect each mapped clip with the page, add the painted edge and translate it back by `ViewMap::distance - m_documentOffset`. This keeps the annotation strip on the desk and page content on the paper.

`KWCanvasBase::paintPageDecorations()` has no per-page shadow. The canvas as a whole has a `QGraphicsDropShadowEffect`. Qt's effect-source paint runs the rectangle paint for the current eye and invalidates the cached source between eyes. The effect still draws the composite.

## LibreOffice is milestone 3

The KF6 VCL plugin paints the whole frame as one `QtWidget`. Feed Writer's visible page geometry into a `SalFrame` virtual with an empty default, forward output pixels from `vcl::Window` into frame coordinates and let `QtFrame` publish the widget declaration. Recompute after a viewport or layout change and zoom. Use visible `SwPageFrame::getFrameArea()` in frame pixel coordinates, the Writer area as the desk and paper at 0. Writer's existing shadow paint belongs to the desk. Exercise print layout, multiple pages, zoom and scrolling, web layout without paper declarations, background windows and a pixel-identical 2D control under `SAL_USE_VCLPLUGIN=kf6`.

## The proof

The stereo proof rig ([the rig](../../stereo-proof-rig/SKILL.md)): Stereo KWin's virtual output in a 3D mode, 1920 wide, a fresh session per case, the published round plus the stage installed by apt.

- The desk's shift against the page's, from colour-keyed marks: a desk mark and a page mark measured in each eye; the page's own content moves with the page.
- A page scrolled under the toolbar: the page's edge at the toolbar in both eyes at the same column.
- Presentation mode, a page filling the output: equal eyes.
- A background window: flat inside, its paper, desk and title bar at one level (Stereo KWin moves the whole window, so its eyes are not equal).
- Red rows: the published packages show no step; `ElementLimit=0` gives equal eyes; a 2D output gives the same pixels as the published build.
- A second, measuring scale (a larger `ElementLimit`) makes every share whole pixels; it is a measuring scale only, never a default.

Measured in row 121 milestone 1 (KWin's virtual output in its 3D twin mode, 1920 wide, the NVIDIA card through CDI; left eye minus right eye, in pixels of one view; every match exact):

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

For the second milestone, rerun the reference-output cases and take two more measurements. A virtual display with a known physical size must show the element limit multiplied by its own factor, with a red control on +69/+25. A single directional override must move the in-front marker without altering the behind marker. Set the control through the installed KCM and compare the saved setting with the wire and the measured desk. On a published system, simulate installing Qt alone with KWin +70 available and check that apt selects KWin for Qt +26. The older Qt is the control. For Words use two pages, a scrolled and a background case, and a 2D capture compared to Debian's Words.

## Traps

- **Symptom:** Words paints the paper and desk correctly but a stock desk has no horizontal mark to measure. **Cause:** the desk between the pages is a single palette color. **Fix:** the rig supplies a patterned brush through its test style on `KWCanvas`. The ordinary `eraseRect()` draws it, and the same style runs on Debian's Words and the edition build. **Found by:** the two-page Debian capture showed a uniform gap between the pages.
- **Symptom:** the KCM compiles and the stand-alone shell shows a blank page. **Cause:** Qt's resource compiler preserved a syntactically invalid QML placeholder. **Fix:** parse the source with qmlformat and launch the KCM in the rig. **Found by:** the shell's QML error and the missing 3D Depth form.
- **Symptom:** the rig clicks the KCM field and its value stays at 1. **Cause:** focus can still belong to the document window while the shell starts, and immediate releases can prevent a useful click. **Fix:** position the KCM by caption, read back its frame and let the button and key presses reach the client before release. **Found by:** comparing the KWin frame list, the edited capture and the KCM's Wayland input log.
- **Symptom:** Words declares rectangles but its pages remain flat. **Cause:** the canvas installs a widget-wide drop-shadow effect, and the previous rectangle paint bypassed widgets with effects. **Fix:** draw the effect's source with the current eye's depth rectangles and discard the source pixmap cache between eyes. **Found by:** reading the canvas constructor against Qt's effect and backing-store paths.
- **Symptom:** reloading the display override in `testElementLimit` can reset the global test limit to 1. **Cause:** `Options::updateSettings()` loads `[StereoDepth]` before reading the display group. **Fix:** keep the global test value in the shared KConfig while the test changes one display direction, and restore both entries on exit. **Found by:** following the reload through `Options::loadConfig()`.
- **Symptom:** a resumed package fails at Lean Code projection with “already exists; never replace a published version”. **Cause:** binary output from an earlier candidate with the same version is still in the build directory. **Fix:** move the earlier candidate's .debs and build metadata aside. Keep the source inputs and compiled objects for the resume. **Found by:** the resumed KWin build reached `override_dh_builddeb` and found the first candidate's debug package.
- **Symptom:** the package builds but configuring the integration tests fails to find `libei-1.0`. **Cause:** the integration CMake files also configure input emulation tests. **Fix:** include `libei-dev` and `libeis-dev` in the test image. **Found by:** the CMake log points to the pkg-config call in `autotests/integration/CMakeLists.txt`.
- **Symptom:** the active monitor has stereo eyes but `testElementLimit` times out before its first protocol group. **Cause:** KWin flushes pending Wayland messages when its event loop is about to block. **Fix:** use the existing `waitFor` helper, which waits on the depth object's signal in a nested event loop. **Found by:** the polling fixture failed with zero groups and the signal-driven fixture passed all 18 rows.
- **Symptom:** a new source recipe creates a .dsc but the builder cannot find the upstream tarball. **Cause:** the successor tool reuses the unchanged archive and produces only the new Debian portion. **Fix:** copy every source input named by the .dsc alongside the generated files before running the binary recipe. **Found by:** the protocols +14 build stopped at its first source copy.
- **Symptom:** the selected display's limits arrive while the old output geometry is still set on the window. **Cause:** the two state paths are asynchronous. **Fix:** consume the element steps and selected output width from the same group, on `depth_limits`. **Found by:** reading client property updates alongside the compositor's wire grouping.

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
- **Symptom:** Okular's presentation case shows different eyes where a full-screen page should give equal ones. **Cause:** Okular's notice "There are two ways of exiting presentation mode" (`PresentationWidget`, `KMessageBox::information` with the name `presentationInfo`) is a dialog over the presentation, and a dialog is at its own depth. `[Notification Messages] presentationInfo=false` in okularrc did not stop it in the rig (the client still sets a title beginning with `Information`); in that image only KIOWidgets carries the group's name, and nothing showed that the dialog's storage reads it. **Fix:** the rig closes the notice through KWin's scripting, by its caption, as a person closes it, and captures after. **Found by:** the left eye of the capture, then `set_title` in the client's `WAYLAND_DEBUG` log.
- **Symptom:** the measuring script finds a third "page" left of the pages, or a page split in two. **Cause:** Okular's thumbnail sidebar shows small pages, and paper-coloured toolbar fields are white too. **Fix:** the rig starts Okular with its sidebar and bottom bar hidden (okularrc `[General] ShowSidebar=false`, `ShowBottomBar=false`); the script takes a page as a white or pure-coloured run wider than 150 pixels with more than 60 rows of its own, and drops pages under any window stacked above the program. **Found by:** the page list in `measure.json` against the left eye.
- **Symptom:** the desk's disparity comes out as a large number such as -20. **Cause:** the desk is a flat colour; matching a block of it along a row ties at every offset. **Fix:** match the desk in the strip just below a page, where the page's shadow gives texture, and report a tie as "no measurement" rather than its first offset.
- **Symptom:** plasma-wayland-protocols' build fails at `virtual-stereo-contract.py`, `'7' != '6'`. **Cause:** the package's contract test pins the interface versions and events. **Fix:** the protocol change updates the test: version 7, the new event's form, and the events' order, which is their wire opcodes.
- **Symptom:** KWin's stereo test runner (`test-in-container.sh`) prints `BUILD FAILED` and runs no test; the link of `bin/testQuickStereo` reports `undefined reference to KWin::LayerShellV1Window::staticMetaObject`. **Cause:** the test compiles `src/scene/stereodepth.cpp` into itself, and that file casts to `LayerShellV1Window` (the overlay layer-shell check of an earlier change, in +68 already), whose metaobject libkwin does not export. **Fix, for a run now:** a copy of the runner without `testQuickStereo` runs the other 44 (row 121: 43 pass; `testXdgShellWindow` fails 3 rows that need an icon theme's `wayland` icon and the frozen-window helper process). **Found by:** the tail of `ninja.log`.
- **Symptom:** every function of KWin's `testStereoDepthExchange` fails at `init()`. **Cause:** `init()` compared the manager's version with 5 after the protocol went to 6. **Fix:** compare with the protocol's version (7 now).
