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
- `lang/` holds `en` first, `pl` second (Paweł's language, which he reviews), `pt_BR` third, then `fr`, `de`, `es`, `ja`, `ko`, `zh_CN` and `zh_TW`.
  These ten are the required set for every string the edition adds (Daniel, 2026-10-11; German since 2026-10-15; Spanish since 2026-11-10); any other language comes after them.
- A commit in a tool's repository has the new version string as its message, followed by the `Assisted-by:` trailer when an assistant helped.

## The binary package

- Assembled by hand with `dpkg-deb --root-owner-group -b`.
- `DEBIAN/control` and `DEBIAN/md5sums`, plus `DEBIAN/conffiles` when the package ships files under `/etc` ([below](#files-under-etc-are-conffiles)). Maintainer scripts only when they are needed, and small.
- `/usr/share/doc/<package>/copyright`, and no `changelog.Debian`.
- **Control fields in this order:** `Package`, `Version`, `Architecture`, `Maintainer`, `Installed-Size`, `Depends`, then `Recommends`, `Suggests`, `Conflicts` or `Replaces` when needed, `Section`, `Priority`, `Homepage`, `Description`.
- `Section:` is a capitalised free word (`System`, `Utilities`). `Priority: optional`. `Architecture: all` for scripts.
- `Depends` is alphabetical, with versions only when they are needed.
- `Description` is a short title line, then the body indented by two spaces.
- The provenance fields (`Maintainer`, `Homepage`, `Bugs`) are the edition's, as [the skill's provenance section](../SKILL.md#provenance-daniel-2026-10-02-always) says.

## Files under /etc are conffiles

Debian Policy 4.7.4.1, section 10.7.3: configuration files' "local changes must be preserved during a package upgrade", and "The easy way to achieve this behavior is to make the configuration file a conffile".
So every file the package ships under `/etc` is listed in `DEBIAN/conffiles`, and the maintainer scripts never edit it.
Policy names the other way, files managed only by maintainer scripts, and the two must not be mixed for one file.

**Turning shipped files into conffiles in a later version** needs maintainer scripts, because dpkg has no record of what the old version shipped (measured with Forky's dpkg on 2026-10-31, for `sparky-stereo-apt` 20261031.1~sparky9~0):

- Without them, dpkg treats every file whose bytes differ from the new one as changed by the person, edited or not. At a terminal it asks about each one; under `apt-get -y` with no `--force-conf*` it stops at the question (end of file on standard input, exit 100, the package unpacked but not configured, until `dpkg --configure -a` with the two options finishes it); with `--force-confdef --force-confold` it keeps every old file silently and writes the new one as `.dpkg-dist`, so an unattended upgrade would keep a stale file for good.
- With them, the pattern `dpkg-maintscript-helper rm_conffile` uses ([dpkg-maintscript-helper(1)](https://manpages.debian.org/testing/dpkg/dpkg-maintscript-helper.1.en.html)): the `preinst`, on `upgrade` from a version before the first one with conffiles, compares each file with the installed version's `md5sums` and moves an unchanged one aside as `FILE.dpkg-remove`, so dpkg installs the new file without a question; the `postinst` deletes the moved-aside copies; the `postrm` puts them back on `abort-install` and `abort-upgrade`. A changed file stays where it is, and dpkg asks, keeping the person's version by default.

What to check before publishing, each in a throwaway container that starts from the published version:

| Case | Expected |
| --- | --- |
| Nothing edited, `apt-get -y` | no question; every file is the new package's; no `.dpkg-*` left; `dpkg --verify` clean |
| One file edited, at a terminal, Enter | one question, for that file only; the edit kept, the new file as `.dpkg-dist` |
| One file edited, `--force-confdef --force-confold` | the edit kept, the new file as `.dpkg-dist`, exit 0 |
| The package without its maintainer scripts (the control that must fail) | dpkg asks about, or silently keeps, files nobody edited |
| A later version changes a file, nothing edited | "Installing new version of config file", no question |

A file the person deleted before the conversion comes back once, since the old version never recorded it as theirs; after the conversion a deleted conffile stays deleted.

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
  Then match the bare language, so `fr` serves fr_FR, fr_CA and fr_BE, and `es` serves es_ES, es_MX and es_AR (one Spanish catalogue, no territory variants), and `ja` and `ko` work the same way.
  Chinese keeps its territory, `zh_CN` or `zh_TW`. English comes last.
- Write the fr, es, ja, ko and zh strings with care, have a second model check them, and welcome corrections from native speakers.
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
  A program that is not a package at all (an AppImage from its author's release) is an entry of its own kind: [adding a program to a distribution's app center](../../upstream-outreach/references/adding-a-program-to-an-app-center.md) has the recipe and the proof.

## Working with Paweł

- **His review comes after publication (Daniel, 2026-10-02).**
  Our packages, Polish strings included, ship once our own review chain has passed: the work, a review, the fixes, an independent second review, and tests that fail on the old code.
  Then we tell Paweł what to look at, and his feedback becomes the next version.
- Anything on his side needs his approval first: sparkyos.org on his server, his packages and repositories, his keys and suites.
- His own packages are never modified in place: ship ours beside them, divert with `dpkg-divert`, or send him a pull request.
- Release posts follow the shape of Paweł's own release posts on sparkylinux.org and carry the edition's disclaimer: the system is provided as is, it is built on Debian testing like most derivatives, and there is no paid support.
