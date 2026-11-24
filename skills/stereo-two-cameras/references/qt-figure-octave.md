# An Octave figure's 3D axes, fitted to the person's limits under an orthographic shear (GNU Octave)

**For** anyone giving a program that draws several orthographic 3D plots in one OpenGL canvas a stereo pair on the edition, where the program draws one picture upstream and we add the two eyes: which case it is, the shear of an orthographic view, the fit per axes from a measuring pass, how a Qt figure reads the person's depth limits, what a script's own separation property does now, Enable 3D as a figure default, the welcome example, the closed-form scene, the proofs and the traps.
Learned on GNU Octave 11.3.0 (Debian 11.3.0-1, the edition's `11.3.0-1+stereo3d3+lc1`, queue row 50 step 5, November 2026), on Stereo KWin 6.7.4 +stereo3d59, Mesa 26.1.6 +stereo3d29, qt6-base 6.11.2 +stereo3d23 and libstereo-declare 1.12.2.

## Which case it is

Grep upstream's own tree, never our patches: Octave 11.3.0's orig tarball has five lines with "stereo", all of them about audio; no `GL_BACK_LEFT`, no `StereoBuffers`, no `currentTargetBuffer`.
Its tracker (Savannah) and its GitHub mirror name stereo only for sound.
So a figure is a scene where we add the eyes: fitted to the person's limits, no separation setting (memory one-separation-one-place, stereo-two-cameras-scene-fit).
The edition's earlier patches (0001 to 0003, October 2026) added the figure property `stereo` and a separation property `stereoeyeseparation` (default 0.05) that decided the depth; patch 0004 replaces the property's effect with the fit.

## The shear of an orthographic view

Octave's axes draw orthographic: the modelview is `S(1,1,-1) * x_mat1` and the projection `glOrtho(0, W, H, 0, Z1, Z2) * x_mat2`, where `x_mat1` maps data to the camera's frame (its z is the distance `d` along the view) and `x_mat2` (viewport times projection scale) maps camera units to buffer pixels and keeps z (`axes::properties::update_camera`, `opengl_renderer::setup_opengl_transformation`).
Turning the eyes would be toe-in; each eye's projection is instead sheared about the camera target, after `x_mat2`'s factor: a point moves `xs * sh * (dt - d)` buffer pixels, `xs = x_mat2(0,0)`, `dt` the target's distance, `sh = -eye * t / 2` for the left (`eye = -1`) and the right eye (`eye = 1`).
So a point stands `D = xs * t * (d - dt)` pixels further right in the right eye: negative (in front of the screen) nearer than the target, positive behind it, zero on its plane.
Markers and text are drawn in window coordinates and get the same shift as the point they belong to (`stereo_shift`), so a label stays with its point.

## The fit, per axes

1. **A measuring pass.** Before the left eye, Qt's `paintGL()` for the left buffer draws the whole figure once with no shear (the camera between the eyes), then the left eye draws over it.
2. **One read per 3D axes.** Octave clears the depth buffer at the start of every axes (`setup_opengl_transformation`), so the read comes at the end of `draw_axes`, after its children and before the next axes: every pixel below the cleared depth 1.0 belongs to this axes.
   The depth of an orthographic view is linear in the distance: `d = ((2b - 1)(Z2 - Z1) + Z1 + Z2) / 2` for the window depth `b`.
   Text and markers are textured quads at their anchor's depth with the depth test on, so they count where they are drawn; a translucent face writes depth too (Octave never calls `glDepthMask`), so it counts at its own depth, not at a weighted mean.
3. **The separation** of each axes is the smallest of `popped / (xs (dt - dnear))` and `sunk / (xs (dfar - dt))` for the sides that exist; nothing off the target's plane gives no depth (an orthographic view has no infinity).
   It is kept by the axes' handle and used by both eyes; a 2D axes (a legend, a colour bar, a 2D plot) is never sheared and never measured.
4. **The limits** come in the figure buffer's pixels from libstereo-declare: Wayland `stereo_depth_wayland_get_buffer_limits()` with the top-level window's `wl_surface` (`QPlatformNativeInterface::nativeResourceForWindow("surface", window()->windowHandle())`, the private header `<QtGui/qpa/qplatformnativeinterface.h>`, reached in Octave's autotools build with `-I$(pkg-config --variable=includedir Qt6Gui)/QtGui/$(pkg-config --modversion Qt6Gui)` and `qt6-base-private-dev`; a private header binds the package to the Qt it was built with, so `octave` depends on `qt6-base-private-abi (= Qt's upstream version)`, set in `debian/rules` as OpenSCAD's recipe does, which `libqt6core6t64` provides), X11 `stereo_depth_x11_get_buffer_limits()` on the drawing area's own window (`winId()` of the stereo `QOpenGLWidget`), read four times a second; a change redraws the figure.

## The options and what is told

- **Enable 3D** is the figure property `stereo`'s default (`set (0, "defaultfigurestereo", ...)`), set in the site `octaverc` from the preference `sparky_stereo`/`enable_3d` (default true), and changed in every Qt figure's Tools menu ("Enable 3D (applies to new figures)"): a figure chooses its OpenGL buffers when its window is made.
  A script can still make a figure with `"stereo", "off"` or `"on"`.
- **"3D display settings..."** in the same menu runs `systemsettings kcm_kscreen`, else `kcmshell6 kcm_kscreen`, and says so when neither exists.
- **`stereoeyeseparation`** stays a figure property a script can read and set; it no longer decides anything, and a script that sets it to another value is told once that the depth follows the limits in the desktop's 3D settings.
- **Told once, in the command window, in the person's language:** the limits not offered, not delivered after two seconds, not readable; the depth not readable; a figure that asked for stereo buffers and got none on a desktop that offers them.
  A desktop without stereo buffers gets one picture and nothing said, unless the person turned Enable 3D on themselves.
  The C++ side hands a key to an m-file (`sparky_stereo_tell`) through the canvas's `interpreter_event`, so the sentences live in one table (`sparky_stereo_text`, ten languages, chosen from `LANGUAGE`, `LC_ALL`, `LC_MESSAGES` and `LANG` as gettext chooses).
- **The welcome** (Daniel, 2026-10-10: "Octave: opens with a nice 3D example as an invitation, with an "Open empty" option"): the GUI's site `octaverc` opens a Klein bottle in its own figure; its menu Welcome, Open empty turns it off for the next starts (the preference `open_with_example`).
- **One output.** Only the drawing area asks for stereo buffers (its own format): the edition's Qt gives the stereo `QOpenGLWidget` a native window of its own and Mesa declares it, so the menus, the toolbar and the controls stay one picture.

## The closed-form scene

`view (0, 0)` in a cube plot box (`axis ([-1 1 -1 1 -1 1])`, data and plot box aspect ratio 1), `axis off` so nothing but the scene writes depth: a point's distance from the camera target is then half its y coordinate in plot box units.
A red square at y = -0.6 stands 0.30 in front, a blue one at y = +1 stands 0.50 behind, and a checkerboard `surf` of the known function y = 0.5 z runs from -0.225 to +0.225 between them.
The popped limit decides (4 / 0.30 < 10 / 0.50), so red stands at the popped limit and blue at `popped * 0.50 / 0.30`: -4.000 and +6.667 at 10 sunk and 4 popped, -8.000 and +13.333 at 20 and 8.
The prediction needs only the scene and the limits, not the window: the separation follows the axes' scale (the trace showed 0.0390 in a 560-pixel figure and 0.0168 once maximized) while the disparities stay -4 and +6.667.
On the published build (the property's 0.05) the same scene measured red -12.0 and blue +20.0, the ratio of the closed form, past the sunk limit.

## Proof (development build laid over the published package, Stereo KWin's virtual output 1920 x 1080, one fresh session per row)

| Row | Expected | Measured |
|---|---|---|
| Debian's 11.3.0-1+b1 | one view | 1920-wide capture, nothing declared |
| Published +stereo3d2, `stereo` on | a pair at the property's depth | only the drawing area declared (0 pixels differ outside it); red -12.0, blue +20.0; 62 % of blocks inside 10/4 |
| A new account, 10/4 | -4.000, +6.667; every block inside; 0 pixels outside the area | the trace's distances 0.300 in front and 0.500 behind the target, separation 0.0390, predicted -4.0000 and +6.6673; red -4.0, blue +6.0 (whole pixels); 1,436 blocks from -4 to +6, all inside; 0 pixels outside the area (3, 80, 1914 x 975 from the wire); rows aligned |
| Live change to 20/8 (kwinrc and KWin's reconfigure, nothing sent to Octave) | -8.000, +13.333 | red -8.0, blue +14.0, every block inside |
| Rotate by a drag (`rotate3d`), `camzoom`, a click on the red square | every block inside; the pick as in 2D | view [-17.0 3.4]; every block inside at each step; 0 pixels outside; the current object the red surface, as in Debian's build |
| `surf (peaks (40))` with its axes, grid, ticks and title | every pixel inside | 1st to 99th percentile -3.65 to +3.99 against the trace's -4.000 and +4.49; 31 of 5,899 blocks at about +-20 px, each more than 5 px from the median of its neighbours: false matches one mesh cell away |
| Enable 3D off against Debian's, five views (start, rotate, after the drag, zoom, pick) | 0 pixels in the area | 0 of 1,866,150 in each view, 0 outside |
| A 2D figure (3D on) against Debian's | 0 pixels | 0 in the area, 0 outside |
| Limits not offered (libstereo-declare's calls answer `-ENOTSUP`), German | told once; one picture in both eyes | "3D-Tiefe: Dieser Desktop bietet keine Tiefengrenzen, deshalb sehen beide Augen dasselbe Bild" once; still declared; eyes equal |
| `set (gcf, "stereoeyeseparation", 0.2)`, Portuguese | told once; the depth unchanged | told once; red still -4.0 |
| The X11 route (`QT_QPA_PLATFORM=xcb` under Xwayland); NVIDIA through zink | as above | red -4.0, blue +7.0; red -4.0, blue +6.0; every block inside |
| The GUI's start, an account that used the GUI and a new one (Octave's first-run assistant first) | the welcome as a pair | a pair; 0 pixels differ outside the welcome figure; 753 blocks from -3.34 to +2.36 |
| Tools, Enable 3D off by keys (German), then a new figure | the choice kept; the new figure flat | preference 0, default off, the new figure `stereo` off, still one declared surface on the wire |
| Tools, 3D display settings, in a session with neither program (German) | told once | "Die Anzeigeeinstellungen konnten nicht geöffnet werden." once |
| `print -dpng` of a 3D figure | as the published build writes it | 3840 x 1080, the window once per eye side by side (red centre 776.5 left, 772.5 right), no stereo mark; Debian's 1920 x 1080 |

## Proof of the package (octave 11.3.0-1+stereo3d3+lc1 installed by apt from the stage, the same rig, one fresh session per row)

Installed over Debian's 11.3.0-1+b1: octave and octave-common upgraded, nothing removed; over the published +stereo3d2+lc1 the same; `dpkg --audit` clean both ways.
Against the published packages: no file left or came in `octave`, `octave-dev` and `octave-doc`; `octave-common` gains the three site m-files; `octave` gains `libstereo-declare1 (>= 1.12.2)`, `libwayland-client0` and `qt6-base-private-abi (= 6.11.2)` in Depends.

| Row | Expected | Measured |
|---|---|---|
| Debian's 11.3.0-1+b1; the published +stereo3d2 with `stereo` on | one view; a pair at the property's depth | one 1920-wide view, nothing declared; a pair, only the drawing area declared, red -12.0, blue +20.0 |
| A new account, 10/4 | -4.000, +6.667; every block inside; 0 pixels outside the area | the trace: separation 0.0390, then 0.0168 once maximized, disparities -4.0000 and +6.6673 at both; red -4.0, blue +6.0; every block from -4 to +6; 0 pixels outside the area (3, 80, 1914 x 975); rows aligned |
| Live change to 20/8 | -8.000, +13.333 | red -8.0, blue +14.0; every block inside |
| Rotate by a drag, `camzoom`, a click on the red square | every block inside; the pick as in 2D | every block inside at each step, 0 pixels outside; view [-16.99 3.40]; the red surface picked |
| `surf (peaks (40))` | every pixel inside | 1st to 99th percentile -3.65 to +3.99 against the trace's -4.000 and +4.49; the 31 blocks outside each a false match one mesh cell away, none agreeing with its neighbours |
| Enable 3D off against Debian's, five views; a 2D figure (3D on) against Debian's | 0 pixels | 0 of 1,866,150 in each view, 0 outside; 0 and 0 |
| Limits not offered (German); `stereoeyeseparation` set by a script (Portuguese) | told once each; eyes equal; the depth unchanged | told once, still declared, eyes equal; told once, red still -4.0 |
| The X11 route; NVIDIA through zink; a 2D screen (Xvfb) | as above; one view, nothing said | red -4.0, blue +7.0; red -4.0, blue +6.0; one 1920-wide view with both squares, nothing said |
| The GUI's start, an account that used it and a new one | the welcome as a pair, 0 pixels differ outside it | both pairs, 0 outside; 704 blocks from -1.97 to +1.16 and 753 from -3.34 to +2.36 |
| Tools: Enable 3D off (German), then a new figure; 3D display settings with neither program | the choice kept, the new figure flat; told once | preference 0, default off, the new figure flat, one declared surface; told once |
| `print -dpng` of a 3D figure | as the published build writes it | 3840 x 1080 as the published build's; Debian's 1920 x 1080 |

The edition's m-files in the installed package: 359 checks, none failed.
A session without X11 (no `DISPLAY`): the published build says "X11 DISPLAY environment variable not set" and has no graphics toolkit at all; this build draws the figure, because its build dependencies now bring `wayland-client.h` and Octave's own configure turns on its Wayland display code (`cdisplay.c`), which Debian's build leaves off.

The edition's m-files alone (`octave-cli`): 359 checks pass (every sentence in ten languages with its placeholders, the language chosen from `LANGUAGE`, `LC_ALL`, `LC_MESSAGES` and `LANG` as gettext chooses, told once, the 2D desktop told only after the person's own choice); the same test fails on the published site files, which have no sentence table.

## Traps

- **A script's own preference read writes it.** **Symptom:** a new account's first start already has `enable_3d` set, so a sentence meant only for a person who turned Enable 3D on is said to everyone. **Cause:** Octave's `getpref (group, pref, default)` creates the preference with the default when it does not exist (`addpref`, its own help text). **Fix:** read a preference only through `ispref (...) && getpref (...)`, in the site `octaverc`, the menu, the welcome and every test script. **How found:** the rig's log line printed the preference before any choice had been made.
- **A library built over an older build keeps an object of the old class layout.** **Symptom:** the patched figure dies at its first paint, `SIGSEGV` in `GLWidget::draw` (gdb's backtrace in the container), exit 139. **Cause:** the work tree was copied into the development tree with `rsync -a`, which keeps each file's time; the files had been edited before the baseline build's objects were made, so make rebuilt only the file edited later (`GLCanvas.cc`), and liboctgui used a renderer class with new members while liboctinterp kept the old one. **Fix:** copy by content without the source's times (`rsync -rlpgoD --checksum`), so a copied file is newer than its objects; after a header change check the make log for every file that includes it. **How found:** the make log listed two compiled files where `gl-render.h`'s six includers were expected.
- **Automake refuses a pkg-config link line in `LIBADD`.** **Symptom:** `autoreconf` stops: "linker flags such as '--libs' belong in 'libgui_liboctgui_la_LDFLAGS'". **Cause:** automake reads the `--libs` word of `$(shell $(PKG_CONFIG) --libs stereo-declare)`. **Fix:** write the library (`-lstereo-declare`, pkg-config's own Libs line) in `LIBADD`; compile flags through `$(shell ...)` in `CPPFLAGS` are accepted.
- **The wire's last values are the window's closing.** **Symptom:** the analyzer placed the 3D area at 560 x 470 on a maximized figure and counted the depth as pixels "outside" the area. **Cause:** Octave shrinks the figure's drawing area while it closes, after the captures. **Fix:** read the wire only up to the capture's time (the case log's time of the capture). Mesa's declaration on Octave's figure is `kde_stereo_content_manager_v1.create(new id kde_stereo_content_v1, wl_surface)`, not `get_stereo_content`.
- **Whole-pixel edges.** Octave draws without antialiasing, so each eye's shift is rounded: a predicted +6.667 measures +6 (two shifts of 3.33 rounded to 3). Compare edges and colour centroids within one pixel; the trace's predicted extremes are exact.
- **A GUI row with the wire trace hides what the GUI says.** **Symptom:** after Octave's first-run assistant the GUI showed no welcome, and its command window was full of `wl_surface` lines. **Cause:** Octave's GUI shows its own stderr in its command window, and `WAYLAND_DEBUG=client` filled it. **Fix:** no wire trace in GUI rows; place the welcome by KWin's client rectangle of its window and require 0 differing pixels outside it. **How found:** the capture of the GUI after the assistant.
- **Octave's first-run assistant.** A new account's GUI start shows "Welcome to Octave!" first (Enter on Next, Next, Finish); the edition's welcome follows it. An account that used the GUI has `global_skip_welcome_wizard=true` under `[General]` in `~/.config/octave/octave-gui.ini`; an empty file does not skip it.
- **A told sentence without "3D" in it.** A filter of the program's output on "3D" dropped the German "Die Anzeigeeinstellungen konnten nicht geöffnet werden.": read the whole output for told sentences.
- **The installed GUI opens on a warning, the development build did not.** **Symptom:** the package's GUI rows found no welcome window; the capture shows one dialog, "Octave Documentation: Could not setup the data required for the documentation viewer. Maybe the Qt SQlite module is missing?", and the published +stereo3d2 shows the same in the same image. **Cause:** the rig images install without Recommends, and Qt's SQLite plugin (`libqt6sql6-sqlite`) comes only as a Recommends of `libqt6sql6`; Octave's help engine needs it, and the dialog is compiled only with `ENABLE_DOCS` (`libgui/src/documentation.cc`), which the package has and the development build (configured without documentation) did not. **Fix:** the green image installs `libqt6sql6-sqlite` beside Xvfb, as a default installation would. **How found:** the window list of the capture held only "Octave Documentation"; the picture showed the dialog; `dpkg-query` in the three images and on the station.
- **Without X11, Octave's resolution comes out negative on KWin's virtual output.** **Symptom:** with `DISPLAY` empty, `get (0, "screenpixelsperinch")` is -38100 and Octave warns once "opengl_renderer: Error 'invalid value' (1281) occurred drawing 'text' object". **Cause:** the virtual output announces `wl_output.geometry(0, 0, -1, -1, ...)`, a physical size of -1 mm, and Octave's `cdisplay.c` falls back to 96 only for exactly 0 mm (`wd_mm == 0 || ht_mm == 0`, unchanged on upstream's default branch on 2026-11-23), so it divides by -1 (the mean of 1920 x 25.4 / -1 and 1080 x 25.4 / -1). With Xwayland's `DISPLAY` the X11 path runs first and gives 96.13. **How found:** the case's Wayland trace of the run without `DISPLAY`. Not filed; a real screen announces its millimetres.
- **A private Qt header and no private ABI dependency.** **Symptom:** none in any row: the build, the Lean Code gate and the link gate pass, and `dpkg-shlibdeps` adds only `libqt6gui6 (>= 6.11.2)`. **Cause:** `QPlatformNativeInterface` is Qt's private API, with no compatibility between Qt versions; nothing derives a dependency from an included header. **Fix:** `qt6-base-private-abi (= Qt's upstream version)` through a substitution in `debian/rules`, as OpenSCAD's recipe has it. **How found:** comparing the finished recipe with OpenSCAD's, the step's model for a Qt 6 view; the first package was built and proved without it and was built again.
- **A mesh matches one cell away.** On `peaks` with its mesh lines 0.5 % of blocks matched at about +-20 px, one cell, though the program's own nearest and farthest pixels give -4.000 and +4.49; a surface's disparity is continuous, so a block more than 5 px from the median of its neighbours (within 24 px) is a false match, and none was a real one.
