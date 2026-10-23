# Paweł's formula for Sparky-style packages

**For maintainers of the edition's own tools, themes and metapackages:** how SparkyLinux packages its own work, and what the edition adds.

Sparky Stereo OS is Daniel Ramos's edition of SparkyLinux (https://sparkylinux.org), the distribution Paweł "pavroo" Pijanowski created.
Everything we ship follows Paweł's way first; our side adds only what the stereo stack needs.
These rules come from reading Paweł's own packages and repositories (2026-10-02), with Daniel's later decisions dated where they apply.
His repositories are the reference: when this page and his current practice differ, follow his and correct this page.

## The tool's repository

- One git repository per tool. The folder name is the package name, with the `sparky-` prefix for tools of the Sparky ecosystem.
- It holds `bin/`, `lang/`, `share/` (the `.desktop` file and the icon), `install.sh` (install and uninstall), `CHANGELOG`, `copyright`, `LICENSE` (GPLv3) and `README.md`.
- `README.md` follows his template: a title line, a one-sentence description, the copyright line, the GPL paragraph, then the `Dependencies:`, `Install:` and `Uninstall:` blocks, each under a line of `-------------`.
- `lang/` holds `en` first, `pl` second (Paweł's language, which he reviews), `pt_BR` third, then `fr`, `de`, `ja`, `ko`, `zh_CN` and `zh_TW`.
  These nine are the required set for every string the edition adds (Daniel, 2026-10-11; German since 2026-10-15); any other language comes after them.
- A commit in a tool's repository has the new version string as its message, followed by the `Assisted-by:` trailer when an assistant helped.

## The binary package

- Assembled by hand with `dpkg-deb --root-owner-group -b`.
- `DEBIAN/control` and `DEBIAN/md5sums` only. Maintainer scripts only when they are needed, and small.
- `/usr/share/doc/<package>/copyright`, and no `changelog.Debian`.
- **Control fields in this order:** `Package`, `Version`, `Architecture`, `Maintainer`, `Installed-Size`, `Depends`, then `Recommends`, `Suggests`, `Conflicts` or `Replaces` when needed, `Section`, `Priority`, `Homepage`, `Description`.
- `Section:` is a capitalised free word (`System`, `Utilities`). `Priority: optional`. `Architecture: all` for scripts.
- `Depends` is alphabetical, with versions only when they are needed.
- `Description` is a short title line, then the body indented by two spaces.
- The provenance fields (`Maintainer`, `Homepage`, `Bugs`) are the edition's, as [the skill's provenance section](../SKILL.md#provenance-daniel-2026-10-02-always) says.

## Versions and the changelog

- Small tools: `0.MINOR.PATCH`, one step per change.
- Packages tied to a generation (themes, desktop settings, ISO tooling): `YYYYMMDD~sparky9~0`. A second build on the same day is `YYYYMMDD.1~sparky9~0`.
- Metapackages: the date alone.
- `CHANGELOG` lives in git, newest first: a rule line of 79 dashes, `  Version X (YYYY-MM-DD)`, the rule line again, then `  * ` bullets, terse and capitalised, with no full stop.

## Copyright and script headers

- `copyright` keeps his prose shape: `Upstream Author(s):`, `Files: *` with the indented `Copyright ...` and `License: GPL-2` lines, the GPL paragraph, and the line that points at `/usr/share/common-licenses`.
- Our authors get their own `Files:` block. Anything derived keeps its upstream licence text. State one GPL version consistently.
- A script starts with this header (GPL3 on new code), and forked code keeps its credit chain above ours:

```sh
# Created by Paweł "pavroo" Pijanowski and Daniel Ramos (Capitain Jack) YYYY/MM/DD
# Copyright YYYY under the GNU GPL2 License
# Last update YYYY/MM/DD
```

## Code

- Bash, indented with tabs.
- Strings live in sourced files, `/usr/share/sparky/<tool>/<code>`, as `LOCAL1` to `LOCALn` (`LOCAL001` and up in AppCenter).
- The language comes from `/etc/default/locale`.
  Match the whole `LANG=xx_YY` first, never a substring: a plain `grep de` also matches other locales.
  Then match the bare language, so `fr` serves fr_FR, fr_CA and fr_BE, and `ja` and `ko` work the same way.
  Chinese keeps its territory, `zh_CN` or `zh_TW`. English comes last.
- Write the fr, ja, ko and zh strings with care, have a second model check them, and welcome corrections from native speakers.
  Paweł reviews pl after publication; Daniel reviews pt_BR.
- Dialogs use yad (zenity for progress, dialog in text mode), not kdialog.
- A root check comes first in a tool that needs root, and commands run visibly in `sparky-xterm`.
- **Privilege:** the `.desktop` entry runs `Exec=remsu /usr/bin/<tool>` (`remsu` is `pkexec "$@"`), with a polkit policy `org.<tool>.policy` whose action is `org.<tool>`, whose `exec.path` is the program and whose `allow_gui` is true.
  His policies live in `sparky-remsu`; ours ship in our own package.
- **`.desktop` files** use his keys: `Version=1.0`, `Encoding=UTF-8`, `Name[xx]` and `Comment[xx]` inside the file, and `Categories=Applications;<One>;`.
  The icon comes from the theme or from `/usr/share/icons/sparky/<tool>/`.

## APTus

- Today's APTus is AppCenter (`/usr/lib/sparky-aptus-appcenter`): HTML pages shown in yad, `aptus://<prefix>_<key>` links handled by `handler`, the logic for each application in `bin/aptus-app`, and the vendor flows in `bin/aptus-package-install`, `bin/aptus-package-reinstall` and `bin/aptus-package-remove`.
- Its sections are hard-coded in `handler` and `aptus-appcenter`.
  A new section (3D emulation, say, or certificate tools such as PJeOffice and tokens) is either our own package in the older per-section style (`/usr/lib/sparky-aptus/<section>/<app>.desktop`, a `sparky-aptus-<section>` script, its strings and its policy) or a pull request to [sparky-aptus-appcenter](https://github.com/sparkylinux/sparky-aptus-appcenter).
  The edition's own fork is `sparky-aptus-stereo-appcenter` in [the build tree](https://github.com/Sparky-OS/sparky-stereo-os-build/tree/main/sparky-os/sparky-aptus-stereo-appcenter).
  Never overwrite his files.
- Vendor downloads follow his pattern (`wget`, then `apt-get install ./x.deb` in `sparky-xterm`), plus what his lacks: check a known SHA-256 before installing.

## Working with Paweł

- **His review comes after publication (Daniel, 2026-10-02).**
  Our packages, Polish strings included, ship once our own review chain has passed: the work, a review, the fixes, an independent second review, and tests that fail on the old code.
  Then we tell Paweł what to look at, and his feedback becomes the next version.
- Anything on his side needs his approval first: sparkyos.org on his server, his packages and repositories, his keys and suites.
- His own packages are never modified in place: ship ours beside them, divert with `dpkg-divert`, or send him a pull request.
- Release posts follow the shape of Paweł's own release posts on sparkylinux.org and carry the edition's disclaimer: the system is provided as is, it is built on Debian testing like most derivatives, and there is no paid support.
