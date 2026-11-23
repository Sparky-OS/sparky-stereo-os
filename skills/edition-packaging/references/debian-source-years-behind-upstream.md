# A program whose Debian source is years behind its upstream

**For** a packager whose program is missing from Debian testing while Debian's own source is an old release and the edition's work stands on upstream's current tree: which source to build, how to choose the version so upstream's final release replaces it, what of Debian's packaging to keep, and the traps met.
Learned on OpenSCAD (queue row 50, step 4, November 2026): Debian testing had none, unstable had 2021.01-14 (Qt 5, qmake), and upstream's newest tag was `openscad-2026.11-RC1` (Qt 6, CMake).

## The recipe

1. **Read why it is missing, then where it lives.**
   Follow [carried from Debian unstable](carried-from-debian-unstable.md): britney's `excuses.yaml.gz` (the item's block, not one line: the fields come before `source:`), the bug over SOAP, `removals.txt`, the source's suites from `sources.debian.org/api/src/NAME/`, madison.
   Then SparkyLinux's own suites (core, tiamat, orion, sisters): each `InRelease` checked with Paweł's key, each `Packages` against its `SHA256` line.
   Then the published edition tree, the accepted pool and every stage (`find ... -iname '*NAME*.dsc'`).
   OpenSCAD: blocked only by serious bug 1149820, a build test of the 2021 source; autopkgtests passing on seven architectures; no removal record; SparkyLinux carries none.
2. **Decide the source by where the work stands.**
   When the edition's patches target upstream's current tree and Debian's source is a release years older, a patch series does not apply there (OpenSCAD's stereo patches touch Qt 6 code a 2021 tree does not have), so the package is built from upstream's newest tag.
   Read the tags with `git ls-remote --tags` and the releases with the forge's API, and date both: a tag can exist with no release yet (OpenSCAD's RC1 was tagged on master's head the same night, with no tarball and no release page; RC0 had both, signed).
3. **Make the orig tarball reproducibly when upstream published none.**
   `git archive` of the tag's commit, checked against the commit the recipe records (a moved tag stops the script), plus only the submodules the build takes from source, each fetched at the commit the tag pins and checked; write the version files upstream's build reads (OpenSCAD's `VERSION.txt` and `COMMIT.txt`); `tar --sort=name --owner=0 --group=0 --numeric-owner --mtime=@COMMIT_TIME`, `xz -T1`.
   Two runs must give the same bytes; put the SHA-256 in `build.sh` and check it before unpacking.
4. **Version it below the final release and below Debian's first packaging.**
   `UPSTREAM~rcN-0+stereo3d1`: `~` sorts below the bare upstream version, so the final, packaged as `UPSTREAM-0+stereo3d1`, replaces it, and Debian revision `0` sorts below Debian's own `UPSTREAM-1`.
   Check every pair with `dpkg --compare-versions` in the build container; Debian itself used the form once (`openscad 2019.01~RC2-2`).
5. **Keep Debian's packaging where it still fits, and name every departure.**
   Kept for OpenSCAD: the description, hardening, the removals Debian made in `debian/rules` (bundled fonts, the examples' licence copy, the MCAD library left to its own package), the GLES-free dependency, `debian/copyright` as the base, the reportbug script, the documentation link.
   Departed, each said in the recipe's README and changelog: the build system (CMake and Ninja; upstream dropped qmake), the toolkit (Qt 6), the catalogues compiled in `debian/rules`, a bundled library Debian lacks built from its submodule (Manifold), the test-suite packages not built, files upstream removed (its Emacs mode, with upstream's commit named).
6. **One copy of each library.** Configure with Debian's libraries wherever Debian has them (Clipper2, OpenCSG, mimalloc found through its CMake package) and look each name up with `apt-cache policy` first; a library Debian lacks is built from its submodule and gets its stanza in `debian/copyright`.
7. **Then the edition's own steps** as for any rebuilt package: the patches last in the series, `lean.debian_prepare`, `reproducible.py normalize-tree`, `dpkg-buildpackage -sa`, `lean.release check-debs`, the build record with `recipeDirty` false.
8. **Compare with what a person had before:** Debian unstable's binary packages of the old release, `dpkg-deb -c` of both, every path that left explained (OpenSCAD: the test-suite packages, the Emacs mode, the files of a 2021 tree that a 2026 tree no longer has).

## Traps, symptom first

- **Symptom:** britney's excuse for the package prints only `source: NAME`. **Cause:** an `awk` that starts the block at `source:`; the YAML item's fields come before it. **Fix:** buffer each item from its `- ` line and print the item whose `item-name:` matches.
- **Symptom:** a SOAP bug log's first message decodes to bytes of noise. **Cause:** the body was base64-decoded although its element was plain text. **Fix:** decode by the element's `xsi:type` (`base64Binary` or a string), as the carry recipe's trap says.
- **Symptom:** `gpgv` prints no "Good signature" line in a script. **Cause:** a localized system prints it in its own language. **Fix:** `LC_ALL=C gpgv ...`.
- **Symptom:** `snapshot.debian.org` returns a few hundred bytes of HTML instead of an index. **Cause:** it answers with a redirect to `/file/HASH`. **Fix:** `curl -L`, then check the file's SHA-256 against the signed `InRelease`.
- **Symptom:** a rig built from Debian's snapshot of a later day cannot install Stereo KWin ("libkf6xmlgui6 Depends libkf6iconthemes6 (>= 6.32.0~) but none of the choices are installable"). **Cause:** Debian moved to KDE Frameworks 6.32 after the published tree was made; the edition's own 6.32 forks are in the accepted pool, not in the published tree. **Fix:** give the rig the accepted pool as a flat repository at the same pin (or take Debian from the snapshot of the published tree's own day), and say which in the report.
- **Symptom:** configuring fails with "Could not open file for write in copy operation /src/openscad.appdata.xml.in2.tmp: Read-only file system". **Cause:** OpenSCAD's CMake writes generated files into its source tree. **Fix:** build from a copy of the tree, never a read-only mount.
- **Symptom:** an incremental build recompiles almost everything after a one-file change. **Cause:** `rsync --delete` from a clean checkout removed the files CMake had generated into the source copy, so CMake regenerated its configuration headers. **Fix:** copy without `--delete`.
- **Symptom:** Debian's package installed the release notes and the new tree still has the file. **Cause:** upstream stopped updating it: OpenSCAD's `RELEASE_NOTES.md` in the 2026.11 tree still describes 2021.01 (last changed 2021-02-07). **Fix:** read a document's first lines before carrying it into `debian/*.docs`; one that describes an older release stays out, and the comparison says why.
- **Symptom:** text in a model is drawn with another font than upstream's build draws. **Cause:** Debian's rules drop the bundled fonts and name no font package, while upstream's default is "Liberation Sans" (`FontCache::DEFAULT_FONT`); the edition's image installs `fonts-liberation`, a bare install does not. **Fix:** name the font's package in `Depends` when the default font comes bundled upstream (OpenSCAD: `fonts-liberation`).
- **Symptom:** "expected primary-expression before 'int'" at `Status::Ok` in a file that includes `stereo-declare.h`. **Cause:** Xlib (which the header includes) defines `Status` as a macro. **Fix:** keep the library's calls in a translation unit of their own behind a plain interface, and name nothing `Status` there.
