---
metadata:
  requires-packages: plasma-desktop
name: kde-desktop-defaults
description: >-
  The edition's Plasma defaults and small KDE patches, with native and packaged proof: KRunner search order, the unit
  converter's currency rates, task management, Ctrl+Alt+Del to System Monitor and Ctrl+Alt+Esc to log out, frozen-window
  recovery, formatting a removable drive and running scripts from Dolphin, the look package (cursor theme names,
  wallpaper, lock screen, the video wallpaper plugin), Discover and its AppStream cache and memory, sparky-stereo-look
  and /etc/xdg files, the KScreen KCM, widgets that must say when a service is unreachable. Load it when a default
  should be decided instead of left to the person, a shortcut clashes, a lock screen shows only its wallpaper, a cursor
  theme name does not exist, a KCM page is out of order in another language, a widget shows zero instead of an error, a
  video wallpaper keeps the old clip, Discover's memory must be measured fairly, or a KDE patch needs its CI and package
  gate.
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

## Decided defaults, out of the box

The edition sets good defaults itself instead of leaving each choice to the person, as stock Debian and KDE do (Daniel, 2026-10-08: "Having the freedom is perfect, but, for a newcommer ... is a pain, not a feature").
Newcomers in Linus Tech Tips' Linux challenge and in Diolinux's videos struggled with choices a distribution could have made for them.

- Decide each default, with its reason and its source, rather than leave it to a first-run question or to the stock value.
  Where a recorded decision sets it, cite that decision beside the file that ships it.
- Personalisation stays: every default remains a setting the person can change in the ordinary settings, and nothing is removed to make a default work.
- KConfig reads the system's files before the person's own, so a value in the person's configuration wins over one under `/etc/xdg` ([KConfig's entry options](https://invent.kde.org/frameworks/kconfig/-/blob/master/docs/options.md): "Typically, the system administrator might set global defaults, and a user might override them in their local configuration files").
  The tests below check both cases.

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

Recipe for a new Dolphin pack: copy the nearest pack, write `gen.py` (nine languages), add the row to `lists/integrations.tsv`, run the pack's `tests/run.sh` in a container, run `lists/tests/integrations-test.py`.
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

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (32 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
