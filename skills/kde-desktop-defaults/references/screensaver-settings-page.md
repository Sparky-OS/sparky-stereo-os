# The Screensavers page

**Check freshness first.**
Written on 2026-11-25 (queue row 96) from `sparky-stereo-screensavers` 0.1.0, gl-stereo 0.4.6, Plasma 6.7.4 and Stereo KWin 6.7.4 +stereo3d64.
The recipes are in [the build tree](https://github.com/Sparky-OS/sparky-stereo-os-build): `sparky-os/packages/sparky-stereo-screensavers`, `gl-stereo`, `sparky-os/packages/screensavers-links-96` and `sparky-os/packages/video-wallpaper`.

Daniel Ramos asked for it twice (2026-10-14 and 2026-11-24): "the classical screen saver selection", a page of its own in System Settings with the list, a small preview of the selected saver and a button that shows it on the whole screen, for every screensaver and not only the OpenGL ones, linked from the pages where a person looks for it.
KDE had such a page and removed it: `kcontrol/screensaver` of kde-workspace, last released in KDE Workspace 4.11.22, removed by Martin Gräßlin in 2013 (invent.kde.org `unmaintained/kde-workspace`, commit 7f176542).
Its layout is what the page carries; its code (Qt 4 widgets, a saver reparented into the page with `XReparentWindow`) has no meaning on Wayland.

## The page's parts and where each value lives

Module `kcm_sparkystereo_screensavers`, category `appearance`, beside Wallpaper.
The rule that keeps it small: the page edits only the keys that already exist and keeps no copy of any.

| Part | Where it lives |
|---|---|
| The list: every saver the installed packages ship | read from `/usr/share/gl-stereo/catalogue.json` and `savers.json` (the stereo catalogue, drawn as a pair) and from `/usr/share/xscreensaver/config/*.xml` with its program in `/usr/libexec/xscreensaver` (XScreenSaver's 2D savers, one view) |
| Which catalogue savers cannot be offered, and why | `catalogue.dropped()` of gl-stereo-savers, the code the show's controller runs, called through `python3 -I`; the page only turns each reason into a sentence |
| The tick of a catalogue saver | `stereoshowrc [General] DisabledSavers` (the savers left out) |
| The tick of a 2D saver | `stereoshowrc [General] FlatSavers` (the savers added; empty unless a person ticks one) |
| Show on or off, start after, change every | `stereoshowrc [General] Enabled`, `IdleSeconds`, `CycleSeconds`; Screen Locking edits the same three |
| "Lock screen automatically", the two background kinds | read only: `kscreenlockerrc [Daemon]` and `[Greeter] WallpaperPlugin`, and the `wallpaperplugin` of each desktop in `plasma-org.kde.plasma.desktop-appletsrc`; each has a button to the page that edits it |

Write with `KConfig::Notify`: the running show and the other page follow through `KConfigWatcher`.
A name the store holds for a saver that is not installed now is written back as it was.

## A saver as a preview in a settings page

A saver never runs inside System Settings and never on the session's display.

1. **A helper starts it on a private display.** `sparky-saver-preview` (Python, in the page's package) starts an Xvfb as the show's controller does, starts the saver on it, and ends when its standard input closes.
   A catalogue saver is started through gl-stereo's `announce` with the receipt's own command and environment, only the view's size and the share replaced; the layer hands its pairs to the page itself over `GL_STEREO_FRAME_FD`.
   A 2D saver is started with `-window-id` on a window the helper makes (`flat.Grabber` of gl-stereo-savers 0.4.6) and the helper reads that window back with `XGetImage`.
   Both arrive as frames of the show's channel: one sealed memory file each, checked for envelope, size, format, owner and seals before a byte is read, one frame outstanding.
2. **The pair is a surface of its own over the rectangle.** System Settings draws a page into a `QQuickWidget`, which has no `wl_surface` of its own, so nothing can be laid under a hole in the page.
   `QQuickRenderControl::renderWindowFor(item->window(), &offset)` gives the window that is on screen and where the page sits in it; the page makes a `wl_subsurface` of that window's surface, places it **above** at the rectangle, gives it an empty input region, sizes it with `wp_viewport`, and declares it once with `stereo_declare_wayland_format(surface, STEREO_SBS_FULL)`.
   The page draws nothing over the rectangle, so no hole is needed.
3. **Whole device pixels at every scale.** The rectangle's corner is put on a multiple of 4 of the window's pixels and its width on a multiple of 8, inside a black frame a few pixels larger: whole device pixels at 100, 125, 150 and 175 %, and an even view width.
4. **When the pair cannot be shown, one view is, and the page says so.** No stereo compositor, a refused declaration, or a rectangle cut by the window or by an ancestor that clips (the side column scrolled): the item paints the left view as an ordinary picture and a line under it says why.
5. **Depth: the person's limits, at the size shown.** The page watches the limits on its own surface (`stereo_depth_wayland_watch_limits`; Stereo KWin answers `depth_limits(sunk, popped)` for a sub-surface too) and converts them with `stereo_depth_limits_for_buffer(limits, screen width, buffer width, shown width)`.
   The layer's separation is a share of one view's width, so the page asks for `100 * sunk_in_buffer / buffer_width`: a preview 320 px wide and the whole screen then show the same pixels of separation (measured: 5.3 and 5.7 px for the same saver on a 1280 px screen, where the receipt's fixed 0.5 would give 1.3 in the preview).
6. **The full-screen preview** is a `QRasterWindow` shown full screen on the page's screen, black, with the same surface code over the whole window; it ends on a key, a button, a wheel step, a touch, or a pointer move of more than 10 px from where the pointer was (XScreenSaver's own hysteresis).

## A System Settings page that links to another

`KCM.KCMLauncher.openSystemSettings("kcm_NAME")` from `org.kde.kcmutils` opens the page inside System Settings (the running one, when there is one).
Put the button where the page already has its actions (`actions: [ Kirigami.Action { ... } ]` of the KCM's root, the header's tool bar); PowerDevil has a row of related pages (`MostUsedItem` in `kcm/ui/GlobalConfig.qml`).
The package that carries the button Depends on the package of the page it opens.
A KDE fork takes no `po/` change: the string's translations go in `sparky-os/translations/PROJECT-FEATURE.po.patch`, last in the series.
One job builds all four successors (`screensavers-links-96/build-job.sh`, a table of predecessors pinned by the hash of each `.dsc`).

## Adding a saver to the list

- **A 2D saver:** install its program in `/usr/libexec/xscreensaver` and its XScreenSaver description file in `/usr/share/xscreensaver/config/NAME.xml` (the title is the root element's `_label`, the authors the "Written by ..." sentence of `_description`). Nothing else: the page lists it, previews it, and the show takes it when a person ticks it.
- **A saver with depth:** it needs a receipt in gl-stereo's catalogue, made by the requalification ([native-linux, requalifying the gl-stereo savers](../../native-linux/references/requalifying-gl-stereo-savers.md)); then it is listed as 3D and ticked by default.

## Traps

- **Symptom:** every capture of the rig is cancelled (`org.kde.KWin.ScreenShot2.Error.Cancelled`).
  **Cause:** KWin's virtual backend had no render node. **Fix:** give the container a card (the NVIDIA one through CDI); the programs under test still draw in software. **Found by:** `kwin.log`, "Failed to open drm node".
- **Symptom:** the measured pair lies 36 px below the rectangle the page logged.
  **Cause:** the page's rectangle is in the window's own pixels; a capture is in the screen's, and the title bar is between them. **Fix:** add the client corner KWin reports (`kwin_windows.py`, `cg`) before comparing. **Found by:** a saver that fills its whole view (`glmatrix`): the box of differing pixels had the rectangle's size, moved down by the title bar's height.
- **Symptom:** the first preview after the page opens has the saver's own separation; the log says the compositor gave no depth limits.
  **Cause:** the limits arrive a moment after the first request, later still while the window is not on an output yet. **Fix:** wait once (700 ms) for the first answer, and draw the saver again when `depth_limits` arrives or changes. **Found by:** `WAYLAND_DEBUG=client`: `depth_limits(10, 4)` 40 ms after `get_depth`.
- **Symptom:** the preview shows one view and says it does not fit, in System Settings' default window.
  **Cause:** the page's side column was wider than the page (566 px beside the sidebar), so the rectangle reached past the window. **Fix:** a page fits about 560 px; the preview is 320 by 180. **Found by:** the page's own log line with the rectangle, the window and the page.
- **Symptom:** at 125 % the preview's far side stands at 10.7 px where the limit is 6.7 (measured 9.0 px for a saver that should read 5.5).
  **Cause:** at a fractional scale `QScreen::devicePixelRatio()` is the next whole number (2) while `QScreen::size()` is in the desktop's own pixels, so "size times ratio" made a 1280 px screen 2048 wide. **Fix:** the screen's size times the window's `devicePixelRatio()` (1.25). **Found by:** the page's own log line (`screen 2048`) in the rig's 125 % row.
- **Symptom:** one move of the pointer does not end the full-screen preview.
  **Cause:** the first motion event was taken as the place to measure from, and a window that opens under a resting pointer gets an enter event, not a motion. **Fix:** take the place from `QEvent::Enter` too. **Found by:** `WAYLAND_DEBUG=client`: `wl_pointer.enter` at the button's place, then a single `motion`.
- **Symptom:** the rig's click lands 36 px above the button, or a row passes on one page and fails on another.
  **Cause:** as above, window pixels against screen pixels. **Fix:** compute the click from the page's logged rectangle plus KWin's client corner (`rig/button.py`), never from a picture alone.
- **Symptom:** the Power Management page says "The Power Management Service appears not to be running" in the rig, and the daemon says "Operation not permitted".
  **Cause:** the daemon's file capability cannot be granted to the rig's user, and a container has no system bus. **Fix:** run a copy of the daemon (a copy has no file capability) with `DBUS_SYSTEM_BUS_ADDRESS` on a `dbus-daemon` of the container's own, with stand-ins for UPower and logind (`rig/system-bus-fixture.py`).
- **Symptom:** plasmashell stops with "Aborting shell load: The activity manager daemon (kactivitymanagerd) is not running".
  **Cause:** `kactivitymanagerd` is not on `PATH`. **Fix:** start `/usr/lib/x86_64-linux-gnu/libexec/kactivitymanagerd` first.
- **Symptom:** an apt proof that adds SparkyLinux's repository plans to replace the edition's Qt with Debian's.
  **Cause:** the station's source file for SparkyLinux is named `sparky.sources`, the same name as the round's own source in the rig image, so copying it in removed the round from apt's sources and its 1001 pin had nothing to pin. **Fix:** copy it under another name; read `apt-cache policy` of one edition package before trusting a plan.
- **Symptom:** a container script stops with no message right after `apt-cache policy NAME | head -4 > file`.
  **Cause:** `set -o pipefail`: `head` ends first and the writer dies of SIGPIPE. **Fix:** no `head` behind a program whose status matters.
- **Symptom:** a button reads "Display _Monitor…".
  **Cause:** `&` is a mnemonic mark in a Qt Quick Controls button. **Fix:** `&&`, in the English and in every translation that keeps the sign.
- **Symptom:** `make` warns that `debian/rules` has a modification time in the future, and a second build differs in file times.
  **Cause:** a changelog entry dated later than the clock. **Fix:** date the entry before the build.
- **Symptom:** binding the Wayland globals from a plugin blocks or re-enters the toolkit.
  **Cause:** a roundtrip on the default queue dispatches the toolkit's own events. **Fix:** bind on a queue of your own (`wl_proxy_create_wrapper`, `wl_display_roundtrip_queue`), then move each bound proxy to the default queue (`wl_proxy_set_queue(proxy, NULL)`), or its events (a buffer's `release`) are never dispatched and the fourth frame never shows.
- **Symptom:** a gl-stereo rebuild stops at "untested layer binary".
  **Not met here, and how it was avoided:** before touching gl-stereo, rebuild its published source unchanged in the builder you will use and compare the layer's SHA-256 with the receipts'; when they are equal, a change that leaves `gl-stereo.c` and its includes alone keeps the receipts (0.4.6 built this way, layer f83c52ca..., no requalification).
- **Symptom:** the link gate refuses PowerDevil's successor: `sparky-stereo-graphics Depends libqt6gui6 (= 6.11.2+dfsg-5+stereo3d23+lc1) but none of the choices are installable`; with that solved, `previous edition dependency qualification failed; provide the matching previous sibling snapshot` for the published build.
  **Cause:** Debian's Qt in the archive was newer than ours (6.11.2+dfsg-8), and the gate applies only the pins that a supplied package ships: without the edition's policy package among them APT's candidate is Debian's, and an exact dependency takes the candidate only.
  **Fix:** put the published `sparky-stereo-apt` among the siblings, and again beside the previous packages (a folder of copies given as `SPARKY_LC_PREVIOUS_DIR`); SparkyLinux's own repository goes into `sources.json`, because the policy package depends on its `sparky-apt`.
  **Found by:** `case-*/policy-attempts.json` in the gate's scratch (`"enabled": []` before, the two preferences files after) and `apt-cache policy libqt6gui6` in the builder.
- **Symptom:** a build script stops with "unexpected EOF while looking for matching `'`" at a line that has no quote.
  **Cause:** an apostrophe inside `"${VAR:?the gate's folder}"`: bash reads a single quote in a parameter expansion's word as the start of a string, also inside double quotes. **Fix:** no apostrophe there; `bash -n` the script before the first run.
- **Symptom:** the image for a page's build stops with "Packages were downgraded and -y was used without --allow-downgrades".
  **Cause:** the edition's 1001 pin replaces newer Debian builds with ours. **Fix:** `--allow-downgrades` on that install.

## What the page does not do yet

- XScreenSaver's own per-saver options (the old page's "Setup..."): the description files list them, but their labels have no catalogue on the image and the show's controller takes no options yet.
- A saver as the desktop's background: a wallpaper kind of its own, with the pause rules Daniel set for the video background.
- The show itself still uses each receipt's fixed share (0.5), and the layer bounds only the far side: a saver whose scene comes in front of its convergence plane passes the popped limit.
