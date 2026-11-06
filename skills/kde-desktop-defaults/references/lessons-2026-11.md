# kde-desktop-defaults: lessons from the lanes of 25 October to 6 November 2026

Harvested by ORDER 429 from the accepted lane reports; each line names the lane it came from.
A trap gives its symptom, its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Recipes that worked

- Discover AppStream cache: `appstreamcli` compile of the Flatpak pool with --datapath; on failure Discover logs "Could not compile the AppStream cache, AppStream will compile it in this process" and the engine keeps a record (severity degraded, message id b329c1b8...), cleared when a good compile follows. Resident memory 1,056 to 368 MiB after a catalog change (lane discover-review-386)
- Shortcut change proof with real key events through KWin: Ctrl+Alt+Del, Ctrl+Esc, Ctrl+Shift+Esc open System Monitor; Ctrl+Alt+Esc opens the logout greeter; Meta+Ctrl+Esc kills the selected window while a control survives; saved Log Out assignments (Meta+Ctrl+F12, the old Ctrl+Alt+Del) tested; look package Depends on the matching workspace so a partial upgrade cannot leave a clash (lane time-shortcuts-359)

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: a KAuth policy built by kauth-policy-gen has an empty polkit `<message>` for some languages. Cause: the `.actions` file is parsed as QSettings INI, so an unquoted value with a comma is a list. Fix: quote such values (German and Polish needed it). Found by: lintian-free build output showing empty messages in de and pl (lane publish-kwin36-289)
- Symptom: about one lock in eight showed only the wallpaper's colour (5 failures in 42 runs). Cause: plasma-workspace TransientImage drops its picture once it is a texture, and the texture belongs to the window it was made for; moved to another window it drew nothing. Fix: read the picture again when the texture is released (red/green test; 0 in 15 runs after, 0 in 37 final cases) (lane wallpaper-depth-fix-291)
- Symptom: a Kirigami FormLayout with Repeater delegates inserted dynamically shows the problem/actions group out of order. Fix: give the group a stable parent layout, test visual geometry in more than one locale (real Portuguese LANG). Also a uid 1000 bubblewrap gate inside Docker may need unmasked /proc paths to mount its own proc (lane memory-kcm-protection-353)
- Symptom: a Plasma widget shows "Output 0.00 W", blank temperature, 0 RPM. Cause: the service returned an empty PSU (powerOut 0, volts/amps/watts {}) because its log said "Unable to get PSU temperature." every 3 s; the widget turned an empty answer into a real zero and never showed the "cannot reach" error. Fix: a hasData flag, "No PSU readings" note, clear the list on connection error (lane icue-link-widget)
- Symptom (video wallpaper): changing the wallpaper's Video setting from a playlist to a single video never starts the selected file (only `clip red.webm` opens, QML test `player.source` stays red). Cause: a Qt/QML derived binding: the synchronous URL change handler runs before `isPlaylist` updates and enters the playlist branch. Fix: correct main.qml ordering and ship a regression in the session smoke that copies a clip to `single.webm` and requires its decoder open trace (original exits 1, corrected exits 0). (lane video-port-278)
- Symptom: CI prints "all checks passed" and exits 0 although the linter exited 42 without JSON. Cause: a loop reading a process substitution under `set -euo pipefail` does not get the producer's status. Fix: capture the producer status, require one complete JSON document with the expected file count, accept qmllint exit 255 only with diagnostics (warning limit), reject crashes (controls: exit 42 and malformed JSON exit 5). (lane video-port-278)
- Symptom: the session smoke fails with an empty `played` string on Qt 6.8; plasma5support QML executable engine "missing" on Debian 13. Cause: older Qt emits no FFmpeg file open messages by default; trixie ships the executable dataengine in plasma-workspace while newer Debian ships it in libplasma5support6. Fix: set `QT_FFMPEG_DEBUG=1`; check which package provides the engine before calling a missing engine a product defect; D-Bus tests in containers need a passwd entry for the uid. (lane video-port-278)

## Perks of the part

- Stereo KWin ScreenShot2 version 6 reports "stereo"; a 3D side by side output captures at the full 2560x800 with stereo=1, so a KCM preview can show both eyes; today it shows the left eye (next item: a declared full side by side surface in the KCM) (lane kscreen-wdisplays-parity)
- A Qt that cannot place the window below says nothing and the greeter keeps the wallpaper in its own window, as before, with one warning; control: new lock-screen packages on the old Qt are pixel-identical outside the clock (lane wallpaper-depth-fix-291)

## Measured facts

- The old restricted-interfaces check was bypassable: a user program writes ~/.local/share/applications/x.desktop with Exec=<its executable> and the key, and KWin grants the whole executable (every Python program) live or at next start; System Settings (Exec=systemsettings, no path) could never pass. This is why upstream dropped it (commit text: user can modify or override the desktop files) (lane kwin-screenshot2-0ea31ae7-330)
- Shift-drag frees both alignment and edge contact like wdisplays; a gap makes Apply show KScreen's "Gaps between displays" message. Upstream c7b9b8b5 carried as s11-0001 with author kept, its number-badge hunk left out because the badge (1993fe12) is master only (lane kscreen-wdisplays-parity)
- sparky-stereo-look sets cursorTheme=Oxygen_Black (KDE 4 name) while Debian's oxygencursors names its themes oxy-black, oxy-white; nothing provides the old name, so KWin falls to the x-cursor-theme alternative (oxy-steel) (lane displayxr-audit)
- Measured contrast failures that hit everyone: Oxygen Dark's negative, positive and link text at 2.4 to 2.6:1 on the view background; Konsole Breeze intense red (192,57,43) at 2.8:1, which is the red root prompt. Recommendation: colour-safe schemes as a switch for hue changes, the two contrast fixes as defaults. Keyboard: plasma-keyboard with the Fcitx 5 bridge because Debian's Qt Virtual Keyboard has no Japanese or Chinese conversion (lane accessibility-study)
- Plasma's launcher cannot route browsers and other menu programs by kind without one hook in KIO's ApplicationLauncherJob; saved choices tests: write, read from a fresh object, Defaults removes keys, invalid values refused, unknown GPU kept, hand edits show (lane graphics-page-227)

