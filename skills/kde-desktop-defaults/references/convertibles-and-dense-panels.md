# Convertibles and small dense panels

Symptoms first.
A notebook with a 13 or 14 inch full HD panel comes up at 100 % and its text is too small to read.
A convertible notebook in tablet mode shows no on-screen keyboard when a text field is touched, until "Plasma Keyboard" is chosen in System Settings, Virtual Keyboard.
The panel stays on screen in tablet mode and takes room a tablet does not have.

The edition sets three defaults for these machines, each with the person's own choice kept (ORDER 567, November 2026; Daniel, 2026-10-08: "the default being set not waiting for the user like stock debian/kde").

| Default | Where it is built | The person's choice |
|---|---|---|
| The first scale of a built-in panel comes from its real size, 125 % at least for a full HD panel of about 13 to 14 inches | KWin (`kwin` +stereo3d55 and later, patches `s55-*`) | a saved scale is kept; Display Settings changes it |
| A computer with a touch screen of its own gets Plasma Keyboard as its virtual keyboard, in the session's language | `sparky-stereo-hardware` 0.1.27 | System Settings, Virtual Keyboard: another keyboard or None, written to the person's own `kwinrc` |
| The keyboard shows only in tablet mode | KWin (`kwin` +stereo3d57, upstream's open merge request 8592) | the same page, "Show automatically: Only when in Tablet Mode"; switched off, any touch shows it |
| While in tablet mode every panel is on automatic hide, and goes back to its own setting afterwards | the shell (`plasma-workspace` +stereo3d8) and the switch in General Behavior (`plasma-desktop` +stereo3d4) | General Behavior, Touch, "In Tablet Mode: Hide panels automatically"; each panel's own visibility setting is never written |

The recipes are in [the build tree](https://github.com/Sparky-OS/sparky-stereo-os-build): `sparky-os/packages/kwin/build-55.sh`, `sparky-os/packages/convertible-defaults-567` and `sparky-os/packages/sparky-stereo-hardware`.

## Where the first scale is chosen, and why it was 100 %

KWin chooses it, once, when it meets an output it has no saved configuration for: `OutputConfigurationStore::chooseScale()` in `src/outputconfigurationstore.cpp`.
The formula divides the panel's pixel density by a target that depends on the kind of device, rounds to 5 %, and turns anything under 120 % into 100 %.

| Kind, as KWin tells it | Target | Smallest logical side |
|---|---|---|
| built-in panel and a lid switch among the input devices (a notebook) | 125 dpi | 800 |
| built-in, no lid switch, short side over 90 mm (a tablet or handheld; from upstream c8a2cb46) | 130 dpi | 720 |
| built-in, no lid switch, smaller (a phone) | 150 dpi in 6.7.4 | 360 |
| external, taller than 500 mm (a television) | 30.5 dpi | 800 |
| external, any other | 96 dpi | 800 |

Three causes, found in this order, each of which alone gave 100 %:

1. **No lid at the first configuration.** In 6.7.4 `LibInput::Connection::setup()` queued its work, so the first output configuration was made before any input device was listed, `hasLaptopLid` was false and every notebook was sized as a phone: a 14 inch full HD panel has 157 dpi, 157 / 150 is 1.05, which is 100 %. Upstream found and fixed it: KWin merge request 10327 by Xaver Hugl, merged on 2026-11-09 (commit 4e6a1ea8, "backends/libinput: list devices during setup", and c8a2cb46 for tablets and handhelds). Carried as `s55-0001` and `s55-0002` with his name.
2. **The wrong field of the EDID.** `determineScreenPhysicalSizeMm()` in `src/utils/edid.cpp` took the first detailed timing's millimetres whenever their aspect matched the mode's. One 13.3 inch notebook panel declares 29 x 17 cm in the screen size field (right) and 344 x 193 mm in its timing (a 15.5 inch panel): 142 dpi, 142 / 125 is 1.13, rounded to 1.15, which is 100 %. The rule is now the boot menu's ([the boot menu](../../system-housekeeping/references/boot-menu.md)): the screen size field decides when it can be a screen (VESA E-EDID Release A2, 3.6.2: "The host (source) is expected to use this data to get a rough idea of the image size to generate properly scaled text and icons"), and the timing's millimetres (3.10.2) are used when they agree with it within a centimetre. A field that cannot be a screen (under 10 cm by 6 cm, an aspect outside 1.2 to 2.6, the 160 x 90 mm placeholder) leaves KWin's choice as it was, so a 32:9 monitor keeps its timing's size. KWin says both sizes in its log when they differ. `s55-0003`.
3. **The rounding.** 120 % for a 14.6 inch full HD notebook, 100 % for a 14.5 inch tablet. A built-in panel of full HD or more with at least 150 dpi (full HD at 14.7 inches) never starts below 125 %. `s55-0004`. The floor is only that: any larger scale is the formula's.

With the three, the 13.3 inch panel starts at 130 % on a notebook with a lid switch and 125 % on one without.
Measured in the rig with that panel's EDID on a virtual built-in output: physical size 290 x 170 mm, first scale 1.25, and KWin's log names both sizes.
The same EDID on an external output gives 135 %, a 24 inch full HD monitor 100 % and a 46 inch full HD television 135 % (the television target, held by the 800 logical pixels): none of the three is touched by the floor, and the television's 135 % is KWin's own formula, there before this work.
A scale the person saved is never touched: `chooseScale()` runs only for an output with no saved state.

### The test

KWin's own `testOutputChanges`, `testGenerateConfigs`, has a row per machine: the device kind, the output and the expected first scale.
The rows of ORDER 567 give the panel as its EDID bytes (`.edid`, no `physicalSizeInMM`), so the whole chain is read: EDID, size rule, scale.
A virtual output that is given an EDID and no size takes the EDID's size, as a DRM connector does.
Run it red by switching one rule off at a time and rebuilding only what changed: a test that passes with every rule off proves nothing.

## The on-screen keyboard: a default only some computers get

KWin starts the program its `kwinrc` names in `[Wayland] InputMethod` and shows it on a text field when the last input came from a touch screen or a pen (`InputMethod::shouldShowOnActive()`).
Plasma Keyboard (`plasma-keyboard`, `/usr/share/applications/org.kde.plasma.keyboard.desktop`) takes the session's locale as its layout when no language is ticked in its own page (`src/qml/main.qml`, `updateLocales()`), so a Portuguese session gets the Portuguese layout with nothing chosen.

The default cannot be a file in `/etc/xdg` (every computer would get it) and it must not be a line written into the person's own `kwinrc` at the first login.
KConfig writes a person's choice explicitly only when a system default exists; with none, a value set back to "nothing" is removed from the file (`KCoreConfigSkeleton::ItemString::writeConfig()`: `if ((mDefault == mReference) && !cg.hasDefault(mKey)) cg.revertToDefault(...)`), so a person who chose None would get the keyboard back at the next login.

So it is a system default in a folder of its own, put in front of `XDG_CONFIG_DIRS` only on a computer with a touch screen of its own:

1. `/usr/lib/sparky-stereo-hardware/has-tablet-mode` reads sysfs: a touch screen (an input device with `INPUT_PROP_DIRECT`, absolute positions and no pen tool) and a built-in panel (an eDP, LVDS or DSI connector of `/sys/class/drm` that is not disconnected). `--why` prints what it found, with the tablet-mode switch and the chassis type for the record only.
2. `/etc/xdg/plasma-workspace/env/sparky-stereo-tablet-mode.sh`, which `startplasma` sources before it starts KWin, puts `/usr/share/sparky-stereo-hardware/tablet-mode/xdg` first in `XDG_CONFIG_DIRS` (XDG Base Directory Specification: the directories are in order of preference).
3. That folder's `kwinrc` holds `[Wayland] InputMethod=/usr/share/applications/org.kde.plasma.keyboard.desktop`.
4. The package depends on `plasma-keyboard`.

The rule follows what KWin can do, not what the firmware says.
KWin puts a computer in tablet mode by a tablet-mode switch, by itself when its touch screen is left without a mouse or touchpad (`TabletModeTouchpadRemovedSpy` in `src/tabletmodemanager.cpp`), or by the Touch Mode setting.
A first rule asked for a switch or a tablet, convertible or detachable chassis, and failed on the machine the work was for: a slider convertible whose chassis type is 10 (notebook), with no tablet-mode switch and no lid switch, its only switches the sound card's jacks.

### Only in tablet mode

KWin 6.7.4 shows the keyboard for any touch on a text field, at the desk too.
Upstream's open merge request 8592 (Luca Tramonti, "Option to limit Virtual Keyboard to Tablet Mode") adds `kwinrc`, `[Wayland] InputMethodTabletOnly`, true by default and honored only while tablet mode is available; the edition carries it adapted to 6.7.4 (`s57-0001`, a DEP-3 header that names it as an open merge request).
On 6.7.4 the condition goes in front of the visibility modes of `InputMethod::shouldShowOnActive()`, and the check box goes in the page's footer.

The test: `tests/tablet-mode.sh` in the package builds fourteen machines as small sysfs trees, the slider among them, and reads the result through `kreadconfig6` for a new person, for one who chose another keyboard and for one who chose None.

## Panels in tablet mode: nothing is written, so nothing is restored

The shell follows KWin's `org.kde.KWin.TabletModeManager` (property `tabletMode`, signal `tabletModeChanged`) on the session bus.
`PanelView` keeps two things apart: the visibility mode in force, which the views, the struts and the screen edge use, and the person's own choice, which is the one saved, the one scripting's `hiding` reads and the one a change made while in tablet mode goes to.
`setHiddenForTabletMode(true)` puts the mode in force on automatic hide and touches nothing else.

A session service that rewrites each panel's saved `hiding` (the first, hand-made form) works, but it has to remember what it changed, and a session that ends in tablet mode leaves every panel on automatic hide with only a state file to say otherwise.

The switch is `plasmarc`, `[TabletMode] HidePanels`, on by default; the General Behavior page (`kcms/workspaceoptions` in plasma-desktop) writes it and the shell reads it again when the file changes.

## Tablet mode in the rig

KWin's tablet mode comes from a libinput switch, which a container has not.
The supported way to drive it is the setting the General Behavior page writes, which KWin watches:

```
kwriteconfig6 --file kwinrc --group Input --key TabletMode --notify on     # "Always enabled"
kwriteconfig6 --file kwinrc --group Input --key TabletMode --notify auto   # back to the hardware's own state
busctl --user get-property org.kde.KWin /org/kde/KWin org.kde.KWin.TabletModeManager tabletMode
```

`auto` in a container is "not in tablet mode", which is also the control for a computer without one.
A container has no touch screen either, so KWin says tablet mode is not available and "Only when in Tablet Mode" is not honored: `KWIN_VIRTUAL_TOUCH_SCREEN=1` in KWin's environment (kwin +stereo3d57) stands for a notebook with a built-in touch screen and a touchpad, tablet mode available and off.

For a first-scale case, `kwin_wayland --virtual` takes an EDID and the built-in flag from the environment (kwin +stereo3d55):

```
KWIN_VIRTUAL_OUTPUT_EDIDS=/path/panel.edid.bin KWIN_VIRTUAL_OUTPUT_INTERNAL=1 kwin_wayland --virtual --width 1920 --height 1080 ...
kscreen-doctor -o        # Scale: 1.25
```

A person's saved scale: set it with `kscreen-doctor output.Virtual-0.scale.1`, stop KWin with SIGTERM (it saves), start it again on the same configuration folder.

For the keyboard, the machine is a sysfs tree: export `SPARKY_STEREO_SYSFS=/path/fixture` and source `/etc/xdg/plasma-workspace/env/*.sh` in the session's shell before KWin starts, as `startplasma` does.
A touch is one step of the rig's fake input client, `t:X,Y` ([sending keys and clicks](../../stereo-proof-rig/references/input-delivery.md)).
The keyboard is a window of its own in KWin's list (`inputMethod` true), so the proof reads it from a KWin script and never from the picture.

For the panels, a real `plasmashell` ([Plasma in the rig](../../stereo-proof-rig/SKILL.md#plasma-in-the-rig-notifications-on-screen-displays-panels-popups)); what is read in each state: KWin's `workspace.clientArea(KWin.MaximizeArea, ...)` (the room a maximized window gets), each dock window's `hidden`, scripting's `panels()[i].hiding` (the person's own setting) and the `panelVisibility` entries of `plasmashellrc`.

## Traps

- Symptom: the detection says no on the very machine the work was for. Cause: the rule was written from what such machines usually report (a tablet-mode switch, a convertible chassis type), and this one reports neither. Fix: read the real machine's sysfs before writing a hardware rule (`chassis_type`, each input device's `capabilities/sw` and `properties`), and make the rule follow what the compositor can do with the hardware. Found by: the review reading the machine.
- Symptom: a new control of a settings page is not on the page, with no error. Cause one: it was an action of the page's header, and the tool bar drops what does not fit beside the page's own selector. Cause two: its `visible` was `Kirigami.Settings.tabletModeAvailable`, which answered false in `kcmshell6` while KWin's `tabletModeAvailable` property answered true. Fix: the page's `footer`, and the page's own class asking KWin over D-Bus. Found by: a capture of the page, then a three-line QML probe printing Kirigami's value beside `busctl get-property`. Check a page change by building only its module in the kept build tree (`make kcm_NAME`) and mounting the `.so` over the installed one in the rig, before a package build.
- Symptom: the link gate says `conflicting supplied package: kwin-common; provide one authoritative edition snapshot` for a build on top of another lane's staged build. Cause: one side of the gate is given two versions, here the previous side (the published list with +54, and the staged +56 as predecessor). Fix: give each side one snapshot: the published list without the sources the staged round replaced, plus that round's packages. A filter by `/pool/main/?/SOURCE/` misses sources under four-letter folders (`libk/libkscreen`).
- Symptom: after a failed gate, `dpkg-buildpackage -nc` stops with `already marked; use a fresh staging tree, never project MR again`. Cause: the staging trees under `debian/` were projected by the first run. Fix: remove the package staging folders, `debian/.debhelper`, `debian/files` and the substvars, keep the build folder, and run it again; the compile is not repeated.
- Symptom: a shell script fails with "unexpected EOF while looking for matching `'`" at a line that has balanced quotes. Cause: an apostrophe inside the message of `"${VAR:?message}"` some lines above. Fix: no apostrophe in that message; `bash -n` before the first run.

- Symptom: the shell never reacts to tablet mode, and its log says `qt.dbus.integration: Could not connect "org.kde.KWin.TabletModeManager" to setTabletMode(bool)`. Cause: the method was declared in a `private:` section, and a D-Bus signal connected by name needs a slot. Fix: declare it under `private Q_SLOTS:`. Found by: the shell's own log in the rig; the package had built and passed every gate.
- Symptom: two captures of the same keyboard layout differ by a few thousand pixels in one run of ten. Cause: the capture caught the keyboard while a key's highlight was still fading. Fix: capture some seconds after the tap, and rerun a pair that differs before believing it; the pair that matters is "the session's language" against "that language ticked by hand", which must give 0.
- Symptom: a check that reads "is the panel drawn?" from the picture's bottom rows says "panel" with the panel hidden. Cause: the wallpaper is a gradient, so rows 200 pixels apart differ anyway. Fix: read the dock window's `hidden` and the maximize area from KWin, and keep the picture for the eye.
- Symptom: a new test row fails on the first green run (a 14.6 inch external monitor expected at 155 %, measured 135 %). Cause: the expectation forgot the formula's clamp, the 800 logical pixels a monitor keeps (1080 / 800 is 1.35). Fix: work a row's expectation through every step of `chooseScale()`, the clamp included.

- Symptom: the touch on the text field does nothing; the field never has the focus. Cause: the seat gains its touch capability with the fake device's first touch, and a client that binds `wl_touch` at that moment has missed the touch (its log shows `wl_touch.up` with no `down`). Fix: one tap on the empty desktop first, the tap on the field a second later, in the same fake input process. Found by: `WAYLAND_DEBUG=client` on the client, `wl_seat.capabilities(7)` arriving with the touch.
- Symptom: every capture is cancelled (`org.kde.KWin.ScreenShot2.Error.Cancelled`). Cause: no render node in the container. Fix: give it one (`--device /dev/dri/renderD128` and its group). KWin itself, the window list and the tablet mode work without.
- Symptom: `docker run` refuses a mount with `stat ...: permission denied` although the path is readable. Cause: the path is a symbolic link in a sticky folder (`/var/tmp`) owned by another user than the daemon, which the kernel does not let it follow (`fs.protected_symlinks`). Fix: mount the link's target.
- Symptom: a package build stops at `'vicCode' was not declared in this scope` after a patch that only rewrote one function. Cause: the patch was made by replacing the text from the function to the next one of the upstream file, and an earlier patch of the series had placed two helpers between them. Fix: replace a function by its own braces, and read the diff for removed lines before building. Found by: `git show` of the commit, filtered to its removed lines.
- Symptom: `dpkg-source -b` stops with "aborting due to unexpected upstream changes" when a new patch is placed inside a published series (before its translation patch). Cause: the published tree is unpacked with every patch of the old series applied, and a new one is applied on top of them. Fix: append the new patch at the end; a new translation patch after it, last.
- Symptom: a default that should hold only on some hardware is written into the person's file at the first login, and a person who then chooses "nothing" in the settings page gets the default back at the next login. Cause: KConfig removes a key that equals the built-in default when no system default exists. Fix: a system default in a folder that the session's environment script puts in front of `XDG_CONFIG_DIRS` on that hardware only.
