# A package that replaces Debian's packages

Written on 2026-11-17 from ORDER 645: installing the edition's FlightGear data downloader took Debian's `flightgear-data-base` away, and dpkg deleted the system's time zone files through an old symbolic link.

## Working recipe

1. **Read the removal before it happens.**
   In a container that has the machine's state, not a clean image (see the rig below), run `apt-get -s install YOURS | grep -E '^(Inst|Remv)'`.
   Every `Remv` line is a package whose file list dpkg will walk.
   An exit status and "0 to remove" prove nothing: read the lines.
2. **For each package to be removed, look for a path that is not what the list says it is.**
   Its file list (`dpkg -L P`, `dpkg-deb -c P.deb`) names paths; dpkg removes each of them with the system's own path resolution.
   If a parent of such a path is a symbolic link on the disk, dpkg deletes whatever the link leads to.
   The link need not be in the package's current version: a package that once shipped a link and now ships a folder keeps the old link on every computer that upgraded, because dpkg does not switch one into the other (dpkg-maintscript-helper(1): "When upgrading a package, dpkg will not automatically switch a symlink to a directory or vice-versa").
   Symbolic links are not in `md5sums`; list the data tar (`ar p P.deb data.tar.xz | xz -dc | tar -tv | grep ' -> '`) of the old versions from snapshot.debian.org (`/mr/binary/NAME/`, then `binfiles`, then `/file/HASH`; a `Range` request of the first megabytes gets the control tar and its `md5sums` without the gigabyte).
3. **Do not ask for the removal when the data can stay.**
   Nothing in a package's own maintainer scripts runs before apt removes the packages it Conflicts with (below).
   If the Debian packages already hold what yours provides, make yours take them as present, and drop `Conflicts`.
   `Provides` of a name a real installed package has is fine for apt and dpkg without a `Conflicts`.
4. **Never follow a link out of your own tree.**
   Before a script removes or writes a path it lists, resolve the folder that holds it (`realpath -m`) and refuse the path unless that folder is still under your tree.
   Say the refusal; do not delete around it.
5. **Tell the machines already hit** through the edition's one problems engine (`sparky-stereo-problems keep --machine --repair JSON PACKAGE KEY LOCALn ARGS`), with a repair that restores what was deleted from the archive and reads it back with `dpkg --verify`, in the ten languages.
6. **A report to Debian** carries the patch against Debian's source, built, and the red and green in one container ([contrib-debian](../../contrib-debian/SKILL.md)).
   For this class of fault the patch is a `debian/PACKAGE.maintscript` line, `symlink_to_dir PATH OLD-TARGET LAST-BAD-VERSION`, which dh_installdeb turns into the preinst, postinst and postrm snippets.

## The rig that reproduces it

- **Base:** `debian:testing` by digest; the edition's source with its key and pins; deb-multimedia (the edition's libraries need its `libdav1d7`); `/K3D/partners/https-only-apt.sh` first.
- **The old state, in two layers committed as images:** Debian's old package set installed from a flat local repository of the `.deb` files fetched from snapshot.debian.org (`deb [trusted=yes] file:/repo/old ./`, `dpkg-scanpackages`), then the newer Debian set upgraded over it with the same repository mechanism.
  A third image holds the machine after the fault, for the notice and repair proof.
  For ORDER 645 the old set is `flightgear-data-base` 1:2020.3.19+dfsg-1 (Timezone is a link) and the new one 1:2024.1.5+dfsg-1 (a folder of 550 files); the upgrade alone already leaves `dpkg --verify tzdata` listing 399 files as changed.
- **Red:** `apt-get -s install YOURS` (the Remv lines), then the real run; read dpkg's `warning: while removing ..., directory '...' not empty so not removed` (the sign that the removal walked a folder it does not own), `ls` of a file of the other package, `dpkg --verify OTHER`, the clock.
- **Green:** the same run with the fixed package from a flat local repository pinned above the published one (`Pin: version ...`, priority 1002), the Inst and Remv lines again, then every order apt can take: the package alone, then the program, then `dist-upgrade` (a stand-in package for the version the machine had, since that build is no longer published).
- **The cause as the one difference:** repack the fixed package with its `Conflicts` put back and run the red again: the removal, the warning and the damage return, so nothing else mattered.
- **Data that is too large to fetch on every run:** download it once into a folder, check its hash against the recorded one, and mount it read-only with `MIRROR_URL=file:///...`.

## Traps

- **Symptom:** a preinst guard in the replacing package passes its tests, yet a machine loses files.
  **Cause:** apt removes the packages a new package `Conflicts` with before it unpacks anything, so no script of the new package, or of a package it Pre-Depends on, runs first.
  **Fix:** none in scripts; do not ask for the removal (Policy 7.4: "If one package is to be unpacked, the other must be removed first").
  **Found by:** a three-case probe with mock packages that print their script names: apt with `Conflicts` printed `Removing victim` before `newpkg preinst`; with `Conflicts` and `Replaces` the same; with a `Pre-Depends: guard` the guard's preinst came after the removal too. Only `dpkg -i` with `Replaces` runs the new preinst before the removal.
- **Symptom:** "Replaces would let dpkg remove it after the preinst" is read from the manual and believed.
  **Cause:** dpkg alone does it (`prerm remove in-favour`, `preinst`, unpack, then the removal); apt still issues a separate removal first.
  **Fix:** test with apt, not with `dpkg -i`.
- **Symptom:** `dpkg --verify tzdata` lists hundreds of files as changed (`??5??????`) on a computer that never edited them.
  **Cause:** a package unpacked its own files through a link into the other package's folder.
  **Fix:** reinstall the package that owns them (`apt-get --reinstall install tzdata tzdata-legacy`); it is also the sign that a removal of the other package will delete them.
- **Symptom:** a repair that reinstalls with `apt-get` also runs the postinst of a package that was waiting to be configured, and downloads gigabytes inside the notifier's Repair.
  **Cause:** apt finishes pending configurations in the same run.
  **Fix:** say it in the problem's text.
- **Symptom:** `apt-get install -f`-style upgrade proofs show nothing for a package that is already unpacked.
  **Cause:** apt does not upgrade a dependency that the installed version still satisfies; name the successor package in the command.
- **Symptom:** a container script with `set -e` stops silently after `apt-get update | grep -v Symlink`.
  **Cause:** `grep -v` exits 1 when it prints nothing.
  **Fix:** `|| true` on that pipeline; read the log of a build that is "running" with no output.
- **Symptom:** a local flat repository under a read-only mount prints `Symlinking file ... failed` for every compression format.
  **Cause:** apt tries `Packages.xz` and the other formats first; the plain `Packages` is read afterwards.
  **Fix:** none needed; filter the lines.
- **Symptom:** a proof script edited while a background loop runs it fails with `command not found` for its own functions.
  **Cause:** bash reads a script as it runs.
  **Fix:** copy the script before starting the loop.

## What the link gate and the build record say for a script package

A package built by `lean.standalone` is checked by `lean.release check-debs` (the build record, written next to the package from the provenance facts of `build-provenance.sh`) and by `check-link` (`lc1: archive-qualified link check passed for 1 packages`; it needs bubblewrap, so the container gets `--cap-add SYS_ADMIN --security-opt seccomp=unconfined --security-opt apparmor=unconfined`, never `--privileged`).
The record says `unrecorded: buildinfo` for such a package because no `dpkg-buildpackage` ran; that is the record's honest line, not a failure.
