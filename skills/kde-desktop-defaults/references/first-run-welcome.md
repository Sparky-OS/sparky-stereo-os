# The first run: KDE's Welcome Center with the edition's pages

**For** whoever changes what a new account sees at its first login: where Plasma Welcome takes a distribution's pages in the version the edition ships, what opens it and when, a page of ours with depth on a 3D screen, how to prove a first login in a container, and the traps met (ORDER 63 and 720, November 2026).

Daniel, 2026-11-18: "change sparky first run to our custom kde first run with all the elements sparkylinux one has, since our native DE is kde, I would rather follow this path".
So the first run is KDE's own Welcome Center (Plasma Welcome, `plasma-welcome`), with the edition's pages in it, and SparkyLinux's first-run window (`sparky-welcome`, by Paweł "pavroo" Pijanowski) gives its elements to it.

## What opens at a first login, and why

- **Plasma Welcome's kded module decides** (`src/kded/daemon.cpp`, 6.7.4): at every login it reads `plasma-welcomerc`, `[General] LastSeenVersion`.
  Empty: it starts `plasma-welcome` (the welcome wizard); set and older by a minor version or more: `plasma-welcome --post-update`, unless `ShowUpdatePage=false`; then it writes the running version into the person's own file.
  So the window opens once, at the first login of a new account, and not again: the trigger is KDE's, nothing of ours runs at login.
  `LiveEnvironment=true` starts it in its live mode at every login instead (the installer page first).
- **A `LastSeenVersion` in `/etc/xdg/plasma-welcomerc` keeps it closed for every new account,** because KConfig reads the system file below the person's and the value is no longer empty.
  sparky-stereo-info 20261016.1 to 20261104.1 wrote such a file to make SparkyLinux's window the only first-run window; 20261125 removes it (only a file that carries its `# sparky-stereo-info` mark).
- **SparkyLinux's window** starts from `/etc/xdg/autostart/sparky-welcome-first.desktop` at every login (`sparky-welcome first`): it sleeps 5 seconds, then shows the window only when `~/.config/autostart/sparky-welcome.desktop` is missing, and writes that file (with an empty `Exec=`) as its mark; later logins end with status 1, which sparky-stereo-service-defaults' drop-in counts as success.

## Where a distribution's pages go (Plasma Welcome 6.7.4, Debian forky)

| Extension point | What it does | Limits |
| --- | --- | --- |
| `/usr/share/plasma/plasma-welcome/extra-pages/NN-Name.qml` | QML pages whose root inherits `Kirigami.Page` (`Welcome.Page` of `org.kde.plasma.welcome`), sorted by name | appended after KDE's Welcome, Network, Simple by Default, Powerful When Needed, Discover and Feedback pages, right before the last page (`src/qml/Main.qml`) |
| `/usr/share/plasma/plasma-welcome/intro-customization.desktop` | `Name` adds a paragraph before KDE's own text on its first page; `Icon` replaces Konqi's picture; `Comment` its caption | the page stays KDE's; the picture is a plain `Image`, so a stereo pair cannot be shown there; `URL` does nothing in 6.7.4 (KDE bug 523776, merge request 291 open) |
| `plasma-welcomerc` `LiveEnvironment`, `LiveInstaller` | the live mode, with a button for the installer's desktop entry | |
| `--pages A,B` | shows only the named pages (KDE's or a distribution's) | the kded module never passes it |
| `--post-update` | KDE's release notes page | |

A page of the distribution cannot come first with these: KDE's bug 499555 asks for more control, and its developers plan it (Oliver Beard, 2025-02-05), with no code yet.
The edition's plasma-welcome (6.7.4-1+stereo3d1) carries one patch for that: pages in `/usr/share/plasma/plasma-welcome/first-pages/` come before KDE's first page (after the live installer page in the live mode), sorted by name, and `--pages` finds them too; nothing changes when the folder is empty.

