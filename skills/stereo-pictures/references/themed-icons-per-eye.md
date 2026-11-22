# Where a themed icon is drawn, and how a pair reaches each place

**For** whoever makes stereo icons reach the screen: which code draws a themed icon in each place of the desktop, where one picture per eye can travel, the recipe that proves it in both eyes, and the traps met on the way.
Check freshness first: written on 2026-11-22 (queue row 77, milestone 1) from KIconThemes 6.32 with the edition's patches up to `+stereo3d2`, Qt 6.11.2 with the edition's per-eye drawing, Kirigami 6.32, KIO 6.30 with the edition's patches, Plasma 6.7.4 and Stereo KWin `+stereo3d64`.

## The rule each place follows

A stereo icon theme carries each pair as one picture, `2N x N`, left view first, in folders listed under `X-StereoDirectories`, each with `X-StereoSize` and `X-StereoLayout=sbs-left-first` ([Icon Theme Specification](https://specifications.freedesktop.org/icon-theme-spec/latest/), `X-` for extensions).
On a 2D screen every place draws the plain icon, exactly as without stereo; on a screen that shows two eyes each eye gets its own view, drawn as the theme carries it: no shift, no scaling by the icon's size, no depth of our own.

## The map

"An eye pass" is the edition's Qt drawing a window once per eye while the window's `QWindow` has `_q_stereo_depth`: Qt Widgets paints the window twice into a backing store twice as wide and names the eye on the window (`_q_stereo_eye`, 1 the left, 2 the right) while it paints it; Qt Quick polishes, synchronizes and renders each eye in a pass of its own with the same property; the Wayland platform hands the double-wide buffer to Stereo KWin as a full side-by-side pair marked as the desktop's own depth.

| Place | Who loads the picture | How a pair reaches it |
|---|---|---|
| Dolphin's file view | `KStandardItemListWidget` asks `KIconLoader::loadStereoIcon()` | Dolphin's own declared layer below the view, the view rendered once per eye with holes at the pairs, only on a stereo screen |
| Dolphin's Places panel, the KDE file dialog (Places and file list), any `QIcon::fromTheme()` in a Qt Widgets program of a KDE session | The KDE platform theme makes a `KIconEngine`; KIO's delegates call `QIcon::pixmap()` while they paint | `KIconEngine` gives each eye its view during an eye pass (KIconThemes `+stereo3d2`); the window needs `_q_stereo_depth`, set today only by a depth style |
| The desktop folder view, the panel (task manager, launchers, wastebin, tray) | Kirigami's `Icon` makes one image in `updatePolish()` from `QIcon::pixmap()` | Not yet: the item must react to `_q_stereo_eye` on its window and name its eye on the application (`_q_stereo_icon_eye`) while it asks |
| GTK programs | GTK reads `Directories` only | Not yet: GTK draws no window once per eye |
| Qt without the KDE platform theme | Qt's own icon engine | Not without a change in Qt |
| `KIconLoader::loadIcon()` called directly, a widget that keeps a pixmap it got once | The loader, no engine around it | Not yet: the picture is chosen once |

## The engine, as built

- **The eye:** `KIconEngine::paint()`, `pixmap()` and `scaledPixmap()` look for the eye first on the application (`_q_stereo_icon_eye`, set by an item that draws itself once per eye, only while it asks), then on the widget window being painted (`QGuiApplication::topLevelWindows()`, the one `QWidgetWindow` whose `_q_stereo_eye` is 1 or 2: Qt Widgets sets it only while it paints that eye, one window at a time). Anywhere else, and off the GUI thread, the eye is 0 and the icon is the plain one.
- **The view:** `KIconLoader::loadScaledIcon()` takes the eye from a thread-local the engine sets around the load; an icon whose first theme with the icon (in the order of inheritance) has a stereo picture gives that eye's view, with the plain icon's state effect and overlays, cached under its own key; any other icon is the plain icon in both eyes.
- **A refused folder is told:** a stereo folder whose section has no `X-StereoSize`, a size that is not a number of pixels, no `X-StereoLayout` or another layout is reported as a warning in the `kf.iconthemes` category, naming the index file, the section and the key to add or correct, for example: `The icon theme file /usr/share/icons/NAME/index.theme lists the stereo folder stereo/places/64 in X-StereoDirectories, but the loader does not use it: its section [stereo/places/64] has no X-StereoLayout key; add X-StereoLayout=sbs-left-first (both views side by side, the left view first).`

## Recipe: prove a place in both eyes

1. **The rig:** a throwaway container per case with Stereo KWin (`kwin_wayland --virtual --width 1920 --height 1080` under `KWIN_VIRTUAL_STEREO_MODES=1`), the KDE platform theme, the theme set in the case's own `kdeglobals` (`[Icons] Theme=`), one render node (the AMD card, or the NVIDIA card through CDI), `--network none`; [the proof rig](../../stereo-proof-rig/SKILL.md) has the session.
2. **A 3D output:** `kscreen-doctor output.1.mode.2` picks the virtual output's first 3D twin (`3D-SBS`); record `kscreen-doctor -o` after it.
3. **Stereo icons on screen:** a fresh account shows no Trash in the Places panel, so give the case a Places bookmark drawn with the icon (`~/.local/share/user-places.xbel`, `<bookmark:icon name="user-trash"/>`) and a folder whose `.directory` says `Icon=user-trash-full` for the file list.
4. **The window drawn once per eye:** until the trigger is built, the test program sets `_q_stereo_depth` on its windows after they settle and repaints them; the Wayland log then shows one `kde_stereo_content_v1.set_content(3)` and `kde_stereo_depth_v1.set_desktop_depth(1)` on the window's surface.
5. **Capture and measure:** ScreenShot2 gives both eyes side by side (3840 x 1080); for each region where the eyes differ, match each eye against the theme's own left and right views composited over the region's background, trying every placement that covers the region; a pass is the left eye on the left view and the right eye on the right view of the same picture (mean error measured: 0.28 and 0.33 of 255 at 64 and 16 px).
6. **Controls:** the same case with the predecessor library (the eyes are equal); a 2D output and a window drawn once, each against the predecessor pixel for pixel (0 differing pixels); a theme without stereo folders, the same; at 125 and 150 % the left eye against the predecessor's left eye.

## Traps

- **Symptom:** no stereo icon was ever drawn as a pair, in any place. **Cause:** the loader dropped every stereo folder whose section lacked `X-StereoLayout=sbs-left-first` with a debug line nobody reads, and the theme had no such line. **Fix:** the theme carries the key, and the loader now tells the author (above). **How found:** a capture of Dolphin's view with the key added by hand drew pairs, without it identical eyes (queue row 752).
- **Symptom:** KIconThemes stops compiling: `kiconengine.cpp: fatal error: QWidget: No such file or directory`. **Cause:** the library under `KIconEngine` links Qt GUI only; the widgets live in KIconWidgets. **Fix:** find the window being painted from `QGuiApplication::topLevelWindows()` (`inherits("QWidgetWindow")` and its `_q_stereo_eye`), not from the painter's widget. **How found:** the build log.
- **Symptom:** at 125 % the left eye differs from the plain drawing in a few pixels along the icon's right edge (22 in the file dialog's Places entry). **Cause:** the pair was read as one picture with `QImageReader::setScaledSize()`, so smooth scaling blended the last column of the left view with the first of the right view. **Fix:** read a raster pair whole, cut it, and scale each view on its own with `QImage::scaled(..., Qt::SmoothTransformation)`, as `QImageReader` scales a plain icon; draw a vector pair at twice the view's width. **How found:** comparing the successor's left eye with the predecessor's at 125 %, in a theme whose plain icon equals its left view.
- **Symptom:** a 3D capture of the KDE file dialog has identical eyes although its window is declared a pair. **Cause:** no stereo icon was on screen: a fresh account's Places panel has no Trash. **Fix:** recipe step 3. **How found:** looking at the capture.
- **Symptom:** a correct eye of a 64 px icon matches its view with a mean error of 10.7 of 255, the same in both eyes. **Cause:** the matcher looked only two pixels around the centred region, and the icon's transparent top rows put the picture three pixels higher. **Fix:** try every placement that covers the region. **How found:** a wider search gave 0.28 for the same capture.
- **Symptom:** a matcher cannot tell the left eye from the plain icon. **Cause:** a theme may ship the left view as its plain icon (Kubabbar Glass 20261122.1 does, byte for byte, at every size). **Fix:** decide on the right eye against the right view, and check the left eye against the predecessor's drawing of the plain icon. **How found:** comparing the theme's files.
- **Symptom:** a rig image refuses to install the look: `libheif-plugin-x265 ... Depends libx265-217 (>= 1:4.3) but none of the choices are installable`. **Cause:** the look depends on the stereo layer, the layer on the edition's KImageFormats, which uses the edition's libheif built on deb-multimedia's x265. **Fix:** give the rig deb-multimedia's source and keyring, with the edition's pin above it. **How found:** apt's "two conflicting assignments" block.

## Perks

- `_q_stereo_eye` on a `QWindow` is the whole interface between Qt's per-eye drawing and anything that draws per eye: no private Qt header is needed to read it.
- `kiconfinder6 NAME` takes no size: it says which file the theme gives at the default size only.
