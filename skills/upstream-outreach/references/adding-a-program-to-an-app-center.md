# Adding a program to a distribution's app center

Written on 2026-11-13 by ORDER 547: KamLynk (by Dionatan Simioni, MIT, published only as an AppImage on its GitHub release page) as an entry in SparkyLinux's APTus AppCenter (by Paweł "pavroo" Pijanowski, [sparkylinux/sparky-aptus-appcenter](https://github.com/sparkylinux/sparky-aptus-appcenter)), prepared as a pull request.
Load it with [upstream-outreach](../SKILL.md) when a program that is not in the distribution's archive should appear in its app center, and with [edition-packaging](../../edition-packaging/SKILL.md) for [Paweł's formula](../../edition-packaging/references/sparky-formula.md#aptus).
Everything below ran on that day; what did not run is said under "What this recipe does not prove".

## Recipe

1. **Read the tool's own precedents before choosing anything.**
   Clone the tool and read how one entry is made, end to end: the page, the handler, the script that builds the entry's page, the install, reinstall and remove scripts, the strings.
   For APTus: an entry is one `<td>` in a page (`accessories-devices.html`), an `aptus://<page key>_<name>` link, a branch in `bin/aptus-app` (architecture check, page text, installed or not), and branches in `bin/aptus-package-install`, `-reinstall` and `-remove` for anything that is not a plain `apt-get install`.
   Then answer from the tree, with the file and line:
   - which trees still get new entries (`git log --format='%h %ad %s' --date=short -- <tree>` and each tree's `CHANGELOG`): here 8 and 9 in 2026, 7 until August 2025, 6 until 2024;
   - which trees the last accepted or open pull request touched, and what it left to the maintainer (here the `CHANGELOG` and the version);
   - whether the files you will touch are the same in those trees (`cmp`), so one change serves both;
   - whether any entry installs something that is not a package of the archive, and how it is removed; when the tool has none, read the maintainer's other installers (here `teamspeak-installer`: files in `/opt/<name>`, a launcher in `/usr/bin`, a menu entry in `/usr/share/applications`, a pinned version in the URL, removal by `rm`);
   - which page holds the program's nearest neighbours, and how they are named, ordered and given an icon (most entries reuse an icon of the tool's own set).
   Search the tool's issues and pull requests, open and closed, for the program's name and for the format (`gh search issues --repo OWNER/NAME "<word>" --include-prs`), and read the open pull requests whole with their review comments: what a reviewer asked last time is asked again.
2. **The author's own channel, and the author's own checksum.**
   Nothing of the program is copied, repackaged or mirrored: the entry fetches the author's release file from the author's address.
   Read the author's page, README, licence and release yourself, and write down the date.
   Take the SHA-256 from the author's checksum file, compare it with the forge's own record of the asset (`gh api repos/OWNER/NAME/releases --jq '.[].assets[] | {name,size,digest}'`) and with a download of your own, and write the version, the file name and the checksum as three variables beside the tool's other download addresses.
   A pinned version with its checksum is what a reviewer can check; it also means each new release of the program needs a small change, and the pull request says so.
3. **The size is said before the download starts, in the tool's own way.**
   Find where the tool tells a person what an entry will fetch (APTus prints `apt show`'s `Version`, `Download-Size` and `Installed-Size` lines on the entry's page, above the Install button), and fill those same lines for a program apt has no record of.
   Use the unit the neighbours use: apt counts in powers of ten (54.6 MB), an author's page may count in powers of two (52 MB) for the same 54,561,272 bytes.
4. **Verify, then extract, then place; remove what was placed.**
   - The download lands in the tool's work folder, not executable.
   - The checksum is checked there; only a matching file is made executable.
   - Everything the install needs from the file (an AppImage's own menu entry and icon: `FILE --appimage-extract <path inside>`, which needs no FUSE) is taken out in the work folder and checked to exist.
   - Only then are the files placed, system-wide, so that every user can start the program: the file under `/opt/<name>` with a name that does not carry the version, a link in `/usr/bin` under the name the program's own menu entry runs, the menu entry in `/usr/share/applications`, the icon in `/usr/share/pixmaps`.
   - A reinstall runs the same steps, so a refused download leaves the installed program as it was.
   - Removal deletes exactly those files and any system file the program installs itself when asked (KamLynk's USB rule in `/etc/udev/rules.d`), shows each removal (`rm -rfv`), and never touches a home folder.
   - The installed state is read from a file the install places last (`[ -f /usr/bin/<name> ]`, a link whose target must exist), since apt knows nothing about it.
5. **Each failure says which one it is.**
   An architecture the program has no build for, a C library older than it needs, no connection, a download that failed, a file that does not match, a missing piece the program needs to start: each ends with its own sentence and with nothing installed.
   Use the tool's existing strings where one already says it (APTus has "The application is available for amd64 architecture only." and "Your version of operating system is too old to install the package."), so that no translation is added; put a new message where the tool's own messages appear (APTus: in its terminal window, in English, ending with `Press <ENTER> to exit...`).
6. **Prove it in the distribution's own containers, through the tool's own windows.**
   Build the image, install the tool from the branch with the tool's own `install.sh`, start it in a virtual display the way its menu entry does, and walk the entry as a person would ([the rig](#the-rig)).
   Green: the page with the entry, the entry's page with the size, the install, the installed file's checksum, the menu entry (`desktop-file-validate`, `gtk-launch <name>` as an ordinary user), the first window, a second user, the reinstall, the removal and a search of the whole system for what is left.
   Red, each in a fresh container with the scripts unchanged: a download with one byte changed, no network at all, the network lost after the page was shown, each architecture the program lacks, an old C library, the missing piece, and the reinstall with a changed download (the installed file's time stamp must not move).
   Look at every capture before calling it proof.
7. **One subject per pull request.**
   The entry and nothing else: a wrong translation of an existing string, a page that prints `\n` as text, a crash of the tool's window in the container are each their own subject, listed in the hand-back.
   Before the hand-back run `bash -n` on every changed script and `shellcheck` in a container, and read only the findings on the added lines: here 13, all of them the tree's own idiom (backticks, the page buttons' quoting, `cd` without a test) and none an error.
   The text follows the maintainer's last accepted or open pull request: what it adds, where the file comes from and how it is checked, where it is placed and how it is removed, what was tested and on what, what was not, one line that credits the author, and what was left to the maintainer.

## The rig

A distribution without a public container image is built from its base: a Debian image pulled by digest, the distribution's keyring package checked against the `SHA256` its own `Packages` index gives, the two files its apt setup package ships (`sparky.sources` with the suites `core` and `tiamat` for Sparky 9 on Debian testing, `core` and `sisters` for Sparky 8 on Debian 13; `preferences.d/sparky` with priority 1001), then `apt-get install sparky-apt sparky-aptus-appcenter`.
Add `xvfb`, `openbox`, `xdotool`, `imagemagick`, `dbus-x11`, `desktop-file-utils`, `libgl1`, `libegl1`, and two ordinary users.

```sh
# inside the container, as root: the tool from the branch, a display, the tool started as pkexec starts it
cd /src/9 && sh install.sh
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp & sleep 2; DISPLAY=:99 openbox &
env -i SHELL=/bin/bash LANG=en_US.UTF-8 TERM=xterm PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME=/root USER=root LOGNAME=root PKEXEC_UID=1000 DISPLAY=:99 /usr/bin/sparky-aptus-appcenter &
# from outside: a capture, a click read from the capture, the Enter a person presses in the terminal
docker exec -e DISPLAY=:99 C sh -c 'import -window root png:-' > page.png
docker exec -e DISPLAY=:99 C xdotool mousemove 572 305 click 1
docker exec -e DISPLAY=:99 C sh -c 'W=$(xdotool search --name SparkyTerminal | head -1); xdotool windowactivate $W; sleep 1; xdotool key Return'
```

The tool's yad window with its HTML pages, its terminal and the program's own Qt window all draw in that display with Mesa's software renderer; WebKit only warns that its sandbox helper does not work in the container.
A red case changes one answer of the system and nothing in the scripts: a directory put first in `PATH` with a stand-in `uname` (`aarch64`), `getconf` (`glibc 2.31`), `wget` (the real download, then one byte changed with `dd conv=notrunc`) or `apt-get` (refusing one package); `setarch i686` in front of the tool for a 32-bit machine; `docker run --network none`, or `docker network disconnect bridge C` once the entry's page is up.
An AppImage has no FUSE device in a container: start it with `APPIMAGE_EXTRACT_AND_RUN=1`, and say so.
Some programs have a mode without hardware (`kamlynk --demo`, a simulated camera): read the program's `main` for it and use it for the second user.

## When the program installs another container

Vinci 0.4.7, Dionatan Simioni's GPL-3.0-or-later installer for DaVinci Resolve, adds another boundary to this recipe.
The audit below was done on 2026-11-13; it is not a proof of a Resolve installation or GPU rendering.

1. Read the installer's own system checker and recipe before deciding the entry's dependencies.
   Separate what the station has installed, what the distribution's published metapackages bring, and what the archive merely offers.
   A pin for the NVIDIA container toolkit does not install it, and a distrobox recommendation does not guarantee podman.
   Vinci uses a compatible host distrobox, otherwise downloads its own; its recipe accepts versions from 1.8.0 up to, but excluding, 2.0.0 and selects 1.8.2.5 when it needs a copy.
   The entry must bring required tools or refuse with a useful message before placing the application.
2. Record every download boundary separately: the installer AppImage, its container image, container packages and the person's proprietary installer ZIP.
   Vinci's AppImage is 38,341,112 bytes and needs glibc 2.39 or newer.
   Its release provides a GitHub asset SHA-256 and a zsync file containing SHA-1, but no standalone SHA-256 manifest or signature file.
   Compare the downloaded bytes with that digest and pin it; say where the digest came from instead of inventing a `SHA256SUMS` file.
   A container image such as `ubuntu:24.04` pins the release series, not immutable bytes; check whether the recipe also records a digest.
   The AppImage's download size cannot stand for the later image, package and Resolve downloads.
3. Follow the actual exported launcher across the boundary.
   Vinci writes its own per-user desktop entry and its Open button uses the same command: an absolute distrobox path, `enter`, `env`, then `/opt/resolve/bin/resolve`.
   A rule that matches the first executable named `resolve` misses that command, and a PATH wrapper cannot intercept its absolute Resolve path inside the container.
   Check inherited GPU variables as well as those the installer adds.
   Test the person's GPU choice and native OpenGL where CUDA shares images with it; an exception for every distrobox would also change unrelated containers.
4. Prove the two execution layers separately.
   Start the installer on a private display, then exercise its actual container runtime.
   Giving a GPU to the outer test container does not prove that podman inside it can create a working container or pass that GPU through.
   If nesting is refused, keep the exact error and test that part in an isolated virtual machine; do not call a simulated runtime a successful installation.
   A virtual GPU cannot qualify the physical NVIDIA or AMD compute path either, so keep that gap explicit.
5. Keep removal boundaries equally clear.
   Removing the installer AppImage is separate from uninstalling the Resolve containers and the projects the person created.
   Read the installer's own uninstall flow, and never remove projects or reach into home folders as part of the app center's removal action.

### Audit traps

- **Symptom:** the prerequisite audit cannot confirm a brief's installed podman.
  **Cause:** archive availability does not establish installed state.
  **Fix:** check both installed package state and the executable's location, then check the published metapackage dependencies separately.
  **How found:** `dpkg-query` reported no installed podman or distrobox and `command -v` found neither, while the reference image's `apt-cache policy podman` offered 5.8.6.
- **Symptom:** an existing native NVIDIA OpenGL exception does not apply to the exported Resolve entry.
  **Cause:** the matcher sees distrobox as the executable; the actual Resolve executable is an argument inside the container.
  **Fix:** reproduce the match against the published implementation, then qualify a scoped launcher integration with the real nested launch before changing it.
  **How found:** the published matcher made one override for a native Resolve fixture and zero for Vinci's distrobox fixture.
  This establishes the matching gap only; actual OpenGL rendering remains a separate check.
- **Symptom:** a reference app-center recipe asks for the author's SHA-256 manifest, but none is published.
  **Cause:** release formats differ; Vinci publishes four assets including a zsync file, but no `SHA256SUMS`.
  **Fix:** record the release asset digest as its own source, compare the download, and never describe it as a separate signed or author-written checksum file.
  **How found:** the release API asset list and body, followed by a local SHA-256 comparison of the downloaded file.

## Traps

- **Symptom:** the image build stops with `dpkg (subprocess): cannot execute rm command for cleanup (rm): No such file or directory` and `Could not exec dpkg!` right after `Unpacking base-files (14.sparky9~0) over (14.2)`.
  **Cause:** Sparky's `base-files` ships `/bin`, `/lib` and `/sbin` as directories and no `/lib64`, while Debian's owns them as the merged-usr links; the swap removes the loader's path in the middle of the unpack. An installed Sparky has those links from its installer.
  **Fix:** keep Debian's `base-files` in the test image with a pin that sorts first (`Package: base-files`, `Pin: release o=Debian`, `Pin-Priority: 1002`); it satisfies `sparky-apt`'s dependency. Say in the report that this one package is Debian's.
  **How found:** `dpkg-deb -c` of Sparky's package against `dpkg -L base-files` in the Debian image.
- **Symptom:** in the test container the tool's first `apt-get update` prints `E: The repository '... Release' no longer has a Release file` for every source.
  **Cause:** the image was built with an apt option naming a CA file that was mounted only during the build.
  **Fix:** give every test container the same mount the build had.
  **How found:** the tool's own log; `apt-get update` in a container started without the mount prints the same lines.
- **Symptom:** the tool's terminal opens black and empty and the install never proceeds; its log has `VTE-CRITICAL ... vte_pty_spawn_with_fds_async ... assertion 'argv[0] != nullptr' failed`.
  **Cause:** the tool was started without `SHELL`; `spterm -e` runs the command through it, and `pkexec`, which the menu entry uses, always sets it for root.
  **Fix:** start the tool with the environment `pkexec` gives (the `env -i` line above).
  **How found:** the log line, then `/proc/PID/fd` of the terminal showing no pty.
- **Symptom:** a four-line change to a page shows as 152 changed lines in `git diff --stat`.
  **Cause:** the page has CRLF line endings and a scripted edit in text mode wrote LF.
  **Fix:** open with `newline=''` and insert lines with the file's own endings; check with `file` and `git diff --stat` before every commit.
- **Symptom:** the terminal says the program was installed, and the icon is missing.
  **Cause:** the AppImage's top-level icon is a link into `usr/share/icons/...`; `--appimage-extract <name>.svg` gave a dangling link, `cp` failed, and the script went on.
  **Fix:** extract the icon by its real path, and check that every extracted file exists before anything is placed, with a message of its own when one is missing.
  **How found:** the list of expected files after the green run, not the terminal's message; list what a step should leave and look for each file.
- **Symptom:** after a later release the program is gone from one user's menu though it is installed.
  **Cause:** some AppImages write their own per-user menu entry at first start (`~/.local/share/applications/<name>.desktop` with `TryExec=` the file's path); with the same file name as the system entry it wins, and a path that carried the version no longer exists.
  **Fix:** install the file under a name without the version (`/opt/kamlynk/KamLynk.AppImage`). After a removal that per-user entry hides itself, since its `TryExec` target is gone (`gtk-launch` answers "no such application").
  **How found:** reading the program's desktop integration source, then the file it wrote for the first user. Not run: the update itself.
- **Symptom:** the capture taken after a fast step shows only the page, as if nothing had happened.
  **Cause:** the tool shows the page again while the terminal opens, and the page's window lands on top.
  **Fix:** raise the terminal (`xdotool windowactivate`) before the capture; a capture with exactly the page's byte size is the page.
- **Symptom:** a 32-bit container still reports `x86_64`.
  **Cause:** `uname -m` answers for the kernel.
  **Fix:** `setarch i686` in front of the tool; for an architecture the host cannot emulate, a stand-in `uname`, named as a stand-in in the report.
- **Symptom:** the status page the install script writes never appears.
  **Cause:** in APTus the call that would show it is commented out; the terminal's last line is what a person sees.
  **Fix:** put the entry's messages in the terminal, and keep the page's text right as well.
  **How found:** reading `handler` and following the windows in the run.

## What this recipe does not prove

- The start through FUSE: the containers have no `/dev/fuse`. This AppImage's runtime is the static one (the string `type2-runtime` in the file), which needs only a `fusermount` program, from the `fuse3` package; the plain start in the container ends with `fuse: device not found, try 'modprobe fuse' first`.
- The program with its hardware, and anything behind a password prompt (KamLynk's "Allow USB access" asks through `pkexec`).
- A real session's menu: the entry was validated and started with `gtk-launch`, which reads it as a menu does.

## Perks of this part

- A GitHub release lists each asset's SHA-256 (`digest`), so the author's checksum file can be compared with the forge's own record without downloading.
- `--appimage-extract <path>` takes one file out of an AppImage without FUSE and without starting the program; `desktop-file-validate` then checks the author's own menu entry.
- The app center's dependencies can already bring what an AppImage needs: on both Sparky images `fuse3` came with the tool's HTML window (`yad` depends on WebKitGTK, which recommends `xdg-desktop-portal-gtk`, whose portal depends on `fuse3`). That is a recommendation, so a system installed without recommended packages can lack it, and the entry checks.

### Container-installer runtime lessons

- **Symptom:** distrobox creates Ubuntu successfully, then `enter` says `rev: not found` and `exec: exec: not found`.
  **Cause:** its entry script calls `rev`; an installation without recommended packages can omit the package that provides it.
  **Fix:** bring `bsdextrautils` with `podman`, `distrobox` and `fuse3`, and check `rev` before placing the AppImage.
  **How found:** the failing real `distrobox enter`, followed by installation of `bsdextrautils` and a successful repeat as the ordinary user.
- **Symptom:** nested podman says `cannot clone: Operation not permitted`, or rootless `newuidmap` cannot write `uid_map`.
  **Cause:** the outer Docker sandbox restricts the namespaces podman needs.
  **Fix:** keep the error, then use an isolated VM or a deliberately scoped container rig whose namespace permissions allow the test.
  An isolated Docker rig with `SYS_ADMIN`, unconfined seccomp/AppArmor and fresh `vfs` storage allowed the ordinary user's podman and distrobox to run here.
  These are test-rig permissions, never instructions to change the person's host or make the installed application privileged.
  **How found:** compare default, unconfined-only and namespace-capable runs, then actually pull the image, create and enter the container as the ordinary user.
- **Symptom:** a static launcher audit predicts a missing NVIDIA exception, but the runtime CUDA/OpenGL probe passes.
  **Cause:** distrobox filters inherited variable names beginning with an underscore, and the installer supplies NVIDIA's GLX vendor for its hybrid launch.
  **Fix:** let runtime evidence decide whether to enable an exception.
  A useful probe makes a physical NVIDIA EGL/OpenGL context current, creates a GL buffer, then requires both `cuGLGetDevices` and `cuGraphicsGLRegisterBuffer` to succeed inside the same distrobox launch environment.
  Retain a negative control and reject a generic exception for every distrobox command.
  **How found:** the probe passed both with and without the edition's inherited zink variables; forcing Mesa's vendor list inside the container failed EGL initialization.
  A narrow candidate can match only `distrobox enter --name vinci-free` or `vinci-studio`, followed by `-- env` and `/opt/resolve/bin/resolve`.
  That candidate is not a reason to enable it, and a desktop-only change would still miss the installer's Open button.
- **Symptom:** the package terminal closes after apt fails, and an installer could continue if its tools were already present.
  **Cause:** terminal exit status alone need not preserve the command's failure.
  **Fix:** make a success marker only after apt succeeds, require it along with each executable, and reject installation without either condition.
  **How found:** an apt stand-in returned 100 while the tools remained installed; the entry refused both installation and replacement.
- **Symptom:** the check's selected AMD heading disagrees with its NVIDIA hybrid message.
  **Cause:** a saved preference changes the selected GPU without changing the earlier hybrid finding.
  **Fix:** update both in the report's owning method and add a test selecting the second GPU.
  **How found:** the real AMD-preference window, source inspection, and a regression test that failed before the change and passed after it.
  Keep the author-facing fix as a draft until reviewed; a core test does not claim that the rebuilt GUI or Resolve was tested.

Keep three download boundaries visible: the app center's verified installer AppImage, the later container/package downloads, and the person's official Resolve ZIP.
A measured absence of that ZIP stops the Resolve proof, while the entry, system check and container-runtime tests can still be completed.
Do not replace the form with an unofficial download or describe media conversion as native codec support.

## A closed vendor program

For a closed program that its vendor offers free of charge (Open Cascade's CAD Assistant, ORDER 559), read the licence text inside the file before preparing the entry: the entry's page says in one sentence that installing accepts the vendor's agreement and where its text is kept, it names the vendor as author, and where the vendor publishes no checksum the pinned SHA-256 is said to be of the file as downloaded on a named day; an AppImage whose runtime needs the FUSE 2 library is unpacked once with its own `--appimage-extract` and started from the unpacked tree under the program's own name ([the recipe and its traps](../../native-linux/references/closed-program-quad-buffer-in-an-appimage.md)).

## The same entry in both app centers

An entry offered to SparkyLinux's main APTus also belongs in the edition's AppCenter, on the same page and with the same protocol key.
Vinci belongs on Multimedia, Video tools, with Kdenlive; KamLynk belongs on Accessories, Devices, as `accdev_kamlynk`.
The stereo tabs stay in the edition and never enter the pull request to main.
The edition stays in step with main while retaining its own entries and stereo tabs.

1. Fetch the upstream default branch and record its exact commit, the previous sync ancestor and all intervening commits by file.
   Compare each page's protocol-key inventory as well as its text diff.
   List removed upstream entries explicitly; do not silently delete an edition or stereo entry while resolving the sync.
2. Inspect the published package's file list before choosing the integration point.
   A dependency on main APTus does not mean the edition package ships its own copy of those pages.
   If it only delegates to the installed original, include the maintained main tree in the edition's own package namespace and keep the original package's files untouched.
3. Carry the accepted entry changes into the edition branch, keeping the settled page, identifier, publisher URL, size and checksum.
   Keep the edition and upstream-offer branches separate.
   On the edition, route both the page protocol and direct install/reinstall/remove backends through its shared verified action and metered-download reader.
   Translate every new sentence and label in the required ten languages; keep vendor metadata outside the stereo catalogue.
4. Relocate the copied main tree's absolute library, locale and launcher paths together.
   Keep its relative resources, category links, handler dispatch and unrelated entries intact.
   Test navigation through the installed package, not only a source `install.sh` or a file opened in isolation.
5. Compare the installed main-page inventories against the fetched source and the edition additions.
   Require every main key and both new keys to remain reachable on their intended pages.
   Compare the stereo catalogue and an unchanged action file against the published package by file hash, then compare each rendered stereo section and one visible tab's pixels.
   State the capture region: matching tab content does not claim an identical whole-window scrollbar.
6. Rebuild through the package recipe and retained source, including the normal package checks and complete build record.
   Require the seed and source-rebuilt binary hashes to match.
   Capture the two real main entry pages, the metered notice, successful installation, a tampered-download refusal and removal, with state assertions alongside the pictures.

### Sync and packaging traps

- **Symptom:** an entry exists in the edition's source tree but never appears in the installed main page.
  **Cause:** the package ships only the stereo front end and reads the original package's categories at runtime; its own maintained main tree is not packaged.
  **Fix:** package the maintained tree under the edition namespace and point category navigation and dispatch there.
  **How found:** the published package's file list, followed by comparison of its actual library paths with the tracked source tree.
- **Symptom:** carrying a second entry conflicts in several shell scripts at the same `elif` boundary.
  **Cause:** both commits insert their branches beside the same existing block, sometimes sharing the trailing `fi` context.
  **Fix:** retain both complete branches, then check syntax and the before/after entry inventories.
  **How found:** the cherry-pick conflict hunks, rather than treating either side as a replacement for the other.
- **Symptom:** a copied category page opens correctly, but its next action returns to the original package or bypasses the edition's notice.
  **Cause:** hard-coded launcher, library or locale paths, or a direct backend that still uses its old installer.
  **Fix:** relocate the complete path set and adapt the canonical backends as well as the visible page handler.
  **How found:** installed navigation and direct-backend tests, plus unchanged hashes of the original package's files.
- **Symptom:** accented entry text appears as `Â`, or the program heading is nearly white on the page.
  **Cause:** the original page was ASCII without a charset declaration, and its heading style was intended for a different location.
  **Fix:** declare UTF-8 on the generated entry page and use the main entry's readable bold-paragraph heading.
  **How found:** the actual installed entry capture; a successful JSON parse did not establish readable rendering.
- **Symptom:** the first binary package and its source rebuild differ even though their extracted file contents match.
  **Cause:** copying the main assets preserves older checkout mtimes, while source extraction normalizes them; SOURCE_DATE_EPOCH clamps newer times but does not raise older ones.
  **Fix:** apply the build tree's shared reproducible timestamp normalizer to the authored staging tree before building the source and binary packages.
  **How found:** raw extraction and content comparison of both packages, then `stat` on a copied stylesheet.
- **Symptom:** an operation changes the installed state, but closing the URI window can also lose the refreshed entry window.
  **Cause:** the next dialog still inherits the old callback's session or output channel and temporary-page lifetime.
  **Fix:** start an independent entry process with the old YAD_PID removed, let that process own its temporary page until its dialog closes, and only then close the old page.
  Keep machine-action output inside the shared action/error engine, not on the URI callback's output channel.
  **How found:** compare the installed state with the live dialog process before and after the operation; require a new surviving dialog, not only a successful install exit code.
- **Symptom:** the entry's own Spanish text is translated, but its metered warning is English.
  **Cause:** the published shared reader's language directory has nine catalogues, although its maintained source already has Spanish.
  **Fix:** check the installed reader's catalogue files and test the actual warning in every required locale.
  Until the reader's next package includes that catalogue, an edition-owned locale overlay can link the existing nine files and provide the maintained Spanish data while using the same reader for detection, settings and formatting.
  Respect the reader's explicit language-directory override.
  **How found:** the published file list and reader language() result, followed by ten installed notice-rendering checks and a Spanish GUI capture.
- **Symptom:** main's Applications link leaves the stereo tabs unreachable without restarting the program.
  **Cause:** the copied main index has no edition tabs of its own.
  **Fix:** keep the main category pages and their entries, but route the copied Home/index destination back to the edition dashboard that contains both its tabs and main's categories.
  **How found:** follow the installed Applications link and require a new dashboard process with the unchanged stereo sections.
