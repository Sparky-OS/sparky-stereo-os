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

No source-only gate proves a final `.deb`, runtime dependencies, installed painting or processor offload.
Those remain separate recorded results.
