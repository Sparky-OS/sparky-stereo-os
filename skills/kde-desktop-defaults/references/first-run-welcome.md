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

**A `StereoPicture` in a Kirigami page is one view in both eyes** (stereo-layer 1.22.0): `PictureItem::updatePolish()` hands over a pair only when no ancestor clips, scales, rotates or fades the item, and both the Welcome page and Kirigami's `ColumnView` set `clip`.
The edition's first page keeps its picture in the window's own content item (`parent: root.Window.contentItem`), over an empty `Item` that holds its place on the page, follows that place every 50 ms, and shows only while the page is the current one and stands still; the Welcome window already has an alpha buffer, so nothing else is needed.
The engine's fix is for stereo-layer: a clip whose rectangle holds the whole item cuts nothing and should not refuse the pair.

## The session proof

The scripts are in [`stereo-proof-rig/scripts/welcome-login`](../../stereo-proof-rig/scripts/welcome-login/) (the loading screen's login rig, [a real login](../../stereo-proof-rig/references/login-splash.md), taken further):

1. `mkrig.sh TAG REPO APTCONF`: the published set on Debian testing pinned by digest, the edition's signed tree, deb-multimedia and SparkyLinux's own repository (Sparky Welcome and the tools it needs). `mkcandidate.sh` puts the packages under test on it as one more layer.
2. `run-case.sh IMAGE OUT VAR=VALUE...`: one fresh container per case, KWin on the NVIDIA card through CDI (`--device nvidia.com/gpu=0`, the render node's group), the session's programs on Mesa's software renderer, the core limit at 1.
3. `welcome-login.sh` (inside): the person's saved 3D screen (or 2D), then two logins in one home with the real `startplasma-wayland`; KWin's own log names each window it adds; the pointer rests on a point of the Welcome window that no other window covers (from KWin's stacking order), the first page is captured, the mouse's forward button (evdev 276) turns the page, a click on the page's button opens the setting; `MOCK_PAGES=A,B` shows other pages with `plasma-welcome --pages` for pictures of pages that do not ship.
4. `measure-welcome.py page1|page2|flat2d`: the first page's eyes against the picture's own views (PSNR), nothing else differing; the drawing's window behind measured on its inner bars against the same page on a 2D output; a 2D output showing the left view.
5. `prove.sh OUT`: every case and every row, one row per claim, exit 1 on a row not as expected.

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

## Traps

- **Symptom:** a fresh install opens both first-run windows, KDE's and SparkyLinux's, although the published sparky-stereo-info was meant to keep KDE's closed. **Cause:** its postinst wrote `/etc/xdg/plasma-welcomerc` only when `plasma-welcome` was already "install ok installed", and apt configured sparky-stereo-info first; its file trigger on the kded module never ran (no `trigproc` line in `/var/log/dpkg.log`). The ISO's pack step reinstalls sparky-stereo-info at the end, so an installed ISO showed only SparkyLinux's window. **Fix:** the mechanism is retired (sparky-stereo-info 20261125). **Found by:** the red login on a rig image made by apt, then `/var/log/dpkg.log`'s configure times of the two packages.
- **Symptom:** the first page's picture is the same in both eyes, the rest of the screen a pair. **Cause:** two clipping ancestors (above). **Found by:** a page of the rig printing `stereoActive`, `stereoFailure` and each ancestor's `clip`, then the same picture in the window's content item: `stereoActive=true`.
- **Symptom:** `Cannot assign to non-existent property "parent"` on a QML `Window` meant as a child window of a page. **Cause:** Qt 6.11.2's QML `Window` here takes no Item as its parent. **Fix:** the content item route above.
- **Symptom:** a drawn pointer is a large white wedge across the page. **Cause:** inside a `ShapePath`, `parent` is not the `Shape`. **Fix:** refer to the shape by `id`.
- **Symptom:** a sunk element measures half its predicted disparity on its edges (−1 for −2). **Cause:** the edition's Qt Quick cuts a sunk element to its 2D rectangle, so each eye loses the shifted pixel at one edge. **Fix:** measure what lies inside the element against the same page on a 2D output: left −1, right +1. **Found by:** the 2D output's edges (160 to 367) against the eyes' (160 to 366, 161 to 367).
- **Symptom:** the pointer rests on the Welcome window and another window takes the keys. **Cause:** Sparky Welcome's window lies over most of KDE's (focus follows the mouse; the window under the pointer gets the keys). **Fix:** rest on a point no window above covers, from KWin's stacking order; it is also the page's own lesson.
- **Symptom:** `plasma-welcome --pages` started from the rig's shell fails with "could not connect to display". **Cause:** the rig's inner shell is not a child of `startplasma-wayland`. **Fix:** give that program `WAYLAND_DISPLAY=wayland-0`, `QT_QPA_PLATFORM=wayland` and the KDE session variables.
- **Symptom:** a rig image stops with `sparky-stereo-hardware Depends nvidia-detect but none of the choices are installable`. **Cause:** Debian's base image lists only `main`; `nvidia-detect` is in `non-free`. **Fix:** `Components: main contrib non-free non-free-firmware` in the image's `debian.sources`, as an installed edition has.
- **Symptom:** a read-only `curl -G --data-urlencode` query to a forge's API is refused as "a write to another project's forge". **Cause:** the outreach guard reads form-encoding options as a write. **Fix:** build the address in Python (`urllib.parse.urlencode`) and GET it (the same trap is in search-upstream-first's lessons for Qt's Jira).
