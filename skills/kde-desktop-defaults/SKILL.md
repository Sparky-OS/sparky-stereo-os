---
metadata:
  requires-packages: plasma-desktop
name: kde-desktop-defaults
description: >-
  Plasma defaults and small KDE patches: KRunner search and currency rates, task management, Ctrl+Alt+Del,
  Ctrl+Alt+Esc, Leave's one-time UEFI restart, System Monitor's Overview, frozen-window recovery, Dolphin
  drive formatting and scripts, cursor themes, wallpapers, lock and splash screens, Discover's AppStream cache,
  /etc/xdg, first scale on built-in panels, tablet mode, Fcitx 5, KDE Welcome and account defaults. Load it
  when a default needs a decision, a shortcut clashes, a firmware restart action is absent or refused, System
  Monitor shows every GPU as one pie, a lock screen shows only its wallpaper, a video wallpaper keeps the old
  clip, an applet reports zero without an error, a notebook starts at the wrong scale, two Welcome windows
  open, a webcam needs a page, colour vision or contrast needs checking, or a KDE patch needs CI.
---

# KDE desktop defaults

## Working recipe

1. Find what ships the behaviour: a system default in `/etc/xdg` or KDE's global-shortcut folder from the look package, or a patch in the KDE program's own recipe.
2. Test a default with an empty user configuration and with an explicit user override: the person's choice must win.
3. Prove a patch with a test that fails on the unpatched release, then repeat the native checks on the installed packages.

**Check freshness first.**
Written on 2026-10-10 from the accepted Plasma 6.7.4 work; published on 2026-10-23; the principle behind the defaults added on 2026-11-02.
Check the edition's current package versions and KDE release before carrying these changes.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; packages follow [`edition-packaging`](../edition-packaging/SKILL.md), and build storage [`system-housekeeping`](../system-housekeeping/SKILL.md).

## Restart to UEFI setup from Leave