A page runs no C++ of its own. What it may do (`Welcome.Utils` in 6.7.4; `Controller` is deprecated): `launchApp("desktop-entry-name")` (KIO's application launcher, a failure is notified), `runCommand("program args", callback)` (split on spaces, no shell; the callback gets the exit status, -1 when the program is missing, and the output), `copyToClipboard()`; `Qt.openUrlExternally()` for an address; `KCMPage { path: "kcm_name" }` embeds a QML settings module only (Window Behavior, `kcm_kwinoptions`, is a QWidget module: open it with `launchApp("kcm_kwinoptions")`, which runs `systemsettings kcm_kwinoptions`).
A page's words use its own translation domain, `i18ndc("domain", "context", "text")`, with the catalogue in `/usr/share/locale/LANG/LC_MESSAGES/domain.mo` (Fedora's `plasma-welcome-fedora` does the same: read, not copied).
A page sets `show: false` to stay out; it is read when the page is made, so a command's answer comes too late for it.

## A page of ours with depth on a 3D screen

The pages use stereo-layer's own element depth (`org.sparky.stereo`, 1.22.0) inside the person's limits and set no separation of their own:
- a stereo picture is a `StereoPicture` (a surface of its own below the window, declared full side by side; its left view on a 2D screen), its depth the picture's own;
- a drawing that already shows depth by its stacking is drawn once per eye with `StereoDepth.depth`, a fraction of the person's limits (`parallax = round(depth × limit × view width / 1920)`); `StereoDepth` knows only the desktop's sunk and popped limits, not the element limit Stereo Union uses for a window's own controls;
- words and buttons are the window's own, the same in both eyes; the window itself is at the screen while it is the active window, and flat and one layer back when it is not.

**A `StereoPicture` in a Kirigami page is a pair since stereo-layer 1.23.4.**
Up to 1.23.3, `PictureItem::updatePolish()` handed over a pair only when no ancestor clipped, scaled, rotated or faded the item, and both the Welcome page and Kirigami's `ColumnView` set `clip`, so every picture in a Kirigami page was one view in both eyes.
1.23.4 compares each clip with what it holds: the clipping item's `clipRect()` mapped to the scene (what `QQuickWindow` gives its clip node, `qquickwindow.cpp`), against the picture's rectangle, to half a device pixel.
A clip that holds the whole picture takes nothing from it; one that cuts it, a rotation, a scale, an opacity or a window with no alpha channel still draws the left view in the scene graph, and the log (`org.sparky.stereo.layer`) now names the item and the reason once for each, where nothing was said before. `PictureItem::flatReason(item)` gives the reason.
A page slide is such a moment: while Kirigami slides a page in or out, the page fades and its clip cuts the picture, so the picture is flat for that moment and two lines are logged once ("is not opaque", "clips it").
The edition's first page holds its picture as an ordinary item of the page again (milestone 1 put it in the window's content item to get round the refusal).

## One window at the first login, Sparky Welcome kept

