# Reconciling an old multi-program request against what ships

A request written weeks ago ("package F3D, GRASS, KiCad and OpenSCAD") is answered by facts, program by program, before any lane builds.
The queue row's warning stands: package absence does not mean no source work; a folder in the build tree does not mean it ships.
Four commands per program give the row; each result goes to a file under `evidence/`.

## The four steps and their commands

1. **What ships.** Unpack the published source's debian tarball and read the series, the changelog and the control file:
   `tar -xJf POOL/.../NAME_VERSION.debian.tar.xz -C scratch/NAME`, then `grep -v '^#' scratch/NAME/debian/patches/series`, `head -40 scratch/NAME/debian/changelog`, `grep -n -i stereo scratch/NAME/debian/control`.
   A name missing from the pool is "not in the round": then `apt-cache policy NAME` and `apt-cache showsrc NAME` in a throwaway `debian:testing` container with deb-src lines, and the role lists of the build tree for whether a task names it.
2. **What exists unshipped.** List the recipe folders (`packages/*`, `upstream/*`) and compare a patch of the folder with the published one by its diff lines without the `index` line: identical means the folder is the shipped source, different means a successor or a superseded copy.
3. **The fork and how far it is behind.** GitHub: `gh api repos/UP/NAME/compare/DEFAULT...OWNER:BRANCH`, read `ahead_by`, `behind_by` and `merge_base_commit`. GitLab across projects: `GET /projects/FORK_ID/repository/compare?from=BRANCH&to=stereo&from_project_id=UP_ID`. List the fork's own commits by their `Assisted-by` trailer.
4. **Does our series still apply.** Unpack Debian's current source with `dpkg-source -x --no-copy`, then `patch -p1 -N` each patch of the series in order, in a container, and record the exit status of each with its failed-hunk count. For a source too large to download, fetch only the files the patches touch from `https://sources.debian.org/data/main/INITIAL/NAME/VERSION/PATH` and apply there.

## Why a program is missing from testing

`apt-cache policy` showing `Candidate: (none)` is the start, not the answer.
Read the source's tracker page (the news list has a line "NAME REMOVED from testing" with a date; the migration excuses name the blocking bug), then the bug over SOAP (`get_status`: subject, severity, date).
The two cases met: OpenSCAD (removed 2026-10-26, a serious FTBFS bug, still in unstable) and PyMOL (removed 2026-06-20, a serious flaky autopkgtest bug, still in unstable).
Both are in unstable, so the edition's carry-from-unstable recipe (`edition-packaging/references/carried-from-debian-unstable.md`) applies; neither is gone for good.

## Traps met

- Symptom: every patch reported as "No such file" with a brace list in the name. Cause: the container's `sh` is dash and does not expand `{1,2,3}`. Fix: run the script with `bash`; a result line that shows a literal brace is the sign.
- Symptom: `apt-get source kicad` downloaded a version testing does not have, and then hundreds of megabytes. Cause: a deb-src line for unstable was present, and `apt-get source` takes the highest version. Fix: add the unstable deb-src only for the programs testing lacks, and fetch single files from sources.debian.org for a big tree.
- Symptom: a fork branch shows `ahead_by` 126 for three commits of our own. Cause: the branch is built on a release tag and upstream's branch had not reached it. Fix: count commits by their `Assisted-by` trailer, and say the base.
- Symptom: `rm` of a download failed with permission denied. Cause: the container ran as root. Fix: `chown -R` the scratch folder to the user at the end of the container's script.
- Symptom: a published series looked correct and carried a width-scaled depth. Cause: the series was read by patch names. Fix: grep the published patches for `width` and `1920` in added lines, as the one-separation check asks.
- Symptom: `gh api search/issues` for "stereo" returned unrelated issues only. Cause: that is the answer; the repository had none. Fix: record "nothing found" with the query.
