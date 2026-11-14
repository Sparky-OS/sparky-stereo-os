# Carrying a Qt Widgets painter in the source package

Recipe checked on Qt 6.11.2 and source format 3.0 (quilt).
Source preparation and re-extraction are separate gates from the full package build and installed proof.

1. Read the published source's series and changelog, then identify its active recipe.
   Check reserved candidate versions in that recipe before choosing the next one.
2. Compare the files the successful build actually used with the exported series.
   In a partial Git snapshot, an edited but untracked CMake file still affects the build and is absent from `git diff`.
   Check `git ls-files` for each source list, resource list and generated input.
3. Keep quilt patches textual.
   Carry checked baked `.qsb` resources through `debian/source/include-binaries`, then re-extract the new source and compare their SHA-256 values and the CMake entries with the measured build.
   [dpkg-source(1)](https://manpages.debian.org/testing/dpkg-dev/dpkg-source.1.en.html) describes binary inclusion in the Debian tarball.
4. Resolve bind-mount input paths with `pwd -P` or `realpath` before starting Docker.
   The daemon must see the actual repository tree, not a client-side convenience symlink.
5. Check the source-preparation tools in the build image, not only the compiler dependencies.
   An existing Qt recipe that changed only packaging did not need quilt; a recipe appending a series does.
   Verify its archive candidate, then install it through the HTTPS-only apt setup before applying patches.
6. Keep source dates from the committed recipe, preserve the inherited Lean Code consumer plan, run header synchronization before documentation where needed, and retain the public-header gate.
7. Tie a settings page to the package that implements its choices.
   A lower bound such as `>= ...-5+stereo3d17` also accepts stock Debian `...-7`, which may have none of the feature.
   An exact candidate bundle dependency prevents that mismatch while the feature is unmerged; update it together with the next qualified Qt build.
   Check package ownership: the Wayland EGL integration plugin can belong to the Wayland client library package, not the generic QPA package.

Traps and how they were found:

- **Symptom:** the prototype works but its patch series contains neither the engine source-list entry nor the shader resource entries.
  **Cause:** the Gui CMake file was outside a partial Git snapshot.
  **Fix:** export the missing diff against the published file and independently build the resulting source package.
  **Found by:** `git ls-files` returned nothing for the edited file; the newly packed source then matched all 27 changed build inputs.
- **Symptom:** Docker reports that creating the repository mount path failed because a file exists.
  **Cause:** the input was a convenience symlink the daemon could not resolve as the client did.
  **Fix:** pass the physical path from `pwd -P`.
  **Found by:** comparing `ls -ld` and `readlink -f` with the rejected mount path.
- **Symptom:** source preparation stops at `quilt: command not found` before any compilation.
  **Cause:** the earlier build image never needed that tool.
  **Fix:** install the verified quilt candidate before extending the series.
  **Found by:** the first real source-preparation run, not a shell syntax check.
- **Symptom:** lintian finds an unstripped KAuth helper even though the recipe has a strip step.
  **Cause:** the file selector names `kauth/HELPER`, while KF6 installs it under `kauth/libexec/HELPER`; the shared-library dependency scan misses the same file.
  **Fix:** select the actual installed path in both steps and check the resulting binary package, rather than only the staging command.
  **Found by:** lintian's exact installed filename compared with the recipe's two `find` expressions.

No source-only gate proves a final `.deb`, runtime dependencies, installed painting or processor offload.
Those remain separate recorded results.

## An incremental binary build needs a separate source archive check

Symptom: `dpkg-buildpackage -nc` produces binary changes but no new `.dsc`.
Cause: this route implicitly selects a binary build when no explicit full-build type is given.
For the normal recipe, use its full source/build pipeline unchanged.
If validating an incremental rebuild, retain a clean authored source with the exact prepared rules, control, changelog and toolkit, pack its source archive, re-extract it and compare every changed compiler input through the qualified projection manifest.
Do not pack an active projected source/build tree as though it were the authored archive.
The missing `.dsc`, dpkg-buildpackage's log and a 27-input re-extraction comparison identified and checked this boundary.
A tools image that has dpkg-source may still lack `dch`; verify preparation prerequisites before running `lean.debian_prepare`.
The measured tools image failed there; using the already prepared build's exact generated rules and changelog completed the clean source archive, with matching control and preserved-source plan.

## Keep the catalog template and compiled translations together

Symptom: the Graphics build says a message is missing from a translated PO file, although the changed QML message and all nine PO catalogs agree.
Cause: its POT template still has the old message; the problems-catalog consumer treats that template as its source authority.
Fix: update or re-extract the template with the QML and PO changes, then run the actual catalog build and load the installed MO catalogs for all nine translated languages.
The exact old key in the error and template identified the mismatch; the earlier C-locale warnings were not this failure.
The corrected installed English page and all nine contextual translations remove an unsupported processor-offload promise while keeping all painting choices.

## Recover compiler commands and a lost log relay

- Symptom: the package build has no `compile_commands.json` for the requested Clang check.
  Cause: its CMake invocation did not enable database export.
  Fix: read `ninja -C BUILD -t compdb`, retain that database, select the changed translation units and compile their actual flags with Clang.
  Drop GCC-only LTO-object flags and the GCC PCH; write objects and dependency files to a separate scratch path.
  The measured 13-unit check then passed without warnings, including the explicit vector-path definition include.
  Object compilation is not a full Clang module link or Qt CI.
- Symptom: a host Docker client exits 143 and its build log freezes, while the owned container keeps compiling.
  The reason for the client termination was not established.
  Fix: inspect only the owned container before restarting work, reconnect `docker logs --follow`, and register `docker wait` before it exits.
  Retain the interrupted relay and direct container exit status separately.
  The measured build continued to exit 0 and passed its 33-package link and 64-package payload gates; a frozen relay alone was not a failed build.

## The painter as a successor of the published source (2026-11-14)

The route above built the painter on a plain source made back from the published one.
Once the published source has itself been made by the successor tool, the recipe follows it: `next-source-N.sh` in the package's recipe folder, which runs `repo/lc-successor.py --in-place --overlay` on the published `+lc1` source.

1. **Pick the number.** The recipe on the main branch names the last version made; candidates a lane built and never published keep their numbers too, so that one version names one set of bytes anywhere. Say which numbers were skipped and why in the script's header.
2. **The overlay holds only what lies under `debian/`:** the new patches, the whole new `series`, and whatever else the source gains. `lc-successor.py` refuses any difference outside `debian/` but the changelog and its own toolkit.
3. **Baked binaries go under `debian/` too.** A quilt patch cannot carry them and the in-place route cannot add them to the upstream tree, so the three baked shaders sit in `debian/painting-shaders`, listed in `debian/source/include-binaries`, and one more patch makes the build take them from there under the names the engine asks for:

   ```cmake
   set_source_files_properties("${QtBase_SOURCE_DIR}/debian/painting-shaders/batchpaint.vert.qsb"
       PROPERTIES QT_RESOURCE_ALIAS "painting/shaders/batchpaint.vert.qsb")
   qt_internal_add_resource(Gui "gui_batchpaint_shaders" PREFIX "/qt-project.org/gui" FILES ...)
   ```

   [`QT_RESOURCE_ALIAS`](https://doc.qt.io/qt-6/cmake-source-file-property-qt-resource-alias.html) "overrides the runtime path where the resource file is found".
   Check it in a build tree before the package build: the generated `.qrc` under `src/gui/.qt/rcc/` must list each file with its alias, and the painting must start.
   Mark the patch as packaging only (`Forwarded: not-needed`): a change offered to Qt adds the files beside its other baked shaders.
4. **The patches that are ours** are named for the copyright file by `repo/provenance-files.py`; run it on a scratch folder that holds the new patches and put its `debian/sparky-provenance-files` in the overlay.
5. **Commit the recipe, then make the source twice** into two folders and compare the `.dsc` and the Debian tarball: the date is the recipe folder's last commit, so any later commit there changes the bytes. Check that the published changelog is a byte-identical suffix of the new one (`tail -c SIZE new | cmp - old`).
6. **Build the binaries from the `.dsc`** with `release/build-from-lc-dsc.sh`, the previous version's packages as `SPARKY_LC_PREVIOUS_DIR`, and a watch on the disk beside it.

Traps:

- **Symptom:** `lc-successor: the new source differs beyond its changelog and toolkit: ['debian/painting-shaders']`.
  **Cause:** the tool's comparison names a folder that exists on one side only by the folder's own name, and its list of allowed paths held the overlay's files.
  **Fix:** the tool now allows a folder the overlay brings whole; before that fix, put the files in a folder the published source already has.
  **Found by:** the message names the folder, not a file.
- **Symptom:** `dpkg-source: error: unexpected end of diff` for a patch written by hand.
  **Cause:** hunk line counts that do not match the hunk.
  **Fix:** make the change in a source tree and take the patch from `git diff`; `dpkg-source -b` is the check that every patch of the series applies.
  **Found by:** the dry run of the source, minutes, not the package build, hours.
- **Symptom:** a native package (`3.0 (native)`, built by its own `build.sh`) has a record that says `NOT complete, unrecorded: buildinfo`.
  **Cause:** its `build.sh` assembles the packages itself, so no `dpkg-buildpackage` wrote a `.buildinfo`.
  **Fix:** build the `.dsc` that `build.sh` made once more with a copy of `release/build-from-lc-dsc.sh` that reads the changelog from the one tarball (`tar -xJOf X.tar.xz --wildcards '*/debian/changelog'`), with the toolkit's `repo` and `lean` folders mounted where the source's rules look for them (two levels above the source tree).
  The record then has `"unrecorded": []`; stage those packages, and keep the first run's `.dsc` and tarball, which are the same bytes on a second run.
  **Found by:** the record's own line, and the published version's stage, which had a `.buildinfo`.
- **Symptom:** `chown: changing ownership of '/work/lean': Read-only file system`, and the build stops before it starts.
  **Cause:** the script gives the whole work folder to the build user, and read-only mounts sit inside it.
  **Fix:** give it only the build and scratch folders.
- **Symptom:** a message in `${VAR:?...}` with an apostrophe breaks every quote after it in the script.
  **Fix:** no apostrophe inside an unquoted `${...:?message}`; `bash -n` before running.
- **Symptom:** two matrices running side by side lose cases with "container name already in use".
  **Cause:** both name their containers after the case alone.
  **Fix:** the matrix's own name goes into the container's name.
