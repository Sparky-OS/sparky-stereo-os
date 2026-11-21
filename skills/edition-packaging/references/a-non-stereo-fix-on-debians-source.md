# A non-stereo fix on Debian's source package

For a bug in a Debian package that has nothing to do with stereo and that upstream has not fixed (ORDER 755: plasma-gamemode, see [the Game Mode applet](../../kde-desktop-defaults/references/gamemode-applet-crash.md)).
The edition rebuilds the package so that its machines stop crashing, without waiting for anybody.

## Recipe

1. Search upstream and Debian first, and write down the result ([search-upstream-first](../../search-upstream-first/SKILL.md)): the default branch's commits on the file, merge requests, issues, and Debian's tracker over SOAP (`https://bugs.debian.org/cgi-bin/soap.cgi`, `get_bugs` with `package` and with `src`).
2. Write the patch against the files of Debian's source, with a DEP-3 header: `Description`, `Author` (ours), `Origin: vendor` (not `upstream`, there is no commit), `Bug-Upstream` saying what was searched and found, `Forwarded: no` (the edition sends nothing to KDE for now), `Last-Update`.
   Credit the author of the code and the packager in the recipe's changelog entry and in the skills' `ATTRIBUTIONS.md`, by name.
3. Name the build `UPSTREAM-DEBIANREV+stereo3d1+lc1`: `+stereo3dN` is the edition's suffix for a package it changes, whatever the change (a fix is not "stereo", but the pin that makes ours win and the repository's checks key on the suffix).
4. A recipe folder `sparky-os/packages/NAME/` with `build.sh` (starts the container), `build-in-container.sh` (checks the `.dsc` by its SHA-256, adds the patch to `debian/patches/series`, writes the changelog entry from `changelog-stereo3d1.txt` with `SOURCE_DATE_RFC2822`, `dpkg-source -b`, `lean.debian_prepare`, `build-dep`, `dpkg-buildpackage`, `lean.release check-debs`), `patches/` and `tests/`. Model it on `packages/librsvg`. Debian builds with `DEB_BUILD_OPTIONS=nocheck`; the fix's test runs in its own harness, never inside the package build.
5. Prove it: the test red on Debian's source and green on the patched one, then the packages compared with Debian's file by file (`dpkg-deb -c`, byte comparison of each file), `readelf -d` NEEDED, and the control fields (Depends).
6. In the hand-back, give "Unfiled failures" the facts for the main session's list: what fails, the cause, the fix, the test.

For a library every program loads, built for amd64 and i386 with a patch of our own (and a Debian source in format 1.0, with no series to append to): [a Debian base library with a patch of our own](a-debian-base-library-with-a-vendor-patch.md).

## Traps

- **Symptom:** `lean.debian_prepare` stops with `[Errno 2] No such file or directory: 'dch'`. **Cause:** the build image lacks devscripts. **Fix:** install `devscripts`.
- **Symptom:** the recipe's docker image `sparky-lc-migration` does not exist on a lane's machine. **Cause:** it is the main session's. **Fix:** a lane builds its own image with `bubblewrap`, `node-acorn`, `nodejs`, `perl`, `gcc`, `python3-yaml`, `devscripts` and the package's build dependencies, and says so.
- **Symptom:** `build.log` ends with `Existing execute_before_dh_auto_configure: preserve and integrate its behavior explicitly`. **Cause:** `lean.debian_prepare` adds that target and two others and refuses a Debian `debian/rules` that already has one (Debian's glib2.0 does). **Fix:** none in the route yet; grep Debian's rules before writing the recipe and say it in the brief: [a Debian base library with one upstream commit](a-debian-base-library-with-one-upstream-commit.md), trap 1.
- **Symptom:** the fork's folder is built from "whatever is checked out". **Fix:** `sparky-backup-core-stereo`'s recipe pins `SOURCE_COMMIT` and a fingerprint of the folder; export the commit with `git archive` and build from the export.
