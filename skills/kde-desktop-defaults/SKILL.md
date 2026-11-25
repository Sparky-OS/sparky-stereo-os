---
metadata:
  requires-packages: plasma-desktop
name: kde-desktop-defaults
description: >-
  The edition's Plasma defaults and small KDE patches: KRunner search order, currency rates, tasks, Ctrl+Alt+Del to
  System Monitor and Ctrl+Alt+Esc to log out, frozen-window recovery, formatting a removable drive and scripts in
  Dolphin, the look package (cursor names, wallpaper, lock screen, splash, video wallpaper), Discover's AppStream
  cache, /etc/xdg files, the KScreen KCM, a built-in panel's first scale, tablet mode, the first run in KDE's Welcome
  Center (Plasma Welcome pages). Load it when a default should be decided instead of left to the person, a shortcut
  clashes, a lock screen shows only its wallpaper, a cursor theme name does not exist, a widget shows zero not an
  error, a video wallpaper keeps the old clip, a notebook starts at 100 %, a convertible shows no on-screen keyboard,
  two first-run windows open at login, a webcam has no page, or a KDE patch needs its CI.
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

## The first run: KDE's Welcome Center

A new account's first login opens KDE's Welcome Center (Plasma Welcome) with the edition's pages first; its kded module opens it once, when `plasma-welcomerc` has no `LastSeenVersion`, and a value in `/etc/xdg/plasma-welcomerc` keeps it closed for everyone.
[Where Plasma Welcome 6.7.4 takes a distribution's pages, the edition's `first-pages/` patch, a page with depth on a 3D screen, the two-login session proof and the traps](references/first-run-welcome.md).

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
A device's command-line tool (a headset's HeadsetControl) joined to System Settings, the system tray and a user service, with its proof in a Plasma login: [the recipe and the traps](references/device-tool-in-kde.md).

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
