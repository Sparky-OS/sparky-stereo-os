# Proving the native dpkg conffile contract

**For the builder or reviewer of the edition's dpkg: prove that a verified projection is unmodified and a person's edit stays theirs.**
Written on 2026-11-14 for dpkg 1.23.11+stereo3d3, which advertises `dpkg-lean-code (= 2)`.
The authored recipe is `sparky-os/packages/dpkg/` in the build repository.
Keep that accepted recipe unchanged when qualifying a rebuild.

## Working recipe

Run these steps only inside a disposable root container, with HTTPS archive sources, the published dpkg family, the candidate family and dpkg-stereo available.
The build's own suite and final archive link gate must pass first; the complete build record must name every binary, source descriptor, buildinfo and changes file with no unrecorded inputs.
Keep all archive inputs read only.
The container needs the recipe's test dependencies, including `eatmydata`, and an ordinary `builder` user.

1. Install the exact published baseline and client, recording the simulation and requiring no `Remv` lines:

   ```sh
   export DPKG_STEREO_DISABLE=1 DPKG_STEREO_NO_PROJECT=1
   apt-get -s install --no-install-recommends "$PUBLISHED"/*.deb "$CLIENT" > baseline-plan.txt
   ! grep -q '^Remv ' baseline-plan.txt
   apt-get -y install --no-install-recommends "$PUBLISHED"/*.deb "$CLIENT"
   ```

   These flags suppress projection of the unrelated stock container image during the fixture setup.
   The tests below still call the installed native dpkg and its fixed trusted verifier.
   This is a native dpkg contract proof, not a whole-edition projection proof.

2. Copy the source's `tests/` directory into a container-local fixture folder, preserving the originals and giving the copy to `builder`:

   ```sh
   mkdir -p /tmp/dpkg-installed
   cp -a "$SOURCE/tests" /tmp/dpkg-installed/tests
   chown -R builder:builder /tmp/dpkg-installed
   bash "$BUILD/sparky-os/packages/dpkg/test-installed.sh" \
       /tmp/dpkg-installed "$EVIDENCE/baseline" baseline
   ```

   With published `+stereo3d2`, the script requires six named failures among twenty-nine conffile tests, one root-only skip, and a passing forged-edit safety control.
   A different failure set refuses the baseline.
   It unsets `DPKG_BUILDTREE` and `DPKG_DATADIR`: the source supplies fixtures, not executables.

3. Simulate and install the candidate family:

   ```sh
   apt-get -s install --no-install-recommends "$CANDIDATE"/*.deb > upgrade-plan.txt
   ! grep -q '^Remv ' upgrade-plan.txt
   apt-get -y install --no-install-recommends "$CANDIDATE"/*.deb
   dpkg-query -W dpkg dpkg-dev libdpkg-perl libdpkg-dev dselect
   dpkg --audit > audit.txt
   test ! -s audit.txt
   apt-get check
   bash "$BUILD/sparky-os/packages/dpkg/test-installed.sh" \
       /tmp/dpkg-installed "$EVIDENCE/candidate" candidate
   ```

   Read the simulation's `Inst` lines: each requested family member must name `1.23.11+stereo3d3+lc1`.
   No removals alone does not prove that the upgrade happened.
   The candidate script requires the whole installed functional suite to pass as `builder`, then all twenty-nine conffile tests as root, including the trusted-verifier controls that require root.
   Repeat `dpkg --audit` after the tests and require it empty.

## What the tests establish

`tests/t-conffile-leancode/test.py` in the retained source exercises the installed binary and real verifier with a private dpkg root and database.
The owning package supplies the authoritative Conffiles digest; another package's placeholder or a merged hash map is not an authority.
The pristine original must match both recorded original digests and that owner's digest.
The current bytes must also equal an independent render of the genuine original, not merely a recorded projection hash.

| Case | Required result |
|---|---|
| Verified unmodified projection, new package content | Upgrade succeeds without a configuration prompt; new content arrives. |
| Same-version reinstall | Projected bytes, inode and modification time stay unchanged. |
| Real edit | Upgrade prompts with EOF on its empty input; the edit stays byte for byte. |
| `--force-confold` / `--force-confnew` | Keep the edit / install the new content, with the same decisions as an unrecorded file. |
| Forged original or projection hash, wrong owner/path, missing original | Refuse the recorded-projection claim and keep Debian's conflict decisions. |
| Missing, writable, non-root-owned, symlinked or failing verifier | Keep the file and prompt; record the refusal reason. |
| Maintscript removal/rename and declarative removal | Treat only a genuinely verified projection as unmodified; preserve real edits. |
| `dpkg --verify` | Still hashes physical bytes; a projection is reported there as changed. |

Do not interpret the last row as a regression: the accepted recipe deliberately keeps physical-byte verification separate from conffile conflict decisions.
The family retains its authored source, HR companions and original copyright records.

## Traps

- **Symptom:** a disk guard stops while the root-only FIFO or ownership controls run, although the workspace is far below its cap.
  **Cause:** the tests create private root-owned directories inside the host-mounted source tree, so the ordinary host user cannot measure that whole tree with `du`.
  **Fix:** use the container-local fixture copy above and mount the build inputs read only; run the archive gate as the ordinary builder so its scratch is measurable too.
  **How found:** the guard's stderr named the conffile fixture's private directory, not a disk-space refusal.
- **Symptom:** an upgrade proof passes while testing the build-tree dpkg rather than the installed one.
  **Fix:** use the recipe's installed-test script, which clears the two build-tree variables, fixes PATH and records installed binary hashes and versions.
  Check those records before reading the verdict.
- **Symptom:** the verifier is refused ("the verifier is missing or its executable or library is not trusted", exit 14) on an upgraded machine although the verifier is fine.
  **Cause:** a folder on its path, or a file under `lean/`, can be written by its group or by others; an early dpkg-stereo shipped its folders 0775 and dpkg keeps the mode of an existing folder.
  **Fix:** dpkg-stereo 0.1.42 sets its own tree right (preinst, postinst, `--repair`); the check stays strict. Find the step with `stat -c '%a %U %n' / /usr /usr/lib /usr/lib/dpkg-stereo /usr/lib/dpkg-stereo/conffile-verify` and `find /usr/lib/dpkg-stereo/lean ! -user root -o -perm /022`; the 0.1.42 refusal names it. See the lessons file, ORDER 707.
- **Symptom:** an edited file is accepted as unmodified because its hash was copied into a record.
  **Cause:** trusting the record alone.
  **Fix:** retain the forged-projection and untrusted-verifier controls; the independently rendered genuine original is required too.

## Credits

Dpkg is maintained by Guillem Jover, following the maintainers named in its own AUTHORS and changelog.
Its C implementation began with Ian Jackson, based on the earlier Perl implementation by Matt Welsh, Carl Streeter and Ian Murdock.
The edition's conffile work and independent review are ORDER 376 and ORDER 388; ORDER 566 rebuilds and qualifies their accepted recipe.
