# An app center entry that needs tools

Daniel, 2026-11-14: "only when someone install vinci - same for anything that needs this sort of dependancy".

An entry in the edition's app center (Stereo APTus, `sparky-aptus-stereo-appcenter`) is an offer.
The packages its program needs to run are the entry's own: they arrive when the person installs that entry, and never as `Depends`, `Pre-Depends` or `Recommends` of the app center package, which would put them on every system at its next update.
Stereo APTus 0.1.8 depended on podman, distrobox, fuse3 and bsdextrautils for one entry (Vinci), and its upgrade proof showed 43 new packages for every system; 0.1.9 (ORDER 565) moved them into the entry and installs none.

## Working recipe

1. **List what each entry's program needs, and what the package depends on only for it.**
   Read the package's `Depends` (`dpkg-deb -f PACKAGE.deb Depends`) name by name and ask who calls it: the app center's own code (apt, python3-apt, curl for its verified downloads, yad, pkexec) stays; a package that only one entry's program needs at run time goes into that entry.
   Check the published package as well as the source: `dpkg-deb -f` on the file in the pool.
2. **Declare the tools once, in the entry.**
   A row of `main-entries.json` carries `"tools": ["podman", "distrobox", "fuse3", "bsdextrautils"]` (package names) and `"commands"` (the commands those packages must provide, checked after the install).
   A tool every entry of one kind needs is declared for the kind, in `KIND_TOOLS` of `stereo/tools.py` (`'flatpak': ['flatpak']`), so the stereo catalogue file stays byte for byte as published.
   Look every name up first: `apt-cache policy NAME` in a container with the edition's sources must show a candidate.
3. **Use the one mechanism, `stereo/tools.py`; never write an entry's own apt call.**
   - `plan(row)` runs `apt-get -s --no-remove --no-install-recommends --no-allow-unauthenticated install` for the declared tools that are **not installed**, reads apt's `Inst` lines (the packages and their archive) and sums each version's download and installed size from apt's records.
     It returns nothing when every tool is there, and refuses with apt's own `E:` reason when a tool cannot be installed.
   - `lines(row, plan)` are the sentences: which tools, how many packages from which archive, how much to download and on disk, and the total with the program's own download.
   - `download(plan)` is the same plan as one row of the install-time download notice, so the metered notice of `sparky-stereo-apt`'s reader names the program's download and the tools' together. There is one reader and one metered test; do not add another.
   - `ensure(row, plan)` downloads every archive (`--download-only`), then installs.
   - `release(row, needed_elsewhere)` runs when the entry is removed, and when an installation fails after its tools arrived.
4. **Say the sizes before anything starts, in both places.**
   The entry's page calls `plan` when it is drawn and shows the sentences beside the program's own download size; the action prints them before its first download.
   On a metered connection (or when NetworkManager cannot be read) the shared notice follows, with both rows.
5. **Order the action so that a failure changes nothing.**
   Plan and say; download the program and verify its checksum; download the tools' archives; install the tools; check the commands; place the program.
   A tool apt cannot install is refused at the plan, before any download.