On a UEFI machine, read login1's capability for the active desktop user.
The Leave screen offers the firmware action when that reply is `yes` and the session can restart.
Kickoff and KRunner open the same explicit confirmation.
[The package paths, virtual firmware reboot, authorization denial, and hardware proof with the current boot preserved](references/firmware-restart.md).
Restart Options' second entry, Restart for anti-cheat games, starts sparky-stereo-boot's anti-cheat start once, after a confirmation that lists what Easy Anti-Cheat would not accept on this computer ([the same reference](references/firmware-restart.md#the-second-choice-restart-for-anti-cheat-games-row-190)).

## A program sent to a GPU that dies at start

A browser or player routed to another GPU can die in its first seconds with nothing on screen.
systemd already knows how every program KIO started ended; the Graphics page keeps a death in the problems engine through a drop-in on the `app-` units, with "Use NAME" for the GPU the program's desktop entry can name, and never starts the program again.
[The recipe, why this place and not the launcher or a wrapper, the window and the traps](references/program-died-at-start.md).

## The Game Mode applet takes plasmashell down

plasmashell dies with SIGSEGV at login in `libplasma-gamemode.so` (Debian's `plasma-gamemode`, the Game Mode applet on the panel): `GamesModel::reload()` ran twice before the first answer and the answers' handlers deleted each other's watchers.
The edition carries a patch on Debian's source (each answer owns its watcher).
[The cause, the search, the test that crashes 29 runs in 30 on Debian's source and passes 200 in 200 on the patched one, the real plasmashell session and the traps](references/gamemode-applet-crash.md).

## Convertibles and small dense panels

A notebook's built-in panel gets its first scale from its real size (125 % at least for a full HD panel of about 13 to 14 inches), a computer with a touch screen of its own gets Plasma Keyboard as its virtual keyboard in the session's language, shown only in tablet mode, and in tablet mode every panel hides by itself and goes back to its own setting afterwards.
[Where KWin chooses the first scale and from which EDID field, why a default that only some computers get is a folder in front of `XDG_CONFIG_DIRS`, the shell's two visibility modes, tablet mode in the rig, and the traps](references/convertibles-and-dense-panels.md).

## The on-screen keyboard with Fcitx 5 (Japanese, Korean, Chinese)

KWin runs one input method: Plasma Keyboard in other sessions, Fcitx 5 in the edition's Japanese, Korean and Chinese sessions, where until row 71 no on-screen keyboard showed.
Plasma Keyboard 6.7.4-2+stereo3d1 runs a second time as Fcitx 5's own keyboard (`plasma-keyboard --fcitx`, through Fcitx 5's `org.fcitx.Fcitx5.VirtualKeyboardBackend1`): it shows when KWin would show a keyboard, Fcitx 5's engines convert its keys, and a bar above them holds the preedit, the candidates chosen by a touch and the input method switch; when Fcitx 5 does not answer it says so and types plain text.
[How the pieces fit, the bridge part by part, how to see it working, the defaults, each language typed in the session rig, the keyboard on a 3D output, and the traps](references/on-screen-keyboard.md).

## The first run: KDE's Welcome Center

A new account's first login opens KDE's Welcome Center (Plasma Welcome) with the edition's pages first; its kded module opens it once, when `plasma-welcomerc` has no `LastSeenVersion`, and a value in `/etc/xdg/plasma-welcomerc` keeps it closed for everyone.
Sparky Welcome's own first run is skipped by a unit condition there, and every one of its elements is on the Welcome Center's SparkyLinux page.
[Where Plasma Welcome 6.7.4 takes a distribution's pages, the edition's `first-pages/` patch and `Distro.flag()`, a page with depth on a 3D screen (a `StereoPicture` in a Kirigami page needs stereo-layer 1.23.4), one window at the first login with the upgrade cases measured, the live session, what a tap does where the mouse keeps its click setting, the session proofs and the traps](references/first-run-welcome.md).

## Account defaults and displayed release name

- [Spell checking](references/spellchecking.md): native QSettings fallback, the two recorded nondefault keys, seven dictionaries and the three entries without word-list data.
- [Desktop shortcuts](references/desktop-shortcuts.md): KDE's Trash and the classic Microsoft My Documents label for the home folder, account state, existing accounts and preserved removals.
- [Copy notifications](references/copy-notifications.md): the owning package, running-job popup timing, tray retention and personal overrides.
- [Online Accounts and secrets](references/online-accounts-and-secrets.md): provider and consumer inventory, wallet ownership, local account fixtures and PIM credential paths.
- [Displayed release name](references/display-release-name.md): display-only os-release reading and the pinned SparkyLinux tools.

## The Camera page

System Settings has a Camera page (`sparky-stereo-camera`, under Multimedia beside Sound): the default camera is WirePlumber's `default.configured.video.source`, so every program that asks PipeWire for a camera follows it; the format, size, frame rate and the camera's own controls are set on the V4L2 device and applied again when the camera is plugged in; a preview comes from PipeWire, and a two-lens camera's pair is drawn as a declared full side by side picture.
Kamoso (our build) and Qt Multimedia's camera (our build, ORDER 582) follow the default; FFmpeg's `-f v4l2` does not (measured).
The Qt side: [the default camera in Qt programs](../contrib-qt/references/default-camera-in-qt-programs.md).
[Where each setting lives, which programs follow, a virtual camera in the rig, and the traps with their symptoms](references/camera-page.md).
Only settings are saved, a governing control is applied before the value it governs, and a camera nobody set starts at its best mode (0.1.3): [which V4L2 controls are settings, flag by flag with the clause, the apply order, the best mode and where each program takes its mode from](references/camera-controls.md).
A device's command-line tool (a headset's HeadsetControl) joined to System Settings, the system tray and a user service, with its proof in a Plasma login: [the recipe and the traps](references/device-tool-in-kde.md).

## The Screensavers page

System Settings has a Screensavers page (`sparky-stereo-screensavers`, in Appearance beside Wallpaper): the list of every screensaver the edition ships, the stereo catalogue's and XScreenSaver's 2D ones, a small live preview of the selected one, a full-screen preview, which savers the show rotates through and its times; Display & Monitor, Power Management, Screen Locking and Wallpaper each have a button to it, and the "Stereo Screensavers" launcher opens it.
The layout is the one of KDE's retired Screen Saver module (kde-workspace 4.11).
Every text the page colours itself stands at 4.5:1 or more in any colour scheme: a dim text keeps the scheme's colour where that can be read and is moved towards the normal text by the smallest step where it cannot.
[Where each value lives, how a saver is hosted as a preview in a settings page (a helper on a private display, the pair as a declared surface above the System Settings window, the person's depth limits at the size shown), how a page links to another, how to add a saver to the list, how every text of a page is measured on a capture (the page's text report, the control, the looks, the states, the red side), and the traps (a dim text on a new page, a preview the scroll bar cuts in a real KDE session, a click before the window is there, a row that depends on the frame caught, fixed sleeps, a meta apt cannot plan)](references/screensaver-settings-page.md).

## System Monitor's Overview fits the computer

At a person's first login `sparky-stereo-systemmonitor` reads the computer's graphics cards (in ksystemstats' order, with what each driver reports of usage, video memory, temperature and power) and its processor threads, writes Overview presets into the person's System Monitor folder (one GPU, or every GPU with two or more; the processor's threads in one chart or a chart each, each thread labelled `Thread N` by its own sensor label, never KDE's facegrid, whose cells share one configuration group), titled short enough for the sidebar at 11 pt (`2 GPUs, threads`), and makes the computer's own the start page, KDE's Overview one tick away in Edit Pages; the person's later choice is never written again, and a sensor a driver does not report is named, never shown as zero.
[Where pages and choices live, the sensor names per driver, the probe, the rig with a real System Monitor read through AT-SPI and umockdev, the bench, and the traps](references/system-monitor-overview-presets.md).

## Colour vision: the one switch, and contrast fixed for everyone

System Settings' Colour Vision page (`sparky-stereo-colour-vision`, beside Accessibility) sets, for one choice of none, protan, deutan, tritan or monochromacy, KWin's correction through the keys KDE's Accessibility page uses, the colour-vision variant of the person's colour scheme, and on request Konsole, nano and the text console; the person's files are kept and their colours come back exactly at none.
The look fixes two contrast failures for everyone (Oxygen Dark's negative, positive and link texts; Konsole's intense red, the root prompt).
[Where each colour comes from, the measuring method and its control, the maps per kind, how each surface is set and kept, and the traps (KWin's tritanopia correction, gamma 2.2, nano's include, a Lean Code digest, a same-name scheme shadowing the built-in one, a hint that ranks an output, a text fix that pushes pairs together, texts in unfocused windows and a Plasma style's own colours)](references/colour-vision.md).

## A program that needs hardware: offered, not installed

DisplayCAL needs a colorimeter, so it stays off the image; the Info Centre's Stereo 3D and Deep Colour page says what it requires, shows apt's sizes and offers "Install DisplayCAL" through Stereo APTus' own entry action, and the roles only Suggest it.
[The recipe, why a role must Suggest and not Recommend, the translation-domain trap and the rig traps](references/hardware-program-offered.md).

## The KDE splash

KSplash takes `Breeze` when no `ksplashrc` names a theme (plasma-workspace `startkde/startplasma.cpp`, `readEntry("Theme", "Breeze")`), and a global theme's `defaults` file is only applied when the person applies that theme, so a fresh user of the edition saw KDE's splash although `org.sparkystereo.desktop` has its own.
`sparky-stereo-look` ships `/etc/xdg/ksplashrc` with `[KSplash] Engine=KSplashQML` and `Theme=org.sparkystereo.desktop`; KConfig reads it below the person's `~/.config/ksplashrc`, key by key, so a new user, an empty file and a file with no `Theme` key get ours and a `Theme` the person chose (another global theme, `None`) stays.
Proof, in a container with `libkf6config-bin`: `tests/ksplashrc.sh` in the look package runs `kreadconfig6 --file ksplashrc --group KSplash --key Theme --default Breeze` for six states of the person's file (4 failing without the file, 0 with it).

What the theme draws is ours too: the loading screen is the boot splash's picture, with depth on a screen in a 3D mode inside the person's limits (ORDER 571).
Until then the theme's `contents/splash` was a copy of Oxygen's, KDE's 2014 splash with the KDE gear, so the setting was ours and the picture was not.
[The loading screen](references/loading-screen.md) has how KSplash picks and draws a theme, the quiet fallback to the theme's `X-KDE-fallbackPackage`, the route for depth in a layer-shell QML window (`StereoDepth` of `org.sparky.stereo`, Stereo KWin `+stereo3d58`), how to capture it in a real login, and the traps.

## Decided defaults, out of the box

The edition sets good defaults itself instead of leaving each choice to the person, as stock Debian and KDE do (Daniel, 2026-10-08: "Having the freedom is perfect, but, for a newcommer ... is a pain, not a feature").
Newcomers in Linus Tech Tips' Linux challenge and in Diolinux's videos struggled with choices a distribution could have made for them.

- Decide each default, with its reason and its source, rather than leave it to a first-run question or to the stock value.
  Where a recorded decision sets it, cite that decision beside the file that ships it.
- Personalisation stays: every default remains a setting the person can change in the ordinary settings, and nothing is removed to make a default work.
- KConfig reads the system's files before the person's own, so a value in the person's configuration wins over one under `/etc/xdg` ([KConfig's entry options](https://invent.kde.org/frameworks/kconfig/-/blob/master/docs/options.md): "Typically, the system administrator might set global defaults, and a user might override them in their local configuration files").
  The tests below check both cases.

## Weather Icons

Appearance & Style → Themes → Weather Icons lets the person choose the look, panel colour, shade and hover animation. The hardware package sets the choice shown by Automatic.
[The default writer, protected files, machine fixtures and live Apply proof](references/weather-icon-defaults.md).

## Session, menu, sound and battery defaults

[ORDER 668](references/session-menu-battery-defaults.md) records each reader, first-account delivery, saved-choice preservation, installed fresh-login recipe and traps.
Use its predecessor red, successor green and saved-panel upgrade cases when extending these defaults.

## Spell checking

[Inspect the native page and dictionary inventory](references/spellchecking.md) before changing spelling defaults.
The recipe separates a configured locale, a selected dictionary and a valid checker, and retains the Japanese-to-English fallback that can otherwise mask missing support.

## Defaults before code

- Ship KDE system configuration under `/etc/xdg`. The look package (`sparky-os/packages/sparky-stereo-look` in [the build tree](https://github.com/Sparky-OS/sparky-stereo-os-build)) carries `krunnerrc` there, as a conffile, beside the desktop's other defaults.
- Test it with an empty user configuration and with an explicit user override: a system default must not erase the person's choice.
- Keep existing capabilities available.

### Plasma search (KRunner)

- Favourites put installed applications before settings (`krunner_services`, then `krunner_systemsettings`), and power actions come after them.
- Keep PowerDevil's runner and the unit converter enabled.
- Disable by default only the dictionary and web-shortcut runners, which send queries online.
- Use the plugin identifiers in the installed release's metadata, never display names.

### The unit converter's currency rates (2026-10-08)

- In Plasma 6.7.4 the converter runner synchronised currency rates at initialisation and on a timer, before any currency query.
- The edition's `plasma-runners-addons` recipe carries a patch that defers this until a query names a currency, with no periodic refresh while idle. Local conversions stay offline, and a current query receives its results after the rates arrive.
- Test startup, a non-currency query, the first currency query and the results after the response.
- A disconnected container cannot prove this: use an active non-loopback interface and an intercepted local endpoint.

### Testing search

- Exercise Plasma's actual RunnerManager and Milou model, result order included. A test that sorts its own stand-in results does not check what Enter selects.
- Run the same queries against the unpatched release, and require the old unwanted behaviour to fail the new expectation.

## Task management and frozen windows

- **Ctrl+Shift+Esc opens System Monitor** through a desktop entry in KDE's global-shortcut folder (`/usr/share/kglobalaccel`, from the look package). The upstream shortcut and the person's own override in the shortcut daemon stay; no menu entry is added.
- **The leave screen (Ctrl+Alt+Del) gains Task manager and Close a frozen window**, from the patch in the `plasma-workspace` recipe.
  - Task manager launches System Monitor through KDE's application launcher.
  - Close a frozen window dismisses the greeter and uses KWin's existing interactive window selection.
  - The power and session actions, and Cancel, stay as they were. New text uses KDE's translation mechanism.
- **Proof:** a headless KWin with a client that stops processing events after it goes full screen, on native Wayland and on Xwayland.
  - Check the actual System Monitor process, the selection, and the victim's exit; Cancel must leave the victim running.
  - Drive the registered global shortcuts, not just a direct call to the greeter's methods.
  - Use a separate client as a control, and keep the test independent of a person's running desktop.

## Removable drives and scripts in Dolphin and Partition Manager

- **Format a removable drive from Dolphin.** The Places panel offers Format… for a removable or hot-pluggable drive when Partition Manager is installed; it runs `partitionmanager --device <node> --format` through KIO's command launcher (the `dolphin` recipe's patch).
- **Partition Manager opens one focused Format dialog** for that request (the `partitionmanager` recipe's patch): the device, the file system by its plain name (FAT32, exFAT or NTFS, through KPMcore and the dosfstools, exfatprogs and ntfs-3g tools), and the label, kept from the drive.
  - A label the chosen file system cannot take is refused with a message, before anything happens.
  - Formatting asks for confirmation ("will erase all its files"), unmounts the partition first, and refuses while other changes are pending.
- **Shell scripts in Dolphin:** a local, non-executable shell script offers Run in a terminal…, which shows the script read-only before it runs. Dolphin also shows Reload.
- **Proof:** each patch keeps its tests with the source, with a cancel row and a row per file system; check the result with an independent `blkid` (file system and label), and run KDE's CI and the native comparison against the unpatched release apart from Debian's nocheck package build.

## The joins of the 252 study (ORDER 252c, 2026-11-06)

Programs the edition ships that stand apart, joined so the person reaches them without knowing (study items J8, J16, J19 to J21, J25 to J27).
Each row: what it is, how a person reaches it, how it was tested. The packages are in [the build tree](https://github.com/Sparky-OS/sparky-stereo-os-build) (`sparky-os/packages`).

| Join | How a person reaches it | Test |
|---|---|---|
| `sparky-stereo-clamav` (data pack) | Dolphin right click on one file or folder, "Scan for viruses", opens ClamTk | `tests/run.sh`: the generated entry, the worker against a recording stand-in, the runner with and without `clamtk` |
| `sparky-stereo-wine` (data pack) | Dolphin right click on `.exe` and `.msi`, "Run with Wine"; no default handler | same shape; Wine's own command (`wine start /unix FILE`) from `/usr/share/doc/wine/examples/wine.desktop` |
| `dpkg-stereo --debsums` | terminal; `debsums` alone calls every Lean Code projection changed; debsums is a Depends of dpkg-stereo from 0.1.39 | `test/debsums-front-test.sh`: control, green, four reds |
| `sparky-stereo-firewall-apps` | turn the firewall (ufw) on in System Settings, Firewall: KDE Connect answers the phone from the local network | `tests/run.sh` against a profile that arrives by trigger |
| `sparky-stereo-locales --add` and the Calamares step `languagepacks` | the new system gets the chosen language's packages; nothing is removed | `tests/add.sh` (stand-in packages), `tests/failures.py` (stand-ins for chroot and the engine); the real install waits for the ISO |
| developer task rows | `ripgrep fd-find bat fzf tealdeer ncdu btop tmux debsums` | `lists/tests/joins-252c-test.py` |
| Stereo APTus sections VPN and Tools | the plain NetworkManager plugins; Syncthing with its Plasma widget, Vorta with Borg, KeePassXC, Solaar, Piper, Yakuake, the rescue set GPart, Partclone, FSArchiver, nwipe and Chrooter (TestDisk and ddrescue are on the image), HPLIP when Debian has a candidate; no Cisco VPNC row, the package has left forky | the fork's `stereo/tests/entries.py` |

Recipe for a new Dolphin pack: copy the nearest pack, write `gen.py` (ten languages), add the row to `lists/integrations.tsv`, run the pack's `tests/run.sh` in a container, run `lists/tests/integrations-test.py`.
Details and traps: [lessons from the lanes](references/lessons-2026-11.md) (the 252c entries).

## The CI and package gates

- Run the owning project's KDE CI jobs locally, the clang FreeBSD proxy included, as [rebuilt packages](../edition-packaging/references/rebuilt-packages.md#before-any-push-to-an-inventkdeorg-fork) says.
- Compare a failure with the same unpatched release, wrapper, image and dependencies.
  A matching test name is not enough: read the assertion or exception and the diagnostic artifacts.
  Count repeated environment failures separately from new ones.
  Keep the assertions and the coverage intact; the comparison must reject an injected extra failure.
- A release tag can need a later upstream build fix to compile against current CI dependencies.
  Carry such fixes as separate commits, identified by their upstream revision, and apply them equally to the control and to the changed build.
  The Plasma 6.7.4 workspace recipe carries two: Nicolas Fella's Qt QML linkage fix from Plasma/6.7 (aa326ad917) and Tobias Fella's QFileInfo include (08383f4b1d, bug 526210).
- Package from the distribution's source package with the edition's patch series. Check that dependencies resolve with nothing removed, compare the installed payloads with the built archives, and repeat the native behaviour checks on the installed packages.
- Report the tested revisions, the results, the control failures, the hardware gaps and the commits a later release must carry. Public credit comes from each project's own author records.

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (33 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
