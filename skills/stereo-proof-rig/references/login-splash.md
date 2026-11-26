# A real login with the loading screen

A core limit of exactly 1 suppresses the piped core helper; a zero limit does not, as the [crash trap](../SKILL.md#traps-that-fooled-us) explains.

Load this to capture what a person sees between the login and the desktop: KSplash's loading screen on one or several virtual outputs, in a 3D mode or not, from a real `startplasma-wayland`, with both eyes of each screen and each level's disparity measured against a prediction.
Written for ORDER 571 (the edition's loading screen, 2026-11-15); what the splash is and why is in [kde-desktop-defaults, the loading screen](../../kde-desktop-defaults/references/loading-screen.md).

## The recipe

The scripts are in `scripts/login-splash/`; one fresh container and one fresh home per case.

1. **An image** of the packages under test on Debian testing, pinned by digest, with the edition's tree as an apt source (`mkrig.sh TAG REPO_DIR APT_CONF_DIR [EXTRA_DEB_DIR]`): KWin, `plasma-workspace`, `plasma-desktop`, `kactivitymanagerd`, the look package, `libkscreen-bin` (for `kscreen-doctor`), `dbus-daemon` and `dbus-bin`, Python with GI, NumPy and Pillow. Debs given in `EXTRA_DEB_DIR` are installed over it with apt, so their `Inst` lines are the upgrade's.
2. **The person's saved screens** (`login.sh`, step 1): KWin started once on the virtual outputs with `KWIN_VIRTUAL_STEREO_MODES=1`, each output's mode set with `kscreen-doctor` (the side by side 3D twin is the mode whose `stereo3D` is 1 in `kscreen-doctor -j`; mode ids count across outputs), KWin stopped so it writes `kwinoutputconfig.json`, and each twin saved with the output's `otherStereoFormats` switch on, as Display Settings saves it.
3. **The person's own settings**: `kwinrc` `[StereoDepth]` `PoppedLimit` and `SunkLimit` written with `kwriteconfig6`, as System Settings writes them, or left unsaved; a `ksplashrc` of the person's when the case needs one.
4. **The login**: `dbus-run-session -- startplasma-wayland`. Without systemd it takes Plasma's classic start: `plasma_session` starts `kwin_wayland_wrapper --xwayland`, then `ksplashqml`, then the autostart phases. The wrapper runs `kwin_wayland` from `PATH` with its own arguments added, so a two-line shim first in `PATH` adds `--virtual --output-count N --width W --height H`; nothing installed is changed. KWin needs the render node (`--device /dev/dri/renderD128` and its group) and `--cap-add SYS_NICE`; `KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1` lets the rig capture.
5. **What happened, from KWin**: a KWin script enabled in the person's `kwinrc` (`splashlog`) prints every window's class, type, output and frame from KWin's first moment; the splash's moments are its `ADDED ksplashqml` and `REMOVED ksplashqml` lines.
6. **Captures** (`shot.py`): ScreenShot2 `CaptureScreen` of each output at chosen seconds after the splash maps: a 3D output gives both eyes side by side, left eye first, each at the output's size.
7. **Measures** (`measure.py`): `eyes` (pixels that differ between the eyes and the shift of the whole right eye that fits the left), `gear` (where a template, KDE's gear, is found and how well), `levels` (each part's shift in each eye against the same login on a 2D output, its disparity left minus right, beside the prediction `layout.py` writes from the person's limits). The moving electrons are not measured by these scripts: a first try (each eye's still picture as the minimum of several captures, an electron as what is brighter) found about 55 blobs per capture where at most 15 sprites exist, so its pairs were mostly not electrons; a measure of moving parts needs the frame's own clock (a deterministic mode) first.

A run: `run-case.sh IMAGE OUTDIR MODES="3d 2d" OUTPUTS=2 HOLD=6 SHOTS="1 3" POPPED=8`; a timing run: `NOSHOT=1` and no `HOLD`, five runs on each build, alternated.

## Traps

- **Symptom:** every capture fails with `org.kde.KWin.ScreenShot2.Error.Cancelled`. **Cause:** no render node in the container, so KWin composites without OpenGL ("Failed to open drm node" in the session log) and the screenshot effect has nothing to read. **Fix:** give the render node and its group. **Found by:** the session log's first KWin lines.
- **Symptom:** the login comes up in 2D although the setup put the output in its 3D twin. **Cause:** KWin restores a hand-switched twin only when the output's "Other stereo formats" switch was saved on (`canRestoreVirtualMode()` in `src/outputconfigurationstore.cpp`); `kscreen-doctor` of that time set the mode, not the switch (libkscreen +stereo3d12 has `output.NAME.otherStereoFormats.enable`). **Fix:** save `otherStereoFormats: true` for each output whose saved mode carries the virtual stereo flag (0x20000). **Found by:** `kscreen-doctor -o` inside the login showed the 2D mode current, and the source of the restore.
- **Symptom:** with two outputs the second stayed 2D. **Cause:** `kscreen-doctor`'s mode ids count across outputs (the second output's twin is 7, not 2). **Fix:** pick each output's twin by its `stereo3D` value in `kscreen-doctor -j`. **Found by:** the setup's arguments printed `mode.None`.
- **Symptom:** the splash is gone before the first capture. **Cause:** a container's Plasma is ready in about two seconds. **Fix:** in capture cases only, the person's autostart folder holds `org.kde.plasmashell.desktop` with `Exec=sh -c 'sleep N; exec /usr/bin/plasmashell'` (`HOLD=N`); never in timing cases. **Found by:** KWin's `REMOVED ksplashqml` 1.4 s after `ADDED`.
- **Symptom:** waiting for the `ksplashqml` process to end took over a minute, once. **Cause:** in that run (without the render node) plasmashell's call to set the "desktop" stage D-Bus-activated `org.kde.KSplash` again after the splash had quit. **Fix:** the splash's moments come from KWin's log, not from the process list.
- **Symptom:** a part's measured disparity is 1 where 4 is predicted, or 0 where 2 is. **Cause:** masks made from a picture's alpha and placed by the layout's sums miss Qt's own scaling by a pixel, and the wordmark is drawn with alpha 101 at most, over a background that does not move: the background dominated. **Fix:** a part's pixels are the brightest 15 % of the plain picture inside its box; the match then follows the part (error 1.2 against 12 for the next shift). **Found by:** measuring the same part on hand-picked boxes of its letters.

## Extending the login cases (ORDER 672)

An isolated tool environment may not expose the host's render-node path to `stat` even though Docker can pass that node to a container.
Set `RENDER_GROUP` to the group measured inside a preflight container; `run-case.sh` uses it instead of probing the hidden host path.
Keep the render node and group explicit, and keep `--ulimit core=1`.

`DESKTOP_PROBE` names a mounted script to run in the same private session bus after the desktop capture, for example a real Splash Screen KCM opened with `kcmshell6`.
A failing desktop probe propagates its status through the session and container.
`EXPECT_NO_SPLASH=1` checks a login with None selected: no splash window may map, and the desktop is still captured.
For fake pointer clicks on a newly created device, allow the device to settle and wait after moving before pressing; the first immediate move/click sequence saved nothing, while the delayed sequence saved the selected entry.
Log `workspace.cursorPos` when distinguishing an input problem from the page's behavior.

`measure-regions.py PAIR PLAIN REGIONS.json` measures both horizontal and vertical offsets against a separate plain login.
Ordinary regions use boundary-weighted colour matching, optionally with `normalize_mean` for a periodic background.
For translucent artwork, use `method: boundary`, `x_edge` and `y_edge` rectangles: it measures the strongest visible edge rather than matching the changing colour behind it.
Report the right-minus-left disparity, both per-eye positions, the mean centre shift and the vertical difference beside the prediction.
The original `measure.py` uses left minus right; state which convention a table uses.

Before running a saved rig recipe, run `bash -n` on it.
The image builder's required-variable error word contained an apostrophe that left a quote unmatched inside the parameter expansion.
An isolated `bash -n` probe reproduced the failure for that error word and passed with the plain wording; the tag substitution was not the cause.
The message is now plain, and tag sanitization is also split into two simple substitutions.
Mark every stereo capture with PNG's sTER chunk, mode 1 for left-first, and keep it as .pns.
The capture JSON's `stereo` field identifies a pair; a wide aspect ratio alone is not a general stereo detector.

`CONFIG_SEED` names a mounted home tree to copy before setup for a saved-choice or package-upgrade case.
Keep the seed read-only, use a fresh case directory, and compare package-upgrade configuration hashes separately from changes Plasma itself saves during login.

`LOGIN_LANG` selects the private login locale, defaulting to C.UTF-8 as before.
Generate the locale in the image and use one fresh login per language when probing a localized page or a locale-derived default.

`EXTRA_PACKAGES` adds verified packages to mkrig's baseline, such as Sonnet's backend and dictionaries, the KCM launcher and the notifications applet's plasma-pa dependency.
`USER_SETUP` names a mounted script run after the private home and LANG are set, before the setup compositor and Plasma start.
Use it to reproduce a Desktop created before KIO, or an existing account copied by CONFIG_SEED; do not overwrite the saved settings being tested.
The lifecycle logger includes each window's internal ID so a popup can be distinguished from the desktop and panel.
Start Plasma through setsid to keep teardown signals inside its session; a German probe completed its assertions but its shared process-group teardown returned 143, while the isolated Spanish case returned 0.
Do not turn a teardown status into a successful assertion; retain the phase logs and repeat the affected case with the corrected fixture.

A rig bootstrap can create a preference or source file without installing its owning apt package.
Installing that package later with confold correctly preserves the local file, which can hide a new distributor default from the test.
For an upgrade proof install the actual published predecessor first, check that its shipped pin is unmodified, then upgrade it.
Keep the local frozen source separate or use apt's Dir::Etc::sourceparts override for an isolated policy query.

## A theme's loading screen with the logo optional and the system's name from os-release (queue row 125)

Kubabbar Glass's loading screen shows the Sparky logo only where the edition's artwork package installs it (`/usr/share/pixmaps/sparkyos.png`), the theme's name, and the system's name and version read from the running system, so a distribution without the logo shows the theme's name in its place.

- **The system's name** comes from KCoreAddons' `KOSRelease` singleton (`import org.kde.coreaddons`, KF 6.11 and later): `KOSRelease.name` and `KOSRelease.version`. QML's XMLHttpRequest cannot read a local file unless the process sets `QML_XHR_ALLOW_FILE_READ`, which KSplash does not.
  When neither `/etc/os-release` nor `/usr/lib/os-release` can be read, `KOSRelease` gives the specification's defaults (name `Linux`, id `linux`, pretty name `Linux`, no version) and has no flag that says so (an upstream TODO in `src/lib/util/kosrelease.cpp`): treat exactly those defaults as "not read" and show the theme's name alone.
- **A logo at another package's path:** an `Image` whose `visible` follows `status === Image.Ready`, inside a `Column`, which closes the gap when the file is missing (Qt logs one "Cannot open" line). A one-colour white logo on a light window is drawn with `MultiEffect { colorization: 1.0; colorizationColor: TEXT }` (measured on the capture: 46,51,43 on the window's 205,205,202).
- **The boot splash's background** keeps its shape: `fillMode: Image.PreserveAspectCrop`, the boot splash's own cover rule (sparky-stereo-plymouth `gen-theme.py`).
- **Depth:** one `StereoDepth.depth` on the window; the logo, the texts and the boxes inside it follow it undeclared; the background is undeclared and stays at the screen.
- **The look package Depends on every QML module the splash imports** (`qml6-module-qtquick`, `qml6-module-qtquick-effects`, `qml6-module-org-kde-coreaddons`, `libstereo-layer1`): a module that fails to load leaves KSplash with its fallback package or nothing.

