# Retiring a released fix and its local copies

A merge, a release containing it, a distribution package containing it, and a disposable local copy are four separate claims.
Each needs its own evidence.
The edition keeps shipping its fix while those checks are incomplete.
The credit remains in [the one merges list](../../../docs/upstream-merges.md).

## Recipe

1. Freeze the inventory at named commits of the documents, recipes and forks.
   Record every merged item, including secondary commits, release-branch picks and fixes a maintainer wrote following a report.
   Keep open reviews and identifier registrations separate from merged software fixes.
   Read the current published `Sources` index and the source package's `debian/changelog`, `debian/patches/series` and patch headers.
   Follow the recipe's imports to other recipe directories and forks.
   A historical recipe folder or a filename search alone does not identify the shipped source.
2. Resolve the upstream commit on the correct project's history.
   In an owned audit clone with complete history and tags, run `git tag --contains COMMIT`.
   Check the containing tags against the project's release record and record the first released version, tag, publication date and URL.
   A development snapshot, release candidate or prerelease stays labelled as such.
   Record the stable-branch commit separately when a backport has a different hash.
   Missing tags in a shallow or stale clone do not prove that no release contains the fix.
3. Match the carried patch to that fix by content.
   Read its DEP-3 `Origin`, `Applied-Upstream` and `Bug` links and any mailbox commit hash, then compare the changes.
   `git patch-id --stable` can establish equivalent textual changes after a cherry-pick.
   A squash, rewritten test or context-adjusted backport needs a documented content comparison too.
   A subject match is a discovery lead, never deletion proof.
4. At the next rebuild **on a release containing the fix**, remove only the redundant patch and its series or generator entry.
   Keep other distribution changes, build from the new release, and rerun the relevant regression and package checks.
   A patch that still applies can still be redundant; one that fails to apply is not automatically redundant.
   Add the verified shipped release to the existing merge entry without removing its credit.
5. Retire our package only when Debian testing's source contains the fix and no other change of ours remains.
   Record the exact testing source version and architecture coverage from current archive metadata, then inspect its changelog or actual patch/code.
   An upload to unstable does not establish testing migration.
   A newer version number alone does not establish that a reverted or omitted fix is present.
   Reconcile every remaining authored change, including dependencies, defaults, maintainer scripts and integrations, before proposing the switch.
   Account for the old package's epoch and suffix, generated pins, renamed binaries, tasks and Lean Code companions in the publication plan.
   Prove the candidate upgrade transaction with the edition's real pins; removing a pin alone may leave the installed version preferred.
6. Prove a local copy separately before freeing it.
   Record its real path, filesystem, allocated size, shared objects/worktrees and any hard links, plus dirty, untracked and ignored files, detached HEAD, local branches, tags, stash, reflogs and recoverable commits.
   Do not open unrelated private files while making that inventory.
   Query live fork tips with `git ls-remote`, and fetch only into an owned audit clone.
   Local remote-tracking refs establish what was cached, not what is online today.
   Compare each unique commit with upstream, our public forks and the build repository's carried patches using stable patch IDs.
   One way to compute the ID of an ordinary commit is:

   ```sh
   git show --format= --binary --no-ext-diff COMMIT | git patch-id --stable
   ```

   Inspect binary changes, merges, empty commits and rewritten or folded changes explicitly; an empty patch-ID result is not a pass.
   A matching patch ID ignores whitespace, so inspect meaningful whitespace and generated or binary files when they matter.
   Save every unmatched change and every needed report, trace, fixture or stage in an approved durable location and verify that copy before proposing deletion.
   Keep public fork branches online.
7. Hand back one row per candidate, sorted by measured reclaimable size, with its proof and exact keep set.
   Separate apparent size from allocated space, and account for shared worktree Git directories, hard-linked publication pools and nested candidates so totals are not counted twice.
   Check for a retained publication stage, an active process or an object store borrowed by another repository.
   Permission errors, missing objects and incomplete comparisons leave the candidate kept with the unanswered check named.
   A proposal-only audit makes no removals and reports zero space actually freed.

## Traps found while inventorying retirement candidates

- **Symptom:** the carried FFmpeg or mpv patch is absent from an inventory of `upstream/` and `packages/`.
  **Cause:** a source generator imports its active stack from `sparky-os/media`, while the old patch folder remains.
  **Fix:** trace generator inputs and match them against the published source's series.
  **Found by:** reading `packages/ffmpeg-dmo/make-source.py`, its `RECIPE` assignment and the published Debian tarball.
- **Symptom:** a shipped patch does not byte-match the fork's patch although its change is present.
  **Cause:** packaging removed a binary test clip from the Qt Multimedia luminance patch.
  **Fix:** compare the actual code and retained tests, record the omitted fixture, and keep the fork's test evidence.
  **Found by:** reading `upstream/qtmultimedia/packaging/build-qt6-multimedia.sh` and the published patch header.
- **Symptom:** a package has no quilt patches, so the audit concludes that no distribution changes remain.
  **Cause:** native sources, fork-based orig archives and direct packaging edits carry changes without a quilt series.
  **Fix:** compare the complete authored source and packaging against the proposed replacement.
  **Found by:** the publication inventory showed native sources and dependency-only rebuilds beside ordinary quilt packages.
- **Symptom:** a repository appears disposable because its default branch's advertised fix merged.
  **Cause:** other branches, worktrees, ignored files, unmatched commits or a retained stage were never inventoried.
  **Fix:** prove the whole local copy and its consumers before approving removal.
  **Found by:** the [existing local-only audit](../SKILL.md#the-audit) distinguishes rewritten, missing, uncommitted and preserved work.