- **Sparky Welcome's first run is skipped by a unit condition, owned by sparky-stereo-welcome:** `/usr/lib/systemd/user/app-sparky\x2dwelcome\x2dfirst@autostart.service.d/sparky-stereo-welcome.conf` sets `ConditionPathExists=!/usr/share/plasma/plasma-welcome/first-pages/00-SparkyStereoOS.qml`, next to sparky-stereo-service-defaults' own drop-in (`SuccessExitStatus=1`). systemd's XDG autostart generator makes the unit; the journal says `skipped, unmet condition check`. Removing sparky-stereo-welcome removes the file and Sparky Welcome's first run comes back. Sparky Welcome stays installed and in the menu.
- **Every element moves to the Welcome Center's SparkyLinux page** (`extra-pages/02-SparkyWorld.qml`) with the same address or command as Sparky Welcome's page and handler. Upgrade goes through `sparky-stereo-welcome-upgrade`, which does what the handler does: `remsu /usr/bin/sparky-aptus-upgrade`, at the first use then `spsudo /usr/lib/sparky-aptus-appcenter/bin/sparky-locale`, then the handler's own mark `/home/$USER/.sparky-welcome-first`. `spsudo` is in SparkyLinux's `sparky-su`, which neither sparky-welcome nor the app center depends on: the welcome package does.
- **A program that is missing or fails is said on the page:** `Welcome.Utils.runCommand(cmd, (status, message) => ...)` gives -1 and "The command … could not be found." for a missing program, the exit status and its error text otherwise; the page shows it in a `Kirigami.InlineMessage`. `remsu` itself is `pkexec "$@"; exit 0`, so a refused password never reaches the page.
- **The live session, what it started before:** the image's autostart entries (14 on the published set: Plasma's own, the hardware layer's live GPU check, SparkyLinux's APTus update check and Sparky Welcome's first run), and the packer's live-config hooks (autologin, the installer's desktop icon and guide, the live user's power and lock settings, the Welcome Center's kded module off for root only). In the ISO's state `/etc/xdg/plasma-welcomerc` kept the Welcome Center closed for the live user too, so a live session met Sparky Welcome only.
- **The live session:** a live-config hook of sparky-stereo-welcome, `/usr/lib/live/config/1187-sparky-stereo-welcome`, writes the live user's own `~/.config/plasma-welcomerc` (`LiveEnvironment=true`, `LiveInstaller=calamares`), as the packer's `1186-sparky-stereo-live` writes that user's power and lock settings; the kded module then starts the Welcome Center in its live mode at every login of the live user, KDE's installer page first, then the edition's pages.

**What opens after the upgrade, measured** (ORDER 63 and 720, milestone 2; each account's home kept from a login on the published set to a login after the upgrade):

| Account | Before | After the upgrade |
| --- | --- | --- |
| New, on the successors | | the Welcome Center at the first login, nothing at the second |
| Made on an installed ISO (its first run was Sparky Welcome; `/etc/xdg/plasma-welcomerc` kept the Welcome Center closed) | Sparky Welcome | the Welcome Center, once: the upgrade removes the system file and the account has no `LastSeenVersion` of its own |
| Made after an apt install (both windows opened) | KDE's and Sparky Welcome's | nothing |

Sparky Welcome's marks (`~/.config/autostart/sparky-welcome.desktop`, `~/.sparky-welcome-first`) stay in every case.
KConfig writes no value that equals the system file's, so an account that never saw the Welcome Center while the system file existed has no `LastSeenVersion` of its own: read the person's file, not the cascade, before saying who will see it.

## The touch page and its condition

Measured with a fake touch screen beside the fake pointer (KWin's fake input protocol, `t:X,Y` of the rig's `fakeinput`):

| Where | KDE's default (double click) | Single click |
| --- | --- | --- |
| Desktop icon, mouse click | selects | opens |
| Desktop icon, tap | opens | opens |
| Dolphin item, mouse click | selects | opens |
| Dolphin item, tap | opens | opens |

The sources agree: Dolphin's `KItemListController::onRelease()` activates on a touch release in double-click mode (`emitItemActivated = touch && !m_selectionMode`), and the desktop's `FolderView.qml` activates on a press Qt synthesized from touch (`mouse.source === Qt.MouseEventSynthesizedByQt`). The edition sets no `SingleClick`, so KDE's default (double click) holds.
The task manager's source activates a window on a tap and opens its menu on a long touch (`Task.qml`: a `TapHandler` for the left button, one for touch screens and pens with `onLongPressed`), but in the rig one tap on an inactive window's button did nothing, two taps activated it, and a long touch (1.2 s) opened no menu, while a tap on the panel's launcher opened it. So the page does not name the task bar; a real touch screen settles it.

**A page cannot run a command to decide whether it shows** (Main.qml reads `show` once, when it makes the page). The edition's plasma-welcome +stereo3d2 adds `Welcome.Distro.flag(key)`: the `[Distribution]` group of `plasma-welcomerc`, read as KConfig reads it (the person's file, then each folder of `XDG_CONFIG_DIRS`), false when no file sets it.
`/etc/xdg/plasma-workspace/env/sparky-stereo-welcome-touch.sh` (sourced by startplasma after the hardware layer's `sparky-stereo-tablet-mode.sh`; the names sort so) puts `/usr/share/sparky-stereo-welcome/touch-screen/xdg` (a `plasma-welcomerc` with `TouchScreen=true`) in front of `XDG_CONFIG_DIRS` where the hardware layer's own folder already is, that is where `has-tablet-mode` found a touch screen of the computer's own.
The page ships with `show: Welcome.Distro.flag("TouchScreen")`, shown only where the hardware layer found a touch screen of the computer's own, because Daniel chose it (2026-11-25, asked whether it shows on every computer: "Only with a touch screen"); `show: true` (every computer) is the other way, one line.

## Pages that explain a default: written from the packages, not from the plan

Three pages after KDE's own and before the SparkyLinux page (Daniel, 2026-11-25: "pick the ones you think are valuable enought to be there"), each built like Point, Then Type: a few plain sentences, why it is so, how to change it, a button to its own setting.
Plasma Welcome orders a folder's pages by file name (`QDir::Name` in `App::distroPages()`), so they are `02-Your3DDepth.qml`, `03-ChangingWallpaper.qml` and `04-WindowsKeysAndSessions.qml`, after the touch page's `01` and before `05-SparkyWorld.qml` and `06-HelpTest.qml`.

**Reconcile each sentence against the published package before writing it.** What a default does on the image is what the published (or staged) package does, not what a design says it will do:

| Page | What ships (read in r1123a, 2026-11-25) | The button |
| --- | --- | --- |
| Your 3D Depth, Set Once | one setting, `kwinrc [StereoDepth] SunkLimit, PoppedLimit`, on Stereo KWin's 3D Depth page under Display; the contract's own words ("one separation setting, centralized, tailored to the screen, not to the element size") and nothing more | `kcm_kwinstereodepth` |
| A Wallpaper That Changes by Itself | Variety 0.9.2-1+stereo3d1: every 300 s once it runs; it starts only when opened, then writes its own autostart entry; its sources at first are folders of the computer, every online source unticked (`Options.py` adds unknown sources as `False`); no rule for a metered connection | `variety --preferences` |
| Keys and Sessions You Know from Windows | Ctrl+Alt+Del, Ctrl+Shift+Esc, Ctrl+Esc to System Monitor (sparky-stereo-look's kglobalaccel entry); Ctrl+Alt+Esc to the logout screen (plasma-workspace +stereo3d6 and later); `ksmserverrc loginMode=emptySession`, `confirmLogout=false` | `kcm_keys`, `kcm_smserver` |

The wallpaper page describes Variety as it is published. The edition's own Variety defaults (on at login, every place Debian and KDE put wallpapers, online sources on, nothing downloaded on a metered connection) are not built yet, and the page's sentences change with the package that brings them.

**Names in each language come from where the person sees them:** KDE's page names from their desktop entries on the image (`Name[pt_BR]=` of `kcm_keys.desktop` and the others), a program's own labels from its catalogues (Variety's in Polish and Traditional Chinese are partly English, so the page quotes them in English there), key names from Qt's `qtbase_LANG.qm` (`QShortcut` context: de Strg, Entf, Umschalt; fr Suppr, Échap, Maj; es Control, Suprimir, Escape, Mayúsculas).

**A page about a program that may be missing** gets the same kind of condition as the touch page: `sparky-stereo-welcome-variety.sh` puts `/usr/share/sparky-stereo-welcome/variety/xdg` (a `plasma-welcomerc` with `Variety=true`) in front of `XDG_CONFIG_DIRS` when `${SPARKY_STEREO_VARIETY:-/usr/bin/variety}` is executable; the page has `show: Welcome.Distro.flag("Variety")`. KConfig merges the `[Distribution]` group of every folder, so the touch and Variety marks stand together.

**A drawing about depth needs something inside each part that moves sideways.** A sunk element's edges keep their 2D place and a vertical gradient has nothing to shift, so the depth page's wallpaper has a sun and a row of hills; the rig measures each part's shift between the eyes (`eyes-align.py` on a region): sun 10 (the sunk limit), the window's lines 0, the menu −4 (the popped limit), at KWin's default limits.

## The session proof

The scripts are in [`stereo-proof-rig/scripts/welcome-login`](../../stereo-proof-rig/scripts/welcome-login/) (the loading screen's login rig, [a real login](../../stereo-proof-rig/references/login-splash.md), taken further):

1. `mkrig.sh TAG REPO APTCONF`: the published set on Debian testing pinned by digest, the edition's signed tree, deb-multimedia and SparkyLinux's own repository (Sparky Welcome and the tools it needs). `mkcandidate.sh` puts the packages under test on it as one more layer.
2. `run-case.sh IMAGE OUT VAR=VALUE...`: one fresh container per case, KWin on the NVIDIA card through CDI (`--device nvidia.com/gpu=0`, the render node's group), the session's programs on Mesa's software renderer, the core limit at 1.
3. `welcome-login.sh` (inside): the person's saved 3D screen (or 2D), then two logins in one home with the real `startplasma-wayland`; KWin's own log names each window it adds; the pointer rests on a point of the Welcome window that no other window covers (from KWin's stacking order), the first page is captured, the mouse's forward button (evdev 276) turns the page, a click on the page's button opens the setting; `MOCK_PAGES=A,B` shows other pages with `plasma-welcome --pages` for pictures of pages that do not ship.
4. `measure-welcome.py page1|page2|flat2d`: the first page's eyes against the picture's own views (PSNR), nothing else differing; the drawing's window behind measured on its inner bars against the same page on a 2D output; a 2D output showing the left view.
5. `prove.sh OUT`: every case and every row, one row per claim, exit 1 on a row not as expected.

Milestone 2 (`prove-m2.sh OUT [m1 … m9]`; m9, the depth, wallpaper and Windows keys pages, came with 20261125.2) adds, in the same folder:
- `mklayer.sh BASE TAG LOGS PKG…`: one thin image layer installed by apt with the edition's tree mounted, apt's plan (`Inst`, `Remv`) kept; `mkbuilder.sh` freezes a source's build dependencies in the builder.
- `eyes-align.py CAPTURE REGION`: pair or one view, by the horizontal shift that best aligns the two eyes (a pair with depth of its own cannot be aligned by one shift; the desktop's own layers can); proved on known-flat and known-pair captures. With `MEASURE_SCALE` and `MEASURE_ORIGIN_X` it maps KWin's logical frame to one output's device pixels (125 %, a second output); `measure-welcome.py` takes the same, and `MEASURE_MIN_DB` for a resampled picture.
- `APP_CMD` (a program run in the first login, then both eyes), `QUIET_FIRST_RUN`, `USER_SETUP`, `SEED_HOME` (an earlier account's home), `STANDIN_PKEXEC` (a pkexec that writes what it was asked), `SCALE`, `OUTPUTS=2` and `LOGIN_LANG` in `welcome-login.sh`; the open catalogues of the Welcome Center read from `/proc/PID/maps`.
- `page-clicks.sh`: real clicks on every button and link of a page opened with `--pages`, the address a stand-in browser receives (`m2-setup.sh`), the commands, the windows and the clipboard after each.
- `touch-measure.sh`: a click and a tap (`fakeinput t:X,Y`; `h:X,Y` is a long touch) on a desktop icon, a Dolphin item and a task button, each read from KWin's own window list; the task buttons from KWin's `iconGeometry` (`kwin-windows-icons.py`).
- `cond-check.sh`: the Welcome Center started with the session's own `XDG_CONFIG_DIRS` (read from plasmashell), the first page it shows told by its first line of text (`which-page.py`, references in `refs/`).
- `unit-case.sh`: a unit under a real user manager (systemd as PID 1); `live-seed.sh`: the live user's home as the live-config hook leaves it.
- `compare-debs.sh OLD NEW`: a successor's paths against its predecessor's; `stage.sh`: a stage as source closures with their sums.
- `m9-setup.sh`: with `VARIETY_RAN=1` the account has started Variety before (its `~/.config/variety/.firstrun`), so its button opens Preferences rather than Variety's first questions; `refs/text-wallpaper.png` tells the wallpaper page by its first line.

## What was measured (ORDER 63 and 720, milestone 1, 2026-11-25)

Fresh logins of a new account on a 1920x1080 virtual output, Stereo KWin +stereo3d64 on the NVIDIA card, the session's programs on llvmpipe, the person's limits unsaved (KWin's 10 sunk and 4 popped) unless named; 18 rows, every one as predicted.

| Case | Result |
| --- | --- |
| Published set installed by apt, first login | both first-run windows, KDE's and SparkyLinux's |
| Published set in the ISO's state, first and second login | SparkyLinux's window only; then nothing |
| The edition's pages, first and second login | KDE's Welcome Center with the two pages first (and SparkyLinux's window until milestone 2); then nothing, `LastSeenVersion=6.7.4` in the person's file |
| First page, 3D output | the picture a pair: each eye matches its own view (33.3 and 33.1 dB, against 16.7 and 16.8 for the other view), 0 differing pixels outside it |
| First page, 2D output | one picture; the picture is the left view (33.2 dB) |
| Pointer page, 3D output, sunk 10 / sunk 20 | the drawing's window behind −1 and +1 / −2 and +2 px in the left and right eye from its 2D place, the window under the pointer and every other pixel at 0 |
| The page's button | System Settings opens on Window Behavior, Focus: Focus follows mouse, 300 ms, raise on hover 750 ms |
| KDE's own Welcome page, 2D output | 0 differing pixels between Debian's 6.7.4-1+b1 and the edition's +stereo3d1 |
| Upgrade from the ISO's state | the marked `/etc/xdg/plasma-welcomerc` removed; a file without the mark kept |

## What was measured (milestone 2, 2026-11-25)

On the successors staged together (stereo-layer 1.23.4, plasma-welcome +stereo3d2, sparky-stereo-welcome 20261125.1, sparky-stereo-info 20261125), one rerun (`prove-m2.sh`), every row as predicted:

| Case | Result |
| --- | --- |
| A picture under clips that hold it (a Welcome page in the ColumnView), 1.23.3 / 1.23.4 | one view, `stereoActive` false / a pair, `stereoActive` true |
| A picture under a clip that cuts it | one view on both; 1.23.4 logs the clip once |
| Koko's viewer, the stereo wallpaper, the installer's slideshow, published layer / 1.23.4 | a pair on both: none of them sits under a clip, so the fix changes nothing they show |
| SparkyLinux page | the 16 addresses as Sparky Welcome's page has them; AppCenter and Upgrade ask pkexec for their programs; Upgrade's first use then spsudo's password window; About and System info their own windows; a missing program and a failed one said on the page |
| Help Test page | the clipboard holds `stereo-display-info`'s text; the tracker's address |
| Touch page | its two buttons open General Behavior and Virtual Keyboard; the touch table above; shown with the mark, not without it, and on every computer as shipped |
| Sparky Welcome's first-run unit under a user manager | run on the published set, skipped on the successors |
| Accounts before and after the upgrade | the table above |
| Live session | the live user's `plasma-welcomerc` from the hook; the Welcome Center in its live mode, KDE's installer page first, then the edition's first page, its picture a pair |
| Ten languages | each login's first page translated, the language's own `sparky-stereo-welcome.mo` open in the Welcome Center |
| 125 % and two outputs | the first page's picture a pair (at 125 % each eye about 24 dB from its own view, 16 from the other: the compositor resamples it); the drawing's window behind −1/+1 device pixels, the rest at the screen |

**20261125.2 (2026-11-25), the same rerun whole, 122 rows, every one as predicted:** the touch page shown where the hardware layer says a touch screen is there, not where it says none, not on the rig; the three new pages' buttons open 3D Depth, Variety's "Welcome to Variety!" on a new account or "Variety Preferences" once Variety has run, Shortcuts and Desktop Session; the depth drawing's sun at 10, the window's lines at 0 and the menu at −4 at KWin's default limits, the keys page flat; the wallpaper page shown where Variety is installed and not where it is not; each page's heading translated in pt_BR, de_DE and ja_JP.

## Traps

### The pages of 2026-11-25 (20261125.2)

- **Symptom:** the wallpaper page's button opens "Welcome to Variety!", not Variety's Preferences. **Cause:** Variety's first start (no `~/.config/variety/.firstrun`) asks its welcome and privacy questions first, then writes its autostart entry and opens Preferences (`VarietyWindow.first_run`). **Fix:** not a fault; the page says so, and the rig proves both accounts, a new one and one that started Variety before (`m9-setup.sh`, `VARIETY_RAN=1`).
- **Symptom:** a drawing's sunk part shows no depth, or half of it at one edge. **Cause:** the edition's Qt Quick keeps a sunk element's edges at their 2D place, and a fill that only changes from top to bottom has nothing that moves sideways. **Fix:** give the part a picture of its own inside it (the depth page's sun and hills) and measure inside it.
- **Symptom:** `build-script-packages.sh` on a `git worktree` stops with `fatal: not a git repository: …/.git/worktrees/NAME`. **Cause:** a worktree's `.git` is a file pointing into the main clone, which the build container does not mount. **Fix:** a standalone `git clone --shared` checked out at the commit.
- **Symptom:** removing that scratch clone is refused ("commits on no remote"). **Cause:** a `--shared` clone carries the source clone's branches, and the cleanup guard counts them. **Fix:** bundle the branch into the lane folder first, then remove the clone.
- **Symptom:** Variety's tray icon or a program's Recommends are missing from a rig image although the ISO has them. **Cause:** `mklayer.sh` installs with `--no-install-recommends`, while the ISO installs the desktop meta with its Recommends (`rootfs.sh`). **Fix:** name such a Recommends in the layer (`gir1.2-ayatanaappindicator3-0.1` beside `variety`).

### Milestone 2

- **Symptom:** a rig session starts Sparky Welcome although its unit carries a drop-in that skips it. **Cause:** the rig's session has no systemd user manager (its bus is `dbus-run-session`'s), so startplasma starts the XDG autostart entries itself and no unit, no drop-in, applies. **Fix:** prove the unit under a real user manager (systemd as PID 1 in a throwaway container, `user@1000.service`, `libpam-systemd` and `dbus-user-session`: the welcome recipe's `tests/first-run-unit.sh`, run by the rig's `unit-case.sh`), and read the rig's session rows for what the kded module and the pages do. **Found by:** the published set and the candidate both showing Sparky Welcome in the rig, then the user manager's journal saying `skipped, unmet condition check ConditionPathExists=!…` for the candidate.
- **Symptom:** Sparky Welcome opens at every login of a rig account that already has its mark. **Cause:** Sparky Welcome looks for its mark under `/home/$(whoami)`, and the rig's session ran with `HOME` in the case folder. **Fix:** mount the case's home folder at the image's `/home/person` (`run-case.sh`), so `HOME` and `/home/$USER` are the same folder, as on an installed system.
- **Symptom:** a rig case gives different results from the same images, or bash prints syntax errors in the middle of a case. **Cause:** a script was edited while a run was executing it; bash reads a script by byte offset as it goes, also through a container's bind mount. **Fix:** never edit a rig script while a run uses it; if it happened, pad the edited line back to its old byte length and rerun the cases that ran meanwhile.
- **Symptom:** a page's Kirigami button or link misses its click after an earlier click on the same page. **Cause:** an `InlineMessage` that appears ("Copied: …") pushes the centred column down. **Fix:** click what lies below a message before what makes it appear, or read the place again.
- **Symptom:** Koko opens no file given on its command line (`Cannot call method 'openMediaViewPage' of null`). **Cause:** its gallery imports `org.kde.purpose`, which neither Debian's koko 26.04.0-1+b1 nor the edition's +stereo3d3 depends on (`${qml6:Depends}` does not bring it). **Fix in the rig:** install `qml6-module-org-kde-purpose`; not filed.
- **Symptom:** Calamares stops at once with "Cowardly refusing to continue startup without a QML directory", then "The branding component name should match the name of the component directory". **Cause:** a configuration folder given with `-c` must hold `qml/` and `branding/`; the edition's branding folder is `sparky-stereo` with `componentName: sparky`, reached through the package's link `/etc/calamares/branding/sparky`. **Fix:** link `qml` to `/usr/share/calamares/qml` and `branding` to `/etc/calamares/branding`, and name `branding: sparky`; Calamares then runs as the session's user in debug mode and shows its slideshow during the install step.
- **Symptom:** a rig image stops with `update-alternatives: error: cannot create symbolic link '/usr/share/images/desktop-base/desktop-background.dpkg-tmp'` configuring `sparky-artwork`. **Cause:** SparkyLinux's `sparky-artwork` makes an alternative in a folder only `desktop-base` creates, and does not depend on it. **Fix in the rig:** install `desktop-base` with it, as the image has; not filed.
- **Symptom:** a test's D-Bus session fails with "Memory allocation failure in message bus". **Cause:** the container has no passwd entry for the user (dbus-daemon logs "Could not get password database information"). **Fix:** run as a user the container knows (`useradd`, `runuser`), as the recipes' build jobs do.
- **Symptom:** an offscreen test window shows the picture's reason as the wrong screen's. **Cause:** the offscreen platform puts a window on the screen its place lies on, `(0, 0)` by default, whatever `setScreen()` said. **Fix:** set the window's geometry inside the screen meant.
- **Symptom:** the task bar answers a fake touch differently from run to run (one tap activates a window in one run and not in another; a long touch opens the window's menu once, not another time) while the desktop and Dolphin answer the same every time. **Cause:** not found. **What to do:** keep such rows as notes, never as claims, and settle them on a real touch screen.

### Milestone 1

- **Symptom:** a fresh install opens both first-run windows, KDE's and SparkyLinux's, although the published sparky-stereo-info was meant to keep KDE's closed. **Cause:** its postinst wrote `/etc/xdg/plasma-welcomerc` only when `plasma-welcome` was already "install ok installed", and apt configured sparky-stereo-info first; its file trigger on the kded module never ran (no `trigproc` line in `/var/log/dpkg.log`). The ISO's pack step reinstalls sparky-stereo-info at the end, so an installed ISO showed only SparkyLinux's window. **Fix:** the mechanism is retired (sparky-stereo-info 20261125). **Found by:** the red login on a rig image made by apt, then `/var/log/dpkg.log`'s configure times of the two packages.
- **Symptom:** the first page's picture is the same in both eyes, the rest of the screen a pair. **Cause:** two clipping ancestors (above). **Found by:** a page of the rig printing `stereoActive`, `stereoFailure` and each ancestor's `clip`, then the same picture in the window's content item: `stereoActive=true`.
- **Symptom:** `Cannot assign to non-existent property "parent"` on a QML `Window` meant as a child window of a page. **Cause:** Qt 6.11.2's QML `Window` here takes no Item as its parent. **Fix:** the content item route above.
- **Symptom:** a drawn pointer is a large white wedge across the page. **Cause:** inside a `ShapePath`, `parent` is not the `Shape`. **Fix:** refer to the shape by `id`.
- **Symptom:** a sunk element measures half its predicted disparity on its edges (−1 for −2). **Cause:** the edition's Qt Quick cuts a sunk element to its 2D rectangle, so each eye loses the shifted pixel at one edge. **Fix:** measure what lies inside the element against the same page on a 2D output: left −1, right +1. **Found by:** the 2D output's edges (160 to 367) against the eyes' (160 to 366, 161 to 367).
- **Symptom:** the pointer rests on the Welcome window and another window takes the keys. **Cause:** Sparky Welcome's window lies over most of KDE's (focus follows the mouse; the window under the pointer gets the keys). **Fix:** rest on a point no window above covers, from KWin's stacking order; it is also the page's own lesson.
- **Symptom:** `plasma-welcome --pages` started from the rig's shell fails with "could not connect to display". **Cause:** the rig's inner shell is not a child of `startplasma-wayland`. **Fix:** give that program `WAYLAND_DISPLAY=wayland-0`, `QT_QPA_PLATFORM=wayland` and the KDE session variables.
- **Symptom:** a rig image stops with `sparky-stereo-hardware Depends nvidia-detect but none of the choices are installable`. **Cause:** Debian's base image lists only `main`; `nvidia-detect` is in `non-free`. **Fix:** `Components: main contrib non-free non-free-firmware` in the image's `debian.sources`, as an installed edition has.
- **Symptom:** a read-only `curl -G --data-urlencode` query to a forge's API is refused as "a write to another project's forge". **Cause:** the outreach guard reads form-encoding options as a write. **Fix:** build the address in Python (`urllib.parse.urlencode`) and GET it (the same trap is in search-upstream-first's lessons for Qt's Jira).