6. **Every failure has its own sentence, in the ten languages:** a tool that cannot be installed (with apt's reason and "apt update"), archives that cannot be downloaded (nothing installed), an installation that failed, a program download that failed.
   The sentence says what failed, why and what to do; `Command '[...]' returned non-zero exit status 6` is not such a sentence.
7. **Tools that are already installed are left alone:** no reinstall, no upgrade, no sentence.
   Only an automatic mark changes: a declared tool that apt had installed automatically is marked manual while the entry is installed, and the entry records it (`/var/lib/sparky-aptus-stereo-appcenter/tools/ID.json`, `brought` and `held`).
8. **Removing the entry removes no tool.**
   The tools it brought or marked go back to "automatically installed" unless another installed entry declares them, and apt's own rule decides from there; the entry names the ones it brought.
   This is the lane's choice where no design was recorded; say so in the hand-back.
9. **Run the package check:** `python3 sparky-os/packages/sparky-aptus-stereo-appcenter/tests/entry-tools.py PACKAGE.deb` reads the declarations out of the built package and exits 1 when `Depends`, `Pre-Depends` or `Recommends` names one of them.

## The proofs, from the installed package

The stereo page must not change for anyone else: render it with the published package and with the new one on the same system and compare the six sections by hash (the catalogue file and the zram action by `sha256sum`).

Each case runs in a fresh container made from the published packages (the published app center installed, the tools absent), with the new package installed by apt from a flat repository that carries the edition's `Origin`.

- **The upgrade, on apt's `Inst` lines.** `apt-get -s install --only-upgrade sparky-aptus-stereo-appcenter` must print one `Inst` line, the package itself, and "1 upgraded, 0 newly installed, 0 to remove". Run the same on the withdrawn version as the red control (0.1.8: "1 upgraded, 43 newly installed").
  A rig image is not a whole edition, so `apt-get -s dist-upgrade` lists many unrelated packages there: run it once without the new package as the control and compare.
- **The entry on a system without the tools:** the page before the click (the sentences, in two languages), apt's own simulation beside it (the same count), the install, the tools' state and marks after it, a reinstall (no apt run: count the `Commandline:` lines of `/var/log/apt/history.log` before and after), the removal (the tools installed and automatic, the person's files kept).
- **The refusals, without network** (`--network none`), each on the page and in the action's output, in en_US and pt_BR: no network at all; the program downloaded and the tools' archives not (a stand-in `curl` that copies the verified file); a tool pinned out (`Pin-Priority: -1`), with a logging `curl` that must never be called; NetworkManager's answer as a fixture for metered and for not metered.
  After each: no program, no tool, and `/var/log/dpkg.log` as long as before.
- **A system that already has the tools:** `dpkg-query -W` and `apt-mark showmanual` before and after must be identical files, no record written, no sentence about tools.

## Traps

- **Symptom:** the upgrade proof of an app center version lists dozens of new packages (buildah, criu, nftables, netavark, passt) for a change that added one entry.
  **Cause:** the entry's tools were written into the package's `Depends`, and apt installs their `Recommends` too.
  **Fix:** this page.
  **Found by:** reading the `Inst` lines of the upgrade proof instead of its "0 to remove".
- **Symptom:** an entry is removed and installed again, and `apt-get -s autoremove` then lists podman while the entry is installed.
  **Cause:** the removal had marked the tools automatic, and the second install found them present and did nothing.
  **Fix:** `ensure` marks a present, automatic tool manual and records it as `held`; `release` gives the mark back.
  **Found by:** `apt-mark showauto` after each step of install, remove, install.
- **Symptom:** after two entries that share a tool are both removed, the tool stays manual although it was automatic before.
  **Cause:** the first entry marked it manual and recorded it; the second found it manual and recorded nothing; the first one's removal skipped it because the second still needed it.
  **Fix:** an entry also records a declared tool that another entry's record answers for; whichever is removed last gives the mark back.
  **Found by:** the same `apt-mark` reading over install A, install B, remove A, remove B.
- **Symptom:** the removal says "these tools came with KamLynk: fuse3" for a tool that was on the system before.
  **Cause:** one list held the tools the entry installed and the ones it only marked.
  **Fix:** two lists; only `brought` is named, `held` goes back silently.
- **Symptom:** a page in pt_BR shows English in the proof container.
  **Cause:** the image sets `LC_ALL=C`, which the package's language lookup reads before `LANG`.
  **Fix:** `unset LC_ALL LANGUAGE` in the proof and set `LANG` per case; generate the locale (`localedef -i pt_BR -f UTF-8 pt_BR.UTF-8`) so apt's own lines are translated too.
  **Found by:** `env | grep -E '^(LANG|LC_)'` in the image.
- **Symptom:** "a system without the tools" cannot be made: removing fuse3 would remove xdg-desktop-portal.
  **Cause:** every desktop has fuse3 through the portal.
  **Fix:** keep it; the proof then shows the better case, that only the missing tools are planned and named.
  **Found by:** `apt-get -s remove fuse3`, read before the removal.
- **Symptom:** an older test that counted the calls of a mocked `subprocess.run` fails after the change.
  **Cause:** the entry's tools step now runs inside the function under test.
  **Fix:** patch `tools.ensure` in that test and test the tools step in its own file.
- **Symptom:** a card says "They bring 1 packages" for an entry with one small tool (flatpak).
  **Cause:** the sentence was written with the first entry's eleven packages in mind, and nine translations inherited the plural.
  **Fix:** give a count as a figure after a label ("Packages apt installs for this: 1, from Debian. Download: 1.6 MiB."), which reads right for any number in every language; test the sentence with the entry that has one tool.
  **Found by:** the proof of the second kind of entry, read by eye.
- **Symptom:** an installation that fails after its tools arrived (no Flathub remote, a placement error) leaves a record for an entry that is not installed, and its tools marked manual for good.
  **Fix:** the action's failure path calls `release` when the entry is not installed afterwards, so the tools go back to apt's rule and the person is told they stayed.
  **Found by:** the Flatpak entry on a system without flatpak and without a remote.
- **Symptom:** stopping one's own long gate run by a pattern over `ps` arguments ends the background task with status 144.
  **Cause:** the pattern also matched the wrapper shell whose command line holds the same text.
  **Fix:** read the PID of the exact process (`ps -eo pid,comm,args`, the `timeout` or `python3` row) and kill that one; another lane's gate with other arguments must never match.
- **Symptom:** the build disk loses several gigabytes while a small package is proved, and the lane's own link gate would take 2 to 3 GB more.
  **Cause:** a publication round runs its own gate on the same disk.
  **Fix:** stop, remove the scratch, and give `lean.release check-link --scratch` a folder on a disk with room (the lane's folder under `/var/tmp`, listed in `.artifacts`); say so in the hand-back.
- **Symptom:** a script that edits several proof files stops at one failed replacement and the files after it keep their old expectations.
  **Fix:** assert every replacement, write each file only after all of its replacements matched, and rerun the syntax check on every file.

## Measured (2026-11-14, Debian testing)

- podman, distrobox and bsdextrautils without `Recommends`: 11 packages, 28.9 MiB to download, 103.8 MiB on disk (the page's sentence agrees with apt's own "Need to get 30.4 MB", "109 MB of additional disk space"); as `Depends` of a package, with `Recommends`: 43 packages.
- flatpak alone, on a system that has its libraries: 1 package, 1.6 MiB.
- lintian 2.143.0 gives the same 45 lines for 0.1.8 and 0.1.9, and every one of the published 0.1.6's 13 lines is among them: compare sorted lists with the version replaced by one word, never chase a clean run.
- `apt-get -s` for them takes about 3 s in a container, so the page of an entry with missing tools opens that much later; an entry whose tools are present runs no simulation.

## The review rule

Before accepting an app center version, read the upgrade proof's `Inst` lines for packages that only an entry needs, and refuse them.
Then run `tests/entry-tools.py` on the package, and read `dpkg-deb -f PACKAGE.deb Depends Recommends Pre-Depends` yourself.

## Bump a pinned entry and build the next app center (ORDER 589b, Vinci 0.4.9, app center 0.1.11)

An AppImage entry (`kind: appimage` in `stereo/main-entries.json`) pins one release: `version`, `url`, `size` and `sha256`.
A new release of the program is a new version of the app center package.

1. **Read what ships first.** The published pool's version (`dists/mashtabba/main/binary-all/Packages.xz`, not a brief's recollection: ORDER 589's brief said 0.1.9, the pool held 0.1.6), the staged one, the source's master.
2. **Pin from the release, not from recall.** Download the file from the project's own release page into a new folder, `sha256sum` it, take the size from `stat -c %s`, and write the four fields.
   Paweł's pages carry the same release in three scripts of the tracked tree (`9/lib/sparky-aptus-appcenter/bin/aptus-app`, `aptus-package-install`, `aptus-package-reinstall`, and the same in `8/`): the pull request that bumps the entry moves them together (a8c1e77 did).
3. **Run the source tests in a container with python3-apt** (`python3 -I -B stereo/tests/entries.py`, then `tools.py`, `displaycal.py`, `zram.py`; all four exit 0). With `SPARKY_INSTALL_DOWNLOADS_LIB` set to the build tree's `sparky-os/packages/sparky-stereo-apt/install-downloads` when the clone stands alone.
4. **Bump the recipe:** `VERSION=` in `sparky-os/packages/sparky-aptus-stereo-appcenter/build.sh`, a CHANGELOG entry on top, the README line, `stereo/VERSION`, and the build tree's gitlink on the commit of the source branch. Commit both before building: the build record is `recipeDirty: true` otherwise.
5. **Build with the recipe's own `build.sh`** in a Debian testing container with git, dpkg-dev, gcc, node-acorn, nodejs, perl, python3-yaml and the published edition set (the recipe calls `sparky-stereo-problems catalog`), mounting the build tree read only and the source clone (not the submodule folder: its `.git` file points outside the mount and `copy-recipe` stops) as `APTUS_SOURCE`.
   Source `repo/build-provenance.sh` first (`SPARKY_PROVENANCE_REQUIRED=1 sparky_provenance_init IMAGE RECIPE_DIR`) and pass `"${SPARKY_PROV_ARGS[@]}"` to `docker run`; end the container with `python3 -m lean.release check-debs /out/*.deb`.
   That first build says `build record NOT complete, unrecorded: buildinfo`; rebuild once from its `.dsc` (`dpkg-source -x`, `dpkg-buildpackage -us -uc -b`, copy the `.dsc` and `.tar.xz` back) and the record is complete; the two `.deb` files are byte for byte the same.
6. **The link gate** (`PYTHONPATH=sparky-os python3 -B -m lean.release check-link PACKAGE.deb --siblings-file S --previous-siblings-file P`, run with the variables `SPARKY_LC_ARCHIVE_CONFIG` and `SPARKY_LC_SCRATCH`; without `-I`, which drops PYTHONPATH) needs a config with Debian forky, deb-multimedia forky (the edition's FFmpeg and GStreamer are newer than Debian's), SparkyLinux's `core` and `tiamat` (the package depends on Paweł's `sparky-aptus-appcenter`) and the edition's published tree as `file:`, each with a dearmored keyring file.
   `S` and `P` list the published amd64 and all `.deb` files (no `-lc-hr`, no `-dbgsym`); `S` leaves out the old app center. Scratch on an SSD with room (about 330 MB); the floors are fixed at 2 GiB scratch and 12 GiB root and the gate refuses a lower `--root-min-free-gib`.
7. **Prove the upgrade on the published set plus the previous staged version:** `apt-get -s install --only-upgrade` prints one `Inst` line; `apt-get -s dist-upgrade` before and after differs by that one line; `tests/entry-tools.py PACKAGE.deb` passes; the entry's page (`main-entry vinci --render`) shows the new version and apt's sizes before the button; the real install leaves `/opt/vinci/application.AppImage` with the pinned SHA-256 and size; the removal says which tools stayed.
8. **A wrong checksum is refused and said:** alter one digit of `sha256` in the installed `main-entries.json` (a fixture edit inside the container, restored and checked with the package's md5sums), run the entry's install: "SHA-256 mismatch. The download was refused.", exit 1, no tool installed, `dpkg.log` as long as before.
   A stand-in `curl` earlier in PATH does not work for this: the action ran the real one.

## The seven failing cases of the app center's source tests (ORDER 589b)

`stereo/tests/entries.py` and `tools.py` failed the same seven cases on the station before and after the Vinci change (Vinci was not the cause).
The seven are what a standalone clone of the fork shows with the host's python (6 in entries.py, 1 in tools.py); in a container with python3-apt it is 5 and 1, and in the build tree's layout 4 and 0, so a count of failures names its layout.

- **Symptom:** `test_install_time_download_notice` (entries.py) and `test_sizes_are_said_first_and_the_metered_notice_names_program_and_tools` (tools.py): `ModuleNotFoundError: No module named 'sparky_install_downloads'`.
  **Cause:** the tests looked for the reader of sparky-stereo-apt at `SOURCE.parents[1]/packages/sparky-stereo-apt/install-downloads`, a path that exists in the build tree and not in the app center's own repository.
  **Fix:** `tests/layout.py` finds it (`SPARKY_INSTALL_DOWNLOADS_LIB`, the build tree beside the source, the installed package and its word catalogues) or stops naming what to set. **Found by:** running the tests in the clone alone, then in the build tree, and diffing the two failure lists.
- **Symptom:** `test_download_failure_has_visible_repair` and `test_page_shows_the_note_beside_the_entry`: `FileNotFoundError ... stereo/main/index.html`.
  **Cause:** `main/` (Paweł's pages) is laid down by the package build (`package_main.py` from the tracked tree `9/`), so no source folder has it; the cases were written when the page read his installed package. **Fix:** `layout.assembled` lays it down into a folder removed at exit, the way `build.sh` does. **Found by:** the traceback's path, `grep -n main package_main.py`.
- **Symptom:** `test_catalogue_shape_and_section_titles_in_every_language`: `'main' not found in ('emulation', 'media', ...)`, then `'appimage' not found in ('apt', 'flatpak', 'download')`. **Cause:** stale expectations: ORDER 553 (0.1.7, 0.1.8) added Vinci and KamLynk as `kind: appimage` in section `main`; the test still described the catalogue of 0.1.5. **Fix:** the test lists the section and the kind (the program was right). Two assertions hide behind each other: fix the first and rerun, the second shows.
- **Symptom:** `test_catalogues`: language files lack twenty keys (`apt_busy`, `tools_sizes`, `vinci_note`). **Cause:** ORDER 565 and 575 wrote their sentences "in the ten languages" (the required ones); the eleven older page languages of Paweł's list (el, es_AR, es_ES, fi, hu, id_ID, it, pt, pt_PT, ru, uk) stop at 0.1.5, and `common.messages()` reads English for a key they lack. **Fix:** the test holds the ten required languages to every key of English and the others to no key English lacks and the same placeholders. Whether to translate the eleven is Daniel's call (no recorded design).
- **Symptom:** `test_installed_pin_records_and_architectures`: `No module named 'apt_pkg'` on the host. **Cause:** the host's python has no python3-apt; the package depends on it. **Fix:** the test says so and fails (a missing dependency is a fault, never a skip); run the tests in a container.
- **Symptom:** after adding a helper module to `tests/`, 19 tests of tools.py fail with `module 'tools' has no attribute 'declared'`. **Cause:** `sys.path.insert(0, tests_dir)` put `tests/tools.py` ahead of the program's `tools.py`. **Fix:** `sys.path.append`.
- **Symptom:** a commit lands on `master` of a clone after a `git checkout master` made for a test run; the lane's branch is left behind. **Fix:** `git branch -f order589b <commit>`, reset master to origin; run tests from a separate worktree or an archive (`git archive REV | tar -x -C DIR`) instead of switching branches in the working clone.