The cases, each a fresh login with `RUN_MOUNTS` (read only):

| Case | Mount |
|---|---|
| no logo | an empty folder over the logo's folder |
| another system | a file over `/etc/os-release` |
| os-release unreadable | a file of mode 000 owned by the run's user over both `/etc/os-release` and `/usr/lib/os-release`: a reader that is not root gets EACCES and `KOSRelease` logs "Failed to open os-release file!" |
| before the packages exist | the clone's theme folders over the installed ones |

`CARD=nvidia RENDER_GROUP=N` runs KWin on the NVIDIA card through CDI and the session's programs on Mesa's software renderer, for a station whose AMD card drives the person's screens.

[`splash_regions.py`](../scripts/login-splash/splash_regions.py) `PLAIN PAIR window|middle POPPED OUT.json` finds the window (or the middle of a look without one) in the plain capture, writes the regions for `measure-regions.py` (the window's left and top border edges, the logo and name; the middle and the top strip) with the predicted disparity, and prints how many pixels differ between the eyes outside it (the background at the screen: 0 expected).

Measured on Kubabbar Glass 20261126 in fresh 1920x1080 logins (right minus left, device pixels): the window, its logo and its name at -4 with the person's popped limit unsaved (KWin's default 4), -8 at a popped limit of 8, -4 at 125 % and 150 %; the menu bar look's middle at -4 and its strip at 0; no vertical difference; outside the window 0 of about 1.9 million pixels differ between the eyes.

Traps:

- **Symptom:** `measure-regions.py` stops with "operands could not be broadcast together" for a strip at the top of the screen. **Cause:** it searches three rows above the box, and the box started at row 0. **Fix:** start the box at row 4.
- **Symptom:** `bash -n` stops on a script at the end of a file. **Cause:** an apostrophe inside `${VAR:?message}` again (this page's earlier trap). **Fix:** a message without one.
