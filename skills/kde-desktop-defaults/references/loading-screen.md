# The loading screen

Between the login and the desktop, KSplash shows the splash of a global theme on every screen.
The default is Daniel Campos Ramos's original Sparky Black design: its background sunk, box and progress bar at the person's popped limit, and original logo at twice that limit, horizontally centred (ORDER 672, 2026-11-18).
The boot-picture loading screen of ORDER 571 remains installed as a separate choice, with its original pictures and levels.
This is KSplash inside Stereo KWin after login; a Plymouth measurement does not qualify its depth.
Daniel asked for it twice: "on KDE - splash screen is not ours" (2026-11-08) and "one more detail, kde loading is the deault KDE one, not ours, why?" (2026-11-14).

## How KSplash picks and draws a theme

- **Who starts it.** In a Wayland session `plasma_session` starts `kwin_wayland_wrapper --xwayland`, then `ksplashqml` with no argument (plasma-workspace `startkde/plasma-session/startup.cpp`); with systemd it is `plasma-ksplash.service`.
  `ksplashqml` reads `ksplashrc`, group `[KSplash]`: with `Engine=KSplashQML` (the default) it takes `Theme`, Breeze when the key is missing (`ksplash/ksplashqml/splashapp.cpp`); `Theme=None` shows nothing.
  The edition ships `/etc/xdg/ksplashrc` naming `org.sparkystereo.desktop` ([the KDE splash](../SKILL.md#the-kde-splash)), and a person's own file wins key by key.
- **What it draws.** The theme is a Plasma look-and-feel package; KSplash loads its `contents/splash/Splash.qml` (`splashmainscript`) as the root of a `QQuickView`, one per screen, and sets the root's `stage` from 1 to 6 (initial, wm, startPlasma, kcminit, ksmserver, desktop); it quits at 6, or closes itself after 30 seconds.
- **Its windows.** One layer-shell surface per screen, scope `ksplashqml`, layer overlay, anchored to every edge with exclusive zone -1, keyboard interactivity exclusive, so each takes the focus as it maps and only the last one mapped keeps it (`ksplash/ksplashqml/splashwindow.cpp`).
- **A quiet fallback to watch for.** When `Splash.qml` fails to load (a missing QML module, a syntax error), KSplash loads the splash of the package the theme names in `metadata.json` as `X-KDE-fallbackPackage`, logging only a warning. The edition's theme falls back to `org.kde.oxygen`, whose splash is KDE's 2014 one with the KDE gear: a broken splash would look exactly like the defect this page fixes. So the look package `Depends` on everything its splash imports (`libstereo-layer1 (>= 1.20.0)`, `qml6-module-qtquick`), and a proof reads the session log for "Failed loading" and checks the picture, never only the setting.

## The retained boot-picture splash (ORDER 571)

- **The picture:** `sparky-stereo-look`'s `default/splash/Splash.qml` with the four pictures of sparky-stereo-plymouth's `sparky-stereo-lines` theme (background, the swirl with its orbit lines, an electron, the SparkyOS wordmark), placed with the sums `gen-theme.py` writes into the boot splash's script: the background covering the screen, the swirl 0.7 of the shorter side high at the top, 0.092 of its width right of centre, the wordmark 0.7 of the swirl's width, 0.092 of the height above the bottom, three electrons with their trails riding the orbits, restarted every 2.5 seconds.
  `tests/splash-pictures.sh` in the look recipe fails when a picture differs from the boot splash's by a byte or a placement factor is missing from either side.
- **The levels:** the boot splash's, as fractions of the person's limits for the screen: background 0 (the screen), swirl half the popped limit, wordmark the popped limit, an electron `popped/2 + popped/2 * f` where its curve rises and `popped/2 + 0.6 * sunk * f` where it falls (`f` is minus the vertical part of the direction of travel); each rounded to whole device pixels as Stereo KWin and the boot splash round their levels.
- **No text, no progress bar:** the boot splash shows none.
- **The chooser's preview** (`contents/previews/splash.png`, 300 x 168) is a capture of the splash on a 2D output, scaled down.

## The route for depth in a layer-shell QML window

Reconciled against what ships before anything was built:

1. The edition's Qt Quick (qt6-declarative `s1-0002`) draws a window once per eye while the window's dynamic property `_q_stereo_depth` is true and moves each item by its `_q_stereo_parallax` (device pixels, positive nearer); `s3-0001` draws an expose's frame as a pair too. It reacts to `QEvent::DynamicPropertyChange` only, so the properties must be set from C++: plain QML cannot set them.
2. Stereo Union sets them for its own controls, inside the style plugin, so a window that is not a Qt Quick Controls window styled by Union gets nothing.
3. So the shared layer gained the missing piece: `StereoDepth`, an attached type of `org.sparky.stereo` (stereo-layer 1.20.0). `StereoDepth.depth` is a fraction of the person's limits (`StereoDepth.Popped` is 1, `StereoDepth.Sunk` -1, 0 the screen). The type follows the window's surface through libstereo-declare on the layer's own queue (`kde_stereo_depth_v1`: `depth_state` for awake, `depth_limits` for the limits of the output the window mainly sits on), sets `_q_stereo_depth` while the surface is awake and the limits are not both zero, and gives each item its parallax; a window that should be a pair and is still one picture after 30 frames says why once in the program's log. `StereoDepth.parallaxFor()` is the sum, checked against the boot splash rig's own rows.
4. Stereo KWin must say the surface is awake. Up to `+stereo3d57` a layer-shell surface of an ordinary scope was a window: the focused splash was the active window, at the screen and awake, and every other screen's splash a window of the pile, drawn whole behind the screen (a fifth of the sunk limit) and asleep. From `+stereo3d58` a surface of the overlay layer that covers its output is `Fixed`, at the screen, and awake, as the lock screen is (`StereoDepth::roleOf()` and `isAwake()` in `src/scene/stereodepth.cpp`; test `testStereoDepthLoadingScreen`).

Without any of these the splash is the same picture, plain, on every screen.

## Capturing it in a real login

The rig is in the proof rig skill ([a real login with the loading screen](../../stereo-proof-rig/references/login-splash.md)): a fresh home, the real `startplasma-wayland`, KWin on virtual outputs through a `kwin_wayland` shim in `PATH`, both eyes captured per screen while the splash is up, each level's disparity measured against the prediction.

## What was measured (ORDER 571, 2026-11-15)

Real logins on 1920 x 1080 virtual outputs, each part's disparity from both eyes against the same login on a 2D output; the rig's virtual output reports no size, so the display factor is 1 and the limits are the person's (KWin's defaults 4 and 10).

| Case | Swirl (half the popped limit) | Wordmark (popped limit) |
|---|---|---|
| Defaults, one 3D screen | 2 px (left eye +1, right -1) | 4 px (+2, -2) |
| PoppedLimit 8, SunkLimit 20 | 4 | 8 |
| PoppedLimit 2, SunkLimit 5 | 1 (+1, 0: the odd pixel to the left eye) | 2 |
| Limits 0 | the eyes identical, 0 differing pixels | |
| 125 % | 2 | 4 |
| Two 3D screens (KWin +stereo3d58) | 2 on each | 4 on each |
| A 2D screen beside a 3D one | plain on the 2D one (no shift), 2 on the 3D one | plain, 4 |

The boot splash's own rig (ORDER 481) measured the same numbers for the same limits (4 and 2 with nothing saved, 2 and 1 at PoppedLimit 2, 8 and 4 at 8, 0 at 0), so nothing jumps in depth between the two.
On two 3D screens with KWin up to +stereo3d57 the screen whose splash lacked the focus showed its whole picture 2 px behind the screen and flat.
With Qt Quick's software renderer forced, the picture is plain in both eyes and the session's log has one line: "items of … are drawn flat: Qt Quick's software renderer draws one picture".

## Traps

Each with its symptom, its cause, its fix and how the cause was found.

- **Symptom:** after the theme was named in `/etc/xdg/ksplashrc` (ORDER 472) the person still saw KDE's gear. **Cause:** the theme's own `contents/splash` was a copy of Oxygen's splash folder, Marco Martin's 2014 KDE splash with `images/kde.png`. **Fix:** the theme's splash is the edition's own. **Found by:** listing the published package's files (`dpkg-deb -c`) and looking at the picture, not the setting.
- **Symptom:** on two 3D screens one loading screen had depth and the other was flat and 2 px behind the screen as a whole. **Cause:** KWin took the splash surface without the focus for a window of the pile (scope `ksplashqml` maps to an ordinary window type). **Fix:** KWin `+stereo3d58`, above. **Found by:** the whole-picture shift of each output's capture in a two-screen login (`measure.py eyes`: -2 on one output, 0 on the other).
- **Symptom:** a QML item with `property real _q_stereo_parallax: 4` shows no depth. **Cause:** Qt Quick hears only dynamic property changes. **Fix:** `StereoDepth.depth`. **Found by:** reading `QQuickWindowStereo::itemPropertyChanged()` in the qt6-declarative patch.
- **Symptom:** the splash is up for about a second and a half in the rig, too short to capture at chosen moments. **Cause:** a container's Plasma is ready fast. **Fix:** for capture cases only, the person's autostart folder holds an `org.kde.plasmashell.desktop` whose `Exec` sleeps a few seconds first (the person's folder overrides the system's entry of the same name); timing cases run without it. **Found by:** KWin's `REMOVED ksplashqml` line 1.4 s after `ADDED`.
- **Symptom:** waiting for `ksplashqml` to leave the process list waited 70 seconds once. **Cause:** in that run (a container without the render node) the session bus logged "Activating service name='org.kde.KSplash' requested by ... plasmashell" after the splash had quit, so a second `ksplashqml` was started by D-Bus activation; with the render node it was not seen again. **Fix:** take the splash's moments from KWin's own log (`ADDED` and `REMOVED ksplashqml`), never from the process list.
- **Symptom:** at 125 % the splash's levels were 1.5 times too deep (wordmark 6 px apart, swirl 3, where 4 and 2 are due). **Cause:** `StereoDepth` took the output's width in device pixels from the screen's ratio, which on Wayland is the whole `wl_output` scale (2), not the window's fractional 1.25. **Fix:** the window's own `devicePixelRatio()`; the case is kept in the proofs (`SCALE=1.25`). **Found by:** the 125 % login measured 6 and 3, which is `round(4 x 1536 x 2 / 1920)` and half of it.

## A loading screen with parts at depth, and a second kept selectable

ORDER 672, 2026-11-18: the prerequisite audit below found the clamp in the published 1.21.1 layer; stereo-layer 1.22.0 adds the explicit exception and the replacement has been measured in real logins.
The ORDER 571 measurements above describe that splash, not every later loading-screen design.

1. Read the requested levels and the published layer's implementation before replacing the pictures.
   `StereoDepth` levels are absolute from the screen plane; nesting a logo inside a popped box does not add the box's depth to the logo's declared depth.
   In stereo-layer 1.21.1, both `DepthAttached::setDepth()` and `Depth::parallaxFor()` clamp to `[-1, 1]`.
   Its `autotests/stereodepthtest.cpp` explicitly checks that depth 2 with a popped limit of 4 gives 4.
   A design requiring a logo at twice that limit needs the explicit artwork multiple of stereo-layer 1.22.0 before its QML can express the requested result.
   Keep the requested design and report the missing primitive; do not call `StereoDepth.depth: 2` a working exception.
2. Preserve a former splash under another look-and-feel package identifier.
   Plasma Desktop 6.7.4's `kcms/ksplash/kcm.cpp`, `availablePackages()`, enumerates `plasma/look-and-feel` directories, clears each package's fallback and requires its own `splashmainscript`.
   `load()` requests that component and adds None itself.
   A second entry therefore needs its own metadata and `contents/splash/Splash.qml`, its pictures and a splash preview; it does not need another copy of the desktop defaults.
   Put both entries in the existing look binary package and name the retained entry in the required languages.
3. Change the system's default splash content while preserving its identifier and the person's own `ksplashrc`.
   Check Breeze, None and the retained entry from the actual chooser, then perform the upgrade from the published package.
4. Use a fresh login for each limit/output case and measure both eyes against the prediction.
   A compiled arithmetic helper is a source-level prerequisite check, not an installed-package test or a stereo rendering proof.

**Trap: the logo remains at the box's depth when its declaration is doubled.**
Cause: the published layer clamps in the setter and again in the arithmetic helper, so changing only the QML or only one clamp is insufficient.
Required repair: an explicit exception in the shared layer for the specially designed item, preserving ordinary bounds and the zero/2D/software behavior, followed by installed-library and real-login checks.
The repair is in stereo-layer 1.22.0: `StereoDepth.artworkDepthMultiple`, default 1.
A larger `depth` alone remains clamped.
Found by reading the published 1.21.1 source and compiling its `parallaxFor()` body unchanged: at 1920 wide, depth 2 returned 4 for limits 4/10 (expected 8) and 8 for 8/20 (expected 16); background, box and zero-limit controls passed.
The source check is `tests/splash-depth-contract.py` in the look recipe and takes the layer's `src/quick/stereodepth.cpp` as its argument.

## An item that must stand past the person's limit

The exception belongs in the shared layer, not in a second rendering route.
The edition's own loading-screen artwork declares it explicitly on one item:

```qml
Image {
    source: "images/kde.png"
    StereoDepth.depth: StereoDepth.Popped
    StereoDepth.artworkDepthMultiple: 2
}
```

`depth` remains a bounded fraction, `[-1, 1]`; the authored multiple is finite and at least 1, with 1 meaning ordinary behavior.
The multiple is never derived from media metadata and is not a setting for a person.
It is applied before rounding into device pixels, not to an already rounded parallax.
C++ uses `DepthAttached::setArtworkDepthMultiple()` and the five-argument `Depth::parallaxFor()`; the original four-argument helper stays bounded.
The attached property has no effect on a sleeping or 2D surface or with both limits zero.
Qt Quick's software renderer keeps the existing flat picture and one explanatory log line per window.

The default look depends on libstereo-layer1 >= 1.22.0.
The retained entry is `org.sparkystereo.boot-picture`, shipped with its own metadata, splash, pictures and preview in the same look package, with its name in all ten required languages.
It has no desktop defaults to apply.
The Sparky Black look's separate splash is unchanged.

Measured in fresh 1920x1080 logins on Stereo KWin +stereo3d58 with stereo-layer 1.22.0:

| Case | Background | Box and progress | Original logo |
|---|---|---|---|
| Sunk 10, popped 4 | +10 | -4 | -8 |
| Sunk 20, popped 8 | +20 | -8 | -16 |
| 125% output scale | +10 | -4 | -8 |
| Each of two 3D outputs | +10 | -4 | -8 |

Numbers are right minus left in device pixels; each part remains centred and the vertical difference is zero.
With limits zero or Qt Quick's software renderer, the two views are identical; the software case logs once.
A 2D output beside the 3D output is pixel-identical to the plain reference.
The actual Splash Screen page saved the retained entry, Breeze and None, and each saved choice was tested in another fresh login.
An upgrade from the published look preserves Breeze and None byte for byte in the person's configuration.

### Traps found during qualification

- **Symptom:** the translucent box measures 3 px where its edge should be 4 px apart, or its progress border follows the background in the matcher.
  **Cause:** the original box's alpha is at most 84/255; raw colour matching includes the differently shifted background behind it.
  **Fix:** measure the sharp border's position in each eye, using the derivative peak of an averaged edge profile, and use a separate top edge for vertical displacement.
  **Found by:** source alpha inspection and the edge profiles: the reference border was at x=751, the left at 753 and the right at 749, giving -4 and mean centre shift zero.
  `measure-regions.py` in the login rig supports boundary regions for this case.
- **Symptom:** a periodic background matches a different repetition when another output is present.
  **Cause:** a small mean-colour difference across captures biases raw matching of a dark repeating texture.
  **Fix:** remove each candidate region's mean before measuring its translation; retain the raw-colour result as diagnostic evidence.
  **Found by:** the correct -5/+5 offsets became the unique best match after mean removal, with both still fitting the broad background shape.
- **Symptom:** a QML test says `parallaxFor ... is not a function`.
  **Cause:** `StereoDepth` resolves to the attached object in that context; a static method on the type is not an attached method.
  **Fix:** test the attached property from QML and both arithmetic overloads from C++.
  **Found by:** the QML test's actual TypeError; no callable QML helper is claimed.

The native suite passes 31 tests.
The library retains all 419 previous dynamic symbols and adds four, while the exported attached object's size remains 64 bytes on amd64.
The version-pinned consumers outside the layer cohort use minimum versions and need no rebuild for this addition; the layer's exact internal cohort is rebuilt together.
